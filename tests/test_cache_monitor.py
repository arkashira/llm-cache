from cache_monitor import CacheMonitor, CachePerformanceMetric

def test_collect_metrics():
    monitor = CacheMonitor()
    monitor.collect_metrics('cache1', 10, 5, 100)
    assert monitor.metrics['cache1'].hits == 10
    assert monitor.metrics['cache1'].misses == 5
    assert monitor.metrics['cache1'].size == 100

def test_report_metrics():
    monitor = CacheMonitor()
    monitor.collect_metrics('cache1', 10, 5, 100)
    monitor.collect_metrics('cache2', 20, 10, 200)
    metrics = monitor.report_metrics()
    assert metrics['cache1']['hits'] == 10
    assert metrics['cache1']['misses'] == 5
    assert metrics['cache1']['size'] == 100
    assert metrics['cache2']['hits'] == 20
    assert metrics['cache2']['misses'] == 10
    assert metrics['cache2']['size'] == 200

def test_visualize_metrics():
    monitor = CacheMonitor()
    monitor.collect_metrics('cache1', 10, 5, 100)
    visualization = monitor.visualize_metrics()
    assert 'Cache cache1:' in visualization
    assert '  Hits: 10' in visualization
    assert '  Misses: 5' in visualization
    assert '  Size: 100' in visualization

def test_optimize_cache():
    monitor = CacheMonitor()
    monitor.collect_metrics('cache1', 10, 5, 100)
    optimization = monitor.optimize_cache('cache1')
    assert optimization == 'Cache cache1 is performing well.'
    monitor.collect_metrics('cache2', 5, 10, 100)
    optimization = monitor.optimize_cache('cache2')
    assert optimization == 'Cache cache2 is underperforming. Consider increasing its size.'
    optimization = monitor.optimize_cache('cache3')
    assert optimization == 'Cache cache3 not found.'
