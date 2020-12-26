#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gegl Operation references:
http://www.gegl.org/operations/
https://gitlab.gnome.org/GNOME/gegl/-/tree/master/operations

If on Linux:
$ gegl --list-all
$ gegl --info "operation-name"

Also build the .gir files using g-ir-doc-tool for additional insight.
If the docs don't have a description on something like class methods,
run python's help() on it to view it in the terminal.
"""

# Uncomment as needed.
# I don't actually know if it's faster to not import some of the gi repo stuff
# since it probably gets imported later anyway ...right?
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
import sys
import os.path
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from bsz_gimp_lib import PlugIn, ParamNumber, ParamBool

import time
try:
    from bsz_shared import filmic_chroma as FC
    EXTERN = True
except Exception:
    import struct
    EXTERN = False


# Main function.
def filmic_chroma(image, drawable, scale, offset, invert):
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

        # create working rectangle area using mask intersect.
        rect = Gegl.Rectangle.new(x, y, width, height)

        # scale base of 100. Since it's divided later, it's also divided here
        # so effect decreases with lower vals
        scale = 100 / scale
        offset = 1 + offset

        # many times faster, but needs the shared library. I currently only
        # have Linux and Windows devs setup, so the backup will stay for now
        if EXTERN:
            print("EXTERN BENCHMARK ENGAGE")
            now = time.perf_counter()  # TODO: optimize & remove bench

            pixels = bytearray(buff.get(rect, 1.0, "CIE LCH(ab) alpha double",
                               Gegl.AbyssPolicy.CLAMP))
            FC(scale, offset, invert, pixels)
            shadow.set(rect, "CIE LCH(ab) alpha double", bytes(pixels))

            print(time.perf_counter() - now)

        else:

            pixels = buff.get(rect, 1.0, "CIE LCH(ab) alpha double",
                              Gegl.AbyssPolicy.CLAMP)
            # creates clusters of pixels for unpack. 32 = 8 bytes
            pixels_iter = (pixels[x:x + 32] for x in range(0, len(pixels), 32))
            new_pixels = bytearray()

            for pixel in pixels_iter:
                # convert 4 bytes to 4 doubles
                l, c, h, a = struct.unpack('dddd', pixel)
                if not invert:
                    c *= offset - l / scale
                else:
                    c *= offset - (100 - l) / scale
                new_pixels += struct.pack('dddd', l, c, h, a)

            shadow.set(rect, "CIE LCH(ab) alpha double", bytes(new_pixels))

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
    ParamNumber("Scale", 1, 0.1, 1,
                "How much the chroma decreases with lightness.",
                ui_step=0.1),
    ParamNumber("Offset", 0.25, 0, 1, "Flat chroma boost.", ui_step=0.1),
    ParamBool("Invert", False, "Invert lightness' effect on chroma."),
    description="Reduces/increases chroma based on intensity.\n"
    "Inspired by Blender's new 'Filmic' tonemapper.",
    images="RGB*",
    preview_function=filmic_chroma_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
