// Výplň okna (Míša 9. 11.: „okna nedodělaná“, „v místnostech tma“): terčíkové sklo v olovu (panské místnosti) nebo napnutá
// blána / plátno (ostatní). Neprůhledné (žádné třídění průhlednosti na tabletu), svítí jako proti dennímu světlu – dovnitř
// prosvětlí niku; zvenku tlumené. Vzor z polohy ve světě (box z Blenderu nemá UV v rovině okna).
shader_type spatial;
render_mode cull_back;
uniform bool sklo = false;
uniform bool ven = false;   // vnější plocha: tmavá, stíněná (KCD fotky: okna zvenku tmavá)
varying vec3 wp;
varying vec3 wn;
float h21(vec2 p) { p = mod(p, 1024.0); vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz); }
void fragment() {
	vec3 n = normalize(wn);
	vec2 uv = vec2(abs(n.x) > abs(n.z) ? wp.z : wp.x, wp.y);
	vec3 col;
	if (sklo) {   // terčíky ~11 cm v olověné síti, nazelenalé, střed terčíku tmavší (pupek)
		vec2 g = uv / 0.085; vec2 f = fract(g) - 0.5; float d = length(f);
		float olovo = smoothstep(0.43, 0.48, d);
		float pupek = 1.0 - smoothstep(0.05, 0.14, d);
		col = mix(vec3(0.5, 0.58, 0.46), vec3(0.34, 0.42, 0.33), pupek) * (0.9 + 0.2 * h21(floor(g)));
		col = mix(col, vec3(0.08, 0.08, 0.07), olovo);
	} else {      // blána: teplá, vláknitá, nerovnoměrně prosvítá
		float v = h21(floor(uv * vec2(40.0, 6.0))) * 0.5 + h21(floor(uv * 9.0)) * 0.5;
		col = vec3(0.86, 0.72, 0.48) * (0.8 + 0.25 * v);
	}
	if (ven) { ALBEDO = col * (sklo ? 0.18 : 0.3); ROUGHNESS = sklo ? 0.15 : 0.8; SPECULAR = sklo ? 0.6 : 0.2; }
	else { ALBEDO = col * 0.2; EMISSION = col * 0.85; ROUGHNESS = 0.9; }   // dovnitř: denní světlo prosvítá
}
