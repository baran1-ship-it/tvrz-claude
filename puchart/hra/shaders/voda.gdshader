// Potoky (blender/voda.py) podle Havrana (shaders/reka.gdshader – Waterways upravený pro Compatibility): bez kopie obrazovky
// a hloubkové textury. Hloubka vody z příčného profilu (UV.y 0..1 napříč, uprostřed nejhlubší), barva od mělké hnědozelené
// po tmavou, u břehu průhledná podle hloubky (pozvolný přechod, ne hrana); vlny = normálová mapa unášená po proudu
// (UV.x = metry po proudu) ve dvou vrstvách, pěna na peřejích (sklon hladiny) a slabě v proudnici. 2 textury, 4 vzorky.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_schlick_ggx;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D pena_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec3 melka : source_color = vec3(0.353, 0.42, 0.227);    // Havran #5A6B3A
uniform vec3 hluboka : source_color = vec3(0.118, 0.165, 0.11);  // Havran #1E2A1C
uniform float hloubka = 0.3;          // m uprostřed proudu
uniform float hloubka_barvy = 0.35;   // m: od této hloubky plně tmavá
uniform float cirost = 0.25;           // m: do této hloubky průhledná (Havran reka cirost 0.35)
uniform float kryti_max = 0.55;       // nejvyšší krytí hladiny (Míša 10. 11.: kamenný potok – dno s valouny musí být vidět; mělký podhorský tok je čirý)
uniform float rychlost = 0.45;        // m/s
uniform float meritko = 2.2;          // m na dlaždici vln
uniform float pena_sklon = 0.03;      // sklon hladiny, od kterého je peřej
varying float sklon;
varying vec3 wpos;

uniform float zdvih_daleko = 0.0;   // m na m vzdálenosti nad 200 m: hrubé LOD terénu (krok 4–16 m) jsou nad úzkým korytem
                                   // (kontrola 5. 11.: LOD 8 m schoval 42 % os toků – „někde chybí voda“)
void vertex() {
	vec3 nw = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (zdvih_daleko > 0.0) {
		float dk = distance(wpos.xz, INV_VIEW_MATRIX[3].xz);
		VERTEX.y += max(0.0, dk - 200.0) * zdvih_daleko;
		wpos.y += max(0.0, dk - 200.0) * zdvih_daleko;
	}
	sklon = sqrt(max(0.0, 1.0 - nw.y * nw.y)) / max(nw.y, 0.2);
}

void fragment() {
	float h = UV.y;                       // skutečná hloubka nad terénem (blender/voda.py)
	vec2 p = vec2(UV.x, (wpos.x - wpos.z) * 0.7) / meritko;   // po proudu UV.x (m), napříč světové souřadnice
	float rv = rychlost * (0.6 + 0.4 * smoothstep(0.0, hloubka, h));   // na mělčině pomaleji
	vec3 n1 = texture(normal_tex, p + vec2(-TIME * rv / meritko, 0.0)).xyz;
	vec3 n2 = texture(normal_tex, p * 2.3 + vec2(-TIME * rv * 1.7 / meritko, 0.37)).xyz;
	NORMAL_MAP = normalize(n1 * 2.0 - 1.0 + (n2 * 2.0 - 1.0) * 0.6) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 0.35;
	float sum = texture(pena_tex, p * 1.7 + vec2(-TIME * rv * 1.2 / meritko, 0.0)).r;
	float sum2 = texture(pena_tex, p * 3.1 + vec2(-TIME * rv * 2.0 / meritko, 0.5)).r;
	float perej = smoothstep(pena_sklon, pena_sklon * 3.0, sklon);
	float pena = smoothstep(0.55, 0.85, sum * 0.6 + sum2 * 0.4) * (perej * 0.8 + 0.08);
	vec3 col = mix(melka, hluboka, smoothstep(0.0, hloubka_barvy, h));
	ALBEDO = mix(col, vec3(0.86, 0.88, 0.84), pena);
	ROUGHNESS = mix(0.22, 0.5, pena); METALLIC = 0.0; SPECULAR = 0.3;   // ne zrcadlo oblohy (potok v lese, zakalený)
	ALPHA = smoothstep(0.0, cirost, h) * kryti_max + pena * 0.25 * smoothstep(0.0, 0.05, h);   // k břehu plynule do ztracena (Havran)
}
