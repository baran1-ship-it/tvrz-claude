shader_type spatial;
// Listi stromu (0.61, Misa: "placacky misto listu a ani pohyb"): misto StandardMaterial3D z modelu.
// 1) vitr: koruna se kyva (vic nahore), listy se chveji (kazdy jinak podle polohy); stejny smer jako trava
// 2) normaly od stredu koruny (radce Jednotny vzhled: "normaly od stredu koruny") - koruna se nasviti jako objem,
//    ne jako jednotlive ploche karty; zadni strana karet prosvita (translucence)
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled, depth_prepass_alpha;

uniform sampler2D barva : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float prah = 0.5;
uniform vec3 stred = vec3(0.0, 6.0, 0.0);     // stred koruny v souradnicich modelu
uniform float vyska = 10.0;                   // vyska modelu (m)
uniform float sila_vetru = 1.0;
uniform float objem = 0.65;                    // 0 = normaly karet, 1 = koule kolem stredu
uniform vec2 vitr_smer = vec2(0.8, 0.6);
varying float v_ao;          // vnitrek koruny tmavsi (Misa 0.61 "placacky": koruna jako jedna plocha bez hloubky)
varying vec3 v_tint;         // kazdy trs listi trochu jinak (svetlejsi, zlutejsi, tmavsi)

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float h = clamp(VERTEX.y / max(vyska, 1.0), 0.0, 1.0);
	float faze = wp.x * 0.13 + wp.z * 0.11;
	// kyvani koruny (pomale, poryvy), roste s vyskou kvadraticky - kmen u zeme stoji
	float kyv = (sin(TIME * 0.9 + faze) * 0.6 + sin(TIME * 1.7 + faze * 1.3) * 0.3) * h * h * 0.18 * sila_vetru;
	// chveni listu (rychle, male, kazdy vrchol jinak)
	float ch = sin(TIME * 6.0 + dot(VERTEX, vec3(3.1, 2.3, 2.7)) + faze) * 0.025 * h * sila_vetru;
	vec2 sm = normalize(vitr_smer);
	VERTEX.x += sm.x * kyv + ch;
	VERTEX.z += sm.y * kyv + ch * 0.7;
	VERTEX.y += ch * 0.5;
	// normala: mix karty a smeru od stredu koruny
	float r_kor = max(vyska * 0.3, 0.8);
	v_ao = smoothstep(0.15 * r_kor, r_kor, length(VERTEX - stred));
	vec3 cel = floor(VERTEX * 1.3);
	float hh = fract(sin(dot(cel, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	v_tint = mix(vec3(0.86, 0.9, 0.82), vec3(1.1, 1.08, 0.92), hh);
	vec3 od = normalize(VERTEX - stred + vec3(0.0001));
	od.y = max(od.y, -0.15);                  // spodek koruny ne normalou dolu (Misa 0.61: smrk zespodu cerny)
	NORMAL = normalize(mix(NORMAL, normalize(od), objem));
}

void fragment() {
	vec4 t = texture(barva, UV);
	ALBEDO = t.rgb * tint.rgb * v_tint * mix(0.5, 1.0, v_ao);
	ALPHA = t.a;
	ALPHA_SCISSOR_THRESHOLD = prah;
	// zadni strana: svetlo prosvita (karty proti slunci nejsou cerne)
	BACKLIGHT = t.rgb * 0.5;
	ROUGHNESS = 0.85;
}
