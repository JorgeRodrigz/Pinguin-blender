import bpy
from mathutils import Quaternion
import math

# Set the active object
obj = bpy.context.active_object

# Define the rotation angle in radians
rotation_angle_degrees = 10

# Define the rotation axis as a normalized vector
rotation_axis = (0.0, 0.0, 1.0)

# Create the quaternion rotation
quaternion_rotation = Quaternion(rotation_axis, math.radians(rotation_angle_degrees))

# Apply the rotation to the object
obj.rotation_mode = 'QUATERNION'
obj.rotation_quaternion = quaternion_rotation

# Update the object to visualize the rotation
obj.update()