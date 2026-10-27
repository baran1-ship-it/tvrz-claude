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
    "police_malovana": ("painted_wooden_shelves", "Malovaná police na zeď", None, "uvnitr", 20.0, 45, {"zed": True}),
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
    "sud_stary": ("wooden_barrels_01", "Starý sud", None, "venku", 25.0, 20, {"dil": "wooden_barrels_01_barrel01", "kont": 60}),
    "trosky_sudu": ("wooden_barrels_01", "Trosky rozbitého sudu", None, "venku", 10.0, 1, {"dil": "wooden_barrels_01_piece"}),
    "jablko": ("food_apple_01", "Jablko", "jidlo", "jidlo", 0.2, 1, {}),
    "cibule": ("yellow_onion", "Cibule", "jidlo", "jidlo", 0.2, 1, {}),

    # vlastni modely (vlastni.py)
    "kozesina": ("@", "Medvědí kožešina", "ostatni", "dekorace", 8.0, 150, {}),
    "ovci_kuze": ("@", "Ovčí kůže", "ostatni", "dekorace", 2.0, 25, {}),
    "koberec": ("@", "Koberec", None, "dekorace", 12.0, 200, {}),
    "koberec_modry": ("@", "Modrý koberec", None, "dekorace", 7.0, 140, {}),
    "polstar": ("@", "Polštář", "ostatni", "dekorace", 0.6, 12, {}),
    "polstar_zeleny": ("@", "Zelený polštář", "ostatni", "dekorace", 0.6, 10, {}),
    "stul_hodovni": ("@", "Hodovní stůl", None, "uvnitr", 90.0, 300, {}),
    "lavice_hodovni": ("@", "Hodovní lavice", None, "uvnitr", 30.0, 60, {"sed": True}),
    "stul_selsky": ("@", "Selský stůl na kozách", None, "uvnitr", 40.0, 80, {}),
    "lavice_selska": ("@", "Selská lavice", None, "uvnitr", 14.0, 25, {"sed": True}),
    "stul_pansky": ("@", "Panský hodovní stůl", None, "uvnitr", 160.0, 900, {}),
    "kreslo_panske": ("@", "Panské křeslo", None, "uvnitr", 22.0, 260, {"sed": True}),
    "drzak_louce": ("@", "Držák s loučí", None, "dekorace", 2.0, 30, {"zed": True, "louc": True}),
    "louc": ("@", "Louč", "ostatni", "dekorace", 0.6, 2, {}),
    "stit_drolerie": ("@", "Štít s trubačem (drolerie)", "zbroj", "zbrojnice", 4.0, 200, {}),
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
    "stojan_louce": ("@", "Stojan na louč", None, "venku", 9.0, 45, {"louc": True, "louc_pos": [-0.079, 1.21, 0.0]}),
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
    # Misa 27. 10. (KCD1 foto): kazda hranice jina - opřene o zed, mix kulatiny a stipanych, konce do schodu
    "drevo_dlouha_1": ("@", "Hranice dřeva", None, "venku", 400.0, 30, {"presne": True}),
    "drevo_dlouha_2": ("@", "Hranice dřeva", None, "venku", 400.0, 30, {"presne": True}),
    "drevo_vysoka_1": ("@", "Vysoká hranice dřeva", None, "venku", 500.0, 40, {"presne": True}),
    "drevo_vysoka_2": ("@", "Vysoká hranice dřeva", None, "venku", 500.0, 40, {"presne": True}),
    "drevo_hromada": ("@", "Hromada polen", None, "venku", 150.0, 15, {"presne": True}),
    "drevo_mala": ("@", "Hranička dřeva se špalkem", None, "venku", 150.0, 15, {"presne": True}),
    "drevo_kulatina": ("@", "Kulatina", None, "venku", 900.0, 60, {"presne": True}),
    "spalek_stipani": ("@", "Špalek na štípání se sekerou", None, "venku", 40.0, 20, {}),
    "bochnik": ("@", "Bochník chleba", "jidlo", "jidlo", 0.8, 2, {}),
    "pecen": ("@", "Pecen chleba", "jidlo", "jidlo", 1.5, 3, {}),
    "syr": ("@", "Sýr", "jidlo", "jidlo", 2.0, 15, {}),
    "korbel": ("@", "Dřevěný korbel", "nadoby", "jidlo", 0.4, 4, {}),
    "kosnice": ("@", "Slaměná košnice", None, "venku", 8.0, 30, {}),
    "pytel_obili": ("@", "Pytel obilí", None, "remeslo", 40.0, 20, {}),
    "pytel_mouky": ("@", "Pytel mouky", None, "remeslo", 30.0, 25, {}),
    "kupka_sena": ("@", "Kupka sena", None, "venku", 120.0, 10, {}),
    "kotlik_trojnozka": ("@", "Kotlík na trojnožce", None, "venku", 25.0, 60, {}),
    "venec_cibule": ("@", "Věnec cibule", None, "dekorace", 1.5, 3, {"zed": True}),
    "venec_cesneku": ("@", "Věnec česneku", None, "dekorace", 1.0, 3, {"zed": True}),
    "byliny": ("@", "Sušené byliny", None, "dekorace", 0.5, 4, {"zed": True}),
    "barbuta": ("@", "Barbuta", "zbroj", "zbrojnice", 2.5, 380, {}),
    "klobouk_zelezny": ("@", "Železný klobouk", "zbroj", "zbrojnice", 2.2, 220, {}),
    "kosile_kruzkova": ("@", "Kroužková košile na stojanu", None, "zbrojnice", 14.0, 900, {}),
    "kuse": ("@", "Kuše", "zbrane", "zbrojnice", 4.5, 420, {}),
    "luk_toulec": ("@", "Luk s toulcem", "zbrane", "zbrojnice", 1.8, 160, {}),
    "pult_kniha": ("@", "Pult s knihou", None, "uvnitr", 18.0, 260, {}),
    "kniha": ("@", "Kniha v kožené vazbě", "ostatni", "dekorace", 1.5, 300, {}),
    "kniha_modra": ("@", "Kniha v modré vazbě", "ostatni", "dekorace", 1.5, 300, {}),
    "kalamar": ("@", "Kalamář s brkem", "ostatni", "dekorace", 0.3, 15, {}),
    "svicen_stojaci": ("@", "Stojací svícen", None, "dekorace", 6.0, 70, {}),
    "kolebka": ("@", "Kolébka", None, "uvnitr", 12.0, 60, {}),
    "kolo_vozu": ("@", "Kolo od vozu", None, "venku", 18.0, 40, {}),
    "soudek": ("@", "Soudek na kozlíku", None, "remeslo", 15.0, 35, {"kont": 30}),
    "kureci_stehno": ("@", "Pečené kuřecí stehno", "jidlo", "jidlo", 0.3, 4, {}),
    "pecene_kure": ("@", "Pečené kuře na prkénku", "jidlo", "jidlo", 1.8, 18, {}),
    "slanina": ("@", "Bok slaniny", "jidlo", "jidlo", 1.5, 12, {}),
    "sunka": ("@", "Uzená šunka", "jidlo", "jidlo", 4.0, 40, {}),
    "klobasy": ("@", "Věnec klobás", "jidlo", "jidlo", 1.2, 14, {}),
    "susene_maso": ("@", "Sušené maso v pytlíku", "jidlo", "jidlo", 0.6, 10, {}),
    "uzena_ryba": ("@", "Uzený kapr", "jidlo", "jidlo", 1.0, 8, {}),
    "vejce_kosik": ("@", "Košík vajec", "jidlo", "jidlo", 1.2, 6, {}),
    "med": ("@", "Hrnec medu", "jidlo", "jidlo", 1.5, 20, {}),
    "kase": ("@", "Mísa kaše", "jidlo", "jidlo", 0.6, 2, {}),
    "polevka": ("@", "Mísa polévky", "jidlo", "jidlo", 0.7, 2, {}),
    "orechy": ("@", "Mísa ořechů", "jidlo", "jidlo", 0.5, 3, {}),
    "hrusky": ("@", "Mísa hrušek", "jidlo", "jidlo", 0.9, 3, {}),
    "vino_lahev": ("@", "Láhev vína", "piti", "jidlo", 1.2, 25, {}),
    "vino_dzban": ("@", "Džbán vína", "piti", "jidlo", 2.0, 20, {}),
    "demizon": ("@", "Opletený demižon", "piti", "jidlo", 12.0, 60, {}),
    "koralka": ("@", "Kořalka", "piti", "jidlo", 0.4, 15, {}),
    "pivo": ("@", "Korbel piva", "piti", "jidlo", 0.9, 3, {}),
    "voda_mech": ("@", "Měch s vodou", "piti", "jidlo", 1.5, 6, {}),
    "bozi_muka": ("@", "Boží muka", None, "venku", 900.0, 400, {}),
    "kad": ("@", "Káď s vodou", None, "venku", 80.0, 60, {"myti": True}),
    "zeli": ("@", "Hlávka zelí", "jidlo", "jidlo", 1.5, 2, {}),
    "mrkev": ("@", "Svazek mrkve", "jidlo", "jidlo", 0.6, 2, {}),
    "vodnice": ("@", "Vodnice", "jidlo", "jidlo", 0.8, 2, {}),
    "kren": ("@", "Křen", "jidlo", "jidlo", 0.4, 3, {}),
    "hriby": ("@", "Hřiby", "jidlo", "jidlo", 0.4, 4, {}),
    "bedly": ("@", "Bedly", "jidlo", "jidlo", 0.3, 3, {}),
    "houska": ("@", "Houska", "jidlo", "jidlo", 0.15, 1, {}),
    "hovezi": ("@", "Syrové hovězí", "jidlo", "jidlo", 1.6, 10, {}),
    "kanci_kyta": ("@", "Kančí kýta", "jidlo", "jidlo", 5.0, 30, {}),
    "kanci_pecene": ("@", "Pečená kančí kýta", "jidlo", "jidlo", 4.5, 45, {}),
    "raci": ("@", "Vaření raci", "jidlo", "jidlo", 0.8, 12, {}),
    "medovina": ("@", "Medovina", "piti", "jidlo", 1.6, 30, {}),
    "skorice": ("@", "Svazek skořice", "jidlo", "jidlo", 0.1, 25, {}),
    "koberec_zeleny": ("@", "Zelený koberec", None, "dekorace", 9.0, 160, {}),
    "koberec_velky": ("@", "Velký koberec", None, "dekorace", 22.0, 380, {}),
    "behoun": ("@", "Běhoun", None, "dekorace", 6.0, 120, {}),
}

