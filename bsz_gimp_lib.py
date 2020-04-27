#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared code between plugins
"""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
# gi.require_version('Gegl', '0.4')
# from gi.repository import Gegl
# from gi.repository import GObject
from gi.repository import GLib
# from gi.repository import Gio
from abc import ABC, abstractmethod

# UI
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: F401
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import bszgw


GEGL_COMPOSITORS = {
    "Source": "svg:src",
    "Source-Atop": "svg:src-atop",
    "Source-In": "svg:src-in",
    "Source-Out": "svg:src-out",
    "Source-Over": "svg:src-over",

    "Destination": "svg:dst",
    "Destination-Atop": "svg:dst-atop",
    "Destination-In": "svg:dst-in",
    "Destination-Out": "svg:dst-out",
    "Destination-Over": "svg:dst-over",

    "Lighten": "svg:lighten",
    "Screen": "svg:screen",
    "Color-Dodge": "svg:color-dodge",
    "Add": "gegl:add",
    "Plus": "svg:plus",

    "Darken": "svg:darken",
    "Multiply": "gegl:multiply",
    "Color-Burn": "svg:color-burn",

    "Overlay": "svg:overlay",
    "Soft-Light": "gegl:soft-light",
    "Hard-Light": "svg:hard-light",

    "Difference": "svg:difference",
    "Exclusion": "svg:exclusion",
    "Subtract": "gegl:subtract",
    "Divide": "gegl:divide",

    "Gamma": "gegl:gamma",
    "Seamless-Clone-Compose": "gegl:seamless-clone-compose",
    "Weighted-Blend": "gegl:weighted-blend",
    "Clear": "svg:clear",
    "Xor": "svg:xor",
}


class Param(ABC):
    def __init__(self, name: str, ui_column: int = 0):
        self.name = name

    @abstractmethod
    def create_widget(self):
        pass


class ParamNumber(Param):
    def __init__(self, name: str, value: int, min, max, integer: bool = False,
                 ui_step: int = 1, ui_logarithmic: bool = False):
        super(ParamNumber, self).__init__(name)
        self.value = value
        self.min = min
        self.max = max
        self.integer = integer
        self.ui_step = ui_step
        self.ui_logarithmic = ui_logarithmic

    def create_widget(self):
        return bszgw.Adjuster.new(
            label=self.name,
            value=self.value,
            min_value=self.min,
            max_value=self.max,
            step_increment=self.ui_step,
            page_increment=self.ui_step,
            decimals=0 if self.integer else 2
        )


class PlugIn():
    # Get & save properties
    def __init__(self, name: str, function: callable, *params: Param,
                 description: str, alt_description: str = None,
                 images: str = "RGB*", live: bool = True,
                 path: str = "<Image>/Beinsezii/", icon=Gimp.ICON_GEGL,
                 author: str = "Beinsezii", date: str = "2020"):
        if not alt_description:
            alt_description = description

        # if PlugIn itself inherits Gimp.PlugIn,
        # gimp doesn't save it's __init__ data when running self.run
        class Procedure(Gimp.PlugIn):
            # GimpPlugIn virtual methods
            # Not completely sure how they work
            # Why do they have 'do_' in front
            # when it's never mentioned in the gir docs?
            def do_query_procedures(self2):
                # This section can also be used to provide translations,
                # but I have no idea how it works or know any other languages
                # so I'm going to ignore that for now.

                # script name as it shows up in the PDB
                return [name.lower().replace(" ", "-")]

            def do_create_procedure(self2, name2):
                # Will almost always be ImageProcedure using PLUGIN proctype
                procedure = Gimp.ImageProcedure.new(
                    self2, name2,
                    Gimp.PDBProcType.PLUGIN,
                    # name of function if something other than 'run'
                    self.run, None
                )
                # Supported colorspaces
                procedure.set_image_types(images)
                # Name in menu
                procedure.set_menu_label(name)
                # Icon. See Gimp-3.0.gir docs and gimp's icon folder for others
                # Usually plugins based on Gegl operations use ICON_GEGL
                # while the rest use ICON_SYSTEM_RUN
                procedure.set_icon_name(icon)
                # Location in the top menu, with <Image> being root
                procedure.add_menu_path(path)
                # Help text. First set is in-menu, second is PDB
                procedure.set_documentation(
                    description,
                    alt_description,
                    name2
                )
                # Me
                procedure.set_attribution(author, author, date)
                return procedure

        self.Procedure = Procedure
        self.name = name
        self.function = function
        self.params = params
        self.live = live

    # I decided to name the function called by the PDB procedure 'run'
    def run(self, procedure, run_mode, image, drawable, args, run_data):

        # run_mode 'NONINTERACTIVE' is if another plugin calls it through PDB
        # I don't understand the __gproperties__ things yet so am ignoring.
        if run_mode == Gimp.RunMode.NONINTERACTIVE:
            return "Non-interactive not supported."

        # run_mode 'WITH_LAST_VALS' is when you use Ctrl-F aka 'Repeat'
        # seems the gimp shelf isn't implemented yet, so kinda useless
        if run_mode == Gimp.RunMode.WITH_LAST_VALS:
            # Gimp.get_pdb().run_procedure('gimp-message',
            #                              "Repeat not supported yet")
            bszgw.Message("Repeat not supported yet")
            run_mode = Gimp.RunMode.INTERACTIVE

        # run_mode 'INTERACTIVE' means clicked in the menu
        if run_mode == Gimp.RunMode.INTERACTIVE:
            widgets = []
            for param in self.params:
                widgets.append(param.create_widget())

            def run_fn(widget):
                self.function(image, drawable, *[wid.value for wid in widgets])
            run_button = bszgw.Button("Run", run_fn)

            box = bszgw.AutoBox([
                [widgets],
                [(run_button, False, False, 0)],
            ])
            # create the app window with the box
            app = bszgw.App(
                self.name, box,
                # hints it as a pop-up instead of a full window.
                hint=Gdk.WindowTypeHint.DIALOG,
            )
            app.launch()

        # Don't actually really know what this does but seems important
        return procedure.new_return_values(
            Gimp.PDBStatusType.SUCCESS, GLib.Error()
        )
