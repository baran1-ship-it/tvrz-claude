// Karty stébel sena (jesle, stodoly, půdy – pravidla/svet/funkce.json jesle; Míša 15. 11.: „seno ale fotorealistické“).
// Jako stebla.gdshader (tráva): alfa nůžky + alfa do pokrytí, bez průhledného míchání, obě strany. Normála karty = normála
// povrchu kupy (funkce.gd jesle_site) i na rubu – rub karty jinak dostane normálu dovnitř kupy a je černý (snímek 15. 11.).
// Barva vrcholu = ztmavení do hloubky (pata karty tmavší, konec světlý – předloha docs/reference/seno/kcd1_seno_staj_misa_15_11.jpg).
shader_type spatial;
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled, alpha_to_coverage_and_one;

uniform sampler2D stebla : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float prah = 0.4;
uniform float prosvit = 0.3;   // tenké suché stéblo proti světlu prosvítá (BACKLIGHT)

void fragment() {
	vec4 c = texture(stebla, UV);
	ALBEDO = c.rgb * COLOR.rgb;
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = prah;
	if (!FRONT_FACING) NORMAL = -NORMAL;
	ROUGHNESS = 1.0;
	BACKLIGHT = vec3(prosvit) * ALBEDO;
}
