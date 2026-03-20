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


# Datablock type items for the dropdown
DATABLOCK_TYPE_ITEMS = [
    ('OBJECT', "Object", "Object reference", 'OBJECT_DATA', 0),
    ('MESH', "Mesh", "Mesh data", 'MESH_DATA', 1),
    ('CURVE', "Curve", "Curve data", 'CURVE_DATA', 2),
    ('CAMERA', "Camera", "Camera data", 'CAMERA_DATA', 3),
    ('LIGHT', "Light", "Light data", 'LIGHT_DATA', 4),
    ('MATERIAL', "Material", "Material data", 'MATERIAL', 5),
    ('TEXTURE', "Texture", "Texture data", 'TEXTURE', 6),
    ('ARMATURE', "Armature", "Armature data", 'ARMATURE_DATA', 7),
    ('ACTION', "Action", "Action data", 'ACTION', 8),
    ('COLLECTION', "Collection", "Collection data", 'OUTLINER_COLLECTION', 9),
    ('WORLD', "World", "World data", 'WORLD', 10),
    ('SCENE', "Scene", "Scene reference", 'SCENE_DATA', 11),
    ('NODE_TREE', "Node Tree", "Node tree (Shader, Geometry, Compositor)", 'NODETREE', 12),
    ('GREASE_PENCIL', "Grease Pencil", "Grease Pencil data", 'GREASEPENCIL', 13),
    ('MOVIE_CLIP', "Movie Clip", "Movie clip data", 'FILE_MOVIE', 14),
    ('SOUND', "Sound", "Sound data", 'SOUND', 15),
    ('TEXT', "Text", "Text datablock", 'TEXT', 16),
    ('VOLUME', "Volume", "Volume data", 'VOLUME_DATA', 17),
    ('LATTICE', "Lattice", "Lattice data", 'LATTICE_DATA', 18),
    ('LIGHT_PROBE', "Light Probe", "Light probe data", 'LIGHTPROBE_SPHERE', 19),
    ('CACHE_FILE', "Cache File", "Cache file data", 'FILE', 20),
]


def on_field_value_update(self, context):
    """Callback triggered when any field value changes - runs evaluation if auto_update is enabled."""
    vf_settings = context.scene.variable_fields
    if vf_settings.auto_update:
        bpy.ops.variable_fields.update_evaluation()


class FieldDefinition(bpy.types.PropertyGroup):
    id: StringProperty(name="ID", description="Unique identifier")
    name: StringProperty(name="Name", description="Display name for the field")
    # IMPORTANT: Keep original type order for backwards compatibility!
    # Old order was: INT(0), FLOAT(1), STRING(2), IMAGE(3), COLOR(4)
    # New types must be appended at the end
    type: EnumProperty(
        name="Type",
        items=[
            ('INT', "Integer", "Integer number", 'DRIVER_TRANSFORM', 0),
            ('FLOAT', "Float", "Floating point number", 'DRIVER_DISTANCE', 1),
            ('STRING', "String", "Text string", 'FILE_TEXT', 2),
            ('IMAGE', "Image", "Select or load an image from disk", 'IMAGE_DATA', 3),
            ('COLOR', "Color", "RGBA Color", 'COLOR', 4),
            # New types added below - do not reorder above items!
            ('BOOL', "Boolean", "True/False value", 'CHECKBOX_HLT', 5),
            ('VECTOR', "Vector", "3D Vector (X, Y, Z)", 'ORIENTATION_GLOBAL', 6),
            ('EULER', "Euler", "Euler rotation (X, Y, Z)", 'ORIENTATION_GIMBAL', 7),
            ('QUATERNION', "Quaternion", "Quaternion rotation (W, X, Y, Z)", 'ORIENTATION_QUATERNION', 8),
            ('DATABLOCK', "Data Block", "Reference to a Blender datablock", 'FILE_BLEND', 9),
        ],
        default='FLOAT'
    )
    # Datablock subtype (only used when type is DATABLOCK)
    datablock_type: EnumProperty(
        name="Datablock Type",
        items=DATABLOCK_TYPE_ITEMS,
        default='OBJECT'
    )
    data_path: StringProperty(name="Data Path", description="Full Blender data path")
    default_value: StringProperty(name="Default Value", description="Initial value for new field values")
    eval_script: PointerProperty(name="Evaluation Script", type=bpy.types.Text)
    last_error: StringProperty(name="Last Error", description="Validation error message")

