// Potoky (blender/voda.py) podle Havrana (shaders/reka.gdshader – Waterways upravený pro Compatibility): bez kopie obrazovky
// a hloubkové textury. Hloubka vody z příčného profilu (UV.y 0..1 napříč, uprostřed nejhlubší), barva od mělké hnědozelené
// po tůňovou, krytí podle hloubky a Fresnelu, u břehu do ztracena (barva vrcholu); vlny = normálová mapa unášená po proudu
// (UV.x = metry po proudu) ve dvou vrstvách, pěna na peřejích (sklon hladiny) a slabě v proudnici. 2 textury, 4 vzorky.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_schlick_ggx;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D pena_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
// Barvy a čísla z pravidla/svet/voda_hra.json vzhled_13_11 (hlavni.gd; zdroje tam: pipeta misa_real_01/03, Schlick, KCD).
// Míša 13. 11. (misa_13_11_voda_deska.jpg): „plochá průsvitná deska s ostrou hranou“ – dřív konstantní krytí 0,55 od 0,25 m.
// Teď krytí = max(pohlcení podle hloubky 1 − exp(−h/čirost), Fresnel podle úhlu) × krytí kraje (COLOR.a z voda.py):
// shora mělká voda skoro neviditelná (dno s valouny), do dálky zrcadlí les a nebe, na čáře vody 0.
uniform vec3 melka : source_color = vec3(0.384, 0.404, 0.31);
uniform vec3 hluboka : source_color = vec3(0.31, 0.267, 0.161);
uniform float hloubka = 0.3;          // m uprostřed proudu (rychlost na mělčině)
uniform float hloubka_barvy = 0.5;    // m: barva od mělké k tůni (1 − exp(−h/x))
uniform float cirost = 0.35;          // m: pohlcení 63 % (Beer–Lambert)
uniform float fresnel_f0 = 0.02;      // voda n ≈ 1,33
uniform float drsnost_klid = 0.08;
uniform float drsnost_pena = 0.5;
uniform float specular = 0.12;
uniform vec3 odraz : source_color = vec3(0.282, 0.302, 0.149);   // barva odrazu lesa (Compatibility nemá SSR – odraz jen oblohy by byl šedá deska)
uniform float kraj_m = 0.08;         // m hloubky, na kterých krytí u čáry vody doroste
uniform float rychlost = 0.45;        // m/s
uniform float meritko = 2.2;          // m na dlaždici vln
uniform float pena_sklon = 0.03;      // sklon hladiny, od kterého je peřej
uniform float pena_zaklad = 0.0;     // pěna mimo peřeje (13. 11.: 0,08 dělal bílý film)
uniform vec3 pena_barva : source_color = vec3(0.72, 0.74, 0.70);
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
	// skutečná hloubka nad terénem (blender/voda.py UV v). Exportér glTF Blenderu ukládá v' = 1 − v a Godot ho nevrací – dřív
	// se četlo UV.y přímo: všude „hloubka“ 0,6–1 m → krytí stále 0,55 i na kraji = deska s ostrou hranou (Míša 13. 11.)
	float h = 1.0 - UV.y;
	vec2 p = vec2(UV.x, (wpos.x - wpos.z) * 0.7) / meritko;   // po proudu UV.x (m), napříč světové souřadnice
	float rv = rychlost * (0.6 + 0.4 * smoothstep(0.0, hloubka, h));   // na mělčině pomaleji
	vec3 n1 = texture(normal_tex, p + vec2(-TIME * rv / meritko, 0.0)).xyz;
	vec3 n2 = texture(normal_tex, p * 2.3 + vec2(-TIME * rv * 1.7 / meritko, 0.37)).xyz;
	NORMAL_MAP = normalize(n1 * 2.0 - 1.0 + (n2 * 2.0 - 1.0) * 0.6) * 0.5 + 0.5;
	float sum = texture(pena_tex, p * 1.7 + vec2(-TIME * rv * 1.2 / meritko, 0.0)).r;
	float sum2 = texture(pena_tex, p * 3.1 + vec2(-TIME * rv * 2.0 / meritko, 0.5)).r;
	float perej = smoothstep(pena_sklon, pena_sklon * 3.0, sklon);
	float pena = smoothstep(0.55, 0.85, sum * 0.6 + sum2 * 0.4) * (perej * 0.8 + pena_zaklad);
	float pk = 1.0 - COLOR.r;   // pěna za kamenem, který láme hladinu (blender/voda.py, misa_real_01: světlé čárky a vrásky za kameny)
	pena = max(pena, pk * smoothstep(0.25, 0.65, sum * 0.6 + sum2 * 0.4 + pk * 0.15));
	NORMAL_MAP_DEPTH = 0.35 + pk * 0.5;   // vrásky za kamenem
	float nv = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);   // geometrická normála (vlny by krytí rozblikaly)
	float fr = fresnel_f0 + (1.0 - fresnel_f0) * pow(1.0 - nv, 5.0);      // Schlick
	float pohl = 1.0 - exp(-h / cirost);
	vec3 col = mix(melka, hluboka, 1.0 - exp(-h / hloubka_barvy));
	ALBEDO = mix(mix(col, odraz, fr), pena_barva, pena);   // při šikmém pohledu převáží odraz okolí (les u potoka)
	ROUGHNESS = mix(drsnost_klid, drsnost_pena, pena); METALLIC = 0.0; SPECULAR = specular;   // lesk slunce, ne zrcadlo oblohy
	float kraj = COLOR.a * smoothstep(0.0, kraj_m, h);   // krajní řada a vrcholy nad vodou: 0 (žádná hrana sítě)
	ALPHA = clamp(max(pohl, fr) + pena * 0.25, 0.0, 1.0) * kraj;
}
