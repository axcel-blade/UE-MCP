# Automotive, product design and manufacturing visualisation

Tools: `unreal_import_cad` (Datasmith/Interchange import of FBX, glTF/GLB, USD, OBJ, STEP/IGES/JT when Datasmith CAD is available), `unreal_create_product_studio` (cyclorama, three-point studio lighting, sky light; add a CC0 HDRI with `unreal_import_online_asset`), `unreal_create_turntable` (rotating platform + sequence), `unreal_create_variant_set` (Variant Manager configurator: material/visibility variants), `unreal_activate_variant`, `unreal_measure` (bounds, distances, dimensions in cm/mm).

Tips: imported CAD is often huge or tiny; check `unreal_measure` and scale. Use material instances for paint options and drive them from variants.
