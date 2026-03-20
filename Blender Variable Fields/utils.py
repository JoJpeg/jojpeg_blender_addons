import bpy
import traceback


# Mapping from datablock type enum to field_value property name
DATABLOCK_VALUE_MAP = {
    'OBJECT': 'value_object',
    'MESH': 'value_mesh',
    'CURVE': 'value_curve',
    'CAMERA': 'value_camera',
    'LIGHT': 'value_light',
    'MATERIAL': 'value_material',
    'TEXTURE': 'value_texture',
    'ARMATURE': 'value_armature',
    'ACTION': 'value_action',
    'COLLECTION': 'value_collection',
    'WORLD': 'value_world',
    'SCENE': 'value_scene',
    'NODE_TREE': 'value_node_tree',
    'GREASE_PENCIL': 'value_grease_pencil',
    'MOVIE_CLIP': 'value_movie_clip',
    'SOUND': 'value_sound',
    'TEXT': 'value_text',
    'VOLUME': 'value_volume',
    'LATTICE': 'value_lattice',
    'LIGHT_PROBE': 'value_light_probe',
    'CACHE_FILE': 'value_cache_file',
}


def get_field_value(field_def, field_value):
    """
    Get the typed value from field_value based on field_def.type.
    Returns the appropriate value for assignment.
    """
    field_type = field_def.type
    
    if field_type == 'INT':
        return field_value.value_int
    elif field_type == 'FLOAT':
        return field_value.value_float
    elif field_type == 'BOOL':
        return field_value.value_bool
    elif field_type == 'STRING':
        return field_value.value_string
    elif field_type == 'VECTOR':
        return tuple(field_value.value_vector)
    elif field_type == 'EULER':
        return tuple(field_value.value_euler)
    elif field_type == 'QUATERNION':
        return tuple(field_value.value_quaternion)
    elif field_type == 'COLOR':
        return tuple(field_value.value_color)
    elif field_type == 'IMAGE':
        return field_value.value_image
    elif field_type == 'DATABLOCK':
        prop_name = DATABLOCK_VALUE_MAP.get(field_def.datablock_type)
        if prop_name:
            return getattr(field_value, prop_name, None)
    return None


def convert_value_for_target(value, field_type, target_type_hint=None):
    """
    Auto-convert field value to match target type if possible.
    Handles: int<->float, int/float->vec3/rot, string->number
    """
    if value is None:
        return None
    
    # int/float -> vec3 (broadcast single value to all components)
    # Check this BEFORE simple int<->float conversion
    if field_type in ('INT', 'FLOAT') and target_type_hint in ('vector', 'euler'):
        v = float(value)
        return (v, v, v)
    
    # int/float -> quaternion (set as W with identity rotation)
    if field_type in ('INT', 'FLOAT') and target_type_hint == 'quaternion':
        return (float(value), 0.0, 0.0, 0.0)
    
    # int <-> float conversion
    if field_type == 'INT' and isinstance(value, int):
        return float(value) if target_type_hint == 'float' else value
    
    if field_type == 'FLOAT' and isinstance(value, float):
        return int(value) if target_type_hint == 'int' else value
    
    # string -> number conversion
    if field_type == 'STRING' and isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                pass
    
    return value


def resolve_data_path(data_path):
    """
    Resolve a data path to (owner, property_name, is_indexed).
    Handles both dot notation (obj.location) and bracket notation (obj["key"]).
    Returns (owner, prop_name, is_indexed) where is_indexed indicates bracket access.
    """
    import re
    
    if not data_path:
        return None, None, False
    
    # Check if path ends with bracket notation ["..."]
    bracket_match = re.search(r'^(.+)\["([^"]+)"\]$', data_path)
    
    if bracket_match:
        # Bracket notation: bpy.data.objects["Cube"].modifiers["GeometryNodes"]["Socket_2"]
        owner_path = bracket_match.group(1)
        key = bracket_match.group(2)
        try:
            owner = eval(owner_path, {"bpy": bpy})
            return owner, key, True
        except Exception as e:
            print(f"[VF] Failed to resolve bracket path '{owner_path}': {e}")
            return None, None, False
    else:
        # Dot notation: bpy.data.objects["Cube"].location
        parts = data_path.split('.')
        if len(parts) < 2:
            return None, None, False
        
        owner_path = '.'.join(parts[:-1])
        prop_name = parts[-1]
        
        try:
            owner = eval(owner_path, {"bpy": bpy})
            return owner, prop_name, False
        except Exception as e:
            print(f"[VF] Failed to resolve dot path '{owner_path}': {e}")
            return None, None, False


def set_value_at_path(owner, prop_name, value, is_indexed):
    """Set a value using either setattr or indexed access."""
    if is_indexed:
        owner[prop_name] = value
    else:
        setattr(owner, prop_name, value)


