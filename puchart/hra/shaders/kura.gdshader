shader_type spatial;
// Kůra stromů (les.gd): jako StandardMaterial z modelu (albedo, normála) + LOD po stromech a rozpouštění do dálky jako
// listi.gdshader (Míša 10. 11.: blikání stromů – přepínání po buňkách).
uniform sampler2D barva : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normala : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool ma_normalu = false;
uniform vec4 tint : source_color = vec4(1.0);
uniform vec2 zanik = vec2(0.0);
uniform vec3 lod_mez = vec3(0.0);
uniform vec2 lod_daleko = vec2(0.0);   // (mez, prolnutí) přechodu na impostor – doplňkový dithering s impostor.gdshader
uniform vec3 kamera_hrace;   // poloha kamery hráče – nastavuje les.gd každý snímek (12. 11.: ne global uniform – pád na tabletu při startu)
uniform vec3 kamera_pred;   // poloha kamery hráče před lod_cas_s (les.gd) – časované prolnutí LOD (stromy_modely.json lod_casove)
uniform float lod_cas = 0.0;   // 1 = časované prolnutí (při překročení meze krátce oba stupně), 0 = pásmo podle vzdálenosti
// Časované prolnutí bez stavu: vzdálenost k stromu teď a před lod_cas_s (kamera_pred); překročila-li mez v tom okně,
// podíl uplynulé doby od překročení = (d_ted − mez) / (d_ted − d_pred) (lineárně mezi polohami kamery). Stojí-li hráč,
// strom je celý v jednom stupni (žádné trvalé dvojí kreslení v pásmu); jinak 0→1 během lod_cas_s (video Míši 16. 11., Havran K13).
float lod_casove(float d_ted, float d_pred, float mez) {
	bool dal = d_ted >= mez;
	if (dal != (d_pred >= mez) && abs(d_ted - d_pred) > 0.0001) {
		float e = clamp((d_ted - mez) / (d_ted - d_pred), 0.0, 1.0);
		return dal ? e : 1.0 - e;
	}
	return dal ? 1.0 : 0.0;
}
varying float v_lod;
varying float v_far;
float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0)); int i = q.x + q.y * 4;
	int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[i]) + 0.5) / 16.0;
}
void vertex() {
	v_lod = 1.0; v_far = 1.0;
	if (lod_mez.z > 0.5) {
		float di = length((MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz - kamera_hrace);
		if (lod_cas > 0.5) {
			float dp = length((MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz - kamera_pred);
			v_lod = lod_casove(di, dp, lod_mez.x);
			if (lod_daleko.y > 0.0) v_far = 1.0 - lod_casove(di, dp, lod_daleko.x);
		} else {
			v_lod = clamp((di - (lod_mez.x - lod_mez.y * 0.5)) / max(lod_mez.y, 0.01), 0.0, 1.0);   // 0 blízko, 1 daleko
			if (lod_daleko.y > 0.0) v_far = 1.0 - clamp((di - (lod_daleko.x - lod_daleko.y * 0.5)) / lod_daleko.y, 0.0, 1.0);
		}
		bool pryc = lod_mez.z < 1.5 ? v_lod >= 1.0 : (v_lod <= 0.0 || v_far <= 0.0);
		if (pryc) { VERTEX = vec3(0.0); }
	}
}
void fragment() {
	if (lod_mez.z > 0.5) {   // doplňkový dithering: LOD0 kreslí pixely b >= f, LOD1 b < f (každý pixel právě jeden), dál LOD1 b < v_far, impostor b >= v_far
		float b = bayer4(FRAGCOORD.xy);
		if (lod_mez.z < 1.5) { if (b < v_lod) discard; }
		else { if (b >= v_lod || b >= v_far) discard; }
	}
	if (zanik.x != zanik.y) {
		float f = clamp((length(VERTEX) - zanik.x) / (zanik.y - zanik.x), 0.0, 1.0);
		if (f < bayer4(FRAGCOORD.xy)) discard;
	}
	ALBEDO = texture(barva, UV).rgb * tint.rgb;
	if (ma_normalu) NORMAL_MAP = texture(normala, UV).rgb;
	ROUGHNESS = 0.9;
}
