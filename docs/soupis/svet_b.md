# Soupis cisel a pravidel - scripts/svet.gd radky 3600-7200 (cast B)

Sloupec "tabulka": 1 ZASAZENI, 2 POVRCHY, 3 TRIDY (vykreslovani), 4 MATERIALY. Souradnice x, z ve svete (m).

## Cesty

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3798-3799 | krok s0 + i*0.8 m; r = max(cesta_ok(w, s, +-1)) | polomer jizdniho pasu (hlina) z cesta_ok na obe strany, bod osy po 0.8 m | _ves_maska_ulice | 2 |
| svet.gd:4007-4013 | krok 2 m po pesine, mrizka 8 m; osa vlnena _pes_o * _brod_tlum | osy pesin pro odstup lesa | _nove_lesy | 1 |
| svet.gd:4054 | pesina 3.5 m od osy | stromy noveho lesa ne blize pesine | _nove_lesy | 1 |
| svet.gd:4143 | pes_d < 1.8 m -> nic | plast ne na pesine | _lesni_plast | 1 |
| svet.gd:4205-4208 | 45 % sance; _vln(i*0.09 + sd*3.1) < 0.1 -> nic; 1.8-5.0 m x pes_f od osy; posun +-1 m; pes_d < 1.5 m -> nic | kere v usecich podel pesiny (Misa 0.87 "pravidelne") | _kere_podel_pesin | 1 |
| svet.gd:4326-4327 | pes_d 0.7-1.8 m: jitrocel (byliny_1) 60 % / podbel (byliny_3) 40 % | bylina na kraji pesiny (seslapana hlina) | _byliny_rozsev | 1 |
| svet.gd:4447-4455 | start 0-5 m, krok 5-9 m; _les < 0.25 -> nic; tvrz abs(x+4)<60 a abs(z)<60 vynechana; 2.2-4.5 m x pes_f; pes_d < 2.0 -> nic | stromoradi podel pesin lesem (koruny nad pesinou) | _les_hustsi | 1 |
| svet.gd:4615-4619 | smoothstep(4, 14 m) | osa pesiny se u brodu nevlni (do 4 m rovna, od 14 m plne vlneni) | _brod_tlum | 1 |
| svet.gd:4810-4811 | chodnicky 0.5 m; PESINY index >= 12 | vyslapane chodnicky ke dverim (mimo vyluku u tvrze) | _pesiny_k_domum | 1 |
| svet.gd:4824 | body (hw+0.25, vstup), (hw+1.5, vstup+0.8), (hw+1.4, f+0.5), (hw+0.9, f+3.0) | chodnicek od vstupu k navsi pres mezeru v plotu | _pesiny_k_domum | 1 |
| svet.gd:4826 | body (-hw-0.25, dvur), (-hw-2.0, dvur-0.3), (-hw-4.0, dvur-1.2) | chodnicek od dvornich dveri do dvora | _pesiny_k_domum | 1 |
| svet.gd:4828 | (0, f+0.2), (0.3, f+2.6) + k_cili | chodnicek od dveri chyse k cili | _pesiny_k_domum | 1 |
| svet.gd:4834 | PES_SIRKA 0.45 | sirka chodnicku ke dverim (komentar 0.5 m) | _pesiny_k_domum | 1/2 |
| svet.gd:4845 | do 16 m od ulice | chodnicek se dotahne na ulici | _pesina_k_ulici | 1 |
| svet.gd:4853-4859 | cil = bod osy ulice o 2 zpet (k vjezdu); d < 1.5 m nic; mezibod min(0.4 d, 2.5 m) + 0.25 (cil-a); posledni bod 1 m pred osou | mirne zahnuty konec chodnicku na okraji ulice | _pesina_k_ulici | 1 |
| svet.gd:4878-4897 | Teren_cesta v oblasti + 20 m, mrizka 2 m, okoli +-4 bunky (8 m) | chyse ne u vozove cesty | _chyse_k_lomu | 1 |
| svet.gd:4955-4956 | placek: osa a + 3.5 ks .. b + 3.5 ks, PES_SIRKA 3.0 (pul sirky 3 m) | vyslapany placek pred vchody chysi | _chyse_k_lomu | 1/2 |
| svet.gd:4957-4958 | cesticka placek -> pesina k lomu, PES_SIRKA 0.45 | jedna cesticka na cestu k lomu | _chyse_k_lomu | 1/2 |
| svet.gd:5808-5814 | komentar: CryEngine/BeamNG reserse; Teren_cesta 8 vrcholu napric, 2 m podel = kolize a dalkova verze nad 85 m; nova sit 0.8 m podel, 0.12-0.3 m napric; dve koleje, travnaty hrbet, val, louze, rozbity okraj, pas pod teren | zamer cest = tvar, ne textura | stavba cest | 2/3 |
| svet.gd:5817 | mrizka 4 m | _cesty_mriz: vyhledani bodu osy cesty | stavba cest | 1 |
| svet.gd:5822-5823 | sin(x)*0.55 + sin(2.31x+1.7)*0.3 + sin(5.13x+0.4)*0.15 | pomaly sum (vlneni okraju, koleji, useku) | _vln | 2 |
| svet.gd:5826-5829 | opotrebeni o: x koleje, y hrbet, z bahno, w vymleti (0..1); koleje 5-15 cm mistami prerusene | profil cesty napric | cesta_profil | 2 |
| svet.gd:5835-5837 | g = 0.02 (trava zakladni); rozchod koleje roz = clamp(hw*0.42, 0.55, 0.78) + 0.05*sum | pulka rozchodu koleji od osy | cesta_profil | 2 |
| svet.gd:5839-5841 | hrboly 0.035 + 0.03*w (vymleti) x sum(0.61 s, 0.23 s); + 0.02 sin(1.7 s + 5.3 lat) | nerovny povrch hliny (hrboly 0.3-2 m) | cesta_profil | 2 |
| svet.gd:5843-5848 | koleje: profil smoothstep(0.08, 0.42 m) od stredu koleje; hloubka o.x*(0.04 + 0.03 bahno + 0.012 sum + 0.008 sum) (komentar 3-5 cm, mekky profil 0.8 m); vyhrnuty okraj +0.01 m v 0.3-0.7 m | koleje (Misa 0.83: melke, siroke, prerusovane) | cesta_profil | 2 |
| svet.gd:5851-5852 | hrbet mezi kolejemi: roz-0.34..roz-0.17; +0.015 m x koleje | travnaty hrbet vyssi | cesta_profil | 2 |
| svet.gd:5853-5869 | vymoly: bunky 5 m podel, sance h1 < vymoly*0.85; polomer 0.4-1.0 m; poloha napric +-0.65 hw; hloubka 0.05 + 0.07*h1/vymoly (komentar 5-12 cm); kaluz na dne (0.45-0.7 dl), x (0.55 + 0.45 bahno), jen h3 + bahno >= 0.3 | vymoly s kaluzemi (kazdy usek jiny) | cesta_profil | 2 |
| svet.gd:5873 | trava = smoothstep(ok - 0.35, ok + 0.05) | za okrajem sit nekresli (zem.gdshader discard), je videt teren | cesta_profil | 2 |
| svet.gd:5926-5929 | komentar: teren pod cestou 66 %, brehy u brodu 34 %; klouzavy prumer 16 m; sklon max 14 %; zarez/nasyp max 5 m; teren do 8 m za okraj | vyrovnany podelny profil cest | _cesty_profil | 1/2 |
| svet.gd:5930 | CESTA_SKLON = 0.14 | nejvetsi podelny sklon cesty | _cesty_profil | 1 |
| svet.gd:5946-5951 | +-10 bodu (x 0.8 m = 16 m) | klouzavy prumer vysky osy | _cesty_profil | 1 |
| svet.gd:5952 | g = CESTA_SKLON * 0.8 (na bod 0.8 m) | omezeni sklonu vpred i vzad | _cesty_profil | 1 |
| svet.gd:5963-5969 | kotva +-15 bodu (rozmazana ~12 m), (1 - smoothstep(0.2, 0.7, kv)); konce osy smoothstep(0, 12 m); dl clamp +-3.0 m (komentar 5 m) | zarez/nasyp; krizovatky a udusana mista (hostinec, brana, lom) zustavaji na terenu | _cesty_profil | 1 |
| svet.gd:6013-6015 | konec do 14 m od jine osy (komentar) -> prodlouzit do stredove cary + 1.5 m | napojeni koncu os | _cesty_napoj | 1 |
| svet.gd:6029 | pesina 6 m, cesta 30 m (lom - cesta od vsi) | dosah napojeni konce osy | _cesty_napoj | 1 |
| svet.gd:6037 | d > 0.4 m, smer dot < 0.3 | ne zpet podel vlastni osy | _cesty_napoj | 1 |
| svet.gd:6044,6069 | krok 0.8 m; prevzorkovani 1.0 | body prodlouzeni | _cesty_napoj | 1 |
| svet.gd:6075-6077 | koleje 0; vymoly smoothstep(0.15, 0.55, sum s*0.017); kamenitost smoothstep(0.2, 0.6, sum s*0.021) | useky podel cesty 20-90 m (kazdy jiny) | cesta_useky | 2 |
| svet.gd:6080-6082 | ok = hw*(1 + 0.16 sum(0.13 s) + 0.08 sum(0.55 s)) + 0.25 sum(1.9 s) | rozbity okraj hliny (jazyky hliny do travy) | cesta_ok | 1/2 |
| svet.gd:6085-6092 | komentar: teren + 2 cm, uvnitr +5 cm s hrboly, koleje do dna +2 cm; dl x (1 - smoothstep(ok + 1, ok + 12)) | vyska povrchu cesty na terenu | cesta_y | 1/2 |
| svet.gd:6097-6100 | vyklenuti zv = 1 - smoothstep(ok - 1.4, ok - 0.1); val smoothstep(ok - 0.6, ok - 0.1)*(1 - smoothstep(ok + 0.1, ok + 0.8)); 0.06 + dy + (disp - 0.5)*0.12, clamp -0.14..0.2; val +0.05 m | profil cesty nad terenem (vyklenuti, relief, val odhrnute hliny) | cesta_d | 2 |
| svet.gd:6173-6180 | typ osy: ulice_vsi (o.ves), pesina (o.pesina), vozova | pasmo podle typu cesty | typ_osy, pasmo_cesty | 1 |
| svet.gd:6193-6203 | strom -> kmen_m; ker, balvan -> ker_od_m; vysoka_bylina -> trsy_od_m; bylina 0 | odstup od kraje hliny podle pasma osy | odstup_cesty | 1 |
| svet.gd:6215-6244 | mrizka 4 m (bunka obsahuje useky do 16 m); s = s0 + (i + t)*0.8 | nejblizsi osa cesty (lat, hw, y, s, opotrebeni, dl, index) | cesta_lat | 1 |
| svet.gd:6261-6264 | komentar: provoz hlavni 1, druha 0.7, ves 0.6, odbocky 0.3 (bez kolej); krizovatky do sire + 3 m; bahno sklon < 2 st. do 15 m od vody; vymleti nad 8 st. | mapa opotrebeni z provozu | _cesty_opotrebeni | 2 |
| svet.gd:6265 | CESTA_UDUSANO [x, z, r]: (0, 24) r 22 brana tvrze; (-71, 881) r 26 hostinec; (150, 938) r 30 lom; (461, 779) r 14 (krcma/ves) | udusana mista bez kolej, sirsi, teren se nemeni | _cesty_opotrebeni | 1/2 |
| svet.gd:6268-6276 | sire z Blenderu kraj.py: hlavni 3.4 m, ves 2.8, stavby 2.2 / 1.7; median hw > 2.05 -> provoz 1.0, > 1.65 -> 0.7, jinak 0.3; pesina 0.3; ves 0.6 | provoz osy podle sire | _cesty_opotrebeni | 2 |
| svet.gd:6304 | krizovatka: 1 - smoothstep(w + 1, w + 6 m) od jine osy | miera krizovatky | _cesty_opotrebeni | 1/2 |
| svet.gd:6307 | udusano: 1 - smoothstep(0.6 r, r) | miera udusaneho mista | _cesty_opotrebeni | 1/2 |
| svet.gd:6308-6310 | sklon z +-3 bodu (min 0.5 m) | podelny sklon v bode | _cesty_opotrebeni | 2 |
| svet.gd:6318-6320 | preruseni smoothstep(0, 0.35, sum(s*0.013) + 0.25 sum(s*0.051)); koleje jen pri provozu > 0.35 | koleje asi na 40 % delky v usecich 30-80 m | _cesty_opotrebeni | 2 |
| svet.gd:6321 | hrbet clamp(1.15 - provoz, 0, 1) | travnaty hrbet tim vic, cim min provozu | _cesty_opotrebeni | 2 |
| svet.gd:6328-6330 | zatacka: uhel na +-4 body (6.4 m), smoothstep(0.12, 0.45 rad) | zatacky sirsi (vozy zkracuji) | _cesty_opotrebeni | 1 |
| svet.gd:6334 | w x (1 + 0.35 kriz + 0.25 zat + 0.9 udus) | rozjete sirsi krizovatky, zatacky, udusana mista | _cesty_opotrebeni | 1 |
| svet.gd:6351-6359 | barva vrcholu g: stred 0.078 (+-0.02), bok 0.298 (+-0.03), vnejsi 0.8 (+-0.05) | rozpoznani sloupcu pasu Teren_cesta z Blenderu | _cesty_tvar | 2 |
| svet.gd:6375-6379 | par stredu do 1.3 m, rozdil vysky < 0.3 m | dvojice stredovych vrcholu = bod osy | _cesty_tvar | 1 |
| svet.gd:6403-6404 | hw = clamp(bok_vzd / 0.45 * 0.75, 1.4, 3.0); bez boku do 5 m -> 3.0 | pulsirka cesty z pasu (KCD2 fotky: hlavni cesta 4-6 m) | _cesty_tvar | 1 |
| svet.gd:6405-6453 | useky bez stredniho sloupce (vrcholy 0.8 0.3 0.3 0.8, napr. (-13,500)-(-32,639) k hostinci, dira 140 m); par boku 1-9 m, smer > 0.95; bez duplikatu v mrizce 2 m | doplneni bodu osy | _cesty_tvar | 1 |
| svet.gd:6475-6533 | sousede do 2.9 m, smer dot >= 0.6; skok az 27 m (dot > 0.5) v ridkem useku (radky po 25 m); odebrani do 0.7 m; cara min 4 body | retezeni bodu do os | _cesty_tvar | 1 |
| svet.gd:6534-6542 | osy po 0.8 m (_osa_prevzorkuj, vyhlazeni 1.0) | prevzorkovani os | _cesty_tvar | 1 |
| svet.gd:6568,6574 | osa vsi = teren + 0.02 m | vyska osy ulice | _cesty_tvar | 1/2 |
| svet.gd:6581 | PESINY 6 -> hw 1.8 (cesta do lomu), PESINY 4 -> hw 2.2 (od padaciho mostu) | pesiny povysene na vozove cesty, Catmull-Rom po 2 m | _cesty_tvar | 1 |
| svet.gd:6586 | (0, 28.5), (0.3, 38), (1, 52), (2, 72) | cesta od konce pevneho mostu pres prikop k hlavni ceste (z 67) | _cesty_tvar | 1 |
| svet.gd:6611-6618 | konec do 8 m od zacatku jine osy -> spojit; preskocit body do 6 m | spojeni v jednu osu (dve site pres sebe z-fightovaly) | _cesty_tvar | 1/3 |
| svet.gd:6631-6656 | PESINY >= 12: hw 0.75 m (PES_SIRKA >= 1 = pul sirky placku), krok 1 m, provoz 0.3 (pesina) | cesticky k domum a chysim stejnym modelem jako cesty | _cesty_tvar | 1/2 |
| svet.gd:6664 | s0 += delka + 50 m | rozestup souradnice s mezi osami (sum se neopakuje) | _cesty_tvar | 2 |
| svet.gd:6666-6667 | +-16 m kolem useku, mrizka 4 m | _cesty_mriz: prechod zarezu 12 m za okraj | _cesty_tvar | 1 |
| svet.gd:6681-6688 | usek 12 bodu (~10 m), krok 2 | nejprudsi usek cesty (jen vypis, Misa 0.84) | _cesty_tvar | 1 |
| svet.gd:6705-6736 | krok 0.8 m; 3x klouzavy prumer 5 bodu (poloha, vyska, sirka); k = kolej | prevzorkovani a vyhlazeni osy (komentar: k = 0 u sirky < 1.35 - v kodu se nepouziva) | _osa_prevzorkuj | 1 |
| svet.gd:7064-7065 | kusy po 48 m (komentar), v kodu 60 bodu x 0.8 = 48 m; do 85 m | kusy site cest (orezani pohledem) | _cesty_site_stavba | 3 |
| svet.gd:7083-7106 | radky po 0.4 m; napric do e = 1.3 hw + 0.45 m; krok 0.12 m (do 1.25 m), 0.2 m (do hw + 0.3), 0.35 m dal | hustota site cesty (koleje, valy, kaminky jsou geometrie) | _cesty_site_stavba | 2/3 |
| svet.gd:7098-7111 | konce: pon = 0.45 x (1 - smoothstep(0, 5 m)); y - 0.3 pon | konce cesty zapustit (ne hrana ve vzduchu, pod napojenou cestou) | _cesty_site_stavba | 1 |

