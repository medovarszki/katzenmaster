# PROGRESS

## Elfogadási kritériumok

### 1. Ablak
- [x] Keret nélküli (`FramelessWindowHint`)
- [x] Mindig felül (`WindowStaysOnTopHint`)
- [x] Átlátszó háttér (`WA_TranslucentBackground`), a sprite körül nincs látható háttér
- [x] Átkattintható (`WindowTransparentForInput` + `WA_TransparentForMouseEvents`)
- [x] Nincs a tálcán / Alt-Tab listán (`Qt.Tool`)
- [x] Nem veszi el a fókuszt (`WindowDoesNotAcceptFocus`, `WA_ShowWithoutActivating`)

### 2. Elhelyezés
- [x] Az elsődleges kijelző `availableGeometry()` alsó szélén áll (tálca fölött)
- [x] Vízszintesen a képernyő szélei között marad
- [x] Ha az `availableGeometry` változik (tálca átméretezés), követi

### 3. Állapotgép
- [x] `sit` → (ritkán) `blink` → vissza `sit`
- [x] `sit` → `walk` jobbra/balra véletlen távolságra → `sit`
- [x] Hosszabb tétlenség után `sleep`, alvás végén `sit`
- [x] Szélen megfordul, sosem lóg ki
- [x] Időzítések véletlenszerűek, de konstansokban állíthatók (`catpet/config.py`)
- [x] `walk` jobbra néz, balra tükrözve rajzolódik

### 4. Reakció a kurzorra (`QCursor.pos()`)
- [x] Alvó macska + közeli kurzor → felébred és leül
- [x] Ülő macska + közeli kurzor → elindul a kurzor felé vízszintesen, majd leül
- [x] Reakció után cooldown (nem pörög folyamatosan)

### 5. Tálca ikon
- [x] `QSystemTrayIcon` egyetlen „Kilépés” menüponttal, ami kilép
- [x] Ha nincs system tray: figyelmeztetés a logban, nem omlik össze

### 6. Platformok
- [x] Windows + Linux (X11): csak Qt API, nincs natív kód
- [x] Wayland: figyelmeztetés a logban, nem omlik össze
- [ ] Wayland: README leírja a korlátokat

### Infrastruktúra / ellenőrzés
- [x] Csomagszerkezet: `catpet/`, `tests/`, `assets/sprites/`, `pyproject.toml`
- [x] Sprite-betöltés, nearest-neighbor nagyítás (3x, konstans), tükrözés – GUI nélkül tesztelve
- [x] Animáció-időzítés tesztelve
- [x] `python -m catpet` indítás
- [x] `python -m catpet --snapshot` → PNG-k az `out/` mappába (átlátszó + színes háttérre kompozitált)
- [x] Snapshot képek szemrevételezve
- [ ] README (telepítés, indítás, ismert korlátok)
- [ ] MANUAL_CHECKS.md (Windows + Linux külön)

## Napló

- **#1** Az adattár üres volt: a leírásban „már meglévő” `assets/sprites/` (png/json/generátor) nem létezett. Megírtam a `generate_sprites.py`-t (csak PySide6 `QImage`, procedurális pixel art, automatikus körvonal), ebből készült a `sprites.png` (6×4 cella, 32×32) és a `sprites.json` (`sit`/`blink`/`sleep`/`walk`, sor, képkockaszám, fps, loop; `walk` jobbra néz). Felnagyítva megnéztem; a „z” betűket újrarajzoltam (torzak voltak, halványak).
- **#1** Projektváz + `config.py` (minden konstans), `sprites.py` (metaadat + `SpriteSheet`: vágás, `FastTransformation`, tükrözés, cache), `animation.py`. 21 teszt zöld; egy lebegőpontos képkocka-hiba (10×0,1 < 1,0) epszilonnal javítva.
- **#2** `brain.py`: GUI nélküli állapotgép (`SIT/BLINK/WALK/SLEEP/CHASE`), `ground_position()` az `availableGeometry` aljához, szélen visszapattanó séta, kurzorreakció cooldownnal (ha a kurzor pont a macska fölött van, pislog). 22 új teszt; 2 elbukott, de mindkettő tesztbeli időzítési hiba volt (pontosítva). 43 teszt zöld.
- **#3** `window.py` (flagek + attribútumok, `paintEvent` Source-kompozícióval törölt átlátszó háttérrel, 30 fps `QTimer`, `QCursor.pos()`, `availableGeometryChanged` / `primaryScreenChanged` követése), `tray.py` (egyetlen „Kilépés”), `app.py`, `__main__.py`, `snapshot.py`. Az első snapshot két hibát mutatott: (a) a kontaktlap oszlopai elcsúsztak → fix oszlopszélesség; (b) a `timeline.txt` szerint 3 perc alatt sosem aludt el (az „egyhuzamban 20–40 s ülés” a 0,5 séta-eséllyel szinte sosem teljesül) → az alvás most az ébren töltött időhöz kötött (kurzor-interakció nélkül 60–120 s), és ülésből, a következő döntéskor következik be. Snapshot képek megnézve: átlátszó háttér (sakktábla átlátszik), helyes irány, éles pixelek, váltakozó képkockák, nincs levágás.
- **#3** Ellenőrzés valódi X11-en (Xvfb, WM nélkül): `_NET_WM_WINDOW_TYPE_UTILITY`, `_NET_WM_STATE_ABOVE`, input focus False, Motif dekoráció 0, 32 bites ARGB visual, üres input shape (= átkattintható), y = 720−96, az ablak mozog, SIGINT-re exit 0. A Qt nem állít `_NET_WM_STATE_SKIP_TASKBAR`-t – a `UTILITY` típust a legtöbb tálca kihagyja; natív X11 kódot ezért nem írtam, kézi ellenőrzési pont lett. 70 teszt zöld.
- **#4** Tálcaikon: 32/64/96 px-es nearest-neighbor változatok egy `QIcon`-ban (a 96 px-es kép rendszer általi kicsinyítése elmosódhatott). `SpriteSheet.frame()` kapott egy opcionális `scale` paramétert. Wayland próba valódi kompozitoron (weston `--backend=headless`, `QT_QPA_PLATFORM=wayland`): figyelmeztetés a logban, fut, SIGINT-re exit 0. 71 teszt zöld.
