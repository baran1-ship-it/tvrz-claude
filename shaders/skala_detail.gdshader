shader_type spatial;
// Skalni vez (K4): zapecena textura modelu (barva, mech, AO z Blenderu) + detail z fotky piskovce promitnuty
// ze sveta (3 smery), aby skala zblizka nebyla rozmazana a pixelova. Detail jen meni jas (barvu dava zapeceni).
render_mode cull_back, diffuse_burley;
global uniform float ab_mip;          // A/B 0.96 (radce 12:10): textury o mip niz (main.gd ab_mip), 0 = beze zmeny

uniform sampler2D barva : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D normala : hint_normal, filter_linear_mipmap_anisotropic;
uniform sampler2D detail : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D detail_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float detail_m = 2.0;       // velikost fotky detailu v metrech
uniform float detail_prumer = 0.3;  // prumerny jas fotky (aby detail neztmavil/nezesvetlil skalu)

varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 b = pow(abs(normalize(wn)), vec3(4.0));
	b /= (b.x + b.y + b.z);
	vec3 dx = texture(detail, wp.zy / detail_m, ab_mip).rgb;
	vec3 dy = texture(detail, wp.xz / detail_m, ab_mip).rgb;
	vec3 dz = texture(detail, wp.xy / detail_m, ab_mip).rgb;
	float l = dot(dx * b.x + dy * b.y + dz * b.z, vec3(0.3, 0.5, 0.2));
	float zbl = 1.0 - smoothstep(25.0, 60.0, length(CAMERA_POSITION_WORLD - wp));
	vec3 c = texture(barva, UV, ab_mip).rgb;
	ALBEDO = c * mix(1.0, clamp(l / detail_prumer, 0.5, 1.6), 0.7 * zbl);
	vec3 nb = texture(normala, UV, ab_mip).rgb;
	vec3 nd = texture(detail_n, (abs(wn.y) > 0.7 ? wp.xz : (abs(wn.x) > abs(wn.z) ? wp.zy : wp.xy)) / detail_m, ab_mip).rgb;
	NORMAL_MAP = normalize(mix(nb, nd, 0.4 * zbl) * 2.0 - 1.0) * 0.5 + 0.5;
	ROUGHNESS = 0.92;
	SPECULAR = 0.3;
}
