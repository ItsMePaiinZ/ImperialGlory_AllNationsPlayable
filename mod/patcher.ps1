<#
  Imperial Glory - All Nations Playable  v1.2.1
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
$ModMD5  = '9ab45eec3aadb5ebb04e736dc779a32e'   # expected result

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
    @(0x4695a, '8b8c2430020000', 'e9c1ac43009090'),  # VA 0x44695a
    @(0x481800, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '455350414e5941004c544558545f504149535f455350414e594100504f52545547414c004c544558545f504149535f504f52545547414c0045504150414c4553004c544558545f504149535f455f504150414c455300455f504150414c455300444f535f534943494c494153004c544558545f504149535f444f535f534943494c494153005049414d4f4e5445004c544558545f504149535f5049414d4f4e5445004c4f4d424152444941004c544558545f504149535f4c4f4d424152444941005248454c564554494341004c544558545f504149535f5248454c56455449434100525f48454c5645544943410042415441564941004c544558545f504149535f424154415649410048414e4e4f564552004c544558545f504149535f48414e4e4f5645520053414a4f4e4941004c544558545f504149535f53414a4f4e49410044494e414d41524341004c544558545f504149535f44494e414d4152434100535545434941004c544558545f504149535f53554543494100504f4c4f4e4941004c544558545f504149535f504f4c4f4e4941004d4f4c4441564941004c544558545f504149535f4d4f4c4441564941004f544f4d414e4f004c544558545f504149535f4f544f4d414e4f0045474950544f004c544558545f504149535f45474950544f004d4152525545434f53004c544558545f504149535f4d4152525545434f530054554e455a004c544558545f504149535f54554e455a00545249504f4c4954414e4941004c544558545f504149535f545249504f4c4954414e4941000018880088418c00081888001b18880088418c00241888003818880088418c00411888005618880088418c00411888006018880088418c006d1888008518880088418c008e188800a218880088418c00ac188800c118880088418c00cc188800e218880088418c00cc188800ee18880088418c00f61888000919880080418c00121988002619880080418c002e1988004119880080418c004b1988006019880080418c006719880079198800508c8b008119880094198800508c8b009d198800b119880078418c00b9198800cc19880078418c00d3198800e519880078418c00ef198800041a880078418c000a1a88001b1a880078418c00281a8800000000000000000000000000'),  # VA 0x881800
    @(0x481740, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '5356578b44241050e8c3e3caff83c40489c3c705402f940000000000be401a88008b0685c0743b50e893f0caff83c40489c750e818f1caff83c40439df740583c60cebdd8b4608a3402f940053e8fef0caff83c404ff7604e863f0caff83c40489c389d85f5e5bc3'),  # VA 0x881740
    @(0x4817b0, 'cccccccccccccccccccccccccccccccccccccccc', '50a1402f940085c074048944240858e93cf0caff'),  # VA 0x8817b0
    @(0x3d064f, 'e8bcf4d5ff', 'e8ec100b00'),  # VA 0x7d064f
    @(0x3d13d6, 'e835e7d5ff', 'e865030b00'),  # VA 0x7d13d6
    @(0x3d1fb4, 'e857dbd5ff', 'e887f70a00'),  # VA 0x7d1fb4
    @(0x3d5924, 'e8e7a1d5ff', 'e817be0a00'),  # VA 0x7d5924
    @(0x3d7844, 'e8c782d5ff', 'e8f79e0a00'),  # VA 0x7d7844
    @(0x3d0687, 'e87401d6ff', 'e824110b00'),  # VA 0x7d0687
    @(0x3d06f6, 'e80501d6ff', 'e8b5100b00'),  # VA 0x7d06f6
    @(0x3d0765, 'e89600d6ff', 'e846100b00'),  # VA 0x7d0765
    @(0x3d07d4, 'e82700d6ff', 'e8d70f0b00'),  # VA 0x7d07d4
    @(0x3d0843, 'e8b8ffd5ff', 'e8680f0b00'),  # VA 0x7d0843
    @(0x3d1fec, 'e80fe8d5ff', 'e8bff70a00'),  # VA 0x7d1fec
    @(0x3d205b, 'e8a0e7d5ff', 'e850f70a00'),  # VA 0x7d205b
    @(0x3d20ca, 'e831e7d5ff', 'e8e1f60a00'),  # VA 0x7d20ca
    @(0x3d2139, 'e8c2e6d5ff', 'e872f60a00'),  # VA 0x7d2139
    @(0x3d21a8, 'e853e6d5ff', 'e803f60a00'),  # VA 0x7d21a8
    @(0x3d595f, 'e89caed5ff', 'e84cbe0a00'),  # VA 0x7d595f
    @(0x3d59d2, 'e829aed5ff', 'e8d9bd0a00'),  # VA 0x7d59d2
    @(0x3d5a45, 'e8b6add5ff', 'e866bd0a00'),  # VA 0x7d5a45
    @(0x3d5ab8, 'e843add5ff', 'e8f3bc0a00'),  # VA 0x7d5ab8
    @(0x3d5b2b, 'e8d0acd5ff', 'e880bc0a00'),  # VA 0x7d5b2b
    @(0x3d787f, 'e87c8fd5ff', 'e82c9f0a00'),  # VA 0x7d787f
    @(0x3d78f2, 'e8098fd5ff', 'e8b99e0a00'),  # VA 0x7d78f2
    @(0x3d7965, 'e8968ed5ff', 'e8469e0a00'),  # VA 0x7d7965
    @(0x3d79d8, 'e8238ed5ff', 'e8d39d0a00'),  # VA 0x7d79d8
    @(0x3d7a4b, 'e8b08dd5ff', 'e8609d0a00'),  # VA 0x7d7a4b
    @(0x481b60, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '88418c0002000000508c8b000300000078418c000400000080418c00050000000000000000000000'),  # VA 0x881b60
    @(0x481da0, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '47616d655c55495c4d61696e4d656e755c54726f7061735c426f746f6e65735c506c616e74696c6c614172616265732e74676100'),  # VA 0x881da0
    @(0x481dd4, 'cccccccccccccccccccccccccccccccccccccccccccccccc', 'b1198800cc198800e5198800041a88001b1a880000000000'),  # VA 0x881dd4
    @(0x481e00, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '9c608b85140100008944241c83ec08894424048d4c2404518d542404528b85d80000008b48208b491883c128e8dfe5d3ff8b85d80000008b40208b40188b40308b0c2439c10f84b50000008b510c89d6bfd41d88008b0785c0745150e89fe9caff83c40489c350e824eacaff83c40439f3740583c704ebdd833d442f940000751268a01d8800e875e9caff83c404a3442f9400b8442f940029e82d74010000c1f8028944242483c408619dc389f252e88cf8ffff83c40489c6833d402f940000742fbf601b88008b0785c0742450e82de9caff83c40489c350e8b2e9caff83c40439f3740583c708ebdd8b47048944242456e899e9caff83c40483c408619dc383c408619dc3'),  # VA 0x881e00
    @(0x481f10, 'cccccccccccccccccccc', '50e8eafeffff89c158c3'),  # VA 0x881f10
    @(0x481f20, 'cccccccccccccccccccc', '50e8dafeffff89c258c3'),  # VA 0x881f20
    @(0x3d02b7, '8b8d14010000', 'e8541c0b0090'),  # VA 0x7d02b7
    @(0x3d02e3, '8b8514010000', 'e8181b0b0090'),  # VA 0x7d02e3
    @(0x3d0320, '8b9514010000', 'e8fb1b0b0090'),  # VA 0x7d0320
    @(0x481c70, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '0018880088418c00081888001b18880088418c00241888003818880088418c00411888005618880088418c00411888006018880088418c006d1888008518880088418c008e188800a218880088418c00ac188800c118880088418c00cc188800e218880088418c00cc188800ee18880088418c00f61888000919880080418c00121988002619880080418c002e1988004119880080418c004b1988006019880080418c006719880079198800508c8b008119880094198800508c8b009d198800000000000000000000000000'),  # VA 0x881c70
    @(0x481d40, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '5356578b44241050e8c3ddcaff83c40489c3be701c88008b0685c0743350e89deacaff83c40489c750e822ebcaff83c40439df740583c60cebdd53e810ebcaff83c404ff7604e875eacaff83c40489c389d85f5e5bc3'),  # VA 0x881d40
    @(0x3ce675, 'e89614d6ff', 'e8c6360b00'),  # VA 0x7ce675
    @(0x481480, 'cccccccccccccccccccccccccccccccccccccccc', '85c00f84b100f7ff8b1089c1ff527ce9a500f7ff'),  # VA 0x881480
    @(0x3f1532, '8b108bc8ff527c', 'e949ff08009090'),  # VA 0x7f1532
    @(0x4814a0, 'cccccccccccccccccccccccccccccccccccccc', '89c585c00f84f900f7ff8b0739d8e9ca00f7ff'),  # VA 0x8814a0
    @(0x3f1577, '8be88b073bc3', 'e924ff080090')  # VA 0x7f1577
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
Info '=== Imperial Glory - All Nations Playable  v1.2.1 ===' 'Cyan'
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
