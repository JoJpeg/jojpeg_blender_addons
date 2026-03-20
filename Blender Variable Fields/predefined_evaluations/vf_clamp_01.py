"""
Clamp 0-1

Clamps numeric values to the range 0.0 to 1.0.
Works with INT, FLOAT, VECTOR, EULER, QUATERNION, and COLOR types.
"""

def _overwrite_eval(field_value, target_blender_data_obj):
    """Clamp value(s) to 0-1 range before assignment."""
    import bpy
    
    def clamp(val):
        return max(0.0, min(1.0, val))
    
    # Get the owner and property name from the data path
    # We need to find what property we're setting
    val = None
    
    # Check which value type we have
    if hasattr(field_value, 'value_float') and field_value.value_float != 0.0:
        val = clamp(field_value.value_float)
    elif hasattr(field_value, 'value_int') and field_value.value_int != 0:
        val = clamp(float(field_value.value_int))
    elif hasattr(field_value, 'value_vector'):
        vec = field_value.value_vector
        if vec[0] != 0.0 or vec[1] != 0.0 or vec[2] != 0.0:
            val = (clamp(vec[0]), clamp(vec[1]), clamp(vec[2]))
    elif hasattr(field_value, 'value_euler'):
        euler = field_value.value_euler
        if euler[0] != 0.0 or euler[1] != 0.0 or euler[2] != 0.0:
            val = (clamp(euler[0]), clamp(euler[1]), clamp(euler[2]))
    elif hasattr(field_value, 'value_quaternion'):
        quat = field_value.value_quaternion
        val = (clamp(quat[0]), clamp(quat[1]), clamp(quat[2]), clamp(quat[3]))
    elif hasattr(field_value, 'value_color'):
        col = field_value.value_color
        val = (clamp(col[0]), clamp(col[1]), clamp(col[2]), clamp(col[3]))
    
    if val is not None:
        # Try to set as attribute of the target object's parent
        # This requires the caller to provide proper context
        pass