## Teren

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3627,3634 | trava_kraj 2 m (k), vyska cm v int16 | mrizka vysky krajiny, deleni /100 = metry | _vyska | 2 |
| svet.gd:3636-3643 | trava_ves pred trava_kraj; okraj 1 bunka | ves ma jemnejsi teren (Teren_ves), na okraji mrizky vsi (<1 nebo >n-2) se bere krajina | _vyska | 2 |
| svet.gd:3656 | 0.0 | vyska mimo obe mrizky | _vyska | 2 |
| svet.gd:3660 | r = 2.0 m (5 bodu kriz) | nejnizsi teren v okoli; mrizka 2 m mine teren na srazu o 1-3 m -> kmen zapustit | _vyska_min | 1 |
| svet.gd:4054 | sklon_bunky > 0.9 -> nic | les ne na strmem svahu | _nove_lesy | 1 |
| svet.gd:4143 | sklon_bunky > 0.9 | plast ne na strmem | _lesni_plast | 1 |
| svet.gd:4330-4331 | sklon_bunky 0.35-1.0, 50 % | divizna (byliny_0) na strani | _byliny_rozsev | 1 |
| svet.gd:4898-4905 | 6 vzorku (stred, +-2.5 diag., (0, 4.5)); svah = max - min vysky | rovinatost pudorysu chyse | _chyse_k_lomu | 1 |
| svet.gd:5107 | zmena > 0.005 m | prah posunu vrcholu terenu rybnika | _ryb_pod_domy | 2 |
| svet.gd:5168 | +-16 m od stredu domu | dosah upravy terenu domem | dum_teren | 1/2 |
| svet.gd:5175-5181 | chyse: dosah 6.5 m, y0 + t_pas, smoothstep(0, 6.5) | teren pod chysi dosypany a siroky prechod do okoli (hruba sit ~5 m) | dum_teren | 1/2 |
| svet.gd:5182-5188 | uvnitr: y0 - 0.15; komora Rychty y0 - 0.85 (z < -4, z > b + 1, abs(x) < 2.9) | teren pod podlahou domu; zahloubena komora rychty (1 m od zdi) | dum_teren | 1/2 |
| svet.gd:5189-5194 | u zdi do 1.8 m: clamp(y, y0 + t_pas (vych. -0.2), y0 - 0.02), smoothstep(0.4, 1.8) | teren u zdi 0.2 m pod podlahou (podezdivka videt 0.5 m), jen dolu | dum_teren | 1/2 |
| svet.gd:5587-5590 | 12 vzorku: x -hw/0/hw, z b/0/f/ft | body pudorysu chyse | _chyse_na_sit | 1 |
| svet.gd:5595 | vynechane Teren_obzor, Teren_cesta_kamen*, *_sukne | site terenu, ze kterych se bere vyska | _chyse_na_sit | 2 |
| svet.gd:5982-6008 | posun mrizky _vyska o dl x (1 - smoothstep(hw + 1, hw + 12 m, lat)); bunky _cesty_mriz 4 m | mrizka vysek (stromy, kere, stavby) podle vyrovnane cesty | _cesty_vys_mrizka | 1/2 |
| svet.gd:6317 | vymleti smoothstep(0.12, 0.2) sklonu | vymleti ve svahu (rygoly) | _cesty_opotrebeni | 2 |
| svet.gd:6739-6772 | site Teren* krome Teren_cesta*, Teren_obzor, *_sukne; trojuhelniky v bunkach _cesty_mriz; mrizka 2 m | trojuhelniky terenu u cest (vyska pro cesta_y) | _cesty_teren | 2 |
| svet.gd:6776-6779 | vyska = puvodni teren + o.dl + cesta_d; CUSTOM0/1 pro zem.gdshader | cesta = teren (pravidla povrchu A); kolize a louka na tomtez povrchu | _cesty_do_terenu | 2/3 |
| svet.gd:6780 | CESTA_KROK = 1.0 m (0.7 = 687 k troj. navic, 1.0 ~ polovina) | deleni trojuhelniku terenu u cest | _cesta_povrch | 2/3 |
| svet.gd:6945-6949 | deli se trojuhelnik do ok + 0.8 m + polomer trojuhelniku | pas terenu u cesty k rozdeleni | _cesta_povrch | 2 |
| svet.gd:6953 | n = clamp(ceil(median delky hrany / CESTA_KROK), 1, 12) | pocet deleni trojuhelniku | _cesta_povrch | 2/3 |
| svet.gd:6929,6969 | klic polohy 1 cm | sdileni vrcholu (bez trhlin) | _cesta_povrch | 2 |

