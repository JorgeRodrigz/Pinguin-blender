bl_info = {
    "name": "Pinguin",
    "author": "Jorge Rodriguez <jorgeandresarq+dev@gmail.com>",
    "version": (3, 5, 0),
    "blender": (3, 6, 0),
    "location": "Operator Search",
    "description": "Takes cutout images(png format) and turns them into a mesh in the 3D Space",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

### Imports all needed modules
import bpy
import bmesh
import sys  
import os
import subprocess
import time
import math
import statistics
from mathutils import (Matrix,Vector, Quaternion)


# Updates pip 
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
# pillow, opencv, numpy are non-preinstalled blender libraries, then it checks if they are already installed
# if not it installs them using a pip subprocess 
try:
    from PIL import Image # pip install Pillow
    print("Pillow module found")
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',"Pillow"])
    from PIL import Image 
    print("Pillow module installed and imported")
try:    
    import cv2 as cv #pip install opencv-python
    print("Open-cv module found") 
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',"opencv-python"])
    import cv2 as cv
    print("Open-cv installed and imported")   
try:    
    import numpy as np #pip install numpy
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',"numpy"])
    import numpy as np 

### ERRRORS ###
class NotFacingTowardsError(Exception):
    "Raised when the tilt operation is "
    pass

class PerpendicularOrientError(Exception):
    "Raised when the tilt operation is "
    pass

### PROPERTIES ###
class PinguinProperties(bpy.types.PropertyGroup):

    pinguin_folder :  bpy.props.StringProperty(
        subtype='DIR_PATH',
        name='',
        description = "Folder where cut-out images are located, only images in .png format will be converted", 
        default="Cutouts directory"
        )
    
    pinguin_mesh_height : bpy.props.FloatProperty(
        name = "Mesh Heigth", 
        description="Mesh target height",
        default=1.7,
        min=0.001, soft_max=10
        )
    
    pinguin_vertical_orient : bpy.props.BoolProperty(
        name = "Vertical", 
        description="Toogle to stand up the meshes",
        default=True
        )
    
    pinguin_holes : bpy.props.BoolProperty(
        name = "Holes", 
        description="Toogle to create a mesh with holes",
        default=False
        )
    
    
    pinguin_cv_algorithm : bpy.props.EnumProperty(
        name = "Contour Algorithm",
        description = "Set the contour search algorithm between a fast one or a presice one",
        items = [("SIMPLE","Fast",""),
                ("NONE","Detailed","")],
        options = {"ENUM_FLAG"},
        default = {"SIMPLE"}
        )
    
    pinguin_face_target_object : bpy.props.PointerProperty(
        name = "Target",
        description = "Set the contour search algorithm between a fast one or a presice one",
        options={'ANIMATABLE'},
        type=bpy.types.Object,
    )

    pinguin_face_target_tilt : bpy.props.BoolProperty(
        name = "Tilt", 
        description="Enable tilt in alignment",
        default=False
        )

### OPERATORS ###
class MESH_OT_pinguin_create(bpy.types.Operator):
    """Converts some png cutouts into a mesh"""
    bl_idname = "mesh.png_to_mesh"
    bl_label = "Png to Mesh"
    #bl_options = {'REGISTER', 'UNDO'}
    ### Define Properties that will be appended to the variables

    def execute(self, context):
        
        ### -1.Variable Assignment
        directory = context.scene.my_tool.pinguin_folder
        mesh_height = context.scene.my_tool.pinguin_mesh_height
        orient_vertical = context.scene.my_tool.pinguin_vertical_orient
        create_holes = context.scene.my_tool.pinguin_holes
        chain_aproximation_method = context.scene.my_tool.pinguin_cv_algorithm
        
        # "CHAIN_APPROX_SIMPLE" or "CHAIN_APROX_NONE"   

        proxie_collection = "proxie_collection_pinguin"
        final_collection = "Pinguin-Cutout to Mesh"   
        opacity_suffix = "_opc"
        vector_suffix = "_poly"

        x_cursor,y_cursor,z_cursor = bpy.context.scene.cursor.location   
        
        ### 0. Program Start - Main()
        start_time = time.time()
        print("👾 Checking directory 👾")
        
        ### Checks Directory Existance
        if directory == "":
            raise TypeError("Empty directory")
        elif not os.path.exists(directory):
            raise FileNotFoundError(f"The directory '{directory}' does not exist.")

        ### 1. Finds all new pngs and procress them into alpha channel maps
        png_paths = image_png_paths(directory)
        opc_images = image_opacity_map(png_paths, opacity_suffix, ".png")
        
        alpha_channels_directory = "Alpha Channel"
        alpha_channels_path = directory + "/" + alpha_channels_directory
        
        if not os.path.exists(alpha_channels_path):
            os.mkdir(alpha_channels_path)

        opc_paths = image_result_path(png_paths, opacity_suffix, ".png")
        final_opc_paths = []
        for opc_image in opc_paths:
            opc_filename = os.path.basename(opc_image)
            opc_destination = os.path.join(alpha_channels_path, opc_filename)
            final_opc_paths.append(opc_destination)
        opc_paths = final_opc_paths   

        ### 2. Saves alpha channel maps
        save_batch_png(opc_images, opc_paths)
        print("🦅 Succesful alpha channel conversion 🐧")

        # ___Desde este punto cada funcion procesa individualmente cada imagen requiriendo el uso de loops para procesar cada imagen en un set___

        ### 3. Computer vision process image into a contour
        contours_list=[]
        hierarchy_list=[]
        dimension_list=[]
        # This one is used if holes are needed
        contour_parent_list=[]
        
        
        for opc_path_ in opc_paths:
            contour,hierarchy,dimensions = alpha_channel_to_contour(opc_path_,chain_aproximation_method)
            contours_list.append(contour)
            hierarchy_list.append(hierarchy)
            dimension_list.append(dimensions)
            
            #Returns a simple list of the parents and holes
            contour_parent = []
            for contours_hierarchy in hierarchy:
                for each_contour_hierarchy in contours_hierarchy:
                    contour_parent.append(each_contour_hierarchy[3])
            contour_parent_list.append(contour_parent)

        
        ### 4. Formats nparrya(contours) into simpler list 
        formated_images_contours = []
        
        for image_contours_ in contours_list:
            formated = format_contour_to_list(image_contours_)
            formated_images_contours.append(formated)
        
        ### 5. Smooth -> Aplies a cyclic rolling average function that smooths the curve vertices  
        smoothed_contours = []

        for form_image_contours_ in formated_images_contours:
            this_image_contours = []
            for contour in form_image_contours_:
                this_image_contours.append(point_rolling_average(contour))
            smoothed_contours.append(this_image_contours)

        ### 6. Scale Contours in each image
        scaled_contours = []
        look_index = 0
        
        for image_conts in smoothed_contours:
            scaled_contours_set = []
            get_size=dimension_list[look_index]
            img_height, img_width, duntknowwhatitdoes = get_size
            scale_factor = mesh_height/img_height   
            for conts in image_conts:
                scaled_contours_set.append(scale_contour(conts, scale_factor))
            scaled_contours.append(scaled_contours_set)      
            look_index +=1

        ### 8. Asignación de vertices    
        verts_set = scaled_contours

        ### 9. Creacion de Edges
        edge_set = []
        face_set = []

        for vertex_sets in verts_set:
            edges = get_edges(vertex_sets)
            edge_set.append(edges)
            faces = get_faces(vertex_sets)
            face_set.append(faces)

        print("🐦 Verts and Edges and Faces are ready 🦚")

        ### 10. Meshes and Object names
        obj_name_set =[]

        for path in png_paths:
            path = path[len(directory)+1:]
            path = path[:-4]
            obj_name_set.append(path)
            
        ### 11 Turns dimensions into image extent vertices 
        extents_set = []

        for dim_index in range(len(dimension_list)):
            get_size = dimension_list[dim_index]
            img_height, img_width, duntknowwhatitdoes = get_size
            scale_factor = mesh_height/img_height
            
            extent_verts = dim_to_extent_verts(dimension_list[dim_index])
            extent_verts = scale_contour(extent_verts, scale_factor)
            extents_set.append(extent_verts)
            
        print("🐦 Extents are ready 🦚")
        
        ### 13.Bl Creates a new proxie_collection to store_ resultant meshes temporarly 
        collections = bpy.data.collections
        pinguin_collection_name = proxie_collection

        if pinguin_collection_name in collections:
            pinguin_collection = bpy.data.collections.get(pinguin_collection_name)
        else:       
            pinguin_collection = bpy.data.collections.new(pinguin_collection_name)
            bpy.context.scene.collection.children.link(pinguin_collection)       
        
        
        ### 14.Bl Meshes from contour sets
        print("🐦 Creating Meshes 🦚", "\n")
        
        if create_holes == False:
            for image_index in range(len(verts_set)):
                
                ### THATS WHAT I AM TAKING ABOUT, THATS WHY HE IS THE MVP, THATS WHY HE IS THE GOAT!
                ### Not only returns a beautiful mesh but also unwrapps it Lets gooo!

                ### get only external edges
                external_verts_set = []
                external_edge_set = []
                
                image_verts_set = verts_set[image_index]
                image_edge_set = edge_set[image_index]
                
                parent_index = 0
                for parent in (contour_parent_list[image_index]):   
                    if parent == -1:
                        external_verts_set.append(image_verts_set[(parent_index)])
                        external_edge_set.append(image_edge_set[(parent_index)])
                    parent_index += 1
                
                #create meshes from external contours
                mesh_from_contours_info(external_verts_set, external_edge_set, extents_set[image_index], obj_name_set[image_index])
                mesh_name = obj_name_set[image_index]
                material_to_mesh(mesh_name, directory)
                
                ### Moves Objects into proxie collection and removes it from previews Collections
                selected_object = bpy.context.active_object
                for obj in bpy.context.selected_objects:
                    for other_col in obj.users_collection:
                        other_col.objects.unlink(obj)
                    if obj.name not in pinguin_collection.objects:
                        pinguin_collection.objects.link(obj) 
        
        if create_holes == True:
            for image_index in range(len(verts_set)):
                ### Get hierarchies list based on contour parent list
                #print("CPL",contour_parent_list[image_index])
                cpl = contour_parent_list[image_index]
                hierarchy_level_list = []
                for parent_index in range(len(cpl)):
                    cpl_parent = cpl[parent_index]
                    hierarchy_level = 0
                    while cpl_parent != -1:
                        parent_index = cpl_parent
                        cpl_parent = cpl[parent_index]
                        hierarchy_level += 1
                    hierarchy_level_list.append(hierarchy_level)
                #print("HLL",hierarchy_level_list)
                
                ### Get a set of the values in the hierarchy_level_list
                hierarchy_level_set = set(hierarchy_level_list)
                #print("HLS", hierarchy_level_set)
                ### Get the indexes of the filled hierarchies present
                pair_fill_void_indexes =[]
                for fill_void_index in hierarchy_level_set:
                    if  fill_void_index % 2 == 0 or fill_void_index == 0:
                        pair_fill_void_indexes.append(fill_void_index)
                #print("PFVI",pair_fill_void_indexes)
                
                separate_mesh_names = []

                for fill_hierearchy_index in pair_fill_void_indexes:
                    void_hierearchy_index = fill_hierearchy_index + 1
                    
                    ### Store valid contours 
                    valid_fill_verts = []
                    valid_fill_edges = []
                    valid_void_verts = []
                    valid_void_edges = []
                    
                    image_verts_set = verts_set[image_index]
                    image_edge_set = edge_set[image_index]

                    for hierarchy_level_index in range(len(hierarchy_level_list)):
                        if hierarchy_level_list[hierarchy_level_index] == fill_hierearchy_index:
                            valid_fill_verts.append(image_verts_set[hierarchy_level_index])
                            valid_fill_edges.append(image_edge_set[hierarchy_level_index])
                        elif hierarchy_level_list[hierarchy_level_index] == void_hierearchy_index:
                            ### Agarra el errror si no hay un mesh de resta
                            try:
                                valid_void_verts.append(image_verts_set[hierarchy_level_index])
                                valid_void_edges.append(image_edge_set[hierarchy_level_index])
                            except:
                                pass
                    ### Build fill meshes and append material
                    mesh_from_contours_info(valid_fill_verts, valid_fill_edges, extents_set[image_index], obj_name_set[image_index]+f"_H{fill_hierearchy_index}")
                    material_name = obj_name_set[image_index]
                    material_to_mesh(material_name, directory)
                    
                    ### This catches in case the pair has no void info
                    
                    ### This if catches if there is a fill witouht a void
                    if valid_void_edges != []:
                    ### Build void meshes + solidify
                        mesh_from_contours_info(valid_void_verts, valid_void_edges, extents_set[image_index], obj_name_set[image_index]+f"_V{fill_hierearchy_index}")
                        bpy.ops.object.modifier_add(type='SOLIDIFY')
                        bpy.context.object.modifiers["Solidify"].offset = 0
                        bpy.context.object.modifiers["Solidify"].thickness = 0.5
                        bpy.ops.object.modifier_apply(modifier="Solidify")

                        ###  Boolean diference between fill and void
                        bool_object = bpy.data.objects.get(obj_name_set[image_index]+f"_H{fill_hierearchy_index}")
                        bool_modifier = bool_object.modifiers.new(name="Boolean", type='BOOLEAN')
                        bool_modifier.operation = 'DIFFERENCE'  # Choose the desired operation (DIFFERENCE, UNION, INTERSECT)
                        bool_modifier.object = bpy.data.objects[obj_name_set[image_index]+f"_V{fill_hierearchy_index}"]
                        
                        bpy.ops.object.select_all(action='DESELECT')
                        object_to_select = bpy.data.objects.get(obj_name_set[image_index]+f"_H{fill_hierearchy_index}")
                        object_to_select.select_set(True)
                        bpy.context.view_layer.objects.active = object_to_select
                        bpy.ops.object.modifier_apply(modifier=bool_modifier.name)

                        ### Delete void Object
                        object_to_delete = bpy.data.objects.get(obj_name_set[image_index]+f"_V{fill_hierearchy_index}")
                        bpy.data.objects.remove(object_to_delete, do_unlink=True)
                        
                    ### Append mesh name to a list to then select that list and join them all
                    separate_mesh_names.append(obj_name_set[image_index]+f"_H{fill_hierearchy_index}")
                
                ### Join Parts
                bpy.ops.object.select_all(action='DESELECT')    
                for mesh_part_name in separate_mesh_names:
                    part_to_select = bpy.data.objects.get(mesh_part_name)
                    part_to_select.select_set(True)    
                bpy.ops.object.join()
                
                ### Rename without suffixes
                selected_objects = bpy.context.selected_objects
                selected_object = selected_objects[0]
                selected_object.name = obj_name_set[image_index]
                
                selected_object = bpy.context.active_object
                for obj in bpy.context.selected_objects:
                    for other_col in obj.users_collection:
                        other_col.objects.unlink(obj)
                    if obj.name not in pinguin_collection.objects:
                        pinguin_collection.objects.link(obj) 
                    
        ### 15 Array Meshes in collection in a matrix
        bpy.context.scene.cursor.location = Vector((x_cursor,y_cursor,z_cursor))
        organize_objects(pinguin_collection)
        bpy.ops.object.select_all(action='DESELECT')     

        ### 15.5 Orient Meshes Vertical if True 
        if orient_vertical:
            for obj in pinguin_collection.objects:
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.transform.rotate(value=math.pi/-2, orient_axis='X')
                bpy.ops.object.select_all(action='DESELECT')    
        
        ### 16.Bl Creates a new final_collection to store_meshes
        collections = bpy.data.collections
        final_collection_name = final_collection
        
        if final_collection_name in collections:
            final_pinguin_collection = bpy.data.collections.get(final_collection_name)
        else:       
            final_pinguin_collection = bpy.data.collections.new(final_collection_name)
            bpy.context.scene.collection.children.link(final_pinguin_collection) 
        
        ### 17. Move all Objects to final collection and removes/hides the proxie collection         
        for obj in pinguin_collection.objects:
            for other_col in obj.users_collection:
                other_col.objects.unlink(obj)
            if obj.name not in final_pinguin_collection:
                final_pinguin_collection.objects.link(obj)
                obj.select_set(True)
        bpy.data.collections.remove(pinguin_collection)
        
        ### 19. Returns statistics on how the program performed
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nElapsed time: {elapsed_time} seconds 🐧") 
        return{"FINISHED"}

class TRANSFORM_OT_face_towards(bpy.types.Operator):
    """Face cutouts towards an object"""
    bl_idname = "transform.face_towards"
    bl_label = "Face Towards"
    
    def execute(self, context):
        
        # 1 Get target object
        target_object = context.scene.my_tool.pinguin_face_target_object
        target_object_location = target_object.location
        # 2 Get all selected objects
        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            obj_location = obj.location
            obj_normal_vector = get_first_face_normal(obj)
            obj_target_vector = target_object_location - obj_location
            
            ### Get rotation angles
            xy_angle_radians, tilt_angle_radians, azimut_angle_radians = get_align_angle(obj_normal_vector, obj_target_vector)
        # 3 Rotate on xy plane  
            # set default rotation mode in case Tilt was enabled and then disabled
            obj.rotation_mode ='XYZ'
            # Create an Euler rotation object
            rotation_euler = obj.rotation_euler
            # Set the rotation in the XY plane
            rotation_euler.rotate_axis('Z', xy_angle_radians)
            # Apply the rotation
            obj.rotation_euler = rotation_euler
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False) 
            
        return{"FINISHED"}

