shader_type spatial;
// Udusana hlina se sterkem a trava; mira travy je v zelene slozce barvy vrcholu.
uniform sampler2D hlina_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D hlina_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D trava_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D trava_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform float hlina_m = 2.17;
uniform float trava_m = 1.4;

varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wp.xz;
	float n1 = texture(sum, p * 0.03).r;
	float gm = smoothstep(0.35, 0.6, COLOR.g * 0.9 + (n1 - 0.5) * 0.8);
	vec3 h = texture(hlina_a, p / hlina_m).rgb * vec3(0.85, 0.8, 0.72);
	// proti opakovani dlazdic: dve meritka travy a velke skvrny (sussi zlutava / syta / tmava trava)
	vec3 tr = mix(texture(trava_a, p / trava_m).rgb, texture(trava_a, p / (trava_m * 3.7) + 0.37).rgb, 0.45) * vec3(0.5, 0.68, 0.3);
	float m1 = texture(sum, p * 0.0071).r;
	float m2 = texture(sum, p * 0.019 + 0.5).r;
	tr *= mix(vec3(0.78, 0.86, 0.7), vec3(1.18, 1.08, 0.82), smoothstep(0.35, 0.7, m1));
	tr *= 0.82 + 0.36 * m2;
	// v dalce se textura travy rozmaze do svetle sede; ztmavit a nasytit jako louka z dalky
	float dd = length(VERTEX);
	tr = mix(tr, vec3(0.13, 0.2, 0.06) * (0.8 + 0.4 * n1), smoothstep(25.0, 140.0, dd));
	vec3 col = mix(h, tr, gm);
	// pole v lanech (cervena = plodina): psenice, oves, uhor, len; jemne brazdy
	float pole = COLOR.r;
	if (pole > 0.05) {
		float c = floor(pole * 4.0 + 0.5);
		vec3 crop = c < 1.5 ? vec3(0.5, 0.44, 0.24) : (c < 2.5 ? vec3(0.3, 0.36, 0.15) : (c < 3.5 ? vec3(0.3, 0.25, 0.17) : vec3(0.38, 0.42, 0.2)));
		crop = mix(crop, tr, 0.25) * (0.8 + 0.4 * texture(sum, p * 0.05).r);
		float br = 0.93 + 0.07 * sin((p.x * 0.6 + p.y * 0.8) * 5.0);
		col = mix(col, crop * br * (0.85 + 0.3 * n1), smoothstep(0.05, 0.2, pole));
	}
	// les (modra): jehlici a mech pod stromy, z dalky tmave koruny
	float les = COLOR.b;
	if (les > 0.01) {
		float dist = dd;
		vec3 dno = mix(vec3(0.16, 0.12, 0.07), vec3(0.12, 0.15, 0.06), n1) * (0.8 + 0.4 * texture(sum, p * 0.21).r);
		vec3 koruny = mix(vec3(0.05, 0.09, 0.04), vec3(0.09, 0.13, 0.06), texture(sum, p * 0.05).r);
		vec3 lc = mix(dno, koruny, smoothstep(160.0, 320.0, dist));
		col = mix(col, lc, les);
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	vec3 nh = texture(hlina_n, p / hlina_m).rgb;
	vec3 nt = texture(trava_n, p / trava_m).rgb;
	NORMAL_MAP = mix(nh, nt, gm);
}
