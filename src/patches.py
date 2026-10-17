"""
Imperial Glory - All Nations Playable v1.2.1
Source of every change made to ImperialGlory.exe (Steam version).

Target: ImperialGlory.exe, Steam, MD5 d2c8a4580bbcfb34a37dae3214b198ea
        32-bit PE, image base 0x400000, no ASLR, so all addresses are fixed.

Each entry is one patch:
    va      virtual address in the exe
    orig    the bytes that must be there before patching (hex).
            None = an unused code cave filled with 0xCC (int3) padding.
    asm     x86 assembly (Intel syntax, assembled with Keystone at `va`)
    data    raw bytes instead of asm (tables, strings)
    pad     number of NOP bytes appended (to fill the rest of a replaced
            instruction so no partial instruction is left behind)
    desc    what the patch does

New code is placed in the unused 0xCC padding at the end of the .text
section (0x880F00 - 0x882000). One byte of unused .data space is used as
a flag: 0x942F00 (FLAG), which tells the nation-list builder which
nations to include (see section 3).

Names of game functions used below (from our own analysis):
    0x530800  intern a string -> string id      (cdecl, 1 arg)
    0x530890  release a string id               (cdecl, 1 arg)
    0x52fb10  add a reference to a string id      (cdecl, 1 arg, returns id)
    0x5c0410  std::map::find                      (thiscall, &result, &key)
    0x5d33d0  build the list of selectable nations (thiscall, 1 arg)
    0x5d35d0  "is this nation selectable?"       (thiscall, 1 arg)
    0x6c0ad0  load the turn-order section of one nation (thiscall, 2 args)
    0x6345b0  "is this player human?"            (thiscall)
    0x65ae50  get the human player's empire       (thiscall)
    0x5584e0  great-power progress panel: add one entry (thiscall, 1 arg)
    0x401690  std::string assign(char*, len)
    0x4461f0  open/mount a .PAK file
    0x405cc9  operator delete
"""

FLAG = 0x942F00

