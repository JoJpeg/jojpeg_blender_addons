bl_info = {
    "name": "Blender Variable Fields",
    "description": "Efficient data swapping and task automation",
    "author": "",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "Properties > Tool",
    "warning": "",
    "doc_url": "",
    "category": "System",
}

import bpy
from . import properties
from . import ui
from . import operators
from bpy.app.handlers import persistent

classes = (
    # Add classes from properties, ui, operators here later
)


@persistent
def on_file_load(dummy):
    """Handler that runs after a .blend file is loaded - migrates legacy data if needed."""
    for scene in bpy.data.scenes:
        if hasattr(scene, 'variable_fields'):
            vf_settings = scene.variable_fields
            if vf_settings.is_active:
                print(f"[VF] File loaded, checking scene '{scene.name}' for legacy data...")
                properties.migrate_legacy_data_to_scopes(vf_settings)


def register():
    properties.register()
    ui.register()
    operators.register()
    
    # Register file load handler
    bpy.app.handlers.load_post.append(on_file_load)


def unregister():
    # Unregister file load handler
    if on_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_file_load)
    
    properties.unregister()
    ui.unregister()
    operators.unregister()

if __name__ == "__main__":
    register()