## Ves/budovy

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3780-3806 | m < 60 = bez travy; zapis 20 | maska trava_ves: bunky v jizdnim pasu ulice vsi -> bez travy | _ves_maska_ulice | 2 |
| svet.gd:3784 | VES_OBLOUK | maska podle ulice jen pri novem oblouku vsi | _ves_maska_ulice | 1 |
| svet.gd:3812-3828 | m < 60 vc. sousedu +-1 bunka | bod je na ceste/navsi/dvore vsi (i kousek pres okraj) | ves_cesta | 1 |
| svet.gd:3831-3843 | vyjimka stromy (_strom_tvar) a skala_ | z cest a dvoru vsi pryc kere, kameny, kmeny, byliny; stromy zustavaji | _ves_cesty_volne | 1 |
| svet.gd:4141 | tvrz: abs(x+4) < 80 a abs(z) < 75; ves: kruh (470, 830) r 140 m | plast ne u tvrze a ve vsi | _lesni_plast | 1 |
| svet.gd:4521-4539 | shluk vrcholu bunka 0.5 m; slouceni do 0.35 m | stredy hlavek zeli z Blenderu (mista pro modely zeli/salatu) | _zeli_stredy | 1 |
| svet.gd:4636-4646 | Brana, Sin; materialy sukno_cervene*, bila*; max 120 vrcholu | cizi stit skryt (pruhledny material skryty_stit); palac ma cervene sukno na zdech (velke plochy zustavaji) | _erb_tvrze | 4 |
| svet.gd:4657-4660 | yaw 0 / +-PI/2 / PI podle tenke osy AABB a strany; y = spodek AABB - 0.04 | stit_havran na miste stareho stitu, licem ven od stredu tvrze | _erb_tvrze | 1 |
| svet.gd:4661-4676 | mosazna makovice BranaDrevo 1.32 m nad vrcholem strechy; apex = top - 1.37 | vrchol veze nad branou pro prapor | _erb_tvrze | 1 |
| svet.gd:4677-4690 | korouhvicka fort.py 0.55 x 0.36 m 0.85 m nad vrcholem; vyrez apex+0.8..+1.26, x -0.02..+0.62, abs(z) < 0.15 | zelezna korouhvicka pryc (material zelezo*) | _erb_tvrze | 1 |
| svet.gd:4699 | apex.y - 0.15; yaw -atan2(0.6, 0.8) | poloha a natoceni praporu korouhev_havran (po vetru) | _erb_tvrze | 1 |
| svet.gd:4708 | VES_DOMY (env TVRZ_BEZ_DOMU vypne) | nove domy vsi misto chalup 1-7 | _domy_ramce aj. | 1 |
| svet.gd:4709 | VES_DOMY_GLB = res://modely/ves/domy.glb | model domu vsi | _domy_ramce, _chyse_k_lomu | 3 |
| svet.gd:4711-4719 | VES_STARE: [k, x, z, yaw, L, W, model] | usedlosti: 1 (484.24, 798.14) yaw 2.2753 L11.26 W5.68 Dum2; 2 (505.59, 816.28) 2.2753 11.08x6.37 Dum1; 3 (525.66, 833.34) 2.2753 11.92x5.65 Dum2; 4 (419.39, 830.95) -0.8663 11.41x6.17 Dum1; 5 (441.20, 849.49) -0.8663 13.00x7.00 Rychta; 6 (461.50, 866.74) -0.8663 10.66x6.08 Dum2; 7 (483.64, 885.56) -0.8663 11.33x5.74 Dum1 | _domy_ramce | 1 |
| svet.gd:4722-4724 | DUM_MER Dum1: vstup -0.5, dvur 0.45, f 5.17, b -5.17, hw 3.67, rx 4.42, rz +-5.95, pod 0.305, ix 3.4; jizba 0.81..4.9, sin -1.69..0.59, komora -4.9..-1.91; "Selsky dum", "Komora" | mistni rozmery modelu (podezdivka, strecha, podlaha, mistnosti) | _domy_ramce, _pesiny_k_domum a dalsi | 1 |
| svet.gd:4725-4726 | DUM_MER Dum2: vstup -0.2, dvur 0.2, f 4.67, b -4.67, hw 3.17, rx 3.8, rz +-5.14, pod 0.255, ix 2.9; jizba 1.0..4.4, sin -1.2..0.8, komora -4.4..-1.4; "Chalupa", "Chlev" | rozmery Dum2 | dtto | 1 |
| svet.gd:4727-4728 | DUM_MER Rychta: vstup -2.25, dvur 2.2, f 4.07, b -8.88, hw 3.97, rx 4.72, rz0 -9.39, rz1 4.86, pod 0.305, ix 3.7; jizba -0.45..3.8, sin -3.8..-0.66, komora -8.23..-4.64; "Kamenna komora" | rozmery Rychty | dtto | 1 |
| svet.gd:4729-4731 | ChyseKura: f +-2.85, hw 1.9, rx 2.25, rz -3.12..2.94, pod 0.0, ft 4.8, t_in -0.03, t_pas -0.03; ChysePrkna: f +-2.41, hw 2.22, rx 2.25, rz +-2.9, pod 0.5, ft 4.8, t_in 0.05, t_pas -0.02 | chyse bez podezdivky: teren pod chysi a pred ni (ft 4.8 m) na urovni podlahy | uprava terenu u chysi | 1/2 |
| svet.gd:4736-4740 | VES_CHYSE: (642, 818) yaw PI/4 ChyseKura paseka 12 m cil (640, 825); (651, 821) yaw PI-0.2 ChyseKura paseka 12 m cil (640, 825) | uhlirske chyse v lese nad vsi; mista podle svahu (svah pod pudorysem < zidka 0.5 m / kuly 0.29 m, rovinky 0.2-0.3 m) | _domy_ramce | 1 |
| svet.gd:4743-4757 | DUM_VYB: [id, x, z, yaw, vyska]; stul_selsky, lavice_selska, miska/hrnec/lzice na stole 0.776 m, ovci_kuze, truhla, vedro, spalek, metla, pytle, sud, kosik, bedna; Rychta korbel, vino_dzban, svicen, kolebka, komora -0.75 m | vybaveni domu (jizba u lavice ve svatem koute, pec -x u sine, sin volne dvere, komora zasoby) | vybaveni domu | 1 |
| svet.gd:4760-4768 | DUM_DREVO: dum 1 drevo_hromada + spalek_stipani; 2 drevo_vysoka_1; 3 drevo_mala; 4 drevo_dlouha_1; 5 drevo_kulatina + drevo_vysoka_2; 6 drevo_dlouha_2; 7 drevo_hromada + drevo_mala (strana, odsazeni, posun, yaw) | drevo u domu | rozmisteni dreva u domu | 1 |
| svet.gd:4771-4775 | DUM_ZEBRIK pata/vrchol/nastup/sestup: Dum1 (1.72,0.30,0.27)/(0.62,2.84,0.27)/(2.35,0.30,0.27)/(-1.0,2.64,0.25); Dum2 o 0.05 niz, z 0.47/0.35; Rychta (2.24,0.30,-0.98)/(0.95,2.84,-0.98)/(2.8,0.30,-0.98)/(-0.8,2.64,-1.03) | zebrik na pudu v sini | zebrik_use | 1 |
| svet.gd:4780-4783 | dosah r 2.2 m; +1.0 m dole, +0.6 m nahore; mezi nastup/pata 0.5, sestup/vrchol 0.4 | body pouziti zebriku | zebrik_use | 1 |
| svet.gd:4795-4796 | o = stred + osa * (L/2 - f); Basis PI/2 - yaw | predni podezdivka v linii stitu stare chalupy | _domy_ramce | 1 |
| svet.gd:4804 | k = 20 + i | cislovani chysi | _domy_ramce | 1 |
| svet.gd:4865-4867 | komentar: mimo lom > 6 m, od pesin a vozove cesty > 7 m, nejrovnejsi; druha chyse 8-11 m od prvni | pravidla umisteni chysi u lomu | _chyse_k_lomu | 1 |
| svet.gd:4868 | LOM_CHYSE_OBLAST = Rect2(150, 885, 60, 85) | oblast hledani chysi u lomu | _chyse_k_lomu | 1 |
| svet.gd:4907-4915 | krok 1.5 m; v_lomu > 6 m; vzd. od pesin > 7 m | kandidatni mista chysi | _chyse_k_lomu | 1 |
| svet.gd:4924 | 8-11 m | druha chyse od prvni | _chyse_k_lomu | 1 |
| svet.gd:4936-4937 | placek 4 m od stredu smerem k LOM_VCHOD; PESINY[6] = pesina k lomu | spolecny vyslapany placek, jedna cesticka na pesinu k lomu | _chyse_k_lomu | 1 |
| svet.gd:4950 | paseka 6.0 m (chyse u lomu, typ ChysePrkna, k od 20) | okruh bez stromu kolem chyse u lomu | _chyse_k_lomu, _na_pasece | 1 |
| svet.gd:4978 | okraj_novy 0.2 m (vychozi), stara = true | bod zabrany domem | _dum_zabira | 1 |
| svet.gd:4981-4985 | stara chalupa: vpredu L/2 + 3.0 m (podsin 1.9 + presah stitu), vzadu L/2 + 1.6 m (drevo), do boku W/2 + 1.35 m | pudorys stare chalupy k odstraneni | _dum_zabira | 1 |
| svet.gd:4988 | abs(x) < hw + okraj, b - okraj < z < f + okraj | pudorys noveho domu | _dum_zabira | 1 |
| svet.gd:5003-5042 | kolize, mistnosti ves_k, vybaveni, ohne pryc v pudorysu; pohyb Pohyb_ves_* s okrajem 0.6 m (stara jen dvere) | data starych chalup pryc | _ves_stare_pryc | 1/3 |
| svet.gd:5059-5069 | stara zahradka (vesnice.py: u -L/2+0.8..L/2-0.6, v -W/2-5.8..-W/2-1); test abs(u) < L/2 + 1.5, -(W/2 + 7.0) < v < 0.5 | stara zahradka usedlosti (nahrazena zahony) | _v_stare_zahrade | 1 |
| svet.gd:5073-5077 | vzdalenost < paseka (12 m uhlirske, 6 m u lomu) | bod na pasece kolem chyse | _na_pasece | 1 |
| svet.gd:5080-5081 | komentar: podezdivka 0.45 m pod podlahou + 0.3; srovnani v pasu 1.5 m | vyska domu z terenu | _domy_vysky | 1/2 |
| svet.gd:5138-5141 | 9 vzorku: x -hw/0/+hw, z b/0/ft (nebo f) | vyska terenu pod pudorysem domu | _domy_vysky_hlavni | 1 |
| svet.gd:5142-5145 | podlaha = max vyska + 0.1 m; y0 = podlaha - pod | place_building: budova svisle, jen yaw, podlaha 0.1 m nad nejvyssim bodem | _domy_vysky_hlavni | 1 |
| svet.gd:5146-5151 | chyse (bez ix): y0 = prumer 9 vzorku | chyse primo na zemi, teren srovnan na prumer | _domy_vysky_hlavni | 1 |
| svet.gd:5152-5153 | svah > pod + 0.45 m -> varovani | svah vetsi nez podezdivka, teren se srovna | _domy_vysky_hlavni | 1 |
| svet.gd:5198-5200 | blender barn: 2 kridla 1.3 m, panty +-1.42 m, prave pootevrene 72 st. | zamer vrat stodol | _stodoly_vrata | 1 |
| svet.gd:5211-5216 | materialy "dvere", "deska_stodola" | kridla a prkna steny stodoly v siti Vesnice | _stodoly_vrata | 4 |
| svet.gd:5257-5258 | dotyk obalek + 0.03 m, mrizka 2 m | spojeni dilu do kridla | _stodoly_vrata | 1 |
| svet.gd:5307-5310 | kridlo: delka 1.15-1.5 m, vyska 2.1-2.6 m (komentar 1.2-1.45 x 2.2-2.5) | rozpoznani kridla stodoly | _stodoly_vrata | 1 |
| svet.gd:5316 | prkna steny do +-1.5 m vysky | pant = konec blize prknum steny | _stodoly_vrata | 1 |
| svet.gd:5337 | panty 2.6-3.1 m od sebe | dvojice kridel jedne stodoly | _stodoly_vrata | 1 |
| svet.gd:5348 | abs(smer . normala) > 0.3 | strana otevirani ven podle pootevreneho kridla | _stodoly_vrata | 1 |
| svet.gd:5386-5391 | otevreni +-90 st., dur 1.6 s; pouziti v dl/2, 1.1 m; kolize kridla [dl/2, 1.2, 0, dl, 2.35, 0.08] | vrata stodol Pohyb_stodola_* oteviraji se ven | _stodoly_vrata | 1/3 |
| svet.gd:5418-5440 | M_RoubeniVnitrni; abs(x) < 2.5, y 1.68..1.97, -z 4.85..5.12 (Blender y 4.90-5.07, z 1.73-1.92) | tram nad schody do komory rychty pryc (strop nese zed od y 5.55) | _rychta_tram_pryc | 1 |
| svet.gd:5520-5531 | dvere otevreni +-100 st. (k sini / do chleva), init = otev u Vstup, dur 1.0 s; pouziti ve vysce 0.95 m; kolize tl. min 0.06 m | dvere domu Pohyb_dum_* | _ves_domy | 1/3 |
| svet.gd:5534-5541 | jizba ambient 0.2, sin 0.16, komora 0.14 (x0.92, x0.8); vyska mistnosti 2.3 m; komora Rychty ix 2.2, podlaha -0.75 m | mistnosti domu (svetlo uvnitr) | _ves_domy | 3 |
| svet.gd:5546-5547 | ohen hearth size 0.4; zapaleny u lichych k a v Rychte; svetlo +0.5 m | ohen v peci (M_Zhar) | _ves_domy | 1 |
| svet.gd:5555 | vyska = pod + v[4] | vybaveni domu nad podlahou | _ves_domy | 1 |
| svet.gd:5563-5574 | rozmer predmetu vychozi [1.5, 0.8, 0.5]; odstup hl = hloubka/2 + odstup; podel steny b+0.8..f-0.8; y = _vyska_min(r 0.8) - 0.03 | drevo u domu (KCD1, kazdy dum jinak) | _ves_domy | 1 |
| svet.gd:5579-5580 | prkenna: zidka na nejnizsim bode; kurova: kuly 0.29 m v zemi | chyse na skutecnou sit terenu (ne mrizka 2 m) | _chyse_na_sit | 1 |
| svet.gd:5642-5648 | hloubka = pod (prkna 0.5) nebo 0.29 (kuly); y0 = min - 0.01 (prkna) / max + 0.03 (kura); svah > hloubka -> varovani | vyska chyse na siti (komentar: podlaha +0.05) | _chyse_na_sit | 1 |
| svet.gd:5657-5659 | komentar: vyvysene zahony s proutenym lemem, plutek s mezerou, zahony na 4 body, plutek svisle | zamer zahradky u domu | _zahrada | 1 |
| svet.gd:5660 | PLODINY: zahon_zeli (2x), zahon_cibule (2x), zahon_salat, zahon_mrkev, zahon_prazdny | druhy zahonu (vaha podle opakovani) | _zahrada | 1 |
| svet.gd:5669-5672 | x0 = hw + 2.0 (za chodnickem hw + 1.4); x1 = W/2 + 5.8 (plot W/2 + 6.2); z0 = max(b, f - L + 0.8) + 0.2; z1 = f - 0.6 | obdelnik zahradky v ramci domu | _zahrada | 1 |
| svet.gd:5674 | seed k * 131 | nahodnost zahradky | _zahrada | 1 |
| svet.gd:5677-5690 | zahon 3.07 x 1.17 m; mezery 0.45-0.6 m (podel) / 0.42-0.55 m (napric); natoceni +-0.03 rad, 50 % otoceny o PI; hlina 0.03 m v zemi | rozmisteni zahonu (polozit_na_body, opory) | _zahrada | 1 |
| svet.gd:5694 | okraje x0-0.4, x1+0.3, z0-0.2, z1+0.4 | obdelnik nove zahrady (_nove_zahrady) | _zahrada | 1 |
| svet.gd:5696-5703 | plutek 2.07 m, krok 2.1 m, x0 - 0.3; mezera +-1.2 m uprostred; pata_lom(.., 2.07, 0.07) - 0.02 | prouteny plutek mezi chodnickem a zahony | _zahrada | 1 |
| svet.gd:5742 | material M_Zhar* (Interier/Drobne) | misto ohne v peci | _dum_zhar | 1 |
| svet.gd:5753-5754 | VECHET_A (459.47, 775.90), VECHET_B (458.55, 775.12) | znameni krcmy (tyc vechtu) k odstraneni | _vechet | 1 |
| svet.gd:5759-5764 | do 2.2 m od B; chvoji*, provaz*; dub_ven do 0.12 m od tyce a nad terenem + 1.8 m | trojuhelniky vechtu pryc ("hnusna kvetina nad vchodem") | _vechet | 1 |
| svet.gd:5771-5787 | Vesnice, Vesnice_ploty, Vesnice_zahrady; okraj 0.15 m; stare chalupy jen v Vesnice; stare zahrady jen v Vesnice_zahrady | vyrez starych chalup ze siti vsi | _ves_site_vyrez | 1 |
| svet.gd:5971-5975 | ulice vsi dl clamp +-0.25 m | ulice vsi kopiruje teren (nasyp az 3 m byl spatne) | _cesty_profil | 1 |
| svet.gd:6546-6569 | VES_OBLOUK: stare osy uvnitr stare navsi (_vo_stara_naves) pryc; ulice pulsirka 1.3-1.6 m, u vjezdu 1.9 (vo.pulsirka, lokace_ves.json ulice.pulsirka); y = teren + 0.02 | ulice vsi v oblouku (ne dalnice, nema bricho) | _cesty_tvar | 1 |
| svet.gd:6570-6575 | stara naves (bez VES_OBLOUK): u -95..38, stred (470, 830), smer (0.76193, 0.64764), v = 2.5 sin(u/23) + 1.2 sin(u/9 + 1); hw clamp(2 + 3 exp(-((u+6)/30)^2) + 0.5 sin(u/7), 3.2, 4.6) | hlavni cesta navsi dle vesnice.py | _cesty_tvar | 1 |

