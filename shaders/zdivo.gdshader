shader_type spatial;
global uniform float ab_mip;          // A/B 0.96 (radce 12:10): textury o mip niz (main.gd ab_mip), 0 = beze zmeny
// Lomove zdivo s vapennou omitkou - postup jako v KCD: vyskova mapa kamene (parallax, hloubka spar)
// a michani vrstev podle vysky: omitka zatece nejdriv do spar a kameny z ni vystupuji.
#include "res://shaders/projekce.gdshaderinc"

uniform sampler2D kamen_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D kamen_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D kamen_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D kamen_h : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D omitka_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D omitka_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D omitka_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform float kamen_m = 2.5;
uniform float omitka_m = 2.0;
uniform float kryti = 0.5;
uniform vec3 tint = vec3(1.0);
uniform vec3 kamen_tint = vec3(0.72, 0.68, 0.62);
uniform float spina = 1.0;
uniform float hloubka = 0.05;      // hloubka spar v metrech
uniform int kroky = 12;            // kroky parallaxu (0 = vypnuto)
uniform vec2 h_rozsah = vec2(0.42, 0.95);

varying vec3 wp;
varying vec3 wn;

float vyska(vec2 u) {
	return smoothstep(h_rozsah.x, h_rozsah.y, texture(kamen_h, u).r);
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(wn);
	vec2 uv; vec3 t; vec3 b;
	projekce(wp, n, uv, t, b);
	vec2 uk = uv / kamen_m;

	// parallax occlusion: pohled do teto plochy v jejich souradnicich
	vec3 v = normalize(CAMERA_POSITION_WORLD - wp);
	vec3 vt = vec3(dot(v, t), dot(v, b), dot(v, n));
	float dist = length(CAMERA_POSITION_WORLD - wp);
	// slabne do dalky a pri ostrem uhlu pohledu (jinak se hrany lamou do schudku)
	float fade = (1.0 - smoothstep(12.0, 25.0, dist)) * smoothstep(0.12, 0.45, vt.z);
	float h = vyska(uk);
	if (kroky > 0 && fade > 0.0) {
		vec2 shift = vt.xy / max(vt.z, 0.3) * (hloubka * fade / kamen_m);
		int nkr = int(mix(float(kroky) * 1.6, float(kroky), vt.z));
		float layer = 1.0 / float(nkr);
		float cur = 1.0;
		vec2 p = uk;
		vec2 dp = shift * layer;
		float hh = h;
		for (int i = 0; i < 24; i++) {
			if (i >= nkr || hh >= cur) break;
			cur -= layer;
			p -= dp;
			hh = vyska(p);
		}
		// zpresneni mezi poslednimi dvema vrstvami
		vec2 prev = p + dp;
		float after = hh - cur;
		float before = vyska(prev) - (cur + layer);
		float w = after / (after - before + 1e-4);
		uk = mix(p, prev, clamp(w, 0.0, 1.0));
		h = vyska(uk);
	}
	vec2 uo = uv / omitka_m + vec2(0.21, 0.47);

	// kde je omitka: velke skvrny + vyska kamene (spary se zaplni prvni)
	float big = texture(sum, uv * vec2(0.05, 0.075), ab_mip).r;
	float detail = texture(sum, uv * 0.6, ab_mip).r;
	float lowz = 1.0 - smoothstep(0.0, 2.2, wp.y);
	// omitka je souvisla, kamen jen u paty zdi a v ostruvcich (podle referenci KCD2)
	float cover = big + (kryti - 0.5) * 0.22 + 0.15 - lowz * 0.24 + (detail - 0.5) * 0.05;
	float level = smoothstep(0.40, 0.56, cover);          // 0 holy kamen .. 1 plna omitka
	float pm = smoothstep(h - 0.08, h + 0.02, level * 1.15 - 0.05);
	float joint = 1.0 - smoothstep(0.05, 0.35, h);         // malta ve sparach i bez omitky
	pm = max(pm, joint * 0.85 * (1.0 - level * 0.3));

	vec3 ka = texture(kamen_a, uk, ab_mip).rgb * kamen_tint;
	ka *= mix(0.55, 1.0, smoothstep(0.0, 0.5, h));        // hloubka spar
	vec3 oa = texture(omitka_a, uo, ab_mip).rgb;
	float og = dot(oa, vec3(0.3, 0.59, 0.11));
	oa = mix(oa, vec3(og), 0.75) * mix(tint, vec3(0.93, 0.9, 0.84), 0.6);
	float tone = texture(sum, uv * 0.012 + 0.3, ab_mip).r;
	oa = mix(oa, oa * vec3(0.72, 0.68, 0.6), smoothstep(0.3, 0.7, tone) * 0.5);
	float streak = texture(sum, vec2(uv.x * 0.15, wp.y * 0.01), ab_mip).r;
	oa = mix(oa, oa * vec3(0.62, 0.6, 0.55), smoothstep(0.55, 0.75, streak) * 0.3 * spina);
	float damp = (1.0 - smoothstep(0.3, 1.9, wp.y + big * 1.2)) * 0.7 * spina;
	oa = mix(oa, oa * vec3(0.35, 0.32, 0.26), damp);
	// okraj omitky: tenka tmava hrana tam, kde konci na kameni
	float rim = smoothstep(0.0, 0.5, pm) * (1.0 - smoothstep(0.5, 1.0, pm)) * level;
	vec3 col = mix(ka, oa, pm);
	col *= 1.0 - rim * 0.35;
	float dirt = (1.0 - smoothstep(-0.3, 1.0, wp.y)) * mix(0.5, 1.0, big);
	col = mix(col, vec3(0.06, 0.05, 0.035), dirt * 0.5 * spina);
	ALBEDO = col;
	ROUGHNESS = mix(texture(kamen_r, uk, ab_mip).r, texture(omitka_r, uo, ab_mip).r, pm);
	SPECULAR = 0.3;
	AO = mix(mix(0.35, 1.0, smoothstep(0.0, 0.45, h)), 1.0, pm * 0.7);
	AO_LIGHT_AFFECT = 0.6;
	vec3 nk = texture(kamen_n, uk, ab_mip).rgb * 2.0 - 1.0;
	vec3 no = texture(omitka_n, uo, ab_mip).rgb * 2.0 - 1.0;
	vec3 tn = normalize(mix(nk * vec3(1.4, 1.4, 1.0), no * vec3(0.6, 0.6, 1.0), pm));
	NORMAL = normalize((VIEW_MATRIX * vec4(normala_svet(tn, t, b, n), 0.0)).xyz);
}
