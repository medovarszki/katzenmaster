# katzenmaster

Egy pixel art macska, aki a képernyő alján él. Ül, néha pislog, sétál a képernyő
egyik szélétől a másikig, nyújtózik, ásít és mosakszik (a mancsát nyalogatja). Ha
sokáig nem foglalkoznak vele, ásít egyet és elalszik, és ha magától ébred,
nyújtózik. Ha a kurzor
a közelébe ér, az alvó macska felébred és leül, az ülő macska pedig odasétál a
kurzor alá.

Nincs más funkciója: nem mozgat ablakokat, nem nyit programokat, nincs
beállítás-ablak. Az egyetlen felület a tálcaikon egy **Kilépés** menüponttal.

## Telepítés

Python 3.11+ kell. Az egyetlen futásidejű függőség a PySide6.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux:

```bash
source .venv/bin/activate
```

Utána:

```bash
pip install -e ".[dev]"
```

A sprite-ok a tárolóban vannak (`assets/sprites/`), és a kód a
csomag mellől tölti be őket, ezért vagy a klónozott mappából indítsd, vagy
szerkeszthető módban (`pip install -e .`) telepítsd.

Linuxon a Qt xcb pluginjának szüksége lehet néhány rendszercsomagra. Debianon és
Ubuntun:

```bash
sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libegl1
```

## Indítás

```bash
python -m katzenmaster
```

Kilépés: a tálcaikon jobb gombos menüjében a **Kilépés**, vagy ha terminálból
indítottad, Ctrl+C.

További kapcsolók:

| Kapcsoló | Hatás |
|---|---|
| `--snapshot` | Képernyő nélkül (`QT_QPA_PLATFORM=offscreen`) lerenderel minden állapotot, és kilép |
| `--out MAPPA` | A `--snapshot` kimeneti mappája (alapértelmezés: `out/`) |
| `-v` | Részletes (debug) naplózás |
| `--version` | Kiírja a verziószámot, és kilép |

A `--snapshot` kimenete:

- `<állapot>_<n>.png`: a nyers, átlátszó hátterű képkockák, ahogy az ablak kirajzolja őket
- `strip_<állapot>.png`: a képkockák egymás mellett, sakktábla-háttérre kompozitálva
  (ahol a sakktábla átlátszik, ott a kép valóban átlátszó)
- `contact_sheet.png`: az összes állapot egy képen, sakktáblán és sima színen
- `timeline.txt`: egy fix seedű, 6 perces szimuláció állapotváltásai szkriptelt kurzorral

## Futtatható állomány (Windows `.exe`, Linux bináris)

Python telepítése nélkül futtatható, egyetlen fájlból álló változat. PyInstallerrel
készül, a sprite-ok benne vannak.

### Letöltés a GitHubról (ajánlott)

A kiadások a GitHub **Releases** oldalán vannak:
<https://github.com/medovarszki/katzenmaster/releases>. Mindegyikhez három fájl
tartozik:

- `katzenmaster-windows-x86_64.exe`: Windows 10/11;
- `katzenmaster-linux-x86_64.tar.gz`: Linux x86_64;
- `SHA256SUMS.txt`: ellenőrzőösszegek.

A legújabb kiadás ezekről az állandó címekről is letölthető:

- <https://github.com/medovarszki/katzenmaster/releases/latest/download/katzenmaster-windows-x86_64.exe>
- <https://github.com/medovarszki/katzenmaster/releases/latest/download/katzenmaster-linux-x86_64.tar.gz>

Linuxon a letöltés ellenőrzése (a két fájl ugyanabban a mappában legyen):

```bash
sha256sum -c --ignore-missing SHA256SUMS.txt
```

Fejlesztői változat: minden `main`-re pusholt commit után a GitHub Actions `build`
workflow mindkét platformra elkészíti a programot. GitHub → **Actions** → **build** →
a legutóbbi zöld futás, lent az **Artifacts** részben:

- `katzenmaster-windows-x86_64`: egy zip, benne a `katzenmaster-windows-x86_64.exe`;
- `katzenmaster-linux-x86_64`: egy zip, benne a `katzenmaster-linux-x86_64.tar.gz`.

### Új kiadás készítése

A verziószám egyetlen helyen van: `katzenmaster/__init__.py` (`__version__`). Ebből
veszi a `pyproject.toml`, a `--version` kapcsoló, a tálcaikon felirata és a napló.