class TRANSFORM_OT_face_towards_tilt(bpy.types.Operator):
    """Face cutouts towards an object"""
    bl_idname = "transform.face_towards_tilt"
    bl_label = "Tilt"
        
    def execute(self, context):
        
        tilt_bool = context.scene.my_tool.pinguin_face_target_tilt
        # 1 Get target object        
        target_object = context.scene.my_tool.pinguin_face_target_object
        target_object_location = target_object.location
        # 2 Get all selected objects
        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        # 3 Get object location
            obj_location = obj.location
            obj_normal_vector = get_first_face_normal(obj)
            obj_target_vector = target_object_location - obj_location
            ### Formating the object targer vector into a list
            otv_x, otv_y, otv_z = obj_target_vector
            obj_target_vector_xyz = [otv_x, otv_y, otv_z]
            obj_target_vector_xy = [otv_x, otv_y, 0]
            
        # 4 Get rotation angles
            # *the tilt_angle_radians (this is projected in the rotation plane)
            xy_angle_radians, tilt_angle_radians, azimut_angle_radians = get_align_angle(obj_normal_vector, obj_target_vector)
            
            #Cut operation alltogether if the xy_angle is different from 0
            print(f"if {xy_angle_radians} > {math.radians(1)}")
            if abs(xy_angle_radians) > math.radians(1):
                raise NotFacingTowardsError ("Execute Face Towards operator first")
            
            ### Correct Azimut angle if is below object
            if obj_location[2] < target_object_location [2]:
                azimut_angle_radians *= -1
                tilt_angle_radians *= -1
            
            
            print("\n","_-_------_----_----_-----___--_-_-----","\n"
                , "xy_angle: ", math.degrees(xy_angle_radians), "\n",
                "azimut_angle: ", math.degrees(azimut_angle_radians), "\n",
                "tilt angle: ", math.degrees(tilt_angle_radians), "\n")
            

        # 5 Evaluate if it is facing backwards and correct the angle to be only if it is facing towards our object
            #print(f"Azimut::{math.degrees(azimut_angle_radians)} + Tilt::{math.degrees(tilt_angle_radians)} = {abs(math.degrees(azimut_angle_radians) + math.degrees(tilt_angle_radians))}")
            
            if abs(xy_angle_radians) > (math.pi/2):
                #print("is facing backwards")
                # print("tar", math.degrees(tilt_angle_radians))
            ## check rotation direction to tilt angle to calculate the tilt angle in the range [0,360] currently [0,180] because of the dot product/cos_angle
                #print("obj_target_vector",obj_target_vector_xyz)
                obj_target_vector_flipped_normalized = normalize_vector(flip_vector(obj_target_vector_xyz))
            ## Compare z components of the obj_target_vector_flipped_normalized vs the object normal vector projected (this is projected in the rotation plane)
                
                projected_obj_normal_vector_onto_target_plane = normalize_vector(project_vector_onto_plane(obj_normal_vector,obj_target_vector_xyz, obj_target_vector_xy))
                z_tar = projected_obj_normal_vector_onto_target_plane[2]
                z_otvfn = obj_target_vector_flipped_normalized[2]
                #print("z_tar", z_tar, "z_otvfn", z_otvfn)
            
                if abs(z_otvfn) > abs(z_tar):
                # Transform axis to a 360 degree rotation format
                    #print("wheee have to format the angel wheee: ",math.degrees(tilt_angle_radians))
                    if tilt_angle_radians < 0:
                        tilt_angle_radians = (-2*math.pi) - tilt_angle_radians
                    elif tilt_angle_radians > 0:
                        tilt_angle_radians = (2*math.pi) - tilt_angle_radians
                    #print("now formated", math.degrees(tilt_angle_radians))
                
                # Correct rotation direction (pendin)
                tilt_angle_radians_after_xy_alignment = ((math.pi) + (2 * abs(azimut_angle_radians)) - abs(tilt_angle_radians))
                tilt_angle_radians = tilt_angle_radians_after_xy_alignment
            
            print("5 tilt_angle_radians after xy alignment:", math.degrees(tilt_angle_radians))    
        # 6 Get rotation axis
            rotation_axis_tilt = normalize_vector(cross_product_3d(obj_target_vector_xyz, obj_target_vector_xy))   
            # print("6 rotation axis tilt: ",rotation_axis_tilt)
            
        # 7 Analize and correct tilt angle direction
            # Define the rotation angle in radians
            obj_target_vector_norm = normalize_vector(obj_target_vector_xyz)
            # pnj_normal_vector is already normalized
            
            print(f"if {obj_target_vector_norm[2]} > {obj_normal_vector[2]}")
            if obj_target_vector_norm[2] > obj_normal_vector[2]:
                print(f"i  have to rotate up by {math.degrees(tilt_angle_radians)}")
                rotation_angle_radians = tilt_angle_radians
            elif  obj_target_vector_norm[2] < obj_normal_vector[2]:
                print(f"i have to rotate down nou {math.degrees(tilt_angle_radians)}")
                rotation_angle_radians = tilt_angle_radians * -1
            
        # 8 Rotate tilt  using quaternions
            # Create the quaternion rotation
            quaternion_rotation = Quaternion(rotation_axis_tilt, rotation_angle_radians)
            # Apply the rotation to the object
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = quaternion_rotation
            
            
        if True: 
            print("Tilt Working")  
                
        return{"FINISHED"}

