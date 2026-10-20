shader_type spatial;
#include "res://shaders/barva_krajiny.gdshaderinc"
// Trs travy z textury (louka): 3 zkrizene svisle karty, obrazek z atlasu obrazky/trava_atlas.png (3x2 bunky,
// fotky naskenovanych trsu z Blenderu: blender/atlas_travy.py). Bunku vybira INSTANCE_CUSTOM.b, UV meshe je
// v ramci bunky (v = 0 nahore, 1 u zeme). Vitr podle vysky, proti slunci prosvita, normaly nahoru (rub neni cerny).
// Na mobilu alfa nuzky (discard), zadne pruhledne michani.
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled, vertex_lighting;

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
uniform bool vejir = false;         // drn-vejir: vlastni atlas uz v barve louky - bez prebarveni grass_pack a bez tmave paty
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
uniform sampler2D stanoviste : filter_linear, repeat_disable;
uniform vec4 stan_rect = vec4(-250.0, -250.0, 1152.0, 1602.0);
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform vec3 barva_louky = vec3(0.08, 0.10, 0.02);
uniform vec3 barva_lesa = vec3(0.040, 0.070, 0.024);
uniform bool barva_terenu = false;
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
	if (z_custom) {
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
	if (!z_custom) {
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
}

void fragment() {
	// rozpad po trsech misto pruhlednosti: kazdy trs ma vlastni nahodny prah (z custom.g), louka do dalky
	// ridne po celych trsech, ne jako mrizka bodu; jemny Bayer 4x4 jen vyhlazuje prechod jednoho trsu
	ivec2 fc = ivec2(FRAGCOORD.xy) % 4;
	int idx = fc.x + fc.y * 4;
	float bayer[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	float prah_trsu = ic.a > 0.5 ? fract(ic.g * 13.71 + 0.37) : 0.5;
	if (viditelnost < mix(prah_trsu, (bayer[idx] + 0.5) / 16.0, 0.08)) {
		discard;
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
	float pata = svisla * step(0.8, UV.y);
	if (c.a * (1.0 + mip * 0.3) < prah && pata < 0.5) {
		discard;
	}
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
	barva *= vejir ? 1.0 : mix(0.75, 1.0, sqrt(clamp(vyska, 0.0, 1.0)));      // 0,55 delalo u zeme tmavy pruh = dira
	if (barva_terenu) {
		float tb = smoothstep(teren_od, teren_do, d_kam);
		if (tb > 0.0) {
			vec4 st = texture(stanoviste, (w_pata.xz - stan_rect.xy) / stan_rect.zw);
			barva = mix(barva, barva_krajiny(w_pata.xz, st, 0.0, sum, barva_louky, barva_lesa), tb);
		}
	}
	ALBEDO = barva;
	// obe strany karty svetle jako louka: Godot u rubu otaci normalu, tak ji vratit a priklonit nahoru
	vec3 n = FRONT_FACING ? NORMAL : -NORMAL;
	NORMAL = normalize(mix(n, (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz, 0.7));
	AO = mix(0.6, 1.0, vyska);
	AO_LIGHT_AFFECT = 0.5;
	ROUGHNESS = 0.9;
	BACKLIGHT = barva * vec3(0.9, 1.0, 0.6) * (0.15 + 0.35 * vyska);
}