# ---- modely od hrace (soukromy repozitar tvrz-modely, stazene do EXT): "ext:<soubor.glb>"
# vlastnosti: vyska / max = cilova vyska / nejdelsi rozmer v m, dil_presne = jmena objektu, troj = strop trojuhelniku,
# tex = nejvetsi strana textury
EXT = os.environ.get("TVRZ_EXT", "/home/user/tvrz-modely/stazene")
KIT = "ext:medieval_tavern_kit.glb"          # AI skeny: kazdy predmet rozdeleny na 2-4 kusy, spojit vsechny
STAN = "ext:medieval_market_tent_prop_02.glb"
# lom (radce 16:20, Misa 0.70 "lom podle obrazku, at je fakt vybaveny"): Poly Haven CC0
KATALOG.update({
    "zebrinak": ("@", "Žebřiňák", None, "venku", 300.0, 600, {"troj": 16000}),
    "pristresek_plachta": ("@", "Plátěný přístřešek", None, "venku", 60.0, 80, {"pruchozi": True, "troj": 10000}),
    "pristresek_maly": ("@", "Malý plátěný přístřešek", None, "venku", 40.0, 60, {"pruchozi": True, "troj": 8000}),
    "stan_jehlan": ("@", "Jehlanový stan", None, "venku", 50.0, 70, {"pruchozi": True}),
    # trziste pred vsi (Misa 24. 10.: modely z Disku) a jejich veci do katalogu stavitele
    "stanek_trzni": ("ext:village_market_stall.glb", "Tržní stánek", None, "venku", 80.0, 60, {"vyska": 2.0, "vyprazdnit": [0.375, 0.6], "troj": 8000}),
    "stan_velky": ("ext:medieval_tent.glb", "Velký plátěný stan", None, "venku", 90.0, 120, {"max": 9.0, "troj": 100000, "tex": 1024, "pruchozi": True}),
    "stan_trzni": ("ext:medieval_market_tent_prop_01.glb", "Pruhovaný tržní stan", None, "venku", 70.0, 100,
                   {"dil_presne": ["tent_back.001_tent_back_0", "tent_front.001_tent_front_0", "tent_sides.001_tent_sides_0",
                                   "tent_top.001_tent_top_0", "Pole.001_pole_0"], "troj": 30000, "pruchozi": True, "bez_barvy_vrcholu": True}),
    "vedro_drevene": ("ext:medieval_market_tent_prop_01.glb", "Dřevěné vědro", "nadoby", "remeslo", 2.0, 4, {"dil_presne": ["wooden_bucket_01.005_wooden_bucket_01_0"], "troj": 1500}),
    "necky": ("ext:medieval_market_tent_prop_01.glb", "Dřevěné necky", "nadoby", "remeslo", 6.0, 8,
              {"dil_presne": ["wooden_bucket_02.001_wooden_bucket_02_0", "wooden_bucket_02_handle_01.001_wooden_bucket_02_0", "wooden_bucket_02_handle_02.001_wooden_bucket_02_0"], "troj": 2000}),
    "lisa_zelenina": ("ext:medieval_market_tent_prop_01.glb", "Lísa se zeleninou", None, "venku", 6.0, 10, {"dil_presne": ["vegetable_box_01.005_vegetable_box_01_0"], "troj": 2000}),
    "bedna_zelenina": ("ext:medieval_market_tent_prop_01.glb", "Bedna se zeleninou", None, "venku", 12.0, 14, {"dil_presne": ["vegetable_box_02.004_vegetable_box_02_0"], "troj": 2500}),
    "bedna_velka_zelenina": ("ext:medieval_market_tent_prop_01.glb", "Velká bedna se zeleninou", None, "venku", 20.0, 18, {"dil_presne": ["vegetable_box_03.006_vegetable_box_03_0"], "troj": 2500}),
    "bedna_trzni": ("ext:medieval_market_tent_prop_01.glb", "Tržní bedna", None, "venku", 10.0, 6, {"dil_presne": ["Crate.003_Crate_0"], "troj": 1500}),
    "bedna_trzni_2": ("ext:medieval_market_tent_prop_01.glb", "Tržní bedna vysoká", None, "venku", 10.0, 6, {"dil_presne": ["Crate_02.008_Crate_02_0"], "troj": 1500}),
    "bedna_trzni_3": ("ext:medieval_market_tent_prop_01.glb", "Tržní bedna nízká", None, "venku", 9.0, 6, {"dil_presne": ["Crate_03.007_Crate_03_0"], "troj": 1500}),
    "stolicka_trzni": ("ext:medieval_market_tent_prop_01.glb", "Trojnohá stolička", None, "uvnitr", 3.0, 5, {"dil_presne": ["stool.006_stool_0"], "troj": 2000, "sed": True}),
    "bochnik": ("ext:medieval_market_tent_prop_01.glb", "Bochník chleba", "jidlo", "dekorace", 0.8, 2, {"dil_presne": ["Bread.016_bread_0"], "troj": 1200}),
    "veka": ("ext:medieval_market_tent_prop_01.glb", "Pecen chleba", "jidlo", "dekorace", 0.5, 2, {"dil_presne": ["bread_02.013_bread_02_0"]}),
    "hrnec_hlineny": ("ext:medieval_market_tent_prop_01.glb", "Hliněný hrnec", "nadoby", "dekorace", 1.5, 4, {"dil_presne": ["Pot_01.006_pot_01_0"], "troj": 1500}),
    "hrnec_velky": ("ext:medieval_market_tent_prop_01.glb", "Velký hliněný hrnec", "nadoby", "dekorace", 2.5, 6, {"dil_presne": ["Pot_02.013_pot_02_0"], "troj": 1500}),
    "koberec_trzni": ("ext:medieval_market_tent_prop_01.glb", "Tkaný koberec", None, "uvnitr", 6.0, 40, {"dil_presne": ["Rug.001_rug_0"], "troj": 1500}),
    "stul_trzni": ("ext:medieval_market_tent_prop_01.glb", "Tržní stůl", None, "venku", 25.0, 30, {"dil_presne": ["table.002_table_0"], "troj": 3000}),
    "pult_bedny": ("ext:medieval_market_tent_prop_01.glb", "Pult z beden", None, "venku", 30.0, 20, {"dil_presne": ["Box_table.001_box_table_0"]}),
    "vesak_kuze": ("ext:medieval_market_tent_prop_01.glb", "Věšák s kůžemi", None, "remeslo", 12.0, 60,
                   {"dil_presne": ["wooden_stick.001_leather_hanger_0", "leather.001_leather_hanger_0"], "troj": 4000}),
    "okurka": ("ext:medieval_market_tent_prop_01.glb", "Okurka", "jidlo", "dekorace", 0.2, 1, {"dil_presne": ["cucumber.010_vegetables_0"], "troj": 600}),
    "zeli_hlavka": ("ext:cabbage.glb", "Hlávka zelí", "jidlo", "dekorace", 1.5, 2, {"max": 0.3, "troj": 1500}),
    "salat": ("ext:vegetable.glb", "Hlávka salátu", "jidlo", "dekorace", 0.3, 1, {"max": 0.24, "troj": 5000}),
    "kul_cedule": ("@", "Kůl s cedulí", None, "venku", 30.0, 15, {"troj": 4000}),
    # zem0: kuly bradla zarazene 0,3 m do zeme - bez toho katalog zvedl model o 0,3 m (Misa 0.78 "napajedlo levituje")
    "koryto_kone": ("@", "Koryto a bradlo pro koně", None, "venku", 80.0, 25, {"troj": 6000, "zem0": True}),
    # zahradky vsi (Misa 25. 10., KCD): vyvyseny zahon s proutenym lemem, rostouci zelenina; proutěny plutek
    "zahon_zeli": ("@", "Záhon zelí", None, "venku", 300.0, 8, {"troj": 9000}),
    "zahon_salat": ("@", "Záhon salátu", None, "venku", 300.0, 6, {"troj": 9000}),
    "zahon_cibule": ("@", "Záhon cibule", None, "venku", 300.0, 6, {"troj": 9000}),
    "zahon_mrkev": ("@", "Záhon mrkve", None, "venku", 300.0, 6, {"troj": 9000}),
    "zahon_prazdny": ("@", "Zrytý záhon", None, "venku", 300.0, 2, {"troj": 5000}),
    "plutek": ("@", "Proutěný plůtek", None, "venku", 20.0, 3, {"troj": 3000}),
    # Misa 25. 10. "na disku by mohly byt plutky z vetvi": withe_fence.glb (Disk Modely) - pleteny z prutu, 2 m
    "plutek_vetve": ("ext:withe_fence.glb", "Plůtek z větví", None, "venku", 20.0, 3, {"max": 2.0, "troj": 1000, "tex": 1024}),
    # havrani erb (obrazky/erb): stit nad branou a v sini, prapor na vezi nad branou
    "stit_havran": ("@", "Štít s havraním erbem", None, "zed", 6.0, 80, {"troj": 1500}),
    "korouhev_havran": ("@", "Prapor rodu z Havraní", None, "venku", 8.0, 60, {"troj": 3000}),
    "leseni_lom": ("@", "Lešení z kulatiny", None, "venku", 400.0, 60, {"troj": 26000, "presne": True, "tex": 1024, "zem0": True}),
    "leseni_lom_2": ("@", "Vysoké lešení z kulatiny", None, "venku", 600.0, 90, {"troj": 40000, "presne": True, "tex": 1024, "zem0": True}),
    "leseni_lom_3": ("@", "Nízké lešení z kulatiny", None, "venku", 300.0, 45, {"troj": 20000, "presne": True, "tex": 1024, "zem0": True}),
    "jerab_slapaci": ("@", "Šlapací jeřáb", None, "venku", 1500.0, 400, {"troj": 30000, "presne": True, "tex": 1024, "zem0": True}),
    "kvadr_hruby_1": ("@", "Otesaný kvádr", None, "venku", 700.0, 40, {}),
    "kvadr_hruby_2": ("@", "Velký otesaný kvádr", None, "venku", 1200.0, 60, {}),
    "kvadr_hruby_3": ("@", "Malý otesaný kvádr", None, "venku", 350.0, 25, {}),
    "perlik": ("sledgehammer_01", "Perlík", "naradi", "remeslo", 5.0, 30, {}),
    "ohniste_kamenne": ("stone_fire_pit", "Ohniště z kamenů", None, "venku", 80.0, 0, {}),
    "kladivo_kamenicke": ("wooden_hammer_01", "Kamenická palice", "naradi", "remeslo", 1.5, 8, {}),
})
KATALOG.update({
    "kovadlina_spalek": ("ext:asset02_medieval_anvil.glb", "Kovadlina na špalku", None, "remeslo", 120.0, 300, {"vyska": 0.85}),
    "mech": ("ext:medieval_bellow.glb", "Kovářský měch", None, "remeslo", 40.0, 80, {"vyska": 1.5}),
    "brus": ("ext:medieval_grindstone.glb", "Brus na šlapání", None, "remeslo", 50.0, 60, {"vyska": 1.0}),
    "naradi_kovar": ("ext:medieval_tools_set.glb", "Kovářské nářadí na stěně", None, "remeslo", 15.0, 90, {"vyska": 1.15, "zed": True}),
    "bascinet": ("ext:medieval_bascinet_with_visor.glb", "Bascinet s hledím", "zbroj", "zbrojnice", 3.0, 400, {"vyska": 0.42}),
    "mec_jednoruc": ("ext:medieval_sword.glb", "Jednoruční meč", "zbrane", "zbrojnice", 1.3, 250, {"max": 1.0}),
    "kladivo_bodec": ("ext:medieval_war_hammer.glb", "Válečné kladivo s bodcem", "zbrane", "zbrojnice", 2.0, 150, {"max": 0.95}),
    "truhla_velka": ("ext:medieval_chest.glb", "Velká okovaná truhla", None, "uvnitr", 40.0, 200, {"max": 1.15, "kont": 150}),
    "svicen_venec": ("ext:medieval_candelabra_free_download.glb", "Stojací svícen s věncem", None, "dekorace", 15.0, 120, {"vyska": 1.9}),
    "kreslo_vysoke": ("ext:medieval_chair.glb", "Vysoké řezbované křeslo", None, "uvnitr", 14.0, 120, {"vyska": 1.45, "sed": True}),
    "vahy": ("ext:medieval_balance_scales.glb", "Kupecké váhy", None, "dekorace", 4.0, 80, {"vyska": 0.55}),
    "pult_psaci": ("ext:medieval_writing_table.glb", "Psací pult", None, "uvnitr", 30.0, 90, {"vyska": 1.15}),
    "stul_kozy_dub": ("ext:mesa_medieval.glb", "Dubový stůl na kozách", None, "uvnitr", 40.0, 70, {"vyska": 0.76}),
    "stul_masivni": ("ext:medieval_table_free.glb", "Masivní stůl", None, "uvnitr", 60.0, 90, {"vyska": 0.78}),
    "police_prkno": ("ext:medieval_shelf.glb", "Prkenná police", None, "dekorace", 3.0, 8, {"max": 1.0, "zed": True}),
    "korbel_okovany": ("ext:medieval_tankard.glb", "Okovaný korbel", "nadoby", "dekorace", 0.6, 6, {"vyska": 0.19}),
    "noze_lzice": ("ext:medieval_cutlery.glb", "Nože a lžíce", "naradi", "dekorace", 0.3, 6, {"max": 0.34}),
    "kniha_otevrena": ("ext:medieval_open_book_2.glb", "Otevřená kniha", None, "dekorace", 2.0, 300, {"max": 0.48}),
    "lis": ("ext:medieval_wine_press_free.glb", "Lis na víno a ovoce", None, "remeslo", 250.0, 400, {"vyska": 2.1}),
    "lustr": ("ext:medieval_chandelier.glb", "Kruhový lustr", None, "dekorace", 20.0, 200, {"vyska": 0.9}),
    # z kitu krcmy (AI skeny, kazdy kus jen jedna nizsi uroven detailu)
    "jeleni_trofej": (KIT, "Jelení trofej", None, "dekorace", 8.0, 150, {"troj": 25000, "dil_presne": ["Deer trophy.001_Material.001_0", "Deer trophy.001_Material.001_0.001"], "max": 1.3, "zed": True}),
    "lucerna_kovana": (KIT, "Kovaná lucerna", "ostatni", "dekorace", 1.5, 40, {"troj": 25000, "dil_presne": ["Lantern_Material.009_0", "Lantern_Material.009_0.001"], "vyska": 0.45}),
    "dzban_kamenny": (KIT, "Cínová konvice", "nadoby", "dekorace", 1.5, 8, {"troj": 25000, "dil_presne": ["Medieval Jug_Material.002_0", "Medieval Jug_Material.002_0.001"], "vyska": 0.3}),
    "pohar_drevo": (KIT, "Cínový korbel", "nadoby", "dekorace", 0.4, 4, {"troj": 25000, "dil_presne": ["Drinking mug_Material.010_0", "Drinking mug_Material.010_0.001", "Drinking mug_Material.010_0.002"], "vyska": 0.16}),
    "svicky": (KIT, "Svíčky na podnosu", None, "dekorace", 0.8, 10, {"troj": 25000, "dil_presne": ["Candle set.002_tripo_material_dfecb981-9b1d-4827-b408-f07e863f2068_0", "Candle set.002_tripo_material_dfecb981-9b1d-4827-b408-f07e863f2068_0.001", "Candle set.002_tripo_material_dfecb981-9b1d-4827-b408-f07e863f2068_0.002", "Candle set.002_tripo_material_dfecb981-9b1d-4827-b408-f07e863f2068_0.003"], "vyska": 0.3}),
    "svice_velke": (KIT, "Velké svíce", None, "dekorace", 3.0, 25, {"troj": 25000, "dil_presne": ["Candle set_tripo_material_e0ad4567-c9e8-4916-aa6d-b4bf28409834_0", "Candle set_tripo_material_e0ad4567-c9e8-4916-aa6d-b4bf28409834_0.001", "Candle set_tripo_material_e0ad4567-c9e8-4916-aa6d-b4bf28409834_0.002"], "vyska": 0.55}),
    "zidle_operadlo": (KIT, "Židle s opěradlem", None, "uvnitr", 6.0, 20, {"troj": 25000, "dil_presne": ["Wooden Chair_Material.003_0", "Wooden Chair_Material.003_0.001"], "vyska": 1.05, "sed": True}),
    "zidle_podrucky": (KIT, "Židle s područkami", None, "uvnitr", 7.0, 25, {"troj": 25000, "dil_presne": ["Wooden chair.001_Material.016_0", "Wooden chair.001_Material.016_0.001"], "vyska": 1.05, "sed": True}),
    "zidle_nizka": (KIT, "Nízká židle", None, "uvnitr", 6.0, 18, {"troj": 25000, "dil_presne": ["Wooden chair_Material.015_0", "Wooden chair_Material.015_0.001"], "vyska": 1.0, "sed": True}),
    "kredenc": (KIT, "Kredenc", None, "uvnitr", 50.0, 120, {"troj": 25000, "dil_presne": ["Wooden cabinet_Material.005_0", "Wooden cabinet_Material.005_0.001", "Wooden cabinet_Material.005_0.002"], "vyska": 1.6, "kont": 80}),
    "almara": (KIT, "Almara", None, "uvnitr", 70.0, 140, {"troj": 25000, "dil_presne": ["Wooden closet_Material.017_0", "Wooden closet_Material.017_0.001"], "vyska": 2.0, "kont": 120}),
    "stul_hospoda": (KIT, "Hospodský stůl", None, "uvnitr", 35.0, 60, {"troj": 25000, "dil_presne": ["Wooden table_Material.006_0", "Wooden table_Material.006_0.001"], "vyska": 0.78}),
    # ze stanu
    "kos_jablka": (STAN, "Košík s jablky", "jidlo", "dekorace", 2.0, 6, {"dil_presne": ["Tent_02_top.001_fruit_basket_0", "Tent_02_top.001_apple_0"], "meritko": 1.0}),
    "bedna_kupecka": (STAN, "Kupecká bedna", None, "venku", 12.0, 15, {"dil_presne": ["Tent_02_top.001_Crate.002_0"], "kont": 60}),
    "pytel_kupecky": (STAN, "Plný pytel", None, "venku", 30.0, 10, {"dil_presne": ["Tent_02_top.001_sand_bag_0"]}),
    # stavby (jen pevne ve svete, ne v nabidce staveni)
    "stan_kupce": (STAN, "Kupecký stan", None, None, 150.0, 500, {"troj": 90000, "tex": 2048, "pevne_stavba": True, "zem0": True}),
    # byliny ke sberu (sber.gd): utrzena rostlina z Poly Haven, jen jedna varianta
    "kopriva": ("ph:nettle_plant", "Kopřiva", "byliny", "jidlo", 0.05, 1, {"dil_presne": ["nettle_plant_medium_a_LOD0"], "vyska": 0.3}),
    "vlastovicnik": ("ph:celandine_01", "Vlaštovičník", "byliny", "jidlo", 0.04, 2, {"dil_presne": ["celandine_01_c_LOD0"], "vyska": 0.16}),
    "barvinek": ("ph:periwinkle_plant", "Barvínek", "byliny", "jidlo", 0.04, 2, {"dil_presne": ["periwinkle_plant_03_LOD0"], "vyska": 0.22}),
    # ruiny (veze CC BY - autor v titulcich)
    "ruina_vez_1": ("ext:pack_of_old_towers_in_ruins.glb", "Zřícená věž", None, None, 0.0, 0, {"dil_presne": ["Object_2"], "max": 11.3, "troj": 25000, "tex": 2048, "pevne_stavba": True}),
    "ruina_vez_2": ("ext:pack_of_old_towers_in_ruins.glb", "Rozpadlá věž", None, None, 0.0, 0, {"dil_presne": ["Object_4"], "max": 8.2, "troj": 20000, "tex": 2048, "pevne_stavba": True}),
    "hostinec": ("ext:medieval_tavern_interior.glb", "Zájezdní hostinec", None, None, 0.0, 0, {"troj": 12000, "tex": 1024, "pevne_stavba": True, "zem0": True, "uprava": "hostinec", "sketchup": True}),
})