PATCHES_V11 = [
    # ------------------------------------------------------------------
    # 1. Selection menu: the "selectable nation" check no longer rejects
    #    minor nations (original: je 0x7ca083 after the check).
    # ------------------------------------------------------------------
    dict(va=0x7CA03D, orig="7444", asm="nop\nnop",
         desc="Selection menu: do not skip nations that fail the "
              "hard-coded great-power check."),

    # ------------------------------------------------------------------
    # 2. Quest map lookups: the game looks up the human player in a map of
    #    quests that only contains the five great powers. For a minor
    #    nation the lookup returned the end() node and the game read
    #    garbage. These two guards check for end()/empty and skip safely.
    # ------------------------------------------------------------------
    dict(va=0x880F00, orig=None,
         asm="""
            mov edx, dword ptr [esp+0x10]
            .byte 0x33, 0xdb            ; xor ebx, ebx   (original encoding)
            cmp edx, dword ptr [esi+0x30]   ; == map end() ?
            je 0x6c064d                     ; -> not found, skip
            mov eax, dword ptr [edx+0x14]
            mov ebp, dword ptr [eax]
            .byte 0x3b, 0xe8            ; cmp ebp, eax   (empty list?)
            je 0x6c064d                     ; -> empty, skip
            jmp 0x6c0437                    ; continue original code
         """,
         desc="Quest lookup guard #1 (cave)."),
    dict(va=0x6C0424, orig="8b5424108b42148b2833db3be80f8416020000",
         asm="jmp 0x880f00", pad=14,
         desc="Quest lookup guard #1: jump into the cave."),

    dict(va=0x880F40, orig=None,
         asm="""
            mov edx, dword ptr [esp+8]
            cmp edx, dword ptr [esi+0x30]   ; == map end() ?
            je 0x6c07c7
            mov eax, dword ptr [edx+0x14]
            mov ebx, dword ptr [eax]
            .byte 0x3b, 0xd8            ; cmp ebx, eax   (empty list?)
            je 0x6c07c7
            jmp 0x6c0762
         """,
         desc="Quest lookup guard #2 (cave)."),
    dict(va=0x6C0755, orig="8b5424088b42148b183bd87465",
         asm="jmp 0x880f40", pad=8,
         desc="Quest lookup guard #2: jump into the cave."),

    # ------------------------------------------------------------------
    # 3. Turn order: originally only the sections of the five great
    #    powers were loaded from DefOrdenTurnos.sb; starting a campaign as
    #    a minor nation crashed. The replacement loads the section of
    #    every nation in TABLE. Sections that do not exist are skipped by
    #    the game's own loader (0x6c0ad0).
    # ------------------------------------------------------------------
    dict(va=0x881100, orig=None,
         asm="""
            push ebx
            push esi
            push edi
            push ebp
            mov edi, ecx                    ; this
            mov ebp, dword ptr [esp+0x14]   ; argument
            mov ebx, 0x881200               ; TABLE of nation names
            sub esp, 4                      ; local: string id
        next:
            mov eax, dword ptr [ebx]
            test eax, eax
            jz done                         ; end of table
            push eax
            call 0x530800                   ; id = intern(name)
            add esp, 4
            mov dword ptr [esp], eax
            push ebp
            lea eax, [esp+4]
            push eax
            mov ecx, edi
            call 0x6c0ad0                   ; load section for this nation
            mov eax, dword ptr [esp]
            test eax, eax
            jz skip
            push eax
            call 0x530890                   ; release(id)
            add esp, 4
        skip:
            add ebx, 4
            jmp next
        done:
            add esp, 4
            mov al, 1                       ; success
            pop ebp
            pop edi
            pop esi
            pop ebx
            ret 4
         """,
         desc="Turn order: load sections for all 24 nations (cave)."),
    dict(va=0x881200, orig=None,
         data="TURN_ORDER_TABLE",          # built below from TURN_ORDER_NAMES
         desc="Turn order: table of pointers to the game's own nation-name "
              "strings (JUG_*), zero-terminated."),
    dict(va=0x6C0D30, orig="83ec185356",
         asm="jmp 0x881100",
         desc="Turn order: replace the original five-nation loader."),

    # ------------------------------------------------------------------
    # 4. Selection menu, part 1: wrapper that sets FLAG=1 ("include all
    #    nations") around the selectable-nation check 0x5d35d0.
    # ------------------------------------------------------------------
    dict(va=0x881340, orig=None,
         asm=f"""
            mov byte ptr [{FLAG:#x}], 1
            push dword ptr [esp+4]
            call 0x5d35d0
            mov byte ptr [{FLAG:#x}], 0
            ret 4
         """,
         desc="Selectable-nation check with FLAG=1 (cave)."),
    dict(va=0x5D34C7, orig="c644241300eb09",
         asm="jmp 0x881380", pad=2,
         desc="List builder, minor-nation branch: decide via FLAG "
              "(see 0x881380) instead of always excluding."),
    dict(va=0x7CA24D, orig="e87e91e0ff", asm="call 0x881300",
         desc="Selection menu: build the nation list in two passes "
              "(0x881300) instead of calling 0x5d33d0 directly."),
    dict(va=0x7CA678, orig="e8538de0ff", asm="call 0x881300",
         desc="Same, second call site."),
    dict(va=0x7CAC07, orig="e8c487e0ff", asm="call 0x881300",
         desc="Same, third call site."),
    dict(va=0x7CA036, orig="e89595e0ff", asm="call 0x881340",
         desc="Selection menu: use the FLAG=1 wrapper for the "
              "selectable-nation check."),

    # ------------------------------------------------------------------
    # 5. The human player is treated as a great power. The original
    #    function 0x65ae50 returned no empire for a human minor nation,
    #    so conquest, permanent occupation and annexation did not work.
    #    The replacement finds the human player, marks it as a great
    #    power (byte at +0xF9) and returns its empire (+0xF4).
    # ------------------------------------------------------------------
    dict(va=0x8813C0, orig=None,
         asm="""
            push esi
            push edi
            mov edi, ecx
            mov esi, dword ptr [edi+0x24]   ; players.begin()
        loop1:
            cmp esi, dword ptr [edi+0x28]   ; players.end()
            je none
            mov ecx, dword ptr [esi]
            call 0x6345b0                   ; is human?
            test al, al
            jnz found
            add esi, 4
            jmp loop1
        found:
            mov eax, dword ptr [esi]
            mov byte ptr [eax+0xf9], 1      ; treat as great power
            mov eax, dword ptr [eax+0xf4]   ; return empire
            pop edi
            pop esi
            ret
        none:
            xor eax, eax
            pop edi
            pop esi
            ret
         """,
         desc="Find the human player and treat it as a great power (cave)."),
    dict(va=0x6C03FB, orig="e850aaf9ff", asm="call 0x8813c0",
         desc="Use the function above instead of 0x65ae50."),

    # ------------------------------------------------------------------
    # 6. Great-power progress panel: null checks. The panel expects an
    #    entry for each great power; with a human minor nation one of the
    #    pointers can be NULL. Skip the entry instead of crashing.
    # ------------------------------------------------------------------
    dict(va=0x881420, orig=None,
         asm="""
            test eax, eax
            jz 0x7f14ab                     ; NULL -> skip entry
            push eax
            mov ecx, esi
            call 0x5584e0                   ; original call
            jmp 0x7f10a2
         """,
         desc="Progress panel null check #1 (cave)."),
    dict(va=0x7F109A, orig="508bcee83e74d6ff",
         asm="jmp 0x881420", pad=3,
         desc="Progress panel null check #1: jump into the cave."),
    dict(va=0x881460, orig=None,
         asm="""
            test eax, eax
            jz 0x7f1013
            push eax
            mov ecx, esi
            call 0x5584e0
            jmp 0x7f0fc2
         """,
         desc="Progress panel null check #2 (cave)."),
    dict(va=0x7F0FBA, orig="508bcee81e75d6ff",
         asm="jmp 0x881460", pad=3,
         desc="Progress panel null check #2: jump into the cave."),

    # ------------------------------------------------------------------
    # 7. Selection menu, part 2 (v1.1): the list on the right side has
    #    room for five entries. The list is built in two passes: first the
    #    five great powers (FLAG=2), then the minor nations (FLAG=3). The
    #    minor-nation rows (index >= 5) are moved off-screen (helpers HA,
    #    HB, HC) so the list no longer covers the OK button. Minor nations
    #    are selected by clicking them on the map.
    # ------------------------------------------------------------------
    dict(va=0x881300, orig=None,
         asm=f"""
            push esi
            mov esi, ecx
            mov byte ptr [{FLAG:#x}], 2     ; pass 1: great powers
            push dword ptr [esp+8]
            mov ecx, esi
            call 0x5d33d0
            mov byte ptr [{FLAG:#x}], 3     ; pass 2: minor nations
            push dword ptr [esp+8]
            mov ecx, esi
            call 0x5d33d0
            mov byte ptr [{FLAG:#x}], 0
            pop esi
            ret 4
         """,
         desc="Two-pass nation list builder (cave)."),
    dict(va=0x881380, orig=None,
         asm=f"""
            push eax
            mov al, byte ptr [{FLAG:#x}]
            and al, 1                       ; include if FLAG is 1 or 3
            mov byte ptr [esp+0x17], al     ; = original local [esp+0x13]
            pop eax
            jmp 0x5d34d7
         """,
         desc="Minor-nation branch of the list builder (cave)."),
    dict(va=0x8816A0, orig=None,
         asm=f"""
            push eax
            mov al, byte ptr [{FLAG:#x}]
            cmp al, 3
            setne al                        ; exclude great powers in pass 2
            mov byte ptr [esp+0x17], al
            pop eax
            jmp 0x5d34d7
         """,
         desc="Great-power branch of the list builder (cave)."),
    dict(va=0x5D34D2, orig="c644241301", asm="jmp 0x8816a0",
         desc="Great-power branch: decide via FLAG."),
    dict(va=0x8816E0, orig=None,
         asm="""
            push edx
            mov edx, dword ptr [esp+0x18]   ; row index
            cmp edx, 5
            jl keep
            add edx, 50                     ; rows >= 5: far below the screen
        keep:
            imul ecx, edx                   ; original: imul ecx,[esp+0x10]
            pop edx
            ret
         """,
         desc="Row position helper HA (cave)."),
    dict(va=0x881700, orig=None,
         asm="""
            push eax
            mov eax, dword ptr [esp+0x18]
            cmp eax, 5
            jl keep
            add eax, 50
        keep:
            imul edx, eax                   ; original: imul edx,[esp+0x10]
            pop eax
            ret
         """,
         desc="Row position helper HB (cave)."),
    dict(va=0x881720, orig=None,
         asm="""
            mov ecx, dword ptr [esp+0x7c]   ; original: mov ecx,[esp+0x78]
            mov edi, dword ptr [esp+0x14]   ; original: mov edi,[esp+0x10]
            cmp edi, 5
            jl keep
            add edi, 50
        keep:
            ret
         """,
         desc="Row position helper HC (cave)."),
    dict(va=0x7CAFCA, orig="0faf4c2410", asm="call 0x8816e0", desc="Row helper HA, site 1."),
    dict(va=0x7CB0A6, orig="0faf4c2410", asm="call 0x8816e0", desc="Row helper HA, site 2."),
    dict(va=0x7CB182, orig="0faf4c2410", asm="call 0x8816e0", desc="Row helper HA, site 3."),
    dict(va=0x7CB51B, orig="0faf4c2410", asm="call 0x8816e0", desc="Row helper HA, site 4."),
    dict(va=0x7CB66E, orig="0faf4c2410", asm="call 0x8816e0", desc="Row helper HA, site 5."),
    dict(va=0x7CB6A7, orig="0faf542410", asm="call 0x881700", desc="Row helper HB."),
    dict(va=0x7CB2B1, orig="8b4c24788b7c2410", asm="call 0x881720", pad=3,
         desc="Row helper HC."),

    # ------------------------------------------------------------------
    # 8. Load ALLNATIONS.PAK after the game's own .PAK files, so the
    #    modified data files in it take precedence.
    # ------------------------------------------------------------------
    dict(va=0x881600, orig=None, data=b"ALLNATIONS.PAK\x00",
         desc="File name of the mod's data archive."),
    dict(va=0x881620, orig=None,
         asm="""
            push 14                         ; strlen("ALLNATIONS.PAK")
            push 0x881600
            lea ecx, [esp+0x18]             ; reuse the loader's std::string
            call 0x401690                   ; str.assign(name, 14)
            lea eax, [esp+0x10]
            push eax
            call 0x4461f0                   ; mount the .PAK
            add esp, 4
            cmp dword ptr [esp+0x28], 0x10  ; heap buffer? (MSVC SSO)
            jb nofree
            mov ecx, dword ptr [esp+0x14]
            push ecx
            call 0x405cc9                   ; free it
            add esp, 4
            mov dword ptr [esp+0x28], 0xf   ; reset string to empty
            mov dword ptr [esp+0x24], 0
            mov byte ptr [esp+0x14], 0
        nofree:
            mov ecx, dword ptr [esp+0x230]  ; original instruction
            jmp 0x446961                    ; back to the game
         """,
         desc="Mount ALLNATIONS.PAK at the end of the game's PAK loader (cave)."),
    dict(va=0x44695A, orig="8b8c2430020000", asm="jmp 0x881620", pad=2,
         desc="PAK loader: jump into the cave."),
]

