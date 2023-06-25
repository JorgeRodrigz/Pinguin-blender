# What is Pinguin?

Pinguin is a Blender add-on that allows you to create meshes from your image cutouts (currently works only with png format images). By using this feature, you can greatly streamline your post-production workflow, as it eliminates the need to manually adjust the placement, scaling, lighting, and shadowing of your cutouts in external software.

## Adjustments

### Cutout to mesh panel
#### Create
After selecting your settings press this button!

#### Directory
Pick the folder where the cutouts you want to convert are stored. The addon will only process files that are in png format. 

#### Mesh Height
Choose a desired height and the meshes will be generated to match it after converting your images.

#### Orient Vertical 
Toggle to generate meshes in an upright position.

#### Fast / Detailed

This picks the algorithm that interprets the contours of the cutout. 95% of the time the fast algorithm will perform as well as the detailed one, producing a mesh with just the right amount of vertices to capture the silhouette of the image and in less time! However, in some specific cases some edges may shrink noticeably from the original contour, for these occasions you can activate the detailed mode which will solve the 

## License

This program is released under the GNU General Public License v3.0. You can find a copy of the license in the LICENSE file in the root directory of the project.

The GPL is a copyleft license that gives users the freedom to use, modify, and distribute the program and its source code. However, any modifications or derivative works of the program must also be released under the same GPL license. This ensures that the program remains free and open-source for all users.

By using or contributing to this program, you agree to the terms of the GPL license. If you have any questions or concerns about the license, please contact the project maintainers.

## Credits

This program uses the following third-party libraries:

    OpenCV: An open-source computer vision library for image and video processing.
    Pillow: A fork of the Python Imaging Library (PIL) that adds support for opening, manipulating, and saving many different image file formats.

We would like to thank the developers of these libraries for their contributions to the open-source community and for making their work available for others to use and build upon. Without their efforts, this program would not have been possible.