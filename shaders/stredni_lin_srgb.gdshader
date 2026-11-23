shader_type spatial;
// Stredni stupen predmetu s barvou vrcholu ulozenou linearne (barvy_vrcholu.json hra_linearni_stredni, plan_18_11 B8):
// Compatibility bere COLOR jako sRGB -> prevod lin -> sRGB (stejny vzorec jako tools/barvy_vrcholu.py srgb).
// 23. 11.: ze souboru misto Shader.new() z retezce v predmety.gd (kontrola shaderu v beh.sh, predehrati jako ostatni).
uniform float drsnost = 0.9;

void fragment() {
	vec3 c = clamp(COLOR.rgb, 0.0, 1.0);
	ALBEDO = mix(1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, c * 12.92, vec3(lessThanEqual(c, vec3(0.0031308))));
	ROUGHNESS = drsnost;
}
