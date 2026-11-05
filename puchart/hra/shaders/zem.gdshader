shader_type spatial;
// Terén Puchartu. Povrchy z pole textur (pravidla/svet/pudy.json), podíl z pečené masky stanovišť (nastroje/stanoviste.py):
// R tráva, G opad, B skála (triplanárně – fotka shora by se na strmině natáhla do pruhů, Havran hlášení 0.54), A břeh, zbytek hlína.
// Vzorkovače: 4 (Adreno limit ~13). Žádná kopie obrazovky (pády Havrana 0.58–0.59).
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2DArray pudy_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray pudy_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D maska : filter_linear, repeat_disable;
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
// cesty (nastroje/cesty.py): R vozová (hlína s kamením, Havran „hlina“), G stezka (Havran „pesina“), B skála v úvozu (droby)
uniform sampler2D maska_cesty : filter_linear, repeat_disable;
// koleje vozových cest (nastroje/cesty.py, 0,5 m): 1 − |vzdálenost od osy|/4 m; podle Havrana (zem.gdshader „cesta = tvar“)
uniform sampler2D maska_koleje : filter_linear, repeat_disable;
uniform vec4 maska_rect = vec4(-1172.0, -1107.0, 2000.0, 2000.0); // x0, z0, šířka, výška (svet.json vysek.hra)
uniform float velikost_m[6];          // pudy.json velikost_m
uniform vec3 kalibrace_travy = vec3(0.62, 0.70, 0.52);   // leafy_grass je v létě přesvícená do žluta (snímek 03 – chyba #6)
uniform vec3 barva_lesa_dal = vec3(0.030, 0.050, 0.018);   // v dálce kopec má barvu toho, co na něm roste (Havran radce 11:20)
uniform vec3 barva_louky_dal = vec3(0.075, 0.095, 0.025);   // Havran barva_louky (lineárně)
uniform float dal_od_m = 120.0;
uniform vec3 opad_barva = vec3(1.0);        // pudy.json dalka: lesní půda tmavší
uniform vec3 opad_zelen = vec3(0.3, 0.42, 0.16);
uniform vec2 opad_zelen_podil = vec2(0.0);  // byliny a mech ve skvrnách (šum n2 → min..max)
uniform float dal_do_m = 450.0;
uniform float hlina_odbarveni = 0.45;   // pudy.json hlina
uniform float hlina_jas = 1.25;
uniform vec3 hlina_ton = vec3(1.0);

varying vec3 svet_poz;
varying vec3 svet_nor;

void vertex() {
	svet_poz = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	svet_nor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec3 vrstva(int i, vec2 xz) { return texture(pudy_a, vec3(xz / velikost_m[i], float(i))).rgb; }
// proti opakování (dlaždice 2 m je z 10 m vidět jako mřížka): druhé měřítko pootočené, míchané šumem
const mat2 ROT = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8));
vec3 vrstva2(int i, vec2 xz, float n) {
	vec3 a = texture(pudy_a, vec3(xz / velikost_m[i], float(i))).rgb;
	vec3 b = texture(pudy_a, vec3(ROT * xz / (velikost_m[i] * 3.7), float(i))).rgb;
	return mix(a, b, smoothstep(0.3, 0.7, n));
}
vec3 vrstva_n(int i, vec2 xz) { return texture(pudy_n, vec3(xz / velikost_m[i], float(i))).rgb; }

