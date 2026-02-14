bl_info = {
    "name": "Toggle Focus Selected",
    "description": "Focuses on similar F-Curves in the Graph Editor",
    "author": "Jonas",
    "version": (0, 36),
    "blender": (5, 0, 0),  # Adjust based on your Blender version
    "location": "Graph Editor > View > Focus Similar F-Curves",
    "category": "Graph Editor",
}

import bpy 
import re
 
# --- Combined Operator Script ---

class GRAPH_OT_focus_and_hide_fcurves(bpy.types.Operator):
    """Focus all F-Curves of the same type as the selected one and hide others. (All X Location F-Curves if X Location is selected etc.)"""
    bl_idname = "graph.focus_and_hide_fcurves"
    bl_label = "Focus Selected Fcurves & Hide Others"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_fcurves_in_editor = context.selected_editable_fcurves

        if not selected_fcurves_in_editor:
            self.report({'INFO'}, "No FCurve selected in the Graph Editor.")
            #show all fcurves
            try:
                bpy.ops.graph.reveal(select = False)
                bpy.ops.graph.view_all()
                
            except Exception as e:
                self.report({'ERROR'}, f"Failed to call graph operators: {e}")
            return {'CANCELLED'}


        # Collect all target F-Curve name formats from selected curves
        # Use regex to strip content inside brackets (e.g. ["bone_name"] or (bone_name)) for generalized matching
        strip_pattern = r'\[.*?\]|\(.*?\)'
        target_fcurve_name_formats = [
            f"{re.sub(strip_pattern, '', fcurve.data_path)}[{fcurve.array_index}]"
            for fcurve in selected_fcurves_in_editor
        ]
        self.report({'INFO'}, f"Target F-Curve name formats: {', '.join(target_fcurve_name_formats)}")
        print(f"Target F-Curve name formats: {', '.join(target_fcurve_name_formats)}")

        fcurves_to_show = []
        fcurves_to_hide = []

        currently_visible_fcurves = context.visible_fcurves

        if not currently_visible_fcurves:
            self.report({'WARNING'}, "No F-Curves found in any action.")
            return {'CANCELLED'}

        for fcurve in currently_visible_fcurves:
            current_fcurve_name_format = f"{re.sub(strip_pattern, '', fcurve.data_path)}[{fcurve.array_index}]"

            if current_fcurve_name_format in target_fcurve_name_formats:
                fcurves_to_show.append(fcurve)
                self.selectCurve(fcurve, True)
            else:
                fcurves_to_hide.append(fcurve)
                self.selectCurve(fcurve, False)

        if not fcurves_to_show:
            self.report({'INFO'}, "No matching F-Curves found across all actions.")
            return {'CANCELLED'}

        # Now, perform the hide and view_all operations using context.temp_override
        graph_editor_area = None
        for area in context.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                graph_editor_area = area
                break

        if not graph_editor_area:
            self.report({'WARNING'}, "No Graph Editor area found")
            return {'CANCELLED'}

        graph_editor_region = next(r for r in graph_editor_area.regions if r.type == 'WINDOW')

        try:
            with context.temp_override(
                window=context.window,
                screen=context.screen,
                area=graph_editor_area,
                region=graph_editor_region,
                blend_data=context.blend_data,
                scene=context.scene,
                space_data=graph_editor_area.spaces.active
            ):
                bpy.ops.graph.reveal()
                bpy.ops.graph.hide(unselected=True)
                bpy.ops.graph.view_all()

        except Exception as e:
            self.report({'ERROR'}, f"Failed to call graph operators: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Focused on {len(fcurves_to_show)} F-Curves and hid others.")
        return {'FINISHED'}

    def selectCurve(self, fcurve, select):
        """Selects the given F-Curve in the Graph Editor"""
        fcurve.select = select
        # Additional logic can be added here if needed to ensure visibility

class GRAPH_PT_focus_similar_fcurves_panel(bpy.types.Panel):
    """Creates a Panel in the Graph Editor's N-Panel under the View tab"""
    bl_label = "Focus Similar F-Curves"
    bl_idname = "GRAPH_PT_focus_similar_fcurves_panel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        layout.operator("graph.focus_and_hide_fcurves", text="Focus Similar F-Curves")


def register():
    bpy.utils.register_class(GRAPH_OT_focus_and_hide_fcurves)
    bpy.utils.register_class(GRAPH_PT_focus_similar_fcurves_panel)

def unregister():
    bpy.utils.unregister_class(GRAPH_PT_focus_similar_fcurves_panel)
    bpy.utils.unregister_class(GRAPH_OT_focus_and_hide_fcurves)

if __name__ == "__main__":
    register()