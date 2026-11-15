# Výkon: Havran × Puchart, postavy, měřicí panel (rešerše 15. 11.)

Míša 15. 11.: „Puchart se neseká, má asi méně hustou louku a nemá postavy – mrkni, jak postavy dělají jiné hry“; „monitor
měření dost bere“; „mohlo zkreslit měření, když na pozadí běžel Chrome a Claude?“ (ano – zavřít aplikace, letadlo, vychladlý tablet).
Značky: **M** naměřeno na tabletu, **S** podezření, **Z** potvrzeno ve zdrojích Godotu 4.4.1.

## Havran × Puchart
| | Havran | Puchart |
|---|---|---|
| 3D, MSAA, FPS, fyzika | 0,75, ne, 30, 60 Hz + interpolace | totéž |
| stín slunce (tablet) | ORTHOGONAL do 40 m, 2048, `soft_shadow_filter_quality.mobile=2` | 2 splity do 40 m, 2048, filtr 1 |
| louka | trs 0,36 m, plná do 20 m, řídne do 80 m, 5 vrstev, buňky do 90 m, stín louky ano (`louka.gd:1327`) | 0,5 m, 14→60 m, dosah 66 m, 1 vrstva, stíny ne, v lese do 18 m |
| rostliny | dosah 115 m | zapečené, buňky jen kolem hráče |
| uzly / VRAM | 28,7 tis. / 894 MB | 3,3 tis. (mez 8000) / 445–515 MB |
| postavy | 36 | 0 |
Ustálený snímek Puchart NENÍ lepší (M: les p50 30–53 ms); rozdíl jsou **špičky** – Puchart na tabletu nic nestaví.

## Postavy (lide.gd má: ruční krok animací, 8 nejbližších plně, 10 fps do 45 m, 4 fps do 70 m, mimo záběr nic, sukně 4, hlava 6)
- Z: v Compatibility každý krok animace znovu nahraje celou texturu kostí a skinuje každý povrch zvlášť (`mesh_storage.cpp:2402`);
  postavy mají 3 povrchy, 89 kostí, ~7 tis. troj. (Godot #88954: animace v OpenGL hlavní úzké hrdlo).
- Z: jakýkoli `SkeletonModifier3D` (i neaktivní) = Skeleton3D se aktualizuje každý snímek (`skeleton_3d.cpp:441`).
Zdroje: github.com/godotengine/godot/issues/88954; Godot docs „animating thousands of fish“ (VAT); forum.godotengine.org
„performance of crowds of animated rigged characters“; GDC „Massive Crowd on Assassin's Creed Unity“ (AI LOD: plné do 12 m,
loutky 12–40 m); godotengine.org „design of the SkeletonModifier3D“.

## Plán (každý bod variantou Měřicí trasy)
1. Lehký monitor při trase: PSS a log jen na hranicích úseků, `node_added` jen čítač, „pod křížem“ vypnuto, popisek 1×/s (S ~0,3 ms/snímek).
2. Strop aktualizací koster za snímek (střídání, ~6) i pro chodící postavy (S 2–6 ms ve vsi).
3. Postava = 1 povrch (atlas) – 3 průchody skinování → 1 (S ~⅓ ceny skinování).
4. Modifikátory z kostry pryč (remove_child) u postav mimo `modif_max` a daleko (S ~1 ms).
5. Daleké postavy: nad 45 m bez animace, dohled 70 → 50 m; později impostory/VAT.
6. Louka jako Puchart: trs 0,5 m, hustota do 60 m, buňky louky bez stínu (M: stín louky největší cena trávy, 0.99992 louka 27 → 17).
7. Špičky ze stavby za běhu: rozpočet vytváření uzlů v plánovači, méně uzlů, test zastavení na louce (103–129, 447–463).
8. Filtr stínu slunce 2 → 1 jako Puchart (M: stín slunce největší cena v lese).
