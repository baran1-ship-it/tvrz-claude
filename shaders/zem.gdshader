shader_type spatial;
// Udusana hlina se sterkem a trava; mira travy je v zelene slozce barvy vrcholu.
uniform sampler2D hlina_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D hlina_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D trava_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D trava_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform float hlina_m = 2.17;
uniform float trava_m = 1.4;

varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wp.xz;
	float n1 = texture(sum, p * 0.03).r;
	float gm = smoothstep(0.35, 0.6, COLOR.g * 0.9 + (n1 - 0.5) * 0.8);
	vec3 h = texture(hlina_a, p / hlina_m).rgb * vec3(0.85, 0.8, 0.72);
	vec3 tr = texture(trava_a, p / trava_m).rgb * vec3(0.5, 0.68, 0.3);
	ALBEDO = mix(h, tr, gm);
	ROUGHNESS = 0.95;
	vec3 nh = texture(hlina_n, p / hlina_m).rgb;
	vec3 nt = texture(trava_n, p / trava_m).rgb;
	NORMAL_MAP = mix(nh, nt, gm);
}
