# Script de instalación y prueba rápida para BESTLIB v2
# PowerShell

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  BESTLIB v2 - Instalación y Prueba" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Paso 1: Verificar estructura
Write-Host "`n[1/4] Verificando estructura..." -ForegroundColor Yellow
if (Test-Path "bestlib-v2\bestlib\__init__.py") {
    Write-Host "  ✓ Estructura OK" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error: No se encuentra bestlib-v2/" -ForegroundColor Red
    exit 1
}

# Paso 2: Instalar en modo desarrollo
Write-Host "`n[2/4] Instalando BESTLIB v2..." -ForegroundColor Yellow
Set-Location bestlib-v2
pip install -e . --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Instalación exitosa" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error en instalación" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Paso 3: Verificar importación
Write-Host "`n[3/4] Verificando importación..." -ForegroundColor Yellow
python -c "import bestlib; print(f'  ✓ BESTLIB v{bestlib.__version__} importado correctamente')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Error al importar" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Paso 4: Ejecutar tests básicos
Write-Host "`n[4/4] Ejecutando tests..." -ForegroundColor Yellow
if (Get-Command pytest -ErrorAction SilentlyContinue) {
    pytest tests/test_basic.py -v
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Tests pasaron" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Algunos tests fallaron (revisar pytest)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ pytest no instalado, saltando tests" -ForegroundColor Yellow
    Write-Host "    Instalar con: pip install pytest" -ForegroundColor Gray
}

Set-Location ..

# Resumen
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  ✅ BESTLIB v2 LISTO PARA USAR" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`nPróximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Abrir Jupyter: jupyter notebook bestlib-v2/examples/quick_start.ipynb"
Write-Host "  2. O importar en Python: import bestlib"
Write-Host "  3. Ver docs: cat bestlib-v2/README.md`n"
