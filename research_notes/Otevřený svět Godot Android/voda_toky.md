# Small rivers, ponds, moats and mills joined to terrain (Godot 4.4 GL Compatibility, Android)

Project context, as given in the brief: streams are a water ribbon along an axis of (x, z, water level) points. Their beds are carved into the terrain in Blender. Ponds are a disc mesh with depth stored per vertex. A mill is a prefab with its own terrain patch and channel. The user's recurring complaints are grey dry slabs, floating banks at the mill, sharp T-junctions, a step at the stream-to-pond join, and a moat that looks dry at its shallow banks.

## 1. Spline rivers: carving the bed and banks, building the surface, keeping height falling, flow and foam, avoiding the "canal" look, meander geometry

### Takeaway
Every mature tool treats the river as one data record: a spline whose points carry width, depth and water height. The terrain carve and the water mesh are both generated from that one record, with an explicit falloff band where the bank meets untouched terrain. Water height is forced to never rise downstream, and it is often stepped (pools and riffles) rather than a constant slope. Natural meanders have a wavelength of about 10–14 channel widths and a bend radius of about 2–3 widths.

### Cited Findings
**Unreal Water plugin (River and Lake water bodies)**
- River spline points carry per-point **Depth** and **River Width**. **Velocity** sets speed, and its sign sets flow direction. — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- On a Lake, all spline points must share one height, and depth comes from a single **Channel Depth**. In the project's terms, a pond or moat has one level and a stream has a level per point. — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- Terrain carve "Curve Settings":
  - **Use Curve Channel**
  - **Elevation Curve Asset**: the bed profile, an S-curve by default. You must keep its Y at 1 so the Depth values stay exact.
  - **Channel Edge Offset**: the offset from the water edge to where the curve starts.
  - **Curve Ramp Width**
  — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- "Water Heightmap Settings":
  - **Blend Mode**: Alpha Blend, Min, Max, Adaptive or Additive.
  - **Falloff Mode**: Angle or Width.
  - **Falloff Angle** and **Falloff Width**: the blend into the surrounding terrain.
  - **Edge Offset**: a flat strip before the falloff starts, "useful for flat river shores".
  - **ZOffset**
  - Carving works only when the Landscape has Edit Layers enabled.
  — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- The Water system unifies mesh rendering and shading for every water surface (river, lake, ocean) through a Water Zone. One surface system, not separate meshes per type. — [UE Water System overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-system-in-unreal-engine)

