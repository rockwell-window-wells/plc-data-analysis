# Built with:
# Python 3.9.8
# kivy 2.0.0
# kivymd 1.0.0.dev0
# pandas 1.3.4
# numpy 1.19.5
# csv 1.0
# matplotlib 3.4.3
# pyfpdf (imported as fpdf) 1.7.2

from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, ObjectProperty

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior, ThemeManager
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.uix.screen import MDScreen
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.snackbar.snackbar import Snackbar
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.checkbox import CheckBox
from kivy.uix.recycleview import RecycleView
from kivymd.uix.dropdownitem import MDDropDownItem

from kivy.config import Config
from kivy.core.window import Window
from libs.layout import KV
# from libs.datamethods import refresh_data, prepare_data, plot_data
# from libs.exportmethods import generatesinglePDF, generatemultiPDF
import os, sys
from kivy.resources import resource_add_path, resource_find
from os.path import exists

import datetime as dt

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.size = (1000, 750)
Window.minimum_width, Window.minimum_height = Window.size


class RootScreen(MDScreen):
    pass


class HomeScreen(MDScreen):
    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()


class OperatorIDScreen(MDScreen):
    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()

class EquipmentIDScreen(MDScreen):
    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()

class OperatorContent(MDBoxLayout):
    pass

class OperatorEvaluationScreen(MDScreen):
    start_time_dialog = None       # Holding variable for time dialog
    startdate = None
    t_start = dt.time(0,0,0)      # Analysis start time
    select_operator_dialog = None
    operator_number = None

    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()


    def show_select_operator_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"

        if not self.select_operator_dialog:
            self.select_operator_dialog = MDDialog(
                title="Select Operator Number",
                type="custom",
                content_cls=OperatorContent(),
                buttons=[
                    MDFlatButton(
                        text="OK",
                        font_style="Button",
                        text_color = app.theme_cls.primary_color,
                        on_release=self.set_operator_number
                    ),
                    MDFlatButton(
                        text="CANCEL",
                        font_style="Button",
                        text_color = app.theme_cls.primary_color,
                        on_release=self.close_select_operator_dialog
                    ),
                ],
            )
        self.select_operator_dialog.open()

    def set_operator_number(self, opnum):

        self.operator_number = opnum
        self.close_select_operator_dialog()

    def close_select_operator_dialog(self, *args):
        self.select_operator_dialog.dismiss(force=True)
        self.select_operator_dialog = None





    ### Functions for choosing analysis times ###
    def show_start_time_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"
        print("Default start time: {}, {}".format(self.t_start, type(self.t_start)))

        if not self.start_time_dialog:
            self.start_time_dialog = MDDialog(
                title="Choose Start Date & Time",
                buttons=[
                    MDRaisedButton(
                        text="Start Date",
                        font_style="Button",
                        on_release=self.show_start_date_picker
                    ),
                    MDRaisedButton(
                        text="Start Time",
                        font_style="Button",
                        on_release=self.show_start_time_picker
                    ),
                    MDRaisedButton(
                        text="Set",
                        font_style="Button",
                        md_bg_color=theme_cls.accent_color,
                        # on_release=self.set_start_time_dialog
                    ),
                    MDFlatButton(
                        text="Clear",
                        font_style="Button",
                        theme_text_color="Custom",
                        text_color=theme_cls.primary_color,
                        # on_release=self.clear_start_time_dialog
                    ),
                    MDFlatButton(
                        text="Cancel",
                        font_style="Button",
                        theme_text_color="Custom",
                        text_color=theme_cls.primary_color,
                        # on_release=self.cancel_start_time_dialog
                    ),
                ],
            )
        self.start_time_dialog.open()

    def show_start_time_picker(self, *args):
        start_time_dialog = MDTimePicker()
        if self.t_start:
            start_time_dialog.set_time(self.t_start)
        start_time_dialog.bind(on_save=self.on_start_time_save)
        start_time_dialog.open()

    def on_start_time_save(self, instance, time):
        self.t_start = time
        print(self.t_start)

    def show_start_date_picker(self, *args):
        start_date_dialog = MDDatePicker()
        start_date_dialog.bind(on_save=self.on_start_date_save)
        start_date_dialog.open()

    def on_start_date_save(self, instance, value, date_range):
        self.startdate = value
        print("Starting date is {}, {}".format(self.startdate, type(self.startdate)))
        # self.dates = None
        # print("self.date = {}\nself.dates = {}".format(self.date, self.dates))

    def set_start_time_dialog(self, *args):
        self.start_time_dialog.dismiss(force=True)
        if not self.t_start or not self.t_end:


            if app.english is True:
                statustext = "MISSING TIME RANGE. Please choose time range before running analysis."
            else:
                statustext = "FALTA RANGO DE TIEMPO. Elija un intervalo de tiempo antes de ejecutar el an\u00E1lisis."
        else:
            if app.english is True:
                statustext = "TIME RANGE SET: {} to {}".format(self.t_start, self.t_end)
            else:
                statustext = "SE HA FIJADO EL RANGO DE TIEMPO: {} a {}".format(self.t_start, self.t_end)
        if self.date and (self.t_start >= self.t_end):
            if app.english is True:
                statustext = "ERROR: Start time is later than end time."
            else:
                statustext = "ERROR: La hora de inicio es posterior a la hora de finalizaci\u00F3n."

        self.snackbar_show(statustext)
        self.time_range_dialog = None

    def clear_time_dialog(self, *args):
        self.t_start = None
        self.t_end = None
        if app.english is True:
            statustext = "TIME RANGE CLEARED. Please choose time range before running analysis."
        else:
            statustext = "RANGO DE TIEMPO BORRADO. Elija un intervalo de tiempo antes de ejecutar el an\u00E1lisis."
        self.snackbar_show(statustext)
        self.time_range_dialog = None

    def cancel_time_dialog(self, *args):
        self.time_range_dialog.dismiss(force=True)
        if not self.t_start or not self.t_end:
            if app.english is True:
                statustext = "MISSING TIME RANGE. Please choose time range before running analysis."
            else:
                statustext = "FALTA RANGO DE TIEMPO. Elija un intervalo de tiempo antes de ejecutar el an\u00E1lisis."
            self.snackbar_show(statustext)
        self.time_range_dialog = None


class SettingsScreen(MDScreen):

    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()


class ContentNavigationDrawer(MDBoxLayout):
    pass


class ItemDrawer(OneLineIconListItem):
    icon = StringProperty()
    text_color = ListProperty((0, 0, 0, 1))


class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        """Called when tap on a menu item."""

        # Set the color of the icon and text for the menu item.
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color


class IDApp(MDApp):

    def build(self):
        # App settings
        # self.theme_cls.colors = colors
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "400"
        # self.theme_cls.accent_palette = "Amber"
        self.title = "Rockwell ID & Evaluation Tool"
        # self.icon = "assets/RWLettermark.png"
        self.items = ["A", "B", "C", "D", "E"]

        screen = Builder.load_string(KV)

        return screen


if __name__ == '__main__':
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        app = IDApp()
        app.run()

    except Exception as e:
        print(e)
        input("Press enter.")
