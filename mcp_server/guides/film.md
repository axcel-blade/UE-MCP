# Film, video and cinematics

Tools: `unreal_create_cinematic` (Level Sequence + CineCameraActor + camera cut + keyframed move), `unreal_add_transform_keys` (animate any actor), `unreal_set_cine_camera` (focal length, aperture, focus distance, filmback), `unreal_render_sequence_mrq` (Movie Render Queue to PNG/JPG/EXR/BMP image sequences), `unreal_list_level_sequences`.

Tips: frame rate defaults to 24 fps. Keep sequences under `/Game/Cinematics`. Render with MRQ needs the Movie Render Queue plugin and a saved level; rendering runs asynchronously, poll `unreal_get_render_status`. Product turntables: `unreal_create_turntable`. Encode frames to video with ffmpeg or MRQ's command-line encoder outside the editor.
