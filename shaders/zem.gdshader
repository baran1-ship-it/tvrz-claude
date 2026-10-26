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
uniform vec4 lom_rect = vec4(0.0);           // lom (svet.LOM_*): x0, z0, x1, z1
uniform float lom_y = -1000.0;
uniform float lom_pata[16];                   // x paty lomove steny po 5 m od lom_rect.y + 16 (svet.LOM_Z.x)
uniform vec2 lom_cerstve = vec2(0.0);         // z0, z1 lamane casti steny (leseni): cerstve plochy svetle, bez okru
uniform vec4 trziste = vec4(0.0, 0.0, 1.0, 0.0);   // trziste vedle cesty: pocatek x, z, smer u (svet.TRZ_*)
uniform vec4 trziste_r = vec4(0.0, -1.0, 0.0, -1.0);   // u od, u do, v od, v do               // vyska dna lomu (nad ni uz je les nad stenou)
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
// cesty = teren (pravidla povrchu A, radce 15:10/15:20): udaje cesty ve vrcholech terenu (svet._cesty_do_terenu)
// CUSTOM0 = (lat / okraj hliny se znamenkem, s podel osy m, jetost koleji, okraj m),
// CUSTOM1 = (trava hrbetu, bahno, |od stredu koleje| / 2, 7 = platne; bez dat 0/1 = mimo cestu)
varying vec4 v_c0;
varying vec4 v_c1;

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
	v_c0 = CUSTOM0;
	v_c1 = CUSTOM1;
}

