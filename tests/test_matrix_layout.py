import pytest

from BESTLIB.layouts.matrix import MatrixLayout
from BESTLIB.core.exceptions import LayoutError


def test_instance_map_is_copy():
    MatrixLayout.map({'A': {'type': 'dummy'}})
    layout = MatrixLayout("A")
    layout._map['A']['custom'] = 'value'
    assert 'custom' not in MatrixLayout._map['A']


def test_validate_mapping_letters_detects_extra():
    MatrixLayout.map({'A': {'type': 'dummy'}})
    layout = MatrixLayout("A")
    with pytest.raises(LayoutError):
        layout._validate_mapping_letters({'B': {'type': 'dummy'}})

