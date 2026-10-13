shader_type spatial;
// Hladina rybnika a prikopu: dve posouvane normalove mapy a obcasne kruhove vlnky (zaba, ryba, kapka).

uniform sampler2D nmap : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec3 deep : source_color = vec3(0.02, 0.05, 0.05);
uniform vec4 rip[4];          // x, z, cas vzniku (sekundy, stejne jako TIME), sila

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = wpos.xz * 0.09;
	vec3 n1 = texture(nmap, uv + TIME * vec2(0.011, 0.006)).rgb;
	vec3 n2 = texture(nmap, uv * 1.7 - TIME * vec2(0.008, 0.012)).rgb;
	vec3 nm = mix(n1, n2, 0.5);
	// kruhove vlnky: nekolik soustrednych hrebenu, rozbihaji se a slabnou
	vec2 g = vec2(0.0);
	for (int i = 0; i < 4; i++) {
		float age = TIME - rip[i].z;
		if (age > 0.0 && age < 4.0 && rip[i].w > 0.0) {
			vec2 d = wpos.xz - rip[i].xy;
			float r = length(d) + 1e-4;
			float front = age * 0.5;
			float x = r - front;
			float env = exp(-x * x * 9.0) * (1.0 - age / 4.0) * rip[i].w;
			g += (d / r) * cos(x * 30.0) * env;
		}
	}
	nm.xy += g * 0.35;
	NORMAL_MAP = nm;
	NORMAL_MAP_DEPTH = 0.55;
	ALBEDO = deep;
	ROUGHNESS = 0.05;
	SPECULAR = 0.9;
	METALLIC = 0.0;
}
