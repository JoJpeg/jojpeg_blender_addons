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

classes = (
    # Add classes from properties, ui, operators here later
)

def register():
    properties.register()
    ui.register()
    operators.register()
    # for cls in classes:
    #     bpy.utils.register_class(cls)

def unregister():
    properties.unregister()
    ui.unregister()
    operators.unregister()
    # for cls in reversed(classes):
    #     bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
