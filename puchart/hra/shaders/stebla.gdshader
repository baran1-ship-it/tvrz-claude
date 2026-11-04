// Převzato z Havrana (shaders/stebla.gdshader, Míša 4. 11.: „na louce není tráva jen rastr“): trsy z atlasu, bez barvy krajiny.
shader_type spatial;
// Trs travy z textury (louka): 3 zkrizene svisle karty, obrazek z atlasu obrazky/trava_atlas.png (3x2 bunky,
// fotky naskenovanych trsu z Blenderu: blender/atlas_travy.py). Bunku vybira INSTANCE_CUSTOM.b, UV meshe je
// v ramci bunky (v = 0 nahore, 1 u zeme). Vitr podle vysky, proti slunci prosvita, normaly nahoru (rub neni cerny).
// Mobil (radce 20:30, godot-mobile-optimized-grass): bez discard (vypina early-Z na dlazdicovych GPU), alfa jako
// pokryti MSAA (alpha_to_coverage_and_one), bez pruhledneho michani.
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled, vertex_lighting, alpha_to_coverage_and_one;

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform float vitr = 1.0;
// prolinani podle vzdalenosti trsu od kamery (renderer compatibility na Androidu neumi fade viditelnosti):
// od < 0 = bez nabehu; ve vzdalenosti [od, od + 12] se trs postupne objevi, [do - fade_sirka, do] postupne zmizi
uniform float fade_od = -1.0;
uniform float fade_do = 100000.0;
uniform float fade_sirka = 14.0;   // sirka pasma mizeni pred fade_do
uniform float prah = 0.5;          // alfa nuzky
// louka (radce 07:30 B): trsy z offline rozsevu, custom = (druh + hash, pata x, y, z v soustave bunky). Trs zmizi,
// kdyz hash > hustota(vzdalenost) - plynulym zmensenim k pate, po jednom trsu, bez hrany. Do 20 m vse, k 130 m nic;
// v dalce trs vetsi (ridsi pasmo zakryje zem jako drive stredni pasmo).
uniform bool z_custom = false;
uniform float hustota = 1.0;
uniform float hust_od = 20.0;
// pasma (radce 10:50): od hust_od do hust_do ubyva na hust_zbytek, od hust_konec do +30 m na 0 (vejir: 25-60 m na 25 %,
// 60-90 m pryc); po instancich podle hashe, instance se srazi k pate (zadna hrana)
uniform float hust_zbytek = 0.0;
uniform bool vejir = false;
uniform bool shora_mizi = false;    // kupy: svisle karty shora = tmave "hvezdice" (Misa 0.74, let 65-115 m) - pri pohledu shora zmizi
uniform float jas = 1.0;
// tablet (radce 20:45 krok 2b): varianta shaderu "unshaded" (louka.gd) - svetlo z teto barvy (slunce + obloha z denni doby)
uniform vec3 svetlo = vec3(1.0);            // normala nahoru (vertex) rozsvitila louku o ~60 % (dalka 0,42): louka.gd 0,85         // drn-vejir: vlastni atlas uz v barve louky - bez prebarveni grass_pack a bez tmave paty
uniform float hust_konec = 1e6;
uniform float hust_do = 130.0;

