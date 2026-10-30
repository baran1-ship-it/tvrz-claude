#!/bin/bash
# Dvě APK z jednoho projektu (Míša 30. 10.): testovací = měření výkonu (data/mereni.json) a pak procházka,
# procházková = rovnou procházka (bez souboru měření). Výstup puchart/apk/ (do 100 MB kvůli GitHubu).
set -e
K=$(cd "$(dirname "$0")/.." && pwd); G=${GODOT:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p $K/build/apk $K/apk
cd $K/hra
$G --headless --export-debug "Android" $K/build/apk/puchart_test.apk > $K/build/apk/export_test.log 2>&1
mv data/mereni.json $K/build/mereni.json.odlozeno
trap 'mv $K/build/mereni.json.odlozeno $K/hra/data/mereni.json' EXIT
$G --headless --export-debug "Android" $K/build/apk/puchart_prochazka.apk > $K/build/apk/export_prochazka.log 2>&1
cp $K/build/apk/puchart_test.apk $K/build/apk/puchart_prochazka.apk $K/apk/
ls -la $K/apk/puchart_test.apk $K/apk/puchart_prochazka.apk