class FieldValue(bpy.types.PropertyGroup):
    field_id: StringProperty(name="Field ID")
    value_int: IntProperty(name="Integer Value", update=on_field_value_update)
    value_float: FloatProperty(name="Float Value", update=on_field_value_update)
    value_bool: BoolProperty(name="Boolean Value", update=on_field_value_update)
    value_string: StringProperty(name="String Value", update=on_field_value_update)
    value_vector: FloatVectorProperty(name="Vector Value", size=3, subtype='XYZ', update=on_field_value_update)
    value_euler: FloatVectorProperty(name="Euler Value", size=3, subtype='EULER', update=on_field_value_update)
    value_quaternion: FloatVectorProperty(name="Quaternion Value", size=4, subtype='QUATERNION', update=on_field_value_update)
    value_color: FloatVectorProperty(name="Color Value", size=4, subtype='COLOR', min=0.0, max=1.0, update=on_field_value_update)
    value_image: PointerProperty(name="Image Value", type=bpy.types.Image, update=on_field_value_update)
    # Datablock pointers - one for each supported type
    value_object: PointerProperty(name="Object", type=bpy.types.Object, update=on_field_value_update)
    value_mesh: PointerProperty(name="Mesh", type=bpy.types.Mesh, update=on_field_value_update)
    value_curve: PointerProperty(name="Curve", type=bpy.types.Curve, update=on_field_value_update)
    value_camera: PointerProperty(name="Camera", type=bpy.types.Camera, update=on_field_value_update)
    value_light: PointerProperty(name="Light", type=bpy.types.Light, update=on_field_value_update)
    value_material: PointerProperty(name="Material", type=bpy.types.Material, update=on_field_value_update)
    value_texture: PointerProperty(name="Texture", type=bpy.types.Texture, update=on_field_value_update)
    value_armature: PointerProperty(name="Armature", type=bpy.types.Armature, update=on_field_value_update)
    value_action: PointerProperty(name="Action", type=bpy.types.Action, update=on_field_value_update)
    value_collection: PointerProperty(name="Collection", type=bpy.types.Collection, update=on_field_value_update)
    value_world: PointerProperty(name="World", type=bpy.types.World, update=on_field_value_update)
    value_scene: PointerProperty(name="Scene", type=bpy.types.Scene, update=on_field_value_update)
    value_node_tree: PointerProperty(name="Node Tree", type=bpy.types.NodeTree, update=on_field_value_update)
    value_grease_pencil: PointerProperty(name="Grease Pencil", type=bpy.types.GreasePencil, update=on_field_value_update)
    value_movie_clip: PointerProperty(name="Movie Clip", type=bpy.types.MovieClip, update=on_field_value_update)
    value_sound: PointerProperty(name="Sound", type=bpy.types.Sound, update=on_field_value_update)
    value_text: PointerProperty(name="Text", type=bpy.types.Text, update=on_field_value_update)
    value_volume: PointerProperty(name="Volume", type=bpy.types.Volume, update=on_field_value_update)
    value_lattice: PointerProperty(name="Lattice", type=bpy.types.Lattice, update=on_field_value_update)
    value_light_probe: PointerProperty(name="Light Probe", type=bpy.types.LightProbe, update=on_field_value_update)
    value_cache_file: PointerProperty(name="Cache File", type=bpy.types.CacheFile, update=on_field_value_update)
    
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
    # Check if we have legacy data and no scopes
    has_legacy_data = (
        len(vf_settings.field_definitions) > 0 or 
        len(vf_settings.alternatives) > 0 or 
        len(vf_settings.actions) > 0
    )
    
    if not has_legacy_data or len(vf_settings.scopes) > 0:
        return False
    
    print(f"[VF] Migrating legacy data to scopes...")
    
    # Create default scope from legacy data
    scope = vf_settings.scopes.add()
    scope.name = "Scope"
    
    # Migrate field definitions
    for old_field in vf_settings.field_definitions:
        new_field = scope.field_definitions.add()
        new_field.id = old_field.id
        new_field.name = old_field.name
        new_field.type = old_field.type
        # Copy datablock_type if it exists (for newer files being migrated)
        if hasattr(old_field, 'datablock_type'):
            new_field.datablock_type = old_field.datablock_type
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
            # Copy all value types (properties default to their zero values if not present)
            new_fv.value_int = old_fv.value_int
            new_fv.value_float = old_fv.value_float
            new_fv.value_bool = getattr(old_fv, 'value_bool', False)
            new_fv.value_string = old_fv.value_string
            new_fv.value_vector = tuple(getattr(old_fv, 'value_vector', (0, 0, 0)))
            new_fv.value_euler = tuple(getattr(old_fv, 'value_euler', (0, 0, 0)))
            new_fv.value_quaternion = tuple(getattr(old_fv, 'value_quaternion', (1, 0, 0, 0)))
            new_fv.value_color = tuple(old_fv.value_color)
            new_fv.value_image = old_fv.value_image
            # Copy datablock references if they exist
            for db_prop in ['value_object', 'value_mesh', 'value_curve', 'value_camera',
                           'value_light', 'value_material', 'value_texture', 'value_armature',
                           'value_action', 'value_collection', 'value_world', 'value_scene',
                           'value_node_tree', 'value_grease_pencil', 'value_movie_clip',
                           'value_sound', 'value_text', 'value_volume', 'value_lattice',
                           'value_light_probe', 'value_cache_file']:
                if hasattr(old_fv, db_prop):
                    setattr(new_fv, db_prop, getattr(old_fv, db_prop))
    
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
    
    print(f"[VF] Migration complete: {len(scope.field_definitions)} fields, {len(scope.alternatives)} alternatives, {len(scope.actions)} actions")
    
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
