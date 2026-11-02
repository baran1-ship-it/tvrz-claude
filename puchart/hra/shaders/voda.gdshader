// Potoky (blender/voda.py): bez kopie obrazovky a bez textur (Adreno), proud po UV.x (m po proudu), UV.y 0..1 napříč.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, specular_schlick_ggx;
uniform vec3 barva_hluboka : source_color = vec3(0.10, 0.13, 0.11);
uniform vec3 barva_melka : source_color = vec3(0.30, 0.30, 0.24);
uniform float rychlost = 0.6;
float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float sum(vec2 p) {
	vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h2(i), h2(i + vec2(1, 0)), f.x), mix(h2(i + vec2(0, 1)), h2(i + vec2(1, 1)), f.x), f.y);
}
void fragment() {
	float v = UV.y, okr = smoothstep(0.0, 0.22, v) * smoothstep(1.0, 0.78, v);
	vec2 p = vec2(UV.x - TIME * rychlost, v * 3.0);
	float a = sum(p * vec2(1.3, 2.0)), b = sum(p * vec2(3.1, 5.0) + 7.0);
	NORMAL_MAP = normalize(vec3((a - 0.5) * 0.5 + (b - 0.5) * 0.3, (b - 0.5) * 0.4, 1.0)) * 0.5 + 0.5;
	ALBEDO = mix(barva_melka, barva_hluboka, okr) + vec3(smoothstep(0.78, 0.95, b) * 0.12 * okr);
	ROUGHNESS = 0.08; METALLIC = 0.0; SPECULAR = 0.5;
	ALPHA = okr * 0.88;
}
