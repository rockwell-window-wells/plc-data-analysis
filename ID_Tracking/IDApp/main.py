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
from dateutil.relativedelta import relativedelta
import pandas as pd

from libs import id_methods
import libs.cycle_time_methods_v2 as cycle
# import libs.cycle_time_methods as cycle
from libs import data_assets

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.size = (1000, 750)
Window.minimum_width, Window.minimum_height = Window.size


class RootScreen(MDScreen):
    pass


class HomeScreen(MDScreen):
    def translate_en(self):
        app.english = True
        app.home_title = app.home_title_en
        app.operator_eval_title = app.operator_eval_title_en
        app.navigation_title = app.navigation_title_en
        app.select_operator_btn = app.select_operator_btn_en
        app.startdate_time_btn = app.startdate_time_btn_en
        app.enddate_time_btn = app.enddate_time_btn_en
        app.generate_report_btn = app.generate_report_btn_en
        app.single_operator_select = app.single_operator_select_en
        app.dayshift_select = app.dayshift_select_en
        app.swingshift_select = app.swingshift_select_en
        app.graveshift_select = app.graveshift_select_en
        app.alloperators_select = app.alloperators_select_en
        app.enter_operator_num = app.enter_operator_num_en
        app.set_btn = app.set_btn_en
        app.clear_btn = app.clear_btn_en
        app.cancel_btn = app.cancel_btn_en
        app.startdate_time_title = app.startdate_time_title_en
        app.startdate_btn = app.startdate_btn_en
        app.starttime_btn = app.starttime_btn_en
        app.enddate_time_title = app.enddate_time_title_en
        app.enddate_btn = app.enddate_btn_en
        app.endtime_btn = app.endtime_btn_en
        app.generating_report_text = app.generating_report_text_en
        app.interpreting_reports_title = app.interpreting_reports_title_en
        app.dismiss_btn = app.dismiss_btn_en
        app.choose_startdate_time_title = app.choose_startdate_time_title_en
        app.choose_enddate_time_title = app.choose_enddate_time_title_en
        app.select_operator_title = app.select_operator_title_en
        app.operator_ids_title = app.operator_ids_title_en
        app.add_operator_btn = app.add_operator_btn_en
        app.enter_id_num = app.enter_id_num_en
        app.enter_operator_name = app.enter_operator_name_en
        app.equipment_title = app.equipment_title_en
        app.purple_select = app.purple_select_en
        app.bag_select = app.bag_select_en
        app.pictureframe_select = app.pictureframe_select_en
        app.num_equip_cards_text = app.num_equip_cards_text_en
        app.print_equip_ids_btn = app.print_equip_ids_btn_en

        self.snackbar_show("Language changed to English")

    def translate_esp(self):
        app.english = False
        app.home_title = app.home_title_esp
        app.operator_eval_title = app.operator_eval_title_esp
        app.navigation_title = app.navigation_title_esp
        app.select_operator_btn = app.select_operator_btn_esp
        app.startdate_time_btn = app.startdate_time_btn_esp
        app.enddate_time_btn = app.enddate_time_btn_esp
        app.generate_report_btn = app.generate_report_btn_esp
        app.single_operator_select = app.single_operator_select_esp
        app.dayshift_select = app.dayshift_select_esp
        app.swingshift_select = app.swingshift_select_esp
        app.graveshift_select = app.graveshift_select_esp
        app.alloperators_select = app.alloperators_select_esp
        app.enter_operator_num = app.enter_operator_num_esp
        app.set_btn = app.set_btn_esp
        app.clear_btn = app.clear_btn_esp
        app.cancel_btn = app.cancel_btn_esp
        app.startdate_time_title = app.startdate_time_title_esp
        app.startdate_btn = app.startdate_btn_esp
        app.starttime_btn = app.starttime_btn_esp
        app.enddate_time_title = app.enddate_time_title_esp
        app.enddate_btn = app.enddate_btn_esp
        app.endtime_btn = app.endtime_btn_esp
        app.generating_report_text = app.generating_report_text_esp
        app.interpreting_reports_title = app.interpreting_reports_title_esp
        app.dismiss_btn = app.dismiss_btn_esp
        app.choose_startdate_time_title = app.choose_startdate_time_title_esp
        app.choose_enddate_time_title = app.choose_enddate_time_title_esp
        app.select_operator_title = app.select_operator_title_esp
        app.operator_ids_title = app.operator_ids_title_esp
        app.add_operator_btn = app.add_operator_btn_esp
        app.enter_id_num = app.enter_id_num_esp
        app.enter_operator_name = app.enter_operator_name_esp
        app.equipment_title = app.equipment_title_esp
        app.purple_select = app.purple_select_esp
        app.bag_select = app.bag_select_esp
        app.pictureframe_select = app.pictureframe_select_esp
        app.num_equip_cards_text = app.num_equip_cards_text_esp
        app.print_equip_ids_btn = app.print_equip_ids_btn_esp

        self.snackbar_show("Idioma cambiado a Espa\u00F1ol")

    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()


