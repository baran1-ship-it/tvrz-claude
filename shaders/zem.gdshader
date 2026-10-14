shader_type spatial;
// Udusana hlina se sterkem a trava; mira travy je v zelene slozce barvy vrcholu.
uniform sampler2D hlina_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D hlina_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D trava_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D trava_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform float hlina_m = 2.17;
uniform float trava_m = 1.4;
uniform vec2 ves = vec2(470.0, 830.0);     // stred navsi (lany poli vybihaji od ni)

const float HON = 125.0;

varying vec3 wp;

uint uhash(uint v) {
	v ^= v >> 16u;
	v *= 0x7FEB352Du;
	v ^= v >> 15u;
	v *= 0x846CA68Bu;
	v ^= v >> 16u;
	return v;
}

uint cell_hash(int ci, int cj) {
	return uhash((uint(ci + 1000) * 73856093u) ^ (uint(cj + 1000) * 19349663u));
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = wp.xz;
	float n1 = texture(sum, p * 0.03).r;
	float nf = texture(sum, p * 0.13 + 0.21).r;
	float gm = smoothstep(0.35, 0.6, COLOR.g * 0.9 + (n1 - 0.5) * 0.8 + (nf - 0.5) * 0.45);
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
	// pole: oblast poli z barvy vrcholu (rozmazana nepravidelnym okrajem), lany a plodiny pocitane tady,
	// hranice lanu zvlnene, mezi lany travnata mez
	float pm = smoothstep(0.3, 0.6, COLOR.r + (texture(sum, p * 0.035 + 0.6).r - 0.5) * 0.5 + (nf - 0.5) * 0.25);
	if (pm > 0.0) {
		// hony (Voronoi bloky jako v blender/kraj.py hon()): kazdy ma lany jinym smerem a jinak siroke
		vec2 wq = p;
		ivec2 g = ivec2(floor(wq / HON));
		float d1 = 1e9;
		float d2 = 1e9;
		uint hb = 0u;
		for (int i = -1; i <= 1; i++) {
			for (int j = -1; j <= 1; j++) {
				ivec2 cc = g + ivec2(i, j);
				uint h = cell_hash(cc.x, cc.y);
				vec2 sd = (vec2(cc) + 0.15 + 0.7 * vec2(float(h & 65535u), float(h >> 16u)) / 65535.0) * HON;
				float dq = length(wq - sd);
				if (dq < d1) { d2 = d1; d1 = dq; hb = h; } else if (dq < d2) { d2 = dq; }
			}
		}
		float edge = (d2 - d1) * 0.5;
		uint h2 = uhash(hb ^ 0x9E3779B9u);
		float ang = float(h2 & 65535u) / 65535.0 * 3.14159265;
		float w = 9.0 + 9.0 * float(h2 >> 16u) / 65535.0;
		vec2 nn = vec2(-sin(ang), cos(ang));
		float t = dot(p, nn) / w + (texture(sum, p * 0.011 + 0.3).r - 0.5) * 0.35;
		float n = floor(t);
		float f = fract(t);
		uint cr = uhash(hb ^ (uint(int(n)) * 2654435761u)) % 4u;
		vec3 crop = cr == 0u ? vec3(0.5, 0.44, 0.24) : (cr == 1u ? vec3(0.3, 0.36, 0.15) : (cr == 2u ? vec3(0.3, 0.25, 0.17) : vec3(0.38, 0.42, 0.2)));
		crop = mix(crop, tr, 0.25) * (0.8 + 0.4 * texture(sum, p * 0.05).r);
		// brazdy podel lanu
		float br = 0.92 + 0.08 * sin(dot(p, nn) * 6.0);
		float mez = 1.0 - smoothstep(0.03, 0.09, f) * (1.0 - smoothstep(0.97, 0.995, f));
		mez = max(mez, 1.0 - smoothstep(2.0, 3.5, edge));          // mez mezi hony
		vec3 pc = mix(crop * br * (0.85 + 0.3 * n1), tr, mez);
		col = mix(col, pc, pm);
	}
	// les (modra): jehlici a mech pod stromy, z dalky tmave koruny
	float les = COLOR.b;
	if (les > 0.001) {
		float dist = dd;
		vec3 dno = mix(vec3(0.16, 0.12, 0.07), vec3(0.12, 0.15, 0.06), n1) * (0.8 + 0.4 * texture(sum, p * 0.21).r);
		vec3 koruny = mix(vec3(0.05, 0.09, 0.04), vec3(0.09, 0.13, 0.06), texture(sum, p * 0.05).r);
		vec3 lc = mix(dno, koruny, smoothstep(160.0, 320.0, dist));
		float lm = smoothstep(0.25, 0.75, les + (texture(sum, p * 0.04 + 0.3).r - 0.5) * 0.7 + (nf - 0.5) * 0.3);
		col = mix(col, lc, lm);
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	vec3 nh = texture(hlina_n, p / hlina_m).rgb;
	vec3 nt = texture(trava_n, p / trava_m).rgb;
	NORMAL_MAP = mix(nh, nt, gm);
}
