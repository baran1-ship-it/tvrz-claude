// Potok (Waterways, MIT - addons/waterways/LICENSE) upraveny pro renderer Compatibility (tablet):
// bez hloubkove a obrazovkove textury. Hloubka vody je ve vrcholech (COLOR.r * 4 m, tools/reka_bake.gd),
// barva od melke hnedozelene po tmavou, pruhlednost u brehu podle hloubky (pozvolny prechod, ne hrana).
// Copyright © 2023 Kasper Arnklit Frandsen - MIT License
// See `LICENSE.md` included in the source distribution for details.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_schlick_ggx;

// If you are making your own shader, you can customize or add your own
// parameters below and they will automatically get parsed and displayed in
// the River inspector.

// Use prefixes: albedo_, emission_, transparency_, flow_, foam_ and custom_
// to automatically put your parameters into categories in the inspector.

// If "curve" is in the name, the inspector will represent and easing curve.
// mat4´s with "color" in their name will get parsed as gradients.

// Main
uniform float normal_scale : hint_range(-16.0, 16.0) = 1.0;
uniform sampler2D normal_bump_texture : hint_normal;
uniform vec3 uv_scale = vec3(1.0, 1.0, 1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.2;
uniform float edge_fade : hint_range(0.0, 1.0) = 0.25;

// Albedo
//uniform mat4 albedo_color = mat4(vec4(0.0, 0.15, 0.0, 0.0), vec4(0.8, 0.2, 0.0, 0.0), vec4(1.0, 0.5, 0.0, 0.0), vec4(0.0));
uniform mat4 albedo_color = mat4(vec4(0.0, 0.8, 1.0, 0.0), vec4(0.15, 0.2, 0.5, 0.0), vec4(0.0), vec4(0.0));
uniform float albedo_depth : hint_range(0.0, 200.0) = 10.0;
uniform float albedo_depth_curve = 0.25;

// Transparency
uniform float transparency_clarity : hint_range(0.0, 200.0) = 10.0;
uniform float transparency_depth_curve = 0.25;
uniform float transparency_refraction : hint_range(-1.0, 1.0) = 0.05;

// Flow
uniform float flow_speed : hint_range(0.0, 10.0) = 1.0;
uniform float flow_base : hint_range(0.0, 8.0) = 0.0;
uniform float flow_steepness : hint_range(0.0, 8.0) = 2.0;
uniform float flow_distance : hint_range(0.0, 8.0) = 1.0;
uniform float flow_pressure : hint_range(0.0, 8.0) = 1.0;
uniform float flow_max : hint_range(0.0, 8.0) = 4.0;

// Foam
uniform vec4 foam_color : source_color = vec4(0.9, 0.9, 0.9, 1.0);
uniform float foam_amount : hint_range(0.0, 4.0) = 2.0;
uniform float foam_steepness : hint_range(0.0, 8.0) = 2.0;
uniform float foam_smoothness : hint_range(0.0, 1.0) = 0.3;

// Internal uniforms - DO NOT CUSTOMIZE THESE
uniform float i_lod0_distance : hint_range(5.0, 200.0) = 50.0;
uniform sampler2D i_texture_foam_noise : hint_default_white;
uniform sampler2D i_flowmap : hint_normal;
uniform sampler2D i_distmap : hint_default_white;
uniform bool i_valid_flowmap = false;
uniform int i_uv2_sides = 2;


vec3 FlowUVW(vec2 uv_in, vec2 flowVector, vec2 jump, vec3 tiling, float time, bool flowB) {
	float phaseOffset = flowB ? 0.5 : 0.0;
	float progress = fract(time + phaseOffset);
	vec3 uvw;
	uvw.xy = uv_in - flowVector * (progress - 0.5);
	uvw.xy *= tiling.xy;
	uvw.xy += phaseOffset;
	uvw.xy += (time - progress) * jump;
	uvw.z = 1.0 - abs(1.0 - 2.0 * progress);
	return uvw;
}

// ease implementation copied from math_funcs.cpp in source
float ease(float p_x, float p_c) {
	if (p_x < 0.0) {
		p_x = 0.0;
	} else if (p_x > 1.0) {
		p_x = 1.0;
	}
	if (p_c > 0.0) {
		if (p_c < 1.0) {
			return 1.0 - pow(1.0 - p_x, 1.0 / p_c);
		} else {
			return pow(p_x, p_c);
		}
	} else if (p_c < 0.0) {
		//inout ease
		
		if (p_x < 0.5) {
			return pow(p_x * 2.0, -p_c) * 0.5;
		} else {
			return (1.0 - pow(1.0 - (p_x - 0.5) * 2.0, -p_c)) * 0.5 + 0.5;
		}
	} else {
		return 0.0; // no ease (raw)
	}
}

float lin2srgb(float lin) {
	return pow(lin, 2.2);
}

mat4 gradient_lin2srgb(mat4 lin_mat) {
	mat4 srgb_mat = mat4(
		vec4(lin2srgb(lin_mat[0].x), lin2srgb(lin_mat[0].y), lin2srgb(lin_mat[0].z), lin2srgb(lin_mat[0].w)),
		vec4(lin2srgb(lin_mat[1].x), lin2srgb(lin_mat[1].y), lin2srgb(lin_mat[1].z), lin2srgb(lin_mat[1].w)),
		vec4(0.0),
		vec4(0.0)
	);
	return srgb_mat;
}

uniform vec3 melka : source_color = vec3(0.353, 0.42, 0.227);   // #5A6B3A
uniform vec3 hluboka : source_color = vec3(0.118, 0.165, 0.11); // #1E2A1C
uniform float hloubka_barvy = 1.2;     // m: od teto hloubky uz plne tmava
uniform float cirost = 0.35;           // m: do teto hloubky je voda u brehu pruhledna
varying float hloubka;
varying vec3 wpos;
// kameny v toku (0.60, Misa: voda kolem kamenu se ma cerit): x, z, polomer, uhel proudu - 12 nejblizsich (svet.kameny_toku_k)
uniform vec4 kam[12];

void vertex() {
	hloubka = COLOR.r * 4.0;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// cereni kolem kamenu: vec3(gradient x, z, pena)
vec3 kolem_kamenu(vec2 p) {
	vec2 g = vec2(0.0);
	float pena = 0.0;
	for (int i = 0; i < 12; i++) {
		float r = kam[i].z;
		if (r <= 0.0) continue;
		vec2 d = p - kam[i].xy;
		float dl = length(d);
		float od = dl - r;                                 // vzdalenost od okraje kamene
		if (od > r * 6.0 + 1.5) continue;
		vec2 tok = vec2(cos(kam[i].w), sin(kam[i].w));
		float po = dot(d, tok);                            // po proudu (+) / proti (-)
		float bok = dot(d, vec2(-tok.y, tok.x));
		// vence vlnek kolem kamene (stojate vlny), proti proudu vyssi (vzduta voda)
		float vl = exp(-max(od, 0.0) * 4.0 / (0.3 + r));
		float pred = smoothstep(0.0, -r, po) * 0.6 + 0.4;
		g += (d / (dl + 1e-4)) * sin(od * 26.0 - TIME * 7.0) * vl * pred * 0.5;
		// pena: tenky vence pri kameni, trha se
		float sum = texture(i_texture_foam_noise, p * 1.8 + tok * TIME * 0.6).r;
		pena = max(pena, exp(-od * od * 18.0 / (0.2 + r)) * smoothstep(0.35, 0.8, sum) * 0.55);
		// uplav za kamenem: zuzujici se pruhy po proudu, unasene proudem
		if (po > 0.0) {
			float sir = r * (0.9 + po * 0.25);
			float stopa = exp(-bok * bok / (sir * sir)) * exp(-po / (r * 5.0 + 0.6));
			float pruhy = texture(i_texture_foam_noise, vec2(po * 0.9 - TIME * 0.9, bok * 2.6) + kam[i].xy).r;
			pena = max(pena, stopa * smoothstep(0.45, 0.8, pruhy) * 0.8);
			g += vec2(-tok.y, tok.x) * sin(bok * 18.0 / (r + 0.2) - po * 6.0 + TIME * 5.0) * stopa * 0.35;
		}
	}
	return vec3(g, pena);
}

void fragment() {
	// Sample the UV2 textures. To avoid issues with the UV2 seams, margins
	// are left on the textures, so the UV2 needs to be rescaled to cut off
	// the margins.
	vec2 custom_UV = (UV2 + 1.0 / float(i_uv2_sides)) * (float(i_uv2_sides) / float(i_uv2_sides + 2));
	vec4 flow_foam_noise = textureLod(i_flowmap, custom_UV, 0.0);
	vec2 dist_pressure = textureLod(i_distmap, custom_UV, 0.0).xy;
	
	vec2 flow;
	float distance_map;
	float pressure_map;
	float foam_mask;
	if (i_valid_flowmap) {
		flow = flow_foam_noise.xy;
		distance_map = (1.0 - dist_pressure.r) * 2.0;
		pressure_map = dist_pressure.g * 2.0;
		foam_mask = flow_foam_noise.b;
	} else {
		flow = vec2(0.5, 0.572);
		distance_map = 0.5;
		pressure_map = 0.5;
		foam_mask = 0.0;
	}
	
	flow = (flow - 0.5) * 2.0; // unpack the flow vectors
	
	// Calculate the steepness map
	vec3 flow_viewspace = flow.x * TANGENT + flow.y * BINORMAL;
	vec3 up_viewspace = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	float steepness_map = max(0.0, dot(flow_viewspace, up_viewspace)) * 4.0;
	
	float flow_force = min(flow_base + steepness_map * flow_steepness + distance_map * flow_distance + pressure_map * flow_pressure, flow_max);
	flow *= flow_force;
	
	vec2 jump1 = vec2(0.24, 0.2083333);
	vec2 jump2 = vec2(0.20, 0.25);
	vec2 jump3 = vec2(0.22, 0.27);
	float time = TIME * flow_speed + flow_foam_noise.a;
	vec3 flow_uvA = FlowUVW(UV, flow, jump1, uv_scale, time, false);
	vec3 flow_uvB = FlowUVW(UV, flow, jump1, uv_scale, time, true);
	vec3 flowx2_uvA = FlowUVW(UV, flow, jump2, uv_scale * 2.0, time, false);
	vec3 flowx2_uvB = FlowUVW(UV, flow, jump2, uv_scale * 2.0, time, true);
	
	// Level 1 Water
	vec3 water_a = texture(normal_bump_texture, flow_uvA.xy).rgb;
	vec3 water_b = texture(normal_bump_texture, flow_uvB.xy).rgb;
	vec3 water = water_a * flow_uvA.z + water_b * flow_uvB.z;

	vec2 water_norFBM = water.rg;
	float water_foamFBM = water.b;

	// Level 2 Water, only add in if closer than lod 0 distance
	if (VERTEX.z < i_lod0_distance) {
		vec3 waterx2_a = texture(normal_bump_texture, flowx2_uvA.xy).rgb;
		vec3 waterx2_b = texture(normal_bump_texture, flowx2_uvB.xy, 0.0).rgb;
		vec3 waterx2 = waterx2_a * flowx2_uvA.z + waterx2_b * flowx2_uvB.z;

		water_norFBM *= 0.65;
		water_norFBM += waterx2.rg * 0.35;
		water_foamFBM *= waterx2.b * 2.0;
	}
	
	float foam_randomness = texture(i_texture_foam_noise, UV * uv_scale.xy).r;
	
	foam_mask += steepness_map * foam_steepness * foam_randomness;
	foam_mask = clamp(foam_mask, 0.0, 1.0);
	water_foamFBM = clamp((water_foamFBM * foam_amount) - (0.5 / foam_amount), 0.0, 1.0);
	float foam_smooth = clamp(water_foamFBM * foam_mask, 0.0, 1.0);
	float foam_sharp = clamp(water_foamFBM - (1.0 - foam_mask), 0.0, 1.0);
	float combined_foam = mix(foam_sharp, foam_smooth, foam_smoothness);

	vec3 kk = kolem_kamenu(wpos.xz);
	combined_foam = max(combined_foam, kk.z * 0.6);
	water_norFBM += kk.xy * 0.12;

	float t = smoothstep(0.0, hloubka_barvy, hloubka);
	vec3 barva = mix(melka, hluboka, t);
	ALBEDO = mix(barva, foam_color.rgb, combined_foam * foam_color.a);
	ALPHA = clamp(smoothstep(0.0, cirost, hloubka) * 0.92 + combined_foam, 0.0, 1.0);
	SPECULAR = 0.25;
	ROUGHNESS = roughness;
	NORMAL_MAP = vec3(water_norFBM, 0);
	NORMAL_MAP_DEPTH = normal_scale;
}
