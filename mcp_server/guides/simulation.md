# Simulation, digital twins and training

Tools: `unreal_run_simulation` (Simulate-in-Editor for N seconds, returns resulting actor transforms), `unreal_create_conveyor` (physics conveyor line with spawned parts), `unreal_spawn_from_data` (digital twin: spawn/position actors from a JSON list), `unreal_create_physics_stack`, physics tools (`unreal_set_simulate_physics`, `unreal_set_mass`, `unreal_set_collision_profile`).

Parts only slide when the slope beats friction (default ~0.7, i.e. steeper than ~35 degrees). Data tables and custom physics materials: use `unreal_execute_python`. Results are deterministic only within a run; record transforms you care about via `unreal_run_simulation(track=[...])`.
