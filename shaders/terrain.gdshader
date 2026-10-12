shader_type spatial;
// Teren: michani travy, hliny a dlazby podle barvy vrcholu (R, G, B). Alfa < 1 = pole (zlutavy odstin).

uniform sampler2D grass_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D grass_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D dirt_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D dirt_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D cobble_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D cobble_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D macro_tex : filter_linear_mipmap, repeat_enable;
uniform vec3 field_color : source_color = vec3(0.62, 0.52, 0.26);

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 t = normalize(vec3(1.0, 0.0, 0.0) - NORMAL * NORMAL.x);
	TANGENT = t;
	BINORMAL = normalize(cross(NORMAL, t));
}

void fragment() {
	vec2 uv = wpos.xz;
	vec3 w = max(COLOR.rgb, vec3(0.0));
	float shade = clamp(w.r + w.g + w.b, 0.0, 1.0);
	// ostrejsi prechody mezi vrstvami
	w = w * w;
	w /= (w.r + w.g + w.b + 0.0001);
	vec3 ga = texture(grass_a, uv / 3.0).rgb;
	float macro = texture(macro_tex, uv / 63.0).r;
	float macro2 = texture(macro_tex, uv / 211.0 + vec2(0.37, 0.11)).r;
	ga *= 0.72 + 0.6 * macro;
	ga = mix(ga, ga * vec3(1.22, 1.1, 0.74), smoothstep(0.45, 0.8, macro2));
	vec3 da = texture(dirt_a, uv / 3.0).rgb * (0.78 + 0.4 * macro);
	vec3 ca = texture(cobble_a, uv / 3.0).rgb;
	vec3 alb = ga * w.r + da * w.g + ca * w.b;
	float field = 1.0 - COLOR.a;
	float lum = dot(alb, vec3(0.3, 0.5, 0.2));
	alb = mix(alb, field_color * (0.5 + 1.6 * lum), field);
	ALBEDO = alb * mix(0.42, 1.0, shade);
	vec3 nm = texture(grass_n, uv / 3.0).rgb * w.r + texture(dirt_n, uv / 3.0).rgb * w.g + texture(cobble_n, uv / 3.0).rgb * w.b;
	NORMAL_MAP = nm;
	NORMAL_MAP_DEPTH = 1.0;
	ROUGHNESS = mix(0.93, 0.82, w.b);
	SPECULAR = 0.25;
}
