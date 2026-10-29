# Oděvy a zbroj – zdroje (stav 29. 10.)

Kostra: Quaternius Universal Base Characters / UAL, 65 kostí (`root … ball_leaf_r`). „Kostra = naše“ znamená, že jména
a pořadí kloubů ve skinu se shodují s `../Male_Peasant.gltf`. Ověřeno skriptem: porovnání seznamu jmen a u GLB navíc
kontrola, že IBM kosti = inverze klidové polohy (chyba < 1e-6). Trojúhelníky se počítaly z indexů.
Textury jsou nejvýš 1024 px. Kusy Peasant a Arms odkazují na sdílené textury o složku výš (`../T_Peasant_*.png`,
`../T_Regular_*.png`), takže nevznikají duplikáty.

## A. Quaternius – Modular Character Outfits – Fantasy [Standard] (CC0 1.0)
Zdroj: https://quaternius.itch.io/modular-character-outfits-fantasy (také https://quaternius.com/packs/modularcharacteroutfitsfantasy.html).
Stáhnuto z Míšova Disku: `Modular Character Outfits - Fantasy[Standard].zip` (id 1WfLfTbQ_c9QywHAv3Roi5Ptf0UCGoLYX).
Autor: Quaternius. Licence: CC0 (License_Standard.txt v balíku). Použita složka `Exports/glTF (Godot-Unreal)/Modular Parts`.
Textury Ranger zmenšeny ze 4096 na 1024 se stejnými názvy.

| soubor | slot | kostra = naše | troj. | poznámka |
|---|---|---|---|---|
| Male_Peasant_Body.gltf | kosile (halena s páskem) | ano | 3856 | dobově použitelné |
| Male_Peasant_Arms.gltf | kosile (rukávy + holé předloktí, kůže MI_Regular_Male) | ano | 5338 | |
| Male_Peasant_Legs.gltf | nohavice | ano | 1112 | |
| Male_Peasant_Feet.gltf | boty (nízké / onuce) | ano | 2588 | |
| Male_Ranger_Body.gltf | prosivanice / svrchni (zelená kazajka s řemeny a pásy) | ano | 4606 | vzhled spíš fantasy, pásy jsou součástí meshe |
| Male_Ranger_Arms.gltf | rukávy + chrániče předloktí (náhrada za rukavice) | ano | 4928 | |
| Male_Ranger_Legs.gltf | nohavice | ano | 1128 | |
| Male_Ranger_Feet_Boots.gltf | boty (vysoké s přezkami) | ano | 9172 | přezky na holenkách nejsou dobové |
| Male_Ranger_Head_Hood.gltf | kapuce | ano | 2136 | prochází helmou, s helmou nekombinovat (nebo kapuci zmenšit) |
| Male_Ranger_Acc_Pauldron.gltf | plat (jen jeden náramenník) | ano | 1376 | doplněk, ne kabátec |
| Female_Peasant_Body / Arms / Legs / Feet.gltf | kosile / kosile / nohavice / boty | ano | 2188 / 6848 / 1944 / 2588 | |
| Female_Ranger_Body / Arms / Legs / Feet.gltf | svrchni / rukávy a chrániče / nohavice / boty | ano | 4570 / 8508 / 1204 / 9172 | |
| Female_Ranger_Head_Hood.gltf / Female_Ranger_Acc_Pauldrons.gltf | kapuce / plat (náramenníky) | ano | 2136 / 1376 | |
| T_Ranger_BaseColor/Normal/ORM.png | textury Ranger | – | – | 1024 px |
| T_Ranger_3_BaseColor.png, T_Peasant_2_BaseColor.png | barevné varianty (vyměnit albedo v materiálu) | – | – | 1024 px |

## B. Kusy bez kostry, přidané na naši kostru (pevně na jednu kost)
Postup: import do Blenderu 4.2 (`--disable-autoexec`) → měřítko a poloha podle změřené hlavy a pasu postavy
(Superhero_Male_FullBody: hlava je široká 0,18 m, temeno je ve výšce 1,81 m; Male_Peasant: pas v 1,05 m má rozměry
0,30 × 0,26 m) → export GLB → skript přidá kostru, skin a IBM z Male_Peasant.gltf. Všechny vrcholy mají váhu 1,0
na jedné kosti. Kusy se nasazují jako ostatní oděvy na stejný Skeleton3D, BoneAttachment není potřeba.
Kontrolní snímky se zkouškou pózy (otočení kosti Head/pelvis hýbe kusem) jsem si prohlédl.

