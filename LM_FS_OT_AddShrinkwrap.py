# LM LM_GPFollowShapes: Make Grease Pencil follow mesh animation
# Copyright (C) 2025 Luca Malisan

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Add shrinkwrap modifier to grease pencil for smoothing

import bpy

class LM_FS_OT_AddShrinkwrap(bpy.types.Operator):
    """Add shrinkwrap modifier to grease pencil for smoothing"""
    bl_idname = "lm_fs.add_shrinkwrap"
    bl_label = "Add Shrinkwrap Modifier"
    bl_description = "Add shrinkwrap modifier to grease pencil for smoothing. Defaults to 5mm offset and 3 steps of smooth factor 0.5"
    bl_options = {'REGISTER', 'UNDO'}

    # main function
    def execute(self, context):
        
        target_gp = context.scene.lm_fs_target_gp
        source_mesh = context.scene.lm_fs_source_mesh
        if not target_gp or not source_mesh:
            self.report({'ERROR'}, "Target Grease Pencil or Source Mesh not set")
            return {'CANCELLED'}
        
        # Check if we are in Blender 4.3 or later
        def is_GP3():
            return hasattr(target_gp.data.layers[0].frames[0], 'drawing')
        
        # Check if shrinkwrap modifier with fs prefix already exists
        fs_shrinkwrap_exists = False
        for modifier in target_gp.modifiers:
            if (modifier.type == 'GREASE_PENCIL_SHRINKWRAP' if is_GP3() else modifier.type == 'SHRINKWRAP') and modifier.name.startswith(context.scene.lm_fs_prefix+ "shrinkwrap"):
                fs_shrinkwrap_exists = True
                break

        # Create shrinkwrap modifier if it doesn't exist
        if not fs_shrinkwrap_exists:
            if is_GP3():
                shrinkwrap_mod = target_gp.modifiers.new(name=context.scene.lm_fs_prefix + "shrinkwrap", type='GREASE_PENCIL_SHRINKWRAP')
            else:
                shrinkwrap_mod = target_gp.grease_pencil_modifiers.new(name=context.scene.lm_fs_prefix + "shrinkwrap", type='SHRINKWRAP')
            shrinkwrap_mod.target = source_mesh
            shrinkwrap_mod.offset = 0.005
            shrinkwrap_mod.wrap_method = 'TARGET_PROJECT'
            shrinkwrap_mod.smooth_factor = 0.5
            shrinkwrap_mod.smooth_step = 3
        else:
            print("Shrinkwrap modifier with FollowShapes prefix already exists on target Grease Pencil")
            self.report({'WARNING'}, "Shrinkwrap modifier with FollowShapes prefix already exists on target Grease Pencil")
            return {'CANCELLED'}
        
        print("Shrinkwrap modifier added to Grease Pencil", target_gp.name)
        

        return {'FINISHED'}