def fetch(res="2k"):
    import urllib.request
    UA = {"User-Agent": "tvrz-blender/1.0"}

    def get_json(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return json.load(r)

    def download(url, path):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(path, "wb") as f:
            f.write(r.read())
    jen = sys.argv[sys.argv.index("fetch") + 1:] if "fetch" in sys.argv else []
    for key, (pid, *_rest) in KATALOG.items():
        if pid == "@" or (jen and key not in jen):
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
    if "fetch" in sys.argv:
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
            vlastni.DILY.clear()
            vlastni.BUILD[key]()
            # krivky a modifikatory (bevel, solidify) na sit, aby se spojily se vsim
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.context.scene.objects:
                if o.type in ("MESH", "CURVE"):
                    o.select_set(True)
                    bpy.context.view_layer.objects.active = o
            bpy.ops.object.convert(target="MESH")
            # Misa 24. 10.: "nic v te dobe nebylo uplne rovne a dokonale" - kazdy dil vlastniho modelu mirne nakloneny
            # (+-0,8 st., at se spoje nerozejdou) a povrch zvlneny sumem (az 1,5 cm, u tenkych dilu umerne tloustce); latky a provazy jen trochu
            if not props.get("presne"):
                import random as _rnd
                from mathutils import noise as _noise, Euler as _Euler
                _R = _rnd.Random(hash(key) & 0xffff)
                for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
                    dims = sorted(o.dimensions)
                    if dims[0] <= 0.0:
                        continue
                    # hlina zahonu: sum "oteseni" (9/m na siti po 8 cm) delal na hladkem stinovani sachovnici
                    # (Misa 0.83 zahony "divna textura") - hlina jako latka, jen bez oteseni
                    latka = o.name.startswith(("plachta", "latka", "hlina")) or dims[1] <= 0.02
                    # Misa: "hlavne opracovani - nebylo do hladka, bylo to hrube otesane": dil rozdelit na plosky ~10 cm
                    # a povrch otesat - velke nerovnosti (1-1,5 cm) a stopy sekery/spicaku (plosky 6-8 cm, 4-6 mm)
                    if not latka and len(o.data.polygons) < 400 and dims[2] > 0.15:
                        # deleni jen podel delky dilu (kul, tram, prkno): rezy po ~15 cm, obvod zustava
                        import bmesh as _bm
                        b_ = _bm.new()
                        b_.from_mesh(o.data)
                        loc = [v.co.copy() for v in b_.verts]
                        ax = max(range(3), key=lambda i_: max(c[i_] for c in loc) - min(c[i_] for c in loc))
                        hrany = [e for e in b_.edges if (e.verts[1].co - e.verts[0].co).length > 0.05
                                 and abs((e.verts[1].co - e.verts[0].co).normalized()[ax]) > 0.9]
                        delka = max(c[ax] for c in loc) - min(c[ax] for c in loc)
                        cuts = max(1, min(14, int(delka / 0.15)))
                        if hrany:
                            _bm.ops.subdivide_edges(b_, edges=hrany, cuts=cuts, use_grid_fill=False)
                        b_.to_mesh(o.data)
                        b_.free()
                    amp = 0.0 if latka else min(0.02, dims[0] * 0.14)
                    amp_h = 0.0 if latka else min(0.014, dims[0] * 0.1)
                    off = Vector((_R.uniform(0, 99), _R.uniform(0, 99), _R.uniform(0, 99)))
                    mw = o.matrix_world.copy()
                    o.data.update()
                    for v in o.data.vertices:
                        w = mw @ v.co
                        n_ = v.normal
                        teseni = _noise.noise(w * 9.0 + off) * amp_h - abs(_noise.noise(w * 4.0 + off * 2.0)) * amp_h
                        v.co += Vector((_noise.noise(w * 3.0 + off), _noise.noise(w * 3.0 + off + Vector((17, 0, 0))),
                                        _noise.noise(w * 3.0 + off + Vector((0, 31, 0))))) * amp + n_ * teseni
                    if not latka:
                        for pl in o.data.polygons:
                            pl.use_smooth = False                     # otesane plosky, ne hladky valec
                    if latka and dims[1] > 0.02:
                        for v in o.data.vertices:
                            w = mw @ v.co
                            v.co += Vector((0, 0, _noise.noise(w * 5.0 + off))) * 0.01
                    if dims[2] > 0.05 and not o.name.startswith(("plachta", "latka")):
                        piv = o.matrix_world.to_translation()
                        rot = _Euler((_R.uniform(-0.014, 0.014), _R.uniform(-0.014, 0.014), _R.uniform(-0.02, 0.02))).to_matrix().to_4x4()
                        o.matrix_world = __import__("mathutils").Matrix.Translation(piv) @ rot @ __import__("mathutils").Matrix.Translation(-piv) @ o.matrix_world
        elif pid.startswith("ph:"):
            # rostliny z Poly Haven (1k, uz stazene pro krajinu): tex_cache/models/<id>/<id>.gltf
            bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "tex_cache", "models", pid[3:], pid[3:] + ".gltf"))
        elif pid.startswith("ext:"):
            try:
                bpy.ops.import_scene.gltf(filepath=os.path.join(EXT, pid[4:]))
            except Exception as e:
                print("PRESKOCENO", key, e)
                continue
        else:
            try:
                bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, pid + "_2k", pid + ".gltf"))
            except Exception as e:      # poskozeny model: preskocit, at stavba pokracuje
                print("PRESKOCENO", key, e)
                continue
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        # pohyblive dily vlastnich modelu (jerab: kolo, kladnice, lano) zvlast: <id>_<dil>.glb s pocatkem v pivotu
        dily = {}
        if pid == "@":
            import vlastni
            for d_, (piv, udaje) in vlastni.DILY.items():
                ds = [o for o in meshes if o.get("dil") == d_]
                if ds:
                    dily[d_] = (ds, piv, udaje)
            meshes = [o for o in meshes if "dil" not in o]
        if "dil_presne" in props:
            meshes = [o for o in meshes if o.name in props["dil_presne"]]
            if not meshes:
                print("PRESKOCENO", key, "dil nenalezen")
                continue
        elif pid.startswith("ext:") and not props.get("pevne_stavba"):
            meshes = [o for o in meshes if "flame" not in o.name.lower()]
        if "dil" in props:
            # sada vice predmetu v jednom skenu: jen vybrany dil
            dil = props["dil"] if isinstance(props["dil"], (list, tuple)) else [props["dil"]]
            meshes = [o for o in meshes if any(o.name.startswith(d) for d in dil)]
        # zachovat svetovou transformaci (Sketchfab ma nadrazeny uzel pootoceny o -90 st. a zmenseny)
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
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
        if props.get("bez_barvy_vrcholu"):
            # strecha trzniho stanu: zakladni barva = textura x barva vrcholu (cerna) -> cerna strecha
            for ca in list(ob.data.color_attributes):
                ob.data.color_attributes.remove(ca)
            for m in ob.data.materials:
                if m and m.use_nodes:
                    nt = m.node_tree
                    bs = nt.nodes.get("Principled BSDF")
                    if bs and bs.inputs["Base Color"].links and bs.inputs["Base Color"].links[0].from_node.type == "MIX":
                        mx = bs.inputs["Base Color"].links[0].from_node
                        tx = [l.from_node for i in mx.inputs for l in i.links if l.from_node.type == "TEX_IMAGE"]
                        if tx:
                            nt.links.new(tx[0].outputs["Color"], bs.inputs["Base Color"])
                    for nd in list(nt.nodes):
                        if nd.type in ("VERTEX_COLOR", "ATTRIBUTE"):
                            nt.nodes.remove(nd)
        if props.get("vyprazdnit"):
            # Misa: "stanek - vyndat veci z pultu, at je prazdny": sken je jedna sit (misky srostle s deskou) ->
            # plochy nad deskou pultu uvnitr pudorysu pryc; deska = nejnizsi souvisla vodorovna vrstva v pasu 40-60 %
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            zs = [v.co.z for v in bm.verts]
            z0, z1 = min(zs), max(zs)
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            hx = (max(xs) - min(xs)) / 2 - 0.12
            hy = (max(ys) - min(ys)) / 2 - 0.12
            cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
            za, zb = z0 + (z1 - z0) * float(props["vyprazdnit"][0]), z0 + (z1 - z0) * float(props["vyprazdnit"][1])
            pryc = [f for f in bm.faces if za < f.calc_center_median().z < zb
                    and abs(f.calc_center_median().x - cx) < hx and abs(f.calc_center_median().y - cy) < hy]
            bmesh.ops.delete(bm, geom=pryc, context="FACES")
            bm.to_mesh(ob.data)
            bm.free()
            print("vyprazdneno", key, len(pryc), "ploch")
            # deska pultu z prken (misky byly zapustene do desky - zbyla by dira)
            import vlastni, random as _r
            R_ = _r.Random(7)
            dub = vlastni._wood_mat("pult_prkna", "tram", (0.55, 0.42, 0.3))
            zd = z0 + (z1 - z0) * 0.37
            x = min(xs) + 0.1
            prkna = []
            while x < max(xs) - 0.12:
                w = R_.uniform(0.2, 0.28)
                prkna.append(vlastni._box((x + w / 2, cy, zd), (w - 0.012, hy * 2 + 0.16, 0.035), dub, bevel=0.004))
                x += w
            bpy.ops.object.select_all(action="DESELECT")
            for o_ in prkna + [ob]:
                o_.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.join()
            ob = bpy.context.view_layer.objects.active
        tmax_ = int(props.get("tex", 0))
        for img in bpy.data.images if tmax_ else []:
            if img.size[0] > tmax_ or img.size[1] > tmax_:
                f_ = tmax_ / max(img.size[0], img.size[1])
                img.scale(max(1, int(img.size[0] * f_)), max(1, int(img.size[1] * f_)))
        for d_, (ds, piv, udaje) in dily.items():
            bpy.ops.object.select_all(action="DESELECT")
            for o in ds:
                o.select_set(True)
            bpy.context.view_layer.objects.active = ds[0]
            if len(ds) > 1:
                bpy.ops.object.join()
            od = bpy.context.view_layer.objects.active
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            od.data.transform(__import__("mathutils").Matrix.Translation(-piv))
            od.name = key + "_" + d_
            bpy.ops.object.select_all(action="DESELECT")
            od.select_set(True)
            bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, key + "_" + d_ + ".glb"), export_format="GLB", use_selection=True,
                                      export_apply=True, export_yup=True, export_image_format="AUTO")
            print("dil", key + "_" + d_, sum(len(p_.vertices) - 2 for p_ in od.data.polygons), "troj.")
        for o in list(bpy.context.scene.objects):
            if o is not ob:
                bpy.data.objects.remove(o)
        if props.get("uprava") == "hostinec":
            import hostinec
            hostinec.uprav_model(ob)
        kol = None
        if props.get("sketchup"):
            # kolize z puvodni site (pred importem byl hostinec pruchozi): kopie se exportuje jako <id>_kolize,
            # hra z ni udela kolizi a nekresli ji; _import_sketchup meni jen viditelny model
            kol = ob.copy()
            kol.data = ob.data.copy()
            kol.name = key + "_kolize"
            kol.data.name = key + "_kolize"
            bpy.context.scene.collection.objects.link(kol)
            kol.hide_render = True
            import nove
            nove._import_sketchup(ob, tris_max=int(props.get("troj", 4000)), tex_max=int(props.get("tex", 1024)),
                                  stavba=bool(props.get("pevne_stavba")))
        vs = [v.co for v in ob.data.vertices]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        c = (mn + mx) / 2
        # stavby: zem v z = 0 (koliky stanu pod zemi model nezvedaji)
        for o_ in [ob] + ([kol] if kol else []):
            o_.data.transform(__import__("mathutils").Matrix.Translation(Vector((-c.x, -c.y, 0.0 if props.get("zem0") else -mn.z))))
        if props.get("pevne_stavba"):
            print("stred stavby", key, round(c.x, 3), round(c.y, 3))
        k = float(props.get("meritko", 1.0))
        if "vyska" in props:
            k = float(props["vyska"]) / max(1e-6, mx.z - mn.z)
        elif "max" in props:
            k = float(props["max"]) / max(1e-6, max(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z))
        if k != 1.0:
            for o_ in [ob] + ([kol] if kol else []):
                o_.data.transform(__import__("mathutils").Matrix.Scale(k, 4))
            mn, mx = mn * k, mx * k
        ob.name = key
        ob.data.name = key
        size = mx - mn
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        lim = int(props.get("troj", 15000 if pid.startswith("ext:") else 40000))
        if tris > lim:
            # tablet: nejvys ~40k trojuhelniku na predmet (sken svicnu ma 200k), modely hrace 15k
            dm = ob.modifiers.new("dec", "DECIMATE")
            dm.ratio = lim / tris
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_apply(modifier="dec")
            tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if pid.startswith("ext:") or "tex" in props:
            # textury zmensit (tablet): drobnosti 1k, stavby 2k
            tmax = int(props.get("tex", 1024))
            for img in bpy.data.images:
                if img.size[0] > tmax or img.size[1] > tmax:
                    f_ = tmax / max(img.size[0], img.size[1])
                    img.scale(max(1, int(img.size[0] * f_)), max(1, int(img.size[1] * f_)))
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
        if dily:
            # pivoty v souradnicich modelu ve hre (Y nahoru, z = -y Blenderu, posun jako u modelu)
            def _g(v):
                return [round(v[0] - c.x, 3), round(v[2] - (0.0 if props.get("zem0") else mn.z), 3), round(-(v[1] - c.y), 3)]
            props = dict(props)
            def _u(a_, v_):
                if a_ in ("horni", "mista"):
                    return [_g(b_) for b_ in v_]
                if a_ == "zebriky":                  # [pata, vrchol, smer, nastup, sestup]; smer je vektor, ne bod
                    return [{"pata": _g(z_[0]), "vrchol": _g(z_[1]), "smer": [z_[2][0], z_[2][2], -z_[2][1]],
                             "nastup": _g(z_[3]), "sestup": _g(z_[4])} for z_ in v_]
                return v_
            props["dily"] = {d_: {"pivot": _g(piv), **{a_: _u(a_, v_) for a_, v_ in udaje.items()}}
                             for d_, (ds, piv, udaje) in dily.items()}
        cat[key] = {"nazev": name, "kat": kat, "stav": stav, "vaha": wt, "cena": price,
                    "rozmer": [round(size.x, 3), round(size.z, 3), round(size.y, 3)],
                    **{a: b for a, b in props.items() if a not in ("meritko", "dil", "dil_presne", "vyska", "max", "troj", "tex", "zem0", "uprava", "vyprazdnit", "bez_barvy_vrcholu")}}
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