# Nation names whose turn-order sections are loaded (patch 3). These are
# addresses of strings that already exist in the original exe; build.py
# checks that each address really holds the expected name.
TURN_ORDER_NAMES = [
    (0x8C451C, "JUG_GRAN_BRETANYA"), (0x8C4510, "JUG_FRANCIA"),
    (0x8C44E4, "JUG_AUSTRIA"),       (0x8C4504, "JUG_PRUSIA"),
    (0x8CD064, "JUG_ESPANYA"),       (0x8CD0F0, "JUG_OTOMANO"),
    (0x8CD0E4, "JUG_EGIPTO"),        (0x8CD0A0, "JUG_DOS_SICILIAS"),
    (0x8CD02C, "JUG_DINAMARCA"),     (0x8CD020, "JUG_SUECIA"),
    (0x8CD03C, "JUG_PORTUGAL"),      (0x8CD070, "JUG_LOMBARDIA"),
    (0x8CD080, "JUG_PIAMONTE"),      (0x8CD090, "JUG_EPAPALES"),
    (0x8CD010, "JUG_RHELVETICA"),    (0x8CD108, "JUG_HANNOVER"),
    (0x8CD058, "JUG_BATAVIA"),       (0x8CD0FC, "JUG_SAJONIA"),
    (0x8CD04C, "JUG_POLONIA"),       (0x8CD000, "JUG_MOLDAVIA"),
    (0x8CD0B4, "JUG_MARRUECOS"),     (0x8CD0C4, "JUG_TUNEZ"),
    (0x8CD0D0, "JUG_TRIPOLITANIA"),  (0x8C44F0, "JUG_RUSIA"),
]


