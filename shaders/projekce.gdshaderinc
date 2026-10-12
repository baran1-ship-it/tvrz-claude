// Svetove promitani jako v Blenderu (lib.wcoord): na svislych plochach vodorovne podel zdi a vyska,
// na vodorovnych (x, z). Vraci UV v metrech a tecny vektor/bitangentu pro normalovou mapu.
void projekce(vec3 wp, vec3 n, out vec2 uv, out vec3 t, out vec3 b) {
	if (abs(n.y) > 0.7) {
		t = vec3(1.0, 0.0, 0.0);
		b = vec3(0.0, 0.0, 1.0);
		uv = wp.xz;
	} else {
		t = normalize(cross(vec3(0.0, 1.0, 0.0), n));
		b = vec3(0.0, 1.0, 0.0);
		uv = vec2(dot(wp, t), wp.y);
	}
	float d = dot(wp, n);
	uv += vec2(d * 0.37, d * 0.61);
}

vec3 normala_svet(vec3 nm_ts, vec3 t, vec3 b, vec3 n) {
	return normalize(t * nm_ts.x + b * nm_ts.y + n * nm_ts.z);
}