**Unreal Landscape splines (the older, general road and river carve)**
- Control points have:
  - **Width**
  - **Side Falloff**: a cosine-blended falloff band on each side.
  - **Left/Right Side Layer Falloff Factor**: the paint layer falloff.
  - **End Falloff**
  — [UE Landscape Splines](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-splines-in-unreal-engine); [UE 4.26 Splines](https://docs.unrealengine.com/4.26/BuildingWorlds/Landscape/Editing/Splines)
- Segments have **Raise Terrain** (for roads on embankments) and **Lower Terrain** (for rivers and ditches), plus a **Layer Name** for painting a material along the spline. — same sources

**Houdini to Unreal procedural river (Simon Schreibt, following Ben Schrijvers' Horizon Zero Dawn river workflow)**
- The steps:
  1. Sample terrain height at each spline point.
  2. Push the points downhill along an axis built from the terrain normal.
  3. A script ensures **no point is higher than the previous one** (monotonic descent).
  4. Replace continuous slopes with **steps**, which look more natural.
  5. Mark slope sections in vertex colors, for texture and particle placement.
  — [simonschreibt.de/gat/river](https://simonschreibt.de/gat/river)
- Mesh and carve:
  - Build the river mesh from the spline and re-align **only its outer edges** to the terrain.
  - The visible water is a thinner, subdivided mesh with UVs scaled by spline length.
  - Carve: lower the terrain under the river, cast rays up from each terrain point, and raise points that hit the river to the hit height.
  — [simonschreibt.de/gat/river](https://simonschreibt.de/gat/river)
- Riverbed mask: terrain polygons whose upward ray hits the river get a vertex colour. That colour drives darker, wetter albedo and roughness. — [simonschreibt.de/gat/river](https://simonschreibt.de/gat/river)
- Flow and foam:
  - Flow direction is written into **vertex colours** from spline direction, and an obstacle node bends the flow around objects.
  - Foam = distance to obstacles (isoOffset) stored in vertex colour, plus noise, minus a scrolling cloud texture.
  - Cascades get faster foam, masked to the slope sections.
  — [simonschreibt.de/gat/river](https://simonschreibt.de/gat/river)

**Godot Waterways (Arnklit)**
- Builds a river mesh from a Bezier curve. Shape parameters: Step Length Divs, Step Width Divs, Smoothing. "Snap to Colliders" places the path on terrain. — [Arnklit/Waterways](https://github.com/Arnklit/Waterways)
- Bakes flow and foam maps by raycasting from the river surface. Bake settings: Resolution, Raycast Distance and Layers, Dilate, Flowmap Blur, Foam Cutoff, Foam Offset, Foam Blur. — [Arnklit/Waterways](https://github.com/Arnklit/Waterways)
- Stated limitations:
  - rivers only (no lakes);
  - **rivers cannot merge or split**;
  - no real-time reflections;
  - no displacement;
  - **it does not carve terrain**.
  — [Arnklit/Waterways](https://github.com/Arnklit/Waterways)
- The original was built for Godot 3.2. — [GameFromScratch](https://gamefromscratch.com/waterways-terrain-add-ons-for-godot/)
- The Godot 4 port is **Waterways .NET** by Tshmofen: C#, .NET 8, Godot 4.2, MIT. — [Godot Asset Library #2607](https://godotengine.org/asset-library/asset/2607)

**Other tools**
- Unity R.A.M. (River Auto Material):
  - a spline with profiles that carves and textures terrain;
  - a wetness option;
  - a flow-map painter to turn local flow around stones.
  — [Unity Asset Store R.A.M 3](https://marketplace.unity.com/packages/tools/terrain/r-a-m-3-river-auto-material-3-287456)
- CryEngine's River Tool is essentially 2D. That makes rivers down mountains hard and waterfalls impossible, which shows the pitfall of a single-plane river. — reported in search results for [CryEngine River Tool](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048840). The page body was not fetched in full, so treat this as secondary.
- Saber's Expeditions map editor computes the default flowmap from height differences along the river spline and its curvature. — search snippet for [Expeditions guides](https://expeditions-guides.saber.games/map_modding/creating_a_map/terrain/geometry_brushes_for_terrain/context_menu/create_default_flowmap)

**Meander geometry**
- Langbein and Leopold's minimum-variance theory: meander length / mean bend radius ≈ **4.7**, about 5 in textbook summaries. Meanders follow a "sine-generated curve". — [USGS PP 422-H](https://pubs.usgs.gov/publication/pp422H); [Leopold & Langbein 1966, Scientific American](https://facultyweb.kennesaw.edu/jdirnber/docs/Leopold%20Riv%20Meand%201966.pdf)
- Wavelength is about **10–14 channel widths, averaging about 11**. Another dataset gives 7–11 widths at riffle sites. — [USGS "River meanders and channel size"](https://pubs.usgs.gov/publication/70015687); lecture summaries in search results ([uomustansiriyah](https://uomustansiriyah.edu.iq/media/lectures/5/5_2019_11_03!11_27_27_AM.pdf))
- Bend radius / width: modal value **2–3** (Williams 1986). About a third of sites fall below 2, and the full range runs to about 7. 11 / 4.7 ≈ 2.3 widths, which is consistent. — [USGS 70015687](https://pubs.usgs.gov/publication/70015687)

### Inferences
- Applying this to the project's (x, z, level) axis:
  - Add width, depth and bank falloff per point, and generate both the Blender carve and the ribbon from that one record. This removes the gaps between them, which are the source of the grey dry slabs.
  - Enforce `level[i+1] <= level[i]` in the data, and make it a test.
  - Group the drop into short riffles: steeper sections with foam and a narrower channel, separated by near-flat pools, instead of an even ramp.
- Avoiding the "canal" look:
  - Vary width ±20–30 % along the stream.
  - Put the meander axis on a sine-generated curve at about 11 widths wavelength.
  - Make the bed asymmetric: deeper at the outside of bends (cut bank), a shallow point bar on the inside.
  - Use Unreal's S-curve profile rather than a box section.
  - Add an "Edge Offset"-style flat wet strip at the waterline.
- A 1.5 m stream would need a wavelength of about 15–20 m and a bend radius of about 3–4.5 m. This is derived from the ratios above, not measured in the game.
- Waterways is not a fit:
  - it carves nothing;
  - it cannot do junctions;
  - its Godot 4 port is C#, an extra runtime on Android.
- Its baked flow/foam idea can be copied offline instead: bake to vertex colour in Blender.

### Gaps
- The GDC talks named in the brief (Uncharted water, Red Dead Redemption 2 rivers, Horizon water) were not fetched. The Horizon workflow is known here only through Schreibt's secondhand article.
- Valve's "Water Flow in Portal 2" (SIGGRAPH 2010, Vlachos) is the standard flow-map reference: two phases offset by half a cycle, plus noise to hide pulsing. Its PDF could not be text-extracted, so the details are unverified. URL: https://cdn.cloudflare.steamstatic.com/apps/valve/2010/siggraph2010_vlachos_waterflow.pdf
- No numeric step heights or riffle spacing were found in game sources. (Geomorphology commonly gives pool–riffle spacing of about 5–7 widths, but this was not verified in this session.)

## 2. Junctions: stream into a pond, out through a weir or dam, a millrace branching off and rejoining, blending water types

### Takeaway
Engines solve junctions by giving each terrain carve a priority or blend mode (Unreal: **Min** when a river crosses a lake) and by blending the water surface materials with a dedicated transition material or an overlap priority. They do not butt two meshes against each other. Waterways cannot do junctions at all. For a ribbon-plus-disc setup, the river's last points must reach the pond level inside the pond outline, and the river mesh must overlap and fade out under or into the pond surface.

### Cited Findings
- Unreal advises **Min blend mode** when a river intersects a lake, "so the river doesn't raise the lake's carved terrain". — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- Unreal Rivers have **River to Lake** and **River to Ocean** transition material slots. **Overlap Material Priority** (−8192..8191) chooses which body's material wins where bodies overlap and no transition material is set. — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- Waterways states "rivers can't merge or split", so a millrace branch is outside its scope. — [Arnklit/Waterways](https://github.com/Arnklit/Waterways)
- Schreibt/Horizon:
  - cascade (step) sections are flagged in vertex colour;
  - particles go at the cascade top and bottom;
  - cascades get faster foam.
  This is a pattern for weirs and the outflow at a dam. — [simonschreibt.de/gat/river](https://simonschreibt.de/gat/river)

### Inferences
- **Stream into pond (the "step into a dark pond" complaint):**
  - Extend the stream's spline 1–2 widths *into* the pond, with its last levels equal to the pond level (descending to it, never below it).
  - Carve with min(stream bed, pond bed).
  - Fade the ribbon's alpha and flow strength to 0 over that overlap, so only the pond surface remains, with no coplanar z-fight. Put the ribbon a few mm under the pond or use render priority.
  - The pond's per-vertex depth near the inlet must be shallow (a delta or fan), not a deep edge. Otherwise depth colour jumps from light to dark at the join.
- **Outflow over a weir or dam:**
  - Model it as a deliberate step: pond level → weir crest → stream level downstream.
  - Make the step a separate short "cascade" piece with foam and flow speed-up, and put particles or foam cards at the top and bottom.
  - The weir crest is an object in the data, so the drop is explained and does not read as a glitch.
- **Millrace (náhon):**
  - Model it as its own spline that starts *inside* the main stream or pond at a point whose level ≥ the race level. The headrace falls very gently; the archaeological example below is about 1:625.
  - It ends at the wheel, and the tailrace is a separate spline that rejoins downstream at a lower level.
  - Both ends overlap the parent water body as above, with the carve by min.
  - Give the branch point a curved entry, a 30–45° offtake angle with a widened mouth, instead of a 90° T. That answers the sharp T-junction complaint. (Design suggestion; the angle has no source.)
- Blending shallow and deep water: use one shader for all water with a per-vertex "depth" and "flow" attribute. Then the stream (shallow, flow > 0) and the pond (deep, flow ≈ 0) differ only in data and blend continuously across the overlap. This is the analogue of Unreal's unified water shading.

### Gaps
- No published game breakdown of a forked river or millrace mesh was found. The junction approaches above are inference.
- No source was found for how commercial tools stitch the surface mesh at confluences, beyond Unreal's material priority.

## 3. Shorelines: water meeting terrain, depth colour without screen texture, foam lines, wet sand

### Takeaway
On Godot GL Compatibility, `hint_depth_texture` does exist and can be read, but it costs a depth copy and uses OpenGL NDC (z in −1..1). It conflicts with the project rule against screen-reading. The mobile-safe approach is to precompute water depth per vertex (for ponds: already done) or in a small baked texture. Drive colour, opacity, foam and the shoreline fade from that, and darken the terrain splat in a wet band above the waterline.

### Cited Findings
- `hint_depth_texture` works in the Compatibility renderer, but Compatibility uses OpenGL NDC z in [−1, 1]. Reconstruct with `vec3(SCREEN_UV, depth) * 2.0 - 1.0`, or branch on `CURRENT_RENDERER == RENDERER_COMPATIBILITY`. The depth value is non-linear and needs the inverse projection matrix. Only the current viewport can be read. — [Godot docs, Advanced post-processing 4.3](https://docs.godotengine.org/es/4.3/tutorials/shaders/advanced_postprocessing.html); [Screen-reading shaders](https://docs.godotengine.org/en/stable/tutorials/shaders/screen-reading_shaders.html)
- The normal-roughness texture is Forward+ only. — [Screen-reading shaders](https://docs.godotengine.org/en/stable/tutorials/shaders/screen-reading_shaders.html)
- A Godot forum thread asking for depth fade and foam on the 4.4 mobile renderer got no concrete technique. — [forum.godotengine.org/t/107378](https://forum.godotengine.org/t/making-a-water-shader-in-godot-mobile/107378)
- Most Godot Shaders site water shaders compute shore foam from depth-texture distance. One stylised shader paints shore foam via vertex colour but needs Forward+ and Godot 4.7. — search results: [Stylized Water for Godot 4.x](https://godotshaders.com/shader/stylized-water-for-godot-4-x), [Foam Edge Water Shader](https://godotshaders.com/?p=10546), [Water shader 3D (Godot 4.3)](https://godotshaders.com/shader/water-shader-3d-godot-4-3/)
- The Horizon/Houdini workflow:
  - foam is a distance-to-obstacle value baked into vertex colour;
  - the riverbed or wet zone is a terrain vertex-colour mask that darkens albedo and lowers roughness.
  Both are offline bakes, with no runtime depth read. — [simonschreibt.de/gat/river](https://simonschreibt.de/gat/river)
- R.A.M. has a "wetness" option on carved banks. — [R.A.M 3](https://marketplace.unity.com/packages/tools/terrain/r-a-m-3-river-auto-material-3-287456)
- Unreal **Edge Offset** gives a flat strip at the shore before the falloff. — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)

### Inferences
- **Mobile recipe (no screen texture):**
  1. At export, compute `d = water_level − terrain_height` at each water vertex. Ponds already store this; do the same for streams and the moat.
  2. Pass `d` in `COLOR.r` or `CUSTOM0`.
  3. In the shader:
     - `alpha = smoothstep(0, d_fade, d)`;
     - `albedo = mix(shallow, deep, smoothstep(0, d_deep, d))`;
     - `foam = (1 − smoothstep(0, d_foam, d)) * noise(uv + flow*t)`.
  4. Extend the water mesh *past* the waterline by 0.3–1 m. Where `d < 0`, alpha = 0, so the intersection is soft and not a hard polygon edge.
- This needs enough vertex density near the shore, or a small baked depth texture (for example 1 px ≈ 0.5 m) over the pond or moat bounding box, sampled by world xz. That is a plain texture read, which is fine on GLES3.
- **The "moat looks dry at shallow banks" complaint:**
  - Current shallow areas are probably alpha ≈ 0 with a grey bed visible.
  - Fix with a minimum opacity / tint (for example alpha ≥ 0.35 where d > 0).
  - Darken and add gloss to a wet band on the terrain from waterline to +0.2–0.4 m, painted from the same record, as a wet/mud splat channel or vertex colour.
  - The dry slab problem is solved in data: the bed must be below the level everywhere the water outline claims water. A test can check `d > 0` inside every water outline.
- **The "black circular pond" complaint:** cap the deep colour, and keep the opacity curve rising gradually over the first 1–1.5 m of depth.

### Gaps
- The cost of `hint_depth_texture` on Compatibility on real Android GPUs was not measured. NEOVĚŘENO (unverified).
- No authoritative published shader for vertex-depth water in Godot Compatibility was found. The recipe above is our own synthesis.

## 4. Prefabs with their own terrain (the mill site): stitching into the heightmap

### Takeaway
The robust pattern is to **stamp** the prefab's ground into the global heightmap, so the terrain itself takes the prefab's shape, and let the prefab mesh carry only the buildings and channel walls. Where a separate mesh must stay, hide the seam with a blend or tape mesh, edge decals (moss, stones, reeds), and terrain-matching normals. Leaving two independent surfaces meeting at an edge produces floating banks.

### Cited Findings
- Unity Terrain Tools **Mesh Stamp**: "projects the shape of a mesh into the heightmap of your Terrain". Ctrl subtracts. Detail is limited by heightmap resolution, and only the widest section of a convex mesh projects. — [Unity Mesh Stamp](https://docs.unity3d.com/Packages/com.unity.terrain-tools@3.0/manual/mesh-stamp.html)
- Unity **Stamp Terrain** has a blend setting for how much existing terrain under the stamp is kept. — [Unity 6 Stamp Terrain](https://docs.unity3d.com/6000.4/Documentation/Manual/terrain-StampTerrain.html); [Terrain Tools 5.1](https://docs.unity3d.com/Packages/com.unity.terrain-tools@5.1/manual/stamp-terrain.html)
- CRYENGINE "Terrain Object Blending" can copy mesh objects into the heightmap mesh, so they become part of the terrain. It must be enabled in Level Settings. — search summary of [CryEngine Terrain Object Blending](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29799251). The page body was not read directly.
- "Taped UV seams": a mesh strip covering the seam with a material that fades in, to hide the material seam. — [orsvarn.com/uv-blend](https://orsvarn.com/uv-blend/)
- Polycount practitioners note that material blending alone leaves lighting seams. Fixes include copying terrain normals onto the mesh, a blend mesh over the intersection, or a border of moss or rocks. — [polycount discussion](https://polycount.com/discussion/comment/2240372)
- Unreal Water carving falloff (Falloff Width/Angle, Edge Offset) is the same idea for water bodies: the stamp has a falloff band so it never ends with a vertical edge. — [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)

### Inferences
- **For the mill**, in pipeline order terrain → paths → buildings → water. This matches the project rule.
  1. Store the mill's patch as a height stamp (a heightmap or mesh plus a falloff band) in the world record.
  2. Apply it to the global terrain in the terrain step.
  3. Carve the head- and tailrace splines.
  4. Place the building with its foundation skirt sunk 0.3–0.5 m below the stamped ground (the brief's "skirts").
  5. Generate water from the same records.
  The prefab's own ground mesh is then removed or reduced to channel walls. This fixes the floating banks at the mill edge.
- The stamp's border must be an exact match on its outer ring: terrain height equals stamp height, followed by a falloff of several metres with a smoothstep. Unity's "blend" or Unreal's "Falloff Width" are the models.
- Terrain normals and splat must be recomputed after stamping, otherwise there are lighting seams. Edge decals and reeds hide the remainder.
- If the prefab ground mesh is kept, its edge vertices should be snapped to the sampled terrain height and given the terrain normal at that point. A test can check for a max vertical gap of a few cm along the ring.

### Gaps
- No 80.lv or GDC breakdown specific to stitching prefab terrain was found in this session.

## 5. Godot 4 water/river addons and mobile suitability

### Takeaway
No Godot addon found here carves terrain *and* does junctions. Waterways (Godot 3, plus a C# Godot 4 port) makes river ribbons with baked flow and foam. Most Godot Shaders site water shaders rely on the depth or screen texture, which is unsuitable under the project's tablet rules. The best fit is the project's own Blender-baked ribbon plus one custom vertex-attribute water shader.

### Cited Findings
- Waterways: river mesh from a Bezier curve, baked flow and foam maps, buoyancy, a WaterSystem map. Stated limitations: no lakes, no merge or split, no reflections, no displacement. — [Arnklit/Waterways](https://github.com/Arnklit/Waterways)
- The Waterways .NET port is for Godot 4.2, written in C#. — [Asset Library 2607](https://godotengine.org/asset-library/asset/2607)
- Godot Shaders water entries mostly use depth-based foam. A vertex-colour-painted stylised shader requires Forward+ and 4.7. — search results ([godotshaders stylized](https://godotshaders.com/shader/stylized-water-for-godot-4-x), [realistic water](https://godotshaders.com/shader/realistic-water/))

### Inferences
- What to borrow from Waterways:
  - its flow and foam bake concept (raycast from the surface, dilate, blur);
  - its shader's two-phase flow-map scrolling.
- Bake these offline into vertex colours (flow xz in RG, foam in B, depth in A), so the runtime needs only vertex attributes and 1–2 tiling normal and noise textures. No screen or depth texture, no MSAA.

### Gaps
- No mobile benchmarks were found for any Godot water addon.

## 6. Medieval mills: millrace, tailrace, weir dimensions

### Takeaway
Archaeological examples give headraces about 1.3–3 m wide and up to about 0.7 m deep, with very gentle falls (about 1:600). Leats run for hundreds of metres. The mill pond is a widening of a few metres to tens of metres. Undershot wheels need little fall (about 0.6 m in the examples); overshot wheels need about 3–9 m. Few precise general medieval figures exist, and the cases below are site-specific.

### Cited Findings
- Terms: the headrace leads to the wheel, the wheelrace drives it, the tailrace leads away. A weir raises water into a millpond. — [Wikipedia: Mill race](https://en.wikipedia.org/wiki/Mill_race)
- **Killoteran, Co. Waterford** (early medieval vertical mill): the race averages about **3 m** wide and widens into a semicircular millpond more than 7 m across. — search summary of [excavations.ie 2004 Waterford](https://excavations.ie/report/2004/Waterford/0012801/)
- **Killaclug, Co. Clare** (post-medieval, possibly 16th-century origins):
  - leat **1.33–2.6 m** wide and 0.1–0.68 m deep;
  - about 375 m long;
  - about 0.6 m fall, a gradient of about **1:625**.
  — search summary of [TII monograph ch. 2 (Jackman)](https://tii.ie/media/gdkaev3x/mon-6-ch-2-jackman.pdf)
- **Kilbegly, Co. Roscommon** (early medieval horizontal mill): the flume narrows to about 0.45 m at the wheel pit, is 0.55 m high, and slopes at 20° from the pond. — same source / search summary
- **Grosmont** corn mill (post-medieval): a weir and sluice on the River Monnow, a **450 m** headrace, a 270 m tailrace. — [Coflein site 40053](https://coflein.gov.uk/en/site/40053)
- Overshot wheels: a drop of at least 10 ft (about 3 m), up to 30 ft (about 9 m), is desirable. — [Penn State, geography of mills](https://www.engr.psu.edu/MTAH/articles/pdf/geography_landscape_mills.pdf)
- Undershot wheels were the earliest type, a "run of the river" wheel needing modest flow. — [Wikipedia Mill race](https://en.wikipedia.org/wiki/Mill_race); [Encyclopedia.com](https://www.encyclopedia.com/history/news-wires-white-papers-and-books/power-technology-water)
- Example at a modern working mill: a fall of about 2 ft at an undershot wheel before the tailrace. — [Charlecote Mill](https://www.charlecotemill.co.uk/technical.html)

### Inferences
- For a small Bohemian village mill in the game, plausible data would be:
  - headrace 1.5–2.5 m wide, 0.4–0.7 m deep, nearly level (about 1:500–1:1000);
  - a weir of about 0.5–1.5 m on the stream;
  - a wheel pit with a drop of about 0.6–1.5 m (undershot or breastshot), or about 3 m+ if overshot;
  - a tailrace rejoining the stream downstream at the lower level.
- These ranges combine the site examples above, not one Czech source.
- Because the headrace is almost level while the stream descends, the race stands *above* the natural stream near the mill. That is why the mill site needs its own embankment, which should be in the terrain stamp rather than in a floating prefab bank.

### Gaps
- No Czech or Central European (náhon/mlýnský náhon) dimensional source was found. KCD2 mill references were not researched here.
- Typical medieval weir heights were not found in any source.
