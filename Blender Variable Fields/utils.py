import bpy
import traceback

def resolve_data_path(data_path):
    parts = data_path.split('.')
    if len(parts) < 2:
        return None, None
    
    owner_path = '.'.join(parts[:-1])
    prop_name = parts[-1]
    
    try:
        owner = eval(owner_path, {"bpy": bpy})
        return owner, prop_name
    except Exception as e:
        return None, None

def evaluate_field(field_def, field_value, context):
    owner, prop_name = resolve_data_path(field_def.data_path)
    
    if not owner or not hasattr(owner, prop_name):
        field_def.last_error = f"Invalid data_path or property: {field_def.data_path}"
        return
        
    target_blender_data_obj = getattr(owner, prop_name)
    
    script_locals = {
        'field_value': field_value,
        'target_blender_data_obj': target_blender_data_obj,
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
            
    # Default data assignment
    try:
        val = None
        if field_def.type == 'INT':
            val = field_value.value_int
        elif field_def.type == 'FLOAT':
            val = field_value.value_float
        elif field_def.type == 'STRING':
            val = field_value.value_string
        elif field_def.type == 'COLOR':
            val = field_value.value_color
        elif field_def.type == 'IMAGE':
            val = field_value.value_image
            
        if val is not None:
            setattr(owner, prop_name, val)
    except Exception as e:
        field_def.last_error = f"Assignment Error: {str(e)}"
        
    if has_post:
        try:
            script_locals['_post'](field_value, getattr(owner, prop_name))
        except Exception as e:
            field_def.last_error = f"Post Eval Error: {str(e)}"