## Voda

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:4057 | voda_y (vychozi -2.75) + 0.5 m | strom ne niz nez 0.5 m nad hladinou | _nove_lesy | 1 |
| svet.gd:4059 | koryto.strop < hy + 1.5 m | ne v zarezu potoka | _nove_lesy | 1 |
| svet.gd:4146 | voda_y + 0.4 m | plast ne niz nez 0.4 m nad hladinou | _lesni_plast | 1 |
| svet.gd:4464-4494 | najezdy NAJEZD_DELKA (14 m); sirka mostu + 7 m strom / + 4 m ker | most a najezdy bez stromu a keru (vc. _daleko) | _most_bez_stromu | 1 |
| svet.gd:4480-4483 | strom: _strom_tvar, vrba, olse, borovice, briza, dead_tree; ker: shrub, bez_, sipek, liska, ker | co se u mostu odstrani | _most_bez_stromu | 1 |
| svet.gd:4498-4504 | AABB site Most_potok + 5 m (grow 5.0) | pudorys mostu + 5 m (bez vody) | _u_mostu_jen | 1 |
| svet.gd:4507-4515 | AABB Most_potok + 5 m NEBO v korytu (vyska < hladina + 0.5 m) | zakazana zona pro rozsev "u mostu" vcetne celeho koryta | _u_mostu | 1 |
| svet.gd:4566-4568 | komentar: melcina 0.28 m pod hladinou, brehy 1:4 v pasu 5 m, dno a najezdy kameny a sterk | zamer brodu (provadi uprava_y, _brody) | _najdi_brody | 1/2 |
| svet.gd:4579 | vzorkovani pesiny po 0.5 m | hledani prechodu pesiny pres vodu | _najdi_brody | 1 |
| svet.gd:4585 | vyska < hladina koryta | bod pesiny je ve vode | _najdi_brody | 1 |
| svet.gd:4591-4596 | mimo _u_mostu_jen; duplicita do 10 m | brod = prechod pesiny pres potok mimo most | _najdi_brody | 1 |
| svet.gd:4598-4611 | hladina koryta -9.2 vs viditelna voda reka.res -8.3 (~1 m rozdil); median vrcholu do 6 m; min 5 vrcholu | hladina brodu podle viditelne vody (jinak suchy pas napric, hloubka > 1.5) | _najdi_brody | 1/2 |
| svet.gd:5088-5089 | dil rybnika ctverec 60 m (rohem pod dum 7) | teren dilu rybnika srovnan pod domy stejne jako dum_teren | _ryb_pod_domy | 2 |
| svet.gd:5121-5130 | mrizka 2 m | trojuhelniky terenu rybnika pro vysky trav (_ryb_tri) | _ryb_pod_domy | 2 |
| svet.gd:5849-5850 | louze v kolejich: smoothstep(0.66, 0.88) pomaleho sumu (s*0.09), x (0.4 + 0.6 bahno); propad 0.03 m x mok | kaluze v kolejich | cesta_profil | 2 |
| svet.gd:5871 | bahno o.z * 0.5 do hw - 0.3..hw + 0.2 | bahnite useky u vody | cesta_profil | 2 |
| svet.gd:6316 | bahno: (1 - smoothstep(10, 15 m od vody)) x (1 - smoothstep(0.03, 0.06 sklon)) | bahno na rovine u vody | _cesty_opotrebeni | 2 |
| svet.gd:6324-6326 | brod: 1 - smoothstep(3, 9 m od vody); bahno = brod; koleje brod * 1.5 * max(provoz, 0.5) | brod a breh: bahno a hlubsi koleje vzdy | _cesty_opotrebeni | 2 |
| svet.gd:6332 | kotva = max(kriz, 0.5 udus, smoothstep(0, 0.6, 1 - smoothstep(6, 20 m od vody))) | brod: profil cesty se nemeni (tvaruje _brody) | _cesty_opotrebeni | 1 |

