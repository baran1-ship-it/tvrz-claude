shader_type spatial;
// Pad kaskady potoka (scripts/pad_vody.gd, Misa 15. 11. r. 4: pady jako ploche leskle plechy). Bez lesku a bez
// screen texture (tablet, Compatibility): voda = pruhy peny z foam_noise posouvane po proudu, dva vzorky s ruznym
// meritkem a rychlosti (Uncharted GDC 2012, Jedi Fallen Order - simonschreibt.de). Cisla z voda.json pad_vody.shader.
//  druh 0 zaclona: UV v metrech (x napric, y po proudu od zacatku okapu), COLOR r pena, g padajici cast, a okraj
//  druh 1 pena u paty (UV jednotkova plocha), druh 2 mlha (karty, UV y nahoru)
render_mode blend_mix, depth_draw_never, cull_disabled, specular_schlick_ggx;

uniform sampler2D pena_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform int druh = 0;
uniform vec3 voda : source_color = vec3(0.30, 0.33, 0.27);
uniform vec3 pena : source_color = vec3(0.78, 0.80, 0.76);
uniform float rychlost = 1.8;          // m/s pruhy na padu
uniform float rychlost_okap = 0.45;    // m/s na okapu (pred lomem)
uniform vec2 meritko_pruhu = vec2(0.55, 0.1);   // opakovani textury na metr napric / po proudu (pruhy po proudu)
uniform float prolinani_hore_m = 0.5;  // okap se od zacatku plynule ztraci do tune
uniform float pruhlednost = 0.82;      // nejvyssi kryti ciste vody (pena kryje plne)
uniform float okap_kryti = 0.45;      // okap (pred lomem, COLOR.g 0) je tenka voda nad tuni - kryje min
uniform float alfa_max = 1.0;

varying vec4 barva;

void vertex() {
	barva = COLOR;
}

void fragment() {
	vec2 uv = UV;
	float n1;
	float n2;
	float a;
	vec3 alb;
	if (druh == 0) {
		float sp = mix(rychlost_okap, rychlost, barva.g);
		n1 = texture(pena_tex, vec2(uv.x * meritko_pruhu.x, (uv.y - TIME * sp) * meritko_pruhu.y)).r;
		n2 = texture(pena_tex, vec2(uv.x * meritko_pruhu.x * 1.73 + 0.37, (uv.y - TIME * sp * 1.31) * meritko_pruhu.y * 1.9 + 0.11)).r;
		float pruhy = clamp(n1 * 0.65 + n2 * 0.65 - 0.15, 0.0, 1.0);
		float pf = clamp(barva.r * 0.85 + (pruhy - 0.45) * 1.1 * (0.4 + barva.g), 0.0, 1.0);
		alb = mix(voda, pena, pf);
		a = mix(pruhlednost * (0.55 + 0.45 * pruhy), 1.0, pf);
		a *= barva.a * smoothstep(0.0, prolinani_hore_m, uv.y) * mix(okap_kryti, 1.0, barva.g);
	} else if (druh == 1) {
		// pena u paty: dva vzorky rozbihajici se od padu
		n1 = texture(pena_tex, vec2(uv.x * 0.9, uv.y * 0.9 - TIME * 0.25)).r;
		n2 = texture(pena_tex, vec2(uv.x * 1.6 + 0.5, uv.y * 1.4 - TIME * 0.4 + 0.3)).r;
		float pp = clamp(n1 * 0.7 + n2 * 0.7 - 0.25, 0.0, 1.0);
		alb = mix(voda, pena, 0.6 + 0.4 * pp);
		a = barva.a * (0.35 + 0.65 * pp);
	} else {
		// mlha: stoupa a ridne
		n1 = texture(pena_tex, vec2(uv.x * 0.6 + 0.2, uv.y * 0.5 - TIME * 0.12)).r;
		n2 = texture(pena_tex, vec2(uv.x * 1.1 + 0.7, uv.y * 0.8 - TIME * 0.2)).r;
		alb = pena;
		a = barva.a * clamp(n1 * 0.6 + n2 * 0.6, 0.0, 1.0);
	}
	ALBEDO = alb;
	ALPHA = clamp(a * alfa_max, 0.0, 1.0);
	SPECULAR = 0.0;
	ROUGHNESS = 1.0;
	METALLIC = 0.0;
}
