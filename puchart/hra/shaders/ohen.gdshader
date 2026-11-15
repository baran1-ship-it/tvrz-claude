// Oheň (Míša 15. 11.: „dodělej ohně… moc se mi nelíbí jejich vzhled“ – Havranovy CPUParticles = rozmazané skvrny).
// Jeden shader pro plamen i žhavé uhlíky (stejný program = jedno sestavení na Adrenu, predehrati.gd):
// - plamen (rezim 0): 3 křížené svislé karty (ohne.gd _sit_plamene), tvar kapky a barva bílá–žlutá–oranžová–červená
//   počítané zde, jedna dlaždicová šumová textura (textury/ohen_sum.png, R = jazyky, G = chvění) čtená 2× s posunem
//   nahoru, vlnění vrcholů; karta natočená hranou ke kameře se ztlumí (nevidět „čáru“).
// - uhlíky (rezim 1): plochý disk, svislý pruh v ústí pece (ohne.gd _karta) nebo překryv sítě žáru (Kovarna_Zhar,
//   material_overlay), žhnutí ze šumu ve světových souřadnicích a pomalé pulzování.
// Aditivní, neosvětlené, bez zápisu hloubky, bez stínu a mlhy; čísla vzhledu z dat (ohne.json plamen / uhliky).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled, specular_disabled;

uniform sampler2D sum_tex : filter_linear_mipmap, repeat_enable;
uniform int rezim = 0;              // 0 plamen, 1 uhlíky
uniform float sila = 1.0;           // celkový jas (0 = zhasnuto)
uniform float rychlost = 1.1;       // stoupání šumu (výšek karty za s)
uniform float vlneni = 0.04;        // vlnění vrcholů (m na 1 m výšky)
uniform float eroze = 0.75;         // jak moc šum ukusuje kraje a špičku
uniform vec3 barva_jadro : source_color = vec3(1.0, 0.96, 0.8);
uniform vec3 barva_zluta : source_color = vec3(1.0, 0.78, 0.3);
uniform vec3 barva_oranz : source_color = vec3(1.0, 0.42, 0.08);
uniform vec3 barva_cervena : source_color = vec3(0.55, 0.08, 0.02);
uniform float uhliky_meritko = 3.0; // buňky žáru na metr
uniform float uhliky_pulz = 0.6;    // rychlost pulzování (Hz)

varying float v_cast;    // náhodná fáze karty (barva vrcholu R)
varying float v_celem;   // jak moc karta míří ke kameře
varying vec3 v_wp;

void vertex() {
	v_cast = COLOR.r;
	v_wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (rezim == 0) {
		float y = UV.y;   // 0 dole, 1 nahoře
		float t = TIME * 2.3 + v_cast * 17.0 + v_wp.x * 3.1 + v_wp.z * 2.7;
		VERTEX.x += (sin(t) * 0.6 + sin(t * 2.1 + 1.3) * 0.4) * vlneni * y * y;
		VERTEX.z += (cos(t * 1.3) * 0.6 + sin(t * 2.7) * 0.4) * vlneni * y * y;
		vec3 n = normalize((MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
		vec3 k = normalize(-(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz);
		v_celem = abs(dot(n, k));
	} else {
		v_celem = 1.0;
	}
}

vec3 rampa(float h) {   // teplota 0..1 → červená, oranžová, žlutá, bílé jádro
	vec3 c = mix(barva_cervena, barva_oranz, smoothstep(0.08, 0.38, h));
	c = mix(c, barva_zluta, smoothstep(0.38, 0.66, h));
	return mix(c, barva_jadro, smoothstep(0.7, 0.95, h));
}

void fragment() {
	if (rezim == 0) {
		vec2 uv = UV; float y = uv.y;
		// dvě čtení téže textury, různé měřítko a rychlost stoupání (šum jede nahoru = plamen stoupá)
		float n1 = texture(sum_tex, vec2(uv.x * 0.7 + v_cast, y * 0.55 - TIME * rychlost)).r;
		float n2 = texture(sum_tex, vec2(uv.x * 1.4 - v_cast * 1.7, y * 1.1 - TIME * rychlost * 1.9)).g;
		float n = n1 * 0.62 + n2 * 0.38;
		// tvar kapky: nejširší ve čtvrtině výšky, ke špičce se zužuje; šum ohýbá osu
		float x = abs(uv.x - 0.5 + (n - 0.5) * 0.35 * y) * 2.0;
		float w = pow(clamp(1.0 - y, 0.0, 1.0), 0.75) * (0.55 + 0.45 * smoothstep(0.0, 0.22, y));
		float tvar = clamp(1.0 - x / max(w, 0.001), 0.0, 1.0);
		float f = tvar - (1.0 - n) * eroze * (0.35 + 0.65 * y);
		f = smoothstep(0.0, 0.45, f) * smoothstep(0.0, 0.06, y);
		float h = f * (1.1 - 0.45 * y);
		vec3 c = rampa(h);
		ALBEDO = c * (0.6 + 1.2 * h) * sila;
		ALPHA = clamp(f * 1.3, 0.0, 1.0) * smoothstep(0.08, 0.45, v_celem);
	} else {
		vec2 p = vec2(v_wp.x + v_wp.z * 0.7, v_wp.z * 0.7 + v_wp.y) * uhliky_meritko;   // i svislý pruh v ústí pece (ne jen vodorovný disk)
		float a = texture(sum_tex, p * 0.25).g;
		float b = texture(sum_tex, p * 0.11 + vec2(TIME * 0.01, 0.0)).r;
		float r = length(UV - 0.5) * 2.0;   // disk: k okraji slábne (překryv žáru má vlastní UV – ořez měkký)
		float okraj = 1.0 - smoothstep(0.55, 1.0, r);
		float puls = 0.75 + 0.25 * sin(TIME * uhliky_pulz * 6.2832 + b * 9.0);
		float g = smoothstep(0.38, 0.72, a * 0.6 + b * 0.5) * puls * okraj;
		ALBEDO = rampa(0.1 + g * 0.45) * g * 1.5 * sila;
		ALPHA = clamp(g, 0.0, 1.0);
	}
}
