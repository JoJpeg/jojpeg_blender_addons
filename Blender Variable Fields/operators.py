import bpy
import os
from . import utils

# Path to predefined action scripts
PREDEFINED_ACTIONS_DIR = os.path.join(os.path.dirname(__file__), "predefined_actions")


def get_predefined_actions():
    """Load predefined action scripts from the predefined_actions folder."""
    actions = {}
    if os.path.isdir(PREDEFINED_ACTIONS_DIR):
        for filename in os.listdir(PREDEFINED_ACTIONS_DIR):
            if filename.endswith('.py') and not filename.startswith('__'):
                filepath = os.path.join(PREDEFINED_ACTIONS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    # Use vf_action_ prefix for internal text blocks
                    text_name = f"vf_action_{filename}"
                    actions[text_name] = {
                        'content': f.read(),
                        'filepath': filepath,
                        'filename': filename,
                    }
    return actions


def get_predefined_action_items(self, context):
    """Generate enum items for predefined actions dropdown."""
    items = []
    actions = get_predefined_actions()
    for text_name, data in sorted(actions.items()):
        # Create human-readable name from filename
        display_name = data['filename'].replace('_', ' ').replace('.py', '').title()
        items.append((text_name, display_name, f"Load {display_name} script"))
    if not items:
        items.append(('NONE', "No predefined actions", ""))
    return items


class VF_LoadPredefinedActionOperator(bpy.types.Operator):
    bl_idname = "variable_fields.load_predefined_action"
    bl_label = "Load Predefined Action"
    bl_description = "Load a predefined action script into the scene"
    
    action_id: bpy.props.EnumProperty(
        name="Predefined Action",
        description="Select a predefined action to load",
        items=get_predefined_action_items,
    )

    def execute(self, context):
        if self.action_id == 'NONE':
            self.report({'WARNING'}, "No predefined actions available")
            return {'CANCELLED'}
        
        actions = get_predefined_actions()
        if self.action_id not in actions:
            self.report({'ERROR'}, f"Action '{self.action_id}' not found")
            return {'CANCELLED'}
        
        # Load the script into Blender's text blocks
        if self.action_id not in bpy.data.texts:
            text = bpy.data.texts.new(self.action_id)
            text.write(actions[self.action_id]['content'])
            self.report({'INFO'}, f"Loaded '{self.action_id}'")
        else:
            self.report({'INFO'}, f"'{self.action_id}' already loaded")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "action_id", text="")


class VF_ActivateOperator(bpy.types.Operator):
    bl_idname = "variable_fields.activate"
    bl_label = "Activate Variable Fields"
    bl_description = "Initializes addon and creates default alternative"

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        vf_settings.is_active = True
        
        # Create default alternative if it doesn't exist
        if len(vf_settings.alternatives) == 0:
            alt = vf_settings.alternatives.add()
            alt.name = "Default"
            
        # Spawn custom_evaluation_template.py
        if "custom_evaluation_template.py" not in bpy.data.texts:
            text = bpy.data.texts.new("custom_evaluation_template.py")
            text.write(
'''"""
Custom Evaluation Script Template

This script lets you customize how field values are applied to Blender data.
The functions receive:
  - field_value: The FieldValue object with typed properties (value_int, value_float, 
                 value_string, value_color, value_datablock)
  - target_blender_data_obj: The resolved Blender data at the field's data_path
"""

def _pre(field_value, target_blender_data_obj):
    """Runs BEFORE default data assignment."""
    # Example: Print the current value before changing it
    # print(f"Current value: {target_blender_data_obj}")
    pass

def _post(field_value, target_blender_data_obj):
    """Runs AFTER default data assignment."""
    # Example: Log when a value was changed
    # print(f"Value was updated to: {target_blender_data_obj}")
    pass

def _overwrite_eval(field_value, target_blender_data_obj):
    """
    Runs INSTEAD OF default data assignment logic.
    Use this when you need full control over how data is set.
    
    Example: Setting object location from a string field like "1.0, 2.0, 3.0"
    """
    import bpy
    
    # Example 1: Parse a comma-separated string into a location vector
    # if hasattr(target_blender_data_obj, '__iter__') and len(target_blender_data_obj) == 3:
    #     coords = [float(x.strip()) for x in field_value.value_string.split(',')]
    #     target_blender_data_obj[0] = coords[0]
    #     target_blender_data_obj[1] = coords[1]
    #     target_blender_data_obj[2] = coords[2]
    
    # Example 2: Set text content from string field
    # if hasattr(target_blender_data_obj, 'body'):
    #     target_blender_data_obj.body = field_value.value_string
    
    # Example 3: Set material color from color field  
    # if hasattr(target_blender_data_obj, 'default_value'):
    #     target_blender_data_obj.default_value = field_value.value_color
    
    pass
''')
        
        return {'FINISHED'}

