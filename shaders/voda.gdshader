shader_type spatial;
// Voda (prikop, rybnik, potok): lom svetla (dno se vlni pod hladinou), odraz oblohy podle uhlu pohledu,
// dve posouvane normalove mapy (potok po proudu s penou), okrehek na stojate vode, kruhove vlnky
// (zaba, ryba, kroky hrace) a ceřeni kolem nohou, kdyz hrac stoji ve vode.
// 18. 11. (Misa: voda jako v lese Hvozd, voda.json vzhled_hvozd): odraz = panorama mlhaveho lesa (equirect, Poly Haven
// misty_pines CC0) ctena smerem odrazeneho paprsku, fresnel Schlick, odraz v EMISSION x voda_svetlo (daylight.gd - v noci
// tma), tmave telo hnede u kraje -> cernozelene uprostred, jedna normalova mapa ctena dvakrat, pena ze sumu po proudu.
render_mode blend_mix, depth_draw_always, cull_back, specular_schlick_ggx;

uniform sampler2D nmap : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform sampler2D panorama : source_color, filter_linear_mipmap, repeat_enable;
global uniform vec3 voda_svetlo;
uniform float tekouci = 0.0;      // potok: UV.x = delka po proudu (m/4)
uniform float okrehek = 0.0;      // stojata voda: ostruvky okrehku
uniform vec4 rip[8];              // x, z, cas vzniku (jako TIME), sila
uniform vec4 hrac = vec4(0.0, 0.0, 0.0, 0.0);   // x, z, polomer kolem nohou, sila (0 = hrac neni ve vode)
uniform vec2 vitr = vec2(0.8, 0.6);               // stojata voda: smer vetru (vlnky a poryvy po vetru)
uniform bool hloubka_vrcholu = false;             // rybnik, prikop: COLOR.r * 4 = hloubka (scripts/nadrz.gd)
// maly tok (potok, odtok, nahon): UV.x = napric pasu 0..1, okraj pasu pod brehem
uniform bool maly_tok = false;
// vzhled Hvozd (voda.json vzhled_hvozd, svet.voda_odraz)
uniform float f0 = 0.03;
uniform float f_mocnina = 5.0;
uniform float odraz_nasobek = 0.8;
uniform float odraz_tonovani = 0.35;
uniform vec3 telo_kraj : source_color = vec3(0.08, 0.065, 0.04);
uniform vec3 telo_stred : source_color = vec3(0.015, 0.024, 0.019);
uniform float stred_hloubka = 1.0;
uniform vec2 alfa = vec2(0.2, 0.92);              // kraj, stred
uniform float vl_uv_m = 4.0;
uniform vec2 vl_meritko = vec2(0.8, 1.9);
uniform vec2 vl_rychlost = vec2(0.45, 0.8);
uniform vec2 vl_vaha = vec2(0.55, 0.45);
uniform float vl_sklon = 0.6;
uniform vec2 pena_mr = vec2(0.35, 0.6);           // meritko, rychlost po proudu
uniform vec2 pena_prah = vec2(0.62, 0.8);
uniform vec2 pena_sila = vec2(0.55, 0.12);        // kraj, stred
uniform vec3 pena_barva : source_color = vec3(0.55, 0.57, 0.52);