# ======================================================================
#  v1.2 - Custom Battle with all nations
# ======================================================================
#
# The custom battle screens (army and navy) only know the five great
# powers: the header text, the unit buttons, the unit icons and the
# auto-buy lists are all chosen by comparing the nation's name with
# AUSTRIA / RUSIA / PRUSIA / FRANCIA / GRAN_BRETANYA. For any other
# nation they showed "FRANCIA", white placeholder pictures, and no unit
# could be bought.
#
# Approach: every minor nation gets an "alias" great power whose screen
# layout it uses (ALIAS_TABLE below). The real nation name is kept for
# the header text (LTEXT_PAIS_*). The five Arab nations do not use an
# alias for their unit pictures: they get their own button template
# (PlantillaArabes.tga) and their own icons, both in ALLNATIONS.PAK.
#
# Two more bytes of unused .data are used:
G_LTEXT   = 0x942F40   # LTEXT key of the selected minor nation, 0 = great power
G_ARABTGA = 0x942F44   # string id of PlantillaArabes.tga, created on first use

# Name strings of the great powers that already exist in the exe
# (checked by build.py before patching).
GREAT_POWER_STRINGS = {
    "FRANCIA": 0x8C4188, "PRUSIA": 0x8C4180,
    "AUSTRIA": 0x8B8C50, "RUSIA": 0x8C4178,
}

