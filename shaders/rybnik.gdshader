shader_type spatial;
// Stojata voda v prikopu: tmava zelenohneda, leskla, s okrehkem a sinicemi.
render_mode specular_schlick_ggx;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform float tekouci = 0.0;      // potok: UV.x = delka po proudu (m/4), vlnky a pena tecou

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
	if (tekouci > 0.5) {
		// tekouci voda: dve vrstvy vlnek unasenych proudem (~0.8 m/s), pena v proudnici, bez okrehku
		vec2 q1 = vec2(UV.x * 1.6 - TIME * 0.8, UV.y * 2.2);
		vec2 q2 = vec2(UV.x * 3.1 - TIME * 1.3, UV.y * 3.7 + 0.37);
		float a1 = texture(sum, q1 * 0.5).r;
		float a2 = texture(sum, q2 * 0.5).r;
		float pena = smoothstep(0.68, 0.8, a1 * 0.6 + a2 * 0.5) * (1.0 - smoothstep(0.3, 1.2, UV.y));
		vec3 cista = mix(vec3(0.03, 0.04, 0.03), vec3(0.08, 0.08, 0.05), n2);
		ALBEDO = mix(cista, vec3(0.55, 0.57, 0.52), pena * 0.6);
		ROUGHNESS = mix(0.04, 0.4, pena);
		SPECULAR = 0.5;
		NORMAL_MAP = vec3(0.5 + (a1 - 0.5) * 0.45, 0.5 + (a2 - 0.5) * 0.45, 1.0);
	} else {
		ALBEDO = mix(w, d, weed);
		ROUGHNESS = mix(0.06, 0.55, weed);
		SPECULAR = mix(0.5, 0.2, weed);
		NORMAL_MAP = vec3(0.5 + (ripple - 0.5) * 0.12, 0.5 + (n2 - 0.5) * 0.08, 1.0);
	}
}
