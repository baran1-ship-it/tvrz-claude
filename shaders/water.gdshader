shader_type spatial;
// Hladina rybnika: dve posouvane normalove mapy.

uniform sampler2D nmap : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec3 deep : source_color = vec3(0.02, 0.05, 0.05);

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = wpos.xz * 0.09;
	vec3 n1 = texture(nmap, uv + TIME * vec2(0.011, 0.006)).rgb;
	vec3 n2 = texture(nmap, uv * 1.7 - TIME * vec2(0.008, 0.012)).rgb;
	NORMAL_MAP = mix(n1, n2, 0.5);
	NORMAL_MAP_DEPTH = 0.55;
	ALBEDO = deep;
	ROUGHNESS = 0.05;
	SPECULAR = 0.9;
	METALLIC = 0.0;
}