1. Írd át a `__version__` értékét, például `0.2.0`-ra (szemantikus verziózás).
2. Írj egy `## [0.2.0] - ÉÉÉÉ-HH-NN` szakaszt a `CHANGELOG.md`-be. Ez lesz a
   GitHub Release leírása. A `pytest` elbukik, ha az aktuális verzióhoz nincs szakasz.
3. Futtasd a teszteket, commitold és pushold a `main`-re.
4. Tegyél rá taget, és pushold:

```bash
git tag v0.2.0
```

```bash
git push origin v0.2.0
```

A tagre induló `build` futás:

1. ellenőrzi, hogy a tag, a `__version__` és a `CHANGELOG.md` egyezik
   (`packaging/release.py check`); ha nem, a build el sem indul;
2. lefuttatja a teszteket, és Windowson és Linuxon is lebuildeli és smoke-teszteli a
   programot;
3. elkészíti a `SHA256SUMS.txt`-t, és létrehozza a `katzenmaster v0.2.0` nevű
   Release-t a három fájllal és a changelog-szakasszal.

Kötőjeles tag (például `v0.2.0-rc1`) előzetes kiadásként (pre-release) jelenik meg.
Ha a tagre induló futás elbukik, javítsd a hibát a `main`-en, majd töröld és tedd fel
újra a taget:

```bash
git push origin :refs/tags/v0.2.0
```

```bash
git tag -f v0.2.0
```

```bash
git push origin v0.2.0
```

### Saját gépen

A PyInstaller nem tud keresztfordítani: a Windows `.exe` Windowson, a Linux bináris
Linuxon készül.

```bash
pip install -e ".[build]"
```

```bash
python packaging/build.py
```

A build lépései:

1. ikon a sprite-ból;
2. PyInstaller a `packaging/katzenmaster.spec` alapján: egy fájl, konzolablak nélkül, a
   nem használt Qt-részek (Quick/QML, PDF, hálózat, GTK-téma) nélkül;
3. smoke test: a kész fájl `--snapshot` módban lerenderel minden állapotot;
4. a kimenet a `dist/` mappába kerül: `katzenmaster-windows-x86_64.exe` vagy
   `katzenmaster-linux-x86_64.tar.gz`.

### Használat

**Windows:** dupla kattintás a `katzenmaster-windows-x86_64.exe` fájlra. Az exe nincs
digitálisan aláírva, ezért a SmartScreen első indításkor figyelmeztethet: **További
információ → Futtatás mindenképp**. Egyes vírusirtók gyanúsnak jelölhetik az
egyfájlos PyInstaller-programokat; ez téves riasztás. Indításkor a program néhány
másodpercig kicsomagolja magát egy ideiglenes mappába, ezért a macska kis késéssel
jelenik meg. Mivel nincs konzolablak, a napló ide kerül: `%TEMP%\katzenmaster.log`.

**Linux:**

```bash
tar xzf katzenmaster-linux-x86_64.tar.gz
```

```bash
./katzenmaster-linux-x86_64/katzenmaster
```

Terminálból indítva a napló a terminálban jelenik meg. Ubuntu 22.04-en készül, ezért
glibc 2.35 vagy újabb kell hozzá (Ubuntu 22.04+, Debian 12+, Fedora 36+). Az xcb
platform plugin függőségei benne vannak a csomagban; a Wayland-korlátok ugyanazok,
mint forrásból futtatva.

## Tesztek

```bash
pytest -q
```

A tesztek képernyő nélkül futnak (`QT_QPA_PLATFORM=offscreen`).

## Testreszabás

Minden időzítés és méret a `katzenmaster/config.py` fájlban van:

- `SCALE`: egész szorzó, nearest-neighbor nagyítással (alapértelmezés 3, vagyis 96 px)
- `SIT_ACTION_INTERVAL`, `BLINK_INTERVAL`: ülés és pislogás
- `WALK_PROBABILITY`, `STRETCH_PROBABILITY`, `YAWN_PROBABILITY`, `GROOM_PROBABILITY`:
  egy ülés végén ilyen eséllyel indul sétálni, nyújtózik, ásít vagy mosakszik
  (a maradék eséllyel tovább ül)
- `GROOM_DURATION`: a mosakodás hossza
- `SLEEP_AFTER`, `SLEEP_DURATION`: ennyi kurzor nélküli ébrenlét után alszik el, és ennyi ideig alszik
- `WALK_DISTANCE`, `WALK_SPEED`, `CHASE_SPEED`: séta hossza és sebessége
- `CURSOR_NEAR_RADIUS`, `REACT_COOLDOWN`: mikor számít közelinek a kurzor, és mennyi szünet van két reakció között