## Vegetace a rozsev

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3603 | seed 1393 | nahodnost nahrady smrku v udoli | _smrky_udoli (fce pred 3600) | 1 |
| svet.gd:3610 | y < 25.0 m, 85 % (randf > 0.15) | smrk pod 25 m n. m. (udoli) nahrazen listnacem (pravidlo 1393: jehlicnany jen nad 25 m) | nahrada smrku listnaci | 1 |
| svet.gd:3612 | 0.8-1.15 | meritko listnace nahrazujiciho smrk (normalizovane na 1) | nahrada smrku listnaci | 1 |
| svet.gd:3606 | "smrk_", "_daleko" | druhy, na ktere se nahrada vztahuje (jen blizke verze) | nahrada smrku listnaci | 1 |
| svet.gd:3689 | kura_y + 0.4 m | trojuhelniky listi brizy pod touto vyskou = spodek kmene (oddeli se do kury) | _briza_kmen | 4 |
| svet.gd:3716 | kura_y + 1.2 m | dolni metr kmene pro proklad UV v (v = ka*y + kb) | _briza_kmen | 4 |
| svet.gd:3746-3747 | rad > 0.02 m, radial > 0.45 | jen plochy hledici od osy kmene = kura; ploche karty u paty (sede desky) pryc | _briza_kmen | 4 |
| svet.gd:3857 | shrub_02_0, shrub_02_1, ker_husty_0 -> ker_kulaty_0..2 | fotoskeny keru nahrazeny kulatym kerem z karet | _kere_kulate | 3 |
| svet.gd:3864 | 50 % / 25 % / 25 % | podil velikosti ker_kulaty_0/1/2 (hash polohy) | _kere_kulate | 1 |
| svet.gd:3865 | y - 0.05 m; meritko 0.7-1.3 | zapusteni a velikost kulateho kere | _kere_kulate | 1 |
| svet.gd:3939-3940 | tree_stump_01/02, dry_branches_medium_01_0-2; shrub_02_0, sipek_0 | druhy lesniho patra (drevo, kere) | _lesni_patro | 1 |
| svet.gd:3949 | seed 404 | nahodnost lesniho patra | _lesni_patro | 1 |
| svet.gd:3953 | dub_, buk_, lipa_, smrk_, borovice_, olse_, briza_ | lesni stromy, kolem nichz lesni patro | _lesni_patro | 1 |
| svet.gd:3961-3965 | kazdy 5. strom; 2-6 m; meritko 0.8-1.3 x ref; y-0.05 | parez nebo spadle vetve u stromu | _lesni_patro | 1 |
| svet.gd:3967-3971 | kazdy 2. strom (komentar: 3.); 3-7 m; meritko 0.7-1.3; y-0.05 | kerik (sipek, shrub_02) v okoli stromu | _lesni_patro | 1 |
| svet.gd:3976-3980 | komentar: divokost > 0.55, ~55 % plochy, stromy po 6 m, okraj 6-10 m keru, pesiny 3.5 m, jehlicnany nad 25 m | zamer novych lesu na neudrzovanych loukach | _nove_lesy | 1 |
| svet.gd:3987,3990 | listnace: buk_stredni, dub_stredni, lipa_stredni, briza_0-2, dub_stary; jehlicnany: smrk_0-2, borovice_0 | druhy noveho lesa | _nove_lesy | 1 |
| svet.gd:4022-4028 | mrizka 6 m | novy les se neprekryva se stavajicimi stromy (bunka 6 m obsazena) | _nove_lesy | 1 |
| svet.gd:4029-4035 | sum seed 6411, freq 0.006, 3 oktavy; sum nd seed 77, freq 0.02; rng 6412 | tvar lesnich celku / mista jehlicnanu | _nove_lesy | 1 |
| svet.gd:4044-4045,4078 | krok 5 m (komentar 6 m), posun +-2 m | rozestup stromu noveho lesa | _nove_lesy | 1 |
| svet.gd:4047 | divokost < 0.4 (komentar 0.55) nebo _louka_m < 0.5 -> nic | les jen na neudrzovane louce | _nove_lesy | 1 |
| svet.gd:4049-4051 | v = sum*0.5+0.5 + (div-0.7)*0.3; v < 0.4 -> nic | prah lesa ze sumu | _nove_lesy | 1 |
| svet.gd:4052 | _u_mostu | ne u mostu | _nove_lesy | 1 |
| svet.gd:4061-4072 | v < 0.48 = okraj lesa; 3-6 keru +-2.5 m; pesina 2.5 m; ker_husty 60 %, sipek_0/2 40 %; y-0.06; meritko 0.7-1.3 (ker_husty ref 1.0) | husty lem keru na okraji lesa | _nove_lesy | 1 |
| svet.gd:4074-4076 | hy > 25 m a nd > -0.2 -> jehlicnan; y-0.1; meritko 0.75-1.15 x ref | volba jehlicnan/listnac, zapusteni stromu | _nove_lesy | 1 |
| svet.gd:4082-4085 | komentar: pas 5-15 m; kraj = zapoj < 0.35, do 8 m zapoj > 0.6; mrizka 2.5 m; plast ~75 %, lem 30 % | zamer lesniho plaste | _lesni_plast | 1 |
| svet.gd:4096 | buk_stredni, lipa_stredni, briza_0/1, olse_mlada | mlade stromy plaste | _lesni_plast | 1 |
| svet.gd:4100,4104 | seed 6414; K = 2.5 m, posun +-0.45 K | mrizka plaste | _lesni_plast | 1 |
| svet.gd:4105-4123 | hruba mrizka 10 m; 5 vzorku; hi > 0.5 a lo < 0.45 | bunky, kde se potkava les a bezlesi (+ sousede) | _lesni_plast | 1 |
| svet.gd:4134-4139 | _les > 0.6 -> nic; max _les ve 6 m (8 smeru, 4.2 diag.) < 0.6 -> nic | bod je kraj lesa | _lesni_plast | 1 |
| svet.gd:4149-4158 | l > 0.35 vnitrni okraj: 30 % mlady strom (meritko 0.25-0.5 x ref, y-0.08), 30 % ker, 40 % nic | vnitrni okraj plaste | _lesni_plast | 1 |
| svet.gd:4159-4168 | l < 0.12 zevni lem: 30 % 1-3 kapradi_les +-0.8 m (y-0.03, meritko 1.0); ker jen u < 0.45 | bylinny lem (kopriva vyrazena: 1-1.5 tis. troj., 25 000 kusu moc) | _lesni_plast | 1 |
| svet.gd:4169-4173 | stred: 80 % ker; y-0.06; meritko 0.7-1.35 | kerovy plast | _lesni_plast | 1 |
| svet.gd:4179-4180 | komentar: kazde 3 m, 1.8-3.2 m od osy, 70 % | zamer keru podel pesin | _kere_podel_pesin | 1 |
| svet.gd:4184,4190 | ker_husty_0 (2x), sipek_0, sipek_1; seed 6413 | druhy keru podel pesin | _kere_podel_pesin | 1 |
| svet.gd:4196-4200 | kazdy 2. bod osy; zapoj max v okoli 8 m < 0.25 -> nic; tvrz abs(x+4)<75 a abs(z)<70 vynechana | kde kere podel pesin | _kere_podel_pesin | 1 |
| svet.gd:4211-4212 | y-0.06; meritko 0.75-1.3 | ker podel pesiny | _kere_podel_pesin | 1 |
| svet.gd:4222-4224 | kapradi_les_0/1, kapradi_1-3, fern_02_0/1, celandine_01_0/1 | kapradi lesni pudy | _lesni_puda | 1 |
| svet.gd:4236 | seed 7171 | nahodnost lesni pudy | _lesni_puda | 1 |
| svet.gd:4241 | dub_, buk_, lipa_, smrk_, borovice_, briza_ (bez olse) | stromy pro lesni pudu | _lesni_puda | 1 |
| svet.gd:4249 | _les < 0.35 -> nic | jen strom v lese | _lesni_puda | 1 |
| svet.gd:4252-4261 | kazdy 2. strom; shluk 1.5-5 m od kmene; 3-7 kusu +-1.6 m; pes_d < 1.6; y-0.03; meritko 0.7-1.3 | shluk kapradi | _lesni_puda | 1 |
| svet.gd:4263-4268 | kazdy 3. strom; 2-6 m od kmene; pes_d < 2.2; y-0.08; meritko 0.7-1.4 | husty ker v lese | _lesni_puda | 1 |
| svet.gd:4273-4274 | kopretiny_0, kvety_bile_0; 5-14 kusu na 1.5 m; jen zblizka (PODROST) | kvetiny na louce | _kvetiny_louky | 3 |
| svet.gd:4283-4285 | seed 5150; 1 shluk na 900 m2 | hustota shluku kvetin | _kvetiny_louky | 1 |
| svet.gd:4288 | _louka_m < 0.6, _les > 0.1, pes_d < 2.5 m, _u_mostu -> nic | kvetiny mimo les, pesiny, most | _kvetiny_louky | 1 |
| svet.gd:4291-4303 | kopretiny 45 %, kvety_bile 25 %, dandelion_01_0-4 30 %; polomer 1.5 m (sqrt); y-0.02; meritko 0.8-1.25 | slozeni shluku kvetin | _kvetiny_louky | 1 |
| svet.gd:4314-4320 | byliny_0-3; seed 6464; 1 pokus na 120 m2 | hustota bylin | _byliny_rozsev | 1 |
| svet.gd:4322 | _les > 0.3 nebo _u_mostu -> nic | byliny mimo les | _byliny_rozsev | 1 |
| svet.gd:4328-4329 | divokost > 0.5, _louka_m > 0.5, 25 % | pelynek (byliny_2) na uhoru | _byliny_rozsev | 1 |
| svet.gd:4335-4339 | 2-6 kusu +-0.8 m; pes_d < 0.6 -> nic; y-0.02; meritko 0.75-1.25 | shluk bylin | _byliny_rozsev | 1 |
| svet.gd:4399-4402 | komentar: podrost u kazdeho 2. stromu 0.25-0.5, 3-7 m; pesiny kazdych 5-9 m 2.2-4.5 m od osy; _pesiny_volne 1.2 m | zamer hustsiho lesa | _les_hustsi | 1 |
| svet.gd:4406-4412 | seed 2026; listnace buk/dub/lipa_stredni, briza_0-3; jehlicnany smrk_0-2, borovice_0 | druhy hustsiho lesa | _les_hustsi | 1 |
| svet.gd:4429-4435 | kazdy 2. strom, _les >= 0.3; 3-7 m; pes_d < 2.0 -> nic; y-0.1; meritko 0.25-0.5 x ref | podrost: mlady strom tehoz druhu | _les_hustsi | 1 |
| svet.gd:4457-4458 | jehlicnan kde _st(0) > _st(1); y-0.1; meritko 0.8-1.2 | druh a velikost stromu u pesiny | _les_hustsi | 1 |
| svet.gd:4960-4967 | 6 m od kazde chyse | stromy a kere na mistech chysi u lomu pryc | _chyse_k_lomu | 1 |
| svet.gd:5047 | okraj 0.6 m od noveho domu (bez stare chalupy) nebo na pasece chyse | rostliny z mist domu pryc | _ves_stare_pryc | 1 |
| svet.gd:5715-5732 | seed 2511; 40 pokusu/dum; z b+0.4..f-0.4; mimo dvere +-1.3 m; 60 % u zdi hw + 0.25-0.7, 40 % u plutku x0 - 0.45-0.7; kopretiny 55 %; y-0.02; meritko 0.8-1.2 | kvetiny zahrad | _kvetiny_zahrad | 1 |
| svet.gd:5870 | trava hrbetu: hrb * o.y * clamp(0.7 sum(0.23 s), 0, 0.9) * 0.22 | travnaty hrbet jen misty a ridce (Misa 0.85 rady trsu) | cesta_profil | 2 |
| svet.gd:6151-6157 | abs(lat) - cesta_ok | vzdalenost za okrajem hliny (louka: nizka ridka trava u cesty) | cesta_kraj | 1 |
| svet.gd:6183-6190 | skupiny: strom, ker, balvan, vysoka_bylina, jinak bylina (pasma.skupiny, podretezec klice) | skupina druhu pro pasma | skupina | 1 |
| svet.gd:6249-6258 | trava jen do abs(lat) < 1.4 hw + 0.9; za okrajem smoothstep(ok + 0.1, ok + 0.7); trsy hrbetu pr.y * 0.9; x > 0.9 = plna trava (louka.gd) | trava na ceste a za rozbitym okrajem | cesta_trava | 1/2 |

