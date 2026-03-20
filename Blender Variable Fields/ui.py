import bpy


class VF_UL_AlternativesList(bpy.types.UIList):
    """UIList for displaying Alternatives (like shapekeys/vertexgroups)"""
    bl_idname = "VF_UL_alternatives_list"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='PRESET')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='PRESET')


class VIEW3D_PT_VariableFieldsPanel(bpy.types.Panel):
    bl_label = "Variable Fields"
    bl_idname = "VIEW3D_PT_VariableFieldsPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        vf_settings = scene.variable_fields

        if not vf_settings.is_active:
            layout.operator("variable_fields.activate", text="Activate Variable Fields")
            return

        # Alternatives UIList (like shapekeys/vertexgroups)
        row = layout.row()
        row.template_list(
            "VF_UL_alternatives_list", "",
            vf_settings, "alternatives",
            vf_settings, "active_alternative_index",
            rows=3
        )
        
        col = row.column(align=True)
        col.operator("variable_fields.add_alternative", text="", icon='ADD')
        col.operator("variable_fields.remove_alternative", text="", icon='REMOVE')
        col.separator()
        col.operator("variable_fields.move_alternative", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("variable_fields.move_alternative", text="", icon='TRIA_DOWN').direction = 'DOWN'

        layout.separator()
        layout.label(text="Field Settings:")
        if vf_settings.dev_mode:
            layout.operator("variable_fields.add_field", text="Add Field", icon='ADD')
            for i, field in enumerate(vf_settings.field_definitions):
                box = layout.box()
                # Header row with name, move buttons, and remove button
                row = box.row(align=True)
                row.prop(field, "name", text="")
                sub = row.row(align=True)
                sub.scale_x = 0.8
                op = sub.operator("variable_fields.move_field", text="", icon='TRIA_UP')
                op.index = i
                op.direction = 'UP'
                op = sub.operator("variable_fields.move_field", text="", icon='TRIA_DOWN')
                op.index = i
                op.direction = 'DOWN'
                row.operator("variable_fields.remove_field", text="", icon='X').index = i
                # Field properties
                box.prop(field, "type")
                box.prop(field, "data_path")
                box.prop(field, "eval_script", text="Custom Eval")
        else:
            if len(vf_settings.alternatives) > 0:
                alt = vf_settings.alternatives[vf_settings.active_alternative_index]
                for field_val in alt.field_values:
                    # Look up definition
                    field_def = None
                    for fd in vf_settings.field_definitions:
                        if fd.id == field_val.field_id:
                            field_def = fd
                            break
                    if field_def:
                        # Field name next to field data (same row)
                        row = layout.row(align=True)
                        row.label(text=field_def.name)
                        if field_def.type == 'INT':
                            row.prop(field_val, 'value_int', text="")
                        elif field_def.type == 'FLOAT':
                            row.prop(field_val, 'value_float', text="")
                        elif field_def.type == 'STRING':
                            row.prop(field_val, 'value_string', text="")
                        elif field_def.type == 'IMAGE':
                            row.template_ID(field_val, 'value_image', open='image.open')
                        elif field_def.type == 'COLOR':
                            row.prop(field_val, 'value_color', text="")


class VIEW3D_PT_VariableFieldsActionsPanel(bpy.types.Panel):
    bl_label = "Actions"
    bl_idname = "VIEW3D_PT_VariableFieldsActionsPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_parent_id = "VIEW3D_PT_VariableFieldsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.variable_fields.is_active

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields
        
        if vf_settings.dev_mode:
            row = layout.row(align=True)
            row.operator("variable_fields.add_action", text="Add Action", icon='ADD')
            row.operator("variable_fields.load_predefined_action", text="", icon='PRESET')
            for i, action in enumerate(vf_settings.actions):
                box = layout.box()
                # Header row with name, move buttons, and remove button
                row = box.row(align=True)
                row.prop(action, "name", text="")
                sub = row.row(align=True)
                sub.scale_x = 0.8
                op = sub.operator("variable_fields.move_action", text="", icon='TRIA_UP')
                op.index = i
                op.direction = 'UP'
                op = sub.operator("variable_fields.move_action", text="", icon='TRIA_DOWN')
                op.index = i
                op.direction = 'DOWN'
                row.operator("variable_fields.remove_action", text="", icon='X').index = i
                # Script property
                box.prop(action, "script", text="Script")
        else:
            for action in vf_settings.actions:
                layout.operator("variable_fields.run_action", text=action.name).action_name = action.name


class VIEW3D_PT_VariableFieldsGeneralActionsPanel(bpy.types.Panel):
    bl_label = "General Actions"
    bl_idname = "VIEW3D_PT_VariableFieldsGeneralActionsPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_parent_id = "VIEW3D_PT_VariableFieldsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.variable_fields.is_active

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields
        
        # Big Update button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("variable_fields.update_evaluation", text="Update")
        
        layout.prop(vf_settings, "auto_update", text="Auto Update", toggle=True)
        layout.operator("variable_fields.deactivate", text="Deactivate")
        layout.separator()
        layout.prop(vf_settings, "dev_mode", text="Dev Mode", toggle=True)


classes = (
    VF_UL_AlternativesList,
    VIEW3D_PT_VariableFieldsPanel,
    VIEW3D_PT_VariableFieldsActionsPanel,
    VIEW3D_PT_VariableFieldsGeneralActionsPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
