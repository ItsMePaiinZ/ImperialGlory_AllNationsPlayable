<#
  Imperial Glory - All Nations Playable  v1.3
  Patcher for the Steam version

  What this script does:
   - checks that ImperialGlory.exe is exactly the supported Steam version (MD5)
   - creates ImperialGlory_AllNations.exe from it (the original exe stays untouched)
   - copies ALLNATIONS.PAK into the game folder
   - optional: Windows 98/ME compatibility mode and a desktop shortcut
  Uninstalling removes exactly these things again.

  All byte changes are listed below in $Patches (file offset, old bytes, new bytes).
#>
param([ValidateSet('install','uninstall')][string]$Action = 'install')

$ErrorActionPreference = 'Stop'
$ModDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$GameDir   = Split-Path -Parent $ModDir
$OrigExe   = Join-Path $GameDir 'ImperialGlory.exe'
$ModExe    = Join-Path $GameDir 'ImperialGlory_AllNations.exe'
$PakSrc    = Join-Path $ModDir  'ALLNATIONS.PAK'
$PakDst    = Join-Path $GameDir 'ALLNATIONS.PAK'
$LinkName  = 'Imperial Glory - All Nations.lnk'
$CompatKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'

$OrigMD5 = 'd2c8a4580bbcfb34a37dae3214b198ea'   # ImperialGlory.exe, Steam version
$ModMD5  = '{{MOD_MD5}}'   # expected result

$Patches = @(
{{PATCHES}}
)

function Info([string]$msg, [string]$color = 'Gray') { Write-Host $msg -ForegroundColor $color }
function Fail([string]$msg) {
    Write-Host ''
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}
function HexToBytes([string]$hex) {
    $b = New-Object byte[] ($hex.Length / 2)
    for ($i = 0; $i -lt $b.Length; $i++) { $b[$i] = [Convert]::ToByte($hex.Substring($i * 2, 2), 16) }
    return ,$b
}
function Md5Hex([byte[]]$data) {
    $md5 = [System.Security.Cryptography.MD5]::Create()
    return ([BitConverter]::ToString($md5.ComputeHash($data)) -replace '-', '').ToLower()
}
function DesktopLink {
    $desk = [Environment]::GetFolderPath('Desktop')
    if ([string]::IsNullOrEmpty($desk)) { return $null }
    return (Join-Path $desk $LinkName)
}

Write-Host ''
Info '=== Imperial Glory - All Nations Playable  v1.3 ===' 'Cyan'
Write-Host ''

if ($Action -eq 'uninstall') {
    foreach ($f in @($ModExe, $PakDst, (DesktopLink))) {
        if ($f -and (Test-Path -LiteralPath $f)) {
            try { Remove-Item -LiteralPath $f -Force; Write-Host "  - $f" }
            catch { Fail "Could not delete $f. Is the game still running?" }
        }
    }
    try {
        if ((Get-ItemProperty -Path $CompatKey -Name $ModExe -ErrorAction SilentlyContinue) -ne $null) {
            Remove-ItemProperty -Path $CompatKey -Name $ModExe
            Write-Host '  - compatibility setting'
        }
    } catch { }
    Write-Host ''
    Info 'Uninstalled. The original game is untouched.' 'Green'
    Info 'You can now delete the AllNations-Mod folder.'
    exit 0
}

# ---------- Installation ----------
if (-not (Test-Path -LiteralPath $OrigExe)) {
    Fail "ImperialGlory.exe not found in: $GameDir`n  The AllNations-Mod folder must be placed directly inside the game folder (next to ImperialGlory.exe)."
}
if (-not (Test-Path -LiteralPath $PakSrc)) {
    Fail 'ALLNATIONS.PAK is missing from the mod folder. Please extract the whole archive.'
}

$data = [System.IO.File]::ReadAllBytes($OrigExe)
$md5 = Md5Hex $data
if ($md5 -ne $OrigMD5) {
    Fail "This ImperialGlory.exe is not supported (MD5 $md5).`n  The mod only works with the unmodified Steam version. Tip: use 'Verify integrity of game files' in Steam."
}
Info 'Steam version detected.' 'Green'

foreach ($p in $Patches) {
    $off = [int]$p[0]; $old = HexToBytes $p[1]; $new = HexToBytes $p[2]
    for ($i = 0; $i -lt $old.Length; $i++) {
        if ($data[$off + $i] -ne $old[$i]) { Fail ('Unexpected bytes at offset 0x{0:x}.' -f $off) }
    }
    [Array]::Copy($new, 0, $data, $off, $new.Length)
}
if ((Md5Hex $data) -ne $ModMD5) { Fail 'Checksum after patching does not match.' }

try {
    [System.IO.File]::WriteAllBytes($ModExe, $data)
    Copy-Item -LiteralPath $PakSrc -Destination $PakDst -Force
} catch {
    Fail "Could not write to the game folder. Is the game still running? Otherwise: right-click 'Install.bat' > Run as administrator. ($($_.Exception.Message))"
}
Info "Created ImperialGlory_AllNations.exe and ALLNATIONS.PAK ($($Patches.Count) patches)." 'Green'

Write-Host ''
Info 'Many players on Windows 10/11 need compatibility mode "Windows 98/ME",'
Info 'otherwise the game crashes after real-time battles.'
$ans = Read-Host 'Enable it for the mod exe? [Y/n]'
if ($ans -notmatch '^(n|no)$') {
    try {
        if (-not (Test-Path $CompatKey)) { New-Item -Path $CompatKey -Force | Out-Null }
        New-ItemProperty -Path $CompatKey -Name $ModExe -Value '~ WIN98' -PropertyType String -Force | Out-Null
        Info '  Compatibility mode set.' 'Green'
    } catch { Info '  Could not set compatibility mode (please set it manually).' 'Yellow' }
}

$ans = Read-Host 'Create a desktop shortcut? [Y/n]'
if ($ans -notmatch '^(n|no)$') {
    try {
        $link = DesktopLink
        if (-not $link) { throw 'no desktop' }
        $ws = New-Object -ComObject WScript.Shell
        $lnk = $ws.CreateShortcut($link)
        $lnk.TargetPath = $ModExe
        $lnk.WorkingDirectory = $GameDir
        $lnk.IconLocation = "$OrigExe,0"
        $lnk.Save()
        Info '  Shortcut created.' 'Green'
    } catch { Info '  Could not create a shortcut.' 'Yellow' }
}

Write-Host ''
Info 'Done! Start the game via ImperialGlory_AllNations.exe (or the shortcut).' 'Cyan'
Info 'Starting through Steam / ImperialGlory.exe still runs the unmodified original game.'
exit 0
