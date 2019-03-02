import concurrent.futures
from xml.etree import ElementTree
from bs4 import BeautifulSoup

import utils

# Since there is no standard way to obtain list of all
# available servers and communities, we have to improvise.

BASE = 'https://{}.ogame.gameforge.com'
BASE_SERVER = 'https://s{}-{}.ogame.gameforge.com'

REPRESENTANTS = {
        'ar': 101,
        'br': 127,
        'cz': 127,
        'de': 127,
        'dk': 104,
        'en': 128,
        'es': 127,
        'fi': 102,
        'fr': 127,
        'gr': 112,
        'hr': 109,
        'hu': 101,
        'it': 128,
        'jp': 101,
        'mx': 101,
        'nl': 104,
        'no': 101,
        'pl': 127,
        'pt': 127,
        'ro': 110,
        'ru': 127,
        'se': 103,
        'si': 101,
        'sk': 101,
        'tr': 128,
        'tw': 101,
        'us': 128
}

def communities():
    """Scrap community list from ogame website."""
    try:
        r = utils.get(BASE.format('pl'))
        soup = BeautifulSoup(r.text, 'html.parser')
        tags = soup.find(id="mmoList1").find_all('a')
        communities = [tag.get('href')[2:4] for tag in tags]
    except Exception as e:
        communities = list(REPRESENTANTS.keys())
    return communities


def servers(community):
    """Scrap all servers for particular community from ogame website."""
    r = utils.get(BASE.format(community))
    soup = BeautifulSoup(r.text, 'html.parser')
    tags = soup.find(id="serverLogin").find_all('option')
    servers = [int(tag.get('value').split('.')[0][1:-3]) for tag in tags]
    return servers

def servers(community):
    try:
        server_id = REPRESENTANTS[community]
    except KeyError:
        return []

    r = utils.get('https://s{}-{}.ogame.gameforge.com/api/universes.xml'
            .format(server_id, community))
    r.encoding = 'utf-8' if r.encoding is None else r.encoding
    xml = ElementTree.fromstring(r.text)
    ids = []
    for child in xml:
        ids.append(int(child.attrib['id']))
    return ids

def all(countries=None):
    """Scraps servers for all communities at once in parallel"""
    action = lambda c: (c, servers(c))
    return utils.parallel(countries or communities(), action)

