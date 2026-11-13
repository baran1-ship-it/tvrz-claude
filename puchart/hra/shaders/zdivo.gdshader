// Lomové zdivo s vápennou omítkou – převzato z Havrana (shaders/zdivo.gdshader, postup jako v KCD): výšková mapa kamene
// (parallax, hloubka spár), omítka zatéká nejdřív do spár a kameny z ní vystupují; kryti = kolik omítky (hradby málo –
// malta ve spárách a ostrůvky, budovy jádra víc – Míša 5. 11.: omítka z Havrana jen na budovy v jádrech). Proti rastru
// (Míša 5. 11.): druhé pootočené vzorkování kamene mezi skvrnami; šum procedurální místo textury šumu. Zapečené stínění
// koutů a vlhká pata zdí z barvy vrcholu G (hrady.zapec_ao) místo Havranovy výšky nad nulou (hrad stojí na kopci).
// Vzorkovače: kámen 4 + omítka 3 = 7 (limit Adreno 13).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D kamen_a : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D kamen_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D kamen_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D kamen_h : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D omitka_a : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D omitka_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D omitka_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float kamen_m = 4.2;   // velikost dlaždice kamene: desky břidlice 20–40 cm (gc_18), dřív 2,5 m = kameny 8–15 cm, z dálky šum
uniform float omitka_m = 2.0;
uniform float kryti = 0.5;
uniform vec3 tint = vec3(0.86, 0.78, 0.62);
uniform vec3 kamen_tint = vec3(0.8, 0.78, 0.75);
uniform float spina = 1.0;
uniform float hloubka = 0.08;
uniform int kroky = 7;
uniform vec2 h_rozsah = vec2(0.42, 0.95);

varying vec3 wp;
varying vec3 wn;

