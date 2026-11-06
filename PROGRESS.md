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
- [x] Időzítések véletlenszerűek, de konstansokban állíthatók (`katzenmaster/config.py`)
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
- [x] Wayland: README leírja a korlátokat

### Infrastruktúra / ellenőrzés
- [x] Csomagszerkezet: `katzenmaster/`, `tests/`, `assets/sprites/`, `pyproject.toml`
- [x] Sprite-betöltés, nearest-neighbor nagyítás (3x, konstans), tükrözés – GUI nélkül tesztelve
- [x] Animáció-időzítés tesztelve
- [x] `python -m katzenmaster` indítás
- [x] `python -m katzenmaster --snapshot` → PNG-k az `out/` mappába (átlátszó + színes háttérre kompozitált)
- [x] Snapshot képek szemrevételezve
- [x] README (telepítés, indítás, ismert korlátok)
- [x] MANUAL_CHECKS.md (Windows + Linux külön)

### 7. Futtatható állomány (második kör)
- [x] Egyfájlos build PyInstallerrel: `packaging/build.py` + `packaging/katzenmaster.spec`
- [x] Fagyasztott futás: assetek a bundle-ből (`config.assets_dir()`); konzol nélküli módban a napló `%TEMP%/katzenmaster.log`-ba megy
- [x] Linux bináris helyben buildelve, smoke test (offscreen), valódi X11 (Xvfb) és Wayland (weston) alatt futtatva
- [x] GitHub Actions: tesztek és build Windowson és Linuxon, artifactok, `v*` tagre Release
- [x] Windows `.exe` a CI-on lebuildelve és smoke testelve
- [x] README és MANUAL_CHECKS frissítve

## Napló

