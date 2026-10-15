"""Zkopíruje hotové .glb do repa a dopíše řádky do seznam.txt (rozměry a trojúhelníky přímo z .glb).
Spuštění: python3 make_seznam.py <cílová_složka> <jmeno1> [jmeno2 ...]
"""
import sys, os, shutil
import bpy
from mathutils import Vector

DST = sys.argv[1]; NAMES = sys.argv[2:]
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")

INFO = {   # předpona -> (český název, kategorie, poznámka)
    "skala_jehla": ("Skalní věž – jehla", "skaly", "pískovcová jehla skalního města (Adršpach/Prachov): vodorovné vrstvy, svislé pukliny, voštiny, černé stékance, mech a lišejník na severu (+Z), borovice a tráva nahoře; pivot = úroveň terénu, spodek 1 m pod zem; 2K textury (barva, normal, ORM)"),
    "skala_vez": ("Skalní věž", "skaly", "široká pískovcová věž, ploché temeno s borovicí; pivot = terén, spodek 1 m pod zem; 2K textury"),
    "skala_hlava": ("Skalní věž s hlavou", "skaly", "věž se zúženým krkem a převislou hlavou nahoře, voštiny pod převisem; pivot = terén, spodek 1 m pod zem; 2K textury"),
    "skala_naklonena": ("Nakloněná skalní věž", "skaly", "nakloněná pískovcová věž, trsy trávy nahoře; pivot = terén, spodek 1 m pod zem; 2K textury"),
    "skala_masiv_2veze": ("Skalní masiv – 2 věže", "skaly", "dvě srostlé věže s hlubokou puklinou mezi nimi, 2 borovice; pivot = terén, spodek 1 m pod zem; 2K textury"),
    "skala_masiv_3veze": ("Skalní masiv – 3 věže", "skaly", "tři srostlé věže různé výšky, 2 borovice a tráva; pivot = terén, spodek 1 m pod zem; 2K textury"),
    "balvan_zula": ("Žulový balvan", "skaly", "oblá žula z pole, zrnitá struktura (živec, křemen, slída), pukliny, mech a lišejník; 2K textury"),
    "kamen_zula": ("Žulový kámen", "skaly", "oblý žulový kámen, pukliny, mech; 1K textury"),
    "kamen_piskovec": ("Pískovcový kámen", "skaly", "pískovec s vrstvami a stékanci, mech; 1K textury"),
    "kamen_droba": ("Kámen z droby", "skaly", "šedá droba, ostrý lom; 1K textury"),
    "kamen_maly": ("Kamínek", "skaly", "kamínek na zem; 1K textury"),
    "zebrinak_plachta": ("Vůz s plachtou", "venku", "žebřiňák s oblouky z prutů a režnou lněnou plachtou (sešité pruhy, záplata, mapy od vody); 2 materiály: dřevo/železo 2K + plátno 2K oboustranné"),
    "zebrinak": ("Žebřiňák", "venku", "čtyřkolový selský vůz kolem r. 1400; každé prkno vlastní kresba, stáří a opotřebení, vyměněné díly, kované šíny s rzí, bláto; 2K (barva, normal, drsnost, kov, AO)"),
    "parez": ("Pařez", "rostliny", "pařez s kořenovými náběhy, letokruhy a praskliny na řezu, mech, choroše; 1K textury"),
    "kmen": ("Padlý kmen", "rostliny", "padlý kmen s pahýly větví, kůra, mech; 1K textury"),
    "trava_vysoka": ("Vysoká tráva", "rostliny", "trs trávy z karet (alpha clip, oboustranné), 1K textura"),
    "trava_nizka": ("Nízká tráva", "rostliny", "nízký trs trávy z karet (alpha clip, oboustranné), 1K textura"),
    "liska": ("Líska", "rostliny", "keř: větve 3D s kůrou, listí jako karty (alpha clip, oboustranné)"),
    "trnka": ("Trnka", "rostliny", "keř: větve 3D s kůrou, listí jako karty (alpha clip, oboustranné)"),
    "bez_cerny": ("Černý bez", "rostliny", "keř s bobulemi: větve 3D s kůrou, listí jako karty (alpha clip, oboustranné)"),
    "hloh": ("Hloh", "rostliny", "keř: větve 3D s kůrou, laločnaté listí jako karty (alpha clip, oboustranné)"),
    "sipek": ("Šípek", "rostliny", "keř se šípky: větve 3D s kůrou, listí jako karty (alpha clip, oboustranné)"),
    "dub": ("Dub", "rostliny", "strom: kmen a větve 3D s brázditou kůrou a kořenovými náběhy, plná koruna z karet větévek; starý dub krátký mohutný kmen, široká nízká koruna, suché větve"),
    "lipa": ("Lípa", "rostliny", "strom: kmen a větve 3D, plná vejčitá koruna z karet větévek"),
    "buk": ("Buk", "rostliny", "strom: hladká šedá kůra, plná koruna z karet větévek"),
    "briza": ("Bříza", "rostliny", "strom: bílá kůra s černými prasklinami a tmavou patou, převislé větévky"),
    "olse": ("Olše", "rostliny", "strom k potoku: tmavá rozpraskaná kůra, kuželovitě vejčitá koruna, starší i vícekmenná"),
    "vrba_hlavata": ("Vrba hlavatá", "rostliny", "ořezávaná vrba u vody: krátký silný kmen s hrbolatou hlavou, svislé pruty s listím"),
    "vrba": ("Vrba", "rostliny", "vrba bílá u vody: nakloněný kmen s hlubokou brázditou kůrou, široká nepravidelná koruna, stříbřité listí"),
    "smrk": ("Smrk", "rostliny", "jehličnan: štíhlý kužel, přesleny vodorovných až svěšených větví s mezerami, šedohnědá šupinatá kůra; starý smrk se suchou spodní třetinou a holými pahýly"),
    "jedle": ("Jedle", "rostliny", "jehličnan: vodorovné ploché větve v patrech, šedá kůra; stará jedle s plošším vrcholem a suchými pahýly dole"),
    "borovice": ("Borovice", "rostliny", "jehličnan: oranžová kůra nahoře, šedohnědá dole, nepravidelná deštníkovitá koruna z chomáčů"),
    "kapradi": ("Kapradí", "rostliny", "trs kapradě (samec): růžice obloukovitých listů z karet"),
    "kopriva": ("Kopřivy", "rostliny", "trs kopřiv s visícími květenstvími, zkřížené karty"),
    "ostruzina": ("Ostružiní", "rostliny", "obloukovité pruty ostružiníku (3D) s listy a plody (zralé, červené, zelené)"),
    "rakos": ("Rákos", "rostliny", "trs rákosu k vodě, vysoké karty 1:3 s latami"),
    "orobinec": ("Orobinec", "rostliny", "trs orobince k vodě: ploché listy a hnědé palice"),
    "mech": ("Mech na kámen", "rostliny", "nízký polštář mechu s roztřepeným okrajem (alpha clip), pokládá se na kameny"),
    "trava_sada": ("Trávy – sada", "rostliny", "všech 6 trsů trávy v jednom souboru se společnou 1K texturou (každý trs je samostatný objekt)"),
}
AGE = {"mlady": "mladý", "mlada": "mladá", "stredni": "střední", "stary": "starý", "stara": "stará"}

