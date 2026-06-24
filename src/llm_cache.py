import json
import os
import dataclasses
from typing import Optional

@dataclasses.dataclass
class CacheEntry:
    key: str
    value: str

class LLMCache:
    def __init__(self, disk_backed: bool = False, memory_limit: int = 100):
        self.disk_backed = disk_backed
        self.memory_limit = memory_limit
        self.cache = {}
        if disk_backed:
            self.db_path = 'llm_cache.db'
            self.load_from_disk()

    def load_from_disk(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    self.cache[key] = CacheEntry(key, value)

    def save_to_disk(self):
        data = {entry.key: entry.value for entry in self.cache.values()}
        with open(self.db_path, 'w') as f:
            json.dump(data, f)

    def get(self, key: str) -> Optional[str]:
        return self.cache.get(key).value if key in self.cache else None

    def set(self, key: str, value: str):
        if key in self.cache:
            self.cache[key].value = value
        else:
            self.cache[key] = CacheEntry(key, value)
            if len(self.cache) > self.memory_limit:
                self.cache.pop(next(iter(self.cache)))
        if self.disk_backed:
            self.save_to_disk()

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            if self.disk_backed:
                self.save_to_disk()