### PANELS ###
class VIEW_PT_pinguin_create(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pinguin"
    bl_label = "Cutout to Mesh"

    def draw(self, context):
        col = self.layout.column()
        
        #Execute Button
        col.operator("mesh.png_to_mesh",
            text="Create",
            icon="MONKEY")
        col.scale_y = 2.0 
    
        col = self.layout.column(align=True)
        row = col.row(align=False)
        col.prop(context.scene.my_tool, "pinguin_folder")
        row.scale_x = .5
        
        col = self.layout.column(align=True)
        row = col.row(align=True)
        row.prop(context.scene.my_tool, "pinguin_vertical_orient")
        row.prop(context.scene.my_tool, "pinguin_holes")
        col.prop(context.scene.my_tool, "pinguin_mesh_height")
        row = col.row(align=True)    
        row.prop(context.scene.my_tool, "pinguin_cv_algorithm")

class VIEW_PT_facetowards(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pinguin"
    bl_label = "Face Towards"
    
    def draw(self, context):
        col = self.layout.column(align=True)
        col.scale_y = 1.5
        #Execute Button
        col.operator("transform.face_towards",
            text="Face Towards",
            icon="LIGHT_AREA")
        col.operator("transform.face_towards_tilt",
            text="Tilt",
            icon="DRIVER_ROTATIONAL_DIFFERENCE")
        
        
        col = self.layout.column(align=True)
        row = col.row(align=False)
        row.prop(context.scene.my_tool, "pinguin_face_target_object",   text="")
        
        """
        row.scale_x = .4
        row.prop(context.scene.my_tool, "pinguin_face_target_tilt",   text="Tilt")
        """
### FUNCTIONS ### 

### Here all the custom functions for the main program
### def_returns list of pngs in folder
def image_png_paths(dir):

    files_in_directory = os.listdir(dir)
    image_paths = []
    number_of_pngs = 0
    number_of_files = 0

    for image_png_name in files_in_directory:
        if str(image_png_name).endswith(".png"):            
            image_path = dir + "/" + image_png_name
            image_paths.append(image_path)

            number_of_pngs += 1
            number_of_files += 1
        else:
            number_of_files += 1
            pass

    ###print("pngs found:", number_of_pngs, "of", number_of_files,"files\n")
    return image_paths 

### def_Creates new paths based in original, and avoids creating a path with dupplicate suffix and filetype
def image_result_path(original_path, suffix, filetype):

    image_result_paths = []
    new_valid_pngs = 0
    
    for img_path_result in original_path:
        ### Condicion evita que un archivo con el sufijo de opacidad sea procesado redundantemente
        if img_path_result.endswith(suffix + filetype):
            pass
        else:
            img_path_result = img_path_result.strip(filetype)
            img_path_result += suffix + filetype
            image_result_paths.append(img_path_result)
            new_valid_pngs += 1

    return image_result_paths

### def_Reads original png and outputs and writes a Alpha channel mask
def image_opacity_map(img_list, suffix, filetype):

    image_opc_list = []

    for img_path in img_list:
        ### Condicion evita que un archivo con el sufijo de opacidad sea procesado redundantemente
        if img_path.endswith(suffix + filetype):
            pass
        else:
            img = Image.open(img_path).convert("RGBA")
            img = img.getchannel("A")
            image_opc_list.append(img)

    return image_opc_list

### def_writes set of images as a given result path lists
def save_batch_png(pil_image_list, result_path_list):
    
    list_index = 0

    for pil_image in pil_image_list:
        pil_image.save(result_path_list[list_index])
        list_index += 1

### def_uses Computer Vision to turn an alpha channel into its outermost contours
def alpha_channel_to_contour(opacity_map, algorithm_set_toogle):   

    ### Procesa el contorno
    ### Aplica un blur para suavisarlo pero tambien para usar un mayor umbral(Thresh) y contraer el contorno
    image_opacity_contour = cv.imread(opacity_map)
    blur = cv.blur(image_opacity_contour,(5,5))
    gray = cv.cvtColor(blur, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, 127, 255, cv.THRESH_BINARY) #200 for contract #100 For expand ###200-Contrats
    ### Decide que algoritmo usar para encontrar contornos    
    if "SIMPLE" in algorithm_set_toogle:
        contours, hierarchies = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE) ### Cambiar CHAIN_APROX_NONE o CHAIN_APPROX_SIMPLE
    elif "NONE" in algorithm_set_toogle:
        contours, hierarchies = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_NONE) ### Cambiar CHAIN_APROX_NONE o CHAIN_APPROX_SIMPLE 
    ###Extrae las dimensiones 
    dimensions = image_opacity_contour.shape
        
    return contours, hierarchies, dimensions   

