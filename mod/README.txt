=====================================================================
  Imperial Glory - All Nations Playable                      v1.3
=====================================================================

This mod lets you play any of the 24 nations, not just the five great
powers - in the campaign and in custom battles. Everything else stays
exactly as in the original game: no bonuses, no new units, no rule
changes.

Playable nations:
  Great powers: France, Great Britain, Austria, Prussia, Russia
  New:          Batavian Republic, Denmark, Egypt, Hanover, Helvetic
                Republic, Lombardy, Moldavia, Morocco, Ottoman Empire,
                Papal States, Piedmont, Poland, Portugal, Saxony, Spain,
                Sweden, Kingdom of the Two Sicilies, Tripolitania, Tunisia

Even with a minor nation you can conquer, permanently occupy and annex
nations through sympathy as usual.


REQUIREMENTS
------------
The unmodified Steam version of Imperial Glory. The installer checks
this itself. The GOG and CD versions are not supported (yet).


INSTALLATION
------------
1. Copy the "AllNations-Mod" folder from the archive directly into the
   game folder, i.e. next to ImperialGlory.exe. In Steam: right-click
   Imperial Glory > Manage > Browse local files.
2. In the AllNations-Mod folder, double-click "Install.bat".
3. Answer the two questions:
   - Enable Windows 98/ME compatibility mode? Recommended. Without it
     the game crashes after real-time battles for many players.
   - Create a desktop shortcut?

The installer creates two files in the game folder:
  ImperialGlory_AllNations.exe   the patched game executable
  ALLNATIONS.PAK                 the modified game data
Your ImperialGlory.exe is left untouched.

Updating from an older version: just copy the new AllNations-Mod folder
over the old one and run Install.bat again. Savegames are kept.


PLAYING
-------
Campaign: run ImperialGlory_AllNations.exe (or the shortcut) and pick
any nation on the map under "New Campaign". The list on the right only
shows the five great powers (as in the original game); minor nations
are selected by clicking them on the map. Name and description of the
selected nation appear in the info box below the map.

Custom battles (new in 1.2): every nation can be chosen for land and
naval battles. The screen shows the nation's real name, and units can
be bought by hand or with Auto-Buy.
  - The Arab nations (Ottoman Empire, Egypt, Morocco, Tunisia,
    Tripolitania) field Arab troops, including the camel riders, with
    their own unit pictures.
  - The European minor nations use the units of a related great power:
      French units:   Spain, Portugal, Papal States, Two Sicilies,
                      Piedmont, Lombardy, Helvetic Republic, Batavia
      Prussian units: Hanover, Saxony, Denmark, Sweden
      Austrian units: Poland, Moldavia
  - Naval battles work the same way.

Starting through Steam or ImperialGlory.exe runs the unmodified original
game. Both can be installed side by side.


UNINSTALL
---------
Double-click "Uninstall.bat", then delete the AllNations-Mod
folder. That removes everything.


KNOWN LIMITATIONS
-----------------
- Minor nations are not shown in the list on the right of the selection
  menu; pick them on the map. They have no resource bars there, and
  their start icon is a placeholder image.
- The info box below the selection map is smaller than in the original
  game; longer descriptions can be scrolled.
- Minor nations have no victory sequence of their own; the game uses an
  existing one instead.
- Custom battles: European minor nations wear the uniforms of their
  related great power.
- Savegames with a minor nation can only be loaded with
  ImperialGlory_AllNations.exe.
- Other mods: ALLNATIONS.PAK is loaded last and only changes the files
  listed below. If another mod changes the same files, this mod wins.


TROUBLESHOOTING
---------------
- "This ImperialGlory.exe is not supported": in Steam use Properties >
  Installed Files > "Verify integrity of game files", then run the
  installer again.
- Writing to the game folder fails: close the game, then right-click
  Install.bat > Run as administrator.
- Crash after a battle: check compatibility mode. Right-click
  ImperialGlory_AllNations.exe > Properties > Compatibility >
  "Windows 98/Windows ME".
- Black screen after Alt+Tab: in Config.sb in the game folder change
  "FULLSCREEN TRUE" to "FULLSCREEN FALSE" (windowed mode).


WHAT THE MOD CHANGES
--------------------
Game data (ALLNATIONS.PAK):
  Game/UI/MainMenu/SelectEmpire/UIDefs_MapaPaisesSelectEmpire.sb
      selection map: all nations clickable
  Game/GameModes/Gestion/DefOrdenTurnos.sb
      turn order when a human plays a minor nation
  Game/UI/ModeloGestion/Iconos/UIDefs_PoolIconosNotificaciones.sb
      start icons for minor nations
  Game/UI/MainMenu/UIDefs_SelectEmpire.sb
  Game/UI/MainMenu/SelectEmpire/UIDefs_ZSToolTips.sb
      selection menu: smaller info box below the map (North Africa
      was hidden behind it)
  Game/UI/MainMenu/SelectEmpire/UIDefs_Banderas.sb
      selection menu: the nation's own flag in the info box (uses the
      flags from the campaign interface)
  Game/UI/MainMenu/UIDefs_SelectArmyAutoBuy.sb
  Game/UI/MainMenu/UIDefs_SelectNavyAutoBuy.sb
      custom battle: Auto-Buy lists for every nation
  Game/UI/MainMenu/UI_DefsSelectArmyButtons.sb
      custom battle: buttons for the camel riders and Arab elite cavalry
  Game/UI/MainMenu/Tropas/Iconos/Genericos/UIDefs_PoolTropasIcons.sb
  Game/UI/MainMenu/Tropas/Botones/PlantillaArabes.tga
      custom battle: unit pictures of the Arab nations (made from the
      game's own Egyptian unit icons)

Executable (ImperialGlory_AllNations.exe, 81 byte patches, all visible
in AllNations-Mod/patcher.ps1):
  - The hard-coded list of five selectable great powers applies to all
    nations in the selection menu. The list on the right keeps showing
    only the great powers; minor nations are added behind them and kept
    out of view.
  - Turn order is loaded for all nations; missing entries are skipped
    safely (previously a crash at campaign start).
  - The human player is treated internally as a great power so that
    conquest, occupation and annexation through sympathy work.
  - Extra safety checks in the great-power progress panel.
  - No crash when right-clicking another nation's territory with a
    minor nation.
  - Custom battle screens: every nation gets the layout of a related
    great power but keeps its own name; Arab nations get their own
    unit button template and unit icons.
  - ALLNATIONS.PAK is loaded after the regular game data.

Source code and build instructions:
  https://github.com/ItsMePaiinZ/ImperialGlory_AllNationsPlayable


VERSION HISTORY
---------------
1.3  Fixed a crash when right-clicking another nation's territory
     with a minor nation.
1.2  Custom battles with all 24 nations (land and naval): real nation
     names, purchasable units, working Auto-Buy; Arab nations with Arab
     troops including camel riders and their own unit pictures.
1.1  North African nations (Morocco, Tunisia, Tripolitania, Egypt) can
     now be clicked on the map; the list on the right no longer runs
     over the OK button; minor nations show their own flag in the info
     box instead of the Austrian coat of arms.
1.0  First release.


Have fun!