## Skaly a kameny

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3880-3881 | balvan_piskovec_2, kamen_piskovec_1/2, kapradi_1-3, mech_1, shrub_02, borovice, smrk, briza | druhy pro skalni mesto (bez kterehokoli se nic nepridava) | _skalni_mesto | 1 |
| svet.gd:3886 | seed 7313 | nahodnost skalniho mesta | _skalni_mesto | 1 |
| svet.gd:3899 | r0 = max(aabb x,z)*0.5 * meritko | polomer veze (pudorys) | _skalni_mesto | 1 |
| svet.gd:3905-3913 | 5 kusu; vzdal. 0.85-1.25 r; velky blok 0.6-1.1, kameny 0.5-1.4; 60 % kamen_1; zapad. 0.2-0.4 x meritko; naklon +-0.3 rad | sut odpadlych bloku u paty veze, zapadana 25-40 % | _skalni_mesto | 1 |
| svet.gd:3916-3921 | 7 kusu (3x kapradi_1, kapradi_2, kapradi_3, 2x mech, 1 shrub_02); vzdal. 0.9-1.6 r; mech 0.04-0.09, ostatni 0.7-1.3; y-0.05 | kapradi, mech a kerik mezi suti | _skalni_mesto | 1 |
| svet.gd:3924-3930 | 1 strom/vez; 1.6-2.6 r; borovice 50 %, smrk 30 %, briza 20 %; _vyska_min - 0.15; meritko 0.8-1.2 x ref | les mezi vezemi | _skalni_mesto | 1 |
| svet.gd:4351 | balvan_, kamen_zula, kamen_piskovec, kamen_droba | kameny, ze kterych nesmi rust strom | _stromy_mimo_balvany | 1 |
| svet.gd:4358-4361 | polomer = meritko x pul max(x,z) AABB; rad < 0.4 m se ignoruje | pudorysny kruh kamene | _stromy_mimo_balvany | 1 |
| svet.gd:4363,4380 | mrizka 8 m | vyhledavani kamenu | _stromy_mimo_balvany | 1 |
| svet.gd:4370-4385 | shrub, sipek, bez_, ker_husty, LISTNACE+JEHLICNATE; uvnitr 0.85 polomeru -> pryc | strom/ker neroste z balvanu | _stromy_mimo_balvany | 1 |
| svet.gd:4871 | LOM_VCHOD = (150, 935) | plocha lomu (PESINY 6 zacina 140,940); smer vchodu chysi | _chyse_k_lomu | 1 |

