"""
Render All Alternatives (Animation)

This action iterates through all alternatives, applies each one,
and renders the full animation for each.
"""
import bpy
import os

def run():
    scene = bpy.context.scene
    vf_settings = scene.variable_fields
    
    if len(vf_settings.alternatives) == 0:
        print("No alternatives to render")
        return
    
    # Store original settings
    original_index = vf_settings.active_alternative_index
    original_filepath = scene.render.filepath
    
    # Get base path
    base_path = bpy.path.abspath(original_filepath)
    base_dir = os.path.dirname(base_path)
    base_name = os.path.splitext(os.path.basename(base_path))[0]
    
    try:
        for i, alt in enumerate(vf_settings.alternatives):
            print(f"Rendering animation {i+1}/{len(vf_settings.alternatives)}: {alt.name}")
            
            # Select this alternative
            vf_settings.active_alternative_index = i
            
            # Run evaluation
            bpy.ops.variable_fields.update_evaluation()
            
            # Set output path with alternative name
            safe_name = alt.name.replace(" ", "_").replace("/", "_")
            scene.render.filepath = os.path.join(base_dir, f"{base_name}_{safe_name}_")
            
            # Render animation
            bpy.ops.render.render(animation=True)
            
            print(f"Saved animation: {scene.render.filepath}")
    
    finally:
        # Restore original settings
        vf_settings.active_alternative_index = original_index
        scene.render.filepath = original_filepath
        bpy.ops.variable_fields.update_evaluation()
    
    print("All alternative animations rendered!")

run()
