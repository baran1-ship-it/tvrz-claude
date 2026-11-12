// Skála jako v KCD (Míša 10. 11.: „ostré hrany jak kostky v minecraftu, chceme kvalitu KCD“; reference
// docs/reference/kcd2/ref_kcd2_vez_skala.jpg, misa_trosky_most_skala.png): světová triplanární projekce fotky droby
// s plynulým přechodem mezi osami, velké tónové skvrny (zvětralá hnědošedá až rezavá, tmavý lišejník), svislé stékance
// na stěnách, mech souvisle i na šikmých stěnách (skutečné fotky docs/reference/puchart_skaly: tmavá droba, mech). 6 vzorkovačů (Adreno ≤ 13), hash bez sin().
shader_type spatial;

uniform sampler2D tex_a : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float meritko = 0.38;          // 1 / velikost fotky v m
uniform float jas = 0.78;
uniform vec3 barva_droby = vec3(0.62, 0.66, 0.68);   // tmavě modrošedá droba (fotky puchart_skaly)
uniform float mech = 0.0;              // 1 = police s mechem (skala_mech)
uniform vec3 barva_mech = vec3(0.26, 0.30, 0.15);   // tmavě olivový mech (fotky puchart_skaly)
uniform vec3 barva_rez = vec3(1.12, 0.98, 0.80);
uniform vec3 barva_lisejnik = vec3(0.55, 0.57, 0.52);

varying vec3 wp;
varying vec3 wn;

float hash(vec2 p) { p = mod(p, 1024.0); vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { return noise(p) * 0.55 + noise(p * 2.1 + 7.3) * 0.3 + noise(p * 4.3 + 1.7) * 0.15; }

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

uniform float mokro = 0.0;   // déšť (pocasi.gd): 0 sucho .. 1 promoklé – tmavší, lesklejší (KCD: mokré povrchy a louže)
void fragment() {
	vec3 n = normalize(wn);
	vec3 w = pow(abs(n), vec3(4.0)); w /= (w.x + w.y + w.z);
	vec2 ux = wp.zy * meritko; vec2 uy = wp.xz * meritko; vec2 uz = wp.xy * meritko;
	vec3 c = texture(tex_a, ux).rgb * w.x + texture(tex_a, uy).rgb * w.y + texture(tex_a, uz).rgb * w.z;
	vec3 tnx = texture(tex_n, ux).rgb * 2.0 - 1.0; vec3 tny = texture(tex_n, uy).rgb * 2.0 - 1.0; vec3 tnz = texture(tex_n, uz).rgb * 2.0 - 1.0;
	// whiteout blend normál ve světě
	vec3 nx = vec3(0.0, tnx.y, tnx.x) * w.x; vec3 ny = vec3(tny.x, 0.0, tny.y) * w.y; vec3 nz = vec3(tnz.x, tnz.y, 0.0) * w.z;
	vec3 nw = normalize(n + (nx + ny + nz) * 1.8);
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	// tónové skvrny ve velkém (každý výchoz jinak zvětralý), lišejník, rezavé fleky
	float g = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(g) * barva_droby, 0.6);
	float t1 = fbm(wp.xz * 0.11 + wp.y * 0.05);
	float t2 = fbm(vec2(wp.x + wp.z, wp.y) * 0.35 + 3.1);
	c *= 0.72 + 0.55 * t1;
	c = mix(c, c * barva_rez, smoothstep(0.45, 0.75, fbm(wp.xz * 0.23 + vec2(wp.y * 0.3, 5.0))));
	c = mix(c, barva_lisejnik * g * 1.4, smoothstep(0.6, 0.8, t2) * 0.6);
	// svislé stékance na stěnách
	float st = smoothstep(0.55, 0.8, noise(vec2((wp.x + wp.z) * 1.7, wp.y * 0.12))) * (1.0 - w.y);
	c *= 1.0 - st * 0.3;
	// mech: nahoru hledící plochy a police (mech), šum ve skvrnách
	// mech jen místy (Míša 10. 11. nad fotkou 88596: „ty to máš na velkých plochách, originál je má sem tam“): skvrny ~1–2 m,
	// hlavně na římsách a mírnějších plochách, na strmé stěně jen ojediněle; mezi nimi holá droba
	float up = smoothstep(0.0, 0.75, n.y);
	float sk = fbm(wp.xz * 0.9 + vec2(wp.y * 0.8, 1.3)) * 0.7 + noise(wp.xz * 3.1 + wp.y * 2.3) * 0.3;
	float m = smoothstep(0.68, 0.8, sk + 0.12 * up + mech * 0.06 + (0.45 - g) * 0.35) * (0.35 + 0.65 * up);   // víc v tmavých puklinách textury
	c = mix(c, barva_mech * (0.35 + 1.3 * g), m);   // struktura kamene prosvítá
	ALBEDO = c * jas;
	ROUGHNESS = mix(0.95, 0.85, m);
	SPECULAR = 0.25;
	ALBEDO *= mix(1.0, 0.66, mokro); ROUGHNESS = mix(ROUGHNESS, 0.45, mokro); SPECULAR = mix(SPECULAR, 0.4, mokro);   // mokro (pocasi.gd)
}
