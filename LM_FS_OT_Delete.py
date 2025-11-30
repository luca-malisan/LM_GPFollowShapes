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

# Delete all FollowShapes bindings

import bpy

class LM_FS_OT_Delete(bpy.types.Operator):
    """Delete all FollowShapes bindings from target and source objects"""
    bl_idname = "lm_fs.delete"
    bl_label = "Delete all FollowShapes bindings"
    bl_description = "Delete all FollowShapes bindings from target and source objects"
    bl_options = {'REGISTER', 'UNDO'}

    # main function
    def execute(self, context):
        
        try:
            
            target = context.scene.lm_fs_target_gp

            if target and (target.type == 'GPENCIL' or target.type == 'GREASEPENCIL'):
                #remove FollowShapes weights from target grease pencil object
                            
                print("Deleting FollowShapes weights from Grease Pencil", target.name)

                # Get all vertex groups from gpencil object
                vgroups = target.vertex_groups

                # Ensure target has matching vertex groups
                for vgroup in vgroups:
                    if not vgroup.lock_weight and vgroup.name.startswith(context.scene.lm_fs_prefix):
                        print("Deleting FollowShapes vertex group:", vgroup.name)
                        
                        for layer in target.data.layers:
                            for frame in layer.frames:
                                if hasattr(frame, 'drawing') and frame.drawing.attributes.get(vgroup.name):
                                    # Remove the vertex group attribute from the drawing
                                    frame.drawing.attributes.remove(frame.drawing.attributes[vgroup.name])

                        target.vertex_groups.remove(vgroup)                        

                print("All FollowShapes weights deleted from", target.name)

                # Remove armature modifiers and corresponding rigs
                for modifier in target.modifiers:
                    if modifier.type == 'GREASE_PENCIL_ARMATURE' and modifier.object:
                        rig = modifier.object
                        if rig.name.startswith(context.scene.lm_fs_prefix):
                            print("Removing FollowShapes armature modifier:", modifier.name)
                            print("Deleting corresponding rig:", rig.name)
                            
                            # Remove parenting if target is parented to this rig
                            if target.parent == rig:
                                target.parent = None
                                target.parent_type = 'OBJECT'
                            
                            # Get the collection containing the rig and delete all objects in it
                            if rig.users_collection:
                                for collection in rig.users_collection:
                                    if collection.name.startswith(context.scene.lm_fs_prefix):
                                        # Remove all objects from the collection
                                        for obj in list(collection.objects):
                                            bpy.data.objects.remove(obj, do_unlink=True)
                                        # Remove the collection itself
                                        bpy.data.collections.remove(collection)
              
                            # Finally, remove the modifier
                            target.modifiers.remove(modifier)


        except Exception as e:
            import traceback
            traceback.print_exc()

            self.report({'WARNING'}, "Unable to delete bindings: " + str(e))
            return {'CANCELLED'}

        return {'FINISHED'}