uniform float sloupce = 3.0;
uniform float radky = 2.0;
uniform int rezim = 0;              // 0 atlas trav (tabulka druhu), 1 grass_pack: bunka = druh, vyska vyska_od..do
uniform float vyska_od = 0.15;
uniform float vyska_do = 0.3;
// barva terenu od teren_od do teren_do (KCD e_vegetationUseTerrainColorDistance = 80 m): trs ma barvu krajiny pod sebou,
// hrana trs/teren ani dalka nemaji jinou barvu (barva_krajiny.gdshaderinc, stejne uniformy jako zem.gdshader)
uniform float teren_od = 40.0;
uniform float teren_do = 80.0;
// MŘÍŽKA kolem kamery (Zylann „grass around the player“, Godot forum „fixed grid that follows the player“ – Míša 4. 11.):
// pevný MultiMesh se posouvá s kamerou po krocích krok_m, trs je ukotven k bodu světové mřížky (hash ze souřadnic) –
// rozsev bez CPU a bez vláken, nic nedoskakuje. Výška z vysek_sit (2 × L8 = hi/lo bajt r16), hustota a druh ze stanoviště
// (L8 index třídy) a tabulky tříd (louka.gd). INSTANCE_CUSTOM.xy = poloha v mřížce (m od uzlu).
uniform bool mrizka = false;
uniform sampler2D vys_hi : filter_nearest, repeat_disable;
uniform sampler2D vys_lo : filter_nearest, repeat_disable;
uniform sampler2D stan : filter_nearest, repeat_disable;
uniform sampler2D tab : filter_nearest, repeat_disable;
uniform sampler2D kryt : filter_linear, repeat_disable;   // krytí korun 0..1 (kryt_korun.py), bilineárně jako Havran
uniform vec4 les_kryt = vec4(0.6, 1.0, 0.9, 0.0);          // od, do, úbytek
uniform float r_od = -1.0;          // prstenec kreslí trsy ve vzdálenosti od kamery [r_od, r_do] s prolnutím r_pas
uniform float r_do = 1e6;
uniform float r_pas = 3.0;
uniform vec4 vys_info = vec4(0.0);     // x0, z0, šířka, výška (1 m)
uniform float vys_h0 = 0.0;            // 300 - pocatek.H
uniform vec4 stan_info = vec4(0.0);    // x0, z0, krok, velikost
uniform float krok_m = 0.5;
uniform float vnitrni_m = 0.0;         // čtverec patřící jemnějšímu prstenci
uniform float vnejsi_m = 1e6;

