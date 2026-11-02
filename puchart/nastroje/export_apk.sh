#!/bin/bash
# Dvě APK z jednoho projektu (Míša 30. 10.): testovací = měření výkonu (data/mereni.json) a pak procházka,
# procházková = rovnou procházka (bez souboru měření). Výstup puchart/apk/ (do 100 MB kvůli GitHubu).
set -e
K=$(cd "$(dirname "$0")/.." && pwd); G=${GODOT:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p $K/build/apk $K/apk
cd $K/hra
python3 -c "import json,subprocess,datetime;c=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip();json.dump({'commit':c,'datum':datetime.datetime.now().strftime('%Y-%m-%d %H:%M')},open('data/sestava.json','w'))"
$G --headless --export-debug "Android" $K/build/apk/puchart_test.apk > $K/build/apk/export_test.log 2>&1
mv data/mereni.json $K/build/mereni.json.odlozeno
trap 'mv $K/build/mereni.json.odlozeno $K/hra/data/mereni.json' EXIT
$G --headless --export-debug "Android" $K/build/apk/puchart_prochazka.apk > $K/build/apk/export_prochazka.log 2>&1
cp $K/build/apk/puchart_test.apk $K/build/apk/puchart_prochazka.apk $K/apk/
ls -la $K/apk/puchart_test.apk $K/apk/puchart_prochazka.apk
