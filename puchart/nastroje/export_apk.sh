#!/bin/bash
# Dvě APK z jednoho projektu (Míša 30. 10.): testovací = měření výkonu (data/mereni.json) a pak procházka,
# procházková = rovnou procházka (bez souboru měření). Výstup puchart/apk/ (do 100 MB kvůli GitHubu).
set -e
K=$(cd "$(dirname "$0")/.." && pwd); G=${GODOT:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p $K/build/apk $K/apk
cd $K/hra
python3 -c "import json,subprocess,datetime;c=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip();json.dump({'commit':c,'datum':datetime.datetime.now().strftime('%Y-%m-%d %H:%M')},open('data/sestava.json','w'))"
# každá APK vlastní aplikace (Míša 2. 11.: stejné jméno balíčku → procházková přepsala testovací, měření se nespustilo)
cp export_presets.cfg $K/build/export_presets.zaloha
trap 'cp $K/build/export_presets.zaloha $K/hra/export_presets.cfg' EXIT
# herní data mimo APK (Míša 2. 11., jako Havran): balík do puchart/data/, APK bez těžkých dat (rozpocty.json data_mimo_apk)
python3 $K/nastroje/data_balik.py $K
python3 - "$K" <<'PY'
import json, re, sys
K = sys.argv[1]; vyl = json.load(open(K + "/pravidla/svet/rozpocty.json"))["velikost_apk"]["data_mimo_apk"]["vylouceno_z_apk"]
p = K + "/hra/export_presets.cfg"; s = open(p).read()
s = re.sub(r'^exclude_filter="([^"]*)"', lambda m: 'exclude_filter="%s, %s"' % (m.group(1), ", ".join(vyl)), s, count=1, flags=re.M)
open(p, "w").write(s)
PY
grep -m1 '^exclude_filter' export_presets.cfg
jmeno() { sed -i "s/^package\/unique_name=.*/package\/unique_name=\"$1\"/; s/^package\/name=.*/package\/name=\"$2\"/" export_presets.cfg; }
jmeno cz.puchart.test "Puchart TEST"
$G --headless --export-debug "Android" $K/build/apk/puchart_test.apk > $K/build/apk/export_test.log 2>&1
mv data/mereni.json $K/build/mereni.json.odlozeno
trap 'mv $K/build/mereni.json.odlozeno $K/hra/data/mereni.json; cp $K/build/export_presets.zaloha $K/hra/export_presets.cfg' EXIT
jmeno cz.puchart.prochazka "Puchart procházka"
$G --headless --export-debug "Android" $K/build/apk/puchart_prochazka.apk > $K/build/apk/export_prochazka.log 2>&1
cp $K/build/apk/puchart_test.apk $K/build/apk/puchart_prochazka.apk $K/apk/
ls -la $K/apk/puchart_test.apk $K/apk/puchart_prochazka.apk
