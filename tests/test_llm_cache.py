import pytest
from llm_cache import AxentxCache

def test_cache_hit():
    cache = AxentxCache()
    cache.set("key", "value")
    assert cache.get("key") == "value"
    assert cache.hit_count == 1
    assert cache.miss_count == 0

def test_cache_miss():
    cache = AxentxCache()
    assert cache.get("key") is None
    assert cache.hit_count == 0
    assert cache.miss_count == 1

def test_cache_hit_rate():
    cache = AxentxCache()
    cache.set("key1", "value1")
    cache.get("key1")
    cache.set("key2", "value2")
    cache.get("key2")
    cache.get("key3")
    assert cache.get_hit_rate() == 2/3

def test_cache_latency():
    cache = AxentxCache()
    assert cache.get_latency() < 1.0
