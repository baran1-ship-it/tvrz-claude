shader_type spatial;
// Trs travy ze skutecnych stebel (zkusebni louka): barva z vrcholu (dole tmava, spicka svetla, kazde steblo
// jiny odstin), vitr podle vysky, proti slunci prosvita. Normaly mirne nahoru - mekke svetlo jako louka.
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;

uniform float vitr = 1.0;

varying float vyska;

void vertex() {
	vyska = UV.y;                                   // 0 pata, 1 spicka
	vec3 w = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float t = TIME * 1.6 + w.x * 0.21 + w.z * 0.17;
	float k = vyska * vyska * 0.09 * vitr;
	VERTEX.x += (sin(t) * 0.7 + sin(t * 2.3 + w.z) * 0.3) * k;
	VERTEX.z += cos(t * 0.8 + w.x) * k * 0.6;
	NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.6));
}

void fragment() {
	ALBEDO = COLOR.rgb;
	AO = mix(0.35, 1.0, vyska);                     // u zeme stinne (mezi stebly)
	ROUGHNESS = 0.9;
	BACKLIGHT = COLOR.rgb * vec3(0.9, 1.0, 0.6) * (0.25 + 0.5 * vyska);
}
