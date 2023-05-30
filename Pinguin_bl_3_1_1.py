bl_info = {
    "name": "Pinguin",
    "author": "Jorge Rodriguez <jorgeandresarq+dev@gmail.com>",
    "version": (3, 1, 1),
    "blender": (2, 80, 0),
    "location": "Operator Search",
    "description": "Takes cutout images(png format) and turns them into a mesh in the 3D Space",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
import bmesh
import sys  
import os
import subprocess
import time
import math
import statistics
from mathutils import (Matrix,Vector)

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
try:
    from PIL import Image 
    print("Pillow module found")
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',"Pillow"])
    from PIL import Image 
    print("Pillow module installed and imported")
try:    
    import cv2 as cv
    print("Open-cv module found") 
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',"opencv-python"])
    import cv2 as cv
    print("Open-cv installed and imported")   
try:    
    import numpy as np 
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',"numpy"])
    import numpy as np 

class PinguinProperties(bpy.types.PropertyGroup):

    pinguin_folder :  bpy.props.StringProperty(
        subtype='DIR_PATH',
        name='Folder',
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
        name = "Orient Vertical", 
        description="Toogle to stand up the meshes",
        default=True
        )
    
    pinguin_cv_algorithm : bpy.props.EnumProperty(
        name = "Contour Algorithm",
        description = "Set the contour search algorithm between a fast one or a presice one",
        items = [("SIMPLE","Fast",""),
                 ("NONE","Detailed","")],
        options = {"ENUM_FLAG"},
        default = {"SIMPLE"}
        )

class MESH_OT_pinguin(bpy.types.Operator):
    """Converts some png cutouts into a mesh"""
    bl_idname = "mesh.png_to_mesh"
    bl_label = "Png to Mesh"

    def execute(self, context):
        
        directory = context.scene.my_tool.pinguin_folder
        mesh_height = context.scene.my_tool.pinguin_mesh_height
        orient_vertical = context.scene.my_tool.pinguin_vertical_orient
        chain_aproximation_method = context.scene.my_tool.pinguin_cv_algorithm

        proxie_collection = "proxie_collection_pinguin"
        final_collection = "Pinguin-Cutout to Mesh"   
       
        opacity_suffix = "_opc"
        vector_suffix = "_poly"

        x_cursor,y_cursor,z_cursor = bpy.context.scene.cursor.location   
        
        start_time = time.time()
        print("👾 Checking directory 👾")
        
        if directory == "":
            raise TypeError("Empty directory")
        elif not os.path.exists(directory):
            raise FileNotFoundError(f"The directory '{directory}' does not exist.")

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

        save_batch_png(opc_images, opc_paths)
        print("🦅 Succesful alpha channel conversion 🐧")


        contours_list=[]
        hierarchy_list=[]
        dimension_list=[]

        for opc_path_ in opc_paths:
            contour,hierarchy,dimensions = alpha_channel_to_contour(opc_path_,chain_aproximation_method)
            contours_list.append(contour)
            hierarchy_list.append(hierarchy)
            dimension_list.append(dimensions)

        formated_images_contours = []
        
        for image_contours_ in contours_list:
            formated = format_contour_to_list(image_contours_)
            formated_images_contours.append(formated)
        
        smoothed_contours = []

        for form_image_contours_ in formated_images_contours:
            this_image_contours = []
            for contour in form_image_contours_:
                this_image_contours.append(point_rolling_average(contour))
            smoothed_contours.append(this_image_contours)

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

        verts_set = scaled_contours

        edge_set = []
        face_set = []

        for vertex_sets in verts_set:
            edges = get_edges(vertex_sets)
            edge_set.append(edges)
            faces = get_faces(vertex_sets)
            face_set.append(faces)

        print("🐦 Verts and Edges and Faces are ready 🦚")

        obj_name_set =[]

        for path in png_paths:
            path = path[len(directory)+1:]
            path = path[:-4]
            obj_name_set.append(path)
            
        extents_set = []

        for dim_index in range(len(dimension_list)):
           
            get_size = dimension_list[dim_index]
            img_height, img_width, duntknowwhatitdoes = get_size
            scale_factor = mesh_height/img_height
            
            extent_verts = dim_to_extent_verts(dimension_list[dim_index])
            extent_verts = scale_contour(extent_verts, scale_factor)
            extents_set.append(extent_verts)
            
        print("🐦 Extents are ready 🦚")
        """
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                override = bpy.context.copy()
                override["area"] = area
                bpy.ops.view3d.view_axis(override, type='TOP', align_active=False) 
                if  area.spaces.active.region_3d.is_perspective:
                    bpy.ops.view3d.view_persportho(override)
        """
        collections = bpy.data.collections
        pinguin_collection_name = proxie_collection
               
        if pinguin_collection_name in collections:
            pinguin_collection = bpy.data.collections.get(pinguin_collection_name)
        else:       
            pinguin_collection = bpy.data.collections.new(pinguin_collection_name)
            bpy.context.scene.collection.children.link(pinguin_collection)       
        
             
        print("🐦 Creating Meshes 🦚", "\n")
        
        
        for image_index in range(len(verts_set)):
            
 
            mesh_from_contours_info(verts_set[image_index], edge_set[image_index], extents_set[image_index], obj_name_set[image_index])
            mesh_name = obj_name_set[image_index]
            material_to_mesh(mesh_name, directory)
            
            selected_object = bpy.context.active_object
            for obj in bpy.context.selected_objects:
                for other_col in obj.users_collection:
                    other_col.objects.unlink(obj)
                if obj.name not in pinguin_collection.objects:
                    pinguin_collection.objects.link(obj) 
                          
        bpy.context.scene.cursor.location = Vector((x_cursor,y_cursor,z_cursor))
        organize_objects(pinguin_collection)
        bpy.ops.object.select_all(action='DESELECT')     

        if orient_vertical:
            for obj in pinguin_collection.objects:
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.transform.rotate(value=math.pi/-2, orient_axis='X')
                bpy.ops.object.select_all(action='DESELECT')    
        
        collections = bpy.data.collections
        final_collection_name = final_collection
               
        if final_collection_name in collections:
            final_pinguin_collection = bpy.data.collections.get(final_collection_name)
        else:       
            final_pinguin_collection = bpy.data.collections.new(final_collection_name)
            bpy.context.scene.collection.children.link(final_pinguin_collection) 
        
        for obj in pinguin_collection.objects:
            for other_col in obj.users_collection:
                other_col.objects.unlink(obj)
            if obj.name not in final_pinguin_collection:
                final_pinguin_collection.objects.link(obj)
                obj.select_set(True)
        bpy.data.collections.remove(pinguin_collection)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nElapsed time: {elapsed_time} seconds 🐧") 
        return{"FINISHED"}

class VIEW_PT_pinguin(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pinguin"
    bl_label = "Cutout to Mesh"

    def draw(self, context):
        col = self.layout.column()
        
        col.operator("mesh.png_to_mesh",
            text="Create",
            icon="MONKEY")
        col.scale_y = 2.0 
       
        col = self.layout.column(align=True)
        col.prop(context.scene.my_tool, "pinguin_folder")

        col = self.layout.column(align=True)
        col.prop(context.scene.my_tool, "pinguin_mesh_height")    
        col.prop(context.scene.my_tool, "pinguin_vertical_orient", toggle = 1)
        row = col.row(align=True)
        row.prop(context.scene.my_tool, "pinguin_cv_algorithm")
        
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

    return image_paths 

def image_result_path(original_path, suffix, filetype):

    image_result_paths = []
    new_valid_pngs = 0
    
    for img_path_result in original_path:
        if img_path_result.endswith(suffix + filetype):
            pass
        else:
            img_path_result = img_path_result.strip(filetype)
            img_path_result += suffix + filetype
            image_result_paths.append(img_path_result)
            new_valid_pngs += 1

    return image_result_paths

def image_opacity_map(img_list, suffix, filetype):

    image_opc_list = []

    for img_path in img_list:
        if img_path.endswith(suffix + filetype):
            pass
        else:
            img = Image.open(img_path).convert("RGBA")
            img = img.getchannel("A")
            image_opc_list.append(img)

    return image_opc_list

def save_batch_png(pil_image_list, result_path_list):
    
    list_index = 0

    for pil_image in pil_image_list:
        pil_image.save(result_path_list[list_index])
        list_index += 1
 
def alpha_channel_to_contour(opacity_map, algorithm_set_toogle):   

    image_opacity_contour = cv.imread(opacity_map)
    blur = cv.blur(image_opacity_contour,(5,5))
    gray = cv.cvtColor(blur, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, 127, 255, cv.THRESH_BINARY) 
    if "SIMPLE" in algorithm_set_toogle:
        contours, hierarchies = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) 
    elif "NONE" in algorithm_set_toogle:
        contours, hierarchies = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE) 
    dimensions = image_opacity_contour.shape
        
    return contours, hierarchies, dimensions   

