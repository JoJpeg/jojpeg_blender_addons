"""
Export All Alternatives as FBX

This action iterates through all alternatives, applies each one,
and exports the scene as FBX.
"""
import bpy
import os

def run():
    scene = bpy.context.scene
    vf_settings = scene.variable_fields
    
    if len(vf_settings.alternatives) == 0:
        print("No alternatives to export")
        return
    
    # Store original index
    original_index = vf_settings.active_alternative_index
    
    # Get export directory from blend file location
    blend_path = bpy.data.filepath
    if not blend_path:
        print("Please save the .blend file first")
        return
    
    export_dir = os.path.dirname(blend_path)
    blend_name = os.path.splitext(os.path.basename(blend_path))[0]
    
    try:
        for i, alt in enumerate(vf_settings.alternatives):
            print(f"Exporting FBX {i+1}/{len(vf_settings.alternatives)}: {alt.name}")
            
            # Select this alternative
            vf_settings.active_alternative_index = i
            
            # Run evaluation
            bpy.ops.variable_fields.update_evaluation()
            
            # Set export path with alternative name
            safe_name = alt.name.replace(" ", "_").replace("/", "_")
            export_path = os.path.join(export_dir, f"{blend_name}_{safe_name}.fbx")
            
            # Export FBX
            bpy.ops.export_scene.fbx(filepath=export_path)
            
            print(f"Exported: {export_path}")
    
    finally:
        # Restore original index
        vf_settings.active_alternative_index = original_index
        bpy.ops.variable_fields.update_evaluation()
    
    print("All alternatives exported!")

run()
