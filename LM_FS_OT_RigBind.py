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

# Create rig and bind grease pencil to mesh

import bpy
import mathutils
import bmesh


class LM_FS_OT_RigBind(bpy.types.Operator):
    """Create rig and bind grease pencil to mesh in the current frame"""
    bl_idname = "lm_fs.rigbind"
    bl_label = "Bind Current Frame"
    bl_description = "Create rig and bind grease pencil to mesh for the current frame"
    bl_options = {'REGISTER', 'UNDO'}

    LM_FS_RIG_SUFFIX = "_RIG"

    # main function
    def execute(self, context):

        target_gp = context.scene.lm_fs_target_gp
        source_mesh = context.scene.lm_fs_source_mesh

        # Check if we are in Blender 4.3 or later
        def is_GP3():
            return hasattr(target_gp.data.layers[0].frames[0], 'drawing')
        
        current_frame = context.scene.frame_current

        rig_name = context.scene.lm_fs_prefix + context.scene.lm_fs_target_gp.name + "_F" + str(current_frame) + self.LM_FS_RIG_SUFFIX

        # Check if armature with rig_name already exists and delete it
        if rig_name in bpy.data.objects:
            existing_rig = bpy.data.objects[rig_name]
            # Remove parenting if target_gp is parented to this rig
            if target_gp.parent == existing_rig:
                target_gp.parent = None
                target_gp.parent_type = 'OBJECT'
            bpy.data.objects.remove(existing_rig, do_unlink=True)
            # Remove armature modifiers that reference the deleted rig
            for modifier in target_gp.modifiers:                
                if modifier.type == 'GREASE_PENCIL_ARMATURE' and modifier.object is None:                   
                    target_gp.modifiers.remove(modifier)

        # Create new armature
        armature_data = bpy.data.armatures.new(rig_name)
        armature_obj = bpy.data.objects.new(rig_name, armature_data)
        armature_obj.data.display_type = 'ENVELOPE'

        # Duplicate the target grease pencil object
        new_gp = target_gp.copy()
        new_gp.data = target_gp.data.copy()
        context.collection.objects.link(new_gp)

        # Add simplify modifier to the duplicated grease pencil
        if is_GP3():
            simplify_modifier = new_gp.modifiers.new(name="Simplify", type='GREASE_PENCIL_SIMPLIFY')
        else:
            simplify_modifier = new_gp.grease_pencil_modifiers.new(name="Simplify", type='GP_SIMPLIFY')
        simplify_modifier.mode = 'ADAPTIVE'
        simplify_modifier.factor = max(1.0, float(context.scene.lm_fs_simplify))/1000
        
        # Apply the simplify modifier
        bpy.context.view_layer.objects.active = new_gp
        if is_GP3():
            bpy.ops.object.modifier_apply(modifier=simplify_modifier.name,all_keyframes=True)
        else:
            bpy.ops.object.modifier_apply(modifier=simplify_modifier.name)

        # Create or get the empties collection
        empties_collection_name = rig_name + "_CTRL"
        if empties_collection_name not in bpy.data.collections:
            empties_collection = bpy.data.collections.new(empties_collection_name)
            context.scene.collection.children.link(empties_collection)
        else:
            empties_collection = bpy.data.collections[empties_collection_name]
            # Clear all objects from the existing collection
            for obj in empties_collection.objects[:]:
                bpy.data.objects.remove(obj, do_unlink=True)
        # Make sure the collection is visible and selectable
        layer_collection = bpy.context.view_layer.layer_collection
        for lc in layer_collection.children:
            if lc.collection == empties_collection:
                lc.hide_viewport = False
                break
        empties_collection.hide_render = False     

        # Link the armature to the scene collection
        context.collection.objects.link(armature_obj)
        # Move armature to empties collection
        if armature_obj.name in context.collection.objects:
            context.collection.objects.unlink(armature_obj)
        empties_collection.objects.link(armature_obj)
        
        bone_size = context.scene.lm_fs_expand
        
        # Get all keyframes from the grease pencil
        gp_data = new_gp.data
        
        # Iterate through all layers
        for layer_idx, layer in enumerate(gp_data.layers):
            print("Processing layer:", layer.name if is_GP3() else layer.info)
            # Iterate through all frames
            for frame in layer.frames:                                
                # compatibilty with 4.2/4.4
                drawing = frame.drawing if is_GP3() else frame

                frame_number = frame.frame_number

                # skip frames that are not the current frame
                if frame_number != current_frame: 
                    continue                
                # Set current frame (redundant, kept for loop compatibility)
                context.scene.frame_set(frame_number)

                print(" Processing frame:", frame.frame_number)
                
                # Count total points for progress tracking
                total_points = 0
                for layer_temp in gp_data.layers:
                    for frame_temp in layer_temp.frames:
                        if frame_temp.frame_number != current_frame: 
                            continue
                        drawing_temp = frame_temp.drawing if is_GP3() else frame_temp
                        for stroke_temp in drawing_temp.strokes:
                            total_points += len(stroke_temp.points)
                
                current_point = 0
                
                # Iterate through all strokes in this frame
                for stroke_idx, stroke in enumerate(drawing.strokes):
                    # Iterate through all points in this stroke
                    for point_idx, point in enumerate(stroke.points):
                        current_point += 1
                        progress = (current_point / total_points) * 100
                        # Only print progress when percentage has 1 unit increment
                        new_progress_unit = int(progress)
                        if not hasattr(self, '_last_progress_unit'):
                            self._last_progress_unit = 0
                        if new_progress_unit > self._last_progress_unit + 5:
                            print(f"Creating and binding empties and bones: {new_progress_unit}% ({current_point}/{total_points})")
                            self._last_progress_unit = new_progress_unit
                        
                        # compatibilty with 4.2/4.4
                        point_co = point.position if is_GP3() else point.co

                        # Get world position of the point
                        world_pos = new_gp.matrix_world @ point_co
                        
                        # Create unique empty name
                        empty_name = f"{context.scene.lm_fs_prefix}CTRL_{target_gp.name}_f{frame_number}_l{layer_idx}_s{stroke_idx}_p{point_idx}"

                        # Create unique bone name
                        bone_name = empty_name 
                                             
                        # Create empty object at point location
                        bpy.ops.object.empty_add(type='SPHERE', location=world_pos)
                        empty = bpy.context.object
                        empty.name = empty_name
                        empty.empty_display_size = bone_size
                        # Move empty to empties collection
                        if empty.name in context.collection.objects:
                            context.collection.objects.unlink(empty)
                        empties_collection.objects.link(empty)

                        # Find nearest face on source mesh
                        # Create bmesh from source mesh
                        bm = bmesh.new()
                        bm.from_mesh(source_mesh.data)
                        bm.faces.ensure_lookup_table()
                        
                        # Find closest face to the world position
                        closest_face = None
                        min_distance =  context.scene.lm_fs_distance
                        if min_distance == 0:
                            min_distance = float('inf')

                        for face in bm.faces:
                            face_center = source_mesh.matrix_world @ face.calc_center_median()
                            distance = (world_pos - face_center).length
                            if distance < min_distance:
                                min_distance = distance
                                closest_face = face
                        
                        if closest_face:
                            # Get the three vertices of the closest face
                            face_verts = [v.co for v in closest_face.verts]
                            face_vert_indices = [v.index for v in closest_face.verts]

                            # Parent empty to source mesh with vertex (3 vertices) parenting
                            bpy.ops.object.select_all(action='DESELECT')
                            source_mesh.select_set(True)
                            empty.select_set(True)
                            bpy.context.view_layer.objects.active = source_mesh

                            # Enter edit mode and select the three vertices
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')                            

                            # Select the three vertices of the closest face
                            for vert_idx in face_vert_indices:
                                source_mesh.data.vertices[vert_idx].select = True

                            # Back to edit mode and set parent
                            bpy.ops.object.mode_set(mode='OBJECT')
                            bpy.ops.object.parent_set(type='VERTEX_TRI')

                            # Create bone
                            # Enter edit mode for armature to add bones
                            bpy.ops.object.mode_set(mode='OBJECT')
                            bpy.context.view_layer.objects.active = armature_obj
                            bpy.ops.object.mode_set(mode='EDIT')
                            bone = armature_data.edit_bones.new(bone_name)
                            bone.head = world_pos
                            bone.tail = world_pos + mathutils.Vector((0, bone_size*0.1, 0 ))
                            bone.envelope_distance = bone_size * 0.8
                            bone.head_radius = bone_size * 0.2
                            bone.tail_radius = bone.head_radius * 0.5

                            # Add constraint to the bone
                            # First, exit edit mode to access pose bones
                            bpy.ops.object.mode_set(mode='OBJECT')
                            bpy.ops.object.mode_set(mode='POSE')

                            # Get the pose bone
                            pose_bone = armature_obj.pose.bones[bone_name]

                            # Add Copy Transforms constraint to follow the empty
                            copy_transforms_constraint = pose_bone.constraints.new('COPY_TRANSFORMS')
                            copy_transforms_constraint.name = f"CopyTransforms_{empty_name}"    
                            copy_transforms_constraint.target = empty
                            bpy.ops.object.mode_set(mode='OBJECT')

                        else:
                            # Delete the empty if no closest face found
                            bpy.ops.object.select_all(action='DESELECT')
                            empty.select_set(True)
                            bpy.ops.object.delete()
                        
                        bm.free()

        print("Rig and empties created successfully")

        # Bind target_gp to armature with automatic weights
        bpy.context.view_layer.objects.active = target_gp
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Select both objects for parenting
        bpy.ops.object.select_all(action='DESELECT')
        target_gp.select_set(True)
        armature_obj.select_set(True)
        bpy.context.view_layer.objects.active = armature_obj
        
        # Parent with automatic weights
        # bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
        print("Grease Pencil bound to rig with envelope weights")      
        
        # Delete the duplicated grease pencil object
        bpy.data.objects.remove(new_gp, do_unlink=True)

        # Hide the collection
        layer_collection = bpy.context.view_layer.layer_collection
        for lc in layer_collection.children:
            if lc.collection == empties_collection:
                lc.hide_viewport = True
                break
        empties_collection.hide_render = True

        # Select GP (for user convenience)
        bpy.ops.object.select_all(action='DESELECT')
        target_gp.select_set(True)
        bpy.context.view_layer.objects.active = target_gp

        print("Bind for frame " + str(current_frame) + " completed successfully")

        return {'FINISHED'}