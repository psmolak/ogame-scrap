import json

class Cache:

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.store = {}

        if self.path.exists():
            with self.path.open('r') as file:
                try:
                    self.store = json.load(file)
                except json.JSONDecodeError:
                    raise
        return self

    def __exit__(self, *args):
        with self.path.open('w') as file:
            file.write(json.dumps(self.store, indent=2))

    def get(self, key, default=0):
        return self.store.get(key, default)

    def set(self, key, value):
        self.store[key] = value

