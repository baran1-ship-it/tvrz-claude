# Godot a Terrain3D – rozhodnutí o verzi (29. 10. 2026)

Dotaz Míši: „Můžeme jít výše s Godotem, pomůže na Terrain3D?“ Ověřeno na oficiálních stránkách 29. 10. 2026:

| | fakt | zdroj |
|---|---|---|
| Godot | poslední stabilní **4.7.2** (18. 8. 2026); 4.8 je beta | godotengine.org/download/archive |
| Godot 4.5 | shader baker (předkompilace shaderů – v článku jen Metal/D3D12), stencil, levná specular occlusion i v Compatibility, SMAA | godotengine.org/releases/4.5 |
| Godot 4.6 | glow před tonemapem, opravy pádů Vulkan Mobile na Adreno; pro Compatibility v článku nic zásadního | godotengine.org/releases/4.6 |
| Terrain3D | stabilní **1.0.2** (podporuje Godot 4.4–4.7), 1.1.0-rc1 (4.5–4.8, mobil „experimental“) | github.com/TokisanGames/Terrain3D/releases |
| Terrain3D + Compatibility | „fully supported in Terrain3D 1.0 and Godot 4.4“ | terrain3d.readthedocs.io platforms |
| Terrain3D + Android | „reported to work“ (od 0.9.1), arm64 binárky; doporučení ETC2/ASTC; „Max Regions“ kvůli malým uniform bufferům mobilů | tamtéž, performance.html |
| Terrain3D umí | clipmap LOD s geomorfingem (žádné švy/sukně), malování až 32 textur, dynamická kolize, instancer vegetace s LOD; streaming regionů až ve 1.2 | releases |

## Co by to Puchartu přineslo
- **Terrain3D:** ruční malování povrchů a doladění terénu v editoru (cesty, okolí hradů, koryta) a terén bez švů. Výkonově
  terén dnes **není brzda** (změřeno: 33 kreslení, 0,36 M troj.; brzda je les 1,8 M). Havran: „Terrain3D jen když měření
  ukáže terén jako hlavní brzdu“ (Míša).
- **Vyšší Godot:** pro Compatibility na Androidu jsem v release poznámkách 4.5/4.6 nenašel nic, co by řešilo náš rozpočet
  (MultiMesh, LOD, okluze, fade visibility range – nezmíněno). Havran má na 4.4.1 ověřené chování na Xiaomi Pad 8.

## Doporučení
1. Zůstat zatím na **4.4.1** (tablet ověřený), ale udělat **A/B na tabletu**: stejný výsek v 4.4.1 a 4.7.2 (APK debug),
   měřit p95, VRAM, pády. Při přechodu brát **4.7.x** (ne 4.8 beta).
2. Terrain3D 1.0.2 zkusit jako **samostatnou zkoušku** (import naší výškové mřížky, kolize, Android) – pokud projde na
   tabletu, přínos je hlavně v editaci, ne ve výkonu. Rozhoduje Míša.
