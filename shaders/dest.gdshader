shader_type spatial;
// Déšť: svislé čáry kapek na válci kolem kamery (Míša 12. 11.: „co nejlepší efekt, ať to vypadá reálně, ale nezasekat tablet“).
// KCD dělá déšť jako závoj kolem pohledu (docs/reference/reserse_dest_kcd.md) – jedna průhledná vrstva na válec, bez částic,
// bez čtení hloubky ani obrazovky (CLAUDE.md: žádná kopie obrazovky v shaderu). Čáry: sloupce po obvodu (UV.x), v každém
// sloupci kapka s vlastní fází, délkou a jasem padá dolů (UV.y), rozmazaná pohybem (protažená), slabě zabarvená oblohou.
render_mode unshaded, cull_disabled, blend_mix, depth_draw_never, shadows_disabled, fog_disabled;

uniform float sila = 0.0;          // 0..1 (pocasi.gd)
uniform float hustota = 200.0;     // počet sloupců po obvodu
uniform float rychlost = 9.0;      // opakování za s (výška válce / s)
uniform float delka = 0.1;         // délka čáry (podíl výšky)
uniform float jas = 0.4;
uniform vec3 barva : source_color = vec3(0.75, 0.8, 0.86);
uniform vec2 vitr = vec2(0.04, 0.0); // sklon čar (posun UV.x na výšku)

float h1(float x) { return fract(sin(x * 127.1) * 43758.5453); }

void fragment() {
	vec2 uv = UV;
	uv.x += uv.y * vitr.x;
	float sl = floor(uv.x * hustota);
	float fx = fract(uv.x * hustota);
	float r = h1(sl); float r2 = h1(sl + 31.7); float r3 = h1(sl + 77.3);
	float sirka = smoothstep(0.22, 0.04, abs(fx - 0.5));            // tenká čára uprostřed sloupce
	float y = fract(uv.y - TIME * rychlost * (0.8 + 0.4 * r) + r2); // poloha kapky ve sloupci (13. 11.: UV.y valce roste dolu -> - TIME = kapky padaji, s + stoupaly)
	float d = delka * (0.6 + 0.8 * r3);
	float kapka = smoothstep(0.0, d * 0.3, y) * smoothstep(d, d * 0.4, y); // protažená, měkké konce
	float y2 = fract(uv.y * 1.7 - TIME * rychlost * 1.1 + r3);           // druhá kapka ve sloupci
	kapka = max(kapka, smoothstep(0.0, d * 0.25, y2) * smoothstep(d * 0.8, d * 0.3, y2) * step(0.45, r));
	float vidi = smoothstep(0.0, 0.12, UV.y) * smoothstep(1.0, 0.85, UV.y); // konce válce mizí
	float a = sirka * kapka * vidi * sila * jas * (0.55 + 0.45 * r2);
	if (a < 0.004) discard;
	ALBEDO = barva;
	ALPHA = a;
}
