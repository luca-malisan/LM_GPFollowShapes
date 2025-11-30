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
import mathutils

class LM_FS_OT_ChangeDistance(bpy.types.Operator):
    """Set new envelope distance"""
    bl_idname = "lm_fs.change_distance"
    bl_label = "Change envelope distance (Current Frame)"
    bl_description = "Change envelope distance for existing rig in the current frame"
    bl_options = {'REGISTER', 'UNDO'}

    LM_FS_RIG_SUFFIX = "_RIG"

    # main function
    def execute(self, context):
        print("Changing envelope distance for existing rig on current frame")

        # Check if we are in Blender 4.3 or later
        def is_GP3():
            return hasattr(target_gp.data.layers[0].frames[0], 'drawing')
    
        current_frame = context.scene.frame_current
        rig_name = context.scene.lm_fs_prefix + context.scene.lm_fs_target_gp.name + "_F" + str(current_frame) + self.LM_FS_RIG_SUFFIX

        # Check if rig exists
        if rig_name not in bpy.data.objects:
            self.report({'WARNING'}, f"No GPFollowShapes rig found for current frame")
            return {'CANCELLED'}

        rig = bpy.data.objects[rig_name]

        # Check if rig is an armature
        if rig.type != 'ARMATURE':
            self.report({'ERROR'}, f"Object '{rig_name}' is not an armature")
            return {'CANCELLED'}
        
        target_gp = context.scene.lm_fs_target_gp

        bone_size = context.scene.lm_fs_expand

        # Remember the lock status of all vertex groups
        vertex_group_locks = {}
        for vg in target_gp.vertex_groups:
            vertex_group_locks[vg.name] = vg.lock_weight
            vg.lock_weight = True

        # Update bone envelopes
        for bone in rig.data.bones:            
            bone.envelope_distance = bone_size * 0.8
            bone.head_radius = bone_size * 0.2
            bone.tail_radius = bone.head_radius * 0.5

            # Find copy transforms constraint target
            for constraint in rig.pose.bones[bone.name].constraints:
                if constraint.type == 'COPY_TRANSFORMS':
                    target_object = constraint.target
                    if target_object:
                        if target_object.type == 'EMPTY':
                            target_object.empty_display_size = bone_size
                    break
            
            # Remove corresponding vertex group from target_gp
            if bone.name in target_gp.vertex_groups:
                vg = target_gp.vertex_groups[bone.name]
                vg.lock_weight = False
                target_gp.vertex_groups.remove(vg)
        
        # Remove parenting if target_gp is parented to this rig
        if target_gp.parent == rig:
            target_gp.parent = None
            target_gp.parent_type = 'OBJECT'
        # Remove armature modifiers that reference the deleted rig
        for modifier in target_gp.modifiers:                
            if modifier.type == 'GREASE_PENCIL_ARMATURE' and modifier.object == rig:                   
                target_gp.modifiers.remove(modifier)

        # Remember lock and hide settings for all layers
        layer_settings = {}
        for layer_idx, layer in enumerate(target_gp.data.layers):
            layer_settings[layer_idx] = {
            'lock': layer.lock,
            'hide': layer.hide
            }
            # If layer has no keyframe at current frame, lock and hide it
            if not any(frame.frame_number == current_frame for frame in layer.frames):
                layer.lock = True
                layer.hide = True


        # Bind target_gp to armature with automatic weights
        bpy.context.view_layer.objects.active = target_gp
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Select both objects for parenting
        bpy.ops.object.select_all(action='DESELECT')
        target_gp.select_set(True)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        
        # Parent with envelope weights
        bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')

        # Restore the lock status of all vertex groups
        for vg in target_gp.vertex_groups:
            if vg.name in vertex_group_locks:
                vg.lock_weight = vertex_group_locks[vg.name]

        # Restore layer settings
        for layer_idx, layer in enumerate(target_gp.data.layers):
            if layer_idx in layer_settings:
                layer.lock = layer_settings[layer_idx]['lock']
                layer.hide = layer_settings[layer_idx]['hide']

        bpy.ops.object.select_all(action='DESELECT')
        target_gp.select_set(True)
        bpy.context.view_layer.objects.active = target_gp

        print("Grease Pencil bound to rig with envelope weights")      

        return {'FINISHED'}