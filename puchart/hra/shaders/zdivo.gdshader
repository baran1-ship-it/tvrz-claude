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
uniform int kroky = 10;
uniform vec2 h_rozsah = vec2(0.42, 0.95);

varying vec3 wp;
varying vec3 wn;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float sum(vec2 p) { return noise(p * 2.5) * 0.6 + noise(p * 6.0 + 3.7) * 0.4; }   // náhrada Havranovy textury šumu

void projekce(vec3 p, vec3 n, out vec2 uv, out vec3 t, out vec3 b) {   // Havran projekce.gdshaderinc
	if (abs(n.y) > 0.7) { t = vec3(1.0, 0.0, 0.0); b = vec3(0.0, 0.0, 1.0); uv = p.xz; }
	else { t = normalize(cross(vec3(0.0, 1.0, 0.0), n)); b = vec3(0.0, 1.0, 0.0); uv = vec2(dot(p, t), p.y); }
	float d = dot(p, n); uv += vec2(d * 0.37, d * 0.61);
}

float vyska(vec2 u) { return smoothstep(h_rozsah.x, h_rozsah.y, texture(kamen_h, u).r); }

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(wn);
	if (!FRONT_FACING) n = -n;
	vec2 uv; vec3 t; vec3 b;
	projekce(wp, n, uv, t, b);
	vec2 uk = uv / kamen_m;
	// proti rastru: v skvrnách jiný výřez kamene (pootočený, jiné měřítko)
	float mk = smoothstep(0.38, 0.62, noise(uv / 3.2) * 0.65 + noise(uv / 1.2 + 13.1) * 0.35);
	vec2 uk2 = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * uk * 0.73 + vec2(0.37, 0.71);
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
	vec2 uo = uv / omitka_m + vec2(0.21, 0.47);
	float ao = COLOR.g;   // zapečené stínění a vlhká pata (1 = volno)
	float big = sum(uv * vec2(0.05, 0.075)); float detail = sum(uv * 0.6);
	float lowz = (1.0 - smoothstep(0.55, 0.95, ao)) * 0.8;   // u paty a v koutech méně omítky (opadává)
	float cover = big + (kryti - 0.5) * 0.22 + 0.15 - lowz * 0.24 + (detail - 0.5) * 0.05;
	float level = smoothstep(0.40, 0.56, cover);
	float pm = smoothstep(h - 0.08, h + 0.02, level * 1.15 - 0.05);
	float joint = 1.0 - smoothstep(0.12, 0.42, h);   // malta ve spárách výrazná – kameny čitelné i z dálky
	pm = max(pm, joint * 0.85 * (1.0 - level * 0.3));
	vec3 ka = mix(texture(kamen_a, uk).rgb, texture(kamen_a, uk2 + (uk - uv / kamen_m)).rgb, mk * 0.6) * kamen_tint;   // plynulé prolnutí druhého výřezu (ostré přepnutí dělalo čtverce)
	ka *= mix(0.4, 1.1, smoothstep(0.0, 0.6, h));   // líc kamene světlejší, hrany do spáry tmavé
	ka *= 0.86 + 0.28 * noise(uv / 9.0 + 4.7);   // velká barevná variace kamene
	vec3 oa = texture(omitka_a, uo).rgb;
	float og = dot(oa, vec3(0.3, 0.59, 0.11));
	oa = mix(oa, vec3(og), 0.75) * mix(tint, vec3(0.93, 0.9, 0.84), 0.6);
	float tone = sum(uv * 0.012 + 0.3);
	oa = mix(oa, oa * vec3(0.72, 0.68, 0.6), smoothstep(0.3, 0.7, tone) * 0.5);
	float streak = sum(vec2(uv.x * 0.15, wp.y * 0.01));
	oa = mix(oa, oa * vec3(0.62, 0.6, 0.55), smoothstep(0.55, 0.75, streak) * 0.3 * spina);
	float damp = (1.0 - smoothstep(0.45, 0.9, ao + big * 0.2)) * 0.7 * spina;
	oa = mix(oa, oa * vec3(0.35, 0.32, 0.26), damp);
	float rim = smoothstep(0.0, 0.5, pm) * (1.0 - smoothstep(0.5, 1.0, pm)) * level;
	vec3 col = mix(ka, oa, pm);
	col *= 1.0 - rim * 0.35;
	col = mix(col, col * vec3(0.84, 0.88, 0.72), smoothstep(0.62, 0.8, noise(uv / 5.5 + 1.9)) * 0.4);   // lišejník
	col = mix(col, vec3(0.15, 0.18, 0.08), smoothstep(0.35, 0.8, n.y) * smoothstep(0.5, 0.75, noise(wp.xz * 0.8)) * 0.6);   // mech na koruně
	ALBEDO = col * mix(0.45, 1.0, ao);
	ROUGHNESS = mix(texture(kamen_r, uk).r, texture(omitka_r, uo).r, pm);
	SPECULAR = 0.3;
	AO = min(mix(mix(0.35, 1.0, smoothstep(0.0, 0.45, h)), 1.0, pm * 0.7), ao);
	AO_LIGHT_AFFECT = 0.6;
	vec3 nk = texture(kamen_n, uk).rgb * 2.0 - 1.0;
	vec3 no = texture(omitka_n, uo).rgb * 2.0 - 1.0;
	vec3 tn = normalize(mix(nk * vec3(2.2, 2.2, 1.0), no * vec3(0.6, 0.6, 1.0), pm));
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(t * tn.x + b * tn.y + n * tn.z), 0.0)).xyz);
}
