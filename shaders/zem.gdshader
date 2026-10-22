shader_type spatial;
#include "res://shaders/barva_krajiny.gdshaderinc"
// Udusana hlina (cesty, dvory, pesiny - bez sterku) a trava; mira travy je v zelene slozce barvy vrcholu.
uniform sampler2D hlina_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D hlina_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D louka_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D louka_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D letecky_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D louka_dal_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D obili_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D oranice_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
// povrchy podle stanoviste (radce 07:50 bod 1): pole textur 0 udusana pesina (nepouzita), 1 listi, 2 jehlici, 3 pisek s jehlicim,
// 4 hrabanka s mechem; maska stanoviste (svet.gd _stanoviste): R jehlicnate, G listnate stromy, B skaly, A pesina
uniform sampler2DArray pudy_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray pudy_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float pudy_k[9];
uniform float pudy_m = 2.2;
// dno a breh potoka (COLOR.a < 1, scripts/koryto.gd): obazky z pole textur (vrstva 5); 6 bahno; 7 skala na strminach
// (kamen s lisejnikem, triplanarne - na svahu nad ~37 st. se fotka shora natahovala do pruhu, hlaseni 0.54 bod 4)
uniform sampler2D stanoviste : filter_linear, repeat_disable;
uniform vec4 stan_rect = vec4(-250.0, -250.0, 1152.0, 1602.0);
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
// zrno travy (radce 07:30 C, tools/zrno_travy.py): RGB normala, A jas ~0,5 - stejna frekvence jako trsy, aby
// prechod trs -> teren nebyl videt; blizko dlazdice 0,8 m, v dalce 5 m (stejny vzor, mensi)
uniform sampler2D zrno : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float zrno_m = 0.8;
// barevna mapa krajiny v dalce (radce 11:20): kopec v 300 m ma barvu toho, co na nem je - louka barvu trsu,
// les tmavou zelen korun (ne opad pod nimi), pole sve; bez bledych fotek
uniform vec3 barva_louky = vec3(0.08, 0.10, 0.02);
uniform vec3 barva_lesa = vec3(0.040, 0.070, 0.024);
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
// pesina: stanoviste.a = 0,5 + znamenkova vzdalenost od osy / 6 m (svet.gd); hodnoty v uzlech mrizky stan_k (2 m),
// texel i ma stred o pul kroku dal - posun o pul texelu. Zadny dalsi vzorkovac: na Adrenu jich material ma jen 13.
uniform float stan_k = 2.0;
// osa navsi (blender/vesnice.py AXIS = atan2(0,85; 1)) a hlavni cesta ves_paths: v = 2,5 sin(u/23) + 1,2 sin(u/9 + 1)
const vec2 VES_AU = vec2(0.76193, 0.64764);
const vec2 VES_AV = vec2(-0.64764, 0.76193);

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
	// okraj hliny (cesty, dvory) zubaty i v metru (jemny sum), ne rovna hrana do louky
	float nj = texture(sum, p * 0.9 + 0.43).r;
	gn += (nj - 0.5) * 0.35 * (1.0 - smoothstep(0.55, 0.85, COLOR.g));
	float gm = smoothstep(0.35, 0.6, COLOR.g * 0.9 + gn);
	vec3 h = texture(hlina_a, p / hlina_m).rgb * hlina_k * mix(0.82, 1.12, nf);     // vlhci a sussi mista
	vec3 nh = texture(hlina_n, p / hlina_m).rgb;
	float vlh = 0.0;
	// cesta navsi (hlaseni 0.54 bod 3): hlina, dve koleje 1,4 m od sebe (tmavsi, vlhci), mezi nimi zbytky travy,
	// okraj zubaty do louky (~4 m); kde je ves podle barvy vrcholu hlinena a blizko osy hlavni cesty
	vec2 vq = p - ves;
	float vu = dot(vq, VES_AU);
	if (gm < 0.98 && abs(vu + 11.0) < 86.0) {
		float c0 = 2.5 * sin(vu / 23.0) + 1.2 * sin(vu / 9.0 + 1.0);
		float d0 = 2.5 / 23.0 * cos(vu / 23.0) + 1.2 / 9.0 * cos(vu / 9.0 + 1.0);
		float lat = abs(dot(vq, VES_AV) - c0) * inversesqrt(1.0 + d0 * d0);
		if (lat < 6.0) {
			// Misa 0.60: "cesta jak dalnice" - rovnobezne koleje a souvisly zluty stredni pruh jako delici cara:
			// rozchod kolej kolisa (n1), stredni travnaty hrbet jen v usecich (nf, ~8 m) a uzsi
			float roz = 0.7 + (n1 - 0.5) * 0.35 + (nf - 0.5) * 0.15;
			float kol = (1.0 - smoothstep(0.08, 0.26, abs(lat - roz) + (nj - 0.5) * 0.18)) * (0.5 + 0.5 * smoothstep(0.3, 0.6, nf + (nj - 0.5) * 0.3));
			// koleje mizi a zase se objevuji (vyjete jen misty), stred bez carek: travnate ostruvky nepravidelne
			kol *= smoothstep(0.35, 0.6, n1 + (nf - 0.5) * 0.6);
			float stred = (1.0 - smoothstep(0.2, 0.5, lat + (nj - 0.5) * 0.3 + (nf - 0.5) * 0.3))
					* smoothstep(0.55, 0.75, nf * 0.6 + n1 * 0.4) * 0.6;
			// za ~2 m od osy (siroka naves) cesta zarusta: ostruvky travy v hline
			float kraj = smoothstep(2.0, 3.0, lat + (nj - 0.5) * 0.9 + (n1 - 0.5) * 0.8) * smoothstep(0.42, 0.6, nj * 0.6 + nf * 0.4);
			h *= 1.0 - 0.22 * kol;
			vlh = kol;
			gm = max(gm, max(stred * 0.75, kraj * 0.7));
		}
	}
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
	// za okrajem mapy (obzor, Misa "sede kopce, nedokreslena krajina"): maska stanoviste tam neni -> lesy ze sumu
	// (velke celky 300-600 m, okraje roztrepene), jinak cely obzor jedna barva louky, v mlze sedy
	vec2 suv = (p - stan_rect.xy) / stan_rect.zw;
	float venku = max(max(-suv.x, suv.x - 1.0), max(-suv.y, suv.y - 1.0));
	if (venku > 0.0) {
		float nl = texture(sum, p * 0.0021 + 0.37).r * 0.7 + texture(sum, p * 0.011 + 0.11).r * 0.3;
		float les_o = smoothstep(0.44, 0.56, nl);
		st = vec4(les_o * 0.35, les_o * 0.65, 0.0, 1.0);          // A 1 = daleko od pesiny
	}
	float n3 = texture(sum, p * 0.3 + 0.17).r;
	// pod korunami opad / jehlici i tam, kde mapa lesa z Blenderu les nema (dub na louce, lipy u vsi) - radce 11:00
	float les = max(COLOR.b, smoothstep(0.6, 1.0, st.r + st.g));          // kryti >= 0,6 (radce 20:05 bod 5)
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
		lc = mix(lc, texture(pudy_a, vec3(up * 1.3, 4.0)).rgb * pudy_k[4], mech);      // hrabanka s mechem (vrstva 4, ne 0)
		vec3 ln = mix(texture(pudy_n, vec3(up, 1.0)).rgb, texture(pudy_n, vec3(up, 2.0)).rgb, jehl);
		nl = mix(ln, texture(pudy_n, vec3(up * 1.3, 4.0)).rgb, mech);
		lm = smoothstep(0.25, 0.75, les + (texture(sum, p * 0.04 + 0.3).r - 0.5) * 0.7 + (nf - 0.5) * 0.3);
		col = mix(col, lc, lm);
	}
	// pesina (hlaseni 0.54 bod 3): udusana hlina ~1 m, okraj rozbity sumem, po stranach vyslapane stopy (tmavsi),
	// uprostred preruseny pruh travy; v lese prosvita opad. Kanal A = znamenkova vzdalenost od osy.
	float pes = 0.0;
	if (abs(st.a - 0.5) < 0.45) {
		float lat = abs(texture(stanoviste, (p - stan_rect.xy + 0.5 * stan_k) / stan_rect.zw).a - 0.5) * 6.0;
		pes = 1.0 - smoothstep(0.45, 0.7, lat + (nj - 0.5) * 0.35 + (nf - 0.5) * 0.2);
		if (pes > 0.0) {
			float stopa = 1.0 - smoothstep(0.1, 0.24, abs(lat - 0.28) + (nj - 0.5) * 0.1);
			float stred = (1.0 - smoothstep(0.06, 0.14, lat + (nj - 0.5) * 0.08)) * smoothstep(0.35, 0.6, nj + (n1 - 0.5) * 0.5);
			vec3 pc = mix(h * (1.0 - 0.08 * stopa), tr, stred * 0.25);   // pesina = hlina (radce 20:05), stopy jen naznak
			float pw = pes * (1.0 - pm * 0.7) * (1.0 - 0.3 * lm);
			col = mix(col, pc, pw);
			nl = mix(nl, nh, pw);
			lm = max(lm, pw);
			vlh = max(vlh, stopa * pw * 0.5);
		}
	}
	// COLOR.a: < 0,5 dno potoka (oblazky), 0,5-1 bahno u rybniku a prikopu
	// okraj pasu roztrepeny i v metru (nj): ne hladka cara po vrcholech site
	float bah_x = (1.0 - COLOR.a) * 2.0;
	float bahno = COLOR.a >= 0.5 ? smoothstep(0.1, 0.45, bah_x + ((n3 - 0.5) * 0.35 + (nj - 0.5) * 0.45) * smoothstep(0.0, 0.12, bah_x)) : 0.0;
	if (bahno > 0.0) {
		col = mix(col, texture(pudy_a, vec3(p / 2.0, 6.0)).rgb * pudy_k[6], bahno);
		nl = mix(nl, texture(pudy_n, vec3(p / 2.0, 6.0)).rgb, bahno);
		lm = max(lm, bahno);
	}
	float koryto = COLOR.a < 0.5 ? smoothstep(0.02, 0.6, (0.5 - COLOR.a) * 2.0 + (n3 - 0.5) * 0.3) : 0.0;
	if (koryto > 0.0) {
		col = mix(col, texture(pudy_a, vec3(p / 1.6, 5.0)).rgb * pudy_k[5], koryto);
		nl = mix(nl, texture(pudy_n, vec3(p / 1.6, 5.0)).rgb, koryto);
		lm = max(lm, koryto);
	}
	// strmina (narazovy breh potoka, srazy, svahy nad ~37 st.): skala s lisejnikem promitnuta ze tri stran (bez pruhu)
	vec3 wn2 = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	// terasa (radce 06:40 bod 7, Misa "skala bude?"): stena 7-35 m je jedna rada trojuhelniku a normala vrcholu
	// (prumer se sousedni rovinou) ji ukazovala jako svah 40 st. - trava natazena po stene. Proto i skutecna plocha
	// trojuhelniku (derivace polohy); mimo branch - derivace v nejednotnem vetveni nejsou definovane
	vec3 fn = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	fn *= dot(fn, NORMAL) < 0.0 ? -1.0 : 1.0;
	vec3 fw = (INV_VIEW_MATRIX * vec4(fn, 0.0)).xyz;
	float strm = min(wn2.y, fw.y + 0.08);
	// skalni stena nad ~45 st.: piskovec ve vrstvach (Cesky raj); na hrane prechod sumem (sousedni trojuhelniky maji
	// normalu vrcholu naklonenou ke stene). Ne u tvrze a ve vsi (breh prikopu je hlina s travou) ani v korytu.
	// (svah terasy 48-58 st. po _terasa_terenu, fw.y ~0,6)
	float pis = smoothstep(0.74, 0.6, strm + (nf - 0.5) * 0.12 + (n1 - 0.5) * 0.08);
	float u_tvrze = step(abs(p.x + 4.0), 80.0) * step(abs(p.y), 75.0);
	pis *= step(0.999, COLOR.a) * (1.0 - u_tvrze) * step(140.0, length(p - ves));
	// mirnejsi strmina (breh potoka, svah nad ~37 st.) podle normaly vrcholu jako drive: rula s lisejnikem;
	// u tvrze ne (breh prikopu a val jsou hlina s travou)
	float sk = max(smoothstep(0.82, 0.72, wn2.y + (nf - 0.5) * 0.14 + (n3 - 0.5) * 0.06) * (1.0 - u_tvrze), pis);
	float mokro = 0.0;
	if (sk > 0.0) {
		vec3 tn = normalize(mix(wn2, fw, pis));
		vec3 bw = pow(abs(tn), vec3(4.0));
		bw /= bw.x + bw.y + bw.z;
		vec3 ra = vec3(0.0);
		vec3 rn = vec3(0.5, 0.5, 1.0);
		if (pis < 1.0) {
			ra = (texture(pudy_a, vec3(wp.zy / 2.6, 7.0)).rgb * bw.x + texture(pudy_a, vec3(wp.xz / 2.6, 7.0)).rgb * bw.y
					+ texture(pudy_a, vec3(wp.xy / 2.6, 7.0)).rgb * bw.z) * pudy_k[7];
			// sedozelena rula/zula (Posazavi), zemita - ne bila (Misa: "jak snih")
			// sedozelena zemita rula/zula (Posazavi), mista mech; modrobily "snih" byl rozbity obrazek pole (svet._pudy_img)
			float lr = dot(ra, vec3(0.3, 0.45, 0.25));
			ra = mix(ra, vec3(lr) * vec3(1.0, 1.0, 0.82), 0.35) * (0.85 + 0.3 * n1);
			ra = mix(ra, vec3(0.045, 0.05, 0.022), 0.25 * smoothstep(0.4, 0.7, n3));
			rn = bw.x > bw.z ? texture(pudy_n, vec3(wp.zy / 2.6, 7.0)).rgb : texture(pudy_n, vec3(wp.xy / 2.6, 7.0)).rgb;
			rn = mix(rn, vec3(0.5, 0.5, 1.0), 0.5);
		}
		if (pis > 0.0) {
			// piskovec: jen dve svisle projekce, v = vyska (vrstvy vodorovne, bez natazeni); fotka 1,83 m, tady 2,4 m
			float wx = bw.x / max(bw.x + bw.z, 1e-4);
			float hor = wp.z * wx + wp.x * (1.0 - wx);
			vec3 pa = (texture(pudy_a, vec3(vec2(wp.z, -wp.y) / 2.4, 8.0)).rgb * wx
					+ texture(pudy_a, vec3(vec2(wp.x, -wp.y) / 2.4, 8.0)).rgb * (1.0 - wx)) * pudy_k[8];
			// druha, hruba dlazdice tehoz pisku (7,3 m) jen v prevazujici projekci: opakovani po metrech se rozbije
			pa = mix(pa, texture(pudy_a, vec3(vec2(wx > 0.5 ? wp.z : wp.x, -wp.y) / 7.3 + 0.31, 8.0)).rgb * pudy_k[8], 0.45);
			// lavice (Prachovske skaly): tloustka kazde jina 0,6-4 m (vyska zkrivena pomalym sumem), hranice zvlnene
			// o 0,3-0,8 m na delce 15-40 m, vrstvy se mista slevaji a mizi
			float wv = (texture(sum, vec2(hor * 0.025, wp.y * 0.006) + 0.47).r - 0.5) * 0.55
					+ (texture(sum, vec2(hor * 0.07, wp.y * 0.02) + 0.83).r - 0.5) * 0.25;
			float lay = wp.y / 1.9 + (texture(sum, vec2(hor * 0.003 + 0.21, wp.y * 0.035)).r - 0.5) * 3.2 + wv;
			float li = floor(lay);
			float lf = lay - li;
			float lh = fract(sin(li * 12.9898 + 4.1) * 43758.5453);          // nahoda vrstvy
			float lh2 = fract(sin(li * 78.233 + 1.7) * 24634.6345);
			// spara: sirka a hloubka podle vrstvy, podel vrstvy prerusovana (sum), nekde zadna (vrstvy splyvaji)
			float jw = mix(0.025, 0.09, lh2);
			float jo = smoothstep(0.25, 0.6, texture(sum, vec2(hor * 0.045 + li * 0.37, li * 0.11)).r + (lh - 0.5) * 0.5);
			float spara = (1.0 - smoothstep(0.0, jw, lf) * smoothstep(1.0, 1.0 - jw * 0.6, lf)) * jo * mix(0.45, 1.0, lh);
			float profil = smoothstep(0.0, 0.1 + 0.15 * lh2, lf) * (1.0 - 0.45 * smoothstep(0.35, 1.0, lf));
			float dprof = (smoothstep(0.0, 0.1 + 0.15 * lh2, lf + 0.01) * (1.0 - 0.45 * smoothstep(0.35, 1.0, lf + 0.01)) - profil) / 0.01 / 1.9 * jo;
			// svisle cleneni: bloky 3-10 m v kazde vrstve posunute (pukliny jako zdivo se nekryji), okraj zvlneny,
			// jen cast puklin otevrena; jemne pukliny ze sumu
			float bw2 = mix(3.0, 10.0, lh);
			float bx = (hor + lh2 * 17.0 + (texture(sum, vec2(wp.y * 0.05, li * 0.29)).r - 0.5) * 1.6) / bw2;
			float bh = fract(sin(floor(bx) * 39.17 + li * 7.31) * 15731.743);
			float bf = abs(fract(bx) - 0.5) * 2.0;
			float puk = smoothstep(1.0 - 0.06 / bw2 * 3.0, 1.0, bf) * step(0.35, bh);
			float pk = texture(sum, vec2(hor * 0.09, wp.y * 0.011) + 0.13).r;
			puk = max(puk, (1.0 - smoothstep(0.006, 0.02, abs(pk - 0.5))) * smoothstep(0.45, 0.7, n1) * 0.6);
			float stek = smoothstep(0.55, 0.8, texture(sum, vec2(hor * 0.21, wp.y * 0.004) + 0.61).r) * (0.4 + 0.6 * (1.0 - lf));
			// barva po velkych plochach: kazda vrstva a blok jiny odstin (rezava, okrova, svetla), sede lisejniky
			float zv = texture(sum, vec2(hor, wp.y) * 0.018 + 0.29).r;
			float lp = dot(pa, vec3(0.3, 0.5, 0.2));
			// fotka piskovce je syte rezava: zesednout k sedookrove (Prachovske skaly, barva bloku skal), rez jen mista
			pa = mix(pa, vec3(lp) * vec3(1.08, 1.0, 0.86), 0.6);
			vec3 odst = mix(vec3(1.1, 0.97, 0.82), vec3(1.0, 0.99, 0.95), lh);           // rezava .. svetla
			odst = mix(odst, vec3(1.06, 0.95, 0.84), step(0.7, bh) * 0.6);
			pa *= odst * (0.82 + 0.3 * lh2 * (0.6 + 0.4 * bh));
			float lis = smoothstep(0.52, 0.75, zv + (n3 - 0.5) * 0.3);
			pa = mix(pa, vec3(lp) * vec3(0.95, 0.97, 0.88) * 1.05, lis * 0.55);       // sedy lisejnik po plochach
			pa *= (1.0 - 0.55 * spara) * (1.0 - 0.5 * puk) * (1.0 - 0.3 * stek);
			// mech a rasy ve sparach a pod rimsou (stin, vlhko)
			float mo = (spara * 0.7 + stek * 0.3) * smoothstep(0.35, 0.65, n3 + (zv - 0.5) * 0.6);
			pa = mix(pa, vec3(0.035, 0.05, 0.022), mo * 0.6);
			mokro = max(max(spara, puk) * 0.8, stek * 0.5) * pis;
			ra = mix(ra, pa, pis);
			rn = mix(rn, vec3(0.5, 0.5, 1.0), pis);
			// relief lavic bez normalove mapy: sklon profilu podel vysky, promitnuty do plochy steny
			vec3 gy = vec3(0.0, dprof * 0.35, 0.0);
			gy -= fw * dot(gy, fw);
			vec3 hw = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
			vec3 nw = normalize(mix(hw, normalize(fw - gy), pis));
			NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
		}
		col = mix(col, ra, sk);
		nl = mix(nl, rn, sk);
		lm = max(lm, sk);
	}
	// detail terenu jen do 100 m (KCD e_TerrainDetailMaterialsViewDistZ = 100), dal jen barva krajiny - teze jako trsy
	float far = smoothstep(70.0, 100.0, dd) * (1.0 - 0.6 * sk - 0.35 * pis);
	if (far > 0.0) {
		vec3 mak = barva_krajiny(p, st, COLOR.b, sum, barva_louky, barva_lesa);
		col = mix(col, mak, far * (1.0 - pm * 0.3) * (1.0 - pes));
	}
	// strmina: tecny site jsou z UV shora a na stene degeneruji -> normala z mapy nesmysl a stena modrobila od oblohy
	// (lisejnik i "pred" na PC); ramec normalove mapy z normaly a svisle osy
	if (strm < 0.8) {
		vec3 tv = cross((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz, NORMAL);
		if (dot(tv, tv) > 0.01) {
			TANGENT = normalize(tv);
			BINORMAL = cross(NORMAL, TANGENT);
		}
	}
	ALBEDO = col;
	ROUGHNESS = 0.95 - 0.05 * vlh * (1.0 - gm) - 0.2 * mokro;        // koleje vlhke - jen malo (0.61 na tabletu leskly bile cary); spary steny vlhke
	vec3 nt = mix(texture(louka_n, p / louka_m).rgb, zr.rgb, 0.6);
	// pojistka: vzorek normalove mapy bez slozky z (cerny - na PC vrstvy pole obcas, radce 0.63 skala) lame normalu
	// k obloze -> modrobila plocha jako snih; takovy vzorek = rovna normala
	nl = nl.b < 0.4 ? vec3(0.5, 0.5, 1.0) : nl;
	NORMAL_MAP = mix(mix(nh, nt, gm), nl, lm);
	SPECULAR = 0.5 - 0.35 * sk;          // skala matna (odlesk oblohy na strmine modrobily)
}

