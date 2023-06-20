#Yes, there is a formula to project a vector onto a plane. 
# The formula for projecting a vector "a" onto a plane 
# defined by a normal vector "n" is given by:


#Projected vector = a - dot(a, n) * n

#In this formula, "a" is the vector you want to project, 
# "n" is the normal vector of the plane, and dot(a, n) 
# represents the dot product between vectors "a" and "n". 
# The dot product measures the projection of one vector onto another.

#By subtracting the component of "a" that is parallel to 
# the plane (dot(a, n) * n) from "a", you obtain the component 
# of "a" that is orthogonal (perpendicular) to the plane. 
# This resulting vector is the projected vector of "a" onto the plane

import math

def main():
    # Example usage
    vector_to_project = [0, 2, 2]
    vector1 = [1, 1, 1]
    vector2 = [1, 1, 0]

    projected_vector, normal_vector_normalized = project_vector_onto_plane(vector_to_project, vector1, vector2)  
    print(projected_vector)

def project_vector_onto_plane(vector_to_project, vector1, vector2):
    # Calculate the normal vector of the plane
    normal_vector = cross_product_3d(vector1, vector2)
    # Normalize the normal vector
    normal_vector_normalized = normalize_vector(normal_vector)
    
    dot_product_proj = dot_product(vector_to_project, normal_vector_normalized)
    #Projected vector = a - dot(a, n) * n
    projected_vector = []
    for i in range(len(vector_to_project)): 
        projected_vector.append(vector_to_project[i] - dot_product_proj * normal_vector_normalized[i])
        
    return projected_vector, normal_vector_normalized

def cross_product_3d(vector1, vector2):
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
        raise ValueError("Both vectors must have same number of components.")
    result = 0
    for i in range(3):
        result += vector1[i] * vector2[i]
    return result

if __name__ == '__main__':
    main()

