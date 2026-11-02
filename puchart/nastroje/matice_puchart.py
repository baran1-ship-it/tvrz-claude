"""Zapojení matice vztahů (pravidla/svet/vztahy.json, převzato z Havrana) pro Puchart: ke každé dvojici druhů testy
Puchartu (testy_puchart), nebo nenastava_puchart / nezavisle_puchart s důvodem. Jednorázově zapíše do vztahy.json;
pak se mapování udržuje v datech (ruční úpravy přímo v souboru). python3 nastroje/matice_puchart.py <koren>"""
import sys, json, itertools
K = sys.argv[1]; p = K + "/pravidla/svet/vztahy.json"; V = json.load(open(p))
NENI = {"plot": "ploty a vrata vsi v Puchartu zatím nejsou (vesnice = krok F)", "posun": "přesun lokace je nástroj Havrana, Puchart stojí na skutečném terénu",
        "kun": "kůň zatím není (krok E funkce)", "postava": "postavy zatím nejsou (krok F lidé)"}
T = {  # dvojice -> testy (smysl:… = nastroje/test_smyslu.py, pruchod:… = hra/scripts/test_pruchod.gd)
 "teren|teren": ["smysl:teren_skoky", "smysl:dlazdice"], "teren|voda": ["smysl:voda_v_korytu", "smysl:hladina_nestoupa"],
 "teren|cesta": ["smysl:cesta_zarez"], "teren|budova": ["smysl:visi_puchart", "pruchod:vse"], "teren|kamen": ["smysl:visi_skaly"],
 "teren|predmet": ["smysl:visi_puchart"], "teren|hrac": ["pruchod:vse"], "teren|svetlo": ["smysl:svetla_u_staveb"],
 "teren|lod": ["smysl:dlazdice"], "teren|kolize": ["pruchod:vse"],
 "voda|voda": ["smysl:hladina_nestoupa"], "voda|cesta": ["smysl:lavka_na_brehu", "pruchod:lavka_brod_velicka"],
 "voda|strom": ["smysl:strom_mimo_vodu"], "voda|ker": ["smysl:porost_mimo_cestu"], "voda|bylina": ["smysl:koryto_kameny", "smysl:stanoviste_porost"],
 "voda|kamen": ["smysl:koryto_kameny"], "voda|hrac": ["pruchod:lavka_brod_velicka"], "voda|kolize": ["pruchod:lavka_brod_velicka"],
 "cesta|cesta": ["smysl:cesta_zarez"], "cesta|budova": ["pruchod:A_vstup", "pruchod:B_vstup"], "cesta|strom": ["smysl:strom_mimo_cestu"],
 "cesta|ker": ["smysl:porost_mimo_cestu"], "cesta|bylina": ["smysl:porost_mimo_cestu"], "cesta|hrac": ["pruchod:cesta_mezi_hrady"], "cesta|kolize": ["pruchod:cesta_mezi_hrady"],
 "budova|budova": ["smysl:visi_puchart", "pruchod:vse"], "budova|strom": ["smysl:hrad_bez_stromu"], "budova|ker": ["smysl:kere_mimo_stavby"],
 "budova|bylina": ["smysl:kere_mimo_stavby", "smysl:stanoviste_porost"], "budova|kamen": ["smysl:visi_puchart", "smysl:visi_skaly"],
 "budova|predmet": ["smysl:visi_puchart"], "budova|hrac": ["pruchod:vse"], "budova|svetlo": ["smysl:svetla_u_staveb"],
 "budova|lod": ["smysl:hrad_daleko"], "budova|kolize": ["pruchod:vse"],
 "strom|lod": ["smysl:lod_navaznost"], "ker|lod": ["smysl:lod_navaznost", "smysl:dohled_za_porostem"], "bylina|lod": ["smysl:lod_navaznost"],
 "kamen|kamen": ["smysl:visi_skaly"], "kamen|hrac": ["pruchod:cesta_mezi_hrady"], "kamen|kolize": ["pruchod:cesta_mezi_hrady"],
 "predmet|predmet": ["smysl:visi_puchart"], "predmet|hrac": ["pruchod:A_sklep_kobky", "pruchod:A_palac"], "predmet|kolize": ["pruchod:A_palac"],
 "hrac|kolize": ["pruchod:vse"], "lod|lod": ["smysl:lod_navaznost", "smysl:dohled_za_porostem"], "kolize|kolize": ["pruchod:vse"],
}
NEZ = {  # vědomě bez testu, s důvodem
 "teren|strom": "výška stromu se bere z terénu za běhu (les.gd svet.vyska) – nemůže se rozejít", "teren|ker": "výška keře z terénu za běhu (byliny.gd)",
 "teren|bylina": "výška byliny z terénu za běhu (byliny.gd)", "voda|svetlo": "voda bez bodových světel (shader)", "voda|lod": "potoky jedna síť bez LOD (17 k troj.)",
 "voda|budova": "hrady na ostrohu, toky v údolí – nepotkají se", "voda|predmet": "předměty jen uvnitř hradu",
 "cesta|kamen": "hřebenová cesta vede záměrně po skalním podkladu (skaly_podklad.py)", "cesta|predmet": "předměty jen uvnitř hradu",
 "cesta|svetlo": "na cestách nejsou světla", "cesta|lod": "cesta je v textuře terénu (maska_cesty)",
 "strom|strom": "polohy a rozestup ze skutečných korun (DMP − DMR)", "strom|ker": "keř pod korunou smí (zmlazení, okraj)", "strom|bylina": "bylina pod korunou smí",
 "strom|kamen": "strom na suti a skále smí (les_sut)", "strom|predmet": "předměty jen uvnitř hradu", "strom|svetlo": "pochodně jen ve stavbách",
 "ker|ker": "shluky jsou záměr (kere.json shluky)", "ker|bylina": "bylina pod keřem smí", "ker|kamen": "keř u kamene smí",
 "ker|predmet": "předměty jen uvnitř hradu", "ker|hrac": "keře bez kolize – procházet se smí (KCD)", "ker|svetlo": "pochodně jen ve stavbách",
 "ker|kolize": "keře záměrně bez kolize", "bylina|bylina": "trsy se smí překrývat", "bylina|kamen": "bylina u kamene smí", "bylina|predmet": "předměty jen uvnitř hradu",
 "bylina|hrac": "byliny bez kolize", "bylina|svetlo": "pochodně jen ve stavbách", "bylina|kolize": "byliny bez kolize",
 "kamen|predmet": "předměty jen uvnitř hradu", "kamen|svetlo": "pochodně jen ve stavbách", "kamen|lod": "skály jedna síť (skaly.glb), dálka = terén",
 "predmet|svetlo": "pochodně bez stínů – předměty se neovlivní", "predmet|lod": "předměty malé, zanikají s LOD hradu", "hrac|hrac": "jeden hráč",
 "hrac|svetlo": "světla bez interakce", "hrac|lod": "LOD podle kamery, hráč ho nemění", "svetlo|svetlo": "pochodně bez stínů, zhasínají na dálku (hlavni.gd)",
 "svetlo|lod": "světla zhasínají na dálku sama (distance_fade)", "svetlo|kolize": "světla bez kolize", "lod|kolize": "kolize z kvádrů KOLIZE, ne z LOD",
}
pokryto = 0; diry = []
for a, b in itertools.combinations_with_replacement(V["druhy"], 2):
    k = "%s|%s" % (a, b); e = V["dvojice"].setdefault(k, {})
    for x in ("testy_puchart", "nenastava_puchart", "nezavisle_puchart"): e.pop(x, None)
    if a in NENI or b in NENI: e["nenastava_puchart"] = NENI[a if a in NENI else b]
    elif k in T: e["testy_puchart"] = T[k]
    elif k in NEZ: e["nezavisle_puchart"] = NEZ[k]
    else: diry.append(k)
V["puchart_zapojeno"] = True
V["puchart_popis"] = "2. 11.: testy_puchart = testy Puchartu (smysl:… nastroje/test_smyslu.py, pruchod:… test průchodu); nenastava_puchart / nezavisle_puchart s důvodem; dvojice bez ničeho = díra (nastroje/kontrola_vztahu.py ji hlásí, ostré vydání odmítne)"
json.dump(V, open(p, "w"), ensure_ascii=False, indent=1)
print("díry:", diry)
