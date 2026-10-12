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
	vec3 c = texture(tex_a, uv).rgb * tint * COLOR.r;
	float g = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(g, g * 0.97, g * 0.9), sedost);
	c = mix(c, vec3(0.06, 0.05, 0.035), (1.0 - smoothstep(-0.2, 1.0, wp.y)) * spina_dole);
	ALBEDO = c;
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
