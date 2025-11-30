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

# Change envelope distance

import bpy

class LM_FS_OT_ChangeDistanceAllFrames(bpy.types.Operator):
    """Set new envelope distance"""
    bl_idname = "lm_fs.change_distance_all_frames"
    bl_label = "Change distance (All Frames)"
    bl_description = "Change envelope distance for existing rig in all frames"
    bl_options = {'REGISTER', 'UNDO'}


    # main function
    def execute(self, context):

        target_gp = context.scene.lm_fs_target_gp
        
        # Check if we are in Blender 4.3 or later
        def is_GP3():
            return hasattr(target_gp.data.layers[0].frames[0], 'drawing')
        
        # Iterate through all frames in all layers
        for layer in target_gp.data.layers:
            for frame in layer.frames:
                context.scene.frame_set(frame.frame_number)
                
                # Call the existing rigbind operator for each frame
                bpy.ops.lm_fs.change_distance('INVOKE_DEFAULT')
                
        return {'FINISHED'}