# (name used by the game, alias great power, header text key)
ALIAS_TABLE = [
    ("ESPANYA",      "FRANCIA", "LTEXT_PAIS_ESPANYA"),
    ("PORTUGAL",     "FRANCIA", "LTEXT_PAIS_PORTUGAL"),
    ("EPAPALES",     "FRANCIA", "LTEXT_PAIS_E_PAPALES"),
    ("E_PAPALES",    "FRANCIA", "LTEXT_PAIS_E_PAPALES"),
    ("DOS_SICILIAS", "FRANCIA", "LTEXT_PAIS_DOS_SICILIAS"),
    ("PIAMONTE",     "FRANCIA", "LTEXT_PAIS_PIAMONTE"),
    ("LOMBARDIA",    "FRANCIA", "LTEXT_PAIS_LOMBARDIA"),
    ("RHELVETICA",   "FRANCIA", "LTEXT_PAIS_RHELVETICA"),
    ("R_HELVETICA",  "FRANCIA", "LTEXT_PAIS_RHELVETICA"),
    ("BATAVIA",      "FRANCIA", "LTEXT_PAIS_BATAVIA"),
    ("HANNOVER",     "PRUSIA",  "LTEXT_PAIS_HANNOVER"),
    ("SAJONIA",      "PRUSIA",  "LTEXT_PAIS_SAJONIA"),
    ("DINAMARCA",    "PRUSIA",  "LTEXT_PAIS_DINAMARCA"),
    ("SUECIA",       "PRUSIA",  "LTEXT_PAIS_SUECIA"),
    ("POLONIA",      "AUSTRIA", "LTEXT_PAIS_POLONIA"),
    ("MOLDAVIA",     "AUSTRIA", "LTEXT_PAIS_MOLDAVIA"),
    ("OTOMANO",      "RUSIA",   "LTEXT_PAIS_OTOMANO"),
    ("EGIPTO",       "RUSIA",   "LTEXT_PAIS_EGIPTO"),
    ("MARRUECOS",    "RUSIA",   "LTEXT_PAIS_MARRUECOS"),
    ("TUNEZ",        "RUSIA",   "LTEXT_PAIS_TUNEZ"),
    ("TRIPOLITANIA", "RUSIA",   "LTEXT_PAIS_TRIPOLITANIA"),
]
ARAB_NATIONS = ["OTOMANO", "EGIPTO", "MARRUECOS", "TUNEZ", "TRIPOLITANIA"]


def _u32(*vals):
    import struct
    return b"".join(struct.pack("<I", v) for v in vals)


# --- string pool + ALIAS_TABLE at 0x881800 ---------------------------
STR_BASE = 0x881800
_blob, _addr = bytearray(), {}


