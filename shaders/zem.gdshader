shader_type spatial;
// Udusana hlina se sterkem a trava; mira travy je v zelene slozce barvy vrcholu.
uniform sampler2D hlina_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D hlina_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D louka_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D louka_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D letecky_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D louka_dal_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D obili_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D oranice_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
// povrchy podle stanoviste (radce 07:50 bod 1): pole textur 0 hrabanka s mechem, 1 listi, 2 jehlici, 3 pisek s jehlicim,
// 4 udusana pesina; maska stanoviste (svet.gd _stanoviste): R jehlicnate, G listnate stromy, B skaly, A pesina
uniform sampler2DArray pudy_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray pudy_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float pudy_k[5];
uniform float pudy_m = 2.2;
uniform sampler2D stanoviste : filter_linear, repeat_disable;
uniform vec4 stan_rect = vec4(-250.0, -250.0, 1152.0, 1602.0);
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
// zrno travy (radce 07:30 C, tools/zrno_travy.py): RGB normala, A jas ~0,5 - stejna frekvence jako trsy, aby
// prechod trs -> teren nebyl videt; blizko dlazdice 0,8 m, v dalce 5 m (stejny vzor, mensi)
uniform sampler2D zrno : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float zrno_m = 0.8;
uniform float hlina_m = 2.17;
uniform float louka_m = 2.0;       // skutecne rozmery fotek v metrech (Poly Haven)
uniform float letecky_m = 15.0;
uniform float louka_dal_m = 2.0;
// kalibrace odrazivosti fotek (cil / prumer fotky), nastavuje svet.gd z modely/textury/albedo.json
uniform float hlina_k = 1.0;
uniform vec3 louka_k = vec3(1.0);       // po kanalech: podklad = barva atlasu travy
uniform vec3 louka_dal_k = vec3(1.0);
uniform float obili_k = 1.0;
uniform float oranice_k = 1.0;
uniform float obili_m = 2.0;
uniform float oranice_m = 3.0;
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
	// sum dela nepravidelny okraj cest a dvoru; uprostred louky (g ~0,85) skoro nepusobi - jinak tam vyhravala hlina
	// a mezi trsy stredniho pasma byla hnedosedá zem (radce 04:55)
	float gn = ((n1 - 0.5) * 0.8 + (nf - 0.5) * 0.45) * (1.0 - 0.7 * smoothstep(0.55, 0.85, COLOR.g));
	float gm = smoothstep(0.35, 0.6, COLOR.g * 0.9 + gn);
	vec3 h = texture(hlina_a, p / hlina_m).rgb * hlina_k;
	// louka: fotka zelene louky ve skutecnem meritku (ambientCG Grass004, 2 m); velke svetlejsi a tmavsi
	// skvrny z jasu leteckeho snimku louky (15 m); v dalce stejnorodejsi tmavsi travnik (Grass001) -
	// porad fotografie, ne plocha barva
	float dd = length(VERTEX);
	vec3 lt = texture(letecky_a, p / letecky_m).rgb;
	float lum_l = dot(lt, vec3(0.3, 0.5, 0.2));
	vec3 tr = texture(louka_a, p / louka_m).rgb * louka_k;
	vec3 trd = texture(louka_dal_a, p / (louka_dal_m * 4.0)).rgb * louka_dal_k;
	tr = mix(tr, trd, smoothstep(40.0, 140.0, dd));
	tr *= clamp(0.8 + 0.4 * lum_l / 0.35, 0.7, 1.15);     // LDR: nad 1,15 prepal (bily obzor)
	// zrno trsu: blizko 0,8 m, od 25 m vetsi dlazdice (jinak by se v mipmapach slilo do plochy)
	float zd = smoothstep(15.0, 45.0, dd);
	vec4 zr = mix(texture(zrno, p / zrno_m), texture(zrno, p / (zrno_m * 6.0) + 0.37), zd);
	tr *= mix(1.0, 0.55 + zr.a * 0.9, 0.55);
	// makro skvrny 20-50 m: svetlejsi zlutozelene a tmavsi syte (KCD2: louka neni jednobarevna)
	float mk = texture(sum, p * 0.022 + 0.71).r * 0.65 + texture(sum, p * 0.05 + 0.13).r * 0.35;
	tr *= mix(vec3(0.84, 0.86, 0.80), vec3(1.10, 1.08, 0.94), smoothstep(0.3, 0.7, mk));
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
		// plodina z fotek (lany): obili/strniste, oranice/uhor, zelena plodina (husty travnik), jetel (louka)
		vec2 lp = vec2(dot(p, vec2(nn.y, -nn.x)), dot(p, nn));           // UV podel lanu
		vec3 crop = cr == 0u ? texture(obili_a, lp / obili_m).rgb * obili_k
				: (cr == 2u ? texture(oranice_a, lp / oranice_m).rgb * oranice_k
				: (cr == 1u ? texture(louka_dal_a, lp / louka_dal_m).rgb * louka_dal_k : texture(louka_a, lp / louka_m).rgb * louka_k));
		// brazdy podel lanu
		float br = 0.92 + 0.08 * sin(dot(p, nn) * 6.0);
		float mez = 1.0 - smoothstep(0.03, 0.09, f) * (1.0 - smoothstep(0.97, 0.995, f));
		mez = max(mez, 1.0 - smoothstep(2.0, 3.5, edge));          // mez mezi hony
		vec3 pc = mix(crop * br * (0.85 + 0.3 * n1), tr, mez);
		col = mix(col, pc, pm);
	}
	// les (modra): povrch podle stanoviste - listnaty les opad listi, bor jehlici, na piskovci pisek s jehlicim,
	// mech na severnich svazich a u skal; prechody sumem 2-4 m
	vec4 st = texture(stanoviste, (p - stan_rect.xy) / stan_rect.zw);
	float n3 = texture(sum, p * 0.3 + 0.17).r;
	// pod korunami opad / jehlici i tam, kde mapa lesa z Blenderu les nema (dub na louce, lipy u vsi) - radce 11:00
	float les = max(COLOR.b, smoothstep(0.35, 0.95, st.r + st.g));
	vec3 nl = vec3(0.5, 0.5, 1.0);
	float lm = 0.0;
	vec2 up = p / pudy_m;
	if (les > 0.001) {
		float jehl = smoothstep(0.35, 0.65, st.r / (st.r + st.g + 0.08) + (n3 - 0.5) * 0.35);
		float skal = smoothstep(0.25, 0.6, st.b + (nf - 0.5) * 0.3) * jehl;
		vec3 wn = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
		float mech = smoothstep(0.55, 0.8, (-wn.z * 0.6 + st.b * 0.5 + (n1 - 0.5) * 0.8) * 0.7 + n3 * 0.3);
		vec3 lc = mix(texture(pudy_a, vec3(up, 1.0)).rgb * pudy_k[1], texture(pudy_a, vec3(up, 2.0)).rgb * pudy_k[2], jehl);
		lc = mix(lc, texture(pudy_a, vec3(up, 3.0)).rgb * pudy_k[3], skal);
		lc = mix(lc, texture(pudy_a, vec3(up * 1.3, 0.0)).rgb * pudy_k[0], mech);
		vec3 ln = mix(texture(pudy_n, vec3(up, 1.0)).rgb, texture(pudy_n, vec3(up, 2.0)).rgb, jehl);
		nl = mix(ln, texture(pudy_n, vec3(up * 1.3, 0.0)).rgb, mech);
		lm = smoothstep(0.25, 0.75, les + (texture(sum, p * 0.04 + 0.3).r - 0.5) * 0.7 + (nf - 0.5) * 0.3);
		col = mix(col, lc, lm);
	}
	// pesina: udusana hlina (v lese s listim), okraj zubaty sumem
	float pes = smoothstep(0.35, 0.6, st.a + (n3 - 0.5) * 0.35 + (nf - 0.5) * 0.2);
	if (pes > 0.0) {
		vec3 pc = mix(h, texture(pudy_a, vec3(up, 4.0)).rgb * pudy_k[4], 0.4 + 0.6 * lm);
		col = mix(col, pc, pes * (1.0 - pm * 0.7));
		nl = mix(nl, texture(pudy_n, vec3(up, 4.0)).rgb, pes);
		lm = max(lm, pes);
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	vec3 nh = texture(hlina_n, p / hlina_m).rgb;
	vec3 nt = mix(texture(louka_n, p / louka_m).rgb, zr.rgb, 0.6);
	NORMAL_MAP = mix(mix(nh, nt, gm), nl, lm);
}
