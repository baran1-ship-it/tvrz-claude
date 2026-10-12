shader_type spatial;
// Lomove zdivo (foto textura) a vapenna omitka, ktera misty opadava - odpovida materialu v Blenderu.
#include "res://shaders/projekce.gdshaderinc"

uniform sampler2D kamen_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D kamen_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D kamen_r : hint_default_white, filter_linear_mipmap, repeat_enable;
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

varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(wn);
	vec2 uv; vec3 t; vec3 b;
	projekce(wp, n, uv, t, b);
	vec2 uk = uv / kamen_m;
	vec2 uo = uv / omitka_m + vec2(0.21, 0.47);
	float big = texture(sum, uv * vec2(0.05, 0.075)).r;
	float detail = texture(sum, uv * 0.6).r;
	float lowz = 1.0 - smoothstep(0.0, 2.2, wp.y);
	float cover = big + (kryti - 0.5) * 0.22 - lowz * 0.07 + (detail - 0.5) * 0.04;
	float pm = smoothstep(0.475, 0.49, cover);
	vec3 ka = texture(kamen_a, uk).rgb * kamen_tint;
	vec3 oa = texture(omitka_a, uo).rgb;
	// ve hre (filmic) omitka vychazi zlutejsi nez v Blenderu (AgX): ubrat sytost
	oa = mix(oa, vec3(dot(oa, vec3(0.3, 0.59, 0.11))), 0.4) * tint;
	// skvrny, stekance, vlhko u paty
	float tone = texture(sum, uv * 0.012 + 0.3).r;
	oa = mix(oa, oa * vec3(0.72, 0.68, 0.6), smoothstep(0.3, 0.7, tone) * 0.5);
	float streak = texture(sum, vec2(uv.x * 0.15, wp.y * 0.01)).r;
	oa = mix(oa, oa * vec3(0.62, 0.6, 0.55), smoothstep(0.55, 0.75, streak) * 0.3 * spina);
	float damp = (1.0 - smoothstep(0.3, 1.9, wp.y + big * 1.2)) * 0.7 * spina;
	oa = mix(oa, oa * vec3(0.35, 0.32, 0.26), damp);
	float rim = smoothstep(0.488, 0.5, cover) * (1.0 - smoothstep(0.5, 0.53, cover));
	vec3 col = mix(ka, oa, pm);
	col = mix(col, vec3(0.15, 0.13, 0.1), rim * 0.6);
	float dirt = (1.0 - smoothstep(-0.3, 1.0, wp.y)) * mix(0.5, 1.0, big);
	col = mix(col, vec3(0.06, 0.05, 0.035), dirt * 0.5 * spina);
	ALBEDO = col;
	ROUGHNESS = mix(texture(kamen_r, uk).r, texture(omitka_r, uo).r, pm);
	SPECULAR = 0.3;
	vec3 nk = texture(kamen_n, uk).rgb * 2.0 - 1.0;
	vec3 no = texture(omitka_n, uo).rgb * 2.0 - 1.0;
	vec3 tn = normalize(mix(nk, no * vec3(0.6, 0.6, 1.0), pm));
	NORMAL = normalize((VIEW_MATRIX * vec4(normala_svet(tn, t, b, n), 0.0)).xyz);
}