// hash bez sinu (Dave Hoskins „Hash without Sine“): sin(velké číslo) na Adreno ztrácí přesnost → šum po čtvercích
// („minecraft“, Míša 9. 11.); vstup zabalený do 1024 m, aby fract() neztrácel bity na souřadnicích stovek metrů
float hash(vec2 p) { p = mod(p, 1024.0); vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float sum(vec2 p) { return noise(p * 2.5) * 0.6 + noise(p * 6.0 + 3.7) * 0.4; }   // náhrada Havranovy textury šumu

// Projekce s PEVNÝMI osami (Míša 9. 11.: „pořád minecraft“): dřív tečna z normály – reliéf zdi naklání každou buňku sítě
// o 1–2°, na souřadnicích stovek metrů to posunulo UV o metry → každá buňka jiný výřez kamene i omítky = čtverce.
// Teď svislá plocha bere osu X nebo Z podle převažující složky normály (na diagonále rozhoduje šum – nepravidelné
// skvrny místo čtverců), vodorovná XZ. Posun podle vzdálenosti roviny (také skákal po buňkách) zrušen.
void projekce(vec3 p, vec3 n, out vec2 uv, out vec3 t, out vec3 b) {
	if (abs(n.y) > 0.7) { t = vec3(1.0, 0.0, 0.0); b = vec3(0.0, 0.0, 1.0); uv = p.xz; return; }
	float wx = n.x * n.x; float wz = n.z * n.z;
	float vyber = wx / (wx + wz + 1e-5) + (noise(p.xz * 0.35 + p.y * 0.21) - 0.5) * 0.35;
	b = vec3(0.0, 1.0, 0.0);
	if (vyber > 0.5) { float sg = n.x >= 0.0 ? 1.0 : -1.0; t = vec3(0.0, 0.0, -sg); uv = vec2(-sg * p.z, p.y); }
	else { float sg = n.z >= 0.0 ? 1.0 : -1.0; t = vec3(sg, 0.0, 0.0); uv = vec2(sg * p.x, p.y); }
}

float vyska(vec2 u) { return smoothstep(h_rozsah.x, h_rozsah.y, texture(kamen_h, u).r); }

// Stochastické (hex) skládání proti opakování (Mikkelsen 2022, „Practical Real-Time Hex-Tiling“; Míša 5. 11.: „pořád je vidět,
// že je to opakovaná textura“): plocha rozdělená na trojúhelníkovou síť, každý vrchol má náhodný posun fotky, tři výřezy se
// míchají podle výšky kamene – přechody vedou spárami mezi kameny, ne přes kámen.
vec2 hash2(vec2 p) { p = mod(p, 1024.0); vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
void hex_vahy(vec2 uv, out vec2 o1, out vec2 o2, out vec2 o3, out vec3 w) {
	vec2 sk = mat2(vec2(1.0, 0.0), vec2(-0.57735027, 1.15470054)) * (uv * 2.6);
	vec2 bs = floor(sk); vec3 tt = vec3(fract(sk), 0.0); tt.z = 1.0 - tt.x - tt.y;
	vec2 v1; vec2 v2; vec2 v3;
	if (tt.z > 0.0) { w = vec3(tt.z, tt.y, tt.x); v1 = bs; v2 = bs + vec2(0.0, 1.0); v3 = bs + vec2(1.0, 0.0); }
	else { w = vec3(-tt.z, 1.0 - tt.y, 1.0 - tt.x); v1 = bs + vec2(1.0, 1.0); v2 = bs + vec2(1.0, 0.0); v3 = bs + vec2(0.0, 1.0); }
	o1 = hash2(v1); o2 = hash2(v2); o3 = hash2(v3);
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

uniform float mokro = 0.0;   // déšť (pocasi.gd): 0 sucho .. 1 promoklé – tmavší, lesklejší (KCD: mokré povrchy a louže)
void fragment() {
	vec3 n = normalize(wn);
	if (!FRONT_FACING) n = -n;
	vec2 uv; vec3 t; vec3 b;
	projekce(wp, n, uv, t, b);
	vec2 uk = uv / kamen_m;
	// proti rastru: v skvrnách jiný výřez kamene (pootočený, jiné měřítko)
	float mk = smoothstep(0.38, 0.62, noise(uv / 3.2) * 0.65 + noise(uv / 1.2 + 13.1) * 0.35);
	vec3 v = normalize(CAMERA_POSITION_WORLD - wp);
	vec3 vt = vec3(dot(v, t), dot(v, b), dot(v, n));
	float dist = length(CAMERA_POSITION_WORLD - wp);
	float fade = (1.0 - smoothstep(20.0, 45.0, dist)) * smoothstep(0.12, 0.45, vt.z);
	float h = vyska(uk);
	if (kroky > 0 && fade > 0.0) {
		vec2 shift = vt.xy / max(vt.z, 0.3) * (hloubka * fade / kamen_m);
		int nkr = int(mix(float(kroky) * 1.6, float(kroky), vt.z));
		float layer = 1.0 / float(nkr); float cur = 1.0; vec2 p = uk; vec2 dp = shift * layer; float hh = h;
		for (int i = 0; i < 20; i++) { if (i >= nkr || hh >= cur) break; cur -= layer; p -= dp; hh = vyska(p); }
		vec2 prev = p + dp; float after = hh - cur; float before = vyska(prev) - (cur + layer);
		uk = mix(p, prev, clamp(after / (after - before + 1e-4), 0.0, 1.0)); h = vyska(uk);
	}
	// hex: tři výřezy kamene (výška, barva, normála) míchané podle výšky – posun z parallaxu zachovaný (uk − základ)
	vec2 o1; vec2 o2; vec2 o3; vec3 hw; hex_vahy(uv / kamen_m, o1, o2, o3, hw);
	float h1 = vyska(uk + o1); float h2 = vyska(uk + o2); float h3 = vyska(uk + o3);
	vec3 hv = hw * pow(vec3(h1, h2, h3) + 0.15, vec3(5.0)); hv /= (hv.x + hv.y + hv.z);
	h = h1 * hv.x + h2 * hv.y + h3 * hv.z;
	vec2 uo = uv / omitka_m + vec2(0.21, 0.47);
	// zapečené stínění: na reliéfu zdi skáče po vrcholech sítě (~0,75 m) – jen jemně a jen v hlubokých koutech; omítka se jím
	// už neřídí (Míša 9. 11.: „pořád minecraft“ – světlé čtverce omítky přesně po síti zdi)
	float ao = mix(1.0, smoothstep(0.15, 0.85, COLOR.g), 0.6);
	float big = sum(uv * vec2(0.05, 0.075)); float detail = sum(uv * 0.6);
	float lowz = 0.0;   // (dřív z AO – po síti zdi čtverce)
	float cover = big + (kryti - 0.5) * 0.22 + 0.15 - lowz * 0.24 + (detail - 0.5) * 0.05;
	float level = smoothstep(0.40, 0.56, cover);
	float pm = smoothstep(h - 0.08, h + 0.02, level * 1.15 - 0.05);
	float joint = 1.0 - smoothstep(0.12, 0.42, h);   // malta ve spárách výrazná – kameny čitelné i z dálky
	pm = max(pm, joint * 0.85 * (1.0 - level * 0.3));
	vec3 ka = (texture(kamen_a, uk + o1).rgb * hv.x + texture(kamen_a, uk + o2).rgb * hv.y + texture(kamen_a, uk + o3).rgb * hv.z) * kamen_tint;
	ka *= mix(0.4, 1.1, smoothstep(0.0, 0.6, h));   // líc kamene světlejší, hrany do spáry tmavé
	ka *= 0.86 + 0.28 * noise(uv / 9.0 + 4.7);   // velká barevná variace kamene
	vec3 oa = texture(omitka_a, uo).rgb;
	float og = dot(oa, vec3(0.3, 0.59, 0.11));
	oa = mix(oa, vec3(og), 0.75) * mix(tint, vec3(0.93, 0.9, 0.84), 0.6);
	float tone = sum(uv * 0.012 + 0.3);
	oa = mix(oa, oa * vec3(0.72, 0.68, 0.6), smoothstep(0.3, 0.7, tone) * 0.5);
	float streak = sum(vec2(uv.x * 0.15, wp.y * 0.01));
	oa = mix(oa, oa * vec3(0.62, 0.6, 0.55), smoothstep(0.55, 0.75, streak) * 0.3 * spina);
	float damp = (1.0 - smoothstep(0.35, 0.8, ao + big * 0.25)) * 0.5 * spina;
	oa = mix(oa, oa * vec3(0.35, 0.32, 0.26), damp);
	float rim = smoothstep(0.0, 0.5, pm) * (1.0 - smoothstep(0.5, 1.0, pm)) * level;
	vec3 col = mix(ka, oa, pm);
	col *= 1.0 - rim * 0.35;
	col = mix(col, col * vec3(0.84, 0.88, 0.72), smoothstep(0.62, 0.8, noise(uv / 5.5 + 1.9)) * 0.4);   // lišejník
	col = mix(col, vec3(0.15, 0.18, 0.08), smoothstep(0.35, 0.8, n.y) * smoothstep(0.5, 0.75, noise(wp.xz * 0.8)) * 0.6);   // mech na koruně
	ALBEDO = col * mix(0.6, 1.0, ao);
	ROUGHNESS = mix(0.9, texture(omitka_r, uo).r, pm);
	SPECULAR = 0.3;
	AO = min(mix(mix(0.35, 1.0, smoothstep(0.0, 0.45, h)), 1.0, pm * 0.7), ao);
	AO_LIGHT_AFFECT = 0.0;   // 13. 11.: přímé světlo (louče, okna) netlumit zapečeným stíněním
	vec3 nk = (texture(kamen_n, uk + o1).rgb * hv.x + texture(kamen_n, uk + o2).rgb * hv.y + texture(kamen_n, uk + o3).rgb * hv.z) * 2.0 - 1.0;
	vec3 no = texture(omitka_n, uo).rgb * 2.0 - 1.0;
	vec3 tn = normalize(mix(nk * vec3(2.2, 2.2, 1.0), no * vec3(0.6, 0.6, 1.0), pm));
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(t * tn.x + b * tn.y + n * tn.z), 0.0)).xyz);
	ALBEDO *= mix(1.0, 0.66, mokro); ROUGHNESS = mix(ROUGHNESS, 0.45, mokro); SPECULAR = mix(SPECULAR, 0.4, mokro);   // mokro (pocasi.gd)
}
