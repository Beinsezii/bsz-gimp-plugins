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
from gi.repository import GLib
# from gi.repository import Gio
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
import bszgw
# from bsz_gimp_lib import GEGL_COMPOSITORS


class DualBloom2(Gimp.PlugIn):
    # GimpPlugIn virtual methods
    # Not completely sure how they work
    # Why do they have 'do_' in front when it's never mentioned in the gir docs
    def do_query_procedures(self):
        # This section can also be used to provide translations,
        # but I have no idea how it works or know any other languages
        # so I'm going to ignore that for now.

        # script name as it shows up in the PDB
        return ["bsz-dualbloom2"]

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
        procedure.set_menu_label("Dual Bloom 2")
        # Icon. See Gimp-3.0.gir docs and gimp's icon folder for others
        # Historically plugins that use the new Gegl operations use ICON_GEGL
        # while the rest use ICON_SYSTEM_RUN
        procedure.set_icon_name(Gimp.ICON_GEGL)
        # Location in the top menu, with <Image> being root
        procedure.add_menu_path('<Image>/Beinsezii/')
        # Help text. First set is in-menu, second is PDB
        procedure.set_documentation(
            "Provides light and dark bloom using thresholds.\n"
            "Based on GIMP/GEGL's existing bloom.",
            "Provides light and dark bloom using thresholds.\n"
            "Only usable in interactive mode right now.",
            name
        )
        # Me
        procedure.set_attribution("Beinsezii", "Beinsezii", "2020")
        return procedure

    def dualbloom2(self, drawable, amount_high, amount_low,
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

            Bloom_High = tree.create_child("gegl:bloom")
            Bloom_High.set_property("amount", amount_high)
            Bloom_High.set_property("softness", softness_high)
            Bloom_High.set_property("radius", radius_high)
            Bloom_High.set_property("strength", strength_high)
            Sub_High = tree.create_child("gegl:subtract")
            Add_High = tree.create_child("gegl:add")

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

            def_blur = round((drawable.width() + drawable.height()) / 2 * 0.01)

            # Creating all the UI widgets using my own BSZGW
            am_tt = "Amount of {} bloom. Acts like a threshold."
            amount_high = bszgw.Adjuster.new("High Amount",
                                             15, 0, 100, 1, 5, decimals=2,
                                             tooltip=am_tt.format('light')
                                             )
            amount_low = bszgw.Adjuster.new("Low Amount",
                                            35, 0, 100, 1, 5, decimals=2,
                                            tooltip=am_tt.format('dark')
                                            )

            sf_tt = "Softness of {} bloom threshold selection"
            softness_high = bszgw.Adjuster.new("High Softness",
                                               25, 0, 100, 1, 5, decimals=2,
                                               tooltip=sf_tt.format('light'))
            softness_low = bszgw.Adjuster.new("Low Softness",
                                              25, 0, 100, 1, 5, decimals=2,
                                              tooltip=sf_tt.format('dark'))

            rd_tt = "Size of {} blur. Initial value set based on image size."
            radius_high = bszgw.Adjuster.new("High Radius",
                                             def_blur, 0, 1500, 1, 5,
                                             decimals=2, logarithmic=True,
                                             tooltip=rd_tt.format('light'))
            radius_low = bszgw.Adjuster.new("Low Radius",
                                            def_blur, 0, 1500, 1, 5,
                                            decimals=2, logarithmic=True,
                                            tooltip=rd_tt.format('dark'))

            st_tt = "Strength of {} bloom."
            strength_high = bszgw.Adjuster.new("High Strength",
                                               50, 0, 1000, 1, 5,
                                               decimals=2, logarithmic=True,
                                               tooltip=st_tt.format('light'))
            strength_low = bszgw.Adjuster.new("Low Strength",
                                              50, 0, 1000, 1, 5,
                                              decimals=2, logarithmic=True,
                                              tooltip=st_tt.format('dark'))

            # copies value from the Gtk.Adjustment that calls it to the
            # widget specified
            def chain(from_adj, chain, to_wid):
                if chain.get_active():
                    to_wid.value = from_adj.props.value

            # Gimp.ChainButton's icon is borked.
            # soft_chain = Gimp.ChainButton(active=True,
            #                               position=Gtk.PositionType.TOP)
            # radius_chain = Gimp.ChainButton(active=True,
            #                                 position=Gtk.PositionType.TOP)
            soft_chain = bszgw.CheckBox("Link", True)
            radius_chain = bszgw.CheckBox("Link", True)

            softness_high.adjustment.connect("value-changed", chain,
                                             soft_chain, softness_low)
            softness_low.adjustment.connect("value-changed", chain,
                                            soft_chain, softness_high)
            radius_high.adjustment.connect("value-changed", chain,
                                           radius_chain, radius_low)
            radius_low.adjustment.connect("value-changed", chain,
                                          radius_chain, radius_high)

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
                self.dualbloom2(drawable2,
                                amount_high.value, amount_low.value,
                                softness_high.value, softness_low.value,
                                radius_high.value, radius_low.value,
                                strength_high.value, strength_low.value)

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

            def test_button_fn(widget):
                clear_preview()
                self.dualbloom2(drawable,
                                amount_high.value, amount_low.value,
                                softness_high.value, softness_low.value,
                                radius_high.value, radius_low.value,
                                strength_high.value, strength_low.value)

            # sets all vals to default. Maybe I should implement .reset() in
            # BSZGW so I can just `for widget in list: widget.reset()`
            def reset_button_fn(widget):
                for widget in [amount_high, amount_low,
                               softness_high, softness_low,
                               radius_high, radius_low,
                               strength_high, strength_low]:
                    widget.reset()
            reset_button = bszgw.Button("Reset Vals", reset_button_fn)

            # Connections for live preview.  GEGL's fast enough this
            # works better than a dedicated 'preview' button.
            for widget in [amount_high, amount_low,
                           softness_high, softness_low,
                           radius_high, radius_low,
                           strength_high, strength_low]:
                widget.scale.connect("button-release-event", preview)
            for widget in [reset_button, preview_check]:
                widget.connect("clicked", preview)

            # widgets will be boxed together visually as shown
            box = bszgw.AutoBox([
                [amount_high, amount_low],
                [softness_high, (soft_chain, False, False, 0), softness_low],
                [radius_high, (radius_chain, False, False, 0), radius_low],
                [strength_high, strength_low],
                [(preview_check, False, False, 0), reset_button, run_button],
            ])
            # create the app window with the box
            app = bszgw.App(
                "BSZ Dual Bloom 2", box, 800, 400,
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
Gimp.main(DualBloom2.__gtype__, sys.argv)
