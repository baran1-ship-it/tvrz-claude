shader_type spatial;
// Voda (prikop, rybnik, potok): lom svetla (dno se vlni pod hladinou), odraz oblohy podle uhlu pohledu,
// dve posouvane normalove mapy (potok po proudu s penou), okrehek na stojate vode, kruhove vlnky
// (zaba, ryba, kroky hrace) a ceřeni kolem nohou, kdyz hrac stoji ve vode.
render_mode blend_mix, depth_draw_always, cull_back, specular_schlick_ggx;

uniform sampler2D nmap : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform sampler2D obraz : hint_screen_texture, filter_linear_mipmap;
uniform vec3 deep : source_color = vec3(0.02, 0.045, 0.04);
uniform vec3 zakal : source_color = vec3(0.09, 0.11, 0.07);
uniform float kalnost = 0.75;     // 0 cista (dno videt) .. 1 neprusvitna
uniform float tekouci = 0.0;      // potok: UV.x = delka po proudu (m/4)
uniform float okrehek = 0.0;      // stojata voda: ostruvky okrehku
uniform vec4 rip[8];              // x, z, cas vzniku (jako TIME), sila
uniform vec4 hrac = vec4(0.0, 0.0, 0.0, 0.0);   // x, z, polomer kolem nohou, sila (0 = hrac neni ve vode)
uniform vec2 vitr = vec2(0.8, 0.6);               // stojata voda: smer vetru (vlnky a poryvy po vetru)

varying vec3 wpos;
varying float v_pena;       // potok: pena kolem a za kameny (barva vrcholu R z Blenderu)
varying float v_perej;      // potok: perej / brod (G)
varying vec2 v_tok;         // potok: smer toku (B, A z Blenderu, vyhlazeny)

