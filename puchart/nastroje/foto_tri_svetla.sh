#!/bin/bash
# Kontrola nového materiálu ve více světlech (plán B3, Second Take: „ráno, poledne, večer + interiér s loučí“):
# jeden start hry, z jedné polohy snímky v několika denních dobách (hlavni.gd PUCHART_FOTO_CASY) – rychlejší než
# opakovaný foto.sh (stavba světa jen jednou). V noci svítí louč v ruce (predmety.gd SVETLA louc × prostredi.json
# atmosfera.svitidla); vypnout PUCHART_FOTO_LOUC=0.
# Použití: bash nastroje/foto_tri_svetla.sh "x,z,y,cx,cz,cy" out_prefix [hodiny]
#   y a cy absolutně (jako foto_portaly.sh); PUCHART_FOTO_REL=1 → výšky nad terénem
#   hodiny: výchozí z den.json klic_hodina (ráno, poledne, soumrak, noc), např. "7,12,19.6,23"
#   výstup: out_prefix_<hodina>.png (např. /tmp/x_7_0.png, /tmp/x_12_0.png, /tmp/x_19_6.png, /tmp/x_23_0.png)
K=$(cd "$(dirname "$0")/.." && pwd); G=${G:-/opt/godot47/Godot_v4.7.2-stable_linux.x86_64}
[ -z "$1" ] || [ -z "$2" ] && { echo "použití: $0 \"x,z,y,cx,cz,cy\" out_prefix [hodiny]"; exit 2; }
POL=$1; OUT=$2
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT";; esac
mkdir -p "$(dirname "$OUT")"
CASY=${3:-$(python3 -c "import json;h=json.load(open('$K/pravidla/svet/den.json'))['klic_hodina'];print(','.join(str(h[k]) for k in ('rano','poledne','soumrak','noc')))")}
PRVNI=${CASY%%,*}
ABS=1; [ -n "$PUCHART_FOTO_REL" ] && ABS=
cd "$K/hra"
PUCHART_FOTO_ABS=$ABS PUCHART_CAS=$PRVNI PUCHART_FOTO_CASY=$CASY PUCHART_FOTO="$POL;$OUT.png" timeout 600 \
  xvfb-run -a -s "-screen 0 1600x1000x24" $G --rendering-driver opengl3 --resolution 1600x1000 2>&1 | grep -E "^FOTO|SCRIPT ERROR" -A0
n=$(ls "$OUT"_*.png 2>/dev/null | wc -l); k=$(echo "$CASY" | tr ',' '\n' | wc -l)
echo "SNIMKU $n z $k"
[ "$n" -ge "$k" ]
