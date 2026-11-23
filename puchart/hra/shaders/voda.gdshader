// Potoky (blender/voda.py) podle Havrana (shaders/reka.gdshader – Waterways upravený pro Compatibility): bez kopie obrazovky
// a hloubkové textury. Hloubka vody z příčného profilu (UV.y 0..1 napříč, uprostřed nejhlubší), barva od mělké hnědozelené
// po tůňovou, krytí podle hloubky a Fresnelu, u břehu do ztracena (barva vrcholu); vlny = normálová mapa unášená po proudu
// (UV.x = metry po proudu) ve dvou vrstvách, pěna jen u kraje a na peřejích. Odraz lesa z equirect panoramy (Hvozd, plán D1,
// Míša 20. 11. H1) do EMISSION × barva okolí podle denní doby (den.gd okoli – v noci nesvítí). 3 textury, 6 vzorků.
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
uniform float hloubka_barvy = 0.2;    // m: barva od kraje (melka) ke středu (hluboka) lineárně h/x (Hvozd 18. 11.)
uniform float cirost = 0.35;          // m: pohlcení 63 % (Beer–Lambert)
uniform float fresnel_f0 = 0.02;      // voda n ≈ 1,33
uniform float drsnost_klid = 0.08;
uniform float drsnost_pena = 0.5;
uniform float specular = 0.12;
uniform sampler2D panorama : source_color, filter_linear_mipmap, repeat_enable;   // equirect les (voda_hra.json vzhled_13_11 panorama_*)
// Hvozd (docs/rozpracovane/voda_hvozd_navod.md): R = reflect(−V, N vlnitá), R.y = |R.y|, u = atan(z, x)/2π + 0,5, v = asin(y)/π;
// Fresnel Schlick z vlnité normály; tělo tmavé (kraj hnědý → střed černozelený), krytí kraj 0,2 → střed 0,92.
uniform vec3 okoli = vec3(1.0);                 // barva okolí podle denní doby (den.gd pridej_vodu: mlha preset / odpoledne)
uniform float odraz_sila = 0.8;       // Hvozd refl·0,8
uniform float odraz_lod = 1.5;        // mip panoramy (rozmazání odrazu; pevný mip = bez švu na atan)
uniform float panorama_otoceni = 0.0; // posun u (0..1) – natočení lesa v odrazu
uniform float kryti_kraj = 0.2;       // Hvozd: krytí u kraje
uniform float kryti_stred = 0.92;     // Hvozd: krytí uprostřed
uniform float hloubka_kryti = 0.2;    // m hloubky, na kterých krytí doroste z kraje na střed
uniform float vlny_protazeni = 2.5;   // Hvozd: vlny protažené po proudu ×2,5
uniform float vlny_sklon = 0.6;       // Hvozd: sklon normály ×0,6
uniform float pena_kraj_hloubka = 0.06;   // m: pěna u kraje do této hloubky
uniform float pena_kraj_sila = 0.6;
uniform float kryti_min = 0.7;      // krytí mělčiny od hloubky kraj_m (voda_hra.json kryti_min; Míša 17. 11.: „nemáš vodu v potoce“)
uniform float kraj_m = 0.08;         // m hloubky, na kterých krytí u čáry vody doroste z kryti_kraj na kryti_min
uniform float rychlost = 0.45;        // m/s
uniform float meritko = 2.2;          // m na dlaždici vln
uniform float pena_sklon = 0.03;      // sklon hladiny, od kterého je peřej
uniform float pena_kamen_sila = 0.5;  // pěna za kameny (voda_hra.json vzhled_13_11 pena_kamen_sila)
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
	// skutečná hloubka nad terénem (blender/voda.py UV v). Exportér glTF Blenderu ukládá v' = 1 − v a Godot ho nevrací.
	float h = 1.0 - UV.y;
	// VLNY (Hvozd): jedna normálová mapa čtená dvakrát (měřítko 1 a 2,3, rychlost 1 a 1,7), sečtené 0,55/0,45, protažené po proudu
	vec2 p = vec2(UV.x / vlny_protazeni, (wpos.x - wpos.z) * 0.7) / meritko;
	float rv = rychlost * (0.6 + 0.4 * smoothstep(0.0, hloubka, h));   // na mělčině pomaleji
	vec3 n1 = texture(normal_tex, p + vec2(-TIME * rv / (meritko * vlny_protazeni), 0.0)).xyz * 2.0 - 1.0;
	vec3 n2 = texture(normal_tex, p * 2.3 + vec2(-TIME * rv * 1.7 / (meritko * vlny_protazeni), 0.37)).xyz * 2.0 - 1.0;
	float pk = 1.0 - COLOR.r;   // pěna za kamenem, který láme hladinu (blender/voda.py)
	vec3 nt = normalize(vec3((n1.xy * 0.55 + n2.xy * 0.45) * (vlny_sklon + pk * 0.5), 1.0));
	NORMAL_MAP = nt * 0.5 + 0.5; NORMAL_MAP_DEPTH = 1.0;
	// PĚNA jen u kraje a na peřejích (Míša 20. 11.: bílé šmouhy po celé ploše) a za kameny, které lámou hladinu
	float sum = texture(pena_tex, p * 1.7 + vec2(-TIME * rv * 1.2 / meritko, 0.0)).r;
	float sum2 = texture(pena_tex, p * 3.1 + vec2(-TIME * rv * 2.0 / meritko, 0.5)).r;
	float sf = sum * 0.6 + sum2 * 0.4;
	float perej = smoothstep(pena_sklon, pena_sklon * 3.0, sklon);
	float u_kraje = 1.0 - smoothstep(0.0, pena_kraj_hloubka, h);
	float pena = smoothstep(0.55, 0.85, sf) * max(perej * 0.8, u_kraje * pena_kraj_sila);
	pena = max(pena, pk * pena_kamen_sila * smoothstep(0.25, 0.65, sf + pk * 0.15));
	// ODRAZ: světová vlnitá normála a odražený pohled → equirect panorama lesa
	vec3 nvw = normalize(NORMAL + TANGENT * nt.x + BINORMAL * nt.y);
	vec3 Nw = normalize((INV_VIEW_MATRIX * vec4(nvw, 0.0)).xyz);
	vec3 Vw = normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz);
	vec3 Rw = reflect(-Vw, Nw); Rw.y = abs(Rw.y);
	vec2 puv = vec2(atan(Rw.z, Rw.x) / 6.28318 + 0.5 + panorama_otoceni, 0.5 - asin(clamp(Rw.y, 0.0, 1.0)) / 3.14159);
	vec3 refl = textureLod(panorama, puv, odraz_lod).rgb * odraz_sila * okoli;
	float frw = fresnel_f0 + (1.0 - fresnel_f0) * pow(1.0 - clamp(dot(Vw, Nw), 0.0, 1.0), 5.0);   // Schlick z vlnité normály
	vec3 col = mix(melka, hluboka, clamp(h / hloubka_barvy, 0.0, 1.0));   // kraj hnědý → střed černozelený lineárně (Hvozd)
	ALBEDO = mix(col * (1.0 - frw), pena_barva, pena);
	EMISSION = refl * frw * (1.0 - pena);   // Compatibility nemá SSR – odraz jako vlastní svit, v noci okoli ≈ 0
	ROUGHNESS = mix(drsnost_klid, drsnost_pena, pena); METALLIC = 0.0; SPECULAR = specular;   // lesk slunce
	// krytí podle hloubky (Hvozd): na čáře vody kryti_kraj → do kraj_m mělčina kryti_min (Míša 17. a 19. 11.: voda musí být
	// vidět i na mělčině) → do hloubka_kryti střed kryti_stred; krajní řada a vrcholy nad vodou COLOR.a = 0 (žádná hrana sítě)
	float kraj = COLOR.a * smoothstep(0.0, 0.005, h);
	ALPHA = clamp(max(mix(mix(kryti_kraj, kryti_min, smoothstep(0.0, kraj_m, h)), kryti_stred, smoothstep(kraj_m, max(hloubka_kryti, kraj_m + 0.01), h)), frw) + pena * 0.3, 0.0, 1.0) * kraj;
}
