# catpet

Egy pixel art macska, aki a képernyő alján él. Ül, néha pislog, sétál a képernyő
egyik szélétől a másikig, és ha sokáig nem foglalkoznak vele, elalszik. Ha a kurzor
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
python -m catpet
```

Kilépés: a tálcaikon jobb gombos menüjében a **Kilépés**, vagy ha terminálból
indítottad, Ctrl+C.

További kapcsolók:

| Kapcsoló | Hatás |
|---|---|
| `--snapshot` | Képernyő nélkül (`QT_QPA_PLATFORM=offscreen`) lerenderel minden állapotot, és kilép |
| `--out MAPPA` | A `--snapshot` kimeneti mappája (alapértelmezés: `out/`) |
| `-v` | Részletes (debug) naplózás |

A `--snapshot` kimenete:

- `<állapot>_<n>.png`: a nyers, átlátszó hátterű képkockák, ahogy az ablak kirajzolja őket
- `strip_<állapot>.png`: a képkockák egymás mellett, sakktábla-háttérre kompozitálva
  (ahol a sakktábla átlátszik, ott a kép valóban átlátszó)
- `contact_sheet.png`: az összes állapot egy képen, sakktáblán és sima színen
- `timeline.txt`: egy fix seedű, 4 perces szimuláció állapotváltásai szkriptelt kurzorral

## Tesztek

```bash
pytest -q
```

A tesztek képernyő nélkül futnak (`QT_QPA_PLATFORM=offscreen`).

## Testreszabás

Minden időzítés és méret a `catpet/config.py` fájlban van:

- `SCALE`: egész szorzó, nearest-neighbor nagyítással (alapértelmezés 3, vagyis 96 px)
- `SIT_ACTION_INTERVAL`, `WALK_PROBABILITY`, `BLINK_INTERVAL`: ülés, séta, pislogás
- `SLEEP_AFTER`, `SLEEP_DURATION`: ennyi kurzor nélküli ébrenlét után alszik el, és ennyi ideig alszik
- `WALK_DISTANCE`, `WALK_SPEED`, `CHASE_SPEED`: séta hossza és sebessége
- `CURSOR_NEAR_RADIUS`, `REACT_COOLDOWN`: mikor számít közelinek a kurzor, és mennyi szünet van két reakció között

A sprite sheet az `assets/sprites/generate_sprites.py` futtatásával generálható újra.

## Felépítés

| Fájl | Tartalom |
|---|---|
| `catpet/config.py` | Konstansok |
| `catpet/sprites.py` | `sprites.json` értelmezése; `SpriteSheet`: vágás, nearest-neighbor nagyítás, tükrözés (csak `QImage`) |
| `catpet/animation.py` | Képkocka-időzítés, ismétlődő és egyszer lefutó animációk (tiszta Python) |
| `catpet/brain.py` | Állapotgép (`SIT`, `BLINK`, `WALK`, `SLEEP`, `CHASE`), szélek kezelése, kurzorreakció, talajpozíció (tiszta Python) |
| `catpet/window.py` | Átlátszó, átkattintható, mindig felül lévő ablak |
| `catpet/tray.py` | Tálcaikon |
| `catpet/app.py` | Az elemek összekötése |
| `catpet/snapshot.py` | A `--snapshot` mód |

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
QT_QPA_PLATFORM=xcb python -m catpet
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
