shader_type spatial;
// Malovana omitka se sablonovym vzorem (ctyrlisty v mrizce), misty oprysklá.
uniform vec3 zaklad = vec3(0.62, 0.6, 0.55);
uniform vec3 barva = vec3(0.28, 0.36, 0.42);
uniform sampler2D sum : filter_linear_mipmap, repeat_enable;
varying vec3 wp;
varying vec3 wn;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(wn);
	vec3 t = normalize(cross(vec3(0.0, 1.0, 0.0), n));
	vec2 uv = vec2(dot(wp, t), wp.y);
	vec2 f = fract(uv / 0.32) - 0.5;
	float r = length(f);
	float ang = atan(f.y, f.x);
	float petal = 0.16 + abs(cos(ang * 2.0)) * 0.12;
	float flower = step(r, petal) - step(r, 0.05);
	float diag = step(abs(abs(f.x) - abs(f.y)), 0.012) * step(0.3, r);
	float wear = smoothstep(0.35, 0.6, texture(sum, uv * 0.3).r);
	float pat = max(flower, diag) * wear;
	float n1 = texture(sum, uv * 0.8).r;
	vec3 base = mix(zaklad * 0.85, zaklad, smoothstep(0.3, 0.7, n1));
	ALBEDO = mix(base, barva, pat * 0.85);
	ROUGHNESS = 0.9;
}
