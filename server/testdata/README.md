# Test data

**Altman Spectra Cyc 100 IES files**, downloaded from `altmanlighting.com/support`.

They are here rather than referenced outside the repo because `test_ies.py` used
to read them through a relative path into a folder on one laptop — and when the
files were not there it printed *"skipped"* and **exited 0**. On CI that made a
suite that tested nothing and reported success. `verify_suites.py` caught it on
the first run.

**⭐ Test data belongs with the test.** A fixture reached by climbing out of the
repo is a fixture that exists on exactly one machine.

**On including them:** manufacturers publish IES photometric files precisely so
they can be loaded into other people's software and passed around in project
files — that is what they are for. *(Unlike USITT RP-2, which is a copyrighted
standard and stays out of this repo; see `docs/SYMBOLS.md`.)*
