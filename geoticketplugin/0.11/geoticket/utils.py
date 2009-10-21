#!/usr/bin/env python
"""
utilities that can/should be abstracted more generally
"""

from math import pi, sin, cos

def colors(parts, hexcode=False):
    """
    return a number of colors spaced evenly apart on the color wheel
    """

    nums = [ 3.*i/parts for i in range(parts) ]
    quads = [ (int(i), i - int(i)) for i in nums ]
    colors = []

    mapping = { 0 : [0,1], # RG
                1 : [1,2], # GB
                2 : [2,0], # BR
                }

    for quad, fraction in quads:
        x, y = cos(0.5*pi*fraction), sin(0.5*pi*fraction)
        color = [ 0 for i in range(3) ]
        color[mapping[quad][0]] = x
        color[mapping[quad][1]] = y
        colors.append(color)

    if hexcode:
        colors = [ [ int(255*x) for x in color] for color in colors ]
        colors = [ '#%02X%02X%02X' % tuple(color) for color in colors ] 

    return colors


if __name__ == '__main__':
    n = 4
    print colors(n, True)
