// Fotografický materiál bez rastru – převzato z Havrana (shaders/textura.gdshader, scripts/svet.gd material()) a zjednodušeno
// na 3 vzorkovače (Adreno ≤ 13) s procedurálním šumem místo textury šumu. Míša 5. 11.: „vše je jen rastr, střecha a kámen
// vše máš stejné“, „inspiruj se ve skutečnosti a v Havranovi“.
//  radky   – šindel: oblasti s posunutým vzorem po řadách (pokládka není mřížka), tmavší/světlejší řady
//  kus     – dřevo: každý kus (COLOR.b = semeno z atributu rnd) jiný výřez fotky, po délce střídání jasu, zasedlé skvrny, odřeniny
//  antitile– kámen: druhé pootočené vzorkování mezi skvrnami, mech na plochách hledících nahoru
//  stekance– venku: svislé tmavé stékance od deště
//  skvrny  – velké vlhké / vybledlé fleky, nazelenalý lišejník
//  budova  – velký tón ve světě (~20 m): každá střecha a stavba jinak stará (sešedlá, tmavší, mechová)
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D tex_a : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D tex_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec3 tint = vec3(1.0);
uniform vec3 tint2 = vec3(1.0);
uniform float pestrost = 0.0;
uniform float radky = 0.0;
uniform float kus = 0.0;
uniform float antitile = 0.0;
uniform float stekance = 0.0;
uniform float skvrny = 0.0;
uniform float budova = 0.0;
uniform float mech = 0.0;
uniform float jas = 1.0;
uniform float sedost = 0.0;   // zvětralé dřevo zešedne (KCD: stříbřitě šedý šindel a prkna)

varying vec3 wp;
varying vec3 wn;

// hash bez sinu (Dave Hoskins „Hash without Sine“): sin(velké číslo) na Adreno ztrácí přesnost → šum po čtvercích
// („minecraft“, Míša 9. 11.); vstup zabalený do 1024 m, aby fract() neztrácel bity na souřadnicích stovek metrů
float hash(vec2 p) { p = mod(p, 1024.0); vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 nw = FRONT_FACING ? wn : -wn;   // oboustranné desky (střechy): rub se svítí jako líc
	vec2 uv = UV;
	vec2 uv2 = uv;
	float atm = 0.0;
	vec3 c = texture(tex_a, uv).rgb;
	float sd = COLOR.b;
	if (antitile > 0.0) {
		uv2 = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * uv * 0.61 + vec2(0.37, 0.71);
		atm = smoothstep(0.35, 0.65, noise(wp.xz * 0.3 + vec2(wp.y * 0.25, 0.0))) * antitile;
		c = mix(c, texture(tex_a, uv2).rgb, atm);
	}
	if (radky > 0.0) {
		uv2 = uv + vec2(0.37, 0.0);
		atm = smoothstep(0.45, 0.55, noise(wp.xz * 0.9 + vec2(wp.y * 0.7, 0.0))) * radky;
		c = mix(c, texture(tex_a, uv2).rgb, atm);
		c = mix(c, texture(tex_a, uv + vec2(0.71, 0.13)).rgb, smoothstep(0.52, 0.62, noise(wp.xz * 0.55 + vec2(3.1, wp.y * 0.5))) * radky);
		c *= mix(1.0, 0.8 + 0.4 * noise(wp.xz * 2.1 + wp.y * 1.3), radky);
	}
	if (kus > 0.0) {
		float al = uv.x; float ac = uv.y;
		uv2 = uv * vec2(0.83, 0.77) + vec2(0.37 + sd * 3.17, 0.61 + sd * 5.31);
		atm = smoothstep(0.46, 0.54, noise(vec2(al * 0.9 + sd * 7.3, sd * 2.9))) * kus;
		c = mix(c, texture(tex_a, uv2).rgb, atm);
		c *= mix(1.0, 0.75 + 0.5 * noise(vec2(al * 0.45 + sd * 3.7, 0.5 + sd * 9.0)), kus);
		c = mix(c, c * vec3(0.55, 0.5, 0.46), smoothstep(0.68, 0.84, noise(vec2(al * 3.6 + sd * 11.0, ac * 3.6 + sd * 5.0))) * 0.7 * kus);
		c = mix(c, c * vec3(1.22, 1.15, 1.06), smoothstep(0.72, 0.86, noise(vec2(al * 2.2 + sd * 2.0 + 0.3, ac * 5.6 + sd * 9.0))) * 0.5 * kus);
	}
	float gg = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(gg * 1.03, gg, gg * 0.94), sedost) * jas;
	vec3 tn = mix(tint, tint2, sd * pestrost);
	c *= tn * mix(1.0, COLOR.r, kus + antitile * 0.5);
	if (budova > 0.0) {   // každá stavba jinak stará: velký šum ve světě
		float b1 = noise(wp.xz / 23.0 + 7.7); float b2 = noise(wp.xz / 17.0 + 2.3);
		c *= mix(1.0, 0.78 + 0.4 * b1, budova);
		float g = dot(c, vec3(0.3, 0.59, 0.11));
		c = mix(c, vec3(g * 1.02, g, g * 0.95), smoothstep(0.45, 0.85, b2) * 0.55 * budova);   // sešedlé (starší) střechy
	}
	if (mech > 0.0) {   // mech a lišejník na plochách hledících nahoru, víc u okapu a na severu
		float mk = smoothstep(0.25, 0.7, abs(nw.y)) * smoothstep(0.6, 0.85, noise(wp.xz * 0.7 + wp.y * 0.3) + 0.1 * (-nw.z));
		vec3 mc = mix(vec3(0.12, 0.15, 0.06), vec3(0.26, 0.29, 0.12), noise(wp.xz * 4.0 + wp.y));
		c = mix(c, mc, mk * 0.45 * mech);
	}
	if (skvrny > 0.0) {
		float n1 = noise(wp.xz * 0.18 + wp.y * 0.12); float n2 = noise(wp.xz * 0.45 + 0.37);
		c *= mix(1.0, mix(0.68, 1.15, n1), skvrny);
		c = mix(c, c * vec3(0.85, 0.9, 0.72), smoothstep(0.62, 0.78, n2) * skvrny * 0.6);
	}
	if (stekance > 0.0) {
		float h = wp.x * 0.93 + wp.z * 1.07 + sd * 3.1 * kus;
		float st = noise(vec2(h * 1.2, wp.y * 0.08)); float st2 = noise(vec2(h * 3.1 + 0.4, wp.y * 0.15));
		c *= 1.0 - (smoothstep(0.58, 0.82, st) * 0.3 + smoothstep(0.62, 0.86, st2) * 0.18) * stekance;
	}
	ALBEDO = c * mix(0.5, 1.0, COLOR.g);   // zapečené stínění (hrady.zapec_ao)
	AO = COLOR.g; AO_LIGHT_AFFECT = 0.6;
	ROUGHNESS = mix(texture(tex_r, uv).r, texture(tex_r, uv2).r, atm);
	SPECULAR = 0.35;
	NORMAL_MAP = mix(texture(tex_n, uv).rgb, texture(tex_n, uv2).rgb, atm);
}
