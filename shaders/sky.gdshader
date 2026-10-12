shader_type sky;
// Obloha: prechod zenit-obzor, zare kolem slunce, mraky z textury sumu, v noci hvezdy.

uniform vec3 zenith : source_color = vec3(0.15, 0.33, 0.64);
uniform vec3 horizon : source_color = vec3(0.7, 0.76, 0.8);
uniform vec3 ground : source_color = vec3(0.22, 0.21, 0.19);
uniform vec3 sun_tint : source_color = vec3(1.0, 0.86, 0.66);
uniform float sun_glow = 0.4;
uniform vec3 cloud_lit : source_color = vec3(1.0, 0.97, 0.92);
uniform vec3 cloud_dark : source_color = vec3(0.52, 0.58, 0.68);
uniform float cloud_cover = 0.46;
uniform float stars = 0.0;
uniform float energy = 1.0;
uniform vec2 cloud_offset = vec2(0.0);
uniform sampler2D cloud_tex : repeat_enable, filter_linear_mipmap;

float hash3(vec3 p) {
	p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3));
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

void sky() {
	vec3 d = normalize(EYEDIR);
	float up = clamp(d.y, 0.0, 1.0);
	vec3 col = mix(horizon, zenith, pow(up, 0.55));
	float sd = 0.0;
	if (LIGHT0_ENABLED) {
		sd = max(dot(d, LIGHT0_DIRECTION), 0.0);
		col += sun_tint * (pow(sd, 5.0) * 0.22 + pow(sd, 40.0) * 0.5) * sun_glow;
	}
	if (stars > 0.001 && d.y > 0.0) {
		vec3 q = floor(d * 190.0);
		float h = hash3(q);
		float tw = smoothstep(0.9965, 1.0, h);
		col += vec3(0.9, 0.95, 1.0) * tw * stars * (0.4 + 0.6 * hash3(q + 7.0)) * smoothstep(0.02, 0.3, d.y);
	}
	float occl = 0.0;
	if (d.y > 0.0) {
		vec2 uv = d.xz / (d.y + 0.14) * 0.12 + cloud_offset;
		float n = texture(cloud_tex, uv).r * 0.66 + texture(cloud_tex, uv * 2.6 + vec2(0.31, 0.17)).r * 0.34;
		float c = smoothstep(1.0 - cloud_cover, 1.0 - cloud_cover + 0.26, n);
		float fade = smoothstep(0.0, 0.2, d.y);
		float dense = smoothstep(0.6, 0.98, n);
		vec3 cc = mix(cloud_lit, cloud_dark, dense * 0.75);
		cc += sun_tint * pow(sd, 10.0) * 0.3 * sun_glow;
		occl = c * fade;
		col = mix(col, cc, occl * 0.94);
	} else {
		col = mix(horizon, ground, smoothstep(0.0, -0.3, d.y));
	}
	if (LIGHT0_ENABLED && d.y > -0.02) {
		float cs = dot(d, LIGHT0_DIRECTION);
		float disk = smoothstep(cos(LIGHT0_SIZE * 1.3), cos(LIGHT0_SIZE * 0.8), cs);
		col += LIGHT0_COLOR * min(LIGHT0_ENERGY, 4.0) * disk * 3.0 * (1.0 - occl * 0.9);
	}
	COLOR = col * energy;
}