class VF_DeactivateOperator(bpy.types.Operator):
    bl_idname = "variable_fields.deactivate"
    bl_label = "Deactivate Variable Fields"

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        vf_settings.is_active = False
        return {'FINISHED'}

class VF_AddAlternativeOperator(bpy.types.Operator):
    bl_idname = "variable_fields.add_alternative"
    bl_label = "Add Alternative"

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        alt = vf_settings.alternatives.add()
        alt.name = f"Alternative {len(vf_settings.alternatives)}"
        
        # Populate with existing field definitions
        for field_def in vf_settings.field_definitions:
            fv = alt.field_values.add()
            fv.field_id = field_def.id
            if field_def.default_value:
                # Need to convert string to typed value if possible
                pass
                
        vf_settings.active_alternative_index = len(vf_settings.alternatives) - 1
        return {'FINISHED'}


class VF_RemoveAlternativeOperator(bpy.types.Operator):
    bl_idname = "variable_fields.remove_alternative"
    bl_label = "Remove Alternative"
    bl_description = "Remove the selected alternative"

    @classmethod
    def poll(cls, context):
        vf_settings = context.scene.variable_fields
        # Don't allow removing the Default alternative (index 0)
        if len(vf_settings.alternatives) <= 1:
            return False
        if vf_settings.active_alternative_index == 0:
            return False
        return True

    def execute(self, context):
        vf_settings = context.scene.variable_fields
        index = vf_settings.active_alternative_index
        vf_settings.alternatives.remove(index)
        
        # Adjust active index
        if vf_settings.active_alternative_index >= len(vf_settings.alternatives):
            vf_settings.active_alternative_index = len(vf_settings.alternatives) - 1
        
        return {'FINISHED'}


class VF_MoveAlternativeOperator(bpy.types.Operator):
    bl_idname = "variable_fields.move_alternative"
    bl_label = "Move Alternative"
    bl_description = "Move the selected alternative up or down"
    
    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
        ]
    )

    @classmethod
    def poll(cls, context):
        vf_settings = context.scene.variable_fields
        return len(vf_settings.alternatives) > 1

    def execute(self, context):
        vf_settings = context.scene.variable_fields
        index = vf_settings.active_alternative_index
        
        if self.direction == 'UP' and index > 0:
            vf_settings.alternatives.move(index, index - 1)
            vf_settings.active_alternative_index -= 1
        elif self.direction == 'DOWN' and index < len(vf_settings.alternatives) - 1:
            vf_settings.alternatives.move(index, index + 1)
            vf_settings.active_alternative_index += 1
            
        return {'FINISHED'}

class VF_AddFieldOperator(bpy.types.Operator):
    bl_idname = "variable_fields.add_field"
    bl_label = "Add Field"

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        field = vf_settings.field_definitions.add()
        import uuid
        field.id = str(uuid.uuid4())
        field.name = f"Field {len(vf_settings.field_definitions)}"
        
        # Add to existing alternatives
        for alt in vf_settings.alternatives:
            fv = alt.field_values.add()
            fv.field_id = field.id
            
        return {'FINISHED'}


class VF_RemoveFieldOperator(bpy.types.Operator):
    bl_idname = "variable_fields.remove_field"
    bl_label = "Remove Field"
    bl_description = "Remove this field definition"
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        vf_settings = context.scene.variable_fields
        
        if self.index < 0 or self.index >= len(vf_settings.field_definitions):
            return {'CANCELLED'}
        
        field_id = vf_settings.field_definitions[self.index].id
        
        # Remove field definition
        vf_settings.field_definitions.remove(self.index)
        
        # Remove corresponding field values from all alternatives
        for alt in vf_settings.alternatives:
            for i, fv in enumerate(alt.field_values):
                if fv.field_id == field_id:
                    alt.field_values.remove(i)
                    break
        
        return {'FINISHED'}


