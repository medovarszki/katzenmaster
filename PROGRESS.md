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

### 3b. Új tevékenységek (harmadik kör)
- [x] `stretch` (nyújtózás): oldalnézet, egyszer lejátszva, helyben; jobbra néz, balra tükrözve; természetes ébredés után mindig
- [x] `yawn` (ásítás): elölnézet, egyszer lejátszva; elalvás előtt mindig
- [x] `groom` (mosakodás): elölnézet, mancsnyalogatás, ismétlődő, `GROOM_DURATION` ideig; a kurzor megszakítja
- [x] Esélyek és időtartam a `config.py`-ban (`STRETCH_/YAWN_/GROOM_PROBABILITY`, `GROOM_DURATION`)
- [x] Snapshot, tesztek, README, MANUAL_CHECKS frissítve

### 8. Kiadás GitHub Release-ként (negyedik kör)
- [x] Egyetlen verzióforrás: `katzenmaster/__init__.py` (`pyproject.toml` dinamikusan veszi), `--version`, verzió a tálcaikon feliratában és a naplóban
- [x] `CHANGELOG.md`; a release leírása a tagnek megfelelő szakasz
- [x] `packaging/release.py`: tag ↔ verzió ↔ changelog ellenőrzés, a tagre induló build első lépése
- [x] Release: Windows-exe, Linux tar.gz, `SHA256SUMS.txt`; verzió nélküli fájlnevek (`releases/latest/download/...`)
- [x] README: letöltés és kiadási folyamat
- [x] Kiadás gombnyomásra: **Actions → build → Run workflow** verzióval; a `plan` job a buildek előtt ellenőriz (verzió, changelog, `main` ág, a tag még nem létezik), a release lépés hozza létre a taget

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
- **#10** CI (`build` #4) zöld, a smoke test mindkét platformon lefutott (37 PNG). Windows-exe: 37,0 → 23,7 MB. Linux tar.gz (CI, Python 3.12): 64,6 → 46,3 MB.
- **#11** Új tevékenységek: nyújtózás, ásítás, mosakodás. A sprite sheet három új sort kapott (`stretch` 6 kocka, `yawn` 6, `groom` 4; a lap továbbra is 6 oszlopos). Az ásítás és a mosakodás az ülő macska rajzát használja (nyitott száj nyelvvel, illetve felemelt mancs). A nyújtózás „meghajlás”: a mellkas lesüllyed, a mellső lábak előrenyúlnak, a farok felemelkedik. A nyújtózás oldalnézetes, ezért a sétához hasonlóan tükrözzük. Az első rajzon a mély fázisban egy függőleges rózsaszín csík látszott: a fél pixelre eltolt fül-háromszög a kerekítés miatt elfajult. A javítás után a fej egész pixellel tolódik. Az állapotgépben egy ülés végén súlyozott választás dönt: séta, nyújtózás, ásítás, mosakodás vagy további ülés. Elalvás előtt a macska mindig ásít. Ha magától ébred, nyújtózik; ha a kurzor ébreszti, csak felül. Mosakodás közben reagál a kurzorra, nyújtózás és ásítás közben csak utána. A snapshot-szimuláció 6 percre nőtt, hogy a természetes ébredés is benne legyen. A kurzoros forgatókönyv most az első ülő pillanatot várja meg, mert sétálás közben a macska nem reagál. 146 teszt zöld, a snapshot képeit megnéztem.
- **#12** Kiadás. A `release` job már létezett, de tag még nem volt, ezért sosem futott le, és három hiányossága volt. (a) Semmi nem ellenőrizte, hogy a tag és a program verziója egyezik-e. (b) A `generate_release_notes` PR-ekből dolgozik, mi viszont közvetlenül a `main`-re commitolunk, így a leírás üres lett volna. (c) Nem voltak ellenőrzőösszegek. Új elemek: `CHANGELOG.md`, `packaging/release.py` (csak standard könyvtár; a `__version__`-t szövegként olvassa, nem importálja a csomagot), ellenőrző lépés a tagre induló build elején, `SHA256SUMS.txt` és pre-release kötőjeles tagre. A verzió egyetlen helyen van. A fájlnevekben nincs verziószám, így a `releases/latest/download/...` linkek mindig a legújabb kiadásra mutatnak. 14 új teszt, köztük egy, amely elbukik, ha az aktuális verzióhoz nincs changelog-szakasz. 160 teszt zöld.
- **#13** A `build` #7 Windowson elbukott: a `release.py notes` a konzol kódolásával írt, ami Windowson cp1252, és ez nem ismeri az „ő” betűt (`UnicodeEncodeError`). A jegyzet most mindig UTF-8 bájtokként kerül ki. A teszt cp1252-es konzolt állít be, így a hiba Linuxon is kiderül; javítás nélkül el is bukik. 160 teszt zöld.
- **#14** A README tetejére került egy kép: az ülő macska a tálca fölött, a tálcán a program ikonjával. Valódi képernyőkép itt nem készülhetett, mert Xvfb alatt nincs kompozitor, így a macska körül fekete négyzet lenne. A `docs/make_screenshot.py` ezért az igazi ablak renderelését (`CatWindow.render_image`) teszi rá egy festett háttérre és tálcára, 2x felbontásban. Egy új teszt lefuttatja a szkriptet, és ellenőrzi, hogy a macska a tálca szélén áll. 161 teszt zöld.
- **#15** Kiadás gombnyomásra. Ebből a környezetből tag pusholására 403 jön, és telefonról amúgy sem kényelmes taget pusholni, ezért a `build` workflow **Run workflow** gombja kapott egy verzió mezőt. Új `plan` job: a `release.py plan` dönti el, hogy a futás kiad-e (pusholt `v*` tag, vagy kézi futás a `main`-en kitöltött verzióval), és még a buildek előtt ellenőriz. Kézi futásnál az is feltétel, hogy a tag még ne létezzen, így meglévő kiadás nem íródik felül. A taget a `softprops/action-gh-release` hozza létre a futás commitján. A `GITHUB_TOKEN`-nel létrehozott tag nem indít új workflow-t, így nincs dupla build. A verzió mező csak környezeti változón keresztül jut el a szkriptig (script injection ellen). A `concurrency` csak a sima `main`-pusholásokat szakítja meg, a kiadási futásokat nem. 169 teszt zöld.