### def _Formats nparrya(contours) into simpler list 
def format_contour_to_list(np_contours):
    list_contours = []
    for nparr_contour in np_contours:
        nparr_contour = nparr_contour.tolist()
        nparr_contour = [inner_lst[0] for inner_lst in nparr_contour]

        list_contours.append(nparr_contour)  
    return list_contours

### def_Takes a list of 3d points [[x,y,z]] and averages its position returning a list of same legnth of those points smoothed
def point_rolling_average(points, window=3):

    ### Base point list
    list_lenght = len(points)

    ###List of base lists shifted each time once and picked first 3 items
    window_lists = []

    for point_co in range(list_lenght):
        window_lists.append(points[0:window])
        shift = points[1:] + points[:1]
        points = shift
        
    ### Average each list to a single a point
    average_points = []

    for point_window in window_lists:
        
        average_point_ = []
        x_values = []
        y_values = []
        z_values = []

        x_average = 0
        y_average = 0
        z_average = 0

        for point in point_window:
            try:
                x_values.append(point[0])
            except:
                x_values.append(0)
        
            try:
                y_values.append(point[1])
            except:
                y_values.append(0)

            try:
                z_values.append(point[2])
            except:
                z_values.append(0)    

        try:    
            x_average = statistics.mean(x_values)
            y_average = statistics.mean(y_values)
            z_average = statistics.mean(z_values)
        except:
            pass
        
        average_point_ = [round(x_average,2), round(y_average,2), round(z_average,2)]
        average_points.append(average_point_)

    return average_points