def format_contour_to_list(np_contours):
    list_contours = []
    for nparr_contour in np_contours:
        nparr_contour = nparr_contour.tolist()
        nparr_contour = [inner_lst[0] for inner_lst in nparr_contour]

        list_contours.append(nparr_contour)  
    return list_contours

def point_rolling_average(points, window=3):

    list_lenght = len(points)

    window_lists = []

    for point_co in range(list_lenght):
        window_lists.append(points[0:window])
        shift = points[1:] + points[:1]
        points = shift
        
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

def scale_contour(scontours, scale_desired_factor):
    scaled_vertex_list = [[scale_desired_factor * x, scale_desired_factor * y, scale_desired_factor * z] for x, y, z in scontours]
    return scaled_vertex_list

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

def get_faces(contours_list):
    mesh_face = []
    faces =[]
    for vertex_set in contours_list:
        face = list(range(len(vertex_set)))
        faces.append(face)
        mesh_face = [[sublist] for sublist in faces]
    return mesh_face

def dim_to_extent_verts(dimension):   
    d_width = dimension[0]
    d_height = dimension[1]
    extents = [[0,0,0],[0,d_width,0],[d_height,0,0],[d_height,d_width,0]]
    return extents

def mesh_from_contours_info(verts_set = [], edges_set = [], extent_set = [],mesh_name = "file_has_no-nam"):

    object_set = []
    extents_edges = [[0,1],[1,3],[3,2],[2,0]]
     
    bpy.ops.object.select_all(action='DESELECT')
        
    ext_mesh_data = bpy.data.meshes.new(mesh_name)
    ext_mesh_data.from_pydata(extent_set, [], [])
    ext_mesh_data.update()
    ext_obj = bpy.data.objects.new(mesh_name, ext_mesh_data)

    scene = bpy.context.scene
    scene.collection.objects.link(ext_obj)
    
    """
    bpy.context.view_layer.objects.active = ext_obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.editmode_toggle()
    """

    for contours_index in range(len(verts_set)):
        
        try:
            each_vert = verts_set[contours_index]
        except:
            sys.exit("no vertices recognized")
            
        try:
            each_edge = edges_set[contours_index]
        except:
            each_edge = []
            
        mesh_data = bpy.data.meshes.new(mesh_name+" mesh") 
        mesh_data.from_pydata(each_vert, each_edge, [])
        mesh_data.update()
        obj = bpy.data.objects.new(mesh_name+" mesh", mesh_data)
        object_set.append(obj)

    for object in object_set:        
        scene.collection.objects.link(object)
        object.select_set(True)

    
    bpy.context.view_layer.objects.active = obj
    if len(object_set) > 1:
        bpy.ops.object.join()

     
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.editmode_toggle()
    
    ext_obj.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = ext_obj    
    bpy.ops.object.join()
    
    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.editmode_toggle()
    
    lower_x, lower_y, lower_z = extent_set[1]
    bpy.context.scene.cursor.location = (0,(lower_y*(-1)),0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    
    me_ext_obj = ext_obj.data
    bm = bmesh.new()
    bm.from_mesh(me_ext_obj)
    x, y, z = np.array([v.co for v in bm.verts]).T
    S = Matrix.Diagonal(
        ( 1 / (x.max() - x.min()),
          1 / (y.max() - y.min()))
          )
    uv_layer = bm.loops.layers.uv.verify()
    
    for face in bm.faces:
        for loop in face.loops:
            loop_uv = loop[uv_layer]
            loop_uv.uv = S @ loop.vert.co.xy

    bm.to_mesh(me_ext_obj)
    me_ext_obj.update()
    
    print(mesh_name, "succesfully converted")

def material_to_mesh(mesh_name, directory): 
    
    ob = bpy.context.active_object
    
    mat = bpy.data.materials.get(mesh_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mesh_name)
        pass
    
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    
    mat.use_nodes = True
    
    tree = mat.node_tree    
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    principled_bsdf_node = tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf_node.inputs['Specular'].default_value = 0.0
    principled_bsdf_node.inputs['Roughness'].default_value = 0.2

    output_node = tree.nodes.new('ShaderNodeOutputMaterial')
    output_node.location = (300,0)
    
    
    image_node = tree.nodes.new("ShaderNodeTexImage")
    image_node.location = (-300,0)
    
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

def organize_objects(collection_objs):
    
    x_location,y_location,z_location = bpy.context.scene.cursor.location
    ox_location = x_location

    number_in_row = 0
    collection_len = len(collection_objs.objects)
    collection_row_len = round(math.sqrt(collection_len))
    
    x_dim_list_width = []
    y_dim_list_height = []
    
    for obj in collection_objs.objects:
                
        obj.select_set(True)
        obj_dim = obj.dimensions
        x_len, y_len, z_len = obj_dim
        
        x_dim_list_width.append(x_len)
        y_dim_list_height.append(y_len)
        
    x_len = max(x_dim_list_width)
    y_len = max(y_dim_list_height)
   
    for obj in collection_objs.objects:
        
        obj.location = (x_location, y_location, z_location)        
        x_location = x_location + (x_len*1.1)
        
        number_in_row +=  1
        
        if number_in_row > collection_row_len:
            y_location = y_location + (y_len*1.1)
            x_location = ox_location  
            number_in_row = 0

    
def register():
    bpy.utils.register_class(MESH_OT_pinguin)
    bpy.utils.register_class(VIEW_PT_pinguin)
    bpy.utils.register_class(PinguinProperties)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type = PinguinProperties)
    
def unregister():
    bpy.utils.unregister_class(MESH_OT_pinguin)
    bpy.utils.unregister_class(VIEW_PT_pinguin)
    bpy.utils.unregister_class(PinguinProperties)   

    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()