# Kůň: animace (Míša 4. 11. „na koni si dáš záležet… na nových animacích“) – rešerše 4. 11.
Současný `modely/kone/kun_hnedak.glb` (Sketchfab Horse, MAXDESIGN-3D, CC-BY) = jedna animace 31 s, chody vyřezané
(krok, cval, stání, pastva); chybí klus, vzad, otáčení.

Hotový realistický CC kůň se stáním + krokem + klusem + cvalem NENÍ (prohledáno: Quaternius, Kenney, Poly Pizza,
Sketchfab CC, OpenGameArt, itch.io, Míšin Disk – jen `horse.glb` bez kostry).
1. **henry_7 „Horse“** – https://sketchfab.com/3d-models/horse-a6f860e43e364619bccb174a1ac7d0c9 – CC-BY 4.0, 30 750 ploch,
   **28 animací** (názvy veřejně nevypsané), realistický, hříva z karet, westernové sedlo (odstranit?). Stáhnout může
   jen přihlášený uživatel (Míša). Nejdřív ověřit seznam animací na stránce (klus, vzad, otočky, pastva).
2. Akhal-Teke (animalanimator, CC-BY) 162 tis. troj., 3 animace – jen zdroj cvalu pro retargeting.
3. Quaternius Animated Animal Pack (CC0/QAL nejasné) – low-poly, bez klusu – nevhodný.
4. flairetic Toon Horse (CC-BY) – jediný s potvrzeným klusem, toon – jen předloha časování.
Nepoužitelné: WildMesh Horse 2.0 (placený / demo CC-BY-NC), Star Equestrian (vytažený herní obsah).

Doplnění chybějících chodů: retargeting v Blenderu (Copy Rotation + bake) na naši kostru; procedurální IK kopyt
v Godotu 4.4 jen vlastním řešičem (nové IK uzly až 4.6).
