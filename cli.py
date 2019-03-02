import io
import sys
import math
import logging
import pathlib
import tarfile
from itertools import chain
from time import time, sleep
from xml.etree import ElementTree
from urllib.parse import urlparse
from timeit import default_timer as timer

import click

import endpoint
import scrap
import utils
import core
from cache import Cache


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(name)s:%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass

@cli.command()
@click.option('--players',    '-p', is_flag=True, default=False)
@click.option('--alliances',  '-a', is_flag=True, default=False)
@click.option('--highscores', '-h', is_flag=True, default=False)
@click.option('--universe',   '-u', is_flag=True, default=False)
@click.argument('countries', nargs=-1)
def snapshot(countries, **options):
    _endpoints = {
        "players": [endpoint.players],
        "alliances": [endpoint.alliances],
        "universe": [endpoint.universe],
        "highscores": endpoint.highscores
    }

    home = pathlib.Path('~/gameter').expanduser()
    communities = [core.Community(c, s) for c, s in scrap.all(countries)]
    communities = sorted(communities, key=lambda c: c.country)
    endpoints = list(
        chain(*(_endpoints[option] for option, flag in options.items() if flag))
    )
    if not endpoints:
        raise RuntimeError('No endpoints provided')

    app = Snapshot(communities, endpoints, home)
    app.run()


class Snapshot:
    ATTEMPTS = 10 # number of retry attempts before rising exception

    def __init__(self, communities, endpoints, home):
        self.communities = communities
        self.endpoints = endpoints
        self.home = home

    @staticmethod
    def fetch(entry):
        resource, cached_timestamp = entry
        total_waiting_time = 0
        start = timer()

        for attempt in range(Snapshot.ATTEMPTS):
            request = utils.get(resource.url)

            # https://github.com/requests/requests/issues/2359
            if request.encoding is None:
                request.encoding = 'utf-8'

            xml = ElementTree.fromstring(request.text)
            new_timestamp = int(xml.attrib['timestamp'])
            now = time()

            if cached_timestamp == new_timestamp:
                ahead = math.ceil(new_timestamp + resource.endpoint.seconds - now)
                if ahead > 0 and ahead < 300:
                    sleep(ahead)
                    total_waiting_time += ahead
            else:
                end = timer()
                resource_name = '{}, {}'.format(resource.server, resource.endpoint.encode())
                if total_waiting_time > 0:
                    logger.info('Slept %ss for (%s)', total_waiting_time, resource_name)

                logger.debug('Fetched (%s) in %.3fs', resource_name, end - start)
                return (resource, request, new_timestamp, total_waiting_time)

        raise RuntimeError('Exceeded attempt limit')

    def snapshot(self, community):
        home = self.home / community.country
        tarname = '{}-{}.tar.bz2'.format(
            '-'.join(sorted(set( pathlib.PurePath(e.path).stem for e in self.endpoints))),
            int(time())
        )
        home.mkdir(parents=True, exist_ok=True)
        tar = tarfile.open(str(home / tarname), mode='w:bz2')
        with Cache(home / 'timestamps.json') as cache:
            resources = (
                (resource, cache.get(resource.url)) for resource
                in chain(*(s.resources(self.endpoints) for s in community))
            )

            total_waited_time = 0
            for resource, request, timestamp, total in utils.parallel(resources, Snapshot.fetch):
                total_waited_time += total
                cache.set(resource.url, timestamp)
                filename = str(resource.server) + '/' + resource.endpoint.encode()
                info = tarfile.TarInfo(name=filename)
                info.size = len(request.content)
                data = io.BytesIO(request.content)
                tar.addfile(info, fileobj=data)
        tar.close()
        return total_waited_time

    def run(self):
        for community in self.communities:
            start = timer()
            total = self.snapshot(community)
            end = timer()
            endpoints = '-'.join(sorted(set(pathlib.PurePath(e.path).stem for e in self.endpoints)))
            logger.info('Done (%s, %s) in %.3fs, waited %ss',
                        community.country,
                        endpoints, end - start, total)


if __name__ == '__main__':
    cli()
