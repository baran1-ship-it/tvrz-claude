shader_type spatial;
// Fotograficky material: UV v metrech (kvadry, tramy, prkna) nebo svetove promitani (podlahy, omitky).
#include "res://shaders/projekce.gdshaderinc"

uniform sampler2D tex_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D tex_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float velikost = 2.0;
uniform bool prohodit = false;
uniform bool svet = false;
uniform vec3 tint = vec3(1.0);
uniform float sedost = 0.0;
uniform float spina_dole = 0.0;
uniform sampler2D tex_h : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float hloubka = 0.0;       // parallax, metry
uniform vec2 h_rozsah = vec2(0.2, 0.9);

varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 uv;
	vec3 t; vec3 b;
	vec3 n = normalize(wn);
	if (svet) {
		projekce(wp, n, uv, t, b);
	} else {
		uv = UV;
		if (prohodit) { uv = uv.yx; }
	}
	uv /= velikost;
	float hgt = 1.0;
	if (hloubka > 0.0) {
		vec3 vt;
		if (svet) {
			vec3 v = normalize(CAMERA_POSITION_WORLD - wp);
			vt = vec3(dot(v, t), dot(v, b), dot(v, n));
		} else {
			// UV rezim: tecny prostor z TANGENT/BINORMAL (stejne jako vyskova mapa StandardMaterial3D)
			vt = normalize(VIEW * mat3(TANGENT, -BINORMAL, NORMAL));
		}
		float fade = (1.0 - smoothstep(10.0, 22.0, length(CAMERA_POSITION_WORLD - wp))) * smoothstep(0.12, 0.45, vt.z);
		vec2 dp = vt.xy / max(vt.z, 0.3) * (hloubka * fade / velikost) / 10.0;
		float cur = 1.0;
		float hh = smoothstep(h_rozsah.x, h_rozsah.y, texture(tex_h, uv).r);
		for (int i = 0; i < 10; i++) {
			if (hh >= cur || fade <= 0.0) break;
			cur -= 0.1;
			uv -= dp;
			hh = smoothstep(h_rozsah.x, h_rozsah.y, texture(tex_h, uv).r);
		}
		hgt = hh;
	}
	vec3 c = texture(tex_a, uv).rgb * tint * COLOR.r;
	float g = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(g, g * 0.97, g * 0.9), sedost);
	c = mix(c, vec3(0.06, 0.05, 0.035), (1.0 - smoothstep(-0.2, 1.0, wp.y)) * spina_dole);
	c *= mix(0.6, 1.0, smoothstep(0.0, 0.5, hgt));
	ALBEDO = c;
	AO = mix(0.4, 1.0, smoothstep(0.0, 0.45, hgt));
	AO_LIGHT_AFFECT = 0.5;
	ROUGHNESS = texture(tex_r, uv).r;
	SPECULAR = 0.35;
	vec3 nm = texture(tex_n, uv).rgb * 2.0 - 1.0;
	if (svet) {
		NORMAL = normalize((VIEW_MATRIX * vec4(normala_svet(nm, t, b, n), 0.0)).xyz);
	} else {
		if (prohodit) { nm = vec3(nm.y, nm.x, nm.z); }
		NORMAL_MAP = nm * 0.5 + 0.5;
	}
}
