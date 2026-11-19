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

void vertex() {
	UV = UV * uv_meritko.xy + uv_posun.xy;
	if (zanik.x != zanik.y) {
		vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
		float vz = clamp((length(wp - INV_VIEW_MATRIX[3].xyz) - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
		float hz = fract(sin(dot(wp.xz, vec2(12.9898, 78.233))) * 43758.5453);
		VERTEX *= clamp((vz - hz * 0.8) / 0.2, 0.0, 1.0);
	}
}

void fragment() {
	vec4 t = ma_barvu ? texture(barva, UV) : vec4(1.0);
	t *= tint;
	if (barva_vrcholu) t *= COLOR;
	ALBEDO = t.rgb;
	if (prah > 0.0) { ALPHA = t.a; ALPHA_SCISSOR_THRESHOLD = prah; }
	if (ma_normaly) NORMAL_MAP = texture(normaly, UV).rgb;
	ROUGHNESS = drsnost;
}
