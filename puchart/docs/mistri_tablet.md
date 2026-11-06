# Mistři stavby her na tablet – co dělají a co si vzít (rešerše 6. 11. 2026, 7 hledání)

| Mistr | Hra | Co je jejich trik | Zdroj | Pro Puchart |
|---|---|---|---|---|
| **Chair Entertainment** (Epic) | Infinity Blade (2010–13), první Unreal na iOS, 5 měsíců | „Náš háček byla grafika“ – postavy a prostředí dělané jako pro konzoli (Gears of War), ale **malé uzavřené arény** místo otevřeného světa; „lidé nechtějí levnou verzi konzolové hry, chtějí vlastní zážitek“ | engadget 2011-03-02, gamespot 1100-6301472, pocketgamer.biz 27932 | Krása soustředěná do **míst, kam se dívá hráč** (hrad, nádvoří); okolí jednodušší |
| **Epic – Niklas Smedberg** | GDC 2012 „Bringing AAA Graphics to Mobile“; UE4 mobil HDR/PBR/IBL | AAA techniky převedené na mobil: zapečené světlo, jednoduché PBR, obrazové osvětlení | gdcvault 1015552, 1020756 | Zapečené světlo + odraz z oblohy místo světel za běhu |
| **Gameloft – Romain Sididris** | Asphalt 8, Modern Combat 5 (GDC 2014) | rozdíly desktop × mobil měřené benchmarkem: CPU, GPU, paměť zvlášť | gdcvault 1021289 | Měřit každou složku zvlášť (už máme panel; přidat paměť textur) |
| **thatgamecompany** | Sky: Children of the Light | vlastní engine; **osvětlení okolí: dynamická cubemapa kolem hráče, paprsky počítané na CPU**, ne GPU (GPU šetří na obraz); umění postavené na denní době a počasí jako vrstvách | gdcvault 1026903, gamedev.net 994 (GDC 2026 přehled – NEOVERENO z originálu) | Okolní světlo do koutů/interiérů levně: světelné sondy / cubemapa na CPU místo GPU efektů |
| **Cornfox & Bros.** | Oceanhorn 2 | cíl „konzolová kvalita na mobilu“; přechod Unity → UE4; Switch začal na **13 FPS**, odladěno na 30 | unrealengine.com spotlight 2019, nintendojo | I mistři začínají pomalu – postupné ladění podle měření je normální |
| **Feral Interactive** | Rome: Total War, Alien: Isolation (iOS/Android) | port „bez kompromisů“; **3 profily kvality**: nejvyšší kvalita / výkon (vyšší FPS) / šetření baterie; nové vyhlazování hran | toucharcade 2021-01-14 a 2021-12-16, gfinityesports interview | Volba profilu pro hráče (kvalita / plynulost / baterie) místo jednoho nastavení |
| **Tencent – Xiaoxin Guo** | GDC: shading pipeline pro 1080p 60 FPS napříč hardwarem; SIGGRAPH 2024 GPU-driven rendering na mobilu | škálovatelný shading podle výkonu zařízení | gdcvault 1029284/1028837, advances.realtimerendering.com/s2024 | Shadery ve 2–3 úrovních (tablet vs. slabší zařízení) |
| **ustwo** | Alba (otevřený svět, Apple Arcade) | jednoduché tvary + barvy + dekály, rozpočet textur od 1. dne | ustwogames.co.uk/news/the-environment-art-of-alba… | Rozpočet textur jako pravidlo (rozpocty.json) |
| **miHoYo** | Genshin Impact | dvě vykreslovací cesty PC/konzole × mobil, stylizované PBR | docswell UnityJapan KWRPQ5 | Zvlášť „tabletová“ verze modelů a shaderů |
| **Google Android** | průvodce osvětlením pro mobil | **zapečené světlo je nejlevnější**; obsahuje i odražené světlo; pozor na velikost lightmap (paměť) | developer.android.com/games/optimize/lighting-for-mobile-games-with-unity | Potvrzuje náš plán zapečeného světla |

## Společné rysy mistrů
1. **Soustředit krásu** tam, kam hráč kouká (Chair) – ne všude stejně.
2. **Světlo předpočítané** (zapečené, sondy, CPU cubemapa) – GPU kreslí jen obraz (Sky, Epic, Google).
3. **Profily kvality** pro hráče a zařízení (Feral, Tencent).
4. **Měřit složky zvlášť** a ladit postupně – i Oceanhorn 2 začal na 13 FPS (Gameloft, Cornfox).
5. **Vlastní mobilní cesta**, ne zmenšená PC verze (miHoYo, Chair: „vlastní zážitek, ne levná kopie“).
6. **Rozpočty od začátku** (ustwo).

## Co z toho přidat do plánu Puchartu
- Zapečené světlo (už v plánu) + **světelné sondy / cubemapa** pro interiéry (Sky).
- **Profily kvality**: Krása / Plynulost / Baterie (Feral) – navázat na teplotní řízení (ADPF).
- Hrad a nádvoří jako „aréna“ s nejvyšším detailem, údolí jednodušší (Chair).
- Panel měření rozšířit o paměť textur a čas CPU/GPU zvlášť (Gameloft).

Odkazy: https://www.engadget.com/2011-03-02-infinity-blade-in-finite-time-how-chair-made-its-ios-hit-in-fiv.html ;
https://gamespot.com/articles/infinity-blade-completed-in-five-months/1100-6301472/ ; https://gdcvault.com/play/1015552/Bringing-AAA-Graphics-to-Mobile ;
https://gdcvault.com/play/1020756/Next-Generation-AAA-Mobile ; https://gdcvault.com/play/1021289/AAA-Mobile-Games-Development ;
https://gdcvault.com/play/1026903/Art-of-Sky-Children-of ; https://gamedev.net/news/994-dynamic-environment-lighting-in-sky-children-of-the-light-gdcrewind-gdc2026/ ;
https://www.unrealengine.com/en-US/spotlights/switching-to-unreal-engine-cornfox-bros-is-moving-mobile-gaming-forward-with-oceanhorn-2 ;
https://toucharcade.com/2021/01/14/feral-interactive-upcoming-games-ios-android-interview-alien-isolation-port-keyboard-mouse-ios-14-pricing-total-war/ ;
https://toucharcade.com/2021/12/16/alien-isolation-mobile-review-frame-rate-resolution-performance-battery-saver-ipad-pro-iphone-11-settings/ ;
https://www.gfinityesports.com/article/interview ; https://www.gdcvault.com/play/1029284/Practical-High-Performance-Rendering-On ;
https://advances.realtimerendering.com/s2024/index.html ; https://ustwogames.co.uk/news/the-environment-art-of-alba-a-wildlife-adventure/ ;
https://developer.android.com/games/optimize/lighting-for-mobile-games-with-unity?hl=en