class VF_MoveFieldOperator(bpy.types.Operator):
    bl_idname = "variable_fields.move_field"
    bl_label = "Move Field"
    bl_description = "Move this field up or down"
    
    index: bpy.props.IntProperty()
    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
        ]
    )

    def execute(self, context):
        vf_settings = context.scene.variable_fields
        fields = vf_settings.field_definitions
        
        if self.index < 0 or self.index >= len(fields):
            return {'CANCELLED'}
        
        new_index = self.index - 1 if self.direction == 'UP' else self.index + 1
        
        if new_index < 0 or new_index >= len(fields):
            return {'CANCELLED'}
        
        fields.move(self.index, new_index)
        
        # Also reorder field_values in all alternatives to keep them in sync
        for alt in vf_settings.alternatives:
            if self.index < len(alt.field_values) and new_index < len(alt.field_values):
                alt.field_values.move(self.index, new_index)
        
        return {'FINISHED'}


class VF_AddActionOperator(bpy.types.Operator):
    bl_idname = "variable_fields.add_action"
    bl_label = "Add Action"

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        action = vf_settings.actions.add()
        action.name = f"Action {len(vf_settings.actions)}"
        return {'FINISHED'}


class VF_RemoveActionOperator(bpy.types.Operator):
    bl_idname = "variable_fields.remove_action"
    bl_label = "Remove Action"
    bl_description = "Remove this action"
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        vf_settings = context.scene.variable_fields
        
        if self.index < 0 or self.index >= len(vf_settings.actions):
            return {'CANCELLED'}
        
        vf_settings.actions.remove(self.index)
        return {'FINISHED'}


class VF_MoveActionOperator(bpy.types.Operator):
    bl_idname = "variable_fields.move_action"
    bl_label = "Move Action"
    bl_description = "Move this action up or down"
    
    index: bpy.props.IntProperty()
    direction: bpy.props.EnumProperty(
        items=[
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
        ]
    )

    def execute(self, context):
        vf_settings = context.scene.variable_fields
        actions = vf_settings.actions
        
        if self.index < 0 or self.index >= len(actions):
            return {'CANCELLED'}
        
        new_index = self.index - 1 if self.direction == 'UP' else self.index + 1
        
        if new_index < 0 or new_index >= len(actions):
            return {'CANCELLED'}
        
        actions.move(self.index, new_index)
        return {'FINISHED'}


class VF_RunActionOperator(bpy.types.Operator):
    bl_idname = "variable_fields.run_action"
    bl_label = "Run Action"
    
    action_name: bpy.props.StringProperty()

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        
        for action in vf_settings.actions:
            if action.name == self.action_name and action.script:
                exec(action.script.as_string(), globals(), locals())
                break
                
        return {'FINISHED'}

class VF_UpdateEvaluationOperator(bpy.types.Operator):
    bl_idname = "variable_fields.update_evaluation"
    bl_label = "Update Evaluation"

    def execute(self, context):
        scene = context.scene
        vf_settings = scene.variable_fields
        
        if len(vf_settings.alternatives) == 0:
            return {'FINISHED'}
            
        alt = vf_settings.alternatives[vf_settings.active_alternative_index]
        
        for field_def in vf_settings.field_definitions:
            fv = None
            for val in alt.field_values:
                if val.field_id == field_def.id:
                    fv = val
                    break
                    
            if not fv:
                continue
                
            utils.evaluate_field(field_def, fv, context)
            
        return {'FINISHED'}

classes = (
    VF_ActivateOperator,
    VF_DeactivateOperator,
    VF_LoadPredefinedActionOperator,
    VF_AddAlternativeOperator,
    VF_RemoveAlternativeOperator,
    VF_MoveAlternativeOperator,
    VF_AddFieldOperator,
    VF_RemoveFieldOperator,
    VF_MoveFieldOperator,
    VF_AddActionOperator,
    VF_RemoveActionOperator,
    VF_MoveActionOperator,
    VF_RunActionOperator,
    VF_UpdateEvaluationOperator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
