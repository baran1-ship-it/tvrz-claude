// Zdivo hradů bez rastru (Míša 5. 11.: „ať zdi nemají ten rastr čtverečků“): stejná fotka zdiva se opakovala po 2,5 m
// a opakování bylo vidět jako mřížka. Dvě vzorkování (posunuté a pootočené, jiné měřítko) se míchají podle šumu v prostoru
// světa, k tomu velká barevná variace (zvětrání, vlhkost u paty) a tmavší břidlicový tón (fotky zdiva GC80T08).
// Vzorkovačů 3 (albedo, normála, drsnost) – limit Adreno 13.
shader_type spatial;
render_mode cull_disabled;   // jako importovaný materiál z glTF (oboustranný) – s cull_back byly vidět rubové plochy kusů

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D rough_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec3 ton = vec3(0.78, 0.76, 0.74);      // tmavší, šedohnědá břidlice
uniform float meritko_b = 0.73;                 // druhé vzorkování: jiné měřítko
uniform float sum_m = 3.2;                      // velikost skvrn míchání v metrech
uniform float variace = 0.18;                   // velká barevná variace

varying vec3 wpos;
varying vec3 wnor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnor = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 uv1 = UV;
	float a = 0.61;
	mat2 r = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a)));
	vec2 uv2 = r * (UV * meritko_b) + vec2(0.37, 0.71);
	vec2 q = (abs(wnor.y) > 0.7) ? wpos.xz : vec2(wpos.x + wpos.z, wpos.y);
	float n = noise(q / sum_m) * 0.65 + noise(q / (sum_m * 0.37) + 13.1) * 0.35;
	float m = smoothstep(0.38, 0.62, n);
	vec3 c1 = texture(albedo_tex, uv1).rgb; vec3 c2 = texture(albedo_tex, uv2).rgb;
	vec3 n1 = texture(normal_tex, uv1).rgb; vec3 n2 = texture(normal_tex, uv2).rgb;
	float r1 = texture(rough_tex, uv1).r; float r2 = texture(rough_tex, uv2).r;
	float big = noise(q / 9.0 + 4.7);
	vec3 col = mix(c1, c2, m) * ton * (1.0 - variace * 0.5 + variace * big);
	// svislé stékance od deště a vlhké skvrny (Havran zdivo/textura.gdshader: stekance, skvrny) – jen na svislých líci
	float hh = wpos.x * 0.93 + wpos.z * 1.07;
	float st = noise(vec2(hh * 3.6, wpos.y * 0.14)); float st2 = noise(vec2(hh * 9.2 + 0.4, wpos.y * 0.24));
	col *= 1.0 - (smoothstep(0.55, 0.8, st) * 0.35 + smoothstep(0.6, 0.85, st2) * 0.2) * (1.0 - abs(wnor.y));
	float vl = noise(q / 5.5 + 1.9);
	col = mix(col, col * vec3(0.86, 0.9, 0.74), smoothstep(0.62, 0.8, vl) * 0.5);   // nazelenalý lišejník / vlhko
	col = mix(col, vec3(0.16, 0.19, 0.08), smoothstep(0.35, 0.8, wnor.y) * smoothstep(0.5, 0.75, noise(wpos.xz * 0.8)) * 0.6);   // mech na koruně a římsách
	ALBEDO = col;
	NORMAL_MAP = mix(n1, n2, m);
	ROUGHNESS = mix(r1, r2, m);
}
