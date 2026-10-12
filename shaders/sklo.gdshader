shader_type spatial;
// Olovene sklo: terciky v olove nebo kosoctverecne tabulky.
render_mode blend_mix, cull_disabled;
uniform bool terce = true;

void fragment() {
	vec2 uv = UV;
	float lead;
	float ring;
	if (terce) {
		vec2 c = fract(uv / 0.085) - 0.5;
		float d = length(c) * 2.0;
		lead = smoothstep(0.82, 0.94, d);
		ring = smoothstep(0.0, 0.84, d);
	} else {
		float a = fract((uv.x + uv.y) / 0.12);
		float b2 = fract((uv.x - uv.y) / 0.12);
		lead = max(smoothstep(0.44, 0.48, abs(a - 0.5)), smoothstep(0.44, 0.48, abs(b2 - 0.5)));
		ring = abs(a - 0.5);
	}
	vec3 g = mix(vec3(0.55, 0.62, 0.42), vec3(0.32, 0.38, 0.22), ring);
	ALBEDO = mix(g, vec3(0.05), lead);
	METALLIC = lead * 0.8;
	ROUGHNESS = mix(0.12, 0.5, lead);
	ALPHA = mix(0.45, 1.0, lead);
}
