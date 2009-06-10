#!/usr/bin/env python

def crop_resize(image, width, height):
    """crop out the proportional middle of the image and set to the desired size"""
    assert width or height
    image_ar = image.size[0]/float(image.size[1])
    if not height:
        height = int(image.size[1]*width/float(image.size[0]) )
    if not width:
        width = int(image.size[0]*height/float(image.size[1]) )
    size_ar = width/float(height)
                
    if image_ar > size_ar:
        # trim the width
        xoffset = int(0.5*(image.size[0] - size_ar*image.size[1]))
        image = image.crop((xoffset, 0, image.size[0]-xoffset, image.size[1]))
    elif image_ar < size_ar:
        # trim the height
        yoffset = int(0.5*(image.size[1] - image.size[0]/size_ar))
        image = image.crop((0, yoffset, image.size[0], image.size[1] - yoffset))

    return image.resize((width, height))

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-f', '--file')
    parser.add_option('-w', '--width')
    parser.add_option('-e', '--height')
    (options, args) = parser.parse_args()

    assert options.file

    from PIL import Image
    i = Image.open(options.file)
    new_image = crop_resize(i, int(options.width), int(options.height))
    new_image.show()
