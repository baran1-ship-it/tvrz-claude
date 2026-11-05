shader_type spatial;
// Latka praporu a vlajek ve vetru (Misa 5. 11.: "vsechny vlajky a prapory na vezich nebo zdech jsou staticke, mely by se
// hybat podle vetru"). Postup jako bezny "flag shader" (GDQuest Flag shader 3D, godotshaders.com Waving flag): posun
// vrcholu ve vertex shaderu umerny vzdalenosti od zerdi, bez fyziky a bez skriptu za snimek.
// Vsechna cisla z dat: pravidla/svet/modely.json "latka" (druh podle predpony modelu), vitr prostredi.json.
//  - vzdalenost od zerdi d (0 u zerdi, 1 na volnem konci) z UV: d = dot(UV, zerd_uv.xy) + zerd_uv.z (blender/vlastni.py
//    _grid_cloth: UV podel latky, overeno na korouhev_havran.glb - UV.x roste od zerdi, UV.y shora dolu)
//  - posun podel osy (normala latky v souradnicich modelu): vlna po delce + jemne trepotani, faze podle polohy predmetu
//  - normala se natoci podle sklonu vlny (svetlo se po latce meni)
render_mode cull_disabled, diffuse_lambert_wrap;

uniform sampler2D barva : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float drsnost = 0.85;
uniform float prosvit = 0.25;          // latka proti slunci prosvita (BACKLIGHT)
uniform vec3 zerd_uv = vec3(1.0, 0.0, 0.0);
uniform vec3 osa = vec3(0.0, 0.0, 1.0);    // smer posunu (normala latky), model
uniform vec3 smer = vec3(1.0, 0.0, 0.0);   // smer od zerdi k volnemu konci, model
uniform float delka_m = 1.0;               // delka latky od zerdi k volnemu konci
uniform float amplituda_m = 0.1;           // vychyleni volneho konce pri sile vetru 1
uniform float vlny = 1.0;                  // pocet vln na delce latky
uniform float rychlost = 2.0;              // rad/s pri sile vetru 1
uniform float trepot = 0.2;                // podil jemneho trepotani (0..1)
uniform float odklon = 0.0;                // vyduti po vetru (podil amplitudy), podle uhlu vetru k latce
uniform float jen_ven = 0.0;               // 1 = jen na +osa (prapor na zdi nesmi do zdi)
uniform vec2 vitr_smer = vec2(0.8, 0.6);
uniform float sila_vetru = 1.0;

void vertex() {
	vec3 wp = MODEL_MATRIX[3].xyz;
	float faze = wp.x * 0.37 + wp.z * 0.53 + wp.y * 0.21;
	float d = clamp(dot(UV, zerd_uv.xy) + zerd_uv.z, 0.0, 1.0);
	float c = dot(UV, abs(zerd_uv.yx));        // souradnice napric latkou
	float k = vlny * 6.2832;
	float t = TIME * rychlost * sila_vetru;
	float p1 = k * d - t + faze;
	float p2 = k * 2.7 * d - t * 2.3 + c * 4.0 + faze * 1.7;
	float w = sin(p1) * (1.0 - trepot) + sin(p2) * trepot;
	float dw = cos(p1) * k * (1.0 - trepot) + cos(p2) * k * 2.7 * trepot;
	w = mix(w, 0.5 + 0.5 * w, jen_ven);
	dw = mix(dw, 0.5 * dw, jen_ven);
	vec3 osa_w = mat3(MODEL_MATRIX) * osa;
	float s = dot(osa_w.xz, normalize(vitr_smer)) / max(length(osa_w), 0.0001);
	float a = amplituda_m * sila_vetru;
	float f = a * (d * w + odklon * s * d * d);
	float df = a * (w + d * dw + 2.0 * odklon * s * d) / max(delka_m, 0.05);
	VERTEX += osa * f;
	VERTEX -= smer * (0.5 * f * f / max(delka_m, 0.05));      // latka se vlnou zkrati (zachova plochu)
	NORMAL = normalize(NORMAL - dot(NORMAL, osa) * df * smer);
}

void fragment() {
	vec4 tx = texture(barva, UV);
	ALBEDO = tx.rgb * tint.rgb;
	ROUGHNESS = drsnost;
	BACKLIGHT = tx.rgb * prosvit;
}
