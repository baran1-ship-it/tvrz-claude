shader_type spatial;
// Mlha pri zemi nad toky (Misa 18. 11., voda jako v lese Hvozd; scripts/mlha_vody.gd): billboard otoceny jen kolem
// svisle osy, mekky ovalny obrys rozbity posouvanym sumem. Unshaded a bez zapisu hloubky (pruhledna vrstva); barva x
// globalni voda_svetlo (daylight.gd), aby v noci nesvitila. Kryti z INSTANCE_CUSTOM.r, faze sumu .g. U kamery
// (blizko) a u konce dosahu mizi - velky billboard pres celou obrazovku = prekresleni (tablet).
render_mode blend_mix, depth_draw_never, cull_disabled, unshaded, shadows_disabled;

uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
uniform vec3 barva : source_color = vec3(0.78, 0.8, 0.76);
uniform vec2 blizko = vec2(2.0, 6.0);
uniform float dosah = 60.0;
global uniform vec3 voda_svetlo;

varying float v_kryti;
varying float v_faze;
varying float v_vzd;

void vertex() {
	vec3 sc = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), 1.0);
	vec3 stred = MODEL_MATRIX[3].xyz;
	vec3 k = INV_VIEW_MATRIX[3].xyz;
	vec2 d = k.xz - stred.xz;
	vec3 vpred = normalize(vec3(d.x, 0.0, d.y) + vec3(0.0, 0.0, 1e-4));
	vec3 vprava = normalize(cross(vec3(0.0, 1.0, 0.0), vpred));
	vec3 w = stred + vprava * VERTEX.x * sc.x + vec3(0.0, 1.0, 0.0) * VERTEX.y * sc.y;
	v_vzd = length(d);
	v_kryti = INSTANCE_CUSTOM.r;
	v_faze = INSTANCE_CUSTOM.g;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(w, 1.0);
}

void fragment() {
	vec2 q = (UV - 0.5) * 2.0;
	float tvar = 1.0 - smoothstep(0.35, 1.0, length(q * vec2(1.0, 1.15)));
	tvar *= smoothstep(0.0, 0.25, 1.0 - UV.y);                       // spodek rozplyvavy do zeme
	float s = texture(sum, UV * vec2(0.6, 0.35) + vec2(TIME * 0.012 + v_faze, v_faze * 0.7)).r;
	float a = v_kryti * tvar * smoothstep(0.15, 0.75, s);
	a *= smoothstep(blizko.x, blizko.y, v_vzd) * (1.0 - smoothstep(dosah * 0.8, dosah, v_vzd));
	ALBEDO = barva * voda_svetlo;
	ALPHA = clamp(a, 0.0, 1.0);
}