| soubor | slot | kost | troj. | zdroj | autor | licence |
|---|---|---|---|---|---|---|
| Prilba_Topfhelm.glb | prilba (hrncová přilba / topfhelm; spíš turnajová, kolem 1390 už starší typ) | Head | 286 | https://opengameart.org/content/bucket-helmet | Lucian Pavel | CC0 |
| Prilba_Klobouk.glb | prilba (železný klobouk / kettle hat, okraj 0,46 m) | Head | 6192 | https://opengameart.org/content/helmet-1 (soubor untitled_0.blend) | Olexanders | CC0 |
| Opasek_Kozeny.glb | opasek (kožený opasek na boky, přezka vpředu, sedí pod páskem haleny) | pelvis | 492 | https://opengameart.org/content/belt | Paul Wortmann (textury: yughues, „commission-medieval“, CC0) | CC0 |

Klobouk neměl v souboru texturu (chyběla externí .jpg), proto má jednoduchý ocelový PBR materiál (kov 1,0, drsnost 0,45).
Měřítka a polohy jsou nastavené podle hlavy a pasu postavy v klidové póze. Ve hře je to NEOVĚŘENO: snímek v Godotu chybí.

## C. Nenalezeno / chybí (stažení zde nebylo možné)
- **krouzky** (drátěná košile), **plat** (kabátec / prsní plát), **svrchni** (dobový waffenrock/jupon), **kukla (coif)**,
  **rukavice / plechové rukavice**, **plast**, **chaperon**: na CC0 webech s přímým stažením (OpenGameArt, Quaternius
  Standard) nic použitelného není. Poly Pizza a itch.io vrací přes proxy 403.
- **Quaternius Source** (stejný balík, 20 USD, CC0) má všech 12 oděvů včetně rytíře (plátová zbroj), šlechtice a dalších.
  Jsou na stejné kostře, takže se nemusí znovu rigovat. Doporučeno koupit.
- **Sketchfab CC-BY** (stažení potřebuje přihlášení / API token, tady chybí; licence podle API „CC Attribution“,
  na stránce ověřit). Kusy jsou bez kostry, rigovat přenosem vah z těla. Kandidáti:
  - Bascinet Hundsgugel (nuist, 4574 troj.): https://sketchfab.com/3d-models/a5ffb06276ce4ff6b82ae7083a9f5c43 (přesně 90. léta 14. st.)
  - Medieval Bascinet with Visor (Pete.Panousis, 1966): https://sketchfab.com/3d-models/016b0f84c7394b5ca2006c1af3ba6aec
  - Bascinet + Visor (waysofdarkness, 2649): https://sketchfab.com/3d-models/880450ce10fa47d2b02c2d625013e8e6
  - Burgundian Kettle Hat Low Poly (Destroyanad, 1494): https://sketchfab.com/3d-models/c4add75769e542a8a38b3864fb78c9af
  - Kapalin 1411 (skald98, 49728): https://sketchfab.com/3d-models/b001a8950e2b4dc2ba9a22e5d85a5c61
  - Hauberk (askei, 798): https://sketchfab.com/3d-models/8881e32f0595469fa12b18e28155cc78
  - Gambeson (Leon.Steiner, 43557): https://sketchfab.com/3d-models/0fc44d2876ed449ca9473e78c83a8d39
  - Gambeson de combate (Gnomon_Mayor, 27472): https://sketchfab.com/3d-models/34df2f8ed156454e8657a28f1bb875c9
  - Visby coat of plates (jarvik1066, 446784, nutno zredukovat; Visby 1361): https://sketchfab.com/3d-models/7cf6f5db03a8425d89d1a860382b7f11
  - Coif-inworks (rsihvo, 17231): https://sketchfab.com/3d-models/982b0ddd2b634274b06247e60b2b645c
  - Medieval Boots (Peakz, 3312): https://sketchfab.com/3d-models/ddfa994dac18462598bddd8c28c75ef3
  - Tunic – medieval – for animation (Andywoodhead, 18476): https://sketchfab.com/3d-models/b3cf100c7fed4468a193e0133002cc03
  - Medieval Peasant Outfit Free (Red_Ilya, 14141): https://sketchfab.com/3d-models/e7aa183b848646558ceb3a3f449e344b
  - Archer's Cloak (Padarozhnik, 233675): https://sketchfab.com/3d-models/7604044e3c744fd996bf783a3fe9db53
- Kde se ještě hledalo: Míšův Disk (Modely: kromě balíků Quaternius žádné oděvy; v docs je zmínka o `arm_piece_armor.glb`
  23 MB, náloketník), Sketchfab s filtrem CC0 (jen muzejní skeny, např. salada nebo hussar half-armour, které nejsou
  z doby a mají 100k+ troj.), OpenGameArt (Viking helmet 72 MB, Robin Hood hat je kreslený, helmet-2 je fantasy:
  nevzato), Kenney / KayKit (stylizované, jiná kostra), Quaternius Ultimate Modular Men/Women a Knight Pack (jiná kostra,
  plochý styl).
