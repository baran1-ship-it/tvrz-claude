shader_type spatial;
// Fotograficky material: UV v metrech (kvadry, tramy, prkna) nebo svetove promitani (podlahy, omitky).
#include "res://shaders/projekce.gdshaderinc"

uniform sampler2D tex_a : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D tex_r : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float velikost = 2.0;
uniform bool prohodit = false;
uniform bool svet = false;
uniform vec3 tint = vec3(1.0);
uniform float sedost = 0.0;
uniform vec3 tint2 = vec3(1.0);    // druhy odstin: kazdy kus (COLOR.b) je nekde mezi tint a tint2
uniform float pestrost = 0.0;
uniform float spina_dole = 0.0;
uniform sampler2D tex_h : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float hloubka = 0.0;       // parallax, metry
uniform vec2 h_rozsah = vec2(0.2, 0.9);
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform float skvrny = 0.0;        // velke skvrny (vlhko, vybledle misto) ve svetovych souradnicich
uniform float antitile = 0.0;
uniform float stekance = 0.0;      // drevo a omitka venku: svisle tmave stekance od deste, zasedle a zcernale skvrny      // skaly: druhe pootocene meritko textury mezi skvrnami (neni videt opakovani)

varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 uv;
	vec3 t; vec3 b;
	vec3 n = normalize(wn);
	if (svet) {
		projekce(wp, n, uv, t, b);
	} else {
		uv = UV;
		if (prohodit) { uv = uv.yx; }
	}
	uv /= velikost;
	float hgt = 1.0;
	if (hloubka > 0.0) {
		vec3 vt;
		if (svet) {
			vec3 v = normalize(CAMERA_POSITION_WORLD - wp);
			vt = vec3(dot(v, t), dot(v, b), dot(v, n));
		} else {
			// UV rezim: tecny prostor z TANGENT/BINORMAL (stejne jako vyskova mapa StandardMaterial3D)
			vt = normalize(VIEW * mat3(TANGENT, -BINORMAL, NORMAL));
		}
		float fade = (1.0 - smoothstep(10.0, 22.0, length(CAMERA_POSITION_WORLD - wp))) * smoothstep(0.12, 0.45, vt.z);
		vec2 dp = vt.xy / max(vt.z, 0.3) * (hloubka * fade / velikost) / 10.0;
		float cur = 1.0;
		float hh = smoothstep(h_rozsah.x, h_rozsah.y, texture(tex_h, uv).r);
		for (int i = 0; i < 10; i++) {
			if (hh >= cur || fade <= 0.0) break;
			cur -= 0.1;
			uv -= dp;
			hh = smoothstep(h_rozsah.x, h_rozsah.y, texture(tex_h, uv).r);
		}
		hgt = hh;
	}
	// odstin kusu (COLOR.r) jen u UV materialu; u omitek by delal viditelne bloky
	// nejdriv odbarvit fotku (sedost), pak obarvit odstinem kusu: kamen muze byt pisk. nebo sedy nezavisle na fotce
	vec3 c = texture(tex_a, uv).rgb;
	float atm = 0.0;
	vec2 uv2 = uv;
	if (antitile > 0.0) {
		// druhe vzorkovani: jine meritko, pootocene a posunute; prolinani podle velkych skvrn ve svete
		uv2 = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * uv * 0.61 + vec2(0.37, 0.71);
		float m = texture(sum, wp.xz * 0.06 + vec2(wp.y * 0.05, 0.0)).r;
		atm = smoothstep(0.35, 0.65, m) * antitile;
		c = mix(c, texture(tex_a, uv2).rgb, atm);
		// jemne preruseni pravidelnosti: treti, velmi velke meritko jen do jasu
		c *= 0.8 + 0.4 * texture(tex_a, uv * 0.17 + 0.5).g;
		// mech: na plochach, ktere hledi nahoru (rimsy, vrsky), v pruzich i v zastinenych zlabcich
		float mk = smoothstep(0.15, 0.6, n.y) * smoothstep(0.35, 0.65, texture(sum, wp.xz * 0.11 + wp.y * 0.05).r + 0.2);
		mk = max(mk, smoothstep(0.62, 0.8, texture(sum, wp.xz * 0.21 + vec2(wp.y * 0.13)).r) * 0.6);
		vec3 mech = mix(vec3(0.1, 0.16, 0.05), vec3(0.24, 0.3, 0.09), texture(sum, wp.xz * 0.9 + wp.y * 0.7).r);
		c = mix(c, mech, mk * 0.9);
	}
	float g = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(g, g * 0.97, g * 0.9), sedost);
	vec3 tn = mix(tint, tint2, COLOR.b * pestrost);
	c *= tn * (svet ? 1.0 : COLOR.r);
	c = mix(c, vec3(0.06, 0.05, 0.035), (1.0 - smoothstep(-0.2, 1.0, wp.y)) * spina_dole);
	c *= mix(0.6, 1.0, smoothstep(0.0, 0.5, hgt));
	if (skvrny > 0.0) {
		float n1 = texture(sum, wp.xz * 0.045 + wp.y * 0.03).r;
		float n2 = texture(sum, wp.xz * 0.11 + 0.37).r;
		c *= mix(1.0, mix(0.62, 1.18, n1), skvrny);                       // vlhka tmava / vybledla mista
		c = mix(c, c * vec3(0.85, 0.9, 0.7), smoothstep(0.62, 0.75, n2) * skvrny * 0.6);  // nazelenaly lisejnik
	}
	if (stekance > 0.0) {
		float h = wp.x * 0.93 + wp.z * 1.07;
		float st = texture(sum, vec2(h * 0.9, wp.y * 0.035)).r;            // svisle protazeny sum = stekance
		float st2 = texture(sum, vec2(h * 2.3 + 0.4, wp.y * 0.06)).r;
		float tm = smoothstep(0.55, 0.8, st) * 0.45 + smoothstep(0.6, 0.85, st2) * 0.3;
		c *= 1.0 - tm * stekance;
		float sk = texture(sum, vec2(h * 0.35, wp.y * 0.3) + 0.77).r;      // zasedle / vybledle fleky
		c = mix(c, c * vec3(1.15, 1.12, 1.05), smoothstep(0.65, 0.8, sk) * stekance * 0.5);
		c = mix(c, c * vec3(0.55, 0.5, 0.45), smoothstep(0.72, 0.9, texture(sum, vec2(h * 1.7, wp.y * 1.3) + 0.13).r) * stekance * 0.6);
	}
	ALBEDO = c;
	AO = mix(0.4, 1.0, smoothstep(0.0, 0.45, hgt));
	AO_LIGHT_AFFECT = 0.5;
	ROUGHNESS = mix(texture(tex_r, uv).r, texture(tex_r, uv2).r, atm);
	SPECULAR = 0.35;
	vec3 nm = mix(texture(tex_n, uv).rgb, texture(tex_n, uv2).rgb, atm) * 2.0 - 1.0;
	if (svet) {
		NORMAL = normalize((VIEW_MATRIX * vec4(normala_svet(nm, t, b, n), 0.0)).xyz);
	} else {
		if (prohodit) { nm = vec3(nm.y, nm.x, nm.z); }
		NORMAL_MAP = nm * 0.5 + 0.5;
	}
}