def _s(text):
    if text not in _addr:
        _addr[text] = STR_BASE + len(_blob)
        _blob.extend(text.encode() + b"\0")
    return _addr[text]


_rows = [(_s(n), GREAT_POWER_STRINGS[gp], _s(lt)) for n, gp, lt in ALIAS_TABLE]
while len(_blob) % 4:
    _blob.append(0)
TBL = STR_BASE + len(_blob)                     # 3 pointers per row, 0-row ends it
_table = b"".join(_u32(*r) for r in _rows) + _u32(0, 0, 0)
STR_AND_TABLE = bytes(_blob) + _table

# --- same table without the Arab nations (for the unit icons) --------
TBL2 = 0x881C70
TABLE_NO_ARAB = b"".join(_u32(*r) for (n, _, _), r in zip(ALIAS_TABLE, _rows)
                         if n not in ARAB_NATIONS) + _u32(0, 0, 0)

# --- great power -> index of its button template (1 GB, 2 FR, 3 AT, 4 RU, 5 PR)
GPTAB = 0x881B60
GP_INDEX = _u32(GREAT_POWER_STRINGS["FRANCIA"], 2, GREAT_POWER_STRINGS["AUSTRIA"], 3,
                GREAT_POWER_STRINGS["RUSIA"], 4, GREAT_POWER_STRINGS["PRUSIA"], 5, 0, 0)

APATH = 0x881DA0
ARAB_TGA = b"Game\\UI\\MainMenu\\Tropas\\Botones\\PlantillaArabes.tga\0"
ARABTAB = 0x881DD4
ARAB_LIST = _u32(*[_addr[n] for n in ARAB_NATIONS], 0)

ALIAS, HSWAP, ALIAS2 = 0x881740, 0x8817B0, 0x881D40
CORE, GIC, GID = 0x881E00, 0x881F10, 0x881F20

# Lookup loop shared by ALIAS and ALIAS2: compare the string id in ebx
# with every name in the table at esi; on a hit, replace ebx by the id
# of the alias great power.
_ALIAS_BODY = """
            push ebx
            push esi
            push edi
            mov eax, dword ptr [esp+0x10]   ; argument: nation name id
            push eax
            call 0x52fb10                   ; take a reference (as the original call did)
            add esp, 4
            mov ebx, eax
            {reset}
            mov esi, {table:#x}
        next:
            mov eax, dword ptr [esi]        ; row: name, alias, ltext
            test eax, eax
            je done
            push eax
            call 0x530800                   ; id of the row's name
            add esp, 4
            mov edi, eax
            push eax
            call 0x530890                   ; release it again
            add esp, 4
            cmp edi, ebx
            je hit
            add esi, 12
            jmp next
        hit:
            {store}
            push ebx
            call 0x530890                   ; drop the minor nation's id
            add esp, 4
            push dword ptr [esi+4]
            call 0x530800                   ; id of the alias great power
            add esp, 4
            mov ebx, eax
        done:
            mov eax, ebx                    ; return (referenced) id
            pop edi
            pop esi
            pop ebx
            ret
"""