// vzorek tekouci hladiny v jedne fazi mapy proudeni: souradnice posunute po proudu, protazene po toku
vec4 tok_vzorek(vec2 p, vec2 tok, float ph, float rych) {
	vec2 bok = vec2(-tok.y, tok.x);
	vec2 q = p - tok * (ph * rych * 2.857);
	vec2 a = vec2(dot(q, tok) * 0.6, dot(q, bok) * 1.1);
	vec3 n1 = texture(nmap, a * 0.3).rgb;
	vec3 n2 = texture(nmap, a * 0.66 + 0.5).rgb;
	float s1 = texture(sum, a * 0.45).r;
	float s2 = texture(sum, a * 0.95 + 0.3).r;
	vec2 nxy = mix(n1.xy, n2.xy, 0.5) - 0.5;
	// normala z prostoru toku zpet do sveta
	vec2 w = tok * nxy.x + bok * nxy.y;
	return vec4(w + 0.5, s1, s2);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	v_pena = 0.0;
	v_perej = 0.0;
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
	vec3 nm;
	float pena = 0.0;
	if (tekouci > 0.5) {
		// mapa proudeni: dve faze posunute o pul periody, prolinaji se (zadne svy v ohybech toku)
		float rych = 0.8 + 1.3 * v_perej;
		float ph0 = fract(TIME * 0.35);
		float ph1 = fract(TIME * 0.35 + 0.5);
		float wg = abs(1.0 - 2.0 * ph0);
		vec4 A = tok_vzorek(p, v_tok, ph0, rych);
		vec4 B = tok_vzorek(p + vec2(3.7, 1.9), v_tok, ph1, rych);
		vec4 F = mix(A, B, wg);
		nm = vec3(0.5 + (F.x - 0.5) * (1.0 + 0.8 * v_perej), 0.5 + (F.y - 0.5) * (1.0 + 0.8 * v_perej), 1.0);
		float s1 = F.z;
		float s2 = F.w;
		// pena: ve stopach za kameny tece a trha se, v perejich prouzky, u brehu ojedinele chomacky
		float stopa = smoothstep(0.3, 0.7, s2 + v_pena * 0.5 - 0.15);
		pena = max(pena, v_pena * stopa);
		pena = max(pena, v_perej * smoothstep(0.6, 0.74, s1 * 0.6 + s2 * 0.5) * 0.7);
		pena = max(pena, smoothstep(0.7, 0.84, s1 * 0.6 + s2 * 0.5) * (1.0 - smoothstep(0.3, 1.2, UV.y)) * 0.4);
	} else {
		// stojata voda: drobne vlnky po vetru, poryvy (tmave cerene skvrny) tahnou po hladine
		vec2 vd = normalize(vitr);
		vec2 vp = vec2(-vd.y, vd.x);
		vec2 uv = vec2(dot(p, vd), dot(p, vp)) * 0.09;
		vec3 n1 = texture(nmap, uv * vec2(1.0, 1.6) - vec2(TIME * 0.03, 0.0)).rgb;
		vec3 n2 = texture(nmap, uv * 1.7 - vec2(TIME * 0.045, TIME * 0.008)).rgb;
		vec3 n3 = texture(nmap, uv * 4.3 * vec2(1.0, 1.5) - vec2(TIME * 0.09, 0.0)).rgb;
		float poryv = smoothstep(0.45, 0.75, texture(sum, p * 0.025 - vd * TIME * 0.035).r);
		nm = mix(mix(n1, n2, 0.5), n3, 0.25 + 0.45 * poryv);
		nm.xy = (nm.xy - 0.5) * (0.6 + 1.2 * poryv) + 0.5;
	}
	// kruhove vlnky: soustredne hrebeny se rozbihaji a slabnou
	vec2 g = vec2(0.0);
	float hreben = 0.0;
	for (int i = 0; i < 8; i++) {
		float age = TIME - rip[i].z;
		if (age > 0.0 && age < 4.0 && rip[i].w > 0.0) {
			vec2 d = p - rip[i].xy;
			float r = length(d) + 1e-4;
			float x = r - age * 0.55;
			float env = exp(-x * x * 7.0) * (1.0 - age / 4.0) * rip[i].w / (1.0 + r * 0.6);
			g += (d / r) * cos(x * 28.0) * env;
			hreben += max(cos(x * 28.0), 0.0) * env;
		}
	}
	// ceřeni kolem nohou (hrac stoji nebo se brodi)
	if (hrac.w > 0.0) {
		vec2 d = p - hrac.xy;
		float r = length(d) + 1e-4;
		float x = r - hrac.z;
		float env = exp(-x * x * 30.0) * hrac.w;
		float chv = texture(sum, p * 2.0 + TIME * vec2(0.3, -0.2)).r;
		g += (d / r) * sin(r * 40.0 - TIME * 9.0) * exp(-max(r - hrac.z, 0.0) * 3.0) * hrac.w * 0.5;
		pena += env * smoothstep(0.35, 0.65, chv) * 0.8;
	}
	nm.xy += g * 0.4;
	NORMAL_MAP = nm;
	NORMAL_MAP_DEPTH = 0.7;

	// okrehek na stojate vode
	float weed = 0.0;
	if (okrehek > 0.0) {
		float w1 = texture(sum, p * 0.04).r;
		float w2 = texture(sum, p * 0.2 + 0.4).r;
		weed = smoothstep(0.62, 0.68, w1 + (w2 - 0.5) * 0.3) * okrehek;
	}

	// lom: obraz pod hladinou posunuty podle vlnek; zdalky a pod malym uhlem odraz oblohy
	vec3 nv = normalize(NORMAL + VIEW_MATRIX[0].xyz * (nm.x - 0.5) * 0.6 + VIEW_MATRIX[2].xyz * (nm.y - 0.5) * 0.6);
	float fres = 0.04 + 0.96 * pow(1.0 - clamp(dot(nv, VIEW), 0.0, 1.0), 5.0);
	vec2 off = (nm.xy - 0.5) * 0.045 + g * 0.02;
	vec3 dno = texture(obraz, SCREEN_UV + off).rgb;
	float hloubka = clamp(-VERTEX.z / 60.0, 0.0, 1.0);       // dal = vic zakalu
	float op = clamp(mix(kalnost, 1.0, hloubka * 0.6), 0.0, 1.0);
	vec3 telo = mix(zakal, deep, 0.6);
	vec3 lom = mix(dno * vec3(0.72, 0.85, 0.78), telo, op);
	float bila = clamp(pena + hreben * 0.25, 0.0, 1.0);
	vec3 povrch = mix(vec3(0.01), vec3(0.06, 0.1, 0.03), weed);
	ALBEDO = mix(povrch, vec3(0.55, 0.57, 0.52), bila);
	ALBEDO = mix(ALBEDO, vec3(0.1, 0.18, 0.03), weed);
	EMISSION = lom * (1.0 - fres) * (1.0 - weed) * (1.0 - bila);
	ROUGHNESS = mix(0.03, 0.5, max(weed, bila));
	SPECULAR = mix(0.6, 0.2, weed);
	METALLIC = 0.0;
	ALPHA = 1.0;
}
