# WAN2_2 telepítő – ComfyUI + Wan 2.2 + Stable Video Infinity 2.0 Pro
# Újraindítható: ami már megvan, azt kihagyja, a félbeszakadt letöltéseket folytatja.
# Használat: telepito.bat  (vagy: powershell -ExecutionPolicy Bypass -File telepito.ps1 [-NemKerdez])
param([switch]$NemKerdez)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ALAP = $PSScriptRoot
$LETOLTES = Join-Path $ALAP "_letoltes"
$MODELLEK = Join-Path $ALAP "_modellek"
$PORTABLE = Join-Path $ALAP "ComfyUI_windows_portable"
$PYTHON = Join-Path $PORTABLE "python_embeded\python.exe"
$NODES = Join-Path $PORTABLE "ComfyUI\custom_nodes"

$COMFY_VERZIO = "v0.46.0"
$COMFY_URL = "https://github.com/Comfy-Org/ComfyUI/releases/download/$COMFY_VERZIO/ComfyUI_windows_portable_nvidia.7z"
$CUSTOM_NODES = @(
    @{ Nev = "ComfyUI-GGUF";    Repo = "city96/ComfyUI-GGUF";   Commit = "6ea2651e7df66d7585f6ffee804b20e92fb38b8a" },
    @{ Nev = "ComfyUI-KJNodes"; Repo = "kijai/ComfyUI-KJNodes"; Commit = "aa2b5ea5e7f61b51f5d26d726f23c1d74e951016" }
)

function Cim($s)  { Write-Host ""; Write-Host "== $s ==" -ForegroundColor Cyan }
function Ok($s)   { Write-Host "  [OK] $s" -ForegroundColor Green }
function Info($s) { Write-Host "  $s" }
function Figy($s) { Write-Host "  [!] $s" -ForegroundColor Yellow }
function Kerdes($s) {
    if ($NemKerdez) { return $true }
    $v = Read-Host "  $s (i/n)"
    return ($v -match '^(i|y|igen|yes)?$')
}
function Letolt($url, $cel) {
    # curl.exe: a Windows 10/11 része; -C - = folytatás
    & curl.exe -L --fail --retry 5 --retry-delay 5 -C - -o $cel $url
    if ($LASTEXITCODE -ne 0) { throw "Sikertelen letöltés: $url" }
}

Write-Host "================================================================"
Write-Host "  WAN2_2 telepítő  –  hosszú videó helyi géppel"
Write-Host "================================================================"
New-Item -ItemType Directory -Force $LETOLTES, $MODELLEK | Out-Null

# ---------------------------------------------------------------- 1. gép
Cim "1. Gép ellenőrzése"
try {
    $gpu = (& nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits) -split ","
    $vram = [int]$gpu[1].Trim()
    Ok "GPU: $($gpu[0].Trim()), $([math]::Round($vram/1024)) GB VRAM"
    if ($vram -lt 11500) { Figy "12 GB-nál kevesebb VRAM: lassú lehet vagy elfogyhat a memória." }
} catch { Figy "Nem találok NVIDIA GPU-t (nvidia-smi). A program NVIDIA kártyát igényel." }
$meghajto = (Get-Item $ALAP).PSDrive
$szabad = [math]::Round($meghajto.Free / 1GB)
if ($szabad -lt 40) { Figy "Csak $szabad GB szabad hely van a $($meghajto.Name): meghajtón, kb. 40 GB kell." } else { Ok "$szabad GB szabad hely" }

# ---------------------------------------------------------------- 2. ComfyUI
Cim "2. ComfyUI ($COMFY_VERZIO, kb. 2 GB)"
if (Test-Path $PYTHON) {
    Ok "Már telepítve van."
} else {
    $sz = @("$env:ProgramFiles\7-Zip\7z.exe", "${env:ProgramFiles(x86)}\7-Zip\7z.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $sz) {
        $sz = Join-Path $LETOLTES "7zr.exe"
        if (-not (Test-Path $sz)) { Info "7-Zip kicsomagoló letöltése..."; Letolt "https://www.7-zip.org/a/7zr.exe" $sz }
    }
    $arch = Join-Path $LETOLTES "ComfyUI_windows_portable_nvidia.7z"
    Info "Letöltés: $COMFY_URL"
    Letolt $COMFY_URL $arch
    Info "Kicsomagolás..."
    & $sz x -y "-o$ALAP" $arch | Out-Null
    if (-not (Test-Path $PYTHON)) { throw "A kicsomagolás nem sikerült." }
    Ok "ComfyUI kész."
}

