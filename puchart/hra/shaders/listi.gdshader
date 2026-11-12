shader_type spatial;
// Listi stromu (0.61, Misa: "placacky misto listu a ani pohyb"): misto StandardMaterial3D z modelu.
// 1) vitr: koruna se kyva (vic nahore), listy se chveji (kazdy jinak podle polohy); stejny smer jako trava
// 2) normaly od stredu koruny (radce Jednotny vzhled: "normaly od stredu koruny") - koruna se nasviti jako objem,
//    ne jako jednotlive ploche karty; zadni strana karet prosvita (translucence)
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;   // Puchart: bez depth_prepass (alfa nůžky stačí, předprůchod kreslil listí 2× – troj. 1,16 → 1,89 M)

uniform sampler2D barva : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float prah = 0.5;
uniform vec3 stred = vec3(0.0, 6.0, 0.0);     // stred koruny v souradnicich modelu
uniform float vyska = 10.0;                   // vyska modelu (m)
uniform float sila_vetru = 1.0;
uniform float objem = 0.65;                    // 0 = normaly karet, 1 = koule kolem stredu
uniform vec2 vitr_smer = vec2(0.8, 0.6);
uniform vec2 zanik = vec2(0.0);
// LOD po stromech (Míša 10. 11.: „blikání stromů, pořád se nějaký strom mění a mizí“ – dřív se přepínala celá buňka 24 m):
// lod_mez = (vzdálenost přepnutí, šířka prolnutí, režim 0 vše / 1 = jen blíž než mez (LOD0) / 2 = jen dál (LOD1)).
// Vzdálenost od kamery hráče (kamera_hrace, i ve stínovém průchodu) k patě stromu; mimo pásmo se strom
// zdegeneruje ve vertex shaderu (žádné pixely), v pásmu prolnutí ditheringem.
uniform vec3 lod_mez = vec3(0.0);
uniform vec2 lod_daleko = vec2(0.0);   // (mez, prolnutí) přechodu na impostor – doplňkový dithering s impostor.gdshader
uniform vec3 kamera_hrace;   // poloha kamery hráče – nastavuje les.gd každý snímek (12. 11.: ne global uniform – pád na tabletu při startu)
varying float v_lod;
varying float v_far;   // Puchart: jako distance_fade (min, max): průhlednost = (d − min)/(max − min); min > max = mizí s dálkou
varying float v_ao;          // vnitrek koruny tmavsi (Misa 0.61 "placacky": koruna jako jedna plocha bez hloubky)
varying vec3 v_tint;         // kazdy trs listi trochu jinak (svetlejsi, zlutejsi, tmavsi)

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	v_lod = 1.0; v_far = 1.0;
	if (lod_mez.z > 0.5) {
		float di = length((MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz - kamera_hrace);
		v_lod = clamp((di - (lod_mez.x - lod_mez.y * 0.5)) / max(lod_mez.y, 0.01), 0.0, 1.0);   // 0 blízko, 1 daleko
		if (lod_daleko.y > 0.0) v_far = 1.0 - clamp((di - (lod_daleko.x - lod_daleko.y * 0.5)) / lod_daleko.y, 0.0, 1.0);
		bool pryc = lod_mez.z < 1.5 ? v_lod >= 1.0 : (v_lod <= 0.0 || v_far <= 0.0);
		if (pryc) { VERTEX = vec3(0.0); }
	}
	float h = clamp(VERTEX.y / max(vyska, 1.0), 0.0, 1.0);
	float faze = wp.x * 0.13 + wp.z * 0.11;
	// kyvani koruny (pomale, poryvy), roste s vyskou kvadraticky - kmen u zeme stoji
	float kyv = (sin(TIME * 0.9 + faze) * 0.6 + sin(TIME * 1.7 + faze * 1.3) * 0.3) * h * h * 0.18 * sila_vetru;
	// chveni listu (rychle, male, kazdy vrchol jinak)
	float ch = sin(TIME * 6.0 + dot(VERTEX, vec3(3.1, 2.3, 2.7)) + faze) * 0.025 * h * sila_vetru;
	vec2 sm = normalize(vitr_smer);
	VERTEX.x += sm.x * kyv + ch;
	VERTEX.z += sm.y * kyv + ch * 0.7;
	VERTEX.y += ch * 0.5;
	// normala: mix karty a smeru od stredu koruny
	float r_kor = max(vyska * 0.3, 0.8);
	v_ao = smoothstep(0.15 * r_kor, r_kor, length(VERTEX - stred));
	vec3 cel = floor(VERTEX * 1.3);
	float hh = fract(sin(dot(cel, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	v_tint = mix(vec3(0.86, 0.9, 0.82), vec3(1.1, 1.08, 0.92), hh);
	vec3 od = normalize(VERTEX - stred + vec3(0.0001));
	od.y = max(od.y, -0.15);                  // spodek koruny ne normalou dolu (Misa 0.61: smrk zespodu cerny)
	NORMAL = normalize(mix(NORMAL, normalize(od), objem));
}

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0));
	int i = q.x + q.y * 4;
	int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[i]) + 0.5) / 16.0;
}

void fragment() {
	if (lod_mez.z > 0.5) {   // doplňkový dithering: LOD0 kreslí pixely b >= f, LOD1 b < f (každý pixel právě jeden), dál LOD1 b < v_far, impostor b >= v_far
		float b = bayer4(FRAGCOORD.xy);
		if (lod_mez.z < 1.5) { if (b < v_lod) discard; }
		else { if (b >= v_lod || b >= v_far) discard; }
	}
	if (zanik.x != zanik.y) {   // stejné jako distance_fade PIXEL_DITHER u StandardMaterial (přechod LOD bez odskočení)
		float dd = length(VERTEX);
		float f = clamp((dd - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
		if (f < bayer4(FRAGCOORD.xy)) discard;
	}
	vec4 t = texture(barva, UV);
	ALBEDO = t.rgb * tint.rgb * v_tint * mix(0.5, 1.0, v_ao);
	// mipmapy prumeruji alfu ridkych listu pod prah (novy dub: z 15 m holy strom) -> alfa roste s urovni mipmapy
	vec2 tsz = vec2(textureSize(barva, 0));
	vec2 ddx = dFdx(UV * tsz);
	vec2 ddy = dFdy(UV * tsz);
	float lod = max(0.0, 0.5 * log2(max(dot(ddx, ddx), dot(ddy, ddy))));
	ALPHA = t.a * (1.0 + lod * 0.35);
	ALPHA_SCISSOR_THRESHOLD = prah;
	// zadni strana: svetlo prosvita (karty proti slunci nejsou cerne)
	BACKLIGHT = t.rgb * 0.5;
	ROUGHNESS = 0.85;
}
