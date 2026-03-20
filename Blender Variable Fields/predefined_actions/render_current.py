"""
Render Current Alternative

Renders the currently selected alternative as a still image.
"""
import bpy

def run():
    scene = bpy.context.scene
    vf_settings = scene.variable_fields
    
    # Make sure evaluation is up to date
    bpy.ops.variable_fields.update_evaluation()
    
    # Render
    bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
    
    print("Render started!")

run()