### def_Takes a list of 3d points [[x,y,z]] and scales them using a desired factor 
def scale_contour(scontours, scale_desired_factor):
    scaled_vertex_list = [[scale_desired_factor * x, scale_desired_factor * y, scale_desired_factor * z] for x, y, z in scontours]
    return scaled_vertex_list

### def_Creates a valid lists of edges for blender API to create meshes
def get_edges(contours_list):    
    edges_ = []
    for vertex_set in contours_list:
        edge_ = [] 
        end_vert = len(vertex_set)
        start_vert = 0
        next_vert = 1
        for vert in vertex_set:
            if next_vert < end_vert:
                edge_.append([start_vert, next_vert])
                start_vert += 1
                next_vert += 1
            else:
                edge_.append([(end_vert-1),0])
        edges_.append(edge_)
    return edges_   

### def_Creates a valid list of faces for blender API to create meshes _ not always works
def get_faces(contours_list):
    mesh_face = []
    faces =[]
    for vertex_set in contours_list:
        face = list(range(len(vertex_set)))
        faces.append(face)
        mesh_face = [[sublist] for sublist in faces]
    return mesh_face

### def_dimensions to extent vertices
def dim_to_extent_verts(dimension):   
    d_width = dimension[0]
    d_height = dimension[1]
    extents = [[0,0,0],[0,d_width,0],[d_height,0,0],[d_height,d_width,0]]
    return extents

