// Barva krajiny z dalky (radce 11:20, KCD 20:50): jedna funkce pro teren za 100 m (zem.gdshader) i pro trsy od 40-80 m
// (stebla.gdshader, e_vegetationUseTerrainColorDistance) - trava a dalka maji barvu z jednoho zdroje.
// p = poloha xz, st = maska stanoviste (R jehl., G listn. koruny), les_v = les z barvy vrcholu terenu (trsy: 0).
vec3 barva_krajiny(vec2 p, vec4 st, float les_v, sampler2D sum_t, vec3 b_louky, vec3 b_lesa) {
	float n1 = texture(sum_t, p * 0.03).r;
	float mk = texture(sum_t, p * 0.022 + 0.71).r * 0.65 + texture(sum_t, p * 0.05 + 0.13).r * 0.35;
	return mix(b_louky * mix(0.85, 1.12, mk), b_lesa * (0.8 + 0.4 * n1), smoothstep(0.2, 0.6, max(les_v, st.r + st.g)));
}
