from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import datetime as dt
from dateutil.relativedelta import relativedelta
import webbrowser
from threading import Timer
import psutil
import os
import time
import signal
import libs.cycle_time_methods_v2 as cycle
import libs.data_assets as data_assets
import libs.id_methods as id_methods
import pandas as pd

# Global Variables
dtdate_start = dt.date.today() - relativedelta(months=3)
dtdate_end = dt.date.today()
dtstart = dt.datetime.combine(dtdate_start, dt.time(0, 0, 0))
dtend = dt.datetime.combine(dtdate_end, dt.time(23, 59, 59))

# Layout Definitions
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.Img(src="assets/RockwellFullLogo.png", alt="Rockwell Logo"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Operator Evaluation", href="/operator_evaluation", active="exact"),
                dbc.NavLink("Operator IDs", href="/operator_id", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

operator_evaluation_content = html.Div([
    html.Div(html.H3("Operator Evaluation"), style={"margin-bottom": "10px"}),
    html.Hr(),
    html.Div(html.H5("Select Date Range:"), style={"margin-bottom": "10px"}),
    dcc.DatePickerRange(
        id='date-picker-range',
        min_date_allowed=dt.date(2022, 1, 1),
        max_date_allowed=dt.date.today(),
        initial_visible_month=dt.date.today(),
        start_date=dtdate_start,
        end_date=dtdate_end,
        style={"width": "100%", "margin-bottom": "30px"}
    ),
    html.Div(id='date-output'),

    html.Div(
        [
            html.Div(html.H5("Select Operators:"), style={"margin-bottom": "10px"}),

            html.Div(dcc.RadioItems(id='operator_radio',
                                    options=[
                                        {'label': 'Single Operator', 'value': '1'},
                                        {'label': 'Day Shift', 'value': '2'},
                                        {'label': 'Swing Shift', 'value': '3'}
                                    ],
                                    value='1',
                                    inputStyle={"margin-right": "10px"}
                                    ),
                    style={"display": "inline-block",}),

            html.Div(dcc.Input(
                id="operator_number_input",
                type="number",
                min=1,
                max=999,
                step=1,
                placeholder="Operator Number",
                style={'width': 150}),
                style={"display": "inline-block",
                       "vertical-align": "top",
                       "margin-left": "20px"})
        ],
        style={"display": "inline-block", "margin-bottom": "20px"}),

    html.Div([dbc.Button("Generate Report", id="generate-report", n_clicks=0, style={})],
             style={"display": "flex",
                    "flex-direction": "column",
                    "width": 150}),
    html.Div(id='output'),
])

operator_id_content = html.Div([
    html.H3("Operator IDs"),
    html.Hr(),
    html.Div(
        [
            html.Div(html.H5("Enter Operator Name:"), style={"margin-bottom": "10px"}),
            html.Div(dcc.Input(
                id="employee_name_input",
                type="text",
                placeholder="Operator Name",
                style={'width': 150}),
                style={"display": "inline-block",
                       "vertical-align": "top",})
        ],
        style={"display": "block", "margin-bottom": "20px"}),
    
    html.Div(
        [
            html.Div(html.H5("Select 3-Digit Operator Number:"), style={"margin-bottom": "10px"}),
            html.Div(dcc.Input(
                id="select_operator_number_input",
                type="number",
                min=0,
                max=999,
                step=1,
                placeholder="Operator Number",
                style={'width': 150}),
                style={"display": "inline-block",
                       "vertical-align": "top",})
        ],
        style={"display": "block", "margin-bottom": "20px"}),
    
    html.Div(
        [
            html.Div(html.H5("Select Shift:"), style={"margin-bottom": "10px"}),

            html.Div(dcc.RadioItems(id='selected_shift',
                                    options=[
                                        {'label': 'Day Shift', 'value': '1'},
                                        {'label': 'Swing Shift', 'value': '2'}
                                    ],
                                    value='1',
                                    inputStyle={"margin-right": "10px"}
                                    ),
                    style={"display": "inline-block",}),
        ],
        style={"display": "block", "margin-bottom": "20px"}),

    html.Div([dbc.Button("Select", id="select_operator_number", n_clicks=0, style={})],
             style={"display": "flex",
                    "flex-direction": "column",
                    "width": 150}),
    html.Div(id='select_operator_output'),
    html.Div(id='select-operator-number-output'),
])

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    sidebar,
    content
])

# Callbacks
@app.callback(
    Output("operator_number_input", "disabled"),
    [Input("operator_radio", "value")]
)
def update_input_disabled(selected_option):
    return selected_option != "1"

