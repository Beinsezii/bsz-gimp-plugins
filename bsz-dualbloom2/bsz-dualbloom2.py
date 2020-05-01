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
# from gi.repository import GObject
# from gi.repository import GLib
# from gi.repository import Gio
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
# import bszgw
from bsz_gimp_lib import PlugIn, ParamNumber, ParamNumberChain


# Main function.
def dual_bloom_2(image, drawable, amount_high, amount_low,
                 softness_high, softness_low, radius_high, radius_low,
                 strength_high, strength_low):

    # Fairly certain mask_intersect() is the current selection mask
    intersect, x, y, width, height = drawable.mask_intersect()
    if intersect:
        # start Gegl
        Gegl.init(None)
        # fetch main buffer
        buff = drawable.get_buffer()
        # fetch shadow aka "temp" buffer
        shadow = drawable.get_shadow_buffer()
        # create a new node tree/graph
        tree = Gegl.Node()

        # Input buffer node using main buffer
        Input = tree.create_child("gegl:buffer-source")
        Input.set_property("buffer", buff)

        # Operations for the high bloom
        Bloom_High = tree.create_child("gegl:bloom")
        Bloom_High.set_property("amount", amount_high)
        Bloom_High.set_property("softness", softness_high)
        Bloom_High.set_property("radius", radius_high)
        Bloom_High.set_property("strength", strength_high)
        Sub_High = tree.create_child("gegl:subtract")
        Add_High = tree.create_child("gegl:add")

        # Operations for the low bloom
        Invert_Low = tree.create_child("gegl:invert-gamma")
        Bloom_Low = tree.create_child("gegl:bloom")
        Bloom_Low.set_property("amount", amount_low)
        Bloom_Low.set_property("softness", softness_low)
        Bloom_Low.set_property("radius", radius_low)
        Bloom_Low.set_property("strength", strength_low)
        Invert_Low2 = tree.create_child("gegl:invert-gamma")

        # Output buffer node using temp buffer
        Output = tree.create_child("gegl:write-buffer")
        Output.set_property("buffer", shadow)

        # base image linked to the thresholds and Comp_Low
        Input.link(Bloom_High)
        Input.connect_to("output", Sub_High, "aux")
        Input.link(Invert_Low)

        # High bloom nodes
        Bloom_High.link(Sub_High)
        Sub_High.connect_to("output", Add_High, "aux")

        # Low bloom nodes
        Invert_Low.link(Bloom_Low)
        Bloom_Low.link(Invert_Low2)
        Invert_Low2.link(Add_High)

        # Combine
        Add_High.link(Output)

        # Run the node tree
        Output.process()

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()


# Preview function. Just runs the same thing on a copy
def dual_bloom_2_preview(image, drawable, *args):
    preview_layer = drawable.copy()
    image.insert_layer(preview_layer, None, 0)
    dual_bloom_2(image, preview_layer, *args)
    return preview_layer


# Parameters from bsz_gimp_lib
amount_high = ParamNumber("Amount High", 15, 0, 100)
amount_low = ParamNumber("Amount Low", 35, 0, 100, ui_column=1)

softness_high = ParamNumber("Softness High", 25, 0, 100)
softness_low = ParamNumber("Softness Low", 25, 0, 100, ui_column=1)

radius_high = ParamNumber("Radius High", 10, 0, 1500,
                          ui_logarithmic=True)
radius_low = ParamNumber("Radius Low", 10, 0, 1500,
                         ui_logarithmic=True, ui_column=1)

strength_high = ParamNumber("Strength High", 50, 0, 1000,
                            ui_logarithmic=True)
strength_low = ParamNumber("Strength Low", 50, 0, 1000,
                           ui_logarithmic=True, ui_column=1)

softness_chain = ParamNumberChain("Softness Chain", True,
                                  softness_high, softness_low, ui_row=1)
radius_chain = ParamNumberChain("Radius Chain", True,
                                radius_high, radius_low, ui_row=1)

# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Dual Bloom 2",  # name
    dual_bloom_2,    # function
    amount_high,     # *params
    amount_low,
    softness_high,
    softness_low,
    radius_high,
    radius_low,
    strength_high,
    strength_low,
    softness_chain,
    radius_chain,
    description="WIP",
    alt_description="Alt Desc WIP",
    images="RGB*, GRAY*",
    preview_function=dual_bloom_2_preview,
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
