"""
Imperial Glory - All Nations Playable v1.1
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

PATCHES = [
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
         data="TURN_ORDER_TABLE",          # filled in by build.py, see below
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
