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
import os, sys
from kivy.resources import resource_add_path, resource_find
from os.path import exists

import datetime as dt

from libs.id_generator import get_all_employee_nums

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
    # def set_operator_list(self, singleoperator, dayshift, swingshift, graveyardshift, alloperators):
    #     if singleoperator:
    #         opnum_str = app.ids.operatorevaluationscreen.select_operator_dialog.content_cls.operatornumbertext.text
    #         print("Operator: {}\nType: {}".format(opnum_str, type(opnum_str)))
    #         # app.OPERATOR_LIST = []
    #     else:
    #         print("Not a single operator")
    pass

class OperatorEvaluationScreen(MDScreen):
    start_time_dialog = None        # Holding variable for time dialog
    end_time_dialog = None
    startdate = None
    enddate = dt.date.today()
    t_start = dt.time(0,0,0)        # Default start time
    t_end = dt.time(23,59,59)       # Default end time
    select_operator_dialog = None
    operator_number = None
    evaluation_info_dialog = None
    boxplot_info_dialog = None

    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()

    ### Functions related to Select Operator button ###
    def show_select_operator_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"

        if not self.select_operator_dialog:
            self.select_operator_dialog = MDDialog(
                title="Select Operator(s)",
                type="custom",
                content_cls=OperatorContent(),
                buttons=[
                    MDFlatButton(
                        text="OK",
                        font_style="Button",
                        # on_release=self.set_operator_number
                        on_release=self.set_operator_list
                    ),
                    MDFlatButton(
                        text="CANCEL",
                        font_style="Button",
                        on_release=self.close_select_operator_dialog
                    ),
                ],
            )
        self.select_operator_dialog.open()

    # def test_dialog_access(self, *args):
    #     print(self.select_operator_dialog.content_cls.dayshiftcheck.active)

    def set_operator_list(self, *args):
        singleoperator = self.select_operator_dialog.content_cls.singleoperatorcheck.active
        dayshift = self.select_operator_dialog.content_cls.dayshiftcheck.active
        swingshift = self.select_operator_dialog.content_cls.swingshiftcheck.active
        graveyardshift = self.select_operator_dialog.content_cls.graveyardshiftcheck.active
        alloperators = self.select_operator_dialog.content_cls.alloperatorscheck.active

        if singleoperator:
            opnum_str = self.select_operator_dialog.content_cls.operatornumbertext.text
            if len(opnum_str) > 0:
                opnum = int(opnum_str)
                app.OPERATOR_LIST = [opnum]
                print("Operator: {}\nType: {}".format(app.OPERATOR_LIST, type(app.OPERATOR_LIST)))
            else:
                print("Empty number")
        elif dayshift:
            print("DAY SHIFT SELECTION FEATURE IS NOT YET COMPLETE")
        elif swingshift:
            print("SWING SHIFT SELECTION FEATURE IS NOT YET COMPLETE")
        elif graveyardshift:
            print("GRAVEYARD SHIFT SELECTION FEATURE IS NOT YET COMPLETE")
        elif alloperators:
            directory = 'C:\\Users\\Ryan.Larson.ROCKWELLINC\\github\\plc-data-analysis\\ID_Tracking\\'
            filepath = directory + "ID_data.xlsx"
            df = get_all_employee_nums(filepath)
            allnums = list(df["ID"])
            allnums = [int(num) for num in allnums]
            print(allnums)
            app.OPERATOR_LIST = allnums
        else:
            print("ERROR IN OPERATOR SELECTION")

        self.close_select_operator_dialog()

    def set_operator_number(self, *args):
        self.operator_number = self.select_operator_dialog.content_cls.operatornumbertext.text
        print("Operator: {}\nType: {}".format(self.operator_number, type(self.operator_number)))
        self.close_select_operator_dialog()

    def close_select_operator_dialog(self, *args):
        self.select_operator_dialog.dismiss(force=True)
        self.select_operator_dialog = None

    ### Functions for choosing start date and time ###
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
                        on_release=self.set_start_time_dialog
                    ),
                    MDFlatButton(
                        text="Clear",
                        font_style="Button",
                        theme_text_color="Custom",
                        on_release=self.clear_start_time_dialog
                    ),
                    MDFlatButton(
                        text="Cancel",
                        font_style="Button",
                        theme_text_color="Custom",
                        on_release=self.cancel_start_time_dialog
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
        if self.t_start is None or self.startdate is None:
            statustext = "Missing start time or date."
        else:
            statustext = "Good to go"
        self.snackbar_show(statustext)
        self.time_range_dialog = None
        print(self.t_start)
        print(self.startdate)

    def clear_start_time_dialog(self, *args):
        self.t_start = None
        self.startdate = None
        statustext = "STARTING DATE AND TIME CLEARED. Please select a new date and time before generating report."
        self.snackbar_show(statustext)
        self.start_time_dialog = None

    def cancel_start_time_dialog(self, *args):
        self.time_range_dialog.dismiss(force=True)
        if not self.t_start or not self.startdate:
            statustext = "Missing start time or date."
            self.snackbar_show(statustext)
        self.time_range_dialog = None

    ### Functions for choosing end date and time ###
    def show_end_time_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"
        print("Default End time: {}, {}".format(self.t_end, type(self.t_end)))

        if not self.end_time_dialog:
            self.end_time_dialog = MDDialog(
                title="Choose End Date & Time",
                buttons=[
                    MDRaisedButton(
                        text="End Date",
                        font_style="Button",
                        on_release=self.show_end_date_picker
                    ),
                    MDRaisedButton(
                        text="End Time",
                        font_style="Button",
                        on_release=self.show_end_time_picker
                    ),
                    MDRaisedButton(
                        text="Set",
                        font_style="Button",
                        md_bg_color=theme_cls.accent_color,
                        on_release=self.set_end_time_dialog
                    ),
                    MDFlatButton(
                        text="Clear",
                        font_style="Button",
                        theme_text_color="Custom",
                        text_color=theme_cls.primary_color,
                        on_release=self.clear_end_time_dialog
                    ),
                    MDFlatButton(
                        text="Cancel",
                        font_style="Button",
                        theme_text_color="Custom",
                        text_color=theme_cls.primary_color,
                        on_release=self.cancel_end_time_dialog
                    ),
                ],
            )
        self.end_time_dialog.open()

    def show_end_time_picker(self, *args):
        end_time_dialog = MDTimePicker()
        if self.t_end:
            end_time_dialog.set_time(self.t_end)
        end_time_dialog.bind(on_save=self.on_end_time_save)
        end_time_dialog.open()

    def on_end_time_save(self, instance, time):
        self.t_end = time
        print(self.t_end)

    def show_end_date_picker(self, *args):
        end_date_dialog = MDDatePicker()
        end_date_dialog.bind(on_save=self.on_end_date_save)
        end_date_dialog.open()

    def on_end_date_save(self, instance, value, date_range):
        self.enddate = value
        print("Ending date is {}, {}".format(self.enddate, type(self.enddate)))

    def set_end_time_dialog(self, *args):
        self.end_time_dialog.dismiss(force=True)
        if not self.t_end:
            statustext = "MISSING END TIME"
        else:
            statustext = "GOOD TO GO"
        self.snackbar_show(statustext)
        self.time_range_dialog = None
        print(self.t_end)
        print(self.enddate)

    def clear_end_time_dialog(self, *args):
        self.t_end = None
        self.enddate = None
        statustext = "ENDING DATE AND TIME CLEARED. Please select a new date and time before generating report."
        self.snackbar_show(statustext)
        self.end_time_dialog = None

    def cancel_end_time_dialog(self, *args):
        self.time_range_dialog.dismiss(force=True)
        if not self.t_end or not self.enddate:
            statustext = "MISSING ENDING DATE OR TIME."
            self.snackbar_show(statustext)
        self.time_range_dialog = None


    ### Functions for showing the operator evaluation info dialog ###
    def show_evaluation_info_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"

        infotext =  """Operator reports are displayed with four box plots. The first three illustrate the cycle times for the chosen operator as a lead, as an assistant, and with all their times combined. The fourth column contains a plot of all cycle times logged at Rockwell during the period of interest.

Compare the median lines for each plot to see what an operator averages most of the time. A median line below the team's median indicates that the operator averages faster cycle times than the team.

The other main feature to look for is how compact or stretched the box plot is. A box plot that is very compact means the operator is very consistent at hitting their cycle times, while a tall or stretched box plot indicates an operator that is variable or inconsistent.

Outlier cases, if they exist, are shown as small circles above or below the box plot. These are cases that should be noted, but can be considered not typical, and in some cases can be ignored. These might happen due to conditions outside the operator's control, such as a bag change. This is not always the case, however.

Box plots are only valid with at least 5 data points. More sample points are better. For a proper evaluation, try to choose an evaluation period with at least 20 sample points. The number of samples in each box plot is displayed below the chart on the generated Operator Report.
                    """

        if not self.evaluation_info_dialog:
            self.evaluation_info_dialog = MDDialog(
                title="Interpreting Operator Reports",
                text=infotext,
                buttons=[
                    MDFlatButton(
                        text="DISMISS",
                        font_style="Button",
                        on_release=self.close_evaluation_info_dialog
                    ),
                ],
            )
        self.evaluation_info_dialog.open()

    def close_evaluation_info_dialog(self, *args):
        self.evaluation_info_dialog.dismiss(force=True)
        self.evaluation_info_dialog = None


    ### Functions for generating the operator evaluation report

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
    OPERATOR_LIST = []

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
