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

# N panel menu in object mode

import bpy

class LM_FS_PT_ObjectMode_Panel(bpy.types.Panel):
    bl_idname = "LM_FS_PT_ObjectMode_Panel"
    bl_label = "GP Follow Shapes"
    bl_category = "Grease Pencil"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bpy.types.Scene.lm_fs_prefix = bpy.props.StringProperty(
        name="Prefix",
        default="LM_FS_",
        description="Prefix for FollowShapes vertex groups and bones"
    )

    bpy.types.Scene.lm_fs_source_mesh = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Source Mesh",
        description="Source mesh object to conform to"
    )

    bpy.types.Scene.lm_fs_target_gp = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Target Grease Pencil",
        description="Target grease pencil object to drive"
    )
    bpy.types.Scene.lm_fs_distance = bpy.props.FloatProperty(
        name="Max distance",
        description="Maximum distance for binding. Points farther than this distance from the mesh will not be bound. Set to 0.0 to disable distance check.",
        default=0,
        min=0.0,
        soft_max=10.0,
        unit='LENGTH'
    )
    bpy.types.Scene.lm_fs_simplify = bpy.props.IntProperty(
        name="Simplify",
        description="Reduce number of points per stroke for rigging (higher value: more simplification. 1 = minimal simplification, recommended 3-7)",
        min=1,
        soft_max=10,
        default=5
    )
    bpy.types.Scene.lm_fs_expand = bpy.props.FloatProperty(
        name="Envelope distance",
        description="Bone influence distance (higher value: more smoothing and expansion of weights)",
        min=0.001,
        soft_max=10,
        default=0.25,
        unit='LENGTH'
    )
    

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT')
    
    def draw(self, context):    
        layout = self.layout

        # mesh input box
        layout.label(text="Source mesh:")
        layout.prop_search(context.scene, "lm_fs_source_mesh", bpy.data, "objects", text="")

        # grease pencil input box
        layout.label(text="Target Grease Pencil:")
        layout.prop_search(context.scene, "lm_fs_target_gp", bpy.data, "objects", text="")

        # delete button        
        layout.operator("lm_fs.delete")

        # transfer button
        layout.label(text= "Rigging options")
        layout.prop(context.scene, "lm_fs_distance")
        layout.prop(context.scene, "lm_fs_simplify") 
        layout.prop(context.scene, "lm_fs_expand")

        layout.label(text= "Create rig and bind GP target to it")
        layout.operator("lm_fs.rigbind")
        layout.operator("lm_fs.rigbind_all_frames")

        layout.label(text="Fine tune envelope distance")
        layout.operator("lm_fs.change_distance")
        layout.operator("lm_fs.change_distance_all_frames")

        layout.label(text="Add shrinkwrap&smoothing for better results")
        layout.operator("lm_fs.add_shrinkwrap")
