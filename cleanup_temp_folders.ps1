# Script para limpiar carpetas temporales
# Ejecutar: .\cleanup_temp_folders.ps1

Write-Host "`n╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🧹 LIMPIEZA DE CARPETAS TEMPORALES                 ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n📋 Se eliminarán las siguientes carpetas:" -ForegroundColor Yellow
Write-Host "  • bestlib-v2/ (1.05 MB)" -ForegroundColor White
Write-Host "  • BESTLIB-backup/ (1.76 MB)" -ForegroundColor White

Write-Host "`n⚠️  CONFIRMACIÓN:" -ForegroundColor Red
$confirm = Read-Host "¿Eliminar estas carpetas? (S/N)"

if ($confirm -eq "S" -or $confirm -eq "s") {
    Write-Host "`n🗑️  Eliminando..." -ForegroundColor Yellow
    
    # Eliminar bestlib-v2
    if (Test-Path "bestlib-v2") {
        Remove-Item "bestlib-v2" -Recurse -Force
        Write-Host "  ✓ Eliminada: bestlib-v2/" -ForegroundColor Green
    }
    
    # Eliminar BESTLIB-backup
    if (Test-Path "BESTLIB-backup") {
        Remove-Item "BESTLIB-backup" -Recurse -Force
        Write-Host "  ✓ Eliminada: BESTLIB-backup/" -ForegroundColor Green
    }
    
    Write-Host "`n✅ Limpieza completada!" -ForegroundColor Green
    Write-Host "   Espacio liberado: ~2.81 MB" -ForegroundColor Gray
    
} else {
    Write-Host "`n❌ Operación cancelada" -ForegroundColor Yellow
    Write-Host "   Las carpetas se mantendrán (están excluidas en .gitignore y MANIFEST.in)" -ForegroundColor Gray
}

Write-Host ""
