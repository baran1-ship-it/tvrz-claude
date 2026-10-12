shader_type spatial;
// Stojata voda v prikopu: tmava zelenohneda, leskla, s okrehkem a sinicemi.
render_mode specular_schlick_ggx;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;

varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wp.xz;
	float n1 = texture(sum, p * 0.04).r;
	float n2 = texture(sum, p * 0.2 + 0.4).r;
	float weed = smoothstep(0.62, 0.68, n1 + (n2 - 0.5) * 0.3);
	float ripple = texture(sum, p * 0.9 + TIME * vec2(0.01, 0.006)).r;
	vec3 w = mix(vec3(0.01, 0.014, 0.006), vec3(0.025, 0.03, 0.012), n2);
	vec3 d = mix(vec3(0.07, 0.14, 0.02), vec3(0.16, 0.22, 0.04), n2);
	ALBEDO = mix(w, d, weed);
	ROUGHNESS = mix(0.06, 0.55, weed);
	SPECULAR = mix(0.5, 0.2, weed);
	NORMAL_MAP = vec3(0.5 + (ripple - 0.5) * 0.12, 0.5 + (n2 - 0.5) * 0.08, 1.0);
}