A sprite sheet az `assets/sprites/generate_sprites.py` futtatásával generálható újra.

## Felépítés

| Fájl | Tartalom |
|---|---|
| `katzenmaster/config.py` | Konstansok |
| `katzenmaster/sprites.py` | `sprites.json` értelmezése; `SpriteSheet`: vágás, nearest-neighbor nagyítás, tükrözés (csak `QImage`) |
| `katzenmaster/animation.py` | Képkocka-időzítés, ismétlődő és egyszer lefutó animációk (tiszta Python) |
| `katzenmaster/brain.py` | Állapotgép (`SIT`, `BLINK`, `WALK`, `SLEEP`, `CHASE`, `STRETCH`, `YAWN`, `GROOM`), szélek kezelése, kurzorreakció, talajpozíció (tiszta Python) |
| `katzenmaster/window.py` | Átlátszó, átkattintható, mindig felül lévő ablak |
| `katzenmaster/tray.py` | Tálcaikon |
| `katzenmaster/app.py` | Az elemek összekötése |
| `katzenmaster/snapshot.py` | A `--snapshot` mód |
| `packaging/build.py`, `packaging/katzenmaster.spec` | Futtatható állomány készítése (PyInstaller) |
| `packaging/release.py` | Kiadás előtti ellenőrzés (tag, verzió, changelog) és a release-jegyzet kiolvasása |
| `.github/workflows/build.yml` | CI: tesztek és build Windowsra és Linuxra, release tagre |
| `CHANGELOG.md` | Változások kiadásonként; ebből készül a release leírása |

## Platformok és ismert korlátok

**Windows 10/11:** támogatott. Az ablak `Qt.Tool` típusú, ezért nem jelenik meg a
tálcán és az Alt-Tab listában. A Qt a `WindowTransparentForInput` flaget
`WS_EX_TRANSPARENT` és `WS_EX_LAYERED` stílusra fordítja, ettől lesz átkattintható.

**Linux, X11:** támogatott. Az ablak `_NET_WM_WINDOW_TYPE_UTILITY` és
`_NET_WM_STATE_ABOVE` tulajdonságot kap, a bemeneti alakja (input shape) üres, ezért
átkattintható. Átlátszósághoz kompozitáló ablakkezelő kell; enélkül a macska körül
fekete négyzet látszhat. A legtöbb asztali környezet nem teszi ki a `UTILITY`
ablakokat a tálcára, de ez nem garantált. Ha nálad mégis megjelenik, jelezd.

**Linux, Wayland:** csak korlátozottan működik. A Wayland protokoll szándékosan nem
engedi, hogy egy alkalmazás:

- maga pozicionálja az ablakát: a `move()` hívást a kompozitor figyelmen kívül
  hagyja, így a macska nem feltétlenül a képernyő alján áll, és nem sétál
  (az ablak egy helyben marad, csak az animáció fut);
- mindig felül tartsa az ablakát (`WindowStaysOnTopHint`);
- lekérdezze a globális kurzorpozíciót: a `QCursor.pos()` csak a saját ablak fölött
  frissül, az átkattintható ablaknál ez gyakorlatilag soha, így a macska nem reagál
  a kurzorra.

Az `availableGeometry()` sem feltétlenül veszi figyelembe a panelt. Az alkalmazás
ilyenkor nem omlik össze, de induláskor figyelmeztetést ír a naplóba.

Ajánlott megkerülés: indítsd XWaylanddel (X11 módban), ott a fentiek többnyire
működnek:

```bash
QT_QPA_PLATFORM=xcb python -m katzenmaster
```

**Tálcaikon:** GNOME alatt a tálcaikonhoz az *AppIndicator and KStatusNotifierItem
Support* bővítmény kell. Ha nincs elérhető tálca, az alkalmazás ezt a naplóba írja,
és ilyenkor terminálból Ctrl+C-vel vagy a folyamat leállításával lehet kilépni.

**HiDPI:** a 96 px logikai pixelben értendő. Nem egész skálázásnál (például 150%)
a pixelek nearest-neighbor nagyítással rajzolódnak, ezért éles marad a kép, de a
pixelek szélessége kissé egyenetlen lehet (4–5 fizikai pixel).

**Több monitor:** a macska az elsődleges kijelzőn él. Ha az elsődleges kijelző vagy a
tálca mérete megváltozik, követi.

A valódi asztali környezetben elvégzendő ellenőrzéseket a [MANUAL_CHECKS.md](MANUAL_CHECKS.md)
írja le.