PATCHES_V12 = [
    # ------------------------------------------------------------------
    # 9. Header text and screen layout of the custom battle screens.
    # ------------------------------------------------------------------
    dict(va=STR_BASE, orig=None, data=STR_AND_TABLE,
         desc="Nation names, LTEXT keys and ALIAS_TABLE."),
    dict(va=ALIAS, orig=None,
         asm=_ALIAS_BODY.format(
             table=TBL,
             reset=f"mov dword ptr [{G_LTEXT:#x}], 0      ; assume great power",
             store=f"mov eax, dword ptr [esi+8]\n"
                   f"            mov dword ptr [{G_LTEXT:#x}], eax  ; remember header text"),
         desc="ALIAS: minor nation -> alias great power, remembers its "
              "header text in G_LTEXT (cave)."),
    dict(va=HSWAP, orig=None,
         asm=f"""
            push eax
            mov eax, dword ptr [{G_LTEXT:#x}]
            test eax, eax
            je keep                         ; great power: unchanged
            mov dword ptr [esp+8], eax      ; minor: use LTEXT_PAIS_<nation>
        keep:
            pop eax
            jmp 0x530800                    ; original call: intern(string)
         """,
         desc="HSWAP: swaps the header text key for minor nations (cave)."),
] + [
    dict(va=va, asm=f"call {ALIAS:#x}", call_from=0x52FB10,
         desc="Custom battle screen: resolve the nation through ALIAS.")
    for va in (0x7D064F, 0x7D13D6, 0x7D1FB4, 0x7D5924, 0x7D7844)
] + [
    dict(va=va, asm=f"call {HSWAP:#x}", call_from=0x530800,
         desc="Custom battle header: text key through HSWAP.")
    for va in (0x7D0687, 0x7D06F6, 0x7D0765, 0x7D07D4, 0x7D0843,
               0x7D1FEC, 0x7D205B, 0x7D20CA, 0x7D2139, 0x7D21A8,
               0x7D595F, 0x7D59D2, 0x7D5A45, 0x7D5AB8, 0x7D5B2B,
               0x7D787F, 0x7D78F2, 0x7D7965, 0x7D79D8, 0x7D7A4B)
] + [
    # ------------------------------------------------------------------
    # 10. Unit button template on the army screen. The template file is
    #     picked from a table at [ebp+0x174 + 4*index], index =
    #     [ebp+0x114] (1..5 = GB, FR, AT, RU, PR). CORE returns the index
    #     to use: the alias great power's index for European minors, and
    #     for Arab nations an index that points at G_ARABTGA (the id of
    #     PlantillaArabes.tga), i.e. (G_ARABTGA - ebp - 0x174) / 4.
    # ------------------------------------------------------------------
    dict(va=GPTAB, orig=None, data=GP_INDEX,
         desc="Great power -> template index table."),
    dict(va=APATH, orig=None, data=ARAB_TGA,
         desc="Path of the Arab button template (in ALLNATIONS.PAK)."),
    dict(va=ARABTAB, orig=None, data=ARAB_LIST,
         desc="List of the five Arab nations."),
    dict(va=CORE, orig=None,
         asm=f"""
            pushfd
            pushad
            mov eax, dword ptr [ebp+0x114]  ; original index
            mov dword ptr [esp+0x1c], eax   ; = return value (saved eax)
            sub esp, 8                      ; [esp]=result node, [esp+4]=key
            mov dword ptr [esp+4], eax
            lea ecx, [esp+4]
            push ecx                        ; &key
            lea edx, [esp+4]
            push edx                        ; &result
            mov eax, dword ptr [ebp+0xd8]
            mov ecx, dword ptr [eax+0x20]
            mov ecx, dword ptr [ecx+0x18]
            add ecx, 0x28                   ; map index -> nation
            call 0x5c0410                   ; map.find(index)
            mov eax, dword ptr [ebp+0xd8]
            mov eax, dword ptr [eax+0x20]
            mov eax, dword ptr [eax+0x18]
            mov eax, dword ptr [eax+0x28+8] ; map.end()
            mov ecx, dword ptr [esp]
            cmp ecx, eax
            je notfound
            mov edx, dword ptr [ecx+0xc]    ; nation name id
            mov esi, edx
            mov edi, {ARABTAB:#x}
        arabloop:                           ; is it one of the Arab nations?
            mov eax, dword ptr [edi]
            test eax, eax
            je notarab
            push eax
            call 0x530800
            add esp, 4
            mov ebx, eax
            push eax
            call 0x530890
            add esp, 4
            cmp ebx, esi
            je isarab
            add edi, 4
            jmp arabloop
        isarab:
            cmp dword ptr [{G_ARABTGA:#x}], 0
            jne havetga
            push {APATH:#x}
            call 0x530800                   ; id of PlantillaArabes.tga (kept)
            add esp, 4
            mov dword ptr [{G_ARABTGA:#x}], eax
        havetga:
            mov eax, {G_ARABTGA:#x}
            sub eax, ebp
            sub eax, 0x174
            sar eax, 2                      ; index that points at G_ARABTGA
            mov dword ptr [esp+8+0x1c], eax
            add esp, 8
            popad
            popfd
            ret
        notarab:
            mov edx, esi
            push edx
            call {ALIAS:#x}                 ; alias great power (referenced id)
            add esp, 4
            mov esi, eax
            cmp dword ptr [{G_LTEXT:#x}], 0
            je release                      ; great power: keep index
            mov edi, {GPTAB:#x}
        gploop:
            mov eax, dword ptr [edi]
            test eax, eax
            je release
            push eax
            call 0x530800
            add esp, 4
            mov ebx, eax
            push eax
            call 0x530890
            add esp, 4
            cmp ebx, esi
            je found
            add edi, 8
            jmp gploop
        found:
            mov eax, dword ptr [edi+4]      ; template index of the alias
            mov dword ptr [esp+8+0x1c], eax
        release:
            push esi
            call 0x530890
            add esp, 4
            add esp, 8
            popad
            popfd
            ret
        notfound:
            add esp, 8
            popad
            popfd
            ret
         """,
         desc="CORE: template index for the nation (cave)."),
    dict(va=GIC, orig=None,
         asm=f"push eax\ncall {CORE:#x}\nmov ecx, eax\npop eax\nret",
         desc="CORE wrapper returning in ecx."),
    dict(va=GID, orig=None,
         asm=f"push eax\ncall {CORE:#x}\nmov edx, eax\npop eax\nret",
         desc="CORE wrapper returning in edx."),
    dict(va=0x7D02B7, orig="8b8d14010000", asm=f"call {GIC:#x}", pad=1,
         desc="Army screen: mov ecx,[ebp+0x114] -> call GIC."),
    dict(va=0x7D02E3, orig="8b8514010000", asm=f"call {CORE:#x}", pad=1,
         desc="Army screen: mov eax,[ebp+0x114] -> call CORE."),
    dict(va=0x7D0320, orig="8b9514010000", asm=f"call {GID:#x}", pad=1,
         desc="Army screen: mov edx,[ebp+0x114] -> call GID."),

    # ------------------------------------------------------------------
    # 11. Unit icons (key NATION_TYPE_BTN_*): European minors use the
    #     icons of their alias great power, Arab nations keep their own
    #     name and get their own icons from ALLNATIONS.PAK.
    # ------------------------------------------------------------------
    dict(va=TBL2, orig=None, data=TABLE_NO_ARAB,
         desc="ALIAS_TABLE without the Arab nations."),
    dict(va=ALIAS2, orig=None,
         asm=_ALIAS_BODY.format(table=TBL2, reset="", store=""),
         desc="ALIAS2: like ALIAS, without header text (cave)."),
    dict(va=0x7CE675, asm=f"call {ALIAS2:#x}", call_from=0x52FB10,
         desc="Unit icon key: resolve the nation through ALIAS2."),
]