## Vykreslovani/LOD/stiny/kolize

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:4089-4090 | ker_husty 382 troj., sipek 650 troj. (bez a shrub_02 2-3 tisice) | do plaste jen lehke kere (vykon); ker_husty 3x vaha | _lesni_plast | 3 |
| svet.gd:5117-5118 | create_trimesh_shape | kolize dilu rybnika znovu ze site | _ryb_pod_domy | 3 |
| svet.gd:5482-5496 | dal = 130 m (PC) / 75 m (mobil, TVRZ_MOBIL); _Daleko od dal; Interier do 35 m; Drobne do min(70, dal - 15) m; podrobny vnejsek do dal | LOD domu vsi (rozpocet ves 2000 kresleni, 3.4 M troj.; _Daleko 3000 troj., 2 materialy) | _ves_domy | 3 |
| svet.gd:5497-5512 | Interier bez stinu; stin jen kopie _Daleko (_Stin, SHADOWS_ONLY) do dal; podrobny vnejsek a drobne stin nevrhaji | stiny domu vsi (Misa 0.92: stin domu 186 kresleni) | _ves_domy | 3 |
| svet.gd:5815 | CESTA_BLIZKO = 85.0 m | dosah podrobne site cesty (dal hruby pas Teren_cesta) | stavba cest | 3 |
| svet.gd:5877-5879,5894 | kusy 64 m; visibility_range_begin = CESTA_BLIZKO - 5 = 80 m; bez stinu; puvodni Teren_cesta skryty (kolize z meta kolize_sit) | hruby pas cest jen zdalky (jinak se kreslil u nohou, Misa 0.88) | _cesty_dal_kusy | 3 |
| svet.gd:6699-6701 | Teren_cesta visible = false, meta bez_kolize | hruby pas z Blenderu se uz nekresli ani nekoliduje - cesta je teren (pravidla povrchu A) | _cesty_tvar | 2/3 |
| svet.gd:6809-6832,6873-6882 | cache user://cache/cesty_<commit>_<manifest>_<CESTA_VERZE>.bin (zstd); jen export (template) nebo TVRZ_CACHE; TVRZ_BEZ_CACHE vypne; CESTA_VERZE = 2 | ulozeny vypocet cest v terenu (~16 s na PC) | _cesty_do_terenu, _cesty_cache_cesta | 3 |
| svet.gd:7156-7157 | bez stinu; visibility_range_end = CESTA_BLIZKO (85 m) | dosah site cesty | _cesty_site_stavba | 3 |
| svet.gd:7164-7168 | okluzory: teren (mrizka 12 m, min v bunce - 0.8 m) a domy vsi, hostinec | occlusion culling (plati i v Compatibility) | _okluzory | 3 |
| svet.gd:7169 | OKL_BUNKA = 12.0 m | bunka okluzoru terenu | _okluzory | 3 |
| svet.gd:7170 | OKL_DOMY = false | krabice domu vypnuty (kamera uvnitr by zakryla vse) | _okluzory | 3 |
| svet.gd:7177-7180 | oblast x -250..900, z -250..1350 | rozsah okluzoru terenu | _okluzory | 3 |
| svet.gd:7186-7190 | min z 3x3 vzorku po 6 m; - 0.8 m | okluzor vsude pod terenem (komentar: 4x4 po 4 m) | _okluzory | 3 |
| svet.gd:7201-7211,7215-7224 | krabice k = 0.8 (komentar: zmensene o 15 %), vyska x 0.6, posun -0.2 vysky; jen obal > 2 m; hostinec AABB > 15 m | krabicove okluzory domu a hostince | _okluzory, _okl_krabice | 3 |

## Materialy/textury

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:3674,3768 | 2 povrchy -> 3 (kura, listi, spodek s kurou kmene) | briza: spodek kmene do neprusvitne kury, stejny material kura0 | _briza_kmen | 4 |
| svet.gd:4553-4557 | material zeli_* pryc, zeli_hlava -> stred | zeli z Blenderu (zelene koule) radeji nic nez primitiv; zahon zustava | _bez_zeli | 4 |
| svet.gd:5801-5804 | override materialy prenaset podle poradi povrchu | jinak stodoly s holym materialem z exportu (hnede krabice) | _ves_site_vyrez | 4 |
| svet.gd:6103-6104 | Poly Haven dry_ground_rocks_disp 512 px na 4 m (p.xz / 4) | vyskova mapa povrchu cest | cesta_disp | 4 |
| svet.gd:6112-6115 | atlas 2x2 po 256 px; prach dlazdice 0 (2 m), kameni dlazdice 2 (2 m), posun 0.37 | vyska podle kamenitosti useku | cesta_disp | 4 |
| svet.gd:6137 | res://obrazky/cesta/cesta_atlas_disp.png | atlas vysek cest | _disp_nacti | 4 |
| svet.gd:6144-6146 | zmenseno na 16x16 px (8 px na 2 m dlazdici = ~0.5 m) | jen hrube hrboly; jemne kaminky delaly podelne ryhy ("uhrabana"); detail = normalova mapa | _disp_nacti | 4 |
| svet.gd:6896-6909 | CUSTOM0 = (lat/ok, s, koleje, ok); CUSTOM1 = (trava, bahno max(pr.z, 0.6 op.z), vzd. od koleje/2 nebo 1, 7.0); mimo cestu (9, 0, 0, 0) / (0, 0, 1, 0) | udaje cesty do vrcholu terenu pro zem.gdshader | _cesta_v | 2/4 |
| svet.gd:7121-7124 | barva: r koleje, g trava (ves x 0.25), b vzd. koleje/2, a = 1 - 0.18 bahno - 0.1 smoothstep(0.4, 0.8) louze | vstupy zem.gdshader (bahno, kalna voda) | _cesty_site_stavba | 2/4 |
| svet.gd:7125-7128 | UV = svet xz (x, -z); UV2 = (abs(lat)/ok, s) | UV textur cesty (>= 1 za okrajem trava site nekresli) | _cesty_site_stavba | 4 |

