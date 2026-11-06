# Puchart ve srovnání se světem (rešerše 6. 11. 2026, 6 hledání – rychlý přehled, ne vyčerpávající)

## Co ve světě existuje
| Typ | Příklady | Platforma | Co mají / nemají oproti Puchartu |
|---|---|---|---|
| AAA historická hra na skutečném místě | Kingdom Come: Deliverance 1/2 (Warhorse, CZ) – Talmberk, Trosky, Rataje | PC, konzole | Měřítko krásy a příběhu; hrady jsou **interpretace**, ne rekonstrukce z DMR; žádná mobilní verze |
| Středověký budovatel | Manor Lords (1 vývojář, PL) | PC, Xbox | Realistický vzhled od jednoho člověka; na tablet oficiálně ne |
| Japonsko – obnovené hrady na skutečném místě | Edo Castle Tower (AR), Takiyama AR, Iimori Castle VR (s minihrou), Yashima Castle, Azuchi Castle, Akashi, „Nishi-Harima yamajiro GO“ | iOS/Android | Nejblíž nápadem: **hrad v ruinách obnovený na skutečném místě, na mobilu**. Ale většinou AR/VR turistické aplikace obcí – nehraje se, nechodí se volně krajinou |
| Vědecké „serious games“ | Yrsum (Itálie, LiDAR + archeologie, ves 11.–14. st.), Fort Ross (USA, Unity + LiDAR), Larochette (Lucembursko), Sammichele di Bari | PC/web | **Stejná metoda jako my** (LiDAR/DMR + prameny), ale malé, akademické, krátkodobé |
| Komunitní rekonstrukce | Vianden Castle 1485 (Roblox, 3 roky práce), německé zříceniny v Unreal 4 | Roblox/PC | Nadšenci dělají přesné hrady, ne celou krajinu |
| Mobilní středověk | Iron Blade, Elder Scrolls: Castles, Townsmen, Drova (2026, pixel art) | Android/iOS | Fantasy nebo strategie, ne realistická procházka po skutečném místě |
| Godot na Androidu | stovky malých her (itch.io) | Android | Nic realistického 3D na skutečném terénu |

## Kde je Puchart jedinečný
Nenašel jsem žádný projekt, který spojuje **všechno najednou**: skutečný terén 1 m (DMR 5G) + historický stav krajiny
k roku (1393) + rekonstrukce konkrétních zaniklých hradů podle archeologie + volná 3D procházka + realistický vzhled
ve stylu KCD + **běh na tabletu**. Japonské aplikace mají místo a mobil, ale ne hru; Yrsum/Fort Ross mají metodu, ale ne
krásu ani rozsah; KCD má krásu, ale ne mobil a ne vědeckou rekonstrukci. Puchart je v této kombinaci **nejspíš ojedinělý**
(s výhradou: rychlá rešerše, malé projekty nemusí být na webu vidět).

## Jak na tom jsme vzhledem
- **Proti KCD2:** jasně níž (osvětlení, modely postav, detail, výkon), což je u tabletu a jednoho týmu očekávané. KCD je měřítko.
- **Proti mobilním hrám:** vzhledem nad většinou mobilního středověku (realistický terén, les, zdivo); výkon zatím horší
  (les 58–71 ms vs. cíl 33–40 ms).
- **Proti japonským hradním aplikacím a serious games:** větší rozsah (2×2 km krajiny), volný pohyb, interiéry, víc doložení.

## Kde máme rezervy proti světu
1. **Hratelnost** – všichni úspěšní (KCD, Iimori VR s minihrou, Manor Lords) mají cíl nebo úkol; my zatím procházku.
2. **Postavy a život** – KCD, Manor Lords; u nás ves Předhradí prázdná.
3. **Osvětlení** – KCD má zapečené/GI světlo; my jen přímé slunce + AO ve vrcholech (rezerva: lightmapy v Blenderu).
4. **Výkon lesa** – mobilní hry šetří impostory/LOD; to je náš úkol 11.
5. **Ukázat zdroje** – japonské aplikace a Yrsum ukazují „takhle to bylo / takhle je to dnes“; my máme značení DOLOZENO/
   REKONSTRUKCE v datech, ale hráč ho nevidí → nápad: režim „dnes vs. 1393“ (srovnání se skutečnou zříceninou).

## Odkazy
- KCD a skutečná místa: https://www.dexerto.com/gaming/compare-kingdom-come-deliverance-with-real-life-locations-thanks-to-this-genius-website-3402066/ ,
  https://80.lv/articles/this-is-how-kingdom-come-deliverance-ii-locations-look-in-real-life , https://kingdomcomedeliverance.wiki.gg/wiki/Sasau_region
- Manor Lords: https://pcgamer.com/games/city-builder/manor-lords-release-date-times , https://mezha.ua/en/2023/10/26/manor-lords-is-another-realistic-urban-planning-simulator-from-a-lone-developer/
- Japonsko: https://apps.apple.com/app/id1615348081 (Iimori Castle VR), https://apps.apple.com/us/app/takiyama-ar/id1088882927 ,
  https://appfollow.io/ios/edo-castle-tower-keep-resurrec/1501321509 , https://web.pref.hyogo.lg.jp/whk02/yamajiro/arapri2.html ,
  https://web.pref.hyogo.lg.jp/ks24/akashi-appli.html , https://himejicastle.jp/en/ar.html
- Serious games: https://iris.unibas.it/handle/11563/156569 (Yrsum), https://scholars.duke.edu/publication/1012916 (Fort Ross),
  https://orbilu.uni.lu/bitstream/10993/51062/11/Gamifying%20the%20Intangible%20History%20of%20Larochette.pdf
- Komunita: https://devforum.roblox.com/t/vianden-castle-1485/2871663 , https://kotaku.com/german-medieval-ruins-recreated-in-unreal-engine-4-1702773357
- Mobil: https://gamingonphone.com/news/drova-forsaken-kin-arrives-on-mobile-in-april-23-2026-with-its-brutal-celtic-based-old-school-arpg-journey ,
  https://www.gematsu.com/2023/09/simulation-game-the-elder-scrolls-castles-now-available-in-early-access-for-android