varying vec3 wpos;
varying float v_pena;       // potok: pena kolem a za kameny (barva vrcholu R z Blenderu)
varying float v_perej;      // potok: perej / brod (G)
varying vec2 v_tok;         // potok: smer toku (B, A z Blenderu, vyhlazeny)
varying float v_hl;         // stojata voda: hloubka (m)

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	v_pena = 0.0;
	v_perej = 0.0;
	v_hl = hloubka_vrcholu ? COLOR.r * 4.0 : 10.0;
	if (tekouci > 0.5) {
		v_pena = COLOR.r;
		v_perej = COLOR.g;
		v_tok = COLOR.ba * 2.0 - 1.0;
		if (length(v_tok) < 0.05) {
			v_tok = vec2(1.0, 0.0);
		}
		v_tok = normalize(v_tok);
		// voda u kamenu a v perejich poskakuje (stojate vlny, kazdy kus jinak)
		float sk = v_pena * 0.06 + v_perej * 0.03;
		VERTEX.y += (sin(t * 7.0 + wpos.x * 3.1 + wpos.z * 2.3) * 0.6 + sin(t * 11.0 - wpos.z * 4.7) * 0.4) * sk + v_pena * 0.03;
	} else {
		v_tok = vec2(1.0, 0.0);
		vec2 vd = normalize(vitr);
		VERTEX.y += (sin(dot(wpos.xz, vd) * 1.3 - t * 2.0) * 0.6 + sin(wpos.x * 0.7 + t * 1.2) * 0.4) * 0.01;
	}
}