### def_toma la informacion de vertices aristas y caras y produce las mallas
def mesh_from_contours_info(verts_set = [], 
                            edges_set = [], 
                            extent_set = [],
                            mesh_name = "file_has_no-name"):

    object_set = []
    extents_edges = [[0,1],[1,3],[3,2],[2,0]]
    
    ### Deselect all selected objects in the scene
    bpy.ops.object.select_all(action='DESELECT')
        
    ### Creates extents vertices 
    ext_mesh_data = bpy.data.meshes.new(mesh_name)
    ext_mesh_data.from_pydata(extent_set, [], [])
    ext_mesh_data.update()
    ext_obj = bpy.data.objects.new(mesh_name, ext_mesh_data)

    scene = bpy.context.scene
    scene.collection.objects.link(ext_obj)
    
    """
    ### Creates Face fpr the extent object
    bpy.context.view_layer.objects.active = ext_obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.editmode_toggle()
    """

    ### Creates each contour into a mesh with objects
    for contours_index in range(len(verts_set)):
        
        try:
            each_vert = verts_set[contours_index]
        except:
            print("no vertices recognized")
            
        try:
            each_edge = edges_set[contours_index]
        except:
            each_edge = []
            
        mesh_data = bpy.data.meshes.new(mesh_name+" mesh") 
        mesh_data.from_pydata(each_vert, each_edge, [])
        mesh_data.update()
        obj = bpy.data.objects.new(mesh_name+" mesh", mesh_data)
        object_set.append(obj)

    ### Selects each object in the object_set
    for object in object_set:        
        scene.collection.objects.link(object)
        object.select_set(True)

    
    ### Sets the las object to active and joins the selection
    bpy.context.view_layer.objects.active = obj
    if len(object_set) > 1:
        bpy.ops.object.join()

    
    ### Face from contour edges
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.editmode_toggle()
    
    ### Join Objects and Extents
    ext_obj.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = ext_obj    
    bpy.ops.object.join()
    
    ### Flips Object because for some reason the mesh is reflected and aplies transforms
    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.editmode_toggle()
    
    # Sets the origin to the lowest y vertex by Set the location of the 3D cursor to the desired coordinate   
    lower_x, lower_y, lower_z = extent_set[1]
    bpy.context.scene.cursor.location = (0,(lower_y*(-1)),0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    
    ### WHAAAT OMG! - Creates Uvs from extents 
    me_ext_obj = ext_obj.data
    bm = bmesh.new()
    bm.from_mesh(me_ext_obj)
    #bm = bmesh.from_edit_mesh(me)
    x, y, z = np.array([v.co for v in bm.verts]).T
    S = Matrix.Diagonal(
        ( 1 / (x.max() - x.min()),
        1 / (y.max() - y.min()))
        )
    uv_layer = bm.loops.layers.uv.verify()
    
    # adjust uv coordinates
    for face in bm.faces:
        for loop in face.loops:
            loop_uv = loop[uv_layer]
            # use xy position of the vertex as a uv coordinate
            loop_uv.uv = S @ loop.vert.co.xy

    bm.to_mesh(me_ext_obj)
    me_ext_obj.update()
    
    ### Succesfull Finished this shite - Letsss goooo 
    print(mesh_name, "succesfully converted")

### def_creates a material for each mesh
def material_to_mesh(mesh_name, directory): 
    
    ob = bpy.context.active_object
    
    # Get material
    mat = bpy.data.materials.get(mesh_name)
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name=mesh_name)
        pass
    
    # Assign it to object    
    if ob.data.materials:
        # assign to 1st material slot
        ob.data.materials[0] = mat
    else:
        # no slots
        ob.data.materials.append(mat)
    
    # Toogle use Nodes
    mat.use_nodes = True
    
    # Adds Principled Bsdf        
    # Get the material node tree and # Clear all nodes
    tree = mat.node_tree    
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    # Create a Principled BSDF node and add it to the node tree
    principled_bsdf_node = tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf_node.inputs['Specular'].default_value = 0.0
    principled_bsdf_node.inputs['Roughness'].default_value = 0.2

    # Create an Material Output node    
    output_node = tree.nodes.new('ShaderNodeOutputMaterial')
    output_node.location = (300,0)
    
    
    # Create an Image node
    image_node = tree.nodes.new("ShaderNodeTexImage")
    image_node.location = (-300,0)
    
    # Load the image and # Set the image property of the Image node to the loaded image
    original_image_filepath = (directory+"/"+mesh_name+".png") 
    original_image = bpy.data.images.load(original_image_filepath)    
    image_node.image = original_image
    
    """
    aca esta creando una imagen nueva en el archivo cada vez que corre el programa a pesar de no reconectar
    el mismo material, toca resolver esto
    """
    
    tree.links.new(principled_bsdf_node.outputs[0], output_node.inputs[0])
    tree.links.new(image_node.outputs[0], principled_bsdf_node.inputs[0])
    tree.links.new(image_node.outputs[1], principled_bsdf_node.inputs[21])

