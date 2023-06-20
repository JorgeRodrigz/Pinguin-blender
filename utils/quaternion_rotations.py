import bpy
from math import radians
from mathutils import Quaternion

### Establecer la rotacion
q = Quaternion((1, 1, 1), radians(45))

##objeto seleccionado
obj = bpy.context.object

#store current location
obj_location = obj.location
obj_x, obj_y, obj_z = obj_location

### Reubicamos y reseteamos la ubicacion del cubo
obj.location = (0,0,0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

### Rotamos usando cuaterniones y reseteamos la matriz 
obj.matrix_world = q.to_matrix().to_4x4() @ obj.matrix_world
bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

### Relocate object in original location
obj.location = (obj_x, obj_y, obj_z)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

print("A",obj.matrix_world)