uint hsh(uvec2 v) {
	v = v * 1664525u + 1013904223u;
	v.x += v.y * 1664525u; v.y += v.x * 1664525u;
	v = v ^ (v >> 16u);
	v.x += v.y * 1664525u; v.y += v.x * 1664525u;
	v = v ^ (v >> 16u);
	return v.x ^ v.y;
}
float vys_v(ivec2 cr) {
	float hi = texelFetch(vys_hi, cr, 0).r * 255.0;
	float lo = texelFetch(vys_lo, cr, 0).r * 255.0;
	return (floor(hi + 0.5) * 256.0 + floor(lo + 0.5)) / 200.0 + vys_h0;
}
float vyska_t(vec2 p) {
	vec2 q = clamp(p - vys_info.xy, vec2(0.0), vys_info.zw - 1.001);
	ivec2 i = ivec2(floor(q)); vec2 f = q - vec2(i);
	float a = vys_v(i), b = vys_v(i + ivec2(1, 0)), c = vys_v(i + ivec2(0, 1)), d = vys_v(i + ivec2(1, 1));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

varying vec3 w_pata;
varying float d_kam;

varying float vyska;
varying float viditelnost;
varying vec4 ic;           // MultiMesh custom: r = suchost (zluta trava), g = odstin, b = bunka atlasu (i + 0.5) / 6, a = 1
varying vec2 bunka;        // levy horni roh bunky v atlasu
varying float svisla;      // 1 = svisla karta (pata nepruhledna), 0 = karta shora

void vertex() {
	svisla = abs(NORMAL.y) < 0.5 ? 1.0 : 0.0;
	vyska = 1.0 - UV.y;                                     // 0 pata, 1 spicka
	ic = INSTANCE_CUSTOM;
	viditelnost = 1.0;
	if (mrizka) {
		vec2 off = INSTANCE_CUSTOM.xy;
		vec3 org = MODEL_MATRIX[3].xyz;
		vec2 g = org.xz + off;
		ivec2 gi = ivec2(round(g / krok_m));
		uint h0 = hsh(uvec2(gi + ivec2(1 << 20)));
		uint h1 = hsh(uvec2(h0, 977u));
		float r1 = float(h0 & 65535u) / 65536.0, r2 = float(h0 >> 16u) / 65536.0;
		float r3 = float(h1 & 65535u) / 65536.0, hs = float(h1 >> 16u) / 65536.0 * 0.999;
		vec2 p = g + (vec2(r1, r2) - 0.5) * 0.9 * krok_m;
		float d = distance(p, INV_VIEW_MATRIX[3].xz);
		ivec2 sc = ivec2(floor((p - stan_info.xy) / stan_info.z));
		float tr = (sc.x < 0 || sc.y < 0 || float(sc.x) >= stan_info.w || float(sc.y) >= stan_info.w) ? 255.0 : floor(texelFetch(stan, sc, 0).r * 255.0 + 0.5);
		vec4 t0 = texelFetch(tab, ivec2(int(tr), 0), 0);
		vec4 t1 = texelFetch(tab, ivec2(int(tr), 1), 0);
		float c3 = t1.r;
		float druh = r3 < t0.g ? 0.0 : (r3 < t0.b ? 1.0 : (r3 < t0.a ? 2.0 : (r3 < c3 ? 3.0 : 4.0)));
		float hust = t0.r;
		if (t1.g > 0.5) {   // les (Havran louka.gd): pod korunami úbytek, na světlinách plná hustota třídy
			float kr = texture(kryt, (p - stan_info.xy) / (stan_info.z * stan_info.w)).r;
			hust *= 1.0 - les_kryt.z * smoothstep(les_kryt.x, les_kryt.y, kr);
			hust *= 1.0 - smoothstep(les_kryt.w - 4.0, les_kryt.w, d);   // v lese tráva jen blízko (měření 4. 11.: les p95 27 → 56 ms s trávou do 56 m)
		}
		float dal = smoothstep(hust_od, hust_do, d);
		float hu = mix(1.0, hust_zbytek, dal) * (1.0 - smoothstep(hust_konec, hust_konec + 30.0, d)) * hustota;
		float potreba = hust * hu * (krok_m / 0.5) * (krok_m / 0.5);   // trsů na bod mřížky (jemná mřížka 0,5 m = 1)
		float zvetseni = sqrt(max(potreba, 1.0));
		// prstence podle vzdálenosti OD KAMERY (ne od uzlu mřížky): uzel se posouvá po kroku, hranice podle něj přeskakovaly
		// (Míša 4. 11.: trsy se při pohybu míhají) – v pásu r_pas se trs vnitřního prstence po jednom ztrácí a vnějšího objevuje
		float hs2 = fract(hs * 37.13 + 0.71);
		float w_in = r_od < 0.0 ? 1.0 : smoothstep(r_od - r_pas, r_od, d);
		float w_out = 1.0 - smoothstep(r_do - r_pas, r_do, d);
		float pas = w_in * w_out;
		float exist = clamp((min(potreba, 1.0) - hs) / 0.1, 0.0, 1.0) * clamp((pas - hs2) / 0.15 + 1.0, 0.0, 1.0) * step(hs2, pas);
		float bun = druh < 1.5 ? 0.0 : (druh < 3.5 ? 1.0 : 2.0);
		float h = druh < 0.5 ? 0.36 : (druh < 1.5 ? 0.5 : (druh < 2.5 ? 0.6 : (druh < 3.5 ? 0.82 : 0.6)));
		float s = h * mix(0.75, 1.25, fract(hs * 17.31)) * exist * mix(1.0, 1.4, dal) * min(zvetseni, 1.6);
		float a = fract(hs * 91.7 + 0.13) * 6.2831853;
		vec3 v = VERTEX * vec3(s, s * mix(0.85, 1.15, fract(hs * 5.13)) / max(min(zvetseni, 1.6) * 0.8, 1.0), s);
		vec3 pata = vec3(p.x, vyska_t(p) - 0.04, p.y) - org;
		VERTEX = pata + vec3(cos(a) * v.x + sin(a) * v.z, v.y, -sin(a) * v.x + cos(a) * v.z);
		ic = vec4(druh > 3.5 ? 0.1 : fract(hs * 7.31) * 0.15, fract(hs * 13.7 + 0.29), (bun + 0.5) / (sloupce * radky), 1.0);
	} else if (z_custom) {
		// louka: transformace instance jednotkova, custom = (druh + hash, pata x, y, z v soustave bunky)
		// cela cast = druh + 16 * q (vyska navic 0,1 q: neudrzovana louka x1,3 - louka.gd _nacti)
		float kod = floor(ic.x);
		float druh = mod(kod, 16.0);
		float navic = 1.0 + 0.1 * floor(kod / 16.0);
		float hs = fract(ic.x);
		vec3 pata = ic.yzw;
		vec3 pw = (MODEL_MATRIX * vec4(pata, 1.0)).xyz;
		float d = distance(pw.xz, INV_VIEW_MATRIX[3].xz);
		float dal = smoothstep(hust_od, hust_do, d);
		float hu = mix(1.0, hust_zbytek, dal) * (1.0 - smoothstep(hust_konec, hust_konec + 30.0, d)) * hustota * 1.1;
		// druh -> bunka atlasu a vyska karty (m)
		float bun = druh < 1.5 ? 0.0 : (druh < 3.5 ? 1.0 : (druh < 4.5 ? 2.0 : druh - 2.0));
		float h0 = druh < 0.5 ? 0.36 : (druh < 1.5 ? 0.5 : (druh < 2.5 ? 0.6 : (druh < 3.5 ? 0.82 : (druh < 4.5 ? 0.6
				: (druh < 5.5 ? 0.28 : (druh < 6.5 ? 0.55 : 0.32))))));
		float h = rezim == 1 ? mix(vyska_od, vyska_do, fract(hs * 3.71 + 0.11)) : h0;
		if (rezim == 1) {
			bun = druh;
		}
		float s = h * navic * mix(0.75, 1.25, fract(hs * 17.31)) * clamp((hu - hs) / 0.1, 0.0, 1.0) * mix(1.0, 1.6, dal);
		float a = fract(hs * 91.7 + 0.13) * 6.2831853;
		vec3 v = VERTEX * vec3(s, s * mix(0.85, 1.15, fract(hs * 5.13)), s);
		VERTEX = pata + vec3(cos(a) * v.x + sin(a) * v.z, v.y, -sin(a) * v.x + cos(a) * v.z);
		ic = vec4(rezim == 0 && druh > 3.5 && druh < 4.5 ? 0.1 : fract(hs * 7.31) * 0.15, fract(hs * 13.7 + 0.29), (bun + 0.5) / (sloupce * radky), 1.0);
	}
	float i = floor(clamp(ic.b, 0.0, 0.999) * sloupce * radky);
	bunka = vec2(mod(i, sloupce) / sloupce, floor(i / sloupce) / radky);
	// poloha vrcholu ve svete: v rendereru compatibility je transformace instance MultiMeshe uz ve VERTEX
	// a MODEL_MATRIX je jen uzel (stred bunky 32 m) - vzdalenost od nej rozpadala celou bunku najednou
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float dist = distance(w, INV_VIEW_MATRIX[3].xyz);
	w_pata = w;
	d_kam = dist;
	if (!z_custom && !mrizka) {
		viditelnost = 1.0 - smoothstep(fade_do - fade_sirka, fade_do, dist);
		if (fade_od >= 0.0) {
			viditelnost *= smoothstep(fade_od, fade_od + 12.0, dist);
		}
	}
	float t = TIME * 1.6 + w.x * 0.21 + w.z * 0.17;
	// byliny (bunka 3 a 4) se hybou mene nez trava
	float k = vyska * vyska * 0.09 * vitr * (i > 2.5 && i < 4.5 ? 0.4 : 1.0);
	VERTEX.x += (sin(t) * 0.7 + sin(t * 2.3 + w.z * 0.3) * 0.3) * k;      // faze se po karte meni jen malo (karta drzi tvar)
	VERTEX.z += cos(t * 0.8 + w.x * 0.3) * k * 0.6;
	// vertex_lighting: svetlo se pocita z teto normaly (uprava NORMAL ve fragment() se neprojevi) - normala
	// skoro nahoru jako louka (KCD normaly_od_stredu), jinak karty odvracene od slunce tmave pruhy (test dira)
	NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 0.75));
}

