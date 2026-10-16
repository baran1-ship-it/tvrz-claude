shader_type spatial;
// Trs travy ze skutecnych stebel (zkusebni louka): barva z vrcholu (dole tmava, spicka svetla, kazde steblo
// jiny odstin), vitr podle vysky, proti slunci prosvita. Normaly mirne nahoru - mekke svetlo jako louka.
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;

uniform float vitr = 1.0;
// prolinani podle vzdalenosti trsu od kamery (renderer compatibility na Androidu neumi fade viditelnosti):
// od < 0 = bez nabehu; ve vzdalenosti [od, od + 12] se trs postupne objevi, [do - 14, do] postupne zmizi
uniform float fade_od = -1.0;
uniform float fade_do = 100000.0;

varying float vyska;
varying float viditelnost;
varying vec4 ic;           // MultiMesh custom: r = suchost (zluta trava), g = odstin, a = 1 pokud se pouziva

void vertex() {
	vyska = UV.y;
	ic = INSTANCE_CUSTOM;                                   // 0 pata, 1 spicka
	vec3 w = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float dist = distance(w, INV_VIEW_MATRIX[3].xyz);
	viditelnost = 1.0 - smoothstep(fade_do - 14.0, fade_do, dist);
	if (fade_od >= 0.0) {
		viditelnost *= smoothstep(fade_od, fade_od + 12.0, dist);
	}
	float t = TIME * 1.6 + w.x * 0.21 + w.z * 0.17;
	float k = vyska * vyska * 0.09 * vitr;
	VERTEX.x += (sin(t) * 0.7 + sin(t * 2.3 + w.z) * 0.3) * k;
	VERTEX.z += cos(t * 0.8 + w.x) * k * 0.6;
	NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.6));
}

void fragment() {
	// rozpad po pixelech (Bayer 4x4) misto pruhlednosti
	ivec2 fc = ivec2(FRAGCOORD.xy) % 4;
	int idx = fc.x + fc.y * 4;
	float bayer[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	if (viditelnost < (bayer[idx] + 0.5) / 16.0) {
		discard;
	}
	vec3 barva = COLOR.rgb;
	if (ic.a > 0.5) {
		float l = dot(barva, vec3(0.3, 0.5, 0.2));
		barva = mix(barva, vec3(l * 1.5, l * 1.3, l * 0.55), ic.r);
		barva *= 0.88 + 0.24 * ic.g;
	}
	ALBEDO = barva;
	// obe strany stebla svetle jako louka: Godot u rubu otaci normalu (dolu = cerna trava), tak ji vratit
	// a priklonit nahoru (ve view prostoru)
	vec3 n = FRONT_FACING ? NORMAL : -NORMAL;
	NORMAL = normalize(mix(n, (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz, 0.5));
	AO = mix(0.6, 1.0, vyska);                      // u zeme stinne (mezi stebly)
	ROUGHNESS = 0.9;
	BACKLIGHT = COLOR.rgb * vec3(0.9, 1.0, 0.6) * (0.25 + 0.5 * vyska);
}