### def_talkes all objects and arrays them in a grid based in the widest obj    
def organize_objects(collection_objs):
    
    x_location,y_location,z_location = bpy.context.scene.cursor.location
    ox_location = x_location

    number_in_row = 0
    collection_len = len(collection_objs.objects)
    collection_row_len = round(math.sqrt(collection_len))
    
    x_dim_list_width = []
    y_dim_list_height = []
    
    # Loop through all objects in the collection and picks the largest dimensions to create an non-overlaping array
    for obj in collection_objs.objects:
                
        obj.select_set(True)
        obj_dim = obj.dimensions
        x_len, y_len, z_len = obj_dim
        
        x_dim_list_width.append(x_len)
        y_dim_list_height.append(y_len)
        
    x_len = max(x_dim_list_width)
    y_len = max(y_dim_list_height)
    
    #Moves each object to a position in the array  
    for obj in collection_objs.objects:
        
        obj.location = (x_location, y_location, z_location)        
        x_location = x_location + (x_len*1.1)
        
        number_in_row +=  1
        
        if number_in_row > collection_row_len:
            y_location = y_location + (y_len*1.1)
            x_location = ox_location  
            number_in_row = 0

### def_ gets the firs indexd normal of any given mesh
def get_first_face_normal(obj):
    if obj.type == 'MESH':
        mesh = obj.data
    # Ensure the mesh has polygons
    if mesh.polygons:
        # Get the first face (polygon)
        face = mesh.polygons[0]
        # Get the normal vector of the face
        normal = face.normal
        # Print the normal vector
        return normal
    
    # Implement
    if obj.type == "CAMERA":
        print("camera facing not yet implemented, coming soon!")
    
### def 
def get_align_angle(normal_vector, target_vector):
    
    x_normal, y_normal, z_normal = normal_vector
    x_target, y_target, z_target = target_vector

### 1.1 Calculate the rotation angle using the dot product
    # Calculate the dot product of the vectors in the XY plane
    dot_product = x_normal * x_target + y_normal * y_target
    # Calculate the magnitudes of the projected vectors 
    magnitude1 = math.sqrt(x_normal ** 2 + y_normal ** 2)
    magnitude2 = math.sqrt(x_target** 2 + y_target ** 2)
    # Calculate the cosine of the angle using the dot product and magnitudes
    try:
        cos_angle = dot_product / (magnitude1 * magnitude2)
    #This handles the perpendicular orientation error
    except ZeroDivisionError:
        print("cannot orient, face normal is directly perpendicular to object-target_vector")
        raise PerpendicularOrientError("cannot orient, face normal is directly perpendicular to object-target_vector")
    # 3 Rotate on xy plane  
    # Catch oput of range error
    if cos_angle < -1:
        cos_angle = -1
    elif cos_angle > 1:
        cos_angle = 1
    # Calculate the angle using the arccosine function
    xy_angle_radians = math.acos(cos_angle)    
    
### 1.2 Calculate the direction of rotation using the cross product sign
    cross_product = x_normal * y_target - y_normal * x_target
    if cross_product < 0:
        xy_angle_radians *= -1   
    
