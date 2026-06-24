import pytest
from llm_cache import LLMCache, CacheEntry

def test_get_set():
    cache = LLMCache()
    cache.set('key', 'value')
    assert cache.get('key') == 'value'

def test_get_nonexistent():
    cache = LLMCache()
    assert cache.get('key') is None

def test_delete():
    cache = LLMCache()
    cache.set('key', 'value')
    cache.delete('key')
    assert cache.get('key') is None

def test_disk_backed():
    cache = LLMCache(disk_backed=True)
    cache.set('key', 'value')
    cache = LLMCache(disk_backed=True)
    assert cache.get('key') == 'value'

def test_memory_limit():
    cache = LLMCache(memory_limit=2)
    cache.set('key1', 'value1')
    cache.set('key2', 'value2')
    cache.set('key3', 'value3')
    assert len(cache.cache) == 2

def test_disk_write_latency():
    import time
    cache = LLMCache(disk_backed=True)
    start_time = time.time()
    cache.set('key', 'value')
    end_time = time.time()
    assert end_time - start_time < 0.005
