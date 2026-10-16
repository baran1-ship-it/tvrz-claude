shader_type spatial;
// Kvety louky v jednom MultiMeshi: atlas 4 barev (512x128), barvu vybira INSTANCE_CUSTOM.r (0, .25, .5, .75).
// Prolinani podle vzdalenosti jako u stebel (renderer compatibility neumi fade viditelnosti).
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;

uniform sampler2D atlas : source_color, filter_linear_mipmap;
uniform float fade_od = -1.0;
uniform float fade_do = 100000.0;

varying float posun;
varying float viditelnost;

void vertex() {
	posun = INSTANCE_CUSTOM.r;
	vec3 w = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float dist = distance(w, INV_VIEW_MATRIX[3].xyz);
	viditelnost = 1.0 - smoothstep(fade_do - 10.0, fade_do, dist);
	float t = TIME * 1.6 + w.x * 0.21 + w.z * 0.17;
	VERTEX.x += sin(t) * (1.0 - UV.y) * 0.03;
}

void fragment() {
	ivec2 fc = ivec2(FRAGCOORD.xy) % 4;
	float bayer[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	if (viditelnost < (bayer[fc.x + fc.y * 4] + 0.5) / 16.0) {
		discard;
	}
	vec4 c = texture(atlas, vec2(posun + UV.x * 0.25, UV.y));
	if (c.a < 0.5) {
		discard;
	}
	ALBEDO = c.rgb;
	ROUGHNESS = 0.9;
	BACKLIGHT = c.rgb * 0.25;
}
