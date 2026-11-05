# Kézi ellenőrzések

Ezeket a pontokat a fejlesztői környezetben nem lehetett ellenőrizni, mert nincs
valódi asztal, tálca és ablakkezelő. Az automatikusan ellenőrzött részek:

- a `pytest` teszt-csomag ellenőrzi a window flageket, az attribútumokat, a
  renderelés átlátszóságát, az állapotgépet és a tálcamenüt;
- a `--snapshot` képek szemrevételezéssel készültek;
- Xvfb-ben, ablakkezelő nélkül ellenőriztük az X11-tulajdonságokat: `UTILITY` típus,
  `_NET_WM_STATE_ABOVE`, üres input shape és 32 bites ARGB visual;
- weston headless backenden ellenőriztük, hogy az alkalmazás Wayland alatt nem omlik össze.

Minden pont előtt indítsd el az alkalmazást a projekt mappájából:

```bash
python -m catpet -v
```

A `-v` miatt a terminálban látszik a napló is.

Gyorsabb teszteléshez a `catpet/config.py`-ban ideiglenesen csökkentheted az
időzítéseket, például `SLEEP_AFTER = (10.0, 15.0)`. Utána állítsd vissza.

---

## Windows 10/11

| # | Lépés | Elvárt eredmény |
|---|---|---|
| W1 | Indítsd el az alkalmazást. | A macska a tálca **fölött** jelenik meg, a lába a tálca felső szélén van, nem takarja ki a tálca. |
| W2 | Nézd meg a macska körüli területet világos és sötét háttérkép előtt is. | Nincs fekete, fehér vagy szürke négyzet a macska körül. Csak a macska látszik, éles pixelekkel. |
| W3 | Kattints a macskára, majd az alatta lévő asztali ikonra vagy ablakra. | A kattintás átmegy a macskán az alatta lévő elemre. A macska nem kap fókuszt, és nem aktiválódik. |
| W4 | Nyiss meg egy maximalizált ablakot, például a böngészőt, és kattints bele. | A macska továbbra is a böngésző fölött látszik (mindig felül). |
| W5 | Nézd meg a tálcát, és nyomj Alt-Tab, majd Win-Tab billentyűt. | A macskához nem tartozik tálcagomb, és nem szerepel az Alt-Tab vagy a Feladatnézet listájában. |
| W6 | Keresd meg a tálcaikont a rendszertálcán (a „^” alatt is lehet). | Ott van a macska ikonja, élesen. A jobb gombos menüben egyetlen pont van: **Kilépés**. |
| W7 | Válaszd a **Kilépés** pontot. | A macska eltűnik, a folyamat leáll, és a tálcaikon is eltűnik. |
| W8 | Indítsd újra, és figyeld 2–3 percig. | Ül, néha pislog, jobbra-balra sétál (balra menet balra néz), a képernyő szélén megfordul és nem lóg ki. Kurzor nélkül 1–2 perc után elalszik („z” betűk). |
| W9 | Az alvó macska fölé vidd a kurzort, de ne kattints. | Felébred és leül. |
| W10 | Várj kb. 5 másodpercet, majd vidd a kurzort 100–150 px-re a macska mellé, kicsit fölé. | A macska odasétál a kurzor alá, és leül. Ha a kurzor pont fölötte van, pislog. |
| W11 | Kapcsold be a tálca automatikus elrejtését, vagy helyezd át a tálcát a képernyő tetejére vagy oldalára. | A macska követi az új `availableGeometry` alsó szélét. A naplóban megjelenik egy `available geometry ...` sor. |
| W12 | Állítsd a kijelző skálázását 150%-ra (Gépház → Kijelző), és indítsd újra az alkalmazást. | A macska nagyobb, a pixelek élesek (nem mosódnak el), és továbbra is a tálca fölött áll. |
| W13 | Több monitorral: cseréld meg, melyik az elsődleges kijelző. | A macska átkerül az új elsődleges kijelző aljára. |

