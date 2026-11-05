# CLAUDE.md

## Git
- **Mindig közvetlenül a `main` ágra dolgozunk.** Nem kell feature branch, nem kell pull request:
  commit a `main`-re, push a `main`-re (`git push origin main`).
- Commit csak zöld tesztekkel (`pytest -q`).

## Projekt
- Python 3.11+, egyetlen futásidejű függőség a PySide6. Indítás: `python -m katzenmaster`.
- Tesztek: `pytest -q` (headless, `QT_QPA_PLATFORM=offscreen`).
- Vizuális ellenőrzés: `python -m katzenmaster --snapshot` → `out/` (a képeket meg is kell nézni).
- GUI nélküli logika (`brain.py`, `animation.py`, `sprites.py`) maradjon külön a widgettől.
- Minden hangolható érték a `katzenmaster/config.py`-ban van.
- Futtatható állomány: `python packaging/build.py` (lásd README, „Futtatható állomány”).
- Haladási napló: `PROGRESS.md`; kézi ellenőrzések: `MANUAL_CHECKS.md`.
- Dokumentáció magyarul, kód és kódkommentek angolul.
