from BESTLIB.charts import ChartRegistry
from BESTLIB.core.registry import Registry


def test_registry_lists_basic_charts():
    available = ChartRegistry.list_types()
    assert 'scatter' in available
    assert 'bar' in available


def test_core_registry_in_sync_with_chart_registry():
    scatter_instance = ChartRegistry.get('scatter')
    registered_cls = Registry.get('chart', 'scatter')
    assert registered_cls is scatter_instance.__class__

