# Changelog

## 1.2.1 – 2026-10-17
### Fixed
- Crash when right-clicking a nation on the campaign map while playing a minor nation (e.g. Portugal as Spain).
  The nation info panel looked up an entry for every great power. The human minor nation is treated as a great power but has no entry, so the lookup returned NULL. Both loops now skip players without an entry (`src/patches.py`, section v1.2.1).

## 1.2 – 2026-10-15
### Added
- Custom battles with all 24 nations, land and naval.
- Real nation names on the custom battle screens.
- Units can be bought for every nation, and Auto-Buy works.
- Ottoman Empire, Egypt, Morocco, Tunisia and Tripolitania field Arab troops, including camel riders, with their own unit pictures (`PlantillaArabes.tga`).
- European minor nations use the units of a related great power (France, Prussia or Austria).

## 1.1 – 2026-10-12
### Fixed
- North African nations (Morocco, Tunisia, Tripolitania, Egypt) can now be clicked on the selection map.
- The nation list on the right no longer covers the OK button.
- Minor nations show their own flag in the info box instead of the Austrian coat of arms.

## 1.0 – 2026-10-12
- First release: play the campaign as any of the 24 nations.
