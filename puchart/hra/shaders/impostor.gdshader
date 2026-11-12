shader_type spatial;
// Impostor stromu (K3): jeden ctverec otoceny ke kamere, pohled z atlasu 8x8 (hemi-oktaedricky, blender/impostory.py)
// podle smeru od stromu ke kamere. Transformace instanci jsou jednotkove (renderer Compatibility je predava jinak
// nez Mobile) - poloha, meritko a otoceni jsou v INSTANCE_CUSTOM: xyz = pata stromu vuci stredu bunky (uzel MultiMeshe;
// custom data jsou v polovicni presnosti, svetove souradnice nad 1024 m by skakaly po 1 m), w = round(meritko*256) + otoceni/2pi.
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;

uniform sampler2D barva : source_color, filter_linear_mipmap;
uniform sampler2D normaly : filter_linear_mipmap;   // normala ve svete (ne tecna mapa)
uniform vec3 stred = vec3(0.0, 8.0, 0.0);     // stred koule stromu nad patou (m, meritko 1)
uniform float polomer = 8.0;
uniform float fade_od = 50.0;                 // nabeh (plny strom konci na 60 m)
uniform float fade_do = 900.0;
uniform vec2 lod_daleko = vec2(0.0);   // jako les.gd LOD1 (mez, prolnutí): doplňkový dithering po pixelech, ne náhodný skok celého stromu
uniform vec3 kamera_hrace;   // poloha kamery hráče – nastavuje les.gd každý snímek (12. 11.: ne global uniform – pád na tabletu při startu)
uniform vec4 tint = vec4(1.0);      // odstin listi druhu (svet.TINT_LISTI) - jako plny strom

const float N = 8.0;

varying vec2 bunka;
varying float viditelnost;
varying float prah;
varying float otoc;

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0)); int i = q.x + q.y * 4;
	int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[i]) + 0.5) / 16.0;
}

void vertex() {
	vec4 ic = INSTANCE_CUSTOM;
	float s = floor(ic.w) / 256.0;
	otoc = fract(ic.w) * 6.2831853;
	vec3 o = MODEL_MATRIX[3].xyz;
	vec3 c = ic.xyz + o + stred * s;
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	vec3 f = normalize(cam - c);
	// smer ke kamere v soustave stromu (bez jeho otoceni kolem svisle osy)
	float co = cos(otoc);
	float si = sin(otoc);
	vec3 fl = vec3(co * f.x - si * f.z, max(f.y, 0.0), si * f.x + co * f.z);
	fl = normalize(fl + vec3(0.0, 0.0001, 0.0));
	vec2 p = fl.xz / (abs(fl.x) + abs(fl.y) + abs(fl.z));
	vec2 uv = vec2(p.x + p.y, p.x - p.y) * 0.5 + 0.5;
	bunka = clamp(floor(uv * N), 0.0, N - 1.0) / N;
	// ctverec kolmo ke kamere, nahoru = svisla osa (stejne jako kamera pri pecení)
	vec3 fv = normalize(vec3(f.x, min(f.y, 0.95), f.z));
	vec3 r = normalize(cross(vec3(0.0, 1.0, 0.0), fv));
	vec3 u = cross(fv, r);
	vec2 k = (UV - 0.5) * 2.0 * polomer * s;
	VERTEX = c - o + r * k.x - u * k.y;
	float dist = distance(c, cam);
	prah = fract(sin(dot(ic.xz + o.xz, vec2(12.9898, 78.233))) * 43758.5453);   // jen odstín stromu
	if (lod_daleko.y > 0.0) {
		float di = length(ic.xyz + o - kamera_hrace);
		viditelnost = clamp((di - (lod_daleko.x - lod_daleko.y * 0.5)) / lod_daleko.y, 0.0, 1.0) * (1.0 - smoothstep(fade_do - 60.0, fade_do, dist));
		if (viditelnost <= 0.0) VERTEX = vec3(0.0);
	} else {
		viditelnost = smoothstep(fade_od, fade_od + 10.0, dist) * (1.0 - smoothstep(fade_do - 60.0, fade_do, dist));
	}
}

void fragment() {
	if (viditelnost < 1.0 && 1.0 - viditelnost > bayer4(FRAGCOORD.xy)) discard;   // doplněk k LOD1 (b < 1 − v_far)
	vec2 uv = bunka + clamp(UV, vec2(0.01), vec2(0.99)) / N;
	vec4 a = texture(barva, uv);
	if (a.a < 0.5) {
		discard;
	}
	// vlastni stin koruny (plny strom ho ma z geometrie, obrazek ne): dole a uvnitr tmavsi
	// odstin jen pro listi (kmen v dalce je par pixelu): zelenejsi nez sede = listi
	float li = smoothstep(0.0, 0.08, a.g - max(a.r, a.b) * 0.8);
	// každý strom jiný odstín (jas ±12 %, posun do žluta/modra) – vzdálené koruny nejsou jednolitá zelená masa
	vec3 var = vec3(0.88 + 0.24 * prah, 0.9 + 0.2 * fract(prah * 7.31), 0.86 + 0.22 * fract(prah * 3.17));
	ALBEDO = a.rgb * mix(vec3(1.0), tint.rgb * var, li) * mix(0.55, 0.85, 1.0 - UV.y);
	// normala ve svete stromu -> otocit o otoceni stromu -> do pohledu kamery
	vec3 n = texture(normaly, uv).rgb * 2.0 - 1.0;
	float co = cos(otoc);
	float si = sin(otoc);
	n = vec3(co * n.x + si * n.z, n.y, -si * n.x + co * n.z);
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ROUGHNESS = 0.9;
}
