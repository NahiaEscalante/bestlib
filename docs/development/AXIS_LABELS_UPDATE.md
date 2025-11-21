# Axis Labels Feature - Update Documentation

## Overview

This update adds **automatic axis labels** to all chart types in the BESTLIB visualization library. Previously, charts displayed axes with tick marks and values but lacked descriptive labels explaining what each axis represented. This made it difficult to understand the data being visualized.

## Problem Solved

**Before:** Charts had axes without labels, making it unclear what data was being displayed on each axis.

**After:** All charts now automatically display descriptive axis labels based on the column names used to create the visualization.

## Changes Made

### 1. JavaScript Updates (`matrix.js`)

Updated all D3.js rendering functions to support `xLabel` and `yLabel` parameters:

- ✅ `renderScatterPlotD3()` - Scatter plots
- ✅ `renderBarChartD3()` - Bar charts  
- ✅ `renderHistogramD3()` - Histograms
- ✅ `renderBoxplotD3()` - Box plots
- ✅ `renderHeatmapD3()` - Heatmaps
- ✅ `renderLineD3()` - Line charts

Each function now checks for `spec.xLabel` and `spec.yLabel` and renders them as text elements positioned appropriately on the chart.

### 2. Python API Updates (`matrix.py`)

Updated all helper methods to automatically set axis labels from column names:

- ✅ `map_scatter()` - Automatically uses `x_col` and `y_col` as labels
- ✅ `map_barchart()` - Uses `category_col` for X-axis, `value_col` or "Count" for Y-axis
- ✅ `map_histogram()` - Uses `value_col` for X-axis, "Frequency" for Y-axis
- ✅ `map_boxplot()` - Uses `category_col` and `value_col` as labels
- ✅ `map_heatmap()` - Uses `x_col` and `y_col` as labels
- ✅ `map_line()` - Uses `x_col` and `y_col` as labels

## Usage

### Automatic Labels (Default Behavior)

Labels are automatically generated from column names:

```python
import pandas as pd
from BESTLIB import MatrixLayout

df = pd.DataFrame({
    'edad': [25, 30, 35, 40],
    'salario': [30000, 45000, 55000, 65000],
    'departamento': ['Ventas', 'IT', 'RRHH', 'Ventas']
})

# Scatter plot - automatically labels axes as "edad" and "salario"
layout = MatrixLayout("S")
MatrixLayout.map_scatter('S', df, x_col='edad', y_col='salario')
layout
```

### Custom Labels (Override)

You can provide custom labels to override the automatic ones:

```python
# Custom axis labels in Spanish
MatrixLayout.map_scatter('S', df, 
                         x_col='edad', 
                         y_col='salario',
                         xLabel='Edad (años)',
                         yLabel='Salario Anual (USD)')
```

## Examples

### Scatter Plot
```python
MatrixLayout.map_scatter('S', df, x_col='edad', y_col='salario')
# X-axis: "edad"
# Y-axis: "salario"
```

### Bar Chart
```python
MatrixLayout.map_barchart('B', df, category_col='departamento')
# X-axis: "departamento"
# Y-axis: "Count"
```

### Histogram
```python
MatrixLayout.map_histogram('H', df, value_col='salario', bins=10)
# X-axis: "salario"
# Y-axis: "Frequency"
```

### Boxplot
```python
MatrixLayout.map_boxplot('B', df, category_col='departamento', value_col='salario')
# X-axis: "departamento"
# Y-axis: "salario"
```

### Line Chart
```python
MatrixLayout.map_line('L', df, x_col='experiencia', y_col='salario')
# X-axis: "experiencia"
# Y-axis: "salario"
```

## Testing

Two test files have been created:

1. **`test_axis_labels.py`** - Python script to verify labels are set correctly
2. **`demo_axis_labels.ipynb`** - Jupyter notebook with visual examples

Run the test script:
```bash
cd examples
python test_axis_labels.py
```

Or open the Jupyter notebook to see visual examples:
```bash
jupyter notebook demo_axis_labels.ipynb
```

## Technical Details

### Label Positioning

- **X-axis labels:** Centered below the X-axis, 35px from the axis line
- **Y-axis labels:** Rotated 90° counterclockwise, centered on the left side, 40px from the axis line
- **Font:** Arial, 13px, bold (weight: 700)
- **Color:** Black (#000000)

### Backward Compatibility

✅ **Fully backward compatible** - Existing code will continue to work without modifications. The automatic labels are only added if not explicitly provided.

### Parameters

All chart methods now accept optional parameters:
- `xLabel` (str): Custom label for X-axis
- `yLabel` (str): Custom label for Y-axis

If not provided, labels are automatically generated from column names.

## Benefits

1. **Better Clarity** - Users can immediately understand what data is being displayed
2. **Automatic** - No extra code needed, labels are generated automatically
3. **Customizable** - Can override with custom labels when needed
4. **Consistent** - All chart types follow the same labeling convention
5. **Professional** - Charts look more polished and publication-ready

## Files Modified

- `BESTLIB/matrix.js` - Added axis label rendering to all chart functions
- `BESTLIB/matrix.py` - Added automatic label generation to all helper methods
- `examples/test_axis_labels.py` - Test script (NEW)
- `examples/demo_axis_labels.ipynb` - Demo notebook (NEW)

## Migration Guide

No migration needed! This is a non-breaking change. Your existing code will automatically benefit from axis labels.

If you want to customize labels, simply add the `xLabel` and `yLabel` parameters:

```python
# Before (still works, now with automatic labels)
MatrixLayout.map_scatter('S', df, x_col='age', y_col='salary')

# After (with custom labels)
MatrixLayout.map_scatter('S', df, x_col='age', y_col='salary',
                         xLabel='Age (years)', yLabel='Annual Salary ($)')
```

## Future Enhancements

Potential improvements for future versions:
- Support for axis label rotation/angle
- Configurable label font size and style
- Support for multi-line labels
- Label positioning options (inside/outside)

---

**Date:** November 2024  
**Version:** 1.1.0  
**Status:** ✅ Complete and tested
