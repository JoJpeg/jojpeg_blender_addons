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


class Scope(bpy.types.PropertyGroup):
    """A scope contains alternatives, fields, and scope-specific actions."""
    name: StringProperty(name="Name", default="Scope")
    field_definitions: CollectionProperty(type=FieldDefinition)
    alternatives: CollectionProperty(type=Alternative)
    actions: CollectionProperty(type=Action)
    active_alternative_index: IntProperty(name="Active Alternative Index", default=0, update=on_field_value_update)


def get_active_scope(vf_settings):
    """Helper function to get the currently active scope."""
    if len(vf_settings.scopes) == 0:
        return None
    index = max(0, min(vf_settings.active_scope_index, len(vf_settings.scopes) - 1))
    return vf_settings.scopes[index]


class VariableFieldsSettings(bpy.types.PropertyGroup):
    is_active: BoolProperty(name="Is Active", default=False)
    dev_mode: BoolProperty(name="Dev Mode", default=True)
    auto_update: BoolProperty(name="Auto Update", default=False)
    
    # Panel expansion states
    show_actions: BoolProperty(name="Show Actions", default=True)
    show_general_actions: BoolProperty(name="Show General Actions", default=True)
    
    # Scopes system
    scopes: CollectionProperty(type=Scope)
    active_scope_index: IntProperty(name="Active Scope Index", default=0)
    
    # Scopeless general actions (e.g., "Render All")
    general_actions: CollectionProperty(type=Action)
    
    # Legacy properties (kept for backwards compatibility with old files)
    # These will be migrated to scopes on activation
    field_definitions: CollectionProperty(type=FieldDefinition)
    alternatives: CollectionProperty(type=Alternative)
    actions: CollectionProperty(type=Action)
    active_alternative_index: IntProperty(name="Active Alternative Index", default=0)


def migrate_legacy_data_to_scopes(vf_settings):
    """
    Migrate old data structure (pre-scopes) to new scopes system.
    Called when activating Variable Fields on a file that has legacy data.
    Returns True if migration was performed.
    """
    # Debug: Print what we find
    print(f"[VF Migration] Checking for legacy data...")
    print(f"[VF Migration] Legacy field_definitions: {len(vf_settings.field_definitions)}")
    print(f"[VF Migration] Legacy alternatives: {len(vf_settings.alternatives)}")
    print(f"[VF Migration] Legacy actions: {len(vf_settings.actions)}")
    print(f"[VF Migration] Existing scopes: {len(vf_settings.scopes)}")
    
    # Check if we have legacy data and no scopes
    has_legacy_data = (
        len(vf_settings.field_definitions) > 0 or 
        len(vf_settings.alternatives) > 0 or 
        len(vf_settings.actions) > 0
    )
    
    if not has_legacy_data or len(vf_settings.scopes) > 0:
        print(f"[VF Migration] Skipping migration - has_legacy_data={has_legacy_data}, scopes_exist={len(vf_settings.scopes) > 0}")
        return False
    
    print(f"[VF Migration] Performing migration...")
    
    # Create default scope from legacy data
    scope = vf_settings.scopes.add()
    scope.name = "Scope"
    
    # Migrate field definitions
    for old_field in vf_settings.field_definitions:
        new_field = scope.field_definitions.add()
        new_field.id = old_field.id
        new_field.name = old_field.name
        new_field.type = old_field.type
        new_field.data_path = old_field.data_path
        new_field.default_value = old_field.default_value
        new_field.eval_script = old_field.eval_script
        new_field.last_error = old_field.last_error
    
    # Migrate alternatives
    for old_alt in vf_settings.alternatives:
        new_alt = scope.alternatives.add()
        new_alt.name = old_alt.name
        for old_fv in old_alt.field_values:
            new_fv = new_alt.field_values.add()
            new_fv.field_id = old_fv.field_id
            new_fv.value_int = old_fv.value_int
            new_fv.value_float = old_fv.value_float
            new_fv.value_string = old_fv.value_string
            new_fv.value_image = old_fv.value_image
            new_fv.value_color = tuple(old_fv.value_color)
    
    # Migrate actions to scope actions
    for old_action in vf_settings.actions:
        new_action = scope.actions.add()
        new_action.name = old_action.name
        new_action.script = old_action.script
    
    # Migrate active alternative index
    scope.active_alternative_index = vf_settings.active_alternative_index
    
    # Clear legacy data after migration
    vf_settings.field_definitions.clear()
    vf_settings.alternatives.clear()
    vf_settings.actions.clear()
    vf_settings.active_alternative_index = 0
    
    print(f"[VF Migration] Migration complete! Created scope with {len(scope.field_definitions)} fields, {len(scope.alternatives)} alternatives, {len(scope.actions)} actions")
    
    return True

classes = (
    FieldDefinition,
    FieldValue,
    Alternative,
    Action,
    Scope,
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
