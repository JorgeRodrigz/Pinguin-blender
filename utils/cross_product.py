from Pinguin_bl import cross_product_3d
import math

def main():
    
    v1 = [-1.0,0.0,1.0]
    v2 = [-1.0,0.0,0.0]
    print(cross_product_3d(v1,v2))

    print(math.radians(360), "=", 2 * math.pi)
    print(math.degrees(math.pi/2))
    
    tilt_angle_radians_after_xy_alignment = ((180) + (2 * abs(45)) - abs(210))
    print("taraxya", tilt_angle_radians_after_xy_alignment)
if __name__ == "__main__":
    main()