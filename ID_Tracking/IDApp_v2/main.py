import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDateEdit,
    QRadioButton, QButtonGroup, QHBoxLayout, QSpinBox, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, QDate
import datetime as dt
from dateutil.relativedelta import relativedelta
import libs.cycle_time_methods_v2 as cycle
import libs.data_assets as data_assets
import libs.id_methods as id_methods
import libs.api_config_vars as api
import pandas as pd


# Global Variables
dtdate_start = dt.date.today() - relativedelta(months=3)
dtdate_end = dt.date.today()
dtstart = dt.datetime.combine(dtdate_start, dt.time(0, 0, 0))
dtend = dt.datetime.combine(dtdate_end, dt.time(23, 59, 59))


# Main Application Window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set the window size and layout
        self.setWindowTitle("Operator Evaluation and ID Assignment")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        # Create a horizontal layout to hold both sections
        main_layout = QHBoxLayout()

        # Create the Operator Evaluation section
        operator_eval_layout = QVBoxLayout()

        # Date range selection
        eval_header = QLabel("Operator Evaluation:")
        eval_header.setStyleSheet("font-weight: bold; font-size: 16px")
        operator_eval_layout.addWidget(eval_header)
        operator_eval_layout.addWidget(QLabel("Select Date Range:"))
        self.date_start = QDateEdit(calendarPopup=True)
        self.date_start.setDate(QDate(dtdate_start.year, dtdate_start.month, dtdate_start.day))
        self.date_end = QDateEdit(calendarPopup=True)
        self.date_end.setDate(QDate(dtdate_end.year, dtdate_end.month, dtdate_end.day))
        operator_eval_layout.addWidget(self.date_start)
        operator_eval_layout.addWidget(self.date_end)

        # Operator selection
        operator_eval_layout.addWidget(QLabel("Select Operators:"))

        self.radio_group = QButtonGroup(self)
        self.single_operator_radio = QRadioButton("Single Operator")
        self.day_shift_radio = QRadioButton("Day Shift")
        self.swing_shift_radio = QRadioButton("Swing Shift")

        self.radio_group.addButton(self.single_operator_radio, 1)
        self.radio_group.addButton(self.day_shift_radio, 2)
        self.radio_group.addButton(self.swing_shift_radio, 3)
        
        # Set default radio button selection
        self.single_operator_radio.setChecked(True)

        operator_eval_layout.addWidget(self.single_operator_radio)
        operator_eval_layout.addWidget(self.day_shift_radio)
        operator_eval_layout.addWidget(self.swing_shift_radio)

        # Operator number input (enabled only for single operator)
        self.operator_number_input = QSpinBox()
        self.operator_number_input.setRange(1, 999)
        self.single_operator_radio.toggled.connect(self.toggle_operator_input)
        operator_eval_layout.addWidget(QLabel("Operator Number:"))
        operator_eval_layout.addWidget(self.operator_number_input)

        # Generate report button
        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_report)
        operator_eval_layout.addWidget(self.generate_report_button)

        # Output area
        self.output_label = QLabel("")
        operator_eval_layout.addWidget(self.output_label)

        # Add a vertical line to separate the sections
        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.VLine)
        separator_line.setFrameShadow(QFrame.Sunken)

        # Create the Operator ID Assignment section
        operator_id_layout = QVBoxLayout()
        
        id_header = QLabel("Operator ID Assignment:")
        id_header.setStyleSheet("font-weight: bold; font-size: 16px;")
        operator_id_layout.addWidget(id_header)

        # Operator Name
        operator_id_layout.addWidget(QLabel("Enter Operator Name:"))
        self.employee_name_input = QLineEdit()
        operator_id_layout.addWidget(self.employee_name_input)

        # Operator number input
        operator_id_layout.addWidget(QLabel("Select 3-Digit Operator Number:"))
        self.select_operator_number_input = QSpinBox()
        self.select_operator_number_input.setRange(1, 999)
        operator_id_layout.addWidget(self.select_operator_number_input)

        # Shift selection
        operator_id_layout.addWidget(QLabel("Select Shift:"))
        self.shift_combo = QComboBox()
        self.shift_combo.addItem("Day Shift", "1")
        self.shift_combo.addItem("Swing Shift", "2")
        operator_id_layout.addWidget(self.shift_combo)

        # Select button
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.assign_employee_num)
        operator_id_layout.addWidget(self.select_button)

        # Output area
        self.select_operator_output = QLabel("")
        operator_id_layout.addWidget(self.select_operator_output)

        # Add both sections to the main layout with equal stretch factors
        main_layout.addLayout(operator_eval_layout, stretch=1)
        main_layout.addWidget(separator_line)
        main_layout.addLayout(operator_id_layout, stretch=1)

        # Add the main layout to the window layout
        layout.addLayout(main_layout)

    def toggle_operator_input(self):
        # Enable or disable the operator number input based on radio button
        self.operator_number_input.setEnabled(self.single_operator_radio.isChecked())

    def generate_report(self):
        # Read input values
        radio_value = self.radio_group.checkedId()
        operator_number = self.operator_number_input.value()

        if radio_value == 1:
            if operator_number == 0:
                self.output_label.setText("Error: Operator number is required for single operator report")
            else:
                self.output_label.setText(f"Report generated for operator {operator_number}")
                self.single_operator_function(operator_number)
        elif radio_value == 2:
            self.output_label.setText("Report generated for day shift")
            self.day_shift_function()
        elif radio_value == 3:
            self.output_label.setText("Report generated for swing shift")
            self.swing_shift_function()

    def assign_employee_num(self):
        # Assign employee number logic
        employee_name = self.employee_name_input.text()
        desired_number = self.select_operator_number_input.value()
        shift_input = self.shift_combo.currentData()

        if desired_number and employee_name:
            # Call your custom method to assign employee number
            # result = id_methods.assign_employee_num(desired_number, employee_name, shift_input)
            shift_dict = {'1': 'Day',
                          '2': 'Swing',
                          '3': 'Graveyard'}
            shift = shift_dict[shift_input]
            # Version of id_methods.assign_employee_num that catches errors so they
            # can be displayed as feedback messages on the app.
            while True:
                # If the number is good, load the data and either insert the number
                # if it isn't taken already, or throw an error and break the loop
                IDfilepath = data_assets.ID_data
        
                # Load the workbook with all sheets (that's what the None flag is for)
                # df is a dictionary of sheet names and dataframes of the sheets
                df = pd.read_excel(IDfilepath, None)
                sheetnames = df.keys()
                
                # print(f'Desired number:\t{desired_number}')
        
                # Iterate through the sheets
                for sheetname in sheetnames:
                    iddata = df[sheetname]
        
                    # All personnel sheets have a Name column. Equipment sheets don't have
                    # this column, so we use it to catch only the personnel relevant data.
                    if "Name" in iddata:
                        IDexample = str(iddata.loc[0,"ID"])
                        prefix = IDexample[0:2]
                        
        
                        if len(str(desired_number)) == 3:
                            idnum_str = str(desired_number)
                            # print(f'\nFound desired number with 3 digits:\nidnum_str: {idnum_str}')
                        else:
                            nzeros = 3 - len(str(desired_number))
                            idnum_str = nzeros*"0" + str(desired_number)
                            # print(f'\nInitial number had less than 3 digits.\nidnum_str: {idnum_str}')
        
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
                            # print("ID {} assigned to {}".format(num, employee_name))
                            id_methods.rewrite_whole_Excel_sheet(df, sheetnames)
                            id_methods.print_IDcard_5digit(num)
        
                            statustext = "ID {} assigned to {}".format(desired_number, employee_name)
                            # self.snackbar_show(statustext)
                        else:
                            statustext = "[ERROR] ID number {} has already been assigned.".format(desired_number)
                            # print(statustext)
                            # self.snackbar_show(statustext)
                            break
                break
        
            id_methods.print_all_employee_IDcards_PDF()
            self.select_operator_output.setText(statustext)
            

    # Dummy functions for testing purposes
    def single_operator_function(self, operator_number):
        global dtstart, dtend
        operator_list = [operator_number]
        df_eval = cycle.load_operator_data(dtstart, dtend)[0]

        # Remove faulty duplicates
        df_eval = cycle.clean_duplicate_times(df_eval)
        cycle.get_operator_stats_by_list(df_eval, operator_list, None)
        # print(f"Running report for single operator: {operator_number}")
        # print(f"Single operator function called for operator {operator_number}")

    def day_shift_function(self):
        global dtstart, dtend
        IDfilepath = data_assets.ID_data
        daylist, _, _ = id_methods.get_shift_lists(IDfilepath)
        df_eval = cycle.load_operator_data(dtstart, dtend)[0]
        cycle.get_operator_stats_by_list(df_eval, daylist)
        # print("Day shift function called")

    def swing_shift_function(self):
        global dtstart, dtend
        IDfilepath = data_assets.ID_data
        _, swinglist, _ = id_methods.get_shift_lists(IDfilepath)
        df_eval = cycle.load_operator_data(dtstart, dtend)[0]
        cycle.get_operator_stats_by_list(df_eval, swinglist)
        # print("Swing shift function called")


# Main program execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())