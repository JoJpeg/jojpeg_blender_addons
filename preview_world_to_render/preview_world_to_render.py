bl_info = {
    "name": "Use the Preview World for Rendering",
    "description": "Uses the preview world settings for rendering, for when you like the look of the preview world and want to render with it as well.",
    "author": "Jonas",
    "version": (0, 1),
    "blender": (4, 0, 0),  # Adjust based on your Blender version
    "location": "VIEW3D_PT_shading > Use Preview World for Render",
    "category": "Render",
}

import bpy
import os

def get_studio_light_path(light_name):
    # Iterate through preferences to find the studio light
    for light in bpy.context.preferences.studio_lights:
        if light.name == light_name:
            return light.path
    return None

class WORLD_OT_copy_shading_hdri(bpy.types.Operator):
    """Copies the current viewport shading HDRI to the World Shader nodes"""
    bl_idname = "world.copy_shading_hdri"
    bl_label = "Use Viewport HDRI in World"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        # 1. Get the current shading settings
        space_data = context.space_data
        shading = space_data.shading
        
        # Check if we are using Scene World (if so, we are already using the world, so nothing to copy)
        # However, the user might be in Material Preview mode which often uses Studio Lights
        # If shading.use_scene_world_render (for rendered view) or shading.use_scene_world (for material view) is True, warn user
        
        # The logic below assumes we want to capture the 'Studio' light (HDRI) currently used in Material Preview or Rendered view (if scene world is unchecked)
        
        studio_light_name = shading.studio_light
        studio_light_path = get_studio_light_path(studio_light_name)
        
        if not studio_light_path or not os.path.exists(studio_light_path):
            self.report({'ERROR'}, f"Could not find path for studio light: {studio_light_name}")
            return {'CANCELLED'}

        # 2. Setup World
        world_name = f"Preview {studio_light_name}"
        # create a new world
        world = bpy.data.worlds.new(world_name)
        context.scene.world = world
            
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        
        # Clear default nodes from the new world to ensure a clean slate
        nodes.clear()
        
        # 3. Add Environment Texture Node
        env_node = nodes.new(type='ShaderNodeTexEnvironment')
        env_node.location = (-300, 0)
        
        # Load the image
        try:
            image_name = os.path.basename(studio_light_path)
            if image_name in bpy.data.images:
                image = bpy.data.images[image_name]
                # Update filepath just in case
                if image.filepath != studio_light_path:
                    # If existing image has different path, maybe load as new to avoid conflicts? 
                    # For simplicty, let's just use load
                     image = bpy.data.images.load(studio_light_path, check_existing=True)
            else:
                image = bpy.data.images.load(studio_light_path, check_existing=True)
                
            env_node.image = image
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load image: {e}")
            return {'CANCELLED'}
            
        # 4. Create Background and Output Nodes
        bg_node = nodes.new(type='ShaderNodeBackground')
        bg_node.location = (0, 0)
            
        # Connect Env -> Background
        links.new(env_node.outputs['Color'], bg_node.inputs['Color'])
        
        output_node = nodes.new(type='ShaderNodeOutputWorld')
        output_node.location = (200, 0)
            
        # Connect Background -> Output
        links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])

        # 5. Fix Color Space (Important for HDRIs)
        if env_node.image:
             if hasattr(env_node.image.colorspace_settings, "name"):
                 # Usually HDRIs are Linear, but check if we need to set it. 
                 # Blender defaults usually handle .exr/.hdr correctly as non-color or linear.
                 pass
        
        # 6. Align rotation if possible
        # Viewport rotation of HDRI is shading.studiolight_rotate_z
        # We need a Mapping node for this.
        
        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-1200, 0)
        
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = (-900, 0)
        
        # Connect TexCoord -> Mapping
        links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
        
        # Create Blur setup
        # Blur (Mix Vector) Node
        blur_node = nodes.new(type='ShaderNodeMix')
        blur_node.data_type = 'VECTOR'
        blur_node.label = "Blur"
        blur_node.location = (-600, 0)
        # Set factor to match viewport blur setting
        blur_node.inputs[0].default_value = shading.studiolight_background_blur 
        
        # Noise Texture
        noise_node = nodes.new(type='ShaderNodeTexNoise')
        noise_node.inputs['Scale'].default_value = 30000.0
        noise_node.location = (-900, 300)
        
        # Vector Math (Subtract 0.5) to center the noise around 0
        sub_node = nodes.new(type='ShaderNodeVectorMath')
        sub_node.operation = 'SUBTRACT'
        sub_node.inputs[1].default_value = (0.5, 0.5, 0.5)
        sub_node.location = (-700, 300)
        
        # Connect Noise -> Subtract
        # Noise output is Color (but acts as vector if 3d). Vector Math takes Vector.
        links.new(noise_node.outputs['Color'], sub_node.inputs[0])
        
        # Connect Subtract -> Blur B
        # For ShaderNodeMix with VECTOR type, B input is index 5
        links.new(sub_node.outputs['Vector'], blur_node.inputs[5]) 
        
        # Connect Mapping -> Blur A
        # For ShaderNodeMix with VECTOR type, A input is index 4
        links.new(mapping.outputs['Vector'], blur_node.inputs[4]) 
        
        # Connect Blur -> Environment
        # For ShaderNodeMix with VECTOR type, Output is index 1
        links.new(blur_node.outputs[1], env_node.inputs['Vector']) 
        
        # Apply rotation (Z axis)
        mapping.inputs['Rotation'].default_value[2] = shading.studiolight_rotate_z
        
        self.report({'INFO'}, f"Copied HDRI '{studio_light_name}' to World")
        return {'FINISHED'}

def draw_menu(self, context):
    if context.space_data.shading.type == 'MATERIAL':
        layout = self.layout
        layout.separator()
        layout.operator("world.copy_shading_hdri", icon='WORLD')

def register():
    bpy.utils.register_class(WORLD_OT_copy_shading_hdri)
    bpy.types.VIEW3D_PT_shading.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(WORLD_OT_copy_shading_hdri)
    bpy.types.VIEW3D_PT_shading.remove(draw_menu)

if __name__ == "__main__":
    register()
