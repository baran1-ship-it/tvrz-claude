# ZÁVĚR: KCD grafika udržitelná na tabletu – pro Puchart i Havran (6. 11. 2026)

> Společný závěr obou her (Odkaz Havrana, Puchart 1393) na Xiaomi Pad 8 (Adreno 825, Godot Compatibility/OpenGL).
> Leží na větvi `ccr-f2d32673-9fi7m5` v `docs/ZAVER_tablet_grafika.md` (kopie `puchart/docs/`). **Havrane:** přečti
> `git show origin/ccr-f2d32673-9fi7m5:docs/ZAVER_tablet_grafika.md`. Podklady: Havran `docs/radce.md` (kapitola
> „KCD2 na Androidu“ 20. 10., paměť 21. 10., sekání 2. 11., Vulkan 16. 10.), Puchart `docs/stavba_her_tablet.md`,
> `docs/mistri_tablet.md`, `docs/kcd_grafika_tablet.md`, `docs/srovnani_svet_6_11.md`.

## 0. ROZHODNUTÍ MÍŠI (6. 11.) – platí nad vším níže
**„Chceme krásu i plynulost; v extrémních situacích povoluji automatiku (degradaci grafiky), ale plný obraz.“**
- **3D se kreslí v plném rozlišení** (100 %) – žádné trvalé snížení rozlišení 3D jako řešení výkonu.
- Výkon se získává **u příčiny**: les bez discard + impostory, zapečené světlo, atlasy, LOD, rozpočty, záseky.
- **Automatika jen v extrému** (teplo / dlouhý pokles FPS pod cíl): ubírá **detail** (dohled podrostu, stíny, hustotu
  vzdáleného listí, dosah LOD), **ne rozlišení obrazu**; po zchladnutí se vrací. Hráč to má vidět v panelu.

## 1. Hlavní myšlenka (mistři + Havranova zkušenost se shodují)
**Nesnižovat hustotu a krásu světa – snižovat práci na pixel a dělat dopředu, co jde dopředu.**
- KCD1 na Switchi (slabší čip než náš): stejná vegetace jako PS4, ale **540–720p s TAA**, 30 FPS (Havran radce 20. 10.).
- Genshin na mobilu ~0,5–0,85 M troj./snímek, zvlášť mobilní cesta (miHoYo).
- Mistři (Chair, Epic, thatgamecompany, Feral, Google): **světlo předpočítané**, krása soustředěná kam hráč kouká,
  profily kvality, měření po složkách, rozpočty od začátku.

## 2. Co Havran už ověřil na tabletu (platí pro obě hry)
| Poučení | Důkaz v Havranovi | Stav v Puchartu |
|---|---|---|
| 3D rozlišení 0,5–0,6× – v Havranovi největší páka | 0.58: louka 15–18 → 34–44 FPS | **Míša 6. 11.: ne – plný obraz.** Výkon jinými kroky (§4) |
| Tráva: **alpha-to-coverage + MSAA nebo geometrická stébla bez alfy**, ne discard | 0.58; Quest grass (Adreno 740 90 FPS) | les a podrost Puchartu = alfa karty (58–71 ms) |
| **RAM ~2 GB reálně** (systém + aplikace) → proces ≤ 1,2 GB; pády = OOM, ne GPU | 0.58 pády `alloc_static`, 219 buněk louky | hlídat (halda 408 MB OK); panel RAM z /proc/self/statm |
| Textury ≤ 300 MB (ořez mipmap, ASTC/ETC2) | 1769 → 458 → 414 MB | zkontrolovat (zdivo 1k ✓) |
| Každý importovaný díl přes tabulku tříd: **hrubá kolize, LOD, portál** dřív, než je ve hře | 2. 11.: tři vlny sekání z importů (trimesh, ves bez LOD) | ✓ princip převzat; hrad má dálkovou verzi |
| **Měřič záseků je součást přejímky** | 2 dny sekání nikdo neviděl | ✓ panel „záseky > 40 ms“ (Míšovy fotky: 3 800–8 600!) → řešit |
| Vlákna nesdílí stav (šum, pole) – pády při teleportu | 0.57–0.58 | Puchart louka/les: ověřit stejné |
| Stíny 1 kaskáda 40 m | 0.58 | ✓ |
| **Vulkan padá při vstupu do hry** (Godot 4.4) – příčina nikdy nezjištěna | radce 16. 10. | nevyřešeno; Godot 4.6 opravil pády Vulkanu na Adreno → nový test s logem pádu v aplikaci |