void fragment() {
	vec2 xz = svet_poz.xz;
	vec2 muv = (xz - maska_rect.xy) / maska_rect.zw;
	vec4 m = texture(maska, muv);
	// mimo výsek (obzor): louka/les podle sklonu
	if (any(lessThan(muv, vec2(0.0))) || any(greaterThan(muv, vec2(1.0)))) {
		float s = 1.0 - svet_nor.y;
		m = vec4(1.0 - smoothstep(0.03, 0.06, s), smoothstep(0.03, 0.06, s), 0.0, 0.0);
	}
	// rozbití opakování: dva měřítka šumu míchají odstín a posouvají hranice vrstev
	float n1 = texture(sum, xz / 23.0).r;
	float n2 = texture(sum, xz / 211.0).r;
	float zbytek = clamp(1.0 - m.r - m.g - m.b - m.a, 0.0, 1.0);
	vec3 w_tr = vec3(0.0);
	vec3 a = vec3(0.0); vec3 nn = vec3(0.0);
	// skála triplanárně
	vec3 bw = pow(abs(svet_nor), vec3(4.0)); bw /= (bw.x + bw.y + bw.z);
	vec3 sk = vrstva(2, svet_poz.zy) * bw.x + vrstva(2, xz) * bw.y + vrstva(2, svet_poz.xy) * bw.z;
	vec3 skn = vrstva_n(2, svet_poz.zy) * bw.x + vrstva_n(2, xz) * bw.y + vrstva_n(2, svet_poz.xy) * bw.z;
	sk = mix(sk, vec3(dot(sk, vec3(0.3, 0.55, 0.15))), 0.6) * vec3(0.95, 0.98, 1.03);   // droba: šedá, ne teplá fotka (fotky Puchartu, ČGS)
	// výšková prolínačka: tráva vyhrává v rovině, opad na hranách se šumem (lem lesa není pravítko)
	float g = clamp(m.g + (n1 - 0.5) * 0.35 * m.g * (1.0 - m.g) * 4.0, 0.0, 1.0);
	float r = m.r * (1.0 - (g - m.g));
	vec3 opad = vrstva2(1, xz, n1) * opad_barva;
	opad = mix(opad, opad * opad_zelen * 2.2, mix(opad_zelen_podil.x, opad_zelen_podil.y, smoothstep(0.3, 0.75, n2)));
	a = vrstva2(0, xz, n1) * kalibrace_travy * r + opad * g + sk * m.b + vrstva(3, xz) * m.a + vrstva(4, xz) * zbytek;
	nn = vrstva_n(0, xz) * r + vrstva_n(1, xz) * g + skn * m.b + vrstva_n(3, xz) * m.a + vrstva_n(4, xz) * zbytek;
	float suma = r + g + m.b + m.a + zbytek;
	a /= max(suma, 0.001); nn /= max(suma, 0.001);
	// cesty přes všechno: hlína / pěšina, kde je zářez, vystupuje drobová skála (šedá, deskovitá)
	vec3 mc = vec3(0.0);
	if (all(greaterThanEqual(muv, vec2(0.0))) && all(lessThanEqual(muv, vec2(1.0)))) mc = texture(maska_cesty, muv).rgb;
	float wc = clamp(mc.r + mc.g, 0.0, 1.0);
	float nn_kol = 0.0;
	if (wc > 0.001) {
		vec3 ca = (vrstva(4, xz) * mc.r + vrstva(5, xz) * mc.g) / max(mc.r + mc.g, 0.001);
		// podloží droby/břidlice: hlína šedohnědá, ne červená (fotka stony_dirt_path je teplá) – odbarvit a zesvětlit
		ca = mix(ca, vec3(dot(ca, vec3(0.3, 0.55, 0.15))), hlina_odbarveni) * hlina_jas * hlina_ton;   // pudy.json hlina (zvětralá droba: hnědošedá, okrová)
		vec3 cn = (vrstva_n(4, xz) * mc.r + vrstva_n(5, xz) * mc.g) / max(mc.r + mc.g, 0.001);
		// vozová cesta jako Havran: dvě vyjeté koleje (tmavší, vlhčí, utlačené), mezi nimi travnatý hřbet v úsecích,
		// prach a kamínky na krajích; koleje místy mizí (vyjeté jen místy), okraj zubatý (Míša 5. 11.)
		if (mc.r > 0.05) {
			float kv = texture(maska_koleje, muv).r;
			if (kv > 0.0) {
				float dk = (1.0 - kv) * 4.0;                                   // |vzdálenost od osy| m
				float n_s = texture(sum, xz * 0.031).r;                       // pomalý šum podél cesty
				float roz = 0.68 + (n_s - 0.5) * 0.18;                        // polovina rozchodu (kolísá)
				float kol = (1.0 - smoothstep(0.12, 0.30, abs(dk - roz))) * smoothstep(0.25, 0.55, n_s + n1 * 0.4);
				float hrb = (1.0 - smoothstep(0.18, 0.42, dk)) * smoothstep(0.45, 0.7, texture(sum, xz * 0.09 + 3.1).r);
				vec3 trava = vrstva2(0, xz, n1) * kalibrace_travy;
				ca = mix(ca, ca * vec3(0.62, 0.6, 0.58), kol * 0.75);           // koleje tmavší a vlhčí
				ca = mix(ca, mix(ca, trava, 0.75), hrb * mc.r);                 // travnatý hřbet
				float kraj = smoothstep(1.0, 1.7, dk) * (1.0 - smoothstep(1.9, 2.4, dk));
				ca = mix(ca, mix(ca, sk * 0.9, 0.35), kraj * smoothstep(0.55, 0.8, n2));   // kamínky na krajích
				nn_kol = kol;
			}
		}
		float sk_w = clamp(mc.b * (0.6 + n1 * 0.8), 0.0, 1.0);
		ca = mix(ca, sk * vec3(0.78, 0.8, 0.84), sk_w); cn = mix(cn, skn, sk_w);
		cn = mix(cn, vec3(0.5, 0.5, 1.0), nn_kol * 0.4);   // koleje utlačené, hladší (Havran)
		a = mix(a, ca, wc); nn = mix(nn, cn, wc);
	}
	a *= mix(0.82, 1.12, n2);
	// dálka: barva porostu místo fotky půdy (les z dálky = koruny, ne opad)
	float d = length(VERTEX);
	float t = smoothstep(dal_od_m, dal_do_m, d);
	vec3 dal = mix(barva_louky_dal, barva_lesa_dal, clamp(g + m.b * 0.3, 0.0, 1.0)) * mix(0.85, 1.1, n2);
	ALBEDO = mix(a, dal, t);
	// síť nemá tečny: normálu fotky přidat ve světě (osa u = +x, v = -z; OpenGL normály), v dálce vypnout
	vec3 tn = (nn * 2.0 - 1.0) * (1.0 - t);
	vec3 wn = normalize(svet_nor + vec3(tn.x, 0.0, -tn.y) * 0.8);
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
	ROUGHNESS = 1.0;
	SPECULAR = 0.08;   // 0,3 dávalo v protisvětle žlutý lesk pásu 100–300 m (snímek 01)
}