// atlas 2x2 dlazdic (cesty): textureGrad s derivacemi puvodni souradnice - bez svu mezi dlazdicemi
// (sampler jako parametr jen s jednim nastavenim - barva a normala zvlast)
vec3 atl(sampler2D t, vec2 uv, int k) {
	vec2 f = fract(uv) * 0.99 + 0.005;
	vec2 o = vec2(float(k % 2), float(k / 2)) * 0.5;
	return textureGrad(t, o + f * 0.5, dFdx(uv) * 0.5, dFdy(uv) * 0.5).rgb;
}
vec3 atln(sampler2D t, vec2 uv, int k) {
	vec2 f = fract(uv) * 0.99 + 0.005;
	vec2 o = vec2(float(k % 2), float(k / 2)) * 0.5;
	return textureGrad(t, o + f * 0.5, dFdx(uv) * 0.5, dFdy(uv) * 0.5).rgb;
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
	// nadvori tvrze (radce 09:20): udusana hlina, ne zeleny travnik - zelen jen v pasu u zdi (trsy tam dela louka)
	vec2 ndp = min(p - vec2(-27.6, -16.6), vec2(18.5, 17.4) - p);
	float nd_in = step(0.0, min(ndp.x, ndp.y)) * smoothstep(1.5, 3.2, min(ndp.x, ndp.y) + (n1 - 0.5) * 1.5);
	gm *= 1.0 - 0.9 * nd_in;
	vec2 tq = p - trziste.xy;
	float tu = dot(tq, trziste.zw);
	float tv = dot(tq, vec2(trziste.w, -trziste.z));
	float td = max(max(trziste_r.x - tu, tu - trziste_r.y), max(trziste_r.z - tv, tv - trziste_r.w));
	gm *= smoothstep(-1.5, 1.5, td + (n1 - 0.5) * 3.0 + (nj - 0.5) * 0.8);
	// vsechna useslapana zem (dvory, pesiny, cesty) z jednoho atlasu hliny (pravidla povrchu A): dlazdice 0 = prach
	vec3 h = atl(hlina_a, p / 2.0, 0) * hlina_k * vec3(1.06, 1.0, 0.91) * mix(0.82, 1.12, nf);     // vlhci a sussi mista
	h = mix(vec3(dot(h, vec3(0.3, 0.55, 0.15))), h, 0.75);   // Misa 0.65: suchy prach, mene do ruda
	vec3 nh = atln(hlina_n, p / 2.0, 0);
	float vlh = 0.0;
	// vaha cesty: uvnitr okraje hliny 1, za nim 0; okraj rozbity sumem
	float rd = v_c1.w > 6.0 ? 1.0 - smoothstep(0.88, 1.1, abs(v_c0.x) + (nj - 0.5) * 0.14 + (nf - 0.5) * 0.08) : 0.0;
	// cesta navsi (hlaseni 0.54 bod 3): hlina, dve koleje 1,4 m od sebe (tmavsi, vlhci), mezi nimi zbytky travy,
	// okraj zubaty do louky (~4 m); kde je ves podle barvy vrcholu hlinena a blizko osy hlavni cesty
	vec2 vq = p - ves;
	float vu = dot(vq, VES_AU);
	if (rd < 0.01 && gm < 0.98 && vu > -97.0 && vu < 57.0) {          // konec u rybnicku (POND 74 +- 14, Misa 0.74: hlina kolem vody)
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
	// cesta = tvar (radce 18:00, reserse CryEngine/BeamNG): vyjete koleje tmave a vlhke s ryhami od kol a otisky
	// kopyt podel, mezi kolejemi a na krajich suchy prach se strikem kaminku; okraj trava/hlina prolnuty podle vysky
	// textury hliny (height blend: hrudky hliny vystupuji do travy, trava zatece do prohlubni), ne linearni prechod
	float cesta_lz = 0.0;
	if (rd > 0.0) {
		vec3 h0 = h;
		float gm0 = gm;
		vec3 nh0 = nh;
		// fotky KCD2 (Misa 25. 10., 17 ks, rozbor barev 0.82): svetly bezovy prach (R/G 1,16, B/G 0,80, sytost 0,31),
		// velky rozptyl jasu (svetla mista 2x tmavsich): tmave sedohnede stopy a koleje, sede kameny, velke skvrny.
		// Atlas 2x2 (hlina_a/hlina_n na materialu cest, svet._cesty_material): 0 forrest_sand_01 (2 m) prach,
		// 1 dry_mud_field_001 (3 m) utlacena hlina, 2 rocky_trail (2 m) kameni, 3 aerial_ground_rock (20 m) skvrny
		float sp = v_c0.y;
		float rw = v_c0.z;                                    // jetost koleji (svet.cesty_opotrebeni)
		float dk = v_c1.z * 2.0;                              // |vzdalenost od stredu koleje|
		float kol = rw * (1.0 - smoothstep(0.1, 0.42, dk + (nj - 0.5) * 0.1));
		vec3 sand = atl(hlina_a, p / 2.0, 0);
		vec3 mud = atl(hlina_a, p / 3.0 + 0.21, 1);
		vec3 rock = atl(hlina_a, p / 2.0 + 0.37, 2);
		vec3 mac = atl(hlina_a, p / 20.0, 3) / vec3(0.212, 0.141, 0.100);      // prumer dlazdice linearne (sRGB 127,105,89)
		float vlhke = texture(sum, p * 0.17 + 0.53).r * 0.6 + texture(sum, p * 0.5 + 0.2).r * 0.4;
		// Misa 0.82 „jak uhrabany, v rastru se tahnou carky“: sum natazeny podel cesty (stopy, kopyta) pryc -
		// tmave misto jen v kolejich a v nepravidelnych skvrnach (izotropni sum), detail dela fotka textury
		float stopy = smoothstep(0.62, 0.78, texture(sum, p * 0.21 + 0.44).r) * smoothstep(0.4, 0.7, texture(sum, p * 0.05 + 0.8).r);
		float kopyta = 0.0;
		// kamenity usek (svet.cesta_useky z, stejny vzorec)
		float xk = sp * 0.021 + 7.7;
		float kmn = smoothstep(0.2, 0.6, sin(xk) * 0.55 + sin(xk * 2.31 + 1.7) * 0.3 + sin(xk * 5.13 + 0.4) * 0.15);
		// Misa 0.83: koleje ani skvrny nemaji byt tmave fleky - jen jemne (KCD2: prach, koleje o malo tmavsi)
		// Misa 0.83 (naves „stejny rastr“): jediny jemny sum po 2 m se zdalky slil do jednoliteho rastru - KCD2 ma
		// velke plochy: udusana tmavsi hlina (kudy se chodi, 4-12 m), svetly prach, sterkova mista; okraje mekke, nesmerove
		float plo = texture(sum, p * 0.045 + 0.17).r * 0.65 + texture(sum, p * 0.13 + 0.61).r * 0.35;
		float udus = smoothstep(0.48, 0.62, plo + (nj - 0.5) * 0.12);
		float tm = clamp(max(max(kol * 0.3, stopy * 0.2), max((1.0 - smoothstep(0.2, 0.35, vlhke)) * 0.25, udus * 0.62)), 0.0, 1.0);
		float sterk = smoothstep(0.58, 0.7, texture(sum, p * 0.09 + 0.83).r + (nj - 0.5) * 0.1) * (1.0 - udus * 0.6);
		float km = clamp(kmn * smoothstep(0.3, 0.6, texture(sum, p * 0.12 + 0.3).r + 0.2) + smoothstep(0.62, 0.8, texture(sum, p * 0.33 + 0.71).r) * 0.5 + sterk * 0.7, 0.0, 1.0);
		h = mix(sand * (1.0 + 0.1 * (1.0 - udus)), mud * 0.9, tm);
		h = mix(h, rock, km * (1.0 - tm * 0.5));
		h *= mix(vec3(1.0), clamp(mac, vec3(0.6), vec3(1.45)), 0.85);        // KCD2: svetla mista 2x tmavsich (0.82: 1,37x)
		h *= hlina_k * vec3(1.06, 1.0, 0.91);                      // rozbor fotek KCD2: R/G 1,16, B/G 0,80 (bez 1,07/0,90; s 1,09/0,86 = 1,19/0,75)
		vec3 nsa = atln(hlina_n, p / 2.0, 0);
		nh = mix(mix(nsa, atln(hlina_n, p / 3.0 + 0.21, 1), tm), atln(hlina_n, p / 2.0 + 0.37, 2), km * (1.0 - tm * 0.5));
		nh = mix(nh, vec3(0.5, 0.5, 1.0), kol * 0.4);            // koleje utlacene, hladsi
		vlh = max(vlh, (kol * 0.25 + (1.0 - smoothstep(0.2, 0.4, vlhke)) * 0.12) * rd);
		float hv = dot(sand, vec3(0.33));
		gm = smoothstep(0.42, 0.6, v_c1.x + (0.42 - hv) * 0.9 + (nj - 0.5) * 0.22 + (nf - 0.5) * 0.1);
		// louze: kalna voda v kolejich, okraj bahno (bahno 0..1 z opotrebeni)
		float bm = v_c1.y;
		cesta_lz = smoothstep(0.2, 0.3, 0.18 * bm + 0.1 * smoothstep(0.4, 0.8, bm) + (nj - 0.5) * 0.06) * 0.8 * rd;
		// prechod do terenu okoli (pole, louka, les) podle vahy cesty - jeden povrch, zadna hrana
		h = mix(h0, h, rd);
		gm = mix(gm0, gm, rd);
		nh = mix(nh0, nh, rd);
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
	float pm = smoothstep(0.3, 0.6, COLOR.r + (texture(sum, p * 0.035 + 0.6).r - 0.5) * 0.5 + (nf - 0.5) * 0.25) * (1.0 - rd);   // na ceste pole ne
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
		lm *= mix(1.0, gm, rd);              // cesta lesem: hlina, hrabanka jen na okraji v trave (0.81)
		col = mix(col, lc, lm);
	}
	// pesina (hlaseni 0.54 bod 3): udusana hlina ~1 m, okraj rozbity sumem, po stranach vyslapane stopy (tmavsi),
	// uprostred preruseny pruh travy; v lese prosvita opad. Kanal A = znamenkova vzdalenost od osy.
	float pes = 0.0;
	if (abs(st.a - 0.5) < 0.45) {
		// 4 uzly zvlast: znamenko se meni i mimo osu (okraj pasu 3 m, ohyby) - prechod -2,4 -> +3 mezi uzly
		// vychazel linearne jako 0 = druha "osa" 5 m vedle cesty (Misa 0.76 "cesty zdvojene"); tam bez znamenka
		vec2 tf = (p - stan_rect.xy) / stan_k;
		ivec2 ti = ivec2(floor(tf));
		vec2 fr = tf - floor(tf);
		ivec2 tmax = textureSize(stanoviste, 0) - 1;
		float a00 = (texelFetch(stanoviste, clamp(ti, ivec2(0), tmax), 0).a - 0.5) * 6.0;
		float a10 = (texelFetch(stanoviste, clamp(ti + ivec2(1, 0), ivec2(0), tmax), 0).a - 0.5) * 6.0;
		float a01 = (texelFetch(stanoviste, clamp(ti + ivec2(0, 1), ivec2(0), tmax), 0).a - 0.5) * 6.0;
		float a11 = (texelFetch(stanoviste, clamp(ti + ivec2(1, 1), ivec2(0), tmax), 0).a - 0.5) * 6.0;
		float lin = abs(mix(mix(a00, a10, fr.x), mix(a01, a11, fr.x), fr.y));
		float bez = mix(mix(abs(a00), abs(a10), fr.x), mix(abs(a01), abs(a11), fr.x), fr.y);
		float lat = mix(lin, bez, smoothstep(1.4, 1.9, bez - lin));
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
	float bahno = COLOR.a >= 0.5 ? smoothstep(0.02, 0.6, (1.0 - COLOR.a) * 2.0 + (n3 - 0.5) * 0.3) : 0.0;
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
	// Misa 0.63 (terasa "hruza"): normala plochy trojuhelniku delala viditelne fasety (kazdy trojuhelnik jinak
	// nasviceny a jinak promitnuty) - terasa uz je svah z _terasa_terenu s hladkymi normalami vrcholu, staci ty
	vec3 fw = wn2;
	float strm = wn2.y;
	// skalni stena nad ~45 st.: piskovec ve vrstvach (Cesky raj); na hrane prechod sumem (sousedni trojuhelniky maji
	// normalu vrcholu naklonenou ke stene). Ne u tvrze a ve vsi (breh prikopu je hlina s travou) ani v korytu.
	// (svah terasy 48-58 st. po _terasa_terenu, fw.y ~0,6)
	float pis = smoothstep(0.74, 0.6, strm + (nf - 0.5) * 0.12 + (n1 - 0.5) * 0.08);
	// lom (KCD Talmberk, Misa 0.70 "drz se fotek"): sedy lamany kamen v blocich, ne piskovec ve vrstvach
	float v_lomu = step(lom_rect.x, p.x) * step(p.x, lom_rect.z) * step(lom_rect.y, p.y) * step(p.y, lom_rect.w);
	float lom_st = v_lomu * smoothstep(0.8, 0.6, strm);
	pis *= 1.0 - v_lomu;
	float mokro = 0.0;
	if (cesta_lz > 0.0) {
		col = mix(col, col * vec3(0.62, 0.6, 0.55) + vec3(0.012, 0.012, 0.01), cesta_lz);   // Misa 0.85: cerne diry - kaluz jen tmavsi bahno         // kalna louze
		mokro = max(mokro, cesta_lz * 1.4);
	}
	// dno lomu: sedy stěrk a bláto s kolejemi (fotky KCD), ne hlina pesiny
	float lom_dno = v_lomu * (1.0 - lom_st) * (1.0 - smoothstep(lom_y + 2.0, lom_y + 4.0, wp.y)) * smoothstep(0.0, 1.0, (min(min(p.x - lom_rect.x, lom_rect.z - p.x), min(p.y - lom_rect.y, lom_rect.w - p.y))) / 4.0);
	// udusana plocha jen k okraji 23-31 m od paty (svet.lom_okraj), dal louka - okraj roztrepeny
	float lzi = clamp((p.y - lom_rect.y - 16.0) / 5.0, 0.0, 14.99);
	float lpx = mix(lom_pata[int(lzi)], lom_pata[int(lzi) + 1], fract(lzi));
	float lokr = 27.5 + 1.8 * sin(p.y * 0.19 + 1.3) + 1.2 * sin(p.y * 0.47 + 0.4) + 0.8 * sin(p.y * 1.07);
	lom_dno *= 1.0 - smoothstep(lokr - 1.2, lokr + 0.8, p.x - lpx + (texture(sum, p * 0.21).r - 0.5) * 2.5);
	if (lom_dno > 0.0) {
		vec3 st2 = texture(pudy_a, vec3(p / 1.6, 5.0)).rgb * pudy_k[5];
		// koleje voza: dve stopy 1,4 m od sebe podel osy lomu (sever-jih) s prohnutim, louze ve vyjetych mistech
		float ox = p.x - lom_rect.x - 0.55 * (lom_rect.z - lom_rect.x) + (texture(sum, vec2(p.y * 0.012, 0.3)).r - 0.5) * 14.0;
		float kol = max(1.0 - smoothstep(0.12, 0.3, abs(abs(ox) - 0.7)), 0.0) * smoothstep(0.35, 0.6, texture(sum, p * 0.05).r + 0.2);
		float sl = clamp(dot(st2, vec3(0.33)) * 5.0, 0.7, 1.3);          // textura oblazku je tmava (mokre dno potoka)
		st2 = vec3(0.33, 0.32, 0.295) * sl * (0.9 + 0.2 * nf) * (1.0 - 0.3 * kol);
		st2 = mix(st2, h * 1.1, 0.25 + 0.35 * smoothstep(0.4, 0.7, n1 + kol * 0.3));   // blato a hlina mezi sterkem
		vlh = max(vlh, kol * 0.6);
		col = mix(col, st2, lom_dno);
		// louze ve vyjetych mistech a u kolej (Misa 0.74): tmave mokre, lesk
		float lz = smoothstep(0.72, 0.76, texture(sum, p * 0.05 + 0.5).r * 0.8 + texture(sum, p * 0.3).r * 0.2 + kol * 0.1) * lom_dno;
		col = mix(col, col * 0.45 + vec3(0.03, 0.04, 0.05), lz);
		vlh = max(vlh, lz * 6.0);
		mokro = max(mokro, lz * 1.6);         // Misa 0.76 (147,924): kaluz na tabletu bile zrcadlo - mokre, ne lesk
		nl = mix(nl, texture(pudy_n, vec3(p / 1.6, 5.0)).rgb, lom_dno);
		lm = max(lm, lom_dno);
	}
	float u_tvrze = step(abs(p.x + 4.0), 80.0) * step(abs(p.y), 75.0);
	pis *= step(0.999, COLOR.a) * (1.0 - u_tvrze) * step(140.0, length(p - ves));
	// mirnejsi strmina (breh potoka, svah nad ~37 st.) podle normaly vrcholu jako drive: rula s lisejnikem;
	// u tvrze ne (breh prikopu a val jsou hlina s travou)
	float sk = max(max(smoothstep(0.82, 0.72, wn2.y + (nf - 0.5) * 0.14 + (n3 - 0.5) * 0.06) * (1.0 - u_tvrze), pis), lom_st);
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
			if (lom_st > 0.0) {
				// lomova stena: bloky 1-3 m - svisle spary (pomaly sum podel steny) a vodorovne po 0,8-1,6 m, sedy kamen,
				// cerstve lomove plochy svetlejsi dole
				float ht = bw.x > bw.z ? wp.z : wp.x;                       // vodorovne podel steny
				float hz = ht + (texture(sum, vec2(wp.y * 0.03, ht * 0.007)).r - 0.5) * 3.0;
				float bu = hz / 3.2;
				float bv = wp.y / 2.2 + floor(bu) * 0.41;
				float sp = max(1.0 - smoothstep(0.0, 0.025, min(fract(bu), 1.0 - fract(bu))), 1.0 - smoothstep(0.0, 0.03, min(fract(bv), 1.0 - fract(bv))));
				float tl = fract(sin(dot(floor(vec2(bu, bv)), vec2(12.9898, 78.233))) * 43758.5453);
				vec3 sedy = vec3(dot(ra, vec3(0.33))) * vec3(0.98, 1.0, 1.02) * (0.8 + 0.4 * tl);
				sedy *= mix(1.15, 0.85, clamp(strm, 0.0, 1.0));
				// Misa: "nic neni ciste sede" - zula se zelezitymi (okrovymi) mapami a zatekly, sedohneda; ne cista seda
				float ok = smoothstep(0.5, 0.8, texture(sum, vec2(ht * 0.04, wp.y * 0.06)).r + tl * 0.2);
				sedy = mix(sedy, sedy * vec3(1.12, 0.98, 0.8), 0.4 + 0.5 * ok);
				// lamana cast (radce 17:55 "leseni tam, kde se lame - cerstve svetle plochy"): spodnich 12 m svetla seda
				float cer = smoothstep(lom_cerstve.x - 3.0, lom_cerstve.x + 1.0, wp.z) * (1.0 - smoothstep(lom_cerstve.y - 1.0, lom_cerstve.y + 3.0, wp.z))
						* (1.0 - smoothstep(lom_y + 9.0, lom_y + 13.0, wp.y));
				// Misa: "stena ma korespondovat s kopcem a ostatnimi stenami" - jen lehce svetlejsi, bez kontrastu navic
				sedy = mix(sedy, vec3(dot(sedy, vec3(0.33))) * vec3(1.1, 1.08, 1.04), 0.3 * cer);
				ra = mix(ra, sedy, 0.7 * lom_st) * (1.0 - 0.35 * sp * lom_st);
			}
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
	ROUGHNESS = max(0.95 - 0.05 * vlh * (1.0 - gm) - 0.2 * mokro, 0.55);        // koleje vlhke - jen malo (0.61 na tabletu leskly bile cary); spary steny vlhke
	vec3 nt = mix(texture(louka_n, p / louka_m).rgb, zr.rgb, 0.6);
	// pojistka: vzorek normalove mapy bez slozky z (cerny - na PC vrstvy pole obcas, radce 0.63 skala) lame normalu
	// k obloze -> modrobila plocha jako snih; takovy vzorek = rovna normala
	nl = nl.b < 0.4 ? vec3(0.5, 0.5, 1.0) : nl;
	NORMAL_MAP = mix(mix(nh, nt, gm), nl, lm);
	SPECULAR = (0.5 - 0.35 * sk) * (1.0 - 0.6 * clamp(mokro, 0.0, 1.0));          // skala matna (odlesk oblohy na strmine modrobily)
}

