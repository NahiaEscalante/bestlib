from BESTLIB.charts.violin import ViolinChart
from BESTLIB.charts.radviz import RadvizChart
from BESTLIB.charts.parallel_coordinates import ParallelCoordinatesChart


def test_violin_chart_returns_values():
    chart = ViolinChart()
    data = [{'group': 'A', 'value': 1}, {'group': 'A', 'value': 2}]
    spec = chart.get_spec(data, value_col='value', category_col='group')
    assert spec['type'] == 'violin'
    assert spec['data'][0]['values']


def test_radviz_chart_requires_features():
    chart = RadvizChart()
    data = [{'x': 1, 'y': 2, 'label': 'a'}]
    spec = chart.get_spec(data, features=['x', 'y'], class_col='label')
    assert spec['features'] == ['x', 'y']


def test_parallel_coordinates_spec_contains_dimensions():
    chart = ParallelCoordinatesChart()
    data = [{'x': 1, 'y': 2}]
    spec = chart.get_spec(data, dimensions=['x', 'y'])
    assert spec['dimensions'] == ['x', 'y']

