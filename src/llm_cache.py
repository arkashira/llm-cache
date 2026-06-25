import json
from dataclasses import dataclass
from typing import Dict

@dataclass
class CacheEntry:
    key: str
    value: str
    timestamp: float

class AxentxCache:
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> str:
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key].value
        else:
            self.miss_count += 1
            return None

    def set(self, key: str, value: str) -> None:
        self.cache[key] = CacheEntry(key, value, 0.0)

    def get_hit_rate(self) -> float:
        total_requests = self.hit_count + self.miss_count
        if total_requests == 0:
            return 0.0
        return self.hit_count / total_requests

    def get_latency(self) -> float:
        # Simulate latency for demonstration purposes
        return 0.5