void fragment() {
	vec2 p = wpos.xz;
	float t = TIME;
	// smer: po proudu (potok) / po vetru (stojata voda)
	vec2 sm = tekouci > 0.5 ? v_tok : normalize(vitr);
	vec2 bok = vec2(-sm.y, sm.x);
	float u = dot(p, sm) / vl_uv_m;
	float v = dot(p, bok) / vl_uv_m;
	// vlnky: jedna normalova mapa ctena dvakrat (Hvozd: uv.x*0,8 - t*0,45 a uv.x*1,9 - t*0,8, vahy 0,55/0,45)
	vec3 n1 = texture(nmap, vec2(u * vl_meritko.x - t * vl_rychlost.x, v * vl_meritko.x)).rgb;
	vec3 n2 = texture(nmap, vec2(u * vl_meritko.y - t * vl_rychlost.y, v * vl_meritko.y) + 0.37).rgb;
	vec2 nxy = ((n1.xy * vl_vaha.x + n2.xy * vl_vaha.y) * 2.0 - 1.0) * vl_sklon * (1.0 + 0.8 * v_perej);
	vec2 g = sm * nxy.x + bok * nxy.y;               // sklon hladiny ve svete (x, z)
	// okraj -> stred (0 = kraj, 1 = stred): hloubka z barvy vrcholu, maly tok napric pasu
	float kraj_p = min(UV.x, 1.0 - UV.x);
	float stred = maly_tok ? smoothstep(0.08, 0.5, kraj_p) : smoothstep(0.0, stred_hloubka, v_hl);
	// pena ze sumu po proudu, u kraje silnejsi (potok: navic kolem kamenu a v perejich z barvy vrcholu)
	float s = texture(sum, vec2(u * pena_mr.x - t * pena_mr.y, v * pena_mr.x * 2.5)).r;
	float pena = smoothstep(pena_prah.x, pena_prah.y, s) * mix(pena_sila.x, pena_sila.y, stred);
	if (tekouci < 0.5) {
		pena *= 0.35;                                 // stojata voda: jen slaby lem
	} else {
		pena = max(pena, v_pena * smoothstep(0.3, 0.7, s + v_pena * 0.5 - 0.15));
		pena = max(pena, v_perej * smoothstep(0.55, 0.75, s) * 0.7);
	}
	// kruhove vlnky: soustredne hrebeny se rozbihaji a slabnou
	float hreben = 0.0;
	for (int i = 0; i < 8; i++) {
		float age = t - rip[i].z;
		if (age > 0.0 && age < 4.0 && rip[i].w > 0.0) {
			vec2 d = p - rip[i].xy;
			float r = length(d) + 1e-4;
			float x = r - age * 0.55;
			float env = exp(-x * x * 7.0) * (1.0 - age / 4.0) * rip[i].w / (1.0 + r * 0.6);
			g += (d / r) * cos(x * 28.0) * env * 0.4;
			hreben += max(cos(x * 28.0), 0.0) * env;
		}
	}
	// ceřeni kolem nohou (hrac stoji nebo se brodi)
	if (hrac.w > 0.0) {
		vec2 d = p - hrac.xy;
		float r = length(d) + 1e-4;
		float x = r - hrac.z;
		float env = exp(-x * x * 30.0) * hrac.w;
		float chv = texture(sum, p * 2.0 + t * vec2(0.3, -0.2)).r;
		g += (d / r) * sin(r * 40.0 - t * 9.0) * exp(-max(r - hrac.z, 0.0) * 3.0) * hrac.w * 0.2;
		pena += env * smoothstep(0.35, 0.65, chv) * 0.8;
	}
	// normala ve svete (bez tecen site - hladiny je nemaji vsechny)
	vec3 wn = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
	// okrehek na stojate vode (Lemna: svetle zelena, albedo ~0,3)
	float weed = 0.0;
	if (okrehek > 0.0) {
		float w1 = texture(sum, p * 0.04).r;
		float w2 = texture(sum, p * 0.2 + 0.4).r;
		weed = smoothstep(0.62, 0.68, w1 + (w2 - 0.5) * 0.3) * okrehek;
	}
	// odraz: panorama mlhaveho lesa smerem odrazeneho paprsku (spodni polokoule zrcadlena nahoru), fresnel Schlick
	vec3 V = normalize(CAMERA_POSITION_WORLD - wpos);
	vec3 R = reflect(-V, wn);
	R.y = abs(R.y);
	vec2 puv = vec2(atan(R.z, R.x) / (2.0 * PI) + 0.5, 0.5 - asin(clamp(R.y, -1.0, 1.0)) / PI);
	// sev atan (u 0/1): derivace z posunute souradnice, at mipmapa neskoci na nejhrubsi stupen
	vec2 dx = dFdx(puv), dy = dFdy(puv);
	vec2 dx2 = dFdx(fract(puv + vec2(0.5, 0.0))), dy2 = dFdy(fract(puv + vec2(0.5, 0.0)));
	if (abs(dx2.x) < abs(dx.x)) { dx.x = dx2.x; }
	if (abs(dy2.x) < abs(dy.x)) { dy.x = dy2.x; }
	vec3 refl = textureGrad(panorama, puv, dx, dy).rgb;
	float fres = f0 + (1.0 - f0) * pow(1.0 - max(dot(V, wn), 0.0), f_mocnina);
	vec3 svetlo = mix(vec3(dot(voda_svetlo, vec3(0.3333))), voda_svetlo, odraz_tonovani);
	vec3 telo = mix(telo_kraj, telo_stred, stred);
	float bila = clamp(pena + hreben * 0.25, 0.0, 1.0);
	float kryt = max(weed, bila);
	// telo osvetlene scenou (stiny stromu na nem), odraz v EMISSION (Compatibility nema SSR) x svetlo obzoru
	ALBEDO = mix(mix(telo * (1.0 - fres), vec3(0.2, 0.34, 0.06), weed), pena_barva, bila);
	EMISSION = refl * odraz_nasobek * fres * svetlo * (1.0 - kryt);
	ROUGHNESS = mix(0.05, 0.5, kryt);
	SPECULAR = 0.15 * (1.0 - kryt);                  // jen odlesk slunce - oblohu z enginu nahrazuje panorama
	METALLIC = 0.0;
	// pruhlednost: kraj alfa.x -> stred alfa.y, pod malym uhlem (fresnel) kryje odraz; okraj site se ztraci
	float a = mix(mix(alfa.x, alfa.y, stred), 1.0, fres);
	a = max(a, kryt);
	if (maly_tok) {
		a *= smoothstep(0.02, 0.2, kraj_p);
	} else if (hloubka_vrcholu) {
		a *= smoothstep(0.0, 0.12, v_hl);
	}
	ALPHA = clamp(a, 0.0, 1.0);
}
