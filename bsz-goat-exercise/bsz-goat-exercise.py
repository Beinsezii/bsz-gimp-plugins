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
# add the parent folder to import search. Will let it find ../bsz_gimp_lib.py
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
# import classes as necessary. Could also import bsz_gimp_lib as bgl if prefer.
from bsz_gimp_lib import PlugIn, ParamNumber, ParamString


# Main function.
def goat_exercise(self, drawable, src_code, brightness):
    # {{{
    # mask_intersect() is the current selection mask
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

        # Filter nodes. See gegl operation help
        Filter_Invert = tree.create_child("gegl:invert")
        Filter_Brightness = tree.create_child("gegl:brightness-contrast")
        Filter_Brightness.set_property("brightness", brightness)

        # Output buffer node using temp buffer
        Output = tree.create_child("gegl:write-buffer")
        Output.set_property("buffer", shadow)

        # Connect the nodes together.
        Input.link(Filter_Invert)
        Filter_Invert.link(Filter_Brightness)
        Filter_Brightness.link(Output)

        # Run the node tree
        Output.process()

        # Flush shadow buffer and combine it with main drawable
        shadow.flush()
        drawable.merge_shadow(True)

        # Update everything.
        drawable.update(x, y, width, height)
        Gimp.displays_flush()
        # }}}


# Parameters from bsz_gimp_lib
# {{{
source_code = "Could not find source code."
with open(os.path.realpath(__file__), mode='r', encoding='UTF-8') as f:
    source_code = f.read()

Source_Code_View = ParamString(
    "Source Code",
    source_code,
    description="Source View. Not actually used in-script",
    ui_multiline=True,
    ui_min_height=900,
    ui_min_width=900,
)

Brightness_Controller = ParamNumber(
    "Brightness", 0, -1, 1,
    description="Adjust the image's brightness after the inversion.",
    ui_step=0.1,
)
# }}}


# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "BSZ Goat Exercise",  # name
    goat_exercise,    # function
    Source_Code_View,  # params
    Brightness_Controller,
    authors="Beinsezii",
    date="2020",
    description="Exercise a goat BSZ style.",
    images="*",
    path="<Image>/Filters/Development/Goat exercises/",
)

# register the plugin's Procedure class with gimp
Gimp.main(plugin.Procedure.__gtype__, sys.argv)
