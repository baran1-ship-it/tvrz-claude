# Rešerše: dlouhý oděv a noha při chůzi, sedu a kleku (13. 11. 2026)

Otázka: jak KCD1/2 a srovnatelné hry drží kotle/sukně/suknice/zástěry na nohou bez propíchnutí stehnem, a za jakou cenu.
Známá chyba u nás: při chůzi prosvítá horní přední část stehna mužským kabátcem po kolena; horních ~25 % sukně je
vázáno na pánev, kořeny řetězů jsou pevně v pase.
Navazuje na `sukne_sed_reserse.md` (12. 11.) – co je tam, se zde neopakuje (PRow parametry, Kawaii tutoriál, recept sedu).

Značení: **[zdroj]** = doloženo odkazem; **NEOVĚŘENO** = bez zdroje / jen odvozeno; „hobby“ = amatérský projekt, slabý zdroj.

---

## 1. Zjištění se zdroji

### 1.1 KCD / Warhorse / CRYENGINE

- **Warhorse veřejně nepopsal, jak váží sukně ani jak řeší nohu.** Jediná technická přednáška k oděvu je GDC Europe
  2015 „Adaptive Clothing System in KCD“ (Tomáš Barák): procedurální přizpůsobení *vrstev* oděvu, aby se nepřekrývaly,
  „kvalita srovnatelná s ručně dělanými“. O nohách, sukních ani kolizích popis nic neříká; video jen pro členy.
  [GDC Vault](https://gdcvault.com/play/1022822/Adaptive-Clothing-System-in-Kingdom),
  [fórum KCD – odkaz na talk](https://forum.kingdomcomerpg.com/t/adaptive-clothing-system-in-kcd/25894)
- Jména kostí sukní v KCD2, zda kabátce používají PRow, a zda mají sedící/klečící postavy speciální animaci kostí sukně:
  **NEOVĚŘENO** (Nexus, Steam, fórum, YouTrack nic nedaly; jediná cesta je otevřít `.chr/.cdf` v KCD2 Modding Tools).
  Komunita jen hlásí, že pláště „s cloth simulací (pohyblivá sukně a rukávy)“ jsou hlavní zdroj kolizí s jinými kusy
  [Nexus KCD2 mod 2761](https://www.nexusmods.com/kingdomcomedeliverance2/mods/2761) – tj. KCD2 nějakou simulaci
  sukní má, typ nedoložen.
- **CRYENGINE – co přesně řeší propíchnutí (Attachment System Tutorial):**
  [CRYENGINE – Attachment System Tutorial](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29450433)
  - Kolize = **projekce, ne simulace**: „růžové“ lozenge na kostech těla vždy odtlačí „modré“ kapsle/koule kostí
    látky; posun „co nejmenší, dokud se nepřekrývají“. Kontrola v pořadí seznamu proxy – „čím méně kontrol, tím rychleji“.
  - **Rotace ven (shortarc / directed rotation) funguje jen, když čep kapsle leží mimo lozenge.** Když animace sama
    vtlačí kořen řetězu do těla, kolize se nevyřeší („Capsule … starts inside of proxy“) – „může nastat i při běžné
    chůzi“. Řešení CRYENGINE: **Translational Projection** = zvláštní socket na *stejném kloubu*, zařazený v seznamu
    **před** kyvadlem, který nejdřív posune samotný kořen ven z lozenge; varianta *Directed Translation* posouvá jen
    v předem dané ose (spolehlivé, „tunelování velmi nepravděpodobné“), *Shortvec* jen pro málo proxy (jinak skáče
    mezi dvěma lozenge).
  - Pořadí omezení: nejdřív projekce z lozenge, pak ořez do kužele – **kužel má poslední slovo**, příliš malý kužel
    zamkne kapsli v těle.
  - Kapsle řetězu: o něco delší než kost, **25 % překryv s potomkem**, poloměr potomka **o ~2 mm menší**.
  - Mřížka kyvadel (pendula cloth) je výslovně pro `cape_*`, `skirt_*`, `coat_*`; pro sukni **Cycle** (kruh).
    Svisle se nenatahuje, výhoda je „ovladatelnost a stabilita“ (žádné tunelování ani výbuch při otočce/teleportu).
    Příklad pláště 13 × 11 = 143 kyvadel.
- CRYENGINE VCloth: kolize látky „je drahá, nastav jen proxy, které opravdu potřebuješ“; bez proxy látka prochází
  nohama. [CRYENGINE – VCloth Setup](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29799652)

### 1.2 Jak se v praxi váže horní část sukně (otázka 1)

- **Kosti sukně řízené rotací stehna (vydaná mobilní hra, CEDEC 2024, QualiArts/CyberAgent):** pomocný kloub čte
  rotaci **stehna**, rozloží ji (stereografická projekce) na ohyb **vpřed/vzad** a **do stran**; ohyb vpřed/vzad hýbe
  **přední a zadní** kostí sukně společně, boční ohyb bočními. Při malém pohybu nohy **vůle (アソビ, mrtvá zóna)**,
  při dotyku nohy se změní váha následování a sukně se **zvedne** místo propíchnutí. Spojeno s pružinovými kostmi
  („揺れもの“); cíl: bez propíchnutí kolidérů a bez cukání. Běží v Animation C# Jobs **po prolnutí animací**, vše
  v jednom Jobu. Čísla pro vůli/váhy **neuvedena**.
  [QualiArts technote – CEDEC 2024](https://technote.qualiarts.jp/article/82/)
- **Kawaii Physics (UE) „Sync Bone“ (v1.20, 2026):** posun/rotaci zdrojové kosti (stehno/lýtko) vůči referenční
  póze přičte k cílovým kostem sukně. Parametry: `GlobalScale` 0–1 (**začít 0,3–0,5**), křivka podle vzdálenosti
  posunu zdroje, křivka podle podílu délky od kořene (**silně u kořene, slabě k lemu**), filtr směru po osách
  (Positive/Negative – např. jen když noha jde *do* sukně), útlum podle vzdálenosti zdroj–cíl (vnitřní/vnější poloměr
  v cm). Autor: samo částečně pomáhá, spolehlivě až se **kolizemi + vazbou mezi kostmi**. Dřív se to dělalo
  Control Rigem nebo Pose Driverem (RBF).
  [Kawaii Physics – Sync Bone](https://pafuhana1213.github.io/KawaiiPhysics-Portal/en/docs/features/sync-bone),
  [GameMakers.jp](https://gamemakers.jp/article/2026_01_09_128311/),
  [Tutorial Skirt](https://github.com/pafuhana1213/KawaiiPhysics/wiki/Tutorial-Skirt-en)
- **Pomocné kosti a RBF ve vydané hře:** Tekken 8 (CEDEC 2024) zvýšil počet pomocných kostí 34 → **245**; zrychlení
  RBF řešiče o **45 %** rozdělením RBF uzlů na jednotlivé pomocné kosti. Sukně v materiálu konkrétně nejsou.
  [Bandai Namco – Speaker Deck](https://speakerdeck.com/bandainamcostudios/cedec2024-tie-quan-8dejin-hua-sitabu-zhu-gu-tosonoying-yong-li-noshao-jie)
- **Přenos vah z těla na sukni nejbližším bodem je chyba:** Epic (SIGGRAPH Asia 2023) ukazuje, že u pouzdrové sukně
  dává produkční přenos nejbližším bodem **špatně skinovanou přední i zadní část sukně** a ostrý zlom uprostřed šatů
  („vrcholy přiřazené nejbližším bodům na nohách“), v rozkroku část vrcholů na levé, část na pravé noze bez přechodu.
  Jejich metoda: přenést jen jisté shody, zbytek **dopočítat hladce (inpainting)**; maska umělce vynutí dopočet.
  Nezaručuje, že nedojde k průniku. [Abdrashitov et al. 2023, preprint](https://www.dgp.toronto.edu/~rinat/projects/RobustSkinWeightsTransfer/preprint.pdf)
- **Praxe riggerů (fóra):** stehno má váhu kolem své nohy a k druhé noze **plynule** klesá (jinak zlom)
  [Second Life fórum](https://community.secondlife.com/forums/topic/309008-short-skirt-rigging-issue); kost
  „skirt-thigh“ s damped-track na koleno (**bez zkrutu stehna**) deformující jen sukni
  [blenderartists](https://blenderartists.org/t/make-skirt-rig-react-to-leg-movement/1563573); kabát: horní část na
  trup, dolní dynamické kosti z boků [Autodesk fórum](https://forums.autodesk.com/t5/maya-animation-and-rigging-forum/best-process-for-rigging-a-long-coat-amp-character/td-p/10629298);
  pomocné klouby se v DCC řídí a **zapékají** do animace, ale zapečené pomocné klouby dělají potíže při prolínání
  animací [Polycount](https://polycount.com/discussion/comment/2428173).
- Hobby (slabé, pro představu): kořen řetězu přebírá 65 % otočení stehna, středový přední řetěz 100 % podílu stehen,
  zadní 50 %, rozděleno mezi nohy podle úhlu po obvodu [GitHub LeviChan #42](https://github.com/LiteLDev/LeviChan/pull/42);
  chlopně kabátu: vliv nad horním kloubem 0, vzadu plný, na bocích ~2/3, vpředu ~1/6
  [GitHub SWLOR #591](https://github.com/zunath/SWLOR_Haks/pull/591). **NEOVĚŘENO** u vydaných her.
- **RDR2:** bývalý animátor Rockstaru (M. York, livestream) – pohyb šatů v RDR2 „vypadal jako simulace látky, ale
  většinu práce dělala animace kostí“. Jen sekundární zpráva, technicky **NEOVĚŘENO**.
  [GTA Boom](https://www.gtaboom.com/former-rockstar-animator-pulls-back-curtain-on-gta-6-physics-d7ea)
- Witcher 3: šaty Triss nemají pod sukní nohy (řešení modaře: šaty prodloužit k zemi); kliping nohou při překřížení
  v cutscénách nelze opravit bez změny animace. [Nexus W3 6812](https://www.nexusmods.com/witcher3/mods/6812),
  [Nexus W3 5011](https://www.nexusmods.com/witcher3/mods/5011) (komunitní, ne CDPR).
- Assassin's Creed: Ubisoft má vlastní simulaci látky (Motion Cloth, přepsáno na compute shadery, >10× rychlejší na
  PS4/XB1); o nohách a sukních veřejně nic. [GDC Vault](https://www.gdcvault.com/play/1022350/contactUs).
  Bannerlord: oblasti látky se určují **alfou vrcholové barvy** (bílá = plná látka) – tj. horní pás sukně zůstává
  skinovaný. [neoficiální průvodce](https://docs.google.com/document/d/1aHBsO3mzkT0JsbCt9aCOh6CWAFATXwKtSaVb__TYIoo/export?format=pdf).
  Totéž v UE: maska **Max Distance** (0 = jen skin) + **Backstop** (koule, která drží body mimo tělo).
  [Epic – Clothing Tool](https://dev.epicgames.com/documentation/en-us/unreal-engine/clothing-tool-in-unreal-engine)

### 1.3 Prevence propíchnutí při chůzi (otázka 2)

- **Kapsle stehno + kapsle koleno–lýtko** na každé noze; poloměr kolizí sukně ke lemu menší (křivka 1,0 → 0,5).
  [Kawaii Tutorial Skirt](https://github.com/pafuhana1213/KawaiiPhysics/wiki/Tutorial-Skirt-en)
- **Levý a pravý kolidér nohou se mají překrývat zhruba z poloviny**, aby středové kosti neproklouzly mezi nohy;
  kolidéry na prázdném potomku kosti nohy (snadné ladění), posunout lehce dozadu; nad nimi 2 větší kolidéry boků,
  po kterých zvednutá sukně sklouzne zpět. Rozložení 16 řetězů × 3 = 48 kostí; poloměr kostí roste ke lemu tak, aby se
  rozevřené překrývaly; **zamknout osu X** (kost neklouže bokem skrz kolidér).
  [mojamegane – Dynamic Bone sukně](https://mojamegane.hatenablog.com/entry/2019/11/16/061332) (VRChat, bez čísel)
- **Vnitřní kolidér + „TwistCancel“:** kolidéry nohou pod pomocným uzlem `SubLeg` pod pánví (následuje švih stehna,
  ne jeho zkrut). Cena: komponenta na každou kost → výkonnostní hodnocení VRChat „Poor“ téměř jisté.
  [SkirtSupporter](https://sites.google.com/view/skirtsup)
- Příliš velký kolidér = sukně vyskakuje nahoru; místa nejčastějšího průniku: **hýždě a stehna**.
  [Qiita – Magica Cloth](https://qiita.com/GONBEEE_project/items/1e906bed210138ef88e6)
- Rozparky/klíny u herních kabátců jako cílené řešení: **NEOVĚŘENO** (nenalezen herní zdroj). Historicky mají
  kotle klíny a rozparky – ověřit v `obleceni_reserse.md`/rešerši střihu, ne zde.
- Ladění na animaci: v cutscénách W3 i Skyrim modaři potvrzují, že některé animace kliping „nutně“ způsobí a ladí se
  animace, ne sukně (viz 1.2). Konkrétní ladění „per-animace“ ve vydané hře: **NEOVĚŘENO**.

### 1.4 Sed a klek (otázka 3)

- QualiArts (mobil): při sedu se pánev posune na bod židle (řízení těžiště), kolena ohne IK chodidel; sukně se tvaruje
  **heuristickou přitažlivostí kloubů sukně k chodidlům, zapnutou jen během animací sedu** – „zdaleka levnější než
  simulace látky“, bez ručního ladění pro každý kostým, „ne dokonalé“.
  [QualiArts technote](https://technote.qualiarts.jp/article/82/)
- SkirtSupporter: pro sed přestaví kosti (SkirtRoot + SkirtBranch pod pánví), sukně v sedu visí dolů; náhled sedu
  komponentou SittingAnimationSimulator. [SkirtSupporter](https://sites.google.com/view/skirtsup)
- **Zapečení simulace do kostí:** EA Dem Bones (SSDR, Le & Deng 2012) převede libovolnou animovanou síť na kosti +
  váhy; v EA v pipeline od 2015, je i v Maya Bake Deformer a Houdini Skinning Converter. Tj. sed/klek nasimulovat
  offline v Blenderu a zapéct jako klíčové pózy kostí sukně – použití přímo na sukně ve hře **NEOVĚŘENO**.
  [EA SEED – Dem Bones](https://www.ea.com/seed/news/open-source-dem-bones)
- Morf pro sed, ručně animované kosti sukně v sedu (hybrid funguje na židli, ne na zemi): viz `sukne_sed_reserse.md`.

### 1.5 Mobil / cena (otázka 4)

- Nejlevnější doložená cesta ve vydané **mobilní** hře: pomocné klouby řízené stehnem + pružinové kosti + heuristika
  sedu, vše v jednom Jobu po prolnutí animací (QualiArts). Čísla ms **neuvedena**.
- Cena roste s **počtem kontrol kost × proxy** (CRYENGINE: méně proxy = rychleji; Kawaii: při výkonu snížit iterace
  vazeb a počet kolizí; SkirtSupporter: komponenta na kost = drahé).
- Tekken 8: 245 pomocných kostí v bojovce (2 postavy na scéně), RBF −45 % – ukazuje, že desítky řízených kostí na
  postavu jsou běžné, pokud je řídič jednoduchý.
- Plná simulace látky (VCloth, Chaos, Motion Cloth) je na konzolích; na tablet bez měření **NEOVĚŘENO** a podle
  CRYENGINE drahá.

---

## 2. Co z toho plyne pro náš systém

Rámec: Godot 4.4, oděv procedurálně v Blenderu, sukně = 8 řetězců × 3 kosti, řidič `sukne_ridic.gd`
(SkeletonModifier3D) s kapslemi stehen a holení, tablet. Vše níže je **návrh, NEOVĚŘENO měřením**; čísla patří do
`pravidla/…` (žádná čísla v kódu), ne do skriptu.

**Pravděpodobná příčina naší chyby (podezření, ne potvrzená příčina):** horních ~25 % délky je na pánvi a kořeny
řetězů jsou pevné v pase. Tyto vrcholy se s nohou nemohou pohnout vůbec – žádný posun kostí sukně je z kapsle stehna
nedostane. CRYENGINE to popisuje přesně: když animace vtlačí *kořen* do těla, rotační projekce nefunguje a musí se
nejdřív posunout kořen (Translational Projection). Ve všech nalezených řešeních (QualiArts, Kawaii Sync Bone, SubLeg,
skirt-thigh) se **horní pás vpředu hýbe podle stehna**, ne podle pánve. Ověřit izolovaně: vypnout váhy pánve na
předních řetězech (varianta) a změřit test_sukne v chůzi.

Doporučené kroky (v pořadí podle poměru přínos/cena):

1. **Váhy v Blenderu (data, ne kód):** pánev jen na **pásku** (horní okraj, cca do výšky kloubu kyčle –
   přesný podíl NEOVĚŘENO, měřit), pod tím už kost 1 řetězu. Přední a boční řetězy pod páskem plynule
   pánev → kost 1, žádný ostrý přechod. Váhy **nepřenášet nejbližším bodem z nohou** (Epic: chyba vpředu a vzadu
   sukně, zlom uprostřed) – buď váhy z řetězů po obvodu, nebo přenos + hladké dopočítání.
2. **Kořen řetězu se hýbe se stehnem (Sync Bone / QualiArts):** v řidiči natočit **kořenový kloub** předních
   (a slaběji bočních) řetězů o podíl **švihu** stehna (bez zkrutu – swing/twist rozklad, nebo damped-track na koleno),
   rozdělený na složku vpřed/vzad a do strany. Středový přední řetěz = průměr obou stehen. Mrtvá zóna při malém
   úhlu, plná váha až při dotyku (vzdálenost kloubu od kapsle stehna). Podíl a křivka do pravidel; výchozí bod podle
   Kawaii 0,3–0,5 a silněji u kořene než u lemu (NEOVĚŘENO pro nás). Jen směr „noha do sukně“ (filtr Positive).
3. **Projekce v pořadí CRYENGINE:** (a) nejdřív posunout **kořen/první kloub** ven z kapsle stehna *v pevné ose*
   (directed translation – dopředu/ven od osy stehna, ne nejkratší vektor, aby neskákal mezi stehnem a holení),
   (b) pak natočit kosti, (c) až poté omezení úhlu – a úhel nesmí vracet kloub do kapsle (kužel „má poslední slovo“).
4. **Kontrola na vrcholech, ne jen na kloubech:** kapsle kostí sukně o ~25 % delší než kost, poloměr potomka menší
   (CRYENGINE ~2 mm); test měřit i vzorkem vrcholů horního pásu proti kapsli stehna v klíčových snímcích chůze
   (prosvítá právě pás mezi pánví a kloubem 1).
5. **Kapsle nohou:** levé a pravé stehno se uprostřed **překrývají zhruba o polovinu** (středové řetězy neproklouznou),
   kapsle lehce dozadu; poloměry z modelu postavy do pravidel. Zvážit kapsle boků nad stehny (zvednutá sukně sjede zpět).
6. **Sed/klek:** ponechat současný cíl řidiče; alternativa s malou cenou = zapnout „přitažlivost k chodidlům“ jen
   během animací sedu/kleku (QualiArts). Zapečení simulace do kostí (Dem Bones / Blender bake) až když heuristika
   nestačí – je to další krok v Blenderu, ne za běhu.
7. **Tablet:** 8 × 3 = 24 kostí, 4 kapsle → 96 testů kost×kapsle za snímek na postavu, analyticky (bez fyzikálního
   serveru). Řídit jen postavy v blízkém LOD, vzdálené nechat čistě skinované. Výkon NEOVĚŘENO NA ZAŘÍZENÍ – změřit
   měřicí trasou. Godot 4.4 má i vestavěný `SpringBoneSimulator3D` s kapslemi (`SpringBoneCollisionCapsule3D`,
   volba *inside*), použitelný jen pro lehký dokmit dolních kostí po našem řidiči.
8. **Rozparek/klín** vpředu nebo po stranách kabátce (historicky doložitelné) snižuje požadavky na řidič – herní
   doklad nenalezen (NEOVĚŘENO); rozhodnout podle rešerše střihu.

Co zůstává otevřené: skutečné nastavení sukní v KCD2 (otevřít `.cdf` v KCD2 Modding Tools: typ připojení, počet řad,
proxy na stehnech, poloměry) – jediný zdroj, který by dal čísla „jak to dělá Warhorse“.
