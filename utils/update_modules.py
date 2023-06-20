def update_pinguin_modules():
    import subprocess
    import sys
    
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
    