@app.callback(
    Output("output", "children"),
    [Input("generate-report", "n_clicks")],
    [State("operator_radio", "value"),
     State("operator_number_input", "value")]
)
def generate_report(n_clicks, radio_value, operator_number):
    if n_clicks > 0:
        if radio_value == '1':
            if operator_number is None or operator_number == "":
                print("Error: Operator number is required for single operator report")
                return "Error: Operator number is required for single operator report"
            else:
                single_operator_function(operator_number)
                return f"Report generated for operator {operator_number}"
        elif radio_value == '2':
            day_shift_function()
            return "Report generated for day shift"
        elif radio_value == '3':
            swing_shift_function()
            return "Report generated for swing shift"
    return ""

@app.callback(
    Output("date-output", "children"),
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")],
)
def update_dtstart_dtend(start_date, end_date):
    if start_date and end_date:
        date_format = '%Y-%m-%d'
        starttime = dt.time(0, 0, 0)
        endtime = dt.time(23, 59, 59)

        startdate = dt.datetime.strptime(start_date, date_format)
        enddate = dt.datetime.strptime(end_date, date_format)

        global dtstart, dtend
        dtstart = dt.datetime.combine(startdate, starttime)
        dtend = dt.datetime.combine(enddate, endtime)
        
        # print(f'dtstart:\t{dtstart}')
        # print(f'dtend:\t{dtend}')

    return ''

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/operator_evaluation':
        return operator_evaluation_content
    elif pathname == '/operator_id':
        return operator_id_content
    else:
        return operator_evaluation_content
    # else:
    #     return html.Div([
    #         html.H3("Welcome to the Dash app. Select a page from the sidebar.")
        # ])

@app.callback(Output("select-operator-number-output", "children"),
              [Input("select_operator_number", "n_clicks")],
               [State("select_operator_number_input", "value"),
                State("employee_name_input", "value"),
               State("selected_shift", "value")])
def assign_employee_num(n_clicks, desired_number:int, employee_name:str, shift_input:str):
    if n_clicks > 0:
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
            
            print(f'Desired number:\t{desired_number}')
    
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
                        print(f'\nFound desired number with 3 digits:\nidnum_str: {idnum_str}')
                    else:
                        nzeros = 3 - len(str(desired_number))
                        idnum_str = nzeros*"0" + str(desired_number)
                        print(f'\nInitial number had less than 3 digits.\nidnum_str: {idnum_str}')
    
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
                        # self.snackbar_show(statustext)
                    else:
                        statustext = "[ERROR] ID number {} has already been assigned.".format(desired_number)
                        print(statustext)
                        # self.snackbar_show(statustext)
                        break
            break
    
        id_methods.print_all_employee_IDcards_PDF()
        
    return ''

# Other Functions
def open_browser():
    webbrowser.open_new("http://localhost:{}".format(port))

def find_and_kill_process_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if name in proc.info['name']:
            os.kill(proc.info['pid'], signal.SIGTERM)

# Dummy functions for demonstration
def single_operator_function(operator_number):
    global dtstart, dtend
    operator_list = [operator_number]
    df_eval = cycle.load_operator_data(dtstart, dtend)[0]

    # Remove faulty duplicates
    df_eval = cycle.clean_duplicate_times(df_eval)
    cycle.get_operator_stats_by_list(df_eval, operator_list, None)
    # print(f"Running report for single operator: {operator_number}")

def day_shift_function():
    global dtstart, dtend
    IDfilepath = data_assets.ID_data
    daylist, _, _ = id_methods.get_shift_lists(IDfilepath)
    df_eval = cycle.load_operator_data(dtstart, dtend)[0]
    cycle.get_operator_stats_by_list(df_eval, daylist)
    # print("Running report for day shift")

def swing_shift_function():
    global dtstart, dtend
    IDfilepath = data_assets.ID_data
    _, swinglist, _ = id_methods.get_shift_lists(IDfilepath)
    df_eval = cycle.load_operator_data(dtstart, dtend)[0]
    cycle.get_operator_stats_by_list(df_eval, swinglist)
    # print("Running report for swing shift")

def run_app():
    try:
        app.run_server(port=port, debug=False)
    except OSError as e:
        if e.errno == 98:
            print("Port is already in use. Killing the existing process and restarting...")
            find_and_kill_process_by_name('python')
            time.sleep(2)
            app.run_server(port=port, debug=False)

# Main
if __name__ == "__main__":
    port = 8050
    Timer(1, open_browser).start()
    run_app()

