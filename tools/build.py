#!/usr/bin/env python3
"""
Build Imperial Glory - All Nations Playable from source.

    python tools/build.py "C:/Program Files (x86)/Steam/steamapps/common/Imperial Glory/ImperialGlory.exe"

Produces in ./out:
    ImperialGlory_AllNations.exe   the patched exe (for testing; the release
                                   does NOT ship an exe, the user's own exe
                                   is patched by patcher.ps1 at install time)
    patches.json                   list of all byte changes
    patcher.ps1                    the installer script with the patch table
    ALLNATIONS.PAK                 the mod's data archive (built from ./pak)
    AllNations-Mod.zip             the release archive

and compares everything with the shipped files in ./mod.

Requirements: Python 3.8+, pip install keystone-engine pefile
"""
import hashlib, json, os, re, struct, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from patches import PATCHES, TURN_ORDER_NAMES, GREAT_POWER_STRINGS  # noqa: E402

import pefile                                           # noqa: E402
from keystone import Ks, KS_ARCH_X86, KS_MODE_32        # noqa: E402

ORIG_MD5 = "d2c8a4580bbcfb34a37dae3214b198ea"   # ImperialGlory.exe, Steam
OUT = os.path.join(ROOT, "out")
PAK_DATE = (2026, 10, 12, 12, 0, 0)             # fixed for reproducible builds


def md5(b):
    return hashlib.md5(b).hexdigest()


def assemble(ks, src, va):
    # Keystone uses ';' as a statement separator, so strip our comments first.
    lines = [ln.split(";", 1)[0].strip() for ln in src.strip().splitlines()]
    code = "\n".join(ln for ln in lines if ln)
    enc, _ = ks.asm(code, va)
    return bytes(enc)


def build_exe(exe_path):
    data = bytearray(open(exe_path, "rb").read())
    if md5(data) != ORIG_MD5:
        sys.exit(f"Unsupported ImperialGlory.exe (MD5 {md5(data)}), "
                 f"expected the Steam version {ORIG_MD5}.")
    pe = pefile.PE(data=bytes(data))
    off = lambda va: pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)

    # existing strings the new code points to must be where we expect them
    for va, name in TURN_ORDER_NAMES + [(v, n) for n, v in GREAT_POWER_STRINGS.items()]:
        o = off(va)
        assert data[o:o + len(name) + 1] == name.encode() + b"\0", (hex(va), name)
    table = b"".join(struct.pack("<I", va) for va, _ in TURN_ORDER_NAMES) + b"\0" * 4

    ks = Ks(KS_ARCH_X86, KS_MODE_32)
    out = []
    for p in PATCHES:
        va = p["va"]
        if "asm" in p:
            new = assemble(ks, p["asm"], va)
        elif p["data"] == "TURN_ORDER_TABLE":
            new = table
        else:
            new = p["data"]
        new += b"\x90" * p.get("pad", 0)
        o = off(va)
        old = bytes(data[o:o + len(new)])
        orig = p.get("orig")
        if "call_from" in p:           # original instruction: call <call_from>
            orig = "e8" + struct.pack("<i", p["call_from"] - (va + 5)).hex()
        if orig is None:
            assert old == b"\xcc" * len(new), f"{va:#x}: cave is not free"
        else:
            assert old == bytes.fromhex(orig), \
                f"{va:#x}: unexpected original bytes {old.hex()}"
        data[o:o + len(new)] = new
        out.append({"va": hex(va), "off": hex(o), "old": old.hex(),
                    "new": new.hex(), "desc": p["desc"]})
    return bytes(data), out


def build_patcher(patches, mod_md5):
    tpl = open(os.path.join(ROOT, "tools", "patcher_template.ps1"),
               "rb").read().decode("utf-8-sig")
    rows = [f"    @({p['off']}, '{p['old']}', '{p['new']}'),  # VA {p['va']}"
            for p in patches]
    rows[-1] = rows[-1].replace("'),  # VA", "')  # VA")   # no comma after last
    s = tpl.replace("{{PATCHES}}", "\r\n".join(rows)).replace("{{MOD_MD5}}", mod_md5)
    return b"\xef\xbb\xbf" + s.encode("utf-8")


