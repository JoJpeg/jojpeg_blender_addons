import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    PointerProperty,
    FloatVectorProperty,
    CollectionProperty,
    BoolProperty,
)


def on_field_value_update(self, context):
    """Callback triggered when any field value changes - runs evaluation if auto_update is enabled."""
    vf_settings = context.scene.variable_fields
    if vf_settings.auto_update:
        bpy.ops.variable_fields.update_evaluation()


class FieldDefinition(bpy.types.PropertyGroup):
    id: StringProperty(name="ID", description="Unique identifier")
    name: StringProperty(name="Name", description="Display name for the field")
    type: EnumProperty(
        name="Type",
        items=[
            ('INT', "Integer", ""),
            ('FLOAT', "Float", ""),
            ('STRING', "String", ""),
            ('IMAGE', "Image", "Select or load an image"),
            ('COLOR', "Color", ""),
        ],
        default='FLOAT'
    )
    data_path: StringProperty(name="Data Path", description="Full Blender data path")
    default_value: StringProperty(name="Default Value", description="Initial value for new field values")
    eval_script: PointerProperty(name="Evaluation Script", type=bpy.types.Text)
    last_error: StringProperty(name="Last Error", description="Validation error message")

class FieldValue(bpy.types.PropertyGroup):
    field_id: StringProperty(name="Field ID")
    value_int: IntProperty(name="Integer Value", update=on_field_value_update)
    value_float: FloatProperty(name="Float Value", update=on_field_value_update)
    value_string: StringProperty(name="String Value", update=on_field_value_update)
    value_image: PointerProperty(name="Image Value", type=bpy.types.Image, update=on_field_value_update)
    value_color: FloatVectorProperty(name="Color Value", size=4, subtype='COLOR', min=0.0, max=1.0, update=on_field_value_update)
    
class Alternative(bpy.types.PropertyGroup):
    name: StringProperty(name="Name")
    field_values: CollectionProperty(type=FieldValue)

class Action(bpy.types.PropertyGroup):
    name: StringProperty(name="Name")
    script: PointerProperty(name="Script", type=bpy.types.Text)

class VariableFieldsSettings(bpy.types.PropertyGroup):
    is_active: BoolProperty(name="Is Active", default=False)
    dev_mode: BoolProperty(name="Dev Mode", default=True)
    auto_update: BoolProperty(name="Auto Update", default=False)
    
    # Panel expansion states
    show_actions: BoolProperty(name="Show Actions", default=True)
    show_general_actions: BoolProperty(name="Show General Actions", default=True)
    
    field_definitions: CollectionProperty(type=FieldDefinition)
    alternatives: CollectionProperty(type=Alternative)
    actions: CollectionProperty(type=Action)
    
    active_alternative_index: IntProperty(name="Active Alternative Index", default=0, update=on_field_value_update)

classes = (
    FieldDefinition,
    FieldValue,
    Alternative,
    Action,
    VariableFieldsSettings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.variable_fields = PointerProperty(type=VariableFieldsSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.variable_fields