# ======================================================================
#  v1.2.1 - fix: crash when right-clicking a nation as a minor nation
# ======================================================================
#
# Right-clicking a nation on the campaign map opens its info panel. The
# panel (function 0x7f14e0) gets the list of great powers - which now
# includes the human minor nation - and looks up each one's entry in the
# panel with 0x5584e0. The human minor nation has no entry, the lookup
# returns NULL and the game called a method on it (crash at 0x7f158f /
# 0x7f1532). Both loops now skip players without an entry, like the two
# progress-panel checks in section 6.
PANEL_A, PANEL_B = 0x881480, 0x8814A0

PATCHES_V121 = [
    dict(va=PANEL_A, orig=None,
         asm="""
            test eax, eax
            jz 0x7f1539                     ; no entry -> next player
            mov edx, dword ptr [eax]
            mov ecx, eax
            call dword ptr [edx+0x7c]       ; original: entry->Hide()
            jmp 0x7f1539
         """,
         desc="Info panel NULL check #1 (cave)."),
    dict(va=0x7F1532, orig="8b108bc8ff527c", asm=f"jmp {PANEL_A:#x}", pad=2,
         desc="Info panel loop #1: jump into the cave."),
    dict(va=PANEL_B, orig=None,
         asm="""
            mov ebp, eax                    ; original instructions
            test eax, eax
            jz 0x7f15a3                     ; no entry -> next player
            mov eax, dword ptr [edi]
            cmp eax, ebx
            jmp 0x7f157d                    ; flags of cmp are used there
         """,
         desc="Info panel NULL check #2 (cave)."),
    dict(va=0x7F1577, orig="8be88b073bc3", asm=f"jmp {PANEL_B:#x}", pad=1,
         desc="Info panel loop #2: jump into the cave."),
]

PATCHES = PATCHES_V11 + PATCHES_V12 + PATCHES_V121