def build_pak():
    pak_dir = os.path.join(ROOT, "pak")
    files = []
    for dp, _, fns in os.walk(pak_dir):
        for fn in fns:
            files.append(os.path.relpath(os.path.join(dp, fn), pak_dir).replace(os.sep, "/"))
    order = [  # same order as the release archive
        # v1.0 / v1.1: campaign
        "Game/GameModes/Gestion/DefOrdenTurnos.sb",
        "Game/UI/MainMenu/SelectEmpire/UIDefs_MapaPaisesSelectEmpire.sb",
        "Game/UI/ModeloGestion/Iconos/UIDefs_PoolIconosNotificaciones.sb",
        "Game/UI/MainMenu/UIDefs_SelectEmpire.sb",
        "Game/UI/MainMenu/SelectEmpire/UIDefs_ZSToolTips.sb",
        "Game/UI/MainMenu/SelectEmpire/UIDefs_Banderas.sb",
        # v1.2: custom battle
        "Game/UI/MainMenu/UIDefs_SelectArmyAutoBuy.sb",
        "Game/UI/MainMenu/UIDefs_SelectNavyAutoBuy.sb",
        "Game/UI/MainMenu/Tropas/Iconos/Genericos/UIDefs_PoolTropasIcons.sb",
        "Game/UI/MainMenu/UI_DefsSelectArmyButtons.sb",
        "Game/UI/MainMenu/Tropas/Botones/PlantillaArabes.tga",
    ]
    assert sorted(files) == sorted(order), files
    dirs = sorted({"/".join(f.split("/")[:i]) + "/" for f in order
                   for i in range(1, f.count("/") + 1)})
    path = os.path.join(OUT, "ALLNATIONS.PAK")
    with zipfile.ZipFile(path, "w") as z:
        for name in dirs + order:
            zi = zipfile.ZipInfo(name, date_time=PAK_DATE)
            zi.external_attr = 0o600 << 16
            zi.create_system = 3
            if name.endswith("/"):
                z.writestr(zi, b"")
            else:
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, open(os.path.join(pak_dir, name), "rb").read())
    return open(path, "rb").read()


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    os.makedirs(OUT, exist_ok=True)

    exe, patches = build_exe(sys.argv[1])
    open(os.path.join(OUT, "ImperialGlory_AllNations.exe"), "wb").write(exe)
    json.dump(patches, open(os.path.join(OUT, "patches.json"), "w"), indent=1)
    patcher = build_patcher(patches, md5(exe))
    open(os.path.join(OUT, "patcher.ps1"), "wb").write(patcher)
    pak = build_pak()

    with zipfile.ZipFile(os.path.join(OUT, "AllNations-Mod.zip"), "w",
                         zipfile.ZIP_DEFLATED) as z:
        for fn in ("Install.bat", "Uninstall.bat", "README.txt"):
            z.write(os.path.join(ROOT, "mod", fn), "AllNations-Mod/" + fn)
        z.write(os.path.join(OUT, "patcher.ps1"), "AllNations-Mod/patcher.ps1")
        z.write(os.path.join(OUT, "ALLNATIONS.PAK"), "AllNations-Mod/ALLNATIONS.PAK")

    print(f"{len(patches)} patches applied")
    print(f"ImperialGlory_AllNations.exe  MD5 {md5(exe)}")
    ok = True
    for fn, built in (("patcher.ps1", patcher), ("ALLNATIONS.PAK", pak)):
        shipped = open(os.path.join(ROOT, "mod", fn), "rb").read() \
            if os.path.exists(os.path.join(ROOT, "mod", fn)) else None
        same = shipped == built
        ok &= same
        print(f"{fn:<29} MD5 {md5(built)}  "
              f"{'identical to release' if same else 'DIFFERS from release'}")
    m = re.search(rb"\$ModMD5  = '([0-9a-f]{32})'",
                  open(os.path.join(ROOT, "mod", "patcher.ps1"), "rb").read())
    same = m and m.group(1).decode() == md5(exe)
    ok &= bool(same)
    print(f"exe MD5 matches the MD5 the release installer expects: {bool(same)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