class OperatorIDScreen(MDScreen):
    shift = None

    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()

    def get_shiftname(self, *args):
        app.dayshift = self.dayshiftcheck.active
        app.swingshift = self.swingshiftcheck.active
        app.graveyardshift = self.graveyardshiftcheck.active

        if app.dayshift:
            self.shift = "Day"
        elif app.swingshift:
            self.shift = "Swing"
        elif app.graveyardshift:
            self.shift = "Graveyard"
        else:
            self.snackbar_show("[ERROR] Shift selection error")


    def assign_employee_num(self, desired_number:str, employee_name:str, shift:str):
        # Version of id_methods.assign_employee_num that catches errors so they
        # can be displayed as feedback messages on the app.
        while True:
            # Catch cases where the ID number is too many digits
            if len(desired_number) > 3:
                statustext = "Desired ID number is too long. Choose one with 3 or fewer digits."
                self.snackbar_show(statustext)
                break

            # If the number is good, load the data and either insert the number
            # if it isn't taken already, or throw an error and break the loop
            IDfilepath = data_assets.ID_data

            # Load the workbook with all sheets (that's what the None flag is for)
            # df is a dictionary of sheet names and dataframes of the sheets
            df = pd.read_excel(IDfilepath, None)
            sheetnames = df.keys()

            # Iterate through the sheets
            for sheetname in sheetnames:
                iddata = df[sheetname]

                # All personnel sheets have a Name column. Equipment sheets don't have
                # this column, so we use it to catch only the personnel relevant data.
                if "Name" in iddata:
                    IDexample = str(iddata.loc[0,"ID"])
                    prefix = IDexample[0:2]

                    if len(desired_number) == 3:
                        idnum_str = desired_number
                    else:
                        nzeros = 3 - len(desired_number)
                        idnum_str = nzeros*"0" + desired_number

                    # Combine the prefix and the ID number
                    num = prefix + idnum_str
                    num = int(num)

                    # Get the rows in leads and assistants that correspond to the desired number
                    numind = iddata.index[iddata["ID"] == num]
                    numind = numind[0]

                    if pd.isna(iddata.loc[numind, "Name"]):
                        # Update the Name column
                        iddata.loc[numind, "Name"] = employee_name
                        # Update the Date column
                        iddata.loc[numind, "Date"] = dt.date.today()
                        iddata.loc[numind, "Shift"] = shift
                        df[sheetname] = iddata
                        print("ID {} assigned to {}".format(num, employee_name))
                        id_methods.rewrite_whole_Excel_sheet(df, sheetnames)
                        id_methods.print_IDcard_5digit(num)

                        statustext = "ID {} assigned to {}".format(desired_number, employee_name)
                        self.snackbar_show(statustext)
                    else:
                        statustext = "[ERROR] ID number {} has already been assigned.".format(desired_number)
                        self.snackbar_show(statustext)
                        break
            break

        id_methods.print_all_employee_IDcards_PDF()


