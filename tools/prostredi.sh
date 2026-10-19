#!/bin/bash
# Novy kontejner (radce 19:15): nastroje pro stavbu, mereni a vydani. Jednou, ~10 min.  bash tools/prostredi.sh
# Godot 4.4.1 + exportni sablony Android, Blender 4.2 jako modul (bpy v /opt/bl), Android SDK build-tools 34,
# textury doplnku Waterways (gitignore "textures/" je v gitu nema). Podpisovy klic NENI tady: docs/predani.md krok 0.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GV=4.4.1
if [ ! -x /opt/godot/Godot_v${GV}-stable_linux.x86_64 ]; then
	mkdir -p /opt/godot && cd /opt/godot
	curl -sSL -o g.zip https://github.com/godotengine/godot/releases/download/${GV}-stable/Godot_v${GV}-stable_linux.x86_64.zip
	unzip -oq g.zip && rm g.zip
fi
ln -sf /opt/godot/Godot_v${GV}-stable_linux.x86_64 /usr/local/bin/godot
T=~/.local/share/godot/export_templates/${GV}.stable
if [ ! -f $T/android_release.apk ]; then
	mkdir -p $T /opt/dl && cd /opt/dl
	curl -sSL -o tpl.tpz https://github.com/godotengine/godot/releases/download/${GV}-stable/Godot_v${GV}-stable_export_templates.tpz
	unzip -oqj tpl.tpz templates/android_release.apk templates/android_debug.apk templates/version.txt -d $T && rm tpl.tpz
fi
if [ ! -x /opt/android/build-tools/34.0.0/apksigner ]; then
	mkdir -p /opt/android && cd /opt/android
	curl -sSL -o ct.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
	unzip -oq ct.zip && rm ct.zip && mkdir -p cmdline-tools/latest
	mv cmdline-tools/bin cmdline-tools/lib cmdline-tools/NOTICE.txt cmdline-tools/source.properties cmdline-tools/latest/ 2>/dev/null || true
	yes | ./cmdline-tools/latest/bin/sdkmanager --sdk_root=/opt/android "build-tools;34.0.0" "platform-tools" > /dev/null
fi
mkdir -p /root/Android && ln -sfn /opt/android /root/Android/Sdk
# editor: cesta k SDK a Jave (sablona editor_settings vznikne prvnim spustenim)
godot --headless --quit > /dev/null 2>&1 || true
ES=$(ls ~/.config/godot/editor_settings-4*.tres 2>/dev/null | head -1)
JH=$(dirname "$(dirname "$(readlink -f "$(which java)")")")
if [ -n "$ES" ] && ! grep -q '^export/android/android_sdk_path' "$ES"; then
	sed -i "/^\[resource\]/a export/android/android_sdk_path = \"/root/Android/Sdk\"\nexport/android/java_sdk_path = \"$JH\"" "$ES"
fi
# Blender jako modul (stejne API jako /opt/bl/bin/python u predchoziho stavitele)
if ! /opt/bl/bin/python -c "import bpy" 2>/dev/null; then
	PY=$(command -v python3.11 || true)
	[ -z "$PY" ] && { echo "chybi python3.11 (bpy 4.2 ho potrebuje)"; exit 1; }
	$PY -m venv /opt/bl && /opt/bl/bin/pip install -q bpy==4.2.0 pillow numpy
fi
# Waterways (MIT): textury, ktere gitignore "textures/" vynechal
W=$ROOT/addons/waterways/textures
mkdir -p $W
for f in foam_noise.png flow_offset_noise.png water1_normal_bump.png debug_pattern.png debug_arrow.svg lava_normal_bump.png lava_emission.png; do
	[ -f $W/$f ] || curl -sSL -o $W/$f https://raw.githubusercontent.com/Arnklit/Waterways/main/addons/waterways/textures/$f
done
python3 -c "import PIL" 2>/dev/null || pip install -q pillow
echo "prostredi OK: $(godot --version 2>/dev/null | head -1), bpy $(/opt/bl/bin/python -c 'import bpy; print(bpy.app.version_string)' 2>/dev/null)"