## Ostatni

| soubor:radek | hodnota | vyznam | kdo pouziva (funkce) | tabulka (1/2/3/4) |
|---|---|---|---|---|
| svet.gd:6160-6170 | res://pravidla/pravidla_sveta.json -> "pasma" | JEDINA tabulka odstupu (cesty, budovy, voda, skaly) pro svet, louka.gd a test zasazeni | pasma | 1 |


## Duplicity a rozpory

Pozn.: svet.gd:6160-6203 uz ma centralni tabulku `pravidla/pravidla_sveta.json` -> `pasma` (cesta vozova/ulice_vsi/pesina: drn_m 2/2/1, trsy_od_m 2/2/1, ker_od_m 3/3/1.5, kmen_m 6/3/3; budova dvur_m 2, kmen_od_zdi_m 2.5; voda breh_m 1.5; skala trava_max_sklon_st 40). Meri se OD KRAJE HLINY (cesta_ok). Vsechny rozsevy v tomto useku (3600-7200) ji ale NEPOUZIVAJI a maji vlastni cisla, merena vetsinou pres pes_d (od osy pesiny).

| tema | mista a hodnoty | rozpor |
|---|---|---|
| Odstup rostlin od pesiny | nove lesy strom 3.5 m (4054), kere okraje 2.5 (4065); lesni plast 1.8 (4143); kere podel pesin 1.5 (4208), umisteni 1.8-5.0 x pes_f (4207); lesni puda kapradi 1.6 (4258), husty ker 2.2 (4266); les hustsi podrost 2.0 (4433), stromoradi 2.0 (4455), umisteni 2.2-4.5 (4454); kvetiny 2.5 (4288); byliny 0.6, pas 0.7-1.8 (4326, 4337); komentar _pesiny_volne 1.2 (4402) | 10 ruznych cisel, jina vztazna cara (osa) nez pasma.pesina (kraj hliny: ker 1.5, kmen 3.0) |
| Odstup od hladiny / vody | nove lesy voda_y + 0.5 (4057), lesni plast voda_y + 0.4 (4146), _u_mostu bere cele koryto do hladina + 0.5 (4514), zarez potoka strop < hy + 1.5 (4059), bahno cest do 10-15 m (6316), brod 3-9 m (6324), kotva 6-20 m (6332); vychozi voda_y -2.75 na dvou mistech | pasma.voda.breh_m 1.5 (vodorovne od brehu) se nepouziva; svisle prahy 0.4 vs 0.5 |
| Hladina u brodu | hladina koryta -9.2 vs viditelna voda reka.res -8.3 (4598-4611) | dva zdroje hladiny lisici se o ~1 m, brod prepisuje medianem z reka.res |
| Vyloucene okoli tvrze (obdelniky) | lesni plast abs(x+4) < 80, abs(z) < 75 (4141); kere podel pesin < 75 / < 70 (4200); les hustsi < 60 / < 60 (4451); CESTA_UDUSANO brana (0, 24) r 22 (6265) | tri ruzne obdelniky pro "okoli tvrze" |
| Vyloucena ves | lesni plast kruh (470, 830) r 140 (4141); stara naves stred (470, 830) (6573); VES_OBLOUK / _vo_stara_naves (6555); ves_cesta maska m < 60 (3826) | ves vymezena kruhem, maskou i obloukem |
| Prahy "je to les" (_les) | lesni puda < 0.35 (4249), les hustsi < 0.3 (4429), stromoradi a kere podel pesin < 0.25 (4451, 4200), plast > 0.6 / > 0.35 / < 0.12 (4134-4159), hrube hi > 0.5 lo < 0.45 (4118), kvetiny > 0.1 (4288), byliny > 0.3 (4322) | ruzne prahy |
| Sklon | sklon_bunky > 0.9 zakaz lesa a plaste (4054, 4143); divizna 0.35-1.0 (4330); pasma.skala trava_max_sklon_st 40 st. (tan ~0.84); vymleti cest smoothstep(0.12, 0.2) (6317) vs komentar "nad 8 st." (0.14); bahno sklon < 0.03-0.06 vs komentar "< 2 st." (0.035) | rozdilne jednotky (pomer vs stupne) a prahy |
| Jehlicnany jen nad 25 m (pravidlo 1393) | nahrada smrku pod 25 m (3610); nove lesy hy > 25 (4074); les hustsi voli jehlicnan podle stanoviste _st(0) > _st(1) bez vysky (4457); skalni mesto pridava smrk/borovici bez kontroly vysky (3927) | pravidlo plati jen ve dvou funkcich |
| Zapusteni rostlin pod teren | stromy -0.1 (4076, 4435, 4458), -0.15 + _vyska_min (3930), mlade -0.08 (4154), kere -0.05 (3865), -0.06 (4071, 4173, 4212), husty ker -0.08 (4268), kapradi -0.03, kvetiny/byliny -0.02, mech a drevo -0.05 | zadna spolecna tabulka; _vyska_min jen u skalniho mesta (r 2 m) a dreva u domu (r 0.8) |
| Stromy u budov | _ves_stare_pryc rostliny do 0.6 m od noveho domu (5047); _dum_zabira okraj 0.2 (4978); chyse paseka 12 m (4738) / 6 m (4950) a zvlast 6 m od chysi u lomu (4964) | pasma.budova.kmen_od_zdi_m 2.5 se zde nepouziva |
| Most | _u_mostu AABB + 5 m (4503, 4513); _most_bez_stromu sirka + 7 m strom / + 4 m ker, najezdy NAJEZD_DELKA 14 m (4486) | dve ruzne zony "u mostu" |
| Vyska cesty nad terenem | komentar cesta_y: teren + 2 cm, uvnitr + 5 cm (6085-6087); cesta_d: 0.06 + dy + relief, clamp -0.14..+0.2, val + 0.05 (6100); osa vsi teren + 0.02 (6568, 6574); konce - 0.3 x 0.45 (7111) | komentar a kod se lisi (0.02 vs 0.06) |
| Hloubka koleji | komentar 5-15 cm (5828), 8-12 cm (5843), 3-5 cm (5844); kod 0.04 + 0.03 bahno + 0.02 sum (~4-9 cm) (5847); komentar "koleje 0.2 m pod osou" (6739) | tri komentare, kod jinak |
| Zarez / nasyp cest | komentar max 5 m (5928); kod clamp +-3.0 (5969); ulice vsi +-0.25 (5975); prechod do okoli ok + 1..ok + 12 m (6005, 6092, 6907) vs komentar "do 8 m za okraj" (5929) | 5 vs 3 m; 8 vs 12 m |
| Dosah site cesty | CESTA_BLIZKO 85 (5815, 7157); hruby pas od 80 m (5919), komentar "80 m" (5878); hruby pas nakonec skryt uplne a bez kolize (6700) | prekryv 80-85 m, _cesty_dal_kusy zrejme uz nepouzite |
| Sirka chodnicku ke dverim | komentar 0.5 m (4810), PES_SIRKA 0.45 (4834, 4958); jako osa cesty pulsirka 0.75 m = 1.5 m sirka (6640) | sit cest ma dvojnasobnou sirku |
| Hustota novych lesu | komentar divokost > 0.55, stromy po 6 m (3977-3978); kod divokost < 0.4 vylouci, krok 5 m (4045, 4047) | komentar neodpovida kodu |
| Lesni patro / kere u pesin | lesni patro komentar "kazdy 3. kerik", kod i % 2 (3967); kere podel pesin komentar "kazde 3 m, 1.8-3.2 m, 70 %", kod kazdy 2. bod (1.6 m), 1.8-5.0 m, 45 % (4196-4207) | komentar neodpovida kodu |
| Podlaha nad terenem | domy max + 0.1 (5144); chyse komentar + 0.05 (5642), kod max + 0.03 (kura) / min - 0.01 (prkna) (5646); komentar podezdivka 0.45 + 0.3 (5080) | ruzne |
| Teren u zdi domu | dum_teren uvnitr y0 - 0.15, u zdi y0 - 0.2 az - 0.02 do 1.8 m (5187-5194); komentar "pas 1.5 m" (5081); pasma.test podlaha_teren_m 0.5 | 1.5 vs 1.8 m |
| Kridla stodol | komentar 1.2-1.45 x 2.2-2.5 m (5274), kod 1.15-1.5 x 2.1-2.6 (5309); blender 1.3 m | tolerance v kodu sirsi nez komentar |
| Okluzory | komentar "zmensene o 15 %" (7201), kod k = 0.8 (20 %); komentar "4 x 4 vzorky po 4 m", kod 3 x 3 po 6 m (7181-7189) | komentar neodpovida kodu |
| Pudorys kamene | skalni mesto r0 = pul max(x, z) AABB (3899); stromy mimo balvany stejny polomer x 0.85, pod 0.4 m ignorovan (4358-4385) | konzistentni, ale pocitano dvakrat |
| Prechod hliny do travy | cesta_trava do 1.4 hw + 0.9 (6251), smoothstep(ok + 0.1, ok + 0.7) (6257); cesta_profil smoothstep(ok - 0.35, ok + 0.05) (5873); maska vsi jizdni pas = cesta_ok (3799); trava ve vsi x 0.25 (7123) | tri ruzne prechody okraje |
