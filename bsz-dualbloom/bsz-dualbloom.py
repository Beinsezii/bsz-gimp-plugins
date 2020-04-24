#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use this for reference on gegl operations and their properties/inputs/outputs.
http://www.gegl.org/operations/

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
from gi.repository import GLib
# from gi.repository import Gio
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
import bszgw
from bsz_gimp_lib import GEGL_COMPOSITORS


class DualBloom(Gimp.PlugIn):
    # GimpPlugIn virtual methods
    # Not completely sure how they work
    # Why do they have 'do_' in front when it's never mentioned in the gir docs
    def do_query_procedures(self):
        # This section can also be used to provide translations,
        # but I have no idea how it works or know any other languages
        # so I'm going to ignore that for now.

        # script name as it shows up in the PDB
        return ["bsz-dualbloom"]

    def do_create_procedure(self, name):
        # Will almost always be ImageProcedure using PLUGIN proctype
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            # name of function if something other than 'run'
            self.run, None
        )
        # Supported colorspaces
        procedure.set_image_types("RGB*, GRAY*")
        # Name in menu
        procedure.set_menu_label("Dual Bloom")
        # Icon. See Gimp-3.0.gir docs and gimp's icon folder for others
        # Historically plugins that use the new Gegl operations use ICON_GEGL
        # while the rest use ICON_SYSTEM_RUN
        procedure.set_icon_name(Gimp.ICON_GEGL)
        # Location in the top menu, with <Image> being root
        procedure.add_menu_path('<Image>/Beinsezii/')
        # Help text. First set is in-menu, second is PDB
        procedure.set_documentation(
            "Provides light and dark bloom using thresholds. See tooltips",
            "Provides light and dark bloom using thresholds."
            "Only usable in interactive mode right now.",
            name
        )
        # Me
        procedure.set_attribution("Beinsezii", "Beinsezii", "2020")
        return procedure

    # function that does the work.
    def dualbloom(self, drawable, thresh_high, thresh_low,
                  size_high, size_low, opacity_high, opacity_low,
                  composite_high="gegl:overlay", composite_low="gegl:overlay"):

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

            # Filter nodes for high threshold. See gegl.org/operations
            Threshold_High = tree.create_child("gegl:threshold")
            Threshold_High.set_property("value", thresh_high)
            CTA_High = tree.create_child("gegl:color-to-alpha")
            # hex was the only string I could get to work.
            CTA_High.set_property("color", Gegl.Color.new("#000000"))
            Blur_High = tree.create_child("gegl:gaussian-blur")
            Blur_High.set_property("std-dev-x", size_high)
            Blur_High.set_property("std-dev-y", size_high)
            Opacity_High = tree.create_child("gegl:opacity")
            Opacity_High.set_property("value", opacity_high)
            Comp_High = tree.create_child(composite_high)

            # Filter nodes for low threshold
            Threshold_Low = tree.create_child("gegl:threshold")
            Threshold_Low.set_property("value", thresh_low)
            CTA_Low = tree.create_child("gegl:color-to-alpha")
            CTA_Low.set_property("color", Gegl.Color.new("#ffffff"))
            Blur_Low = tree.create_child("gegl:gaussian-blur")
            Blur_Low.set_property("std-dev-x", size_low)
            Blur_Low.set_property("std-dev-y", size_low)
            Opacity_Low = tree.create_child("gegl:opacity")
            Opacity_Low.set_property("value", opacity_low)
            Comp_Low = tree.create_child(composite_low)

            # Output buffer node using temp buffer
            Output = tree.create_child("gegl:write-buffer")
            Output.set_property("buffer", shadow)

            # base image linked to the thresholds and Comp_Low
            Input.link(Threshold_High)
            Input.link(Threshold_Low)
            Input.link(Comp_Low)

            # connect the low nodes to each other and Comp_High
            Threshold_Low.link(CTA_Low)
            CTA_Low.link(Blur_Low)
            Blur_Low.link(Opacity_Low)
            # Seems like `.link(node)` is shorthand for
            # `.connect_to("output", node, "input")`
            Opacity_Low.connect_to("output", Comp_Low, "aux")
            Comp_Low.link(Comp_High)

            # connect the high nodes to each other and Output
            Threshold_High.link(CTA_High)
            CTA_High.link(Blur_High)
            Blur_High.link(Opacity_High)
            Opacity_High.connect_to("output", Comp_High, "aux")
            Comp_High.link(Output)

            # Run the node tree
            Output.process()

            # Flush shadow buffer and combine it with main drawable
            shadow.flush()
            drawable.merge_shadow(True)

            # Update everything.
            drawable.update(x, y, width, height)
            Gimp.displays_flush()

    # I decided to name the function called by the PDB procedure 'run'
    def run(self, procedure, run_mode, image, drawable, args, run_data):

        # run_mode 'NONINTERACTIVE' is if another plugin calls it through PDB
        # I don't understand the __gproperties__ things yet so am ignoring.
        if run_mode == Gimp.RunMode.NONINTERACTIVE:
            return "Non-interactive not supported."

        # run_mode 'WITH_LAST_VALS' is when you use Ctrl-F aka 'Repeat'
        # seems the gimp shelf isn't implemented yet, so kinda useless
        if run_mode == Gimp.RunMode.WITH_LAST_VALS:
            bszgw.Message("Repeat not supported yet.")
            run_mode = Gimp.RunMode.INTERACTIVE

        # run_mode 'INTERACTIVE' means clicked in the menu
        if run_mode == Gimp.RunMode.INTERACTIVE:
            # import the ui junk
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk  # noqa: F401
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk

            # sets default blur width to 1% of the mean length
            def_blur = round((drawable.width() + drawable.height()) / 2 * 0.01)

            # Creating all the UI widgets using my own BSZGW
            th_tt = "Values {} this will be considered '{}' bloom"
            thresh_high = bszgw.Adjuster.new(
                "High Threshold",
                0.80, 0, 1, 0.05, 0.1, decimals=2,
                tooltip=th_tt.format('above', 'light')
            )
            thresh_low = bszgw.Adjuster.new(
                "Low Threshold",
                0.35, 0, 1, 0.05, 0.1, decimals=2,
                tooltip=th_tt.format('below', 'dark')
            )

            s_tt = "Size of {} blur. Initial value set based on image size."
            size_high = bszgw.Adjuster.new(
                "High Blur Size",
                def_blur, 0, 1500, 5, 10,
                decimals=2, logarithmic=True,
                tooltip=s_tt.format('light')
            )
            size_low = bszgw.Adjuster.new(
                "Low Blur Size",
                def_blur, 0, 1500, 5, 10,
                decimals=2, logarithmic=True,
                tooltip=s_tt.format('dark')
            )

            o_tt = "Opacity of {} bloom."
            opacity_high = bszgw.Adjuster.new(
                "High Opacity",
                0.25, -10, 10, 0.05, 0.1, decimals=2,
                tooltip=o_tt.format('light')
            )
            opacity_low = bszgw.Adjuster.new(
                "Low Opacity",
                0.1, -10, 10, 0.05, 0.1, decimals=2,
                tooltip=o_tt.format('dark')
            )

            dd_tt = "Compositing method for {} threshold.\n" \
                    "Note this uses raw GEGL methods, so the results may be \
                    different."
            comp_high = bszgw.DropDown(
                tooltip=dd_tt.format("High"),
                vals_list=GEGL_COMPOSITORS,
                value="svg:overlay",
                enums=True,
            )
            comp_low = bszgw.DropDown(
                tooltip=dd_tt.format("Low"),
                vals_list=GEGL_COMPOSITORS,
                value="svg:overlay",
                enums=True,
            )

            # if 'chain' is active, size_low and size_high share adjustments
            def chain(from_adj, chain, to_wid):
                if chain.get_active():
                    to_wid.value = from_adj.props.value
            # # Gimp.ChainButton() icon is busted for some reason
            # # All you have to do is uncomment one and comment the other
            # size_chain = Gimp.ChainButton(active=True,
            #                               position=Gtk.PositionType.TOP)
            size_chain = bszgw.CheckBox("Link\nBlurs", True)
            size_high.adjustment.connect("value-changed", chain,
                                         size_chain, size_low)
            size_low.adjustment.connect("value-changed", chain,
                                        size_chain, size_high)

            # I'm using an oldschool dupe layer preview since that
            # cool live preview doesn't seem to be usable in gir yet,
            # at least that I've been able to find.
            def preview(*args):
                clear_preview()
                if preview_check.value:
                    image.undo_freeze()
                    self.preview_layer = drawable.copy()
                    image.insert_layer(self.preview_layer, None, 0)
                    ui_run(self.preview_layer)
            preview_check = bszgw.CheckBox(
                "\"Live\" Preview", True,
                tooltip="Preview updates after clicking a slider this button,"
                        " or resetting vals.\n"
                        "I can't do the cool truly live preview in stock GIMP."
            )
            # bound to self to avoid capturing
            self.preview_layer = None

            # # don't call self.widget.value directly in execute so you can run
            # # the program without a UI.
            # to avoid retyping for updating the preview and regular runs
            def ui_run(drawable2):
                self.dualbloom(drawable2,
                               thresh_high.value, thresh_low.value,
                               size_high.value, size_low.value,
                               opacity_high.value, opacity_low.value,
                               comp_high.value, comp_low.value)

            # deletes self.preview_layer and thaws undo
            def clear_preview(*args):
                if self.preview_layer:
                    image.remove_layer(self.preview_layer)
                    self.preview_layer = None
                    image.undo_thaw()

            # clear, run, close window.
            def run_button_fn(widget):
                clear_preview()
                ui_run(drawable)
                app.destroy()
            run_button = bszgw.Button("Run", run_button_fn)

            # sets all vals to default. Maybe I should implement .reset() in
            # BSZGW so I can just `for widget in list: widget.reset()`
            def reset_button_fn(widget):
                # Highs
                thresh_high.value = 0.80
                size_high.value = def_blur
                opacity_high.value = 0.25
                comp_high.value = "svg:overlay"
                # Lows
                thresh_low.value = 0.35
                size_low.value = def_blur
                opacity_low.value = 0.1
                comp_low.value = "svg:overlay"
            reset_button = bszgw.Button("Reset Vals", reset_button_fn)

            # Connections for live preview.  GEGL's fast enough this
            # works better than a dedicated 'preview' button.
            for widget in [thresh_high, thresh_low, size_high, size_low,
                           opacity_high, opacity_low,
                           ]:
                widget.scale.connect("button-release-event", preview)
            for widget in [reset_button, preview_check]:
                widget.connect("clicked", preview)

            # widgets will be boxed together visually as shown
            box = bszgw.AutoBox([
                [thresh_high, thresh_low],
                [size_high, (size_chain, False, False, 0), size_low],
                [opacity_high, opacity_low],
                [comp_high, comp_low],
                [(preview_check, False, False, 0), reset_button, run_button],
            ])
            # create the app window with the box
            app = bszgw.App(
                "BSZ Dual Bloom", box, 800, 400,
                # hints it as a pop-up instead of a full window.
                hint=Gdk.WindowTypeHint.DIALOG,
            )
            # Keep the aspect ratio reasonable.
            app_geometry = Gdk.Geometry()
            app_geometry.max_aspect = 3.0
            app_geometry.min_aspect = 2.0
            app.set_geometry_hints(None, app_geometry, Gdk.WindowHints.ASPECT)
            # Clear if you quit without running anything
            app.connect("destroy", clear_preview)

            # gen a first preview and launch gui
            preview()
            app.launch()

        # Don't actually really know what this does but seems important
        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS, GLib.Error()
        )


# load plugin into gimp
Gimp.main(DualBloom.__gtype__, sys.argv)