### 2.1Calculate Azimut (angle)
    # Calculate the dot product of the vectors in the XY plane
    dot_product_azimut = x_target * x_target + y_target * y_target + z_target * 0
    # Calculate the magnitudes of the projected vectors 
    magnitude1_azimut = math.sqrt(x_target ** 2 + y_target ** 2 + z_target **2)
    magnitude2_azimut = math.sqrt(x_target ** 2 + y_target ** 2)
    # Calculate the cosine of the angle using the dot product and magnitudes
    cos_angle_azimut = dot_product_azimut / (magnitude1_azimut * magnitude2_azimut)
    # Catch oput of range error
    if cos_angle_azimut < -1:
        cos_angle_azimut = -1
    elif cos_angle_azimut > 1:
        cos_angle_azimut = 1
    azimut_angle_radians = math.acos(cos_angle_azimut)

### 3.1 Project normal vector into target vector plane
    # Construct vectors
    target_vector__xy = [target_vector[0], target_vector[1], 0]
    #reformat vectors
    normal_vector = [x_normal, y_normal, z_normal] 
    target_vector = [x_target, y_target, z_target]
    ### project
    normal_vector_onto_target_plane = project_vector_onto_plane(normal_vector, target_vector, target_vector__xy)
### Calculate tilt angle
# Solve this shite, learn bout quaternions
# 3Blue1Brown on quaternions: https://www.youtube.com/watch?v=zjMuIxRvygQ&t=353s
    
    x_nvotp, y_nvotp, z_nvotp = normal_vector_onto_target_plane
    # Calculate the dot product of the vectors
    dot_product_tilt = x_nvotp * x_target + y_nvotp * y_target + z_nvotp * z_target
    # Calculate the magnitudes of the projected vectors 
    magnitude1_tilt = math.sqrt(x_nvotp ** 2 + y_nvotp ** 2 + z_nvotp ** 2)
    magnitude2_tilt = math.sqrt(x_target** 2 + y_target ** 2 + z_target ** 2)
    # Calculate the cosine of the angle using the dot product and magnitudes
    cos_angle_tilt = dot_product_tilt / (magnitude1_tilt * magnitude2_tilt)
        # Catch oput of range error
    if cos_angle_tilt < -1:
        cos_angle_tilt = -1
    elif cos_angle_tilt > 1:
        cos_angle_tilt = 1
    # Calculate the angle using the arccosine function
    tilt_angle_radians = math.acos(cos_angle_tilt)
    
    return xy_angle_radians, tilt_angle_radians, azimut_angle_radians
    

def project_vector_onto_plane(vector_to_project, vector1, vector2):
    # Avoids the same vector zero div error given that we 
    # are always projecting into a vertical plane
    if vector1 == vector2:
        vector2[2] += 1
    # Calculate the normal vector of the plane
    normal_vector = cross_product_3d(vector1, vector2)
    # Normalize the normal vector
    normal_vector_normalized = normalize_vector(normal_vector)
    
    dot_product_proj = dot_product(vector_to_project, normal_vector_normalized)
    #Projected vector = a - dot(a, n) * n
    projected_vector = []
    for i in range(len(vector_to_project)): 
        projected_vector.append(vector_to_project[i] - dot_product_proj * normal_vector_normalized[i])
        
    return projected_vector

def cross_product_3d(vector1, vector2):
    if vector1 == vector2:
        vector2[2] += 1
    #### algo oscuro esta pasando aca
    """
    print( f"x = {vector1[1]} * {vector2[2]} - {vector1[2]} * {vector2[1]}")
    print( f"y = {vector1[2]} * {vector2[0]} - {vector1[0]} * {vector2[2]}")
    print( f"z = {vector1[0]} * {vector2[1]} - {vector1[1]} * {vector2[0]}")
    """
    x = vector1[1] * vector2[2] - vector1[2] * vector2[1]
    y = vector1[2] * vector2[0] - vector1[0] * vector2[2]
    z = vector1[0] * vector2[1] - vector1[1] * vector2[0]
    return [x, y, z]

def normalize_vector(vector):
    x, y, z = vector
    magnitude = math.sqrt(x**2 + y**2 + z**2)
    normalized_vector = (x / magnitude, y / magnitude, z / magnitude)
    return normalized_vector

def dot_product(vector1, vector2):
    if len(vector1) != len(vector2):
        raise ValueError("Both vectors must have same number of components. dot_product()")
    result = 0
    for i in range(3):
        result += vector1[i] * vector2[i]
    return result

def flip_vector(vector):
    return [-coord for coord in vector]

def reset_world_matrix(obj):
    
    print("reseting")
    ### Store object_location
    obj_location = obj.location
    obj_x, obj_y, obj_z = obj_location
    
    ### Move object to world origin
    obj.location = (0,0,0)
    
    ### Ctrl A  --- Apply transforms
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    
    ### Return object to original location
    obj.location = (obj_x, obj_y, obj_z)


### Blender_ Register and Unregister Classes   
def register():
    bpy.utils.register_class(MESH_OT_pinguin_create)
    bpy.utils.register_class(TRANSFORM_OT_face_towards)
    bpy.utils.register_class(TRANSFORM_OT_face_towards_tilt)
    bpy.utils.register_class(VIEW_PT_pinguin_create)
    bpy.utils.register_class(VIEW_PT_facetowards)
    bpy.utils.register_class(PinguinProperties)
    
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type = PinguinProperties)
    
def unregister():
    bpy.utils.unregister_class(MESH_OT_pinguin_create)
    bpy.utils.unregister_class(TRANSFORM_OT_face_towards)
    bpy.utils.unregister_class(TRANSFORM_OT_face_towards_tilt)
    bpy.utils.unregister_class(VIEW_PT_pinguin_create)
    bpy.utils.unregister_class(VIEW_PT_facetowards)
    bpy.utils.unregister_class(PinguinProperties)   

    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()