def describe(name):
    base = name.replace("_daleko", "")
    key = max((k for k in INFO if base.startswith(k)), key=len)
    cz, cat, note = INFO[key]
    suf = base[len(key):].strip("_")
    if suf in AGE: cz = f"{cz} {AGE[suf]}"
    elif suf: cz = f"{cz} {suf}"
    if name.endswith("_daleko"):
        cz += " – vzdálená verze (LOD)"; note = "3 zkřížené karty s obrazem rostliny, pro velkou vzdálenost"
    return cz, cat, note

lines = []
for name in NAMES:
    src = os.path.join(OUT, f"{name}.glb")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    ms = [o for o in bpy.data.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    sx = max(p.x for p in pts) - min(p.x for p in pts)
    sy = max(p.y for p in pts) - min(p.y for p in pts)
    sz = max(p.z for p in pts) - min(p.z for p in pts)
    tris = sum(len(p.vertices) - 2 for o in ms for p in o.data.polygons)
    shutil.copy(src, os.path.join(DST, f"{name}.glb"))
    cz, cat, note = describe(name)
    mb = os.path.getsize(src) / 1e6
    lines.append(f"{name}.glb | {cz} | {cat} | nic | {sx:.2f} × {sz:.2f} × {sy:.2f} | {note}; {tris} trojúhelníků, {mb:.1f} MB, vlastní tvorba")
with open(os.path.join(DST, "seznam.txt"), "a") as f:
    for l in lines:
        f.write(l + "\n")
print("SEZNAM", len(lines))
