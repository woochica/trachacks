#!/usr/bin/env python

from PIL import Image

def crop_resize(image, size):
    """crop out the proportional middle of the image and set to the desired size"""
    assert size[0] or size[1]

    size = list(size)

    if size[0] > image.size[0]:
        return image
    if size[1] > image.size[1]:
        return image

    image_ar = image.size[0]/float(image.size[1])
    crop = not size[0] or not size[1]
    if not size[1]:
        size[1] = int(image.size[1]*size[0]/float(image.size[0]) )
    if not size[0]:
        size[0] = int(image.size[0]*size[1]/float(image.size[1]) )
    size_ar = size[0]/float(size[1])
                
    if crop:
        if image_ar > size_ar:
            # trim the width
            xoffset = int(0.5*(image.size[0] - size_ar*image.size[1]))
            image = image.crop((xoffset, 0, image.size[0]-xoffset, image.size[1]))
        elif image_ar < size_ar:
            # trim the height
            yoffset = int(0.5*(image.size[1] - image.size[0]/size_ar))
            image = image.crop((0, yoffset, image.size[0], image.size[1] - yoffset))

    return image.resize(size, Image.ANTIALIAS)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-f', '--file')
    parser.add_option('-w', '--width')
    parser.add_option('-e', '--height')
    (options, args) = parser.parse_args()

    assert options.file

    i = Image.open(options.file)
    new_image = crop_resize(i, (int(options.width), int(options.height)))
    new_image.show()
