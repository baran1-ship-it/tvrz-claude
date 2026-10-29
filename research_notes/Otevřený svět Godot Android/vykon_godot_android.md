# Rendering performance of large open 3D worlds in Godot 4.x on Android (Mali/Adreno, GL Compatibility vs Mobile)

Context: Godot 4.4.1, GL Compatibility, tablet without MSAA, about 42k objects and 20k nodes, MultiMesh grass in 32 m cells, 50–130 ms "drawing" hitches, 20–40 FPS.
Godot source facts below were checked directly in the `4.4` branch on GitHub (ProjectSettings.xml, drivers/gles3/*), retrieved 2026-10-29.

## 1. Budgets (draw calls, triangles, objects, memory) and which renderer to use on Mali/Adreno

### Takeaway
I found no measured, authoritative budget for "draw calls/triangles on mid-range Android in Godot 4". The only figures are rules of thumb from blogs: under 200 draw calls is safe, 200–500 is borderline, over 500 is risky. On the renderer question, the official docs and Arm's analysis agree:
- Compatibility (GLES3) has a low base cost but scales poorly.
- Mobile (Vulkan) has medium base and scaling costs, and through 4.4 it suffered bandwidth problems and regressions on Mali.
- For older or weaker Mali devices (G52-class), Compatibility is often faster. For large, dense scenes on newer GPUs, Mobile can scale better.

### Cited Findings
- The official comparison says Compatibility has "a low base rendering cost with a high scaling cost" and Mobile has medium costs for both. Mobile runs on low-end hardware but more slowly than Compatibility. The docs recommend Compatibility for "older mobile devices" and "best performance without advanced features". — [Godot docs: Overview of renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- Feature limits in Compatibility:
  - 8 omni/spot lights per mesh.
  - Shadowed lights use multi-pass rendering with less accurate blending.
  - 2 ReflectionProbes per mesh.
  - No FXAA/SMAA, no decals, no compute shaders.
  - RGBA8 color buffer.
  — [Godot docs: renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- **Automatic instancing** (merging MeshInstance3D nodes that share a mesh and material into one draw call) exists only in Forward+, not in Mobile or Compatibility. — [Godot docs: Optimizing 3D performance](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)
- Compatibility limits (ProjectSettings, 4.4):
  - `rendering/limits/opengl/max_renderable_elements` = 65536. "Elements refer to mesh surfaces and not meshes themselves". Anything above the limit is not drawn.
  - `max_renderable_lights` = 32.
  - `max_lights_per_object` = 8.
  - Lowering these "may decrease shader compile times".
  — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- Arm (Clay John, June 2025, Godot 4.4 dev 5) found that Godot's Vulkan renderer had been tuned for desktop, "leaving mobile Vulkan behind the OpenGL backend".
  - Test scene: a single cube at 2688×5984 with 4× MSAA on a Pixel 8 Pro. It ran at about 50 FPS and wrote about 30× more memory than it read, because render-pass attachments were always loaded and stored.
  - Fix: PR #98670, where the render graph decides load/store operations automatically. Afterwards the scene was vsync-locked, GPU use was 26%, and external write bandwidth was about 300× lower.
  — [Arm Community: Optimizing 3D scenes in Godot on Arm GPUs](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/optimizing-3d-scenes-in-godot-on-arm-gpus)
- Regression on Mali-G52 MC2 in the Mobile renderer: about 60 FPS on 4.4.dev3, about 45 FPS from 4.4.dev4 on (including 4.4 and 4.4.1 stable).
  - clayjohn: "almost certain" the cause was Swappy frame pacing (PR #96439). It forces multiples of the refresh rate, so a 90 Hz device that cannot hold 90 drops to 45.
  - He also said Godot uses an unoptimized shader for roughly the first minute, until pipelines specialize.
  - Adreno 640: disabling subpasses when there is no sky or transparent pass helped. Replacing an HDRI sky with a procedural sky restored smoothness.
  - The issue was closed after the reporter updated to Android 15; no code fix was merged.
  — [GitHub #109251](https://github.com/godotengine/godot/issues/109251)
- Galaxy A35 (Mali-G68), Godot 4.7.2: a simple scene ran at 80–90 FPS on Mobile and 120 FPS on Compatibility. Setting 3D scale to 0.7 on Mobile dropped it to 48–50 FPS (a scaling bug). — [GitHub #123633](https://github.com/godotengine/godot/issues/123633)
- Pixel 8 Pro / Mali-G610: an unoptimized high-poly scene with Terrain3D and MSAA ran at 15–20 FPS. Switching between Mobile and Compatibility did not help. Another user reported about 10 FPS. Advice from the thread: LOD, occlusion culling, and testing on the phone continuously. — [Godot Forum: Now I'm worried: Performance on Android](https://forum.godotengine.org/t/now-im-worried-performance-on-android/124716)
- Blogs (unverified rules of thumb):
  - Compatibility is "often the only backend that runs acceptably" on Adreno 610 / Mali-G52 because of poor Vulkan drivers.
  - Under 200 draw calls is safe, 200–500 is borderline, over 500 leads to thermal throttling on budget chips.
  — [bugnet: testing on low-end Android](https://bugnet.io/blog/how-to-test-your-godot-game-on-low-end-android-phones); [slicker.me field guide](https://slicker.me/godot/mobile-optimization.html)
- A naive renderer in a town scene can draw 10× to 100× more than is visible. The docs recommend building large worlds from tiles loaded on demand. — [Godot docs: Optimizing 3D](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)
- Textures: on Android the importer always uses the format the platform needs (ETC2/ASTC). `import_etc2_astc` is only an override. Already-imported textures change only after `.godot/imported` is deleted. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)

### Inferences
- In Compatibility, every visible surface of every MeshInstance3D is a separate draw call; there is no automatic instancing. With about 42k objects, the CPU-side render cost depends directly on how many objects are visible at once. The "high scaling cost" in the docs points to exactly this.
- The way out is fewer visible objects: merged meshes per cell, MultiMesh for repeated props, and HLOD through visibility ranges. Switching renderer is not the main lever.
- Switching to Mobile might help a dense scene on a newer Adreno/Mali, but in 4.4.x it carries known risks: the Swappy 45 FPS lock, bandwidth problems, and a heavier base cost. Only an A/B measurement on the real tablet would answer it.

### Gaps
- I found no reliable measured budget (triangles per frame, draw calls, VRAM) for Godot 4 on a specific Mali/Adreno tablet.
- I found no Reddit thread with measured numbers for an open world on Android.

## 2. Visibility ranges (HLOD): use, pitfalls, cost of fade

### Takeaway
Visibility ranges are Godot 4's manual LOD and HLOD tool. They work on any GeometryInstance3D, including MultiMeshInstance3D. "Disabled" fade mode, which uses hysteresis only, is the fastest. "Self" and "Dependencies" render objects as **transparent** during the transition, which costs performance; on a tiler that also means alpha blending and sorting. The cheaper alternative is dithering through material Distance Fade.

### Cited Findings
- **Begin/End** are measured from the camera to the **center of the AABB**. Margins set the width of the hysteresis or fade zone. Fade Mode only has an effect when a margin is greater than 0. — [Godot docs: Visibility ranges](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)
- Fade modes:
  - Disabled: "fastest", nothing is transparent.
  - Self: alpha-blends the node out and "forces transparent rendering", which costs performance.
  - Dependencies: fades in the children (nodes that use Visibility Parent). It is meant for HLOD and is also transparent.
  — [same](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)
- Visibility Parent:
  - Children are hidden according to the parent's range, and only after the parent has fully faded out.
  - The target does not have to be the scene-tree parent, but it must be a GeometryInstance3D.
  - Cycles are reported as errors.
  - A node hidden with `visible = false` drops out of the dependency tree, and its children then ignore its range.
  — [same](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)
- Recommendations from the docs:
  - Use simpler materials on far LODs. Turn off normal maps, "especially on mobile", as well as rim, clearcoat and similar.
  - Use dithering instead of alpha fade: set margins to 0, widen Begin/End by the fade distance, and set matching Distance Fade (Pixel Dither / Object Dither) on the materials.
  - Distance Fade fades only near or only far, so dithering suits just two LODs.
  — [same](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)
- `rendering/mesh_lod/lod_change/threshold_pixels` does **not** affect visibility ranges. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- The ProjectSettings note on occlusion culling says large open scenes "generally benefit more from mesh LOD and visibility ranges". — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- Godot cannot sort transparent objects by material and draws them back to front. Keep as few transparent objects as possible. — [Godot docs: Optimizing 3D](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)

### Inferences
- With fade mode Self or Dependencies on many objects, crossing a range boundary turns a batch of objects transparent for a moment. That raises the transparent-pass cost, can produce spikes when many objects switch at once, and possibly needs another shader variant (see section 4, compile hitches).
- On a tablet, use fade_mode = Disabled with a small margin (hysteresis), or dithering.
- MultiMesh cells do not need per-cell `visibility_range_end`: it is evaluated from the center of the whole cell's AABB. That is good for culling, but a 32 m cell pops in as a whole.

### Gaps
- I found no measured cost (ms) of alpha fade on Mali/Adreno.

## 3. Mesh LOD and occlusion culling on mobile

### Takeaway
Automatic mesh LOD (generated with meshoptimizer on import) works in Compatibility too; the 4.4 GLES3 code computes `lod_index` per surface. Occlusion culling is renderer-independent CPU rasterization with Embree. It costs CPU and, according to the docs, helps little in open terrain; in Mobile it saves overdraw because Mobile has no depth prepass.

### Cited Findings
- Mesh LOD:
  - Generated on import for glTF, .blend, Collada and FBX.
  - Selection is screen-space: the default `threshold_pixels` is 1.0, which is "perceptually lossless"; higher values switch LODs sooner.
  - `lod_bias` > 1 keeps detail longer; < 1 lowers it sooner.
  - Generation "is not perfect", especially on skinned meshes.
  — [Godot docs: Mesh LOD](https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html)
- MultiMesh and LOD: the LOD is chosen from the AABB point closest to the camera, and all instances in the node share it. Distant instances should go into separate nodes; this also enables per-node frustum and occlusion culling. — [Godot docs: Mesh LOD](https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html)
- The GLES3 renderer (4.4) contains mesh LOD selection: `mesh_surface_get_lod(..., lod_model_scale * lod_bias, lod_distance * lod_distance_multiplier, screen_mesh_lod_threshold, ...)`. — [rasterizer_scene_gles3.cpp 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/drivers/gles3/rasterizer_scene_gles3.cpp)
- How occlusion culling works:
  - CPU rasterization of occluders into a low-resolution buffer with Embree.
  - Overly detailed occluders cause "low performance or stuttering".
  - Moving an OccluderInstance3D rebuilds the BVH, which is expensive.
  - Occludees must be fully covered to be culled.
  — [Godot docs: Occlusion culling](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html)
- Mobile has no depth prepass, so occlusion culling saves overdraw there and the gains are greatest. It helps in interiors and in "pyramid-like" terrain. In scenes with few occlusion opportunities the CPU cost can outweigh the benefit. — [same](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html)
- Occlusion culling is off by default. The buffer has about `occlusion_rays_per_thread` (512) × number of CPU cores pixels. ProjectSettings warns that it has a CPU cost and that open scenes benefit little. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- Depth prepass in Compatibility: `depth_prepass/enable` defaults to true, but `disable_for_vendors` defaults to "PowerVR,Mali,Adreno,Apple", so **on Mali/Adreno the prepass is off**, with the reasoning that mobile tilers do not benefit from it. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- Culling runs on multiple threads only above `threaded_cull_minimum_instances` = 1000 instances. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)

### Inferences
- On the tablet, Compatibility runs without a depth prepass, so overdraw (fences, walls, foliage, grass) is paid in full in the fragment shader. A tiler with HSR/FPK (hidden-surface removal and forward pixel kill) partly mitigates this for opaque geometry, but not for alpha-scissor geometry.
- Occlusion culling may pay off in the village or castle (walls) as a few coarse box occluders. Over open landscape it is probably a loss; this needs measuring.
- Thin geometry (blades, branches) can disappear under automatic LOD. The docs only say "not perfect"; I have no specific source on thin geometry.

### Gaps
- I found no measured gain or loss from OccluderInstance3D on Android.
- I found no source on thin geometry disappearing under automatic LOD in Godot 4.

## 4. Shader compilation stutter, pipeline cache, warmup

### Takeaway
The 4.4 ubershaders and pipeline precompilation apply **only to Forward+ and Mobile**. In Compatibility (GLES3), shaders compile synchronously on the render thread the first time an object with a new material or variant is drawn. That is a classic source of one-off hitches of tens to hundreds of ms on Android. Mitigations:
- the disk shader cache (glProgramBinary), which helps from the second launch on;
- warmup: draw every material and variant once during loading.

### Cited Findings
- Ubershaders and precompilation (4.4+) cover Forward+ and Mobile only. "Compatibility is not supported" because OpenGL 3.3 / ES 3.0 / WebGL 2 lack the needed functionality. 2D elements are not precompiled either. — [Godot docs: Reducing stutter from shader (pipeline) compilations](https://docs.godotengine.org/en/latest/tutorials/performance/pipeline_compilations.html)
- The recommendation for Compatibility is to show materials, shaders and particles in the view frustum for at least one frame while the level loads. For Mobile/Forward+, also warm up features (MSAA level, shadows, reflection probes and so on); changing them during play causes immediate stutter. — [same](https://docs.godotengine.org/en/latest/tutorials/performance/pipeline_compilations.html)
- Monitors in the debugger (Forward+/Mobile): Canvas, Mesh, Surface, Draw ("should not happen normally"), and Specialization. — [same](https://docs.godotengine.org/en/latest/tutorials/performance/pipeline_compilations.html)
- The shader baker (4.5+) puts compiled shaders into the PCK. It does not work with Compatibility and "does not fix existing stutters". — [same](https://docs.godotengine.org/en/latest/tutorials/performance/pipeline_compilations.html)
- Android (Pixel 4 XL), issue #86731: stutter was longer in Compatibility than in Mobile. A maintainer: OpenGL limits compilation to the rendering thread, so compiling "will necessarily stall the renderer", and some drivers are bad. Docs on the same topic: render each mesh and effect for a frame during load, hidden behind 2D UI. — [GitHub #86731](https://github.com/godotengine/godot/issues/86731); [Godot docs: jitter/stutter](https://docs.godotengine.org/en/latest/tutorials/rendering/jitter_stutter.html)
- Root cause (Vulkan): pipelines are created in the first frame an object is used, and this is more visible on weaker CPUs/GPUs. — [GitHub #61233](https://github.com/godotengine/godot/issues/61233)
- In 4.4 the GLES3 shader code (`shader_gles3.cpp`):
  - saves and loads program binaries (`glGetProgramBinary` / `glProgramBinary`) to `shader_cache_dir`, keyed by sha;
  - `_compile_specialization` runs synchronously, with no asynchronous path.
  — [shader_gles3.cpp 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/drivers/gles3/shader_gles3.cpp)
- `rendering/shader_compiler/shader_cache/enabled` = true ("prevent stuttering … the next time the shader is needed"). `rendering_device/pipeline_cache/enable` = true applies to RD (Vulkan) only and does not control the driver's own cache. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- GLES3 builds a separate faster path or variant depending on features: discard/alpha clip, vertex modification, world coordinates, depth_prepass_alpha. These are different shader variants. — [rasterizer_scene_gles3.cpp 4.4, ~l. 229–241](https://raw.githubusercontent.com/godotengine/godot/4.4/drivers/gles3/rasterizer_scene_gles3.cpp)
- Forum, June 2026 (Forward+/D3D12): once the materials were pre-triggered during loading, "during runtime there are no stutters". — [Godot Forum: Stuttering when material is first used despite preload](https://forum.godotengine.org/t/stuttering-when-material-is-first-used-despite-preload/139752)

### Inferences
- The 50–130 ms "drawing" hitches on first sight (a new area, a new kind of model, fading or a shadow switching on) match a synchronous GLES3 compile.
- Test: does the hitch repeat in the same place after restarting the app (the cache should be warm by then)? If it disappears on the second launch, it is compilation.
- Warmup in Compatibility has to cover each **combination** that creates a variant: material × (with/without shadow) × skinning × MultiMesh vs single mesh × transparent (fade) vs opaque × lights. Godot's preload() of a resource is not enough; it has to be drawn in the camera view.
- Visibility-range fade (Self/Dependencies) switches an object into the transparent path, which can be a new variant the first time it happens.

### Gaps
- I found no measured compile time of a single GLES3 shader on Mali/Adreno in Godot.
- Unverified: whether a driver update or reinstall invalidates the Godot cache on Android.

## 5. MultiMesh vs MeshInstance3D, culling, shadows, transparency, MSAA

### Takeaway
A MultiMesh is culled as **one whole** by its AABB, LOD is chosen for the whole node, and it is a single draw call. It must therefore be split into cells: the trade-off is draw calls against culling precision. Shadows are expensive on mobile. The defaults for mobile are already lower (2048 directional atlas, soft filter quality 0). In Compatibility, shadowed lights render in multiple passes. MSAA on a tiler costs bandwidth (the Arm case), and transparency means back-to-front sorting.

### Cited Findings
- MultiMesh culling is "all or nothing". Chunking gives each cell its own AABB. More cells mean more draw calls; fewer cells mean worse culling. — [Godot Forum: procedural forest 4.7](https://forum.godotengine.org/t/best-approach-for-rendering-a-procedurally-generated-forest-with-thousands-of-trees-in-godot-4-7/141770); [Godot Forum: MultiMesh vs RenderingServer instances](https://forum.godotengine.org/t/multimesh-vs-renderingserver-meshinstances-for-an-extremely-high-number-of-instances/143319)
- MultiMesh LOD is taken from the nearest point of the AABB, shared by all instances. Separate nodes enable per-node culling. — [Godot docs: Mesh LOD](https://docs.godotengine.org/en/stable/tutorials/3d/mesh_lod.html)
- MultiMesh is the manual tool for thousands of identical objects (grass, crowds). Automatic instancing is Forward+ only. — [Godot docs: Optimizing 3D](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)
- Shadow settings:
  - `directional_shadow/size` = 4096, `size.mobile` = 2048.
  - `soft_shadow_filter_quality.mobile` = 0 (desktop default 2).
  - `positional_shadow/atlas_16_bits` = true ("performance improvements on some devices").
  — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- In Compatibility, shadowed lights use multi-pass rendering. — [Godot docs: renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- Real-time shadows, especially from multiple lights, can be too heavy for mobile. Recommendation: keep DirectionalLight dynamic and make most omni/spot lights Static (baked). — [Godot docs: Optimizing 3D](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)
- Transparent objects are drawn back to front with no batching by material. If only part of a mesh is transparent, give it its own surface. — [same](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)
- MSAA "can be significantly slower on some hardware … due to their limited memory bandwidth". The MSAA texture plus the resolve target being written to memory was the main cause of the bandwidth problem in Arm's test (Mobile renderer, 4.4 dev). — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml); [Arm Community](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/optimizing-3d-scenes-in-godot-on-arm-gpus)
- `force_vertex_shading` "can increase performance a lot" on low-end mobile, at a large cost in quality. — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- Billboards are cheap, but many overlapping ones exhaust fill rate. — [Godot docs: Optimizing 3D](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)

### Inferences
- With 32 m grass cells, each visible cell is a draw call in the color pass, plus more in the shadow pass for each cascade if the grass casts shadows.
- The directional shadow redraws its casters for every cascade. Grass and small props should have `cast_shadow = off`, the shadow distance should be short, and 2 cascades or fewer should be used. This is a standard recommendation; I found no numbers for Godot on Android.
- Alpha-scissor grass and foliage disables early-Z/HSR optimizations on tilers, and the GLES3 code sends materials with discard down a different (slower) path. Measurable overdraw of grass is the main suspect if the bottleneck is the GPU.

### Gaps
- I found no measured ms for directional shadows or alpha-scissor grass on Mali/Adreno in Godot 4.
- I found no recommended MultiMesh cell size backed by numbers.

## 6. Streaming: threaded loading, WorkerThreadPool, add_child, collision

### Takeaway
`ResourceLoader.load_threaded_request` moves reading and parsing off the main thread. `instantiate()`, `add_child()`, entering the scene tree, registering with the RenderingServer and PhysicsServer, and setting collision shapes stay on the main thread. They must be spread across frames (a time budget per frame). Heightmap collision is cheaper than a trimesh (ConcavePolygonShape3D).

### Cited Findings
- The active scene tree is not thread-safe. Build shape data in WorkerThreadPool and apply it with `call_deferred()` on the main thread. Use a lower-resolution HeightMapShape3D per chunk, which is "faster than ConcavePolygonShape3D". Rebuild only when entering a new chunk and reuse existing nodes. — [Godot Forum: optimize adding a collision mesh dynamically](https://forum.godotengine.org/t/how-to-optimize-adding-a-collision-mesh-dynamically/141564)
- Creating a PhysicsBody with collision on a thread and adding it to the tree produces "can only be accessed from either the main thread or a thread group". — [GitHub #83496](https://github.com/godotengine/godot/issues/83496)
- Forum reports on threaded loading:
  - Godot 4.6: threaded loading "doesn't fully fix stutters when instantiating a scene" (disputed in the same thread).
  - 4.3 beta: `instantiate()` in a Thread still froze the main thread.
  - 4.2.2: inconsistent loading times.
  — [Godot Forum: Background Loading freezing main thread](https://forum.godotengine.org/t/background-loading-freezing-main-thread/54782); [Instantiate() freezing game](https://forum.godotengine.org/t/instantiate-freezing-game/69347); [inconsistent loading times](https://forum.godotengine.org/t/godot-inconsistent-loading-times-driving-me-mad-resourceloader-load_threaded_request/65840)
- `load()` / `load_threaded_request()` can freeze the main thread when the game is launched from the editor; it did not reproduce in release builds (4.7.x). — [GitHub #124128](https://github.com/godotengine/godot/issues/124128)
- Blog (unverified): chunk stutter comes from synchronous instancing on the main thread. Fix it with threaded loading plus spreading `add_child` over several frames. — [bugnet: chunk instancing stutter](https://bugnet.io/blog/how-to-fix-godot-scene-chunk-instancing-stutter-on-stream)
- `rendering/driver/threads/thread_model` (a separate render thread) is marked experimental in 4.4, with "several known bugs which can lead to crashing". — [ProjectSettings.xml 4.4](https://raw.githubusercontent.com/godotengine/godot/4.4/doc/classes/ProjectSettings.xml)
- Moving an OccluderInstance3D rebuilds the BVH. Toggling visibility is cheaper. — [Godot docs: Occlusion culling](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html)

### Inferences
- With 20k nodes, adding or removing a chunk with hundreds of nodes in one frame can take tens of ms on a tablet CPU. Use a per-frame time budget (for example, add nodes until 2–4 ms have passed), or use RenderingServer/PhysicsServer RIDs directly without nodes.
- A visual hitch caused by a newly added material is a shader compile (section 4), not a load problem.

### Gaps
- I found no measured cost of `add_child` or of creating a ConcavePolygonShape3D versus a HeightMapShape3D on Android.

## 7. Profiling on Android

### Takeaway
The Godot remote debugger (Profiler, Visual Profiler, Monitors) works over USB/Wi-Fi. For a system and GPU view there are Perfetto (official tracing support with Android templates), Arm Performance Studio (Streamline + Performance Advisor, used by Godot developers themselves), and AGI or Snapdragon Profiler for Adreno. Frame time is determined by the slower of CPU and GPU.

### Cited Findings
- Godot docs list Tracy, Perfetto and Instruments as tracing profilers. Perfetto is the default tracing system for Android, and prebuilt export templates with Perfetto enabled are on the godot-builds Releases page. Only explicitly instrumented code is visible, and binaries must not be stripped. — [Godot docs: Using C++ profilers](https://docs.godotengine.org/en/stable/engine_details/development/profiling/index.html)
- Arm workflow:
  - `streamline_me.py --lwi-mode counters` connects Streamline to the device.
  - Performance Advisor needs a debuggable build.
  - `Streamline-cli -pa` produces the report.
  - Mali Offline Compiler for analyzing shaders.
  — [Arm Community blog](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/optimizing-3d-scenes-in-godot-on-arm-gpus); [Arm Learning Path: Profile Godot with Arm Performance Studio](https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/godot_packages/profile-godot-with-aps/)
- Total frame time is set by the slower side. Example: CPU 9 ms with GPU 50 ms gives a 50 ms frame, and cutting the CPU to 1 ms changes nothing. Measure on several devices; the docs list Arm Performance Studio among GPU tools. — [Godot docs: General optimization](https://docs.godotengine.org/en/stable/tutorials/performance/general_optimization.html)
- Pipeline-compile monitors in the debugger exist for RD renderers (Forward+/Mobile), not for Compatibility. — [Godot docs: pipeline compilations](https://docs.godotengine.org/en/latest/tutorials/performance/pipeline_compilations.html)
- Forum: Profiler and Visual Profiler can show "unaccounted" time, where Process time is much higher than script time. — [Godot Forum](https://forum.godotengine.org/t/profiler-and-visual-profiler-both-show-unaccounted-for-time/123864)
- Mobile renderer: the Swappy frame pacer can lock FPS to a fraction of the refresh rate (for example 45 on 90 Hz). clayjohn recommended experimenting with `swappy_mode` and `input_devices/buffering/agile_event_flushing`. — [GitHub #109251](https://github.com/godotengine/godot/issues/109251)

### Inferences
- A practical way to tell CPU from GPU bottlenecks on the tablet: run at a lower 3D resolution (`scaling_3d_scale`) and see whether FPS changes. If it does not, the bottleneck is the CPU (draw calls, culling, scripts). This is general practice; the Godot docs do not describe it explicitly. In Mobile it is complicated by bug #123633.
- In the Godot monitors, watch `RENDER_TOTAL_DRAW_CALLS_IN_FRAME`, `RENDER_TOTAL_OBJECTS_IN_FRAME` and `RENDER_TOTAL_PRIMITIVES_IN_FRAME` at the moment of a hitch, compared with the frame before. A one-off spike with no change in counts suggests compilation or main-thread work.

### Gaps
- I found no Godot-specific guide to Snapdragon Profiler or AGI.
- Unverified: whether Compatibility on Android shows GPU time in the Visual Profiler (it needs timer queries, which GLES drivers may not support).
