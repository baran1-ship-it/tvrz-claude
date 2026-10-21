shader_type spatial;
// Zakladni postava Quaternius (superhrdina) - z ni jen hlava a krk; telo pod krkem kresli odev (Peasant) se svymi
// rukama. Vyska v prostoru modelu (po skinningu): pod rez nic.
render_mode cull_back;

uniform sampler2D barva : source_color, filter_linear_mipmap;
uniform float rez = 1.45;
varying float v_y;

void vertex() {
	v_y = VERTEX.y;
}

void fragment() {
	if (v_y < rez) {
		discard;
	}
	ALBEDO = texture(barva, UV).rgb;
	ROUGHNESS = 0.7;
}