## 3. Nové z rešerše 6. 11. (Havran to zatím neměl)
1. **Zapečené světlo z Blenderu (Cycles → UV2 → lightmapa)** – Godot Compatibility lightmapy umí zobrazit, ne péct
   (docs 4.4). Je to „KCD vzhled“ (SVOGI v KCD = měkké nepřímé světlo) bez ceny za běhu. Začít jednou místností.
2. **Okolní světlo předem / na CPU** (Sky: cubemapa kolem hráče počítaná na CPU) – interiéry nejsou černé.
3. **Profily kvality pro hráče**: Krása / Plynulost / Baterie (Feral Alien: Isolation).
4. **Teplo**: po 30 min tablet zpomalí (Lineage W 60 → 32 FPS) → měřit dlouhé sezení, snižovat kvalitu podle teploty
   (Android ADPF) dřív, než se čip přiškrtí.
5. **Pořadí kreslení** neprůhledné zepředu → obloha → průhledné (early-Z, −7 ms na Adreno).
6. **Impostory lesa** (Godot doplněk Octahedral Impostor LOD; strom z dálky 2 troj., 1024 impostorů ≈ 8 MB).
7. **Atlasy materiálů** – cíl < 400 kreslení (Puchart dnes 300–900).

## 4. Pořadí pro obě hry (od největšího účinku)
2. **Les/tráva bez discard** (A2C+MSAA nebo geometrie) + **impostory** stromů.
3. **Zapečené světlo** (jedna místnost → celé stavby).
4. **Záseky** – podezření Míši (6. 11.): **oheň, krby, louka a vykreslování**. Ověřit měřením po jednom (vypnout oheň/krby →
   louku → porovnat záseky > 40 ms na stejné trase): částice ohně (CPU částice, overdraw průhledných plamenů, první
   kompilace shaderu = zásek při prvním zobrazení → předehrát shadery), světla krbů (každé světlo v Compatibility = další
   průchod objektů v dosahu), louka (stavba buněk v hlavním vlákně, alokace bufferů – Havran 21. 10.), vykreslování
   (počet kreslení, průhlednost). Puchart: ohniště kuchyně, kamna, světla místností, louka – stejná podezření.
5. Trojúhelníky ≤ 1,2 M, kreslení < 400, textury ≤ 300 MB, RAM ≤ 1,2 GB.
6. **Automatika jen v extrému** (teplo, dlouhý pokles FPS): ubírá detail, ne rozlišení; 30min měření. Profily pro hráče volitelně.
7. Vulkan: test na 4.7 s logem pádu v aplikaci (ne zahodit – příčina neznámá).

## 5. Pravidla, která z toho plynou (zapsat do CLAUDE.md obou her)
- Krása i plynulost zároveň, **plný obraz** (3D 100 %). Výkon u příčiny (per-pixel práce, světlo dopředu, LOD, rozpočty).
- Automatická degradace detailu jen v extrému (teplo / dlouhý pokles), nikdy rozlišení; po zchladnutí zpět.
- Každá nová vrstva světa (import, vegetace, voda) má rozpočet a měření dřív, než jde do APK.
- Tablet: RAM ~2 GB reálně, 30 FPS = 33,3 ms, záseky > 40 ms jsou chyba, ne šum.
