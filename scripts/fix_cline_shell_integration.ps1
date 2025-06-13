# Script para solucionar problemas de Shell Integration con Cline
# Ejecutar como administrador si es necesario

Write-Host "🔧 Solucionando problemas de Shell Integration para Cline..." -ForegroundColor Green

# Verificar versión de VSCode
Write-Host "`n📋 Verificando VSCode..." -ForegroundColor Yellow
$vscodeVersion = code --version
if ($vscodeVersion) {
    Write-Host "✅ VSCode encontrado:" -ForegroundColor Green
    $vscodeVersion | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "❌ VSCode no encontrado en PATH" -ForegroundColor Red
    exit 1
}

# Verificar PowerShell
Write-Host "`n📋 Verificando PowerShell..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
Write-Host "✅ PowerShell $psVersion encontrado" -ForegroundColor Green

# Verificar Poetry
Write-Host "`n📋 Verificando Poetry..." -ForegroundColor Yellow
try {
    $poetryVersion = poetry --version
    Write-Host "✅ $poetryVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Poetry no encontrado en PATH" -ForegroundColor Red
    Write-Host "   Instala Poetry desde: https://python-poetry.org/docs/#installation" -ForegroundColor Yellow
}

# Verificar configuración de ExecutionPolicy
Write-Host "`n📋 Verificando ExecutionPolicy..." -ForegroundColor Yellow
$executionPolicy = Get-ExecutionPolicy
Write-Host "   Política actual: $executionPolicy" -ForegroundColor Gray

if ($executionPolicy -eq "Restricted") {
    Write-Host "⚠️  ExecutionPolicy está en Restricted" -ForegroundColor Yellow
    Write-Host "   Esto puede causar problemas con shell integration" -ForegroundColor Yellow
    Write-Host "   Ejecuta: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
}

# Crear configuración de perfil de PowerShell para shell integration
Write-Host "`n📋 Configurando perfil de PowerShell..." -ForegroundColor Yellow
$profilePath = $PROFILE
$profileDir = Split-Path $profilePath -Parent

if (!(Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Host "✅ Directorio de perfil creado: $profileDir" -ForegroundColor Green
}

# Contenido del perfil optimizado para Cline
$profileContent = @"
# Configuración optimizada para Cline Shell Integration
`$Host.UI.RawUI.WindowTitle = "PowerShell - Cline Ready"

# Habilitar funciones de completado
Set-PSReadlineKeyHandler -Key Tab -Function Complete

# Configurar prompt para mejor visibilidad
function prompt {
    `$path = `$PWD.Path
    if (`$path.Length -gt 50) {
        `$path = "..." + `$path.Substring(`$path.Length - 47)
    }
    Write-Host "[PS] " -NoNewline -ForegroundColor Green
    Write-Host `$path -NoNewline -ForegroundColor Blue
    Write-Host " > " -NoNewline -ForegroundColor Yellow
    return " "
}

# Variables de entorno para mejor compatibilidad
`$env:TERM = "xterm-256color"
`$env:FORCE_COLOR = "1"
`$env:CLICOLOR = "1"

# Función para activar Poetry shell
function Enter-PoetryShell {
    if (Test-Path "pyproject.toml") {
        poetry shell
    } else {
        Write-Host "❌ No se encontró pyproject.toml en el directorio actual" -ForegroundColor Red
    }
}

# Alias útiles
Set-Alias -Name pshell -Value Enter-PoetryShell
Set-Alias -Name ll -Value Get-ChildItem

Write-Host "🚀 PowerShell configurado para Cline" -ForegroundColor Green
"@

# Escribir configuración al perfil
Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8
Write-Host "✅ Perfil de PowerShell configurado: $profilePath" -ForegroundColor Green

# Verificar extensiones de VSCode necesarias
Write-Host "`n📋 Verificando extensiones de VSCode..." -ForegroundColor Yellow
$requiredExtensions = @(
    "ms-python.python",
    "ms-python.debugpy", 
    "charliermarsh.ruff",
    "ms-python.black-formatter"
)

foreach ($extension in $requiredExtensions) {
    $installed = code --list-extensions | Select-String $extension
    if ($installed) {
        Write-Host "✅ $extension instalado" -ForegroundColor Green
    } else {
        Write-Host "⚠️  $extension no instalado" -ForegroundColor Yellow
        Write-Host "   Instalando..." -ForegroundColor Gray
        code --install-extension $extension
    }
}

# Reiniciar configuración de terminal en VSCode
Write-Host "`n📋 Reiniciando configuración de terminal..." -ForegroundColor Yellow

# Crear script temporal para recargar VSCode
$reloadScript = @"
Write-Host "🔄 Para completar la configuración:" -ForegroundColor Cyan
Write-Host "1. Cierra todas las ventanas de VSCode" -ForegroundColor Yellow
Write-Host "2. Abre VSCode de nuevo" -ForegroundColor Yellow
Write-Host "3. Abre un terminal nuevo (Ctrl+Shift+`)" -ForegroundColor Yellow
Write-Host "4. Verifica que aparezca el indicador de shell integration" -ForegroundColor Yellow
Write-Host ""
Write-Host "✨ Si Cline sigue sin ver la salida, prueba:" -ForegroundColor Cyan
Write-Host "   - CMD/CTRL + Shift + P → 'Terminal: Select Default Profile'" -ForegroundColor Gray
Write-Host "   - Selecciona 'PowerShell'" -ForegroundColor Gray
Write-Host "   - CMD/CTRL + Shift + P → 'Developer: Reload Window'" -ForegroundColor Gray
"@

Invoke-Expression $reloadScript

Write-Host "`n🎉 Configuración completada!" -ForegroundColor Green
Write-Host "   El problema de shell integration de Cline debería estar resuelto." -ForegroundColor Gray