void fragment() {
	// rozpad po trsech misto pruhlednosti: kazdy trs ma vlastni nahodny prah (z custom.g), louka do dalky
	// ridne po celych trsech, ne jako mrizka bodu; jemny Bayer 4x4 jen vyhlazuje prechod jednoho trsu
	ivec2 fc = ivec2(FRAGCOORD.xy) % 4;
	int idx = fc.x + fc.y * 4;
	float bayer[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	float prah_trsu = ic.a > 0.5 ? fract(ic.g * 13.71 + 0.37) : 0.5;
	float vid = viditelnost < mix(prah_trsu, (bayer[idx] + 0.5) / 16.0, 0.08) ? 0.0 : 1.0;
	if (shora_mizi) {
		float vy = (INV_VIEW_MATRIX * vec4(VIEW, 0.0)).y;          // k kamere: 1 = kamera primo nad
		vid *= step((bayer[idx] + 0.5) / 16.0, 1.0 - smoothstep(0.35, 0.6, vy));
	}
	// okraj bunky necha pruhledny (mipmapy sousedni bunky neprosakuji)
	vec2 uv = bunka + clamp(UV, vec2(0.01, 0.02), vec2(0.99, 0.995)) / vec2(sloupce, radky);
	vec4 c = texture(atlas, uv);
	// zachovat pokryti v mipmapach (jinak tenka stebla zdalky mizi): alfa nahoru podle urovne mipmapy
	vec2 tx = uv * vec2(textureSize(atlas, 0));
	vec2 dx = dFdx(tx);
	vec2 dy = dFdy(tx);
	float mip = max(0.0, 0.5 * log2(max(dot(dx, dx), dot(dy, dy))));
	// spodnich 20 % svisle karty bez pruhlednosti (radce 09:05 bod 3): trsy se u zeme spoji, mezi paty neni videt
	// teren; pruhledne texely atlasu maji barvu travy (rozliti), ne cernou
	// (0.57 nepruhledna pata svislych karet = cerne obdelniky na tabletu: pruhledne texely atlasu jsou po ETC2 cerne)
	ALPHA = clamp(c.a * (1.0 + mip * 0.3), 0.0, 1.0) * vid;
	ALPHA_SCISSOR_THRESHOLD = prah;
	ALPHA_ANTIALIASING_EDGE = prah * 0.8;
	vec3 barva = c.rgb;
	if (rezim == 1 && !vejir) {
		// grass_pack: svetle klasy a stebla do barvy nasi louky (jinak z dalky bile chomacky)
		float l = dot(barva, vec3(0.3, 0.5, 0.2));
		barva = mix(barva, vec3(l * 0.75, l * 0.95, l * 0.35), 0.55) * 0.8;
	}
	if (ic.a > 0.5) {
		float l = dot(barva, vec3(0.3, 0.5, 0.2));
		barva = mix(barva, vec3(l * 1.5, l * 1.3, l * 0.55), ic.r);
		barva *= 0.88 + 0.24 * ic.g;
	}
	// pata trsu jen mirne tmavsi (ne cerna): textura uz ma zastineni mezi stebly zapecene
	// vejir 0,75: plny do 25 m byl svetlejsi nez louka za nim (test pasmo 60-100 m o 10-20 % tmavsi, dalka 0,42)
	// tmava pata jen blizko: za 40 m je trs maly a pata by zabarvila celou louku (radce 13:50: pasmo 60-100 m tmavsi)
	float blizko = 1.0 - smoothstep(30.0, 40.0, d_kam);
	barva *= vejir ? 0.75 : mix(1.0, mix(0.75, 1.0, sqrt(clamp(vyska, 0.0, 1.0))), blizko);      // 0,55 = tmavy pruh = dira
	ALBEDO = barva * jas * svetlo;
	// obe strany karty svetle jako louka: Godot u rubu otaci normalu, tak ji vratit a priklonit nahoru
	vec3 n = FRONT_FACING ? NORMAL : -NORMAL;
	NORMAL = normalize(mix(n, (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz, 0.7));
	AO = mix(mix(0.8, 1.0, vyska), 1.0, 1.0 - blizko);
	AO_LIGHT_AFFECT = 0.5;
	ROUGHNESS = 0.9;
	BACKLIGHT = barva * vec3(0.9, 1.0, 0.6) * (0.15 + 0.35 * vyska);
}
