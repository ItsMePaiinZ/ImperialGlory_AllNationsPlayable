<#
  Imperial Glory - All Nations Playable  v1.1
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
$ModMD5  = 'c0f421a34b57ebb35cf60b93970da764'   # expected result

$Patches = @(
    @(0x3ca03d, '7444', '9090'),  # VA 0x7ca03d
    @(0x480f00, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '8b54241033db3b56300f843ef7e3ff8b42148b283be80f8431f7e3ffe916f5e3ff'),  # VA 0x880f00
    @(0x2c0424, '8b5424108b42148b2833db3be80f8416020000', 'e9d70a1c009090909090909090909090909090'),  # VA 0x6c0424
    @(0x480f40, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '8b5424083b56300f847af8e3ff8b42148b183bd80f846df8e3ffe903f8e3ff'),  # VA 0x880f40
    @(0x2c0755, '8b5424088b42148b183bd87465', 'e9e6071c009090909090909090'),  # VA 0x6c0755
    @(0x481100, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '5356575589cf8b6c2414bb0012880083ec048b0385c0742e50e8e2f6caff83c404890424558d4424045089f9e89ff9e3ff8b042485c0740950e852f7caff83c40483c304ebcc83c404b0015d5f5e5bc20400'),  # VA 0x881100
    @(0x481200, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '1c458c0010458c00e4448c0004458c0064d08c00f0d08c00e4d08c00a0d08c002cd08c0020d08c003cd08c0070d08c0080d08c0090d08c0010d08c0008d18c0058d08c00fcd08c004cd08c0000d08c00b4d08c00c4d08c00d0d08c00f0448c0000000000'),  # VA 0x881200
    @(0x2c0d30, '83ec185356', 'e9cb031c00'),  # VA 0x6c0d30
    @(0x481340, 'cccccccccccccccccccccccccccccccccccccccccccccccccccc', 'c605002f940001ff742404e88022d5ffc605002f940000c20400'),  # VA 0x881340
    @(0x1d34c7, 'c644241300eb09', 'e9b4de2a009090'),  # VA 0x5d34c7
    @(0x3ca24d, 'e87e91e0ff', 'e8ae700b00'),  # VA 0x7ca24d
    @(0x3ca678, 'e8538de0ff', 'e8836c0b00'),  # VA 0x7ca678
    @(0x3cac07, 'e8c487e0ff', 'e8f4660b00'),  # VA 0x7cac07
    @(0x3ca036, 'e89595e0ff', 'e805730b00'),  # VA 0x7ca036
    @(0x4813c0, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '565789cf8b77243b772874228b0ee8dd31dbff84c0750583c604ebeb8b06c680f9000000018b80f40000005f5ec331c05f5ec3'),  # VA 0x8813c0
    @(0x2c03fb, 'e850aaf9ff', 'e8c00f1c00'),  # VA 0x6c03fb
    @(0x481420, 'cccccccccccccccccccccccccccccccccccccccccc', '85c00f848300f7ff5089f1e8b070cdffe96dfcf6ff'),  # VA 0x881420
    @(0x3f109a, '508bcee83e74d6ff', 'e981030900909090'),  # VA 0x7f109a
    @(0x481460, 'cccccccccccccccccccccccccccccccccccccccccc', '85c00f84abfbf6ff5089f1e87070cdffe94dfbf6ff'),  # VA 0x881460
    @(0x3f0fba, '508bcee81e75d6ff', 'e9a1040900909090'),  # VA 0x7f0fba
    @(0x481300, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '5689cec605002f940002ff74240889f1e8bb20d5ffc605002f940003ff74240889f1e8a920d5ffc605002f9400005ec20400'),  # VA 0x881300
    @(0x481380, 'cccccccccccccccccccccccccccccccccccc', '50a0002f940024018844241758e94521d5ff'),  # VA 0x881380
    @(0x4816a0, 'cccccccccccccccccccccccccccccccccccccccccc', '50a0002f94003c030f95c08844241758e9221ed5ff'),  # VA 0x8816a0
    @(0x1d34d2, 'c644241301', 'e9c9e12a00'),  # VA 0x5d34d2
    @(0x4816e0, 'cccccccccccccccccccccccccccccccccccc', '528b54241883fa057c0383c2320fafca5ac3'),  # VA 0x8816e0
    @(0x481700, 'cccccccccccccccccccccccccccccccccccc', '508b44241883f8057c0383c0320fafd058c3'),  # VA 0x881700
    @(0x481720, 'cccccccccccccccccccccccccccccccccc', '8b4c247c8b7c241483ff057c0383c732c3'),  # VA 0x881720
    @(0x3cafca, '0faf4c2410', 'e811670b00'),  # VA 0x7cafca
    @(0x3cb0a6, '0faf4c2410', 'e835660b00'),  # VA 0x7cb0a6
    @(0x3cb182, '0faf4c2410', 'e859650b00'),  # VA 0x7cb182
    @(0x3cb51b, '0faf4c2410', 'e8c0610b00'),  # VA 0x7cb51b
    @(0x3cb66e, '0faf4c2410', 'e86d600b00'),  # VA 0x7cb66e
    @(0x3cb6a7, '0faf542410', 'e854600b00'),  # VA 0x7cb6a7
    @(0x3cb2b1, '8b4c24788b7c2410', 'e86a640b00909090'),  # VA 0x7cb2b1
    @(0x481600, 'cccccccccccccccccccccccccccccc', '414c4c4e4154494f4e532e50414b00'),  # VA 0x881600
    @(0x481620, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '6a0e68001688008d4c2418e86000b8ff8d44241050e8b64bbcff83c404837c24281072228b4c241451e87b46b8ff83c404c74424280f000000c744242400000000c6442414008b8c2430020000e9ef52bcff'),  # VA 0x881620
    @(0x4695a, '8b8c2430020000', 'e9c1ac43009090')  # VA 0x44695a
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
Info '=== Imperial Glory - All Nations Playable  v1.1 ===' 'Cyan'
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