class EquipmentIDScreen(MDScreen):
    N_IDs = None
    # Snackbar for showing status messages (better than allocating space to labels)
    def snackbar_show(self, snackbartext):
        self.snackbar = Snackbar(text = snackbartext)
        self.snackbar.open()

    def set_N_equipment_IDs(self, *args):
        self.N_IDs = self.num_equip_cards.text
        if self.purplecheck.active is True:
            typestring = "purple"
        elif self.bagcheck.active is True:
            typestring = "bag"
        elif self.pictureframecheck.active is True:
            typestring = "pictureframe"
        else:
            raise ValueError("Invalid typestring")
        id_methods.N_new_equip_ids(int(self.N_IDs), typestring)
        print("{} new {} IDs printed".format(self.N_IDs, typestring))
        id_methods.get_most_recent_equipment_IDcards_PDF(typestring)


class OperatorContent(MDBoxLayout):
    pass


class OperatorEvaluationScreen(MDScreen):
    start_time_dialog = None        # Holding variable for time dialog
    end_time_dialog = None
    enddate = dt.date.today()
    startdate = enddate + relativedelta(months=-6)
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

    def update_report_label(self, *args):
        if app.singleoperator:
            if len(app.OPERATOR_LIST) == 0:
                if app.english is True:
                    labeltext = "NO OPERATOR SELECTED!\nStart: {} at {}\nEnd: {} at {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
                else:
                    labeltext = "¡NINGÚN OPERADOR SELECCIONADO!\nInicio: {} a las {}\nTerminación: {} a las {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
            else:
                if app.english is True:
                    labeltext = "Report will be generated for Operator {}\nStart: {} at {}\nEnd: {} at {}".format(app.OPERATOR_LIST[0], self.startdate, self.t_start, self.enddate, self.t_end)
                else:
                    labeltext = "Se generará un informe para el Operador {}\nInicio: {} a las {}\nTerminación: {} a las {}".format(app.OPERATOR_LIST[0], self.startdate, self.t_start, self.enddate, self.t_end)
        elif app.dayshift:
            if app.english is True:
                labeltext = "Report will be generated for Day Shift\nStart: {} at {}\nEnd: {} at {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
            else:
                labeltext = "Se generará un informe para el turno de día\nInicio: {} a las {}\nTerminación: {} a las {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
        elif app.swingshift:
            if app.english is True:
                labeltext = "Report will be generated for Swing Shift\nStart: {} at {}\nEnd: {} at {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
            else:
                labeltext = "Se generará un informe para el turno de turno\nInicio: {} a las {}\nTerminación: {} a las {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
        elif app.graveyardshift:
            if app.english is True:
                labeltext = "Report will be generated for Graveyard Shift\nStart: {} at {}\nEnd: {} at {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
            else:
                labeltext = "Se generará un informe para el turno de noche\nInicio: {} a las {}\nTerminación: {} a las {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
        elif app.alloperators:
            if app.english is True:
                labeltext = "Report will be generated for all operators\nStart: {} at {}\nEnd: {} at {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
            else:
                labeltext = "Se generará un informe para todos los operadores\nInicio: {} a las {}\nTerminación: {} a las {}".format(self.startdate, self.t_start, self.enddate, self.t_end)
        else:
            if app.english is True:
                raise ValueError("Error with operator selection")
            else:
                raise ValueError("Error con la selección del operador")

        self.evaluationparameterlabel.text = labeltext



    ### Functions related to Select Operator button ###
    def show_select_operator_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"

        if not self.select_operator_dialog:
            self.select_operator_dialog = MDDialog(
                title=app.select_operator_title,
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
                        text=app.cancel_btn,
                        font_style="Button",
                        on_release=self.close_select_operator_dialog
                    ),
                ],
            )
        self.select_operator_dialog.open()

    # def test_dialog_access(self, *args):
    #     print(self.select_operator_dialog.content_cls.dayshiftcheck.active)

    def set_operator_list(self, *args):
        app.singleoperator = self.select_operator_dialog.content_cls.singleoperatorcheck.active
        app.dayshift = self.select_operator_dialog.content_cls.dayshiftcheck.active
        app.swingshift = self.select_operator_dialog.content_cls.swingshiftcheck.active
        app.graveyardshift = self.select_operator_dialog.content_cls.graveyardshiftcheck.active
        app.alloperators = self.select_operator_dialog.content_cls.alloperatorscheck.active

        if app.singleoperator:
            opnum_str = self.select_operator_dialog.content_cls.operatornumbertext.text
            if len(opnum_str) > 0:
                opnum = int(opnum_str)
                app.OPERATOR_LIST = [opnum]
                # self.snackbar_show(app.OPERATOR_LIST)
                self.update_report_label()
                print("Operator: {}\nType: {}".format(app.OPERATOR_LIST, type(app.OPERATOR_LIST)))
            else:
                print("Empty number")
        elif app.dayshift:
            app.OPERATOR_LIST = cycle.get_operator_list("Day")
            self.update_report_label()
            print(app.OPERATOR_LIST)
            # print("DAY SHIFT SELECTION FEATURE IS NOT YET COMPLETE")
        elif app.swingshift:
            app.OPERATOR_LIST = cycle.get_operator_list("Swing")
            self.update_report_label()
            print(app.OPERATOR_LIST)
        elif app.graveyardshift:
            app.OPERATOR_LIST = cycle.get_operator_list("Graveyard")
            self.update_report_label()
            print(app.OPERATOR_LIST)
        elif app.alloperators:
            # directory = 'Z:\\Production\\ID_Tracking\\ID_numbers\\'
            # filepath = directory + "ID_data.xlsx"
            filepath = data_assets.ID_data
            df = id_methods.get_all_employee_nums()
            allnums = list(df["ID"])
            allnums = [int(num) for num in allnums]
            app.OPERATOR_LIST = allnums
            print(app.OPERATOR_LIST)
            self.update_report_label()
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
                title=app.choose_startdate_time_title,
                buttons=[
                    MDRaisedButton(
                        text=app.startdate_btn,
                        font_style="Button",
                        on_release=self.show_start_date_picker
                    ),
                    MDRaisedButton(
                        text=app.starttime_btn,
                        font_style="Button",
                        on_release=self.show_start_time_picker
                    ),
                    MDRaisedButton(
                        text=app.set_btn,
                        font_style="Button",
                        md_bg_color=theme_cls.accent_color,
                        on_release=self.set_start_time_dialog
                    ),
                    MDFlatButton(
                        text=app.clear_btn,
                        font_style="Button",
                        theme_text_color="Custom",
                        on_release=self.clear_start_time_dialog
                    ),
                    MDFlatButton(
                        text=app.cancel_btn,
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
        self.update_report_label()
        print(self.t_start)

    def show_start_date_picker(self, *args):
        start_date_dialog = MDDatePicker()
        start_date_dialog.bind(on_save=self.on_start_date_save)
        start_date_dialog.open()

    def on_start_date_save(self, instance, value, date_range):
        self.startdate = value
        self.update_report_label()
        print("Starting date is {}, {}".format(self.startdate, type(self.startdate)))
        if self.startdate < dt.date(2022,2,8):
            if app.english is True:
                statustext = "WARNING: Starting dates earlier than Feb 2, 2022 may cause errors."
            else:
                statustext = "ADVERTENCIA: Las fechas de inicio anteriores al 2 de febrero de 2022 pueden generar errores."
            self.snackbar_show(statustext)

    def set_start_time_dialog(self, *args):
        self.start_time_dialog.dismiss(force=True)
        if self.t_start is None or self.startdate is None:
            if app.english is True:
                statustext = "Missing start time or date."
            else:
                statustext = "Falta la fecha o la hora de inicio."
            self.snackbar_show(statustext)
        if self.startdate < dt.date(2022,2,8):
            if app.english is True:
                statustext = "WARNING: Starting dates earlier than Feb 2, 2022 may cause errors."
            else:
                statustext = "ADVERTENCIA: Las fechas de inicio anteriores al 2 de febrero de 2022 pueden generar errores."
            self.snackbar_show(statustext)
        self.start_time_dialog = None
        print(self.t_start)
        print(self.startdate)

    def clear_start_time_dialog(self, *args):
        self.t_start = None
        self.startdate = None
        if app.english is True:
            statustext = "STARTING DATE AND TIME CLEARED. Please select a new date and time before generating report."
        else:
            statustext = "FECHA Y HORA DE INICIO LIMPIA. Seleccione una nueva fecha y hora antes de generar el informe."
        self.snackbar_show(statustext)
        # self.start_time_dialog = None

    def cancel_start_time_dialog(self, *args):
        self.start_time_dialog.dismiss(force=True)
        print(self.startdate, self.t_start)
        if not self.t_start or not self.startdate:
            print(self.startdate, self.t_start)
            if app.english is True:
                statustext = "Missing start time or date."
            else:
                statustext = "Falta la fecha o la hora de inicio."
            self.snackbar_show(statustext)
        self.start_time_dialog = None

    ### Functions for choosing end date and time ###
    def show_end_time_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"
        print("Default End time: {}, {}".format(self.t_end, type(self.t_end)))

        if not self.end_time_dialog:
            self.end_time_dialog = MDDialog(
                title=app.choose_enddate_time_title,
                buttons=[
                    MDRaisedButton(
                        text=app.enddate_btn,
                        font_style="Button",
                        on_release=self.show_end_date_picker
                    ),
                    MDRaisedButton(
                        text=app.endtime_btn,
                        font_style="Button",
                        on_release=self.show_end_time_picker
                    ),
                    MDRaisedButton(
                        text=app.set_btn,
                        font_style="Button",
                        md_bg_color=theme_cls.accent_color,
                        on_release=self.set_end_time_dialog
                    ),
                    MDFlatButton(
                        text=app.clear_btn,
                        font_style="Button",
                        theme_text_color="Custom",
                        text_color=theme_cls.primary_color,
                        on_release=self.clear_end_time_dialog
                    ),
                    MDFlatButton(
                        text=app.cancel_btn,
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
        self.update_report_label()
        print(self.t_end)

    def show_end_date_picker(self, *args):
        end_date_dialog = MDDatePicker()
        end_date_dialog.bind(on_save=self.on_end_date_save)
        end_date_dialog.open()

    def on_end_date_save(self, instance, value, date_range):
        self.enddate = value
        self.update_report_label()
        print("Ending date is {}, {}".format(self.enddate, type(self.enddate)))

    def set_end_time_dialog(self, *args):
        self.end_time_dialog.dismiss(force=True)
        if not self.t_end:
            if app.english is True:
                statustext = "MISSING END TIME"
            else:
                statustext = "FALTA LA HORA DE FINALIZACIÓN"
            self.snackbar_show(statustext)
        # else:
        #     statustext = "GOOD TO GO"
        self.end_time_dialog = None
        print(self.t_end)
        print(self.enddate)

    def clear_end_time_dialog(self, *args):
        self.t_end = None
        self.enddate = None
        if app.english is True:
            statustext = "ENDING DATE AND TIME CLEARED. Please select a new date and time before generating report."
        else:
            statustext = "ENDING DATE AND TIME CLEARED. Please select a new date and time before generating report."
        self.snackbar_show(statustext)
        # self.end_time_dialog = None

    def cancel_end_time_dialog(self, *args):
        self.end_time_dialog.dismiss(force=True)
        print(self.enddate, self.t_end)
        if not self.t_end or not self.enddate:
            print(self.enddate, self.t_end)
            if app.english is True:
                statustext = "MISSING ENDING DATE OR TIME."
            else:
                statustext = "FALTA FECHA U HORA DE FINALIZACIÓN."
            self.snackbar_show(statustext)
        self.end_time_dialog = None


    ### Functions for showing the operator evaluation info dialog ###
    def show_evaluation_info_dialog(self, *args):
        theme_cls = ThemeManager()
        theme_cls.theme_style = "Light"
        theme_cls.primary_palette = "Teal"
        theme_cls.primary_hue = "400"

        if app.english is True:
            infotext =  """Operator reports are displayed with three box plots. The first one illustrates the cycle times for the chosen operator as a lead, the second shows the operator's shift, and the third shows all cycle times at RockWell over the same period.

Compare the medians for each plot to see what an operator averages most of the time. A median below the team's median indicates that the operator averages faster cycle times than the team.

The other main feature to look for is how compact or stretched the box plot is. A box plot that is very compact means the operator is very consistent at hitting their cycle times, while a tall or stretched box plot indicates an operator that is variable or inconsistent.

Outlier cases, if they exist, are shown as small circles above or below the box plot. These are cases that should be noted, but can be considered not typical, and in some cases can be ignored. These might happen due to conditions outside the operator's control, such as a bag change, but they can still be due to operator factors.

Box plots are only valid with at least 5 data points. More sample points are better. For a proper evaluation, try to choose an evaluation period with at least 100 sample points for each box plot. The number of samples in each box plot is displayed below the chart on the generated Operator Report.
                    """
        else:
            infotext =  """Los informes del operador se muestran con tres diagramas de caja. El primero ilustra los tiempos de ciclo para el operador elegido como guía, el segundo muestra el turno del operador y el tercero muestra todos los tiempos de ciclo en RockWell durante el mismo período.

Compare las medianas de cada gráfico para ver cuál es el promedio de un operador la mayor parte del tiempo. Una mediana por debajo de la mediana del equipo indica que el operador promedia tiempos de ciclo más rápidos que el equipo.

La otra característica principal a buscar es qué tan compacto o estirado es el diagrama de caja. Un diagrama de caja que es muy compacto significa que el operador es muy consistente en alcanzar sus tiempos de ciclo, mientras que un diagrama de caja alto o estirado indica un operador que es variable o inconsistente.

Los casos atípicos, si existen, se muestran como pequeños círculos encima o debajo del diagrama de caja. Estos son casos que deben tenerse en cuenta, pero pueden considerarse no típicos y, en algunos casos, pueden ignorarse. Estos pueden ocurrir debido a condiciones fuera del control del operador, como un cambio de bolsa, pero aún pueden deberse a factores del operador.

Los diagramas de caja solo son válidos con al menos 5 puntos de datos. Más puntos de muestra son mejores. Para una evaluación adecuada, intente elegir un período de evaluación con al menos 100 puntos de muestra para cada diagrama de caja. El número de muestras en cada diagrama de caja se muestra debajo del gráfico en el Informe del operador generado.
                    """

        if not self.evaluation_info_dialog:
            self.evaluation_info_dialog = MDDialog(
                title=app.interpreting_reports_title,
                text=infotext,
                buttons=[
                    MDFlatButton(
                        text=app.dismiss_btn,
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
    def get_operator_reports(self, *args):
        if (self.startdate or self.enddate or self.t_start or self.t_end) is None:
            raise ValueError("A date or time is missing")
        else:
            dtstart = dt.datetime.combine(self.startdate, self.t_start)
            dtend = dt.datetime.combine(self.enddate, self.t_end)

        # singleoperator = self.select_operator_dialog.content_cls.singleoperatorcheck.active
        # dayshift = self.select_operator_dialog.content_cls.dayshiftcheck.active
        # swingshift = self.select_operator_dialog.content_cls.swingshiftcheck.active
        # graveyardshift = self.select_operator_dialog.content_cls.graveyardshiftcheck.active
        # alloperators = self.select_operator_dialog.content_cls.alloperatorscheck.active

        if app.singleoperator:
            if len(app.OPERATOR_LIST) > 0:
                opnum = app.OPERATOR_LIST[0]
                cycle.get_specific_operator_report(opnum, dtstart, dtend)
            else:
                if app.english is True:
                    statustext = "No operator selected"
                else:
                    statustext = "Ningún operador seleccionado"
                self.snackbar_show(statustext)
        elif app.dayshift:
            cycle.get_operator_report_by_list(app.OPERATOR_LIST, "Day", dtstart, dtend)
        elif app.swingshift:
            cycle.get_operator_report_by_list(app.OPERATOR_LIST, "Swing", dtstart, dtend)
        elif app.graveyardshift:
            cycle.get_operator_report_by_list(app.OPERATOR_LIST, "Graveyard", dtstart, dtend)
        elif app.alloperators:
            cycle.get_all_operator_reports(dtstart, dtend)
        else:
            print("Error with report generation.")


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
    singleoperator = True
    dayshift = False
    swingshift = False
    graveyardshift = False
    alloperators = False

    ### Labels in English ###
    home_title_en = "Home"
    operator_eval_title_en = "Operator Evaluation"
    navigation_title_en = "Navigation"
    select_operator_btn_en = "Select Operator"
    startdate_time_btn_en = "Starting Date/Time"
    enddate_time_btn_en = "Ending Date/Time"
    generate_report_btn_en = "Generate Report"
    single_operator_select_en = "Single Operator"
    dayshift_select_en = "Day Shift"
    swingshift_select_en = "Swing Shift"
    graveshift_select_en = "Graveyard Shift"
    alloperators_select_en = "All Operators"
    enter_operator_num_en = "Enter Operator Number"
    set_btn_en = "Set"
    clear_btn_en = "Clear"
    cancel_btn_en = "Cancel"
    startdate_time_title_en = "Choose Start Date & Time"
    startdate_btn_en = "Start Date"
    starttime_btn_en = "Start Time"
    enddate_time_title_en = "Choose End Date & Time"
    enddate_btn_en = "End Date"
    endtime_btn_en = "End Time"
    generating_report_text_en = "Generating Report..."
    interpreting_reports_title_en = "Interpreting Operator Reports"
    dismiss_btn_en = "Dismiss"
    choose_startdate_time_title_en = "Choose Start Date & Time"
    choose_enddate_time_title_en = "Choose End Date & Time"
    select_operator_title_en = "Select Operator(s)"
    operator_ids_title_en = "Operator IDs"
    add_operator_btn_en = "Add Operator"
    enter_id_num_en = "Enter a number with up to 3 digits"
    enter_operator_name_en = "Enter operator's name"
    equipment_title_en = "Equipment IDs"
    purple_select_en = "Purple"
    bag_select_en = "Bag"
    pictureframe_select_en = "Picture Frame"
    num_equip_cards_text_en = "Enter the number of new equipment IDs to generate."
    print_equip_ids_btn_en = "Print Equipment IDs"


    ### Labels in Spanish ###
    home_title_esp = "Inicio"
    operator_eval_title_esp = "Evaluaci\u00F3n del Operador"
    navigation_title_esp = "Navegaci\u00F3n"
    select_operator_btn_esp = "Seleccionar operador"
    startdate_time_btn_esp = "Fecha/hora de inicio"
    enddate_time_btn_esp = "Fecha/hora de finalizaci\u00F3n"
    generate_report_btn_esp = "Generar informe"
    single_operator_select_esp = "Operador \u00FAnico"
    dayshift_select_esp = "Turno de dia"
    swingshift_select_esp = "Turno cambiante"
    graveshift_select_esp = "Turno de noche"
    alloperators_select_esp = "Todos los operadores"
    enter_operator_num_esp = "Ingrese el n\u00FAmero de operador"
    set_btn_esp = "Colocar"
    clear_btn_esp = "Limpiar"
    cancel_btn_esp = "Cancelar"
    startdate_time_title_esp = "Elija fecha y hora de inicio"
    startdate_btn_esp = "Fecha de inicio"
    starttime_btn_esp = "Hora de inicio"
    enddate_time_title_esp = "Elija la fecha y hora de finalizaci\u00F3n"
    enddate_btn_esp = "Fecha final"
    endtime_btn_esp = "Hora de finalizaci\u00F3n"
    generating_report_text_esp = "Generando informe..."
    interpreting_reports_title_esp = "Interpretación de los informes del operador"
    dismiss_btn_esp = "Descartar"
    choose_startdate_time_title_esp = "Elija fecha y hora de inicio"
    choose_enddate_time_title_esp = "Elija la fecha y hora de finalización"
    select_operator_title_esp = "Seleccionar operador(s)"
    operator_ids_title_esp = "ID de operador"
    add_operator_btn_esp = "Agregar operador"
    enter_id_num_esp = "Introduce un número de hasta 3 dígitos"
    enter_operator_name_esp = "Ingrese el nombre del operador"
    equipment_title_esp = "ID de equipo"
    purple_select_esp = "Purple"
    bag_select_esp = "Bag"
    pictureframe_select_esp = "Picture Frame"
    num_equip_cards_text_esp = "Ingrese el número de ID de nuevos equipos para generar."
    print_equip_ids_btn_esp = "Imprimir IDs de equipos"


    ### Reference variables for text labels ###
    home_title = StringProperty(home_title_en)
    operator_eval_title = StringProperty(operator_eval_title_en)
    navigation_title = StringProperty(navigation_title_en)
    select_operator_btn = StringProperty(select_operator_btn_en)
    startdate_time_btn = StringProperty(startdate_time_btn_en)
    enddate_time_btn = StringProperty(enddate_time_btn_en)
    generate_report_btn = StringProperty(generate_report_btn_en)
    single_operator_select = StringProperty(single_operator_select_en)
    dayshift_select = StringProperty(dayshift_select_en)
    swingshift_select = StringProperty(swingshift_select_en)
    graveshift_select = StringProperty(graveshift_select_en)
    alloperators_select = StringProperty(alloperators_select_en)
    enter_operator_num = StringProperty(enter_operator_num_en)
    set_btn = StringProperty(set_btn_en)
    clear_btn = StringProperty(clear_btn_en)
    cancel_btn = StringProperty(cancel_btn_en)
    startdate_time_title = StringProperty(startdate_time_title_en)
    startdate_btn = StringProperty(startdate_btn_en)
    starttime_btn = StringProperty(starttime_btn_en)
    enddate_time_title = StringProperty(enddate_time_title_en)
    enddate_btn = StringProperty(enddate_btn_en)
    endtime_btn = StringProperty(endtime_btn_en)
    generating_report_text = StringProperty(generating_report_text_en)
    interpreting_reports_title = StringProperty(interpreting_reports_title_en)
    dismiss_btn = StringProperty(dismiss_btn_en)
    choose_startdate_time_title = StringProperty(choose_startdate_time_title_en)
    choose_enddate_time_title = StringProperty(choose_enddate_time_title_en)
    select_operator_title = StringProperty(select_operator_title_en)
    operator_ids_title = StringProperty(operator_ids_title_en)
    add_operator_btn = StringProperty(add_operator_btn_en)
    enter_id_num = StringProperty(enter_id_num_en)
    enter_operator_name = StringProperty(enter_operator_name_en)
    equipment_title = StringProperty(equipment_title_en)
    purple_select = StringProperty(purple_select_en)
    bag_select = StringProperty(bag_select_en)
    pictureframe_select = StringProperty(pictureframe_select_en)
    num_equip_cards_text = StringProperty(num_equip_cards_text_en)
    print_equip_ids_btn = StringProperty(print_equip_ids_btn_en)

    english = True

    def build(self):
        # App settings
        # self.theme_cls.colors = colors
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "400"
        # self.theme_cls.accent_palette = "Amber"
        self.title = "Rockwell ID & Evaluation Tool"

        # self.icon = "assets/Boxplot.png"

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