- **#1** Az adattár üres volt: a leírásban „már meglévő” `assets/sprites/` (png/json/generátor) nem létezett. Megírtam a `generate_sprites.py`-t (csak PySide6 `QImage`, procedurális pixel art, automatikus körvonal), ebből készült a `sprites.png` (6×4 cella, 32×32) és a `sprites.json` (`sit`/`blink`/`sleep`/`walk`, sor, képkockaszám, fps, loop; `walk` jobbra néz). Felnagyítva megnéztem; a „z” betűket újrarajzoltam (torzak voltak, halványak).
- **#1** Projektváz + `config.py` (minden konstans), `sprites.py` (metaadat + `SpriteSheet`: vágás, `FastTransformation`, tükrözés, cache), `animation.py`. 21 teszt zöld; egy lebegőpontos képkocka-hiba (10×0,1 < 1,0) epszilonnal javítva.
- **#2** `brain.py`: GUI nélküli állapotgép (`SIT/BLINK/WALK/SLEEP/CHASE`), `ground_position()` az `availableGeometry` aljához, szélen visszapattanó séta, kurzorreakció cooldownnal (ha a kurzor pont a macska fölött van, pislog). 22 új teszt; 2 elbukott, de mindkettő tesztbeli időzítési hiba volt (pontosítva). 43 teszt zöld.
- **#3** `window.py` (flagek + attribútumok, `paintEvent` Source-kompozícióval törölt átlátszó háttérrel, 30 fps `QTimer`, `QCursor.pos()`, `availableGeometryChanged` / `primaryScreenChanged` követése), `tray.py` (egyetlen „Kilépés”), `app.py`, `__main__.py`, `snapshot.py`. Az első snapshot két hibát mutatott: (a) a kontaktlap oszlopai elcsúsztak → fix oszlopszélesség; (b) a `timeline.txt` szerint 3 perc alatt sosem aludt el (az „egyhuzamban 20–40 s ülés” a 0,5 séta-eséllyel szinte sosem teljesül) → az alvás most az ébren töltött időhöz kötött (kurzor-interakció nélkül 60–120 s), és ülésből, a következő döntéskor következik be. Snapshot képek megnézve: átlátszó háttér (sakktábla átlátszik), helyes irány, éles pixelek, váltakozó képkockák, nincs levágás.
- **#3** Ellenőrzés valódi X11-en (Xvfb, WM nélkül): `_NET_WM_WINDOW_TYPE_UTILITY`, `_NET_WM_STATE_ABOVE`, input focus False, Motif dekoráció 0, 32 bites ARGB visual, üres input shape (= átkattintható), y = 720−96, az ablak mozog, SIGINT-re exit 0. A Qt nem állít `_NET_WM_STATE_SKIP_TASKBAR`-t – a `UTILITY` típust a legtöbb tálca kihagyja; natív X11 kódot ezért nem írtam, kézi ellenőrzési pont lett. 70 teszt zöld.
- **#4** Tálcaikon: 32/64/96 px-es nearest-neighbor változatok egy `QIcon`-ban (a 96 px-es kép rendszer általi kicsinyítése elmosódhatott). `SpriteSheet.frame()` kapott egy opcionális `scale` paramétert. Wayland próba valódi kompozitoron (weston `--backend=headless`, `QT_QPA_PLATFORM=wayland`): figyelmeztetés a logban, fut, SIGINT-re exit 0. 71 teszt zöld.
- **#5** `README.md` (telepítés, indítás, kapcsolók, konfiguráció, felépítés, platformkorlátok: Wayland, X11 kompozitor, GNOME tray, HiDPI) és `MANUAL_CHECKS.md` (Windows W1–W13, Linux X11 L1–L12, Wayland WL1–WL4). `pip install -e .[dev]` venv-ben ellenőrizve, másik munkakönyvtárból is megtalálja az asseteket. Végső kör: 71 teszt zöld, friss snapshot rendben. Minden kritérium kipipálva.
- **#6** Munka a `main` ágon (`CLAUDE.md`). Futtatható állomány PyInstallerrel. A PyInstaller nem tud keresztfordítani, ezért a Windows-build a GitHub Actions `windows-latest` runnerén készül. Az első Linux-build 75 MB lett, mert a PySide6 hookjai behúzták a virtuális billentyűzet (QtQuick/QML), a PDF és a Lottie képformátum, valamint a GTK3-téma pluginjait. Ezeket a `.spec` kiszűri, így 57 MB lett. A `libcrypto`/`libssl` és a `Qt6OpenGL` szándékosan bent maradt (Python `_hashlib`/`_ssl`, illetve az xcb plugin használhatja). A kész bináris Xvfb alatt `UTILITY`/`ABOVE` tulajdonságú, üres input shape-pel; weston alatt figyelmeztet és fut; plugin-betöltési hiba nincs (`QT_DEBUG_PLUGINS=1`). 76 teszt zöld.
- **#7** Első CI-futás (`build` #1) zöld mindkét platformon. Windows: a tesztek lefutottak, `katzenmaster-windows-x86_64.exe` 37 MB, a smoke testben 37 PNG készült. Linux (ubuntu-22.04): tesztek és build zöld. Mindkettő letölthető artifactként.
- **#8** Átnevezés: a projekt neve mindenhol `katzenmaster`. Érintett: a csomag (`katzenmaster/`, `python -m katzenmaster`), a `pyproject.toml`, az ablakcím, a tálcaikon felirata, a naplófájl (`%TEMP%/katzenmaster.log`), a `.spec`, az exe és a CI-artifactok (`katzenmaster-windows-x86_64.exe`, `katzenmaster-linux-x86_64.tar.gz`), valamint a dokumentáció. 76 teszt zöld, a snapshot változatlan, a helyi Linux-build és a smoke test rendben.
- **#9** Méretcsökkentés. A szűrési szabály külön modulba került (`packaging/bundle_filter.py`), 50 teszt ellenőrzi, mi marad bent és mi esik ki. Kiesik: fordítások, képformátum- és ikonmotor-pluginok, QtSvg, a nem használt platform pluginok (csak windows/xcb/wayland/offscreen marad), Windowson az `opengl32sw.dll` (szoftveres OpenGL, 7,7 MB tömörítve) és a `d3dcompiler`, valamint a `_hashlib`/`_ssl` (velük a `libcrypto`). Linuxon strip. Linux: 57,2 → 50,8 MB; X11 (Xvfb) és Wayland (weston) alatt futtatva rendben. A legnagyobb maradék tétel az ICU-adat (12,3 MB tömörítve), ezt a QtCore Linuxon kötelezően használja. UPX-et szándékosan nem használunk (vírusirtós hamis riasztások, Qt-pluginok sérülhetnek). 126 teszt zöld.
