# PROGRESS

## Elfogadási kritériumok

### 1. Ablak
- [ ] Keret nélküli (`FramelessWindowHint`)
- [ ] Mindig felül (`WindowStaysOnTopHint`)
- [ ] Átlátszó háttér (`WA_TranslucentBackground`), a sprite körül nincs látható háttér
- [ ] Átkattintható (`WindowTransparentForInput` + `WA_TransparentForMouseEvents`)
- [ ] Nincs a tálcán / Alt-Tab listán (`Qt.Tool`)
- [ ] Nem veszi el a fókuszt (`WindowDoesNotAcceptFocus`, `WA_ShowWithoutActivating`)

### 2. Elhelyezés
- [ ] Az elsődleges kijelző `availableGeometry()` alsó szélén áll (tálca fölött)
- [ ] Vízszintesen a képernyő szélei között marad
- [ ] Ha az `availableGeometry` változik (tálca átméretezés), követi

### 3. Állapotgép
- [x] `sit` → (ritkán) `blink` → vissza `sit`
- [x] `sit` → `walk` jobbra/balra véletlen távolságra → `sit`
- [x] Hosszabb tétlenség után `sleep`, alvás végén `sit`
- [x] Szélen megfordul, sosem lóg ki
- [x] Időzítések véletlenszerűek, de konstansokban állíthatók (`catpet/config.py`)
- [ ] `walk` jobbra néz, balra tükrözve rajzolódik

### 4. Reakció a kurzorra (`QCursor.pos()`)
- [x] Alvó macska + közeli kurzor → felébred és leül
- [x] Ülő macska + közeli kurzor → elindul a kurzor felé vízszintesen, majd leül
- [x] Reakció után cooldown (nem pörög folyamatosan)

### 5. Tálca ikon
- [ ] `QSystemTrayIcon` egyetlen „Kilépés” menüponttal, ami kilép
- [ ] Ha nincs system tray: figyelmeztetés a logban, nem omlik össze

### 6. Platformok
- [ ] Windows + Linux (X11): csak Qt API, nincs natív kód
- [ ] Wayland: figyelmeztetés a logban, nem omlik össze; README leírja a korlátokat

### Infrastruktúra / ellenőrzés
- [x] Csomagszerkezet: `catpet/`, `tests/`, `assets/sprites/`, `pyproject.toml`
- [x] Sprite-betöltés, nearest-neighbor nagyítás (3x, konstans), tükrözés – GUI nélkül tesztelve
- [x] Animáció-időzítés tesztelve
- [ ] `python -m catpet` indítás
- [ ] `python -m catpet --snapshot` → PNG-k az `out/` mappába (átlátszó + színes háttérre kompozitált)
- [ ] Snapshot képek szemrevételezve
- [ ] README (telepítés, indítás, ismert korlátok)
- [ ] MANUAL_CHECKS.md (Windows + Linux külön)

## Napló

- **#1** Az adattár üres volt: a leírásban „már meglévő” `assets/sprites/` (png/json/generátor) nem létezett. Megírtam a `generate_sprites.py`-t (csak PySide6 `QImage`, procedurális pixel art, automatikus körvonal), ebből készült a `sprites.png` (6×4 cella, 32×32) és a `sprites.json` (`sit`/`blink`/`sleep`/`walk`, sor, képkockaszám, fps, loop; `walk` jobbra néz). Felnagyítva megnéztem; a „z” betűket újrarajzoltam (torzak voltak, halványak).
- **#1** Projektváz + `config.py` (minden konstans), `sprites.py` (metaadat + `SpriteSheet`: vágás, `FastTransformation`, tükrözés, cache), `animation.py`. 21 teszt zöld; egy lebegőpontos képkocka-hiba (10×0,1 < 1,0) epszilonnal javítva.
- **#2** `brain.py`: GUI nélküli állapotgép (`SIT/BLINK/WALK/SLEEP/CHASE`), `ground_position()` az `availableGeometry` aljához, szélen visszapattanó séta, kurzorreakció cooldownnal (ha a kurzor pont a macska fölött van, pislog). 22 új teszt; 2 elbukott, de mindkettő tesztbeli időzítési hiba volt (pontosítva). 43 teszt zöld.
