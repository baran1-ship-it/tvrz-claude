"""Predmety pro inventar a staveni: modely Poly Haven (CC0) ve 2k, kazdy jako samostatny GLB s texturami,
k nemu ikona (render 3/4 pohled) a zapis v katalogu modely/predmety.json.
  /opt/bl/bin/python predmety.py fetch     -> stahne modely do tex_cache/models/<id>
  /opt/bl/bin/python predmety.py build     -> modely/predmety/<id>.glb, modely/predmety/<id>.png, modely/predmety.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "tex_cache", "models")
OUT = os.path.join(HERE, "..", "modely", "predmety")

# id: (poly haven id, nazev, kategorie brasny nebo None, podzalozka staveni nebo None, vaha kg, cena gr, vlastnosti)
# vlastnosti: kont=N (uloziste s N mista), sed (da se sednout), lehat
KATALOG = {
    "sud": ("wine_barrel_01", "Sud", "nadoby", "uvnitr", 25.0, 30, {"kont": 80}),
    "truhla": ("treasure_chest", "Okovaná truhla", None, "uvnitr", 30.0, 120, {"kont": 120}),
    "bedna": ("wooden_crate_01", "Bedna", None, "venku", 12.0, 15, {"kont": 60}),
    "bedna_znak": ("wooden_crate_02", "Bedna se značkou", None, "venku", 12.0, 18, {"kont": 60}),
    "vedro": ("wooden_bucket_01", "Vědro", "nadoby", "venku", 2.0, 4, {}),
    "kad": ("wooden_bucket_02", "Káď", "nadoby", "remeslo", 14.0, 12, {"meritko": 1.55, "kont": 60}),
    "kosik": ("wicker_basket_01", "Košík", "nadoby", "uvnitr", 0.5, 4, {"kont": 10}),
    "kos_viko": ("wicker_basket_02", "Koš s víkem", "nadoby", "uvnitr", 3.0, 10, {"meritko": 2.3, "kont": 40}),
    "postel": ("GothicBed_01", "Gotická postel", None, "uvnitr", 60.0, 400, {"lehat": True}),
    "skrin": ("GothicCabinet_01", "Gotická skříň", None, "uvnitr", 70.0, 450, {"kont": 150}),
    "lavice_nizka": ("WoodenTable_01", "Nízká lavice", None, "uvnitr", 15.0, 20, {"sed": True}),
    "stolicka": ("wooden_stool_01", "Stolička", None, "uvnitr", 3.0, 6, {"sed": True}),
    "spalek": ("wooden_stool_02", "Špalková stolička", None, "venku", 4.0, 4, {"sed": True, "meritko": 2.5}),
    "stolicka_skladaci": ("folding_wooden_stool", "Skládací stolička", None, "venku", 2.5, 8, {"sed": True}),
    "lavice": ("painted_wooden_bench", "Lavice s opěradlem", None, "uvnitr", 25.0, 60, {"sed": True}),
    "kolovrat": ("spinning_wheel_01", "Kolovrat", None, "remeslo", 12.0, 90, {}),
    "sekera": ("wooden_axe", "Sekera", "naradi", "zbrojnice", 2.2, 90, {}),
    "sekera_tesarska": ("wooden_axe_02", "Tesařská sekera", "naradi", "zbrojnice", 2.4, 110, {}),
    "sekera_valecna": ("wooden_axe_03", "Válečná sekera", "zbrane", "zbrojnice", 2.6, 310, {}),
    "stit": ("kite_shield", "Štít", "zbroj", "zbrojnice", 4.5, 260, {}),
    "kladivo_valecne": ("ornate_war_hammer", "Válečné kladivo", "zbrane", "zbrojnice", 3.0, 420, {}),
    "lucerna": ("wooden_lantern_01", "Lucerna", "ostatni", "dekorace", 1.2, 25, {}),
    "svicen": ("wooden_candlestick", "Svícen", "ostatni", "dekorace", 0.6, 12, {}),
    "miska": ("wooden_bowl_01", "Miska", "nadoby", "dekorace", 0.3, 2, {}),
    "lzice": ("wooden_spoon", "Lžíce", "ostatni", "dekorace", 0.1, 1, {}),
    "talir": ("carved_wooden_plate", "Talíř", "nadoby", "dekorace", 0.4, 3, {}),
    "prkenko": ("wooden_cutting_board", "Prkénko", "ostatni", "dekorace", 0.8, 3, {}),
    # druha varka: stoly, zidle, kresla, nadobi
    "stul_prkenny": ("wooden_table_02", "Prkenný stůl", None, "uvnitr", 25.0, 40, {}),
    "stolek": ("small_wooden_table_01", "Stolek", None, "uvnitr", 12.0, 18, {}),
    "stul_malovany": ("painted_wooden_table", "Malovaný stůl na kozách", None, "uvnitr", 30.0, 60, {}),
    "stul_ubrus": ("dining_table", "Stůl s ubrusem", None, "uvnitr", 35.0, 80, {}),
    "stolek_goticky": ("gothic_coffee_table", "Gotický stolek", None, "uvnitr", 18.0, 120, {}),
    "truhla_vyrezavana": ("gallinera_table", "Vyřezávaná truhla", None, "uvnitr", 40.0, 160, {"kont": 120}),
    "zidle_goticka": ("WoodenChair_01", "Gotická židle", None, "uvnitr", 8.0, 90, {"sed": True, "meritko": 0.65}),
    "zidle_selska": ("painted_wooden_chair_02", "Selská židle", None, "uvnitr", 5.0, 15, {"sed": True}),
    "kreslo": ("gallinera_chair", "Vyřezávané křeslo", None, "uvnitr", 18.0, 140, {"sed": True}),
    "stolicka_vysoka": ("painted_wooden_stool", "Vysoká stolička", None, "remeslo", 4.0, 8, {"sed": True}),
    "hrnec": ("ceramic_pot", "Hliněný hrnec", "nadoby", "dekorace", 2.0, 5, {}),
    "kotlik": ("brass_pot_01", "Měděný kotlík", "nadoby", "remeslo", 4.0, 45, {}),
    "panev": ("brass_pot_02", "Měděná pánev", "nadoby", "dekorace", 2.5, 30, {}),
    "svicny": ("brass_candleholders", "Mosazný kandelábr", "ostatni", "dekorace", 1.4, 45, {"dil": "brass_candleholder_03"}),
    "dvojsvicen": ("brass_candleholders", "Mosazný dvojsvícen", "ostatni", "dekorace", 0.6, 20, {"dil": "brass_candleholder_02"}),
    "svicen_mosaz": ("brass_candleholders", "Mosazný svícen", "ostatni", "dekorace", 0.3, 12, {"dil": "brass_candleholder_01"}),
    # treti varka (Poly Haven): nabytek, zbrane, naradi, vyzdoba, jidlo
    "komoda": ("GothicCommode_01", "Gotická komoda", None, "uvnitr", 45.0, 300, {"kont": 100}),
    "kreslo_goticke": ("ArmChair_01", "Čalouněné křeslo", None, "uvnitr", 20.0, 220, {"sed": True}),
    "zidle_calounena": ("GreenChair_01", "Čalouněná židle", None, "uvnitr", 7.0, 110, {"sed": True}),
    "nocni_stolek": ("painted_wooden_nightstand", "Noční stolek", None, "uvnitr", 10.0, 30, {"kont": 20}),
    "police": ("Shelf_01", "Dřevěná police", None, "uvnitr", 15.0, 25, {}),
    "police_malovana": ("painted_wooden_shelves", "Malovaná police", None, "uvnitr", 20.0, 45, {}),
    "police_stara": ("wooden_bookshelf_worn", "Stará police", None, "remeslo", 18.0, 15, {}),
    "skrin_malovana": ("painted_wooden_cabinet", "Malovaná skříň", None, "uvnitr", 50.0, 160, {"kont": 100}),
    "skrinka": ("painted_wooden_cabinet_02", "Skříňka", None, "uvnitr", 25.0, 70, {"kont": 50}),
    "skrin_selska": ("vintage_cabinet_01", "Selská skříň", None, "uvnitr", 55.0, 120, {"kont": 110}),
    "stul_kulaty": ("round_wooden_table_01", "Kulatý stůl", None, "uvnitr", 20.0, 50, {}),
    "stul_kulaty_stary": ("round_wooden_table_02", "Starý kulatý stůl", None, "uvnitr", 22.0, 45, {}),
    "stul_dubovy": ("WoodenTable_02", "Dubový stůl", None, "uvnitr", 28.0, 55, {}),
    "stul_dilna": ("WoodenTable_03", "Stůl do dílny", None, "remeslo", 30.0, 35, {}),
    "pohovka_drevena": ("painted_wooden_sofa", "Dřevěná pohovka", None, "uvnitr", 30.0, 90, {"sed": True}),
    "dyka": ("ornate_medieval_dagger", "Zdobená dýka", "zbrane", "zbrojnice", 0.5, 180, {}),
    "palcat": ("ornate_medieval_mace", "Palcát", "zbrane", "zbrojnice", 2.5, 380, {}),
    "estok": ("antique_estoc", "Estok", "zbrane", "zbrojnice", 1.6, 520, {}),
    "tesak": ("wooden_handle_saber", "Tesák", "zbrane", "zbrojnice", 1.3, 160, {}),
    "sekerka": ("hatchet", "Sekerka", "naradi", "zbrojnice", 1.0, 40, {}),
    "kladivo": ("cross_pein_hammer", "Kladivo", "naradi", "remeslo", 1.0, 25, {}),
    "krumpac": ("picke_dirty_01", "Krumpáč", "naradi", "remeslo", 3.0, 35, {}),
    "ryc": ("rusted_spade_01", "Rýč", "naradi", "remeslo", 2.0, 20, {}),
    "hoblik": ("hand_plane_no4", "Hoblík", "naradi", "remeslo", 1.5, 30, {}),
    "nebozez": ("vintage_hand_drill", "Nebozez", "naradi", "remeslo", 1.2, 28, {}),
    "pohary": ("brass_goblets", "Mosazné poháry", "nadoby", "dekorace", 0.6, 60, {}),
    "dzban": ("jug_01", "Džbán", "nadoby", "dekorace", 1.0, 6, {}),
    "dzban_kovovy": ("metal_jug", "Kovový džbán", "nadoby", "dekorace", 1.2, 20, {}),
    "vaza": ("brass_vase_01", "Mosazná váza", "nadoby", "dekorace", 1.0, 40, {}),
    "konvice_zdobena": ("brass_vase_03", "Zdobená konvice", "nadoby", "dekorace", 1.2, 55, {}),
    "miska_zdobena": ("wooden_bowl_02", "Zdobená miska", "nadoby", "dekorace", 0.4, 8, {}),
    "panvice": ("brass_pan_01", "Měděná pánev s rukojetí", "nadoby", "remeslo", 1.5, 25, {}),
    "sachy": ("chess_set", "Šachy", "ostatni", "dekorace", 1.5, 90, {}),
    "lvi_hlava": ("lion_head", "Lví hlava na podstavci", None, "dekorace", 6.0, 150, {}),
    "konska_hlava": ("horse_head", "Koňská hlava", None, "dekorace", 6.0, 140, {"zed": True}),
    "zrcadlo": ("ornate_mirror_01", "Zdobené zrcadlo", None, "dekorace", 8.0, 300, {"zed": True}),
    "socha": ("gothic_statue", "Gotická socha", None, "dekorace", 60.0, 500, {}),
    "sudy": ("wooden_barrels_01", "Hromada sudů", None, "venku", 80.0, 60, {}),
    "jablko": ("food_apple_01", "Jablko", "jidlo", "dekorace", 0.2, 1, {}),
    "cibule": ("yellow_onion", "Cibule", "jidlo", "dekorace", 0.2, 1, {}),
    "bochanky": ("hamburger_buns", "Bochánky", "jidlo", "dekorace", 0.5, 2, {}),
    # vlastni modely (vlastni.py)
    "kozesina": ("@", "Medvědí kožešina", "ostatni", "dekorace", 8.0, 150, {}),
    "ovci_kuze": ("@", "Ovčí kůže", "ostatni", "dekorace", 2.0, 25, {}),
    "koberec": ("@", "Koberec", None, "dekorace", 12.0, 200, {}),
    "koberec_modry": ("@", "Modrý koberec", None, "dekorace", 7.0, 140, {}),
    "polstar": ("@", "Polštář", "ostatni", "dekorace", 0.6, 12, {}),
    "polstar_zeleny": ("@", "Zelený polštář", "ostatni", "dekorace", 0.6, 10, {}),
    "stul_hodovni": ("@", "Hodovní stůl", None, "uvnitr", 90.0, 300, {}),
    "lavice_hodovni": ("@", "Hodovní lavice", None, "uvnitr", 30.0, 60, {"sed": True}),
    "stul_pansky": ("@", "Panský hodovní stůl", None, "uvnitr", 160.0, 900, {}),
    "kreslo_panske": ("@", "Panské křeslo", None, "uvnitr", 22.0, 260, {"sed": True}),
    "drzak_louce": ("@", "Držák s loučí", None, "dekorace", 2.0, 30, {"zed": True, "louc": True}),
    "louc": ("@", "Louč", "ostatni", "dekorace", 0.6, 2, {}),
    "stit_lipa": ("@", "Štít pánů z Lipé", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_lichtenburk": ("@", "Štít Lichtenburků", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_rozmberk": ("@", "Štít Rožmberků", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_hradec": ("@", "Štít pánů z Hradce", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_krumlov": ("@", "Štít pánů z Krumlova", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_sternberk": ("@", "Štít Šternberků", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_pernstejn": ("@", "Štít Pernštejnů", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_svamberk": ("@", "Štít Švamberků", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_michalovic": ("@", "Štít Michaloviců", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_vartenberk": ("@", "Štít Vartenberků", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_kolovrat": ("@", "Štít Kolovratů", "zbroj", "zbrojnice", 4.0, 300, {}),
    "stit_lobkovic": ("@", "Štít Lobkoviců", "zbroj", "zbrojnice", 4.0, 300, {}),
    "paveza": ("@", "Pavéza", "zbroj", "zbrojnice", 9.0, 340, {}),
    "puklir": ("@", "Puklíř", "zbroj", "zbrojnice", 1.8, 150, {}),
    "mec_dlouhy": ("@", "Dlouhý meč", "zbrane", "zbrojnice", 1.5, 600, {}),
    "halapartna": ("@", "Halapartna", "zbrane", "zbrojnice", 3.2, 260, {}),
    "kopi": ("@", "Kopí", "zbrane", "zbrojnice", 2.2, 90, {}),
    "hak_zbrane": ("@", "Hák na zbraň", None, "zbrojnice", 1.5, 12, {"zed": True, "kont": 20, "jen": ["zbrane", "zbroj", "naradi"],
                                                                  "sloty": [[0.0, 0.11, 0.05]]}),
    "stojan_zbrani": ("@", "Stojan na zbraně", None, "zbrojnice", 35.0, 80, {"kont": 60, "jen": ["zbrane", "naradi"],
                                                                         "sloty": [[-0.55 + 0.22 * i, 0.2, 0.0] for i in range(6)]}),
    "stojan_louce": ("@", "Stojan na louč", None, "venku", 9.0, 45, {"louc": True, "louc_pos": [0.0, 1.21, 0.0]}),
    "prapor_lipa": ("@", "Prapor pánů z Lipé", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_lipa": ("@", "Vlajka pánů z Lipé", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_lichtenburk": ("@", "Prapor Lichtenburků", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_lichtenburk": ("@", "Vlajka Lichtenburků", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_rozmberk": ("@", "Prapor Rožmberků", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_rozmberk": ("@", "Vlajka Rožmberků", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_hradec": ("@", "Prapor pánů z Hradce", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_hradec": ("@", "Vlajka pánů z Hradce", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_krumlov": ("@", "Prapor pánů z Krumlova", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_krumlov": ("@", "Vlajka pánů z Krumlova", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_sternberk": ("@", "Prapor Šternberků", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_sternberk": ("@", "Vlajka Šternberků", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_pernstejn": ("@", "Prapor Pernštejnů", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_pernstejn": ("@", "Vlajka Pernštejnů", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_svamberk": ("@", "Prapor Švamberků", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_svamberk": ("@", "Vlajka Švamberků", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_michalovic": ("@", "Prapor Michaloviců", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_michalovic": ("@", "Vlajka Michaloviců", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_vartenberk": ("@", "Prapor Vartenberků", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_vartenberk": ("@", "Vlajka Vartenberků", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_kolovrat": ("@", "Prapor Kolovratů", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_kolovrat": ("@", "Vlajka Kolovratů", None, "venku", 4.0, 150, {"zed": True}),
    "prapor_lobkovic": ("@", "Prapor Lobkoviců", None, "dekorace", 3.0, 180, {"zed": True}),
    "vlajka_lobkovic": ("@", "Vlajka Lobkoviců", None, "venku", 4.0, 150, {"zed": True}),
    "tapiserie_rozmberk": ("@", "Tapiserie Rožmberků", None, "dekorace", 6.0, 400, {"zed": True}),
    "tapiserie_hradec": ("@", "Tapiserie pánů z Hradce", None, "dekorace", 6.0, 400, {"zed": True}),
    "tapiserie_sternberk": ("@", "Tapiserie Šternberků", None, "dekorace", 6.0, 400, {"zed": True}),
    "tapiserie_lipa": ("@", "Tapiserie pánů z Lipé", None, "dekorace", 6.0, 400, {"zed": True}),
    "tapiserie_pernstejn": ("@", "Tapiserie Pernštejnů", None, "dekorace", 6.0, 400, {"zed": True}),
    "tapiserie_svamberk": ("@", "Tapiserie Švamberků", None, "dekorace", 6.0, 400, {"zed": True}),
    "metla": ("@", "Březová metla", "naradi", "remeslo", 1.0, 3, {}),
    "vidle": ("@", "Dřevěné vidle", "naradi", "venku", 1.5, 6, {}),
    "vidle_kovane": ("@", "Kované vidle", "naradi", "venku", 2.0, 20, {}),
    "hrabe": ("@", "Hrábě", "naradi", "venku", 1.2, 5, {}),
    "kosa": ("@", "Kosa", "naradi", "venku", 2.5, 40, {}),
    "srp": ("@", "Srp", "naradi", "venku", 0.4, 12, {}),
    "cep": ("@", "Cep", "naradi", "venku", 2.0, 8, {}),
    "lopata": ("@", "Dřevěná lopata s obitím", "naradi", "remeslo", 2.0, 15, {}),
    "palice": ("@", "Palice", "naradi", "remeslo", 2.0, 8, {}),
    "pila": ("@", "Rámová pila", "naradi", "remeslo", 2.5, 45, {}),
    "teslice": ("@", "Teslice", "naradi", "remeslo", 1.5, 30, {}),
    "kleste": ("@", "Kovářské kleště", "naradi", "remeslo", 1.5, 25, {}),
    "zebrik": ("@", "Žebřík", None, "venku", 12.0, 20, {}),
    "trakar": ("@", "Dřevěný trakař", None, "venku", 25.0, 40, {}),
    "maselnice": ("@", "Máselnice", None, "remeslo", 8.0, 25, {}),
    "hmozdir": ("@", "Hmoždíř", "nadoby", "remeslo", 2.0, 10, {}),
    "zernov": ("@", "Ruční žernov", None, "remeslo", 60.0, 120, {}),
    "snop": ("@", "Snop slámy", None, "venku", 8.0, 2, {}),
    "panak_snopu": ("@", "Panák ze snopů", None, "venku", 70.0, 15, {}),
    "hranice_dreva": ("@", "Hranice dřeva", None, "venku", 300.0, 30, {}),
    "spalek_stipani": ("@", "Špalek na štípání se sekerou", None, "venku", 40.0, 20, {}),
    "koberec_zeleny": ("@", "Zelený koberec", None, "dekorace", 9.0, 160, {}),
    "koberec_velky": ("@", "Velký koberec", None, "dekorace", 22.0, 380, {}),
    "behoun": ("@", "Běhoun", None, "dekorace", 6.0, 120, {}),
}


def fetch(res="2k"):
    import urllib.request
    UA = {"User-Agent": "tvrz-blender/1.0"}

    def get_json(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return json.load(r)

    def download(url, path):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(path, "wb") as f:
            f.write(r.read())
    for key, (pid, *_rest) in KATALOG.items():
        if pid == "@":
            continue
        d = os.path.join(ROOT, pid + "_" + res)
        main = os.path.join(d, pid + ".gltf")
        if os.path.exists(main):
            continue
        files = get_json("https://api.polyhaven.com/files/" + pid)
        g = files["gltf"][res]["gltf"]
        os.makedirs(d, exist_ok=True)
        download(g["url"], main)
        for rel, inc in g.get("include", {}).items():
            path = os.path.join(d, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            download(inc["url"], path)
        print("stazeno", key, pid)


if __name__ == "__main__":
    if sys.argv[-1] == "fetch":
        fetch()


def build():
    import bpy  # noqa: E402
    from mathutils import Vector
    os.makedirs(OUT, exist_ok=True)
    hdr = os.path.join(HERE, "tex_cache", "studio_small_09_1k.hdr")
    cat = {}
    only = [a for a in sys.argv[sys.argv.index("build") + 1:]] if "build" in sys.argv else []
    for key, (pid, name, kat, stav, wt, price, props) in KATALOG.items():
        if only and key not in only:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if pid == "@":
            import vlastni
            vlastni.BUILD[key]()
            # krivky a modifikatory (bevel, solidify) na sit, aby se spojily se vsim
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.context.scene.objects:
                if o.type in ("MESH", "CURVE"):
                    o.select_set(True)
                    bpy.context.view_layer.objects.active = o
            bpy.ops.object.convert(target="MESH")
        else:
            try:
                bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, pid + "_2k", pid + ".gltf"))
            except Exception as e:      # poskozeny model: preskocit, at stavba pokracuje
                print("PRESKOCENO", key, e)
                continue
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        if "dil" in props:
            # sada vice predmetu v jednom skenu: jen vybrany dil
            meshes = [o for o in meshes if o.name.startswith(props["dil"])]
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob.parent = None
        # staticke plameny ze skenu pryc: hori jen kdyz se zapali (castice ve hre)
        fl = [i for i, m in enumerate(ob.data.materials) if m and "flame" in m.name.lower()]
        if fl:
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in fl], context="FACES")
            bm.to_mesh(ob.data)
            bm.free()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for o in list(bpy.context.scene.objects):
            if o is not ob:
                bpy.data.objects.remove(o)
        vs = [v.co for v in ob.data.vertices]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        c = (mn + mx) / 2
        ob.data.transform(__import__("mathutils").Matrix.Translation(Vector((-c.x, -c.y, -mn.z))))
        k = float(props.get("meritko", 1.0))
        if k != 1.0:
            ob.data.transform(__import__("mathutils").Matrix.Scale(k, 4))
            mn, mx = mn * k, mx * k
        ob.name = key
        ob.data.name = key
        size = mx - mn
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if tris > 40000:
            # tablet: nejvys ~40k trojuhelniku na predmet (sken svicnu ma 200k)
            dm = ob.modifiers.new("dec", "DECIMATE")
            dm.ratio = 40000 / tris
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_apply(modifier="dec")
            tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, key + ".glb"), export_format="GLB", use_selection=False,
                                  export_apply=True, export_yup=True, export_image_format="AUTO")
        # ikona: 3/4 pohled shora, studiove svetlo, pruhledne pozadi
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 48
        sc.render.resolution_x = sc.render.resolution_y = 384
        sc.render.film_transparent = True
        sc.view_settings.view_transform = "AgX"
        w = bpy.data.worlds.new("W")
        w.use_nodes = True
        env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hdr)
        w.node_tree.links.new(env.outputs["Color"], w.node_tree.nodes["Background"].inputs[0])
        w.node_tree.nodes["Background"].inputs[1].default_value = 1.1
        sc.world = w
        cam = bpy.data.cameras.new("K")
        cam.type = "ORTHO"
        co = bpy.data.objects.new("K", cam)
        sc.collection.objects.link(co)
        sc.camera = co
        tgt = Vector((0, 0, size.z / 2))
        d = Vector((math.cos(math.radians(-50)), math.sin(math.radians(-50)), 0.65)).normalized()
        co.location = tgt + d * (size.length * 3 + 2)
        co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
        # ortho meritko podle promitnuteho obrysu
        bpy.context.view_layer.update()
        inv = co.matrix_world.inverted()
        corners = [Vector((x, y, z)) for x in (-size.x / 2, size.x / 2) for y in (-size.y / 2, size.y / 2) for z in (0, size.z)]
        pc = [inv @ p for p in corners]
        cam.ortho_scale = max(max(p.x for p in pc) - min(p.x for p in pc), max(p.y for p in pc) - min(p.y for p in pc)) * 1.12
        sc.render.filepath = os.path.join(OUT, key + ".png")
        bpy.ops.render.render(write_still=True)
        cat[key] = {"nazev": name, "kat": kat, "stav": stav, "vaha": wt, "cena": price,
                    "rozmer": [round(size.x, 3), round(size.z, 3), round(size.y, 3)],
                    **{a: b for a, b in props.items() if a not in ("meritko", "dil")}}
        print("predmet", key, "%d troj." % tris, [round(v, 2) for v in size])
    p = os.path.join(OUT, "..", "predmety.json")
    old = json.load(open(p)) if os.path.exists(p) and only else {}
    old.update(cat)
    json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__" and "build" in sys.argv:
    build()


def meta():
    """Doplnit katalog (predmety.json) z uz postavenych GLB: rozmery z modelu, vlastnosti z KATALOGu."""
    import bpy  # noqa: E402
    p = os.path.join(OUT, "..", "predmety.json")
    cat = json.load(open(p)) if os.path.exists(p) else {}
    for key, (pid, name, kat, stav, wt, price, props) in KATALOG.items():
        f = os.path.join(OUT, key + ".glb")
        if key in cat or not os.path.exists(f):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=f)
        vs = [o.matrix_world @ v.co for o in bpy.context.scene.objects if o.type == "MESH" for v in o.data.vertices]
        mn = [min(v[i] for v in vs) for i in range(3)]
        mx = [max(v[i] for v in vs) for i in range(3)]
        size = [mx[i] - mn[i] for i in range(3)]
        cat[key] = {"nazev": name, "kat": kat, "stav": stav, "vaha": wt, "cena": price,
                    "rozmer": [round(size[0], 3), round(size[2], 3), round(size[1], 3)],
                    **{a: b for a, b in props.items() if a not in ("meritko", "dil")}}
        print("meta", key, cat[key]["rozmer"])
    json.dump(cat, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__" and "meta" in sys.argv:
    meta()
