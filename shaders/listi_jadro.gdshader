shader_type spatial;
// Listi stromu (0.61, Misa: "placacky misto listu a ani pohyb"): misto StandardMaterial3D z modelu.
// 1) vitr: koruna se kyva (vic nahore), listy se chveji (kazdy jinak podle polohy); stejny smer jako trava
// 2) normaly od stredu koruny (radce Jednotny vzhled: "normaly od stredu koruny") - koruna se nasviti jako objem,
//    ne jako jednotlive ploche karty; zadni strana karet prosvita (translucence)
// JÁDRO KORUNY (10. 11., podle Puchartu 12ad855): listy uvnitř elipsoidu koruny (svet._jadro_koruny) bez alfy a discard
// -> early-Z, vrstvy listí za obrysem se nestínují znovu. Obrys koruny zůstává listi.gdshader.
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;

uniform sampler2D barva : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float prah = 0.5;
uniform vec3 stred = vec3(0.0, 6.0, 0.0);     // stred koruny v souradnicich modelu
uniform float vyska = 10.0;                   // vyska modelu (m)
uniform float sila_vetru = 1.0;
uniform float objem = 0.65;                    // 0 = normaly karet, 1 = koule kolem stredu
uniform vec2 vitr_smer = vec2(0.8, 0.6);
uniform float stin_min = 0.5;               // les_podrost.json koruny.listi_stin_min (prosvitani listu ve stinu)
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
	// Misa 17. 11. r. 3 (tmave obdelniky v korune brizy, rozbor 23. 11. v izolovane scene build/dbg/briza_stin.gd):
	// cull_disabled -> Godot rubu karty normalu otoci; nase normala je ale smer od stredu koruny (objem), po otoceni
	// miri dovnitr a cela karta zcerna. Rub tedy vraci normalu zpet (koruna se svitit jako objem z obou stran karty).
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
	vec4 t = texture(barva, UV);
	// Misa 17. 11. r. 3 (listi zespodu cerne obdelniky): karta jadra je bez alfy, pruhledna mista textury maji RGB 0
	// -> zespodu / zevnitr koruny cerny ctverec. Pruhledna mista = prumerna barva listu (nejmensi mip, deleno alfou =
	// bez cerneho pozadi), tj. husty vnitrek koruny misto cerne.
	// Misa 18. 11. (strom ve vsi zluty, 03-05): deleni alfou nejmensiho mipu (na tabletu alfa skoro 0) prepalilo barvu do
	// zluta -> jen odstin prumeru listu (normovany na nejsilnejsi kanal) v pevnem tmavem jasu vnitrku koruny
	vec4 pr = textureLod(barva, UV, 12.0);
	float pm = max(pr.r, max(pr.g, pr.b));
	vec3 prum = pm > 0.01 ? pr.rgb / pm * 0.3 : vec3(0.1, 0.16, 0.06);   // mip bez barvy (cerne pozadi) -> tmave zelena
	vec3 c = mix(prum, t.rgb, smoothstep(0.0, prah, t.a));
	ALBEDO = c * tint.rgb * v_tint * mix(0.5, 1.0, v_ao);
	// zadni strana: svetlo prosvita (karty proti slunci nejsou cerne)
	BACKLIGHT = c * 0.5;
	ROUGHNESS = 0.85;
}

// Misa 17. 11. r. 3 (tmave obdelniky v korune brizy; izolovane 23. 11.: bez stinu zadne, se stinem stinoveho telesa
// koruny i vlastniho listi cele karty cerne): list ve stinu neni cerny - prosvita (listi_stin_min). Jinak stejne jako
// diffuse_lambert_wrap + BACKLIGHT.
void light() {
	float nl = dot(NORMAL, LIGHT);
	float wrap = max((nl + 0.5) / 1.5, 0.0);
	float att = mix(stin_min, 1.0, ATTENUATION);
	DIFFUSE_LIGHT += wrap * att * LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += BACKLIGHT * max(-nl, 0.0) * att * LIGHT_COLOR / PI;
}
