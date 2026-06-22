import json
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class CachePerformanceMetric:
    hits: int
    misses: int
    size: int

class CacheMonitor:
    def __init__(self):
        self.metrics = {}

    def collect_metrics(self, cache_name: str, hits: int, misses: int, size: int):
        self.metrics[cache_name] = CachePerformanceMetric(hits, misses, size)

    def report_metrics(self) -> Dict[str, Dict[str, int]]:
        return {cache_name: {
            'hits': metric.hits,
            'misses': metric.misses,
            'size': metric.size
        } for cache_name, metric in self.metrics.items()}

    def visualize_metrics(self) -> str:
        metrics = self.report_metrics()
        visualization = ''
        for cache_name, metric in metrics.items():
            visualization += f'Cache {cache_name}:\n'
            visualization += f'  Hits: {metric["hits"]}\n'
            visualization += f'  Misses: {metric["misses"]}\n'
            visualization += f'  Size: {metric["size"]}\n\n'
        return visualization

    def optimize_cache(self, cache_name: str) -> str:
        metric = self.metrics.get(cache_name)
        if metric:
            if metric.misses > metric.hits:
                return f'Cache {cache_name} is underperforming. Consider increasing its size.'
            else:
                return f'Cache {cache_name} is performing well.'
        else:
            return f'Cache {cache_name} not found.'
