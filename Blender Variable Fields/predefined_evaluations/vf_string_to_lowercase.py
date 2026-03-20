"""
String to Lowercase

Converts string field values to lowercase before assignment.
"""

def _pre(field_value, target_blender_data_obj):
    """Convert string to lowercase before assignment."""
    if hasattr(field_value, 'value_string'):
        # Modify the string value in place (lowercase)
        field_value['value_string'] = field_value.value_string.lower()
