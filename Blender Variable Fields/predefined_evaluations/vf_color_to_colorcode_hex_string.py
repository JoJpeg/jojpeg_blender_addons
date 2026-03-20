"""
Color to Hex String

Converts a COLOR field value to a hex color code string (#RRGGBB or #RRGGBBAA)
and assigns it to the target (useful when target expects a string).
"""

def _overwrite_eval(field_value, target_blender_data_obj):
    """Convert color to hex string and assign."""
    import bpy
    
    if not hasattr(field_value, 'value_color'):
        return
    
    col = field_value.value_color
    
    # Convert linear color to sRGB for proper hex representation
    def linear_to_srgb(c):
        if c <= 0.0031308:
            return c * 12.92
        else:
            return 1.055 * (c ** (1.0 / 2.4)) - 0.055
    
    r = int(max(0, min(255, linear_to_srgb(col[0]) * 255)))
    g = int(max(0, min(255, linear_to_srgb(col[1]) * 255)))
    b = int(max(0, min(255, linear_to_srgb(col[2]) * 255)))
    a = int(max(0, min(255, col[3] * 255)))  # Alpha is typically linear
    
    # Generate hex string
    if a == 255:
        hex_string = f"#{r:02X}{g:02X}{b:02X}"
    else:
        hex_string = f"#{r:02X}{g:02X}{b:02X}{a:02X}"
    
    # Try to assign the hex string to the target
    # This works if target_blender_data_obj is a property that accepts strings
    try:
        # If target is a text object body, font object, etc.
        if hasattr(target_blender_data_obj, 'body'):
            target_blender_data_obj.body = hex_string
        elif isinstance(target_blender_data_obj, str):
            # If we need to set via parent, store for later
            field_value['_computed_hex'] = hex_string
    except Exception as e:
        print(f"[VF] Color to hex error: {e}")
