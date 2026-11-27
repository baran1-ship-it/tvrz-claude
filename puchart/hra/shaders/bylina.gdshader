// Puchart (Míša 19. 11., plán E1 krok 1, „mizející rostliny jako šachovnice“): byliny bez ditheru – náhrada StandardMaterialu
// (byliny.gd _zanik_inst: textura, barva, nůžky alfy, normálová mapa, drsnost z původního materiálu). Ke konci dosahu
// zanik (min > max = mizí s dálkou, jako distance_fade) mizí celé rostliny: práh z hashe pozice instance, srazí se k patě.
shader_type spatial;
render_mode cull_disabled, specular_disabled;
uniform sampler2D barva : source_color, filter_linear_mipmap, repeat_enable;
uniform bool ma_barvu = false;
uniform vec4 tint : source_color = vec4(1.0);
uniform bool barva_vrcholu = false;
uniform float prah = 0.0;
uniform sampler2D normaly : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool ma_normaly = false;
uniform float drsnost = 1.0;
uniform vec3 uv_meritko = vec3(1.0);
uniform vec3 uv_posun = vec3(0.0);
uniform vec2 zanik = vec2(0.0);
// Míša 27. 11. („ne, doskakovala tráva“; video 16. 11. – časované prolnutí 0,25 s jako stromy): rostlina, která právě překročila
// svůj práh (mezi polohou kamery teď a před lod_cas_s – byliny.gd z les.gd), se prolne ditheringem místo naskočení/zmizení
uniform vec3 kamera_pred;
uniform float lod_cas = 0.0;
varying float v_cas;
float bayer4b(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0)); int i = q.x + q.y * 4;
	int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[i]) + 0.5) / 16.0;
}

void vertex() {
	v_cas = 1.0;
	UV = UV * uv_meritko.xy + uv_posun.xy;
	if (zanik.x != zanik.y) {
		vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
		float vz = clamp((length(wp - INV_VIEW_MATRIX[3].xyz) - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
		float hz = fract(sin(dot(floor(wp.xz * 8.0 + 0.5) * 0.125, vec2(12.9898, 78.233))) * 43758.5453);   // poloha na 1/8 m – stejný hash jako ker_impostor.gdshader (Míša 23. 11.)
		v_cas = 1.0;
		bool ted = vz >= hz * 0.8;
		if (lod_cas > 0.5) {
			float vp = clamp((length(wp - kamera_pred) - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
			if (ted != (vp >= hz * 0.8) && abs(vz - vp) > 1e-5) {
				float e = clamp((vz - hz * 0.8) / (vz - vp), 0.0, 1.0);
				v_cas = ted ? e : 1.0 - e; ted = true;   // mizející ještě kreslit a rozpouštět
			}
		}
		VERTEX *= ted ? 1.0 : 0.0;   // Míša 20. 11.: „před očima mi lezou stromy a keře ze země“ – žádné zvětšování od paty, rostlina se objeví celá v náhodné vzdálenosti pásma
	}
}

void fragment() {
	if (v_cas < 1.0 && v_cas <= bayer4b(FRAGCOORD.xy)) discard;   // časované prolnutí (viz kamera_pred)
	vec4 t = ma_barvu ? texture(barva, UV) : vec4(1.0);
	t *= tint;
	if (barva_vrcholu) t *= COLOR;
	ALBEDO = t.rgb;
	if (prah > 0.0) { ALPHA = t.a; ALPHA_SCISSOR_THRESHOLD = prah; }
	if (ma_normaly) NORMAL_MAP = texture(normaly, UV).rgb;
	ROUGHNESS = drsnost;
}
