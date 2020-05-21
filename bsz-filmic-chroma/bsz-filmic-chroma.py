#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use these for reference on gegl operations and their properties/inputs/outputs.
http://www.gegl.org/operations/
https://gitlab.gnome.org/GNOME/gegl/-/tree/master/operations

Also build the .gir files using g-ir-doc-tool for additional insight.
If the docs don't have a description on something like class methods,
run python's help() on it to view it in the terminal.
Requires having a debug term open in gimp obvs
"""

# Uncomment as needed.
# I don't actually know if it's faster to not import some of the gi repo stuff
# since it probably gets imported later anyway ...right?
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
# gi.require_version('Babl', '0.1')
# from gi.repository import Babl
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
# import bszgw
from bsz_gimp_lib import PlugIn, ParamNumber

import numpy


# Main function.
def filmic_chroma(image, drawable, scale, offset):
    # {{{
    # Fairly certain mask_intersect() is the current selection mask
    intersect, x, y, width, height = drawable.mask_intersect()
    if intersect:
        # start Gegl
        Gegl.init(None)
        # fetch main buffer
        buff = drawable.get_buffer()

        # fetch shadow aka "temp" buffer
        shadow = drawable.get_shadow_buffer()

        rect = Gegl.Rectangle.new(x, y, width, height)

        # get pixel bytes
        pixels = bytearray(buff.get(rect, 1.0, "CIE LCH(ab) alpha double",
                           Gegl.AbyssPolicy.CLAMP))

        # scale base of 100. Since it's divided later, it's also divided here
        # so effect decreases with lower vals
        scale = 100 / scale
        offset = 1 + offset

        # interpret the bytearray as floats (doubles)
        np_array = numpy.frombuffer(pixels, dtype=float)
        # [::4] == for every 4 elements in the array do this
        # [1::4] picks the 2nd, chroma in this case
        # later, [::4] is iterating the array in the same 'steps',
        # picking the 1st element, lightness in this case.
        # *= modifies in-place. I guess it automatically transfers through
        # frombuffer to directly modify pixels bytearray?
        # tl;dr new to the numpy black magic, StackOverflow showed the way.
        np_array[1::4] *= offset - np_array[0::4] / scale

        shadow.set(rect, "CIE LCH(ab) alpha double", bytes(pixels))

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()
        # }}}


# Preview function. Just runs the same thing on a copy
def filmic_chroma_preview(image, drawable, *args):
    # {{{
    preview_layer = drawable.copy()
    image.insert_layer(preview_layer, None, 0)
    filmic_chroma(image, preview_layer, *args)
    return preview_layer
    # }}}


# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Filmic Chroma",  # name
    filmic_chroma,    # function
    ParamNumber("Scale", 1, 0.1, 1, ui_step=0.1),
    ParamNumber("Offset", 0.25, 0, 1, ui_step=0.1),
    description="Reduces chroma based on intensity.\n"
    "Inspired by the 'Filmic' tonemapper in Blender.",
    images="RGB*",
    preview_function=filmic_chroma_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