# ---------------------------------------------------------------- 3. custom node-ok
Cim "3. Kiegészítők (custom nodes)"
foreach ($n in $CUSTOM_NODES) {
    $cel = Join-Path $NODES $n.Nev
    if (Test-Path $cel) { Ok "$($n.Nev) már megvan."; continue }
    $zip = Join-Path $LETOLTES "$($n.Nev).zip"
    Info "$($n.Nev) letöltése ($($n.Commit.Substring(0,7)))..."
    Letolt "https://github.com/$($n.Repo)/archive/$($n.Commit).zip" $zip
    $tmp = Join-Path $LETOLTES "_kibont_$($n.Nev)"
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Expand-Archive -Path $zip -DestinationPath $tmp
    Move-Item (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName $cel
    Remove-Item -Recurse -Force $tmp
    $req = Join-Path $cel "requirements.txt"
    if (Test-Path $req) {
        Info "Python-csomagok telepítése..."
        & $PYTHON -s -m pip install -q --no-warn-script-location -r $req
        if ($LASTEXITCODE -ne 0) { throw "pip hiba: $($n.Nev)" }
    }
    Ok "$($n.Nev) kész."
}

# ---------------------------------------------------------------- 4. modellútvonal
Cim "4. Modellmappa beállítása"
$yaml = (Get-Content (Join-Path $ALAP "extra_model_paths.yaml.minta") -Raw -Encoding UTF8).Replace("{MODELLEK}", ($MODELLEK -replace '\\', '/'))
[IO.File]::WriteAllText((Join-Path $PORTABLE "ComfyUI\extra_model_paths.yaml"), $yaml, (New-Object Text.UTF8Encoding $false))
Ok "extra_model_paths.yaml -> $MODELLEK"

# ---------------------------------------------------------------- 5. modellek
Cim "5. Modellek (kb. 31 GB – ez a leghosszabb rész)"
$sorok = Get-Content (Join-Path $ALAP "modellek.txt") -Encoding UTF8 | Where-Object { $_ -match '\S' -and $_ -notmatch '^\s*#' }
$i = 0
foreach ($sor in $sorok) {
    $i++
    $alm, $meret, $url = $sor -split '\|' | ForEach-Object { $_.Trim() }
    $meret = [int64]$meret
    $nev = [IO.Path]::GetFileName($url)
    $dir = Join-Path $MODELLEK $alm
    New-Item -ItemType Directory -Force $dir | Out-Null
    $cel = Join-Path $dir $nev
    if ((Test-Path $cel) -and ((Get-Item $cel).Length -eq $meret)) { Ok "[$i/$($sorok.Count)] $nev megvan."; continue }
    Info "[$i/$($sorok.Count)] $nev ($([math]::Round($meret/1GB,1)) GB)"
    Letolt $url $cel
    if ((Get-Item $cel).Length -ne $meret) { throw "Hibás méret: $nev – futtasd újra a telepítőt." }
    Ok "$nev kész."
}

# ---------------------------------------------------------------- 6. ffmpeg
Cim "6. ffmpeg (a videó összefűzéséhez)"
if ((Get-Command ffmpeg -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $ALAP "ffmpeg\ffmpeg.exe"))) {
    Ok "ffmpeg megvan."
} elseif ((Get-Command winget -ErrorAction SilentlyContinue) -and (Kerdes "Nincs ffmpeg. Telepítsem a winget-tel?")) {
    & winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    Figy "Az ffmpeg a következő indítástól lesz elérhető (új ablakban)."
} else {
    Figy "Nincs ffmpeg. Telepítsd (winget install Gyan.FFmpeg), vagy tedd az ffmpeg.exe-t ide: $ALAP\ffmpeg\"
}

# ---------------------------------------------------------------- 7. Ollama (opcionális)
Cim "7. Ollama a promptíráshoz (nem kötelező)"
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    $lista = (& ollama list) -join "`n"
    if ($lista -match 'gemma4:12b') { Ok "gemma4:12b megvan." }
    elseif (Kerdes "Letöltsem a gemma4:12b modellt (kb. 7,6 GB) a promptíráshoz?") { & ollama pull gemma4:12b }
    else { Info "Kihagyva: a varázsló másik telepített modellt használ, vagy kézi promptot kér." }
} else {
    Info "Nincs Ollama. Nem baj: a varázsló ilyenkor kézzel kéri a promptokat."
    Info "Ha szeretnéd: https://ollama.com  majd: ollama pull gemma4:12b"
}

Cim "KÉSZ"
Info "Indítás: Video_keszito.bat (dupla kattintás)"
Info "Az ideiglenes _letoltes mappa törölhető."
