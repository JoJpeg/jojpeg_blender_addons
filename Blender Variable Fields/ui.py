import bpy
from .properties import get_active_scope


class VF_UL_ScopesList(bpy.types.UIList):
    """UIList for displaying Scopes"""
    bl_idname = "VF_UL_scopes_list"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='OUTLINER_COLLECTION')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION')


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
        
        # Ensure at least one scope exists (safety fallback)
        if len(vf_settings.scopes) == 0:
            scope = vf_settings.scopes.add()
            scope.name = "Scope"
            alt = scope.alternatives.add()
            alt.name = "Default"

        # Just show a summary when activated - content is in sub-panels
        scope = get_active_scope(vf_settings)
        if scope:
            layout.label(text=f"Active Scope: {scope.name}")
        else:
            layout.label(text="No scope selected", icon='INFO')


class VIEW3D_PT_VariableFieldsScopesPanel(bpy.types.Panel):
    bl_label = "Scopes"
    bl_idname = "VIEW3D_PT_VariableFieldsScopesPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_parent_id = "VIEW3D_PT_VariableFieldsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        vf_settings = context.scene.variable_fields
        if not vf_settings.is_active:
            return False
        # Show if more than 1 scope OR in dev_mode (to allow adding scopes)
        return len(vf_settings.scopes) > 1 or vf_settings.dev_mode

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields

        row = layout.row()
        row.template_list(
            "VF_UL_scopes_list", "",
            vf_settings, "scopes",
            vf_settings, "active_scope_index",
            rows=2
        )
        
        col = row.column(align=True)
        col.operator("variable_fields.add_scope", text="", icon='ADD')
        col.operator("variable_fields.remove_scope", text="", icon='REMOVE')
        col.separator()
        col.operator("variable_fields.move_scope", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("variable_fields.move_scope", text="", icon='TRIA_DOWN').direction = 'DOWN'


class VIEW3D_PT_VariableFieldsAlternativesPanel(bpy.types.Panel):
    bl_label = "Alternatives"
    bl_idname = "VIEW3D_PT_VariableFieldsAlternativesPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_parent_id = "VIEW3D_PT_VariableFieldsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        vf_settings = context.scene.variable_fields
        return vf_settings.is_active and get_active_scope(vf_settings) is not None

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields
        scope = get_active_scope(vf_settings)
        
        if not scope:
            return

        row = layout.row()
        row.template_list(
            "VF_UL_alternatives_list", "",
            scope, "alternatives",
            scope, "active_alternative_index",
            rows=3
        )
        
        col = row.column(align=True)
        col.operator("variable_fields.add_alternative", text="", icon='ADD')
        col.operator("variable_fields.remove_alternative", text="", icon='REMOVE')
        col.separator()
        col.operator("variable_fields.move_alternative", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("variable_fields.move_alternative", text="", icon='TRIA_DOWN').direction = 'DOWN'


class VIEW3D_PT_VariableFieldsFieldSettingsPanel(bpy.types.Panel):
    bl_label = "Field Settings"
    bl_idname = "VIEW3D_PT_VariableFieldsFieldSettingsPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_parent_id = "VIEW3D_PT_VariableFieldsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        vf_settings = context.scene.variable_fields
        if not vf_settings.is_active:
            return False
        scope = get_active_scope(vf_settings)
        if not scope:
            return False
        # Show if there are fields OR in dev_mode (to allow adding fields)
        return len(scope.field_definitions) > 0 or vf_settings.dev_mode

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields
        scope = get_active_scope(vf_settings)
        
        if not scope:
            return

        if vf_settings.dev_mode:
            layout.operator("variable_fields.add_field", text="Add Field", icon='ADD')
            for i, field in enumerate(scope.field_definitions):
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
                # Show datablock type selector when type is DATABLOCK
                if field.type == 'DATABLOCK':
                    box.prop(field, "datablock_type")
                box.prop(field, "data_path")
                # Evaluation script with load predefined button
                row = box.row(align=True)
                row.prop(field, "eval_script", text="Custom Eval")
                op = row.operator("variable_fields.load_predefined_evaluation", text="", icon='PRESET')
                op.field_index = i
        else:
            if len(scope.alternatives) > 0:
                alt = scope.alternatives[scope.active_alternative_index]
                for field_val in alt.field_values:
                    # Look up definition
                    field_def = None
                    for fd in scope.field_definitions:
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
                        elif field_def.type == 'BOOL':
                            row.prop(field_val, 'value_bool', text="")
                        elif field_def.type == 'STRING':
                            row.prop(field_val, 'value_string', text="")
                        elif field_def.type == 'VECTOR':
                            row.prop(field_val, 'value_vector', text="")
                        elif field_def.type == 'EULER':
                            row.prop(field_val, 'value_euler', text="")
                        elif field_def.type == 'QUATERNION':
                            row.prop(field_val, 'value_quaternion', text="")
                        elif field_def.type == 'COLOR':
                            row.prop(field_val, 'value_color', text="")
                        elif field_def.type == 'IMAGE':
                            row.template_ID(field_val, 'value_image', open='image.open')
                        elif field_def.type == 'DATABLOCK':
                            # Show appropriate datablock picker based on datablock_type
                            db_type = field_def.datablock_type
                            if db_type == 'OBJECT':
                                row.prop_search(field_val, 'value_object', context.scene, 'objects', text="")
                            elif db_type == 'MESH':
                                row.prop_search(field_val, 'value_mesh', bpy.data, 'meshes', text="")
                            elif db_type == 'CURVE':
                                row.prop_search(field_val, 'value_curve', bpy.data, 'curves', text="")
                            elif db_type == 'CAMERA':
                                row.prop_search(field_val, 'value_camera', bpy.data, 'cameras', text="")
                            elif db_type == 'LIGHT':
                                row.prop_search(field_val, 'value_light', bpy.data, 'lights', text="")
                            elif db_type == 'MATERIAL':
                                row.prop_search(field_val, 'value_material', bpy.data, 'materials', text="")
                            elif db_type == 'TEXTURE':
                                row.prop_search(field_val, 'value_texture', bpy.data, 'textures', text="")
                            elif db_type == 'ARMATURE':
                                row.prop_search(field_val, 'value_armature', bpy.data, 'armatures', text="")
                            elif db_type == 'ACTION':
                                row.prop_search(field_val, 'value_action', bpy.data, 'actions', text="")
                            elif db_type == 'COLLECTION':
                                row.prop_search(field_val, 'value_collection', bpy.data, 'collections', text="")
                            elif db_type == 'WORLD':
                                row.prop_search(field_val, 'value_world', bpy.data, 'worlds', text="")
                            elif db_type == 'SCENE':
                                row.prop_search(field_val, 'value_scene', bpy.data, 'scenes', text="")
                            elif db_type == 'NODE_TREE':
                                row.prop_search(field_val, 'value_node_tree', bpy.data, 'node_groups', text="")
                            elif db_type == 'GREASE_PENCIL':
                                row.prop_search(field_val, 'value_grease_pencil', bpy.data, 'grease_pencils', text="")
                            elif db_type == 'MOVIE_CLIP':
                                row.prop_search(field_val, 'value_movie_clip', bpy.data, 'movieclips', text="")
                            elif db_type == 'SOUND':
                                row.prop_search(field_val, 'value_sound', bpy.data, 'sounds', text="")
                            elif db_type == 'TEXT':
                                row.prop_search(field_val, 'value_text', bpy.data, 'texts', text="")
                            elif db_type == 'VOLUME':
                                row.prop_search(field_val, 'value_volume', bpy.data, 'volumes', text="")
                            elif db_type == 'LATTICE':
                                row.prop_search(field_val, 'value_lattice', bpy.data, 'lattices', text="")
                            elif db_type == 'LIGHT_PROBE':
                                row.prop_search(field_val, 'value_light_probe', bpy.data, 'lightprobes', text="")
                            elif db_type == 'CACHE_FILE':
                                row.prop_search(field_val, 'value_cache_file', bpy.data, 'cache_files', text="")


class VIEW3D_PT_VariableFieldsActionsPanel(bpy.types.Panel):
    bl_label = "Scope Actions"
    bl_idname = "VIEW3D_PT_VariableFieldsActionsPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_parent_id = "VIEW3D_PT_VariableFieldsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        vf_settings = context.scene.variable_fields
        if not vf_settings.is_active:
            return False
        scope = get_active_scope(vf_settings)
        if not scope:
            return False
        # Show if there are scope actions OR in dev_mode (to allow adding actions)
        return len(scope.actions) > 0 or vf_settings.dev_mode

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields
        scope = get_active_scope(vf_settings)
        
        if not scope:
            return
        
        if vf_settings.dev_mode:
            row = layout.row(align=True)
            row.operator("variable_fields.add_action", text="Add Scope Action", icon='ADD')
            row.operator("variable_fields.load_predefined_action", text="", icon='PRESET')
            for i, action in enumerate(scope.actions):
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
            for action in scope.actions:
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
        vf_settings = context.scene.variable_fields
        if not vf_settings.is_active:
            return False
        # Show if there are general actions OR in dev_mode (to allow adding actions)
        return len(vf_settings.general_actions) > 0 or vf_settings.dev_mode

    def draw(self, context):
        layout = self.layout
        vf_settings = context.scene.variable_fields
        
        if vf_settings.dev_mode:
            row = layout.row(align=True)
            row.operator("variable_fields.add_general_action", text="Add General Action", icon='ADD')
            row.operator("variable_fields.load_predefined_action", text="", icon='PRESET')
            for i, action in enumerate(vf_settings.general_actions):
                box = layout.box()
                # Header row with name, move buttons, and remove button
                row = box.row(align=True)
                row.prop(action, "name", text="")
                sub = row.row(align=True)
                sub.scale_x = 0.8
                op = sub.operator("variable_fields.move_general_action", text="", icon='TRIA_UP')
                op.index = i
                op.direction = 'UP'
                op = sub.operator("variable_fields.move_general_action", text="", icon='TRIA_DOWN')
                op.index = i
                op.direction = 'DOWN'
                row.operator("variable_fields.remove_general_action", text="", icon='X').index = i
                # Script property
                box.prop(action, "script", text="Script")
        else:
            for action in vf_settings.general_actions:
                layout.operator("variable_fields.run_general_action", text=action.name).action_name = action.name


class VIEW3D_PT_VariableFieldsSettingsPanel(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "VIEW3D_PT_VariableFieldsSettingsPanel"
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
        
        # Update button with Auto Update toggle (wider toggle)
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("variable_fields.update_evaluation", text="Update")
        row.prop(vf_settings, "auto_update", text="", icon='FILE_REFRESH', toggle=True)
        
        layout.separator()
        layout.operator("variable_fields.deactivate", text="Deactivate")
        layout.separator()
        layout.prop(vf_settings, "dev_mode", text="Dev Mode", toggle=True)


classes = (
    VF_UL_ScopesList,
    VF_UL_AlternativesList,
    VIEW3D_PT_VariableFieldsPanel,
    VIEW3D_PT_VariableFieldsScopesPanel,
    VIEW3D_PT_VariableFieldsAlternativesPanel,
    VIEW3D_PT_VariableFieldsFieldSettingsPanel,
    VIEW3D_PT_VariableFieldsActionsPanel,
    VIEW3D_PT_VariableFieldsGeneralActionsPanel,
    VIEW3D_PT_VariableFieldsSettingsPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
