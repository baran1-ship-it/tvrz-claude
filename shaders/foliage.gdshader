shader_type spatial;
render_mode cull_disabled;
// Listi a vetve z karet s pruhlednosti. Barva vrcholu: RGB odstin, A = jak moc se kyve ve vetru.

uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float alpha_cut = 0.38;
uniform vec3 tint : source_color = vec3(1.0);
uniform float sway = 0.06;
uniform vec3 back : source_color = vec3(0.22, 0.3, 0.08);

varying float tone;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float ph = wp.x * 0.23 + wp.z * 0.19;
	float k = COLOR.a * sway;
	VERTEX.x += sin(TIME * 1.3 + ph) * k;
	VERTEX.z += cos(TIME * 1.07 + ph * 1.3) * k;
	VERTEX.y += sin(TIME * 1.9 + ph * 2.1) * k * 0.35;
	tone = fract(sin(dot(MODEL_MATRIX[3].xz, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec4 t = texture(tex, UV);
	ALBEDO = t.rgb * COLOR.rgb * tint * mix(0.78, 1.16, tone);
	ALPHA = t.a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cut;
	ROUGHNESS = 0.82;
	SPECULAR = 0.15;
	BACKLIGHT = back;
	// karty maji normaly mirici ven z koruny; zadni strana se nema prevracet
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}
