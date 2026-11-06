# Változások

A formátum a [Keep a Changelog](https://keepachangelog.com/hu/1.1.0/) ajánlását
követi, a verziószámok a [szemantikus verziózást](https://semver.org/lang/hu/).
Kiadáskor ennek a fájlnak a megfelelő szakasza lesz a GitHub Release leírása.

## [0.1.0] - 2026-11-06

Az első kiadás.

### Letöltés

- **Windows 10/11:** `katzenmaster-windows-x86_64.exe`. Nem kell telepíteni,
  dupla kattintással indul. Az exe nincs digitálisan aláírva, ezért a SmartScreen
  figyelmeztethet: **További információ → Futtatás mindenképp**.
- **Linux (x86_64, glibc 2.35+, X11):** `katzenmaster-linux-x86_64.tar.gz`.
  Kicsomagolás után a `katzenmaster-linux-x86_64/katzenmaster` fájl indítja.
- `SHA256SUMS.txt`: ellenőrzőösszegek a letöltött fájlokhoz.

### Újdonságok

- Pixel art macska a képernyő alján, a tálca fölött. Az ablak átlátszó,
  átkattintható, mindig felül van, és nem jelenik meg a tálcán.
- Tevékenységek: ülés, pislogás, séta (a képernyő szélén megfordul), nyújtózás,
  ásítás, mosakodás és alvás.
- Ha sokáig nem foglalkoznak vele, ásít egyet és elalszik. Ha magától ébred,
  nyújtózik.
- Reagál a kurzorra: az alvó macska felébred, az ülő odasétál a kurzor alá.
- Tálcaikon egyetlen **Kilépés** menüponttal.
- `--snapshot` mód: képernyő nélkül lerenderel minden állapotot PNG-be.

### Ismert korlátok

- Wayland alatt a macska nem tud a képernyő aljára állni és sétálni, és nem
  reagál a kurzorra. Megoldás: XWayland (`QT_QPA_PLATFORM=xcb`), részletek a
  README-ben.
- GNOME alatt a tálcaikonhoz az *AppIndicator* bővítmény kell.
