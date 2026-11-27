shader_type spatial;
// Puchart (Míša 23. 11.: „to vyskakování a růst keřů přede mnou je hrozný“): vzdálená podoba keře – impostor 8×8 pohledů
// (blender/impostory.py ker_<druh>, stejné mapování jako impostor.gdshader stromů) v MultiMeshi bylin (byliny.gd režim daleko).
// Poloha, měřítko a otočení z transformace instance (stejné polohy jako plné keře – stejný generátor buněk).
// Všechny druhy v jednom atlasu (nastroje/kere_atlas.py, 4 × 3 políčka) – INSTANCE_CUSTOM = (políčko, střed y, poloměr, –),
// jeden MultiMesh na buňku = 1 volání kreslení (hlídač scén 23. 11.: 11 druhů zvlášť přidalo 60–94 volání).
// Doplněk k plnému keři: listi.gdshader / bylina.gdshader kreslí keř, když vz >= h*0,8; tady naopak (vz < h*0,8) – každý keř
// je v každé vzdálenosti právě jednou, celý (žádné šachovnice ani růst). Na konci dosahu (konec) mizí po celých keřích.
render_mode world_vertex_coords, cull_disabled, diffuse_lambert_wrap, specular_disabled;

uniform sampler2D barva : source_color, filter_linear_mipmap;
uniform sampler2D normaly : filter_linear_mipmap;   // normála ve světě (ne tečná mapa)
uniform vec2 policek = vec2(4.0, 3.0);   // sloupců, řádků atlasu
uniform vec2 zanik = vec2(0.0);    // jako plný keř (byliny.gd _fade: (do, od)); regulator.gd ho násobí stejně
uniform vec2 konec = vec2(150.0, 130.0);   // (do, od): za „do“ nic, mezi od a do mizí po celých keřích
uniform vec4 tint = vec4(1.0);

const float N = 8.0;

varying vec2 bunka;
varying vec2 policko;
varying float otoc;
varying float odst;
uniform vec3 kamera_pred;   // Míša 27. 11.: časované prolnutí s plným keřem/bylinou (listi.gdshader, bylina.gdshader)
uniform float lod_cas = 0.0;
varying float v_kcas;   // podíl plného (0 = jen impostor); impostor kreslí pixely b >= v_kcas

// stejný hash jako listi.gdshader / bylina.gdshader (poloha zaokrouhlená na 1/8 m – plný keř a impostor jsou v různých
// buňkách, poloha se liší v posledních bitech; nezaokrouhlený sin-hash by dal jiné číslo)
float hash_ker(vec3 wp) {
	vec2 q = floor(wp.xz * 8.0 + 0.5) * 0.125;
	return fract(sin(dot(q, vec2(12.9898, 78.233))) * 43758.5453);
}

void vertex() {
	vec3 wp = MODEL_MATRIX[3].xyz;
	float sl = INSTANCE_CUSTOM.x;
	policko = vec2(mod(sl, policek.x), floor(sl / policek.x + 0.01)) / policek;
	vec3 stred = vec3(0.0, INSTANCE_CUSTOM.y, 0.0);
	float polomer = INSTANCE_CUSTOM.z;
	vec3 sx = MODEL_MATRIX[0].xyz;
	float s = length(sx);
	float sy = length(MODEL_MATRIX[1].xyz);
	otoc = atan(-sx.z, sx.x);   // Basis(UP, a): sloupec x = (cos a, 0, −sin a) × s
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	float d = length(wp - cam);
	float hz = hash_ker(wp);
	odst = fract(hz * 7.31);
	bool vid = true;
	v_kcas = 0.0;
	if (zanik.x != zanik.y) {
		float vz = clamp((d - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
		vid = vz < hz * 0.8;   // přesný doplněk k plnému keři
		if (lod_cas > 0.5) {
			float vp = clamp((length(wp - kamera_pred) - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
			bool plny = !vid;
			if (plny != (vp >= hz * 0.8) && abs(vz - vp) > 1e-5) {
				float e = clamp((vz - hz * 0.8) / (vz - vp), 0.0, 1.0);
				v_kcas = plny ? e : 1.0 - e; vid = true;
			}
		}
	}
	float vk = clamp((d - konec.x) / (konec.y - konec.x), 0.0, 1.0);
	if (vk < fract(hz * 13.7 + 0.29)) vid = false;
	vec3 c = wp + vec3(stred.x * s, stred.y * sy, stred.z * s);
	vec3 f = normalize(cam - c);
	float co = cos(otoc);
	float si = sin(otoc);
	vec3 fl = vec3(co * f.x - si * f.z, max(f.y, 0.0), si * f.x + co * f.z);
	fl = normalize(fl + vec3(0.0, 0.0001, 0.0));
	vec2 p = fl.xz / (abs(fl.x) + abs(fl.y) + abs(fl.z));
	vec2 uv = vec2(p.x + p.y, p.x - p.y) * 0.5 + 0.5;
	bunka = clamp(floor(uv * N), 0.0, N - 1.0) / N;
	vec3 fv = normalize(vec3(f.x, min(f.y, 0.95), f.z));
	vec3 r = normalize(cross(vec3(0.0, 1.0, 0.0), fv));
	vec3 u = cross(fv, r);
	vec2 k = (UV - 0.5) * 2.0 * polomer * vec2(s, sy);
	VERTEX = vid ? c + r * k.x - u * k.y : vec3(0.0);
}

void fragment() {
	vec2 uv = policko + (bunka + clamp(UV, vec2(0.01), vec2(0.99)) / N) / policek;
	vec4 a = texture(barva, uv);
	if (a.a < 0.5) discard;
	if (v_kcas > 0.0) {   // přechod s plným keřem: doplňkový dithering (každý pixel jen jedna podoba)
		ivec2 q = ivec2(mod(FRAGCOORD.xy, 4.0)); int i = q.x + q.y * 4;
		int bm[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
		if ((float(bm[i]) + 0.5) / 16.0 < v_kcas) discard;
	}
	float li = smoothstep(0.0, 0.08, a.g - max(a.r, a.b) * 0.8);
	vec3 var = vec3(0.9 + 0.2 * odst, 0.92 + 0.16 * fract(odst * 7.31), 0.9 + 0.18 * fract(odst * 3.17));
	ALBEDO = a.rgb * mix(vec3(1.0), tint.rgb * var, li) * mix(0.7, 0.95, 1.0 - UV.y);
	vec3 n = texture(normaly, uv).rgb * 2.0 - 1.0;
	float co = cos(otoc);
	float si = sin(otoc);
	n = vec3(co * n.x + si * n.z, n.y, -si * n.x + co * n.z);
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ROUGHNESS = 0.9;
}