## Linux, X11 (például Ubuntu Xorg munkamenet, KDE X11, XFCE, Cinnamon)

Ellenőrizd, hogy X11-en vagy:

```bash
echo $XDG_SESSION_TYPE
```

Ennek `x11`-et kell kiírnia.

| # | Lépés | Elvárt eredmény |
|---|---|---|
| L1 | Indítsd el az alkalmazást. | A macska a panel vagy dokk **fölött** áll, a lába a panel felső szélén. A naplóban nincs Wayland-figyelmeztetés. |
| L2 | Nézd meg a macska körüli területet. | Nincs fekete négyzet a macska körül. Ha van, akkor nem fut kompozitor: XFCE-n kapcsold be a Beállítások → Ablakkezelő finomhangolása → Kompozitor lehetőséget, i3/Openbox alatt indíts el egy kompozitort (például `picom`), és indítsd újra az alkalmazást. |
| L3 | Kattints a macskára, majd az alatta lévő ikonra vagy ablakra. | A kattintás átmegy. A macska nem kap fókuszt. |
| L4 | Maximalizálj egy ablakot, és kattints bele. | A macska fölötte marad (mindig felül). |
| L5 | Nézd meg a panelt vagy tálcát, nyomj Alt-Tab billentyűt, és nézd meg a munkaterület-váltót is. | A macska nem szerepel a tálcán és az Alt-Tab listában. Ha mégis szerepel, ellenőrizd: `xprop` → kattints a macskára (az átkattintás miatt nehéz lehet; inkább: `xwininfo -root -tree \| grep catpet`, majd `xprop -id <ID> _NET_WM_WINDOW_TYPE _NET_WM_STATE`), és jegyezd fel az asztali környezet nevét. |
| L6 | Keresd meg a tálcaikont. GNOME alatt ehhez az *AppIndicator* bővítmény kell. | A macska ikonja ott van. A jobb gombos menüben egyetlen pont van: **Kilépés**. Ha nincs tálca, a naplóban `no system tray available` figyelmeztetés látszik, és az alkalmazás fut tovább. |
| L7 | Válaszd a **Kilépés** pontot. A második körben terminálból Ctrl+C-vel lépj ki. | Mindkét esetben tiszta kilépés (exit 0). |
| L8 | Figyeld 2–3 percig. | Ugyanaz, mint a W8 pontban. |
| L9 | Az alvó macska fölé vidd a kurzort. | Felébred és leül. |
| L10 | Várj kb. 5 másodpercet, majd vidd a kurzort 100–150 px-re a macska mellé. | Odasétál a kurzor alá, és leül. |
| L11 | Méretezd át vagy helyezd át a panelt, vagy kapcsold be az automatikus elrejtését. | A macska követi az új alsó szélt. |
| L12 | HiDPI esetén (például `QT_SCALE_FACTOR=2 python -m catpet`) | A pixelek élesek, a macska a panel fölött áll. |

## Linux, Wayland (GNOME, KDE Plasma Wayland)

Itt csak az elvárt, dokumentált korlátokat kell megerősíteni.

| # | Lépés | Elvárt eredmény |
|---|---|---|
| WL1 | Indítsd el: `python -m catpet -v` | A naplóban látszik a `running on Wayland: ...` figyelmeztetés. Az alkalmazás **nem omlik össze**. |
| WL2 | Figyeld meg az ablakot. | Az animáció fut. A pozíció, a „mindig felül” viselkedés és a kurzorreakció valószínűleg **nem** működik (lásd README). Ez elfogadott. |
| WL3 | Indítsd XWaylanddel: `QT_QPA_PLATFORM=xcb python -m catpet -v` | Az L1–L11 pontok többsége teljesül. Jegyezd fel, melyik nem. |
| WL4 | Lépj ki a tálcamenüből vagy Ctrl+C-vel. | Tiszta kilépés. |
