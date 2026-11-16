# Genuine food photographs — REQUIRED BEFORE LAUNCH

The downloadable website has **32 original dish-specific illustrations**, not 32 real food photographs. The original requirement for **32 real, unique, visually accurate** photos is **NOT YET MET**. The current system works for coding and testing but should not be published as representing actual vendor dishes.

To finish photography correctly:

1. Collect **32 separately licensed** actual photographs or get written permission from the vendors to use their photographs. Wikimedia Commons, licensed stock libraries and vendors can be sources. A Google Images thumbnail alone is not permission.
2. Use `PHOTO_SOURCES.csv` for the photo, exact food, source URL, photographer and license.
3. Save as the filenames listed in `PHOTO_SOURCES.csv`, in `photos_to_import`.
4. Run `py -3 IMPORT_REAL_PHOTOS.py --check`, open `REAL_PHOTO_REVIEW_SHEET.jpg` and visually compare all names/photos. The script detects exact and near duplicates, but **cannot prove semantic dish correctness**.
5. Only after verifying each dish and the license, run `py -3 IMPORT_REAL_PHOTOS.py --apply --confirmed-reviewed`.

The installer only installs the full 32-image set when it passes file validation. Never bulk reuse, crop or color-adjust source photos and pretend they are different.