def get_value_at_path(owner, prop_name, is_indexed):
    """Get a value using either getattr or indexed access."""
    if is_indexed:
        return owner[prop_name]
    else:
        return getattr(owner, prop_name)


def trigger_updates_for_path(data_path, context):
    """
    Trigger necessary updates after modifying data at a path.
    Handles modifiers, shape keys, materials, and other data that needs refresh.
    """
    import re
    
    # Check if path targets an object's modifier
    obj_modifier_match = re.search(r'bpy\.data\.objects\["([^"]+)"\]\.modifiers\[', data_path)
    if obj_modifier_match:
        obj_name = obj_modifier_match.group(1)
        obj = bpy.data.objects.get(obj_name)
        if obj:
            # Tag object for update
            obj.update_tag()
            # Also tag the object's data if it exists
            if obj.data:
                obj.data.update_tag()
    
    # Check if path targets object data directly (mesh, curve, etc.)
    obj_data_match = re.search(r'bpy\.data\.objects\["([^"]+)"\]', data_path)
    if obj_data_match:
        obj_name = obj_data_match.group(1)
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.update_tag()
    
    # Update the depsgraph to process changes
    if context and hasattr(context, 'view_layer'):
        context.view_layer.update()


def evaluate_field(field_def, field_value, context):
    owner, prop_name, is_indexed = resolve_data_path(field_def.data_path)
    
    if owner is None:
        err_msg = f"[VF] Invalid data_path: {field_def.data_path}"
        print(err_msg)
        field_def.last_error = err_msg
        return
    
    # Check if property exists
    if is_indexed:
        try:
            target_blender_data_obj = owner[prop_name]
        except (KeyError, TypeError) as e:
            err_msg = f"[VF] Key '{prop_name}' not found in {field_def.data_path}"
            print(err_msg)
            field_def.last_error = err_msg
            return
    else:
        if not hasattr(owner, prop_name):
            err_msg = f"[VF] Property '{prop_name}' not found at {field_def.data_path}"
            print(err_msg)
            field_def.last_error = err_msg
            return
        target_blender_data_obj = getattr(owner, prop_name)
    
    # Clear any previous error
    field_def.last_error = ""
    
    script_locals = {
        'field_value': field_value,
        'field_def': field_def,
        'target_blender_data_obj': target_blender_data_obj,
        'owner': owner,
        'prop_name': prop_name,
        'is_indexed': is_indexed,
        'bpy': bpy,
        'context': context,
    }
    
    has_pre = False
    has_post = False
    has_overwrite = False
    
    if field_def.eval_script:
        try:
            exec(field_def.eval_script.as_string(), globals(), script_locals)
            has_pre = '_pre' in script_locals
            has_post = '_post' in script_locals
            has_overwrite = '_overwrite_eval' in script_locals
        except Exception as e:
            field_def.last_error = f"Script Error: {str(e)}"
            return
            
    if has_overwrite:
        try:
            script_locals['_overwrite_eval'](field_value, target_blender_data_obj)
        except Exception as e:
            field_def.last_error = f"Overwrite Eval Error: {traceback.format_exc()}"
        return
        
    if has_pre:
        try:
            script_locals['_pre'](field_value, target_blender_data_obj)
        except Exception as e:
            field_def.last_error = f"Pre Eval Error: {str(e)}"
            
    # Default data assignment - get typed value
    try:
        val = get_field_value(field_def, field_value)
        
        # Try to detect target type for auto-conversion
        target_type_hint = None
        try:
            if hasattr(target_blender_data_obj, '__len__'):
                if len(target_blender_data_obj) == 3:
                    target_type_hint = 'vector'
                elif len(target_blender_data_obj) == 4:
                    target_type_hint = 'quaternion'
            elif isinstance(target_blender_data_obj, float):
                target_type_hint = 'float'
            elif isinstance(target_blender_data_obj, int):
                target_type_hint = 'int'
        except:
            pass
        
        # Apply auto-conversion if needed
        if val is not None and target_type_hint:
            val = convert_value_for_target(val, field_def.type, target_type_hint)
            
        if val is not None:
            set_value_at_path(owner, prop_name, val, is_indexed)
            # Trigger updates for modifiers, drivers, etc.
            trigger_updates_for_path(field_def.data_path, context)
        else:
            err_msg = f"[VF] No value to assign for field '{field_def.name}' at {field_def.data_path}"
            print(err_msg)
            field_def.last_error = err_msg
    except Exception as e:
        err_msg = f"[VF] Assignment failed for '{field_def.name}': {str(e)} (field type: {field_def.type}, target: {field_def.data_path})"
        print(err_msg)
        field_def.last_error = err_msg
        
    if has_post:
        try:
            script_locals['_post'](field_value, get_value_at_path(owner, prop_name, is_indexed))
        except Exception as e:
            field_def.last_error = f"Post Eval Error: {str(e)}"
