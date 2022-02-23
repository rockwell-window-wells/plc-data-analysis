"""employee_cycle_times.py: Code for taking in a CSV downloaded from StrideLinx
and outputting all the cycle times for each employee, as well as averages
and other useful metrics.

Date created: 1/26/2022
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from fpdf import FPDF
import seaborn as sns
from sklearn.linear_model import LinearRegression

class OperatorStatsPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297

    def header(self):
        # Custom logo and positioning
        self.image('assets/RockwellFullLogo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 11)
        self.cell(self.WIDTH - 80)
        self.cell(60, 1, 'Mold Operator Stats', 0, 0, 'R')
        self.ln(20)

    def footer(self):
        # Page numbers in the footer
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 5, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def page_body(self, datestart, dateend, plot, opnum, opname, cycles_logged, averages):
        datetext = "Evaluation Period:"
        dateval = "{} to {}".format(str(datestart), str(dateend))
        leadcyclestext = "Lead Cycles:"
        leadcyclesval = str(cycles_logged[0])
        assistcyclestext = "Assistant Cycles:"
        assistcyclesval = str(cycles_logged[1])
        opcyclestext = "Operator Cycles:"
        opcyclesval = str(cycles_logged[2])
        teamcyclestext = "Team Cycles:"
        teamcyclesval = str(cycles_logged[3])
        nametext = "Operator Name:"
        numtext = "Operator Number:"
        leadavg = averages[0]
        assistavg = averages[1]
        opavg = averages[2]
        teamavg = averages[3]
        leadavgtext = "Lead Average:"
        assistavgtext = "Assistant Average:"
        if np.isnan(leadavg):
            leadavgval = "N/A"
        else:
            leadavgval =   "{} min".format(leadavg)
        if np.isnan(assistavg):
            assistavgval = "N/A"
        else:
            assistavgval = "{} min".format(assistavg)
        opavgtext =   "All Operator Average:"
        opavgval = "{} min".format(opavg)
        teamavgtext = "Team Average:"
        teamavgval = "{} min".format(teamavg)
        
        # Get the maximum text width and calculate the cell size accordingly
        texts = [datetext, leadcyclestext, assistcyclestext, opcyclestext,
                 teamcyclestext, nametext, numtext, leadavgtext, assistavgtext,
                 opavgtext, teamavgtext]
        maxtxtwidth = 0
        for txt in texts:
            if self.get_string_width(txt) > maxtxtwidth:
                maxtxtwidth = self.get_string_width(txt)
        cellwidth = round(maxtxtwidth/5)*5
        if cellwidth < maxtxtwidth:
            cellwidth += 5
        
        self.set_margins(25, 25, 25)

        self.image(plot, 15, 25, self.WIDTH - 30)
        self.cell(0,self.HEIGHT-175, "", 0, 1, 'L')
        self.set_font('Arial', 'B', 12)
        self.cell(40, 6, "Stats:", 0, 1, 'L')
        self.set_font('Arial', '', 11)
        self.cell(cellwidth, 6, nametext, 0, 0, 'L')
        self.cell(self.get_string_width(opname), 6, opname, 0, 1, 'L')
        self.cell(cellwidth, 6, numtext, 0, 0, 'L')
        self.cell(self.get_string_width(str(opnum)), 6, str(opnum), 0, 1, 'L')
        self.cell(cellwidth, 6, datetext, 0, 0, 'L')
        self.cell(self.get_string_width(dateval), 6, dateval, 0, 1, 'L')
        self.cell(40, 3, "", 0, 1, 'L')
        self.cell(cellwidth, 6, leadcyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(leadcyclesval), 6, leadcyclesval, 0, 1, 'L')
        self.cell(cellwidth, 6, assistcyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(assistcyclesval), 6, assistcyclesval, 0, 1, 'L')
        self.cell(cellwidth, 6, opcyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(opcyclesval), 6, opcyclesval, 0, 1, 'L')
        self.cell(cellwidth, 6, teamcyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(teamcyclesval), 6, teamcyclesval, 0, 1, 'L')
        self.cell(40, 3, "", 0, 1, 'L')
        self.cell(cellwidth, 6, leadavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(leadavgval), 6, leadavgval, 0, 1, 'L')
        self.cell(cellwidth, 6, assistavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(assistavgval), 6, assistavgval, 0, 1, 'L')
        self.cell(cellwidth, 6, opavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(opavgval), 6, opavgval, 0, 1, 'L')
        self.cell(cellwidth, 6, teamavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(teamavgval), 6, teamavgval, 0, 1, 'L')


    def print_page(self, datestart, dateend, plot, opnum, opname, cycles_logged, averages):
        # Generates the report
        self.add_page()
        self.page_body(datestart, dateend, plot, opnum, opname, cycles_logged, averages)

def generate_operator_PDF(datestart, dateend, plot, opnum, opname, cycles_logged, averages, filename, exportpath):
    pdf = OperatorStatsPDF()
    pdf.print_page(datestart, dateend, plot, opnum, opname, cycles_logged, averages)
    exportfilepath = exportpath + '/' + filename
    # Check if the exported PDF file already exists in the export folder
    if os.path.exists(exportfilepath):
        # Change exportfilepath by appending a number to the end of the PDF file name
        filename = os.path.splitext(filename)[0]
        i = 1
        while os.path.exists(exportpath + '/' + filename + "({}).pdf".format(i)):
            i += 1
        exportfilepath = exportpath + '/' + filename + "({}).pdf".format(i)
    pdf.output(exportfilepath, 'F')

def get_closest_operator(cycle_idx, operator_inds):
    """
    Take an index of the cycle time and an array of indices for a given
    operator. Determine the index of the closest previous operator value to the
    chosen cycle index. If there is no previous operator value to the chosen
    cycle index, copy the closest operator value.

    Parameters
    ----------
    cycle_idx : integer
        DESCRIPTION.
    operator_inds : numpy array
        DESCRIPTION.

    Returns
    -------
    operator_idx : integer of the index closest and previous to the chosen
        cycle time index.

    """

    # Get array with all differences between cycle_idx and operator_inds
    diff_arr = cycle_idx - operator_inds

    posdiffs = [x for x in diff_arr if x > 0] or None
    if posdiffs is None:
        operator_idx = min(operator_inds)
    else:
        mindiff = min(posdiffs)
        # print("Cycle index: {}\tLead is {} away".format(cycle_idx, mindiff))
        operator_idx = cycle_idx - mindiff

    return operator_idx

def align_inds_times(input_inds, input_times, ref_inds, longest_inds, longest_len):
    while len(input_inds) < longest_len:
        for i in range(len(input_inds)):
            diff = ref_inds[i] - input_inds[i]
            if diff < 0:
                input_inds.insert(i, i)
                input_times.insert(i, np.nan)
                break
        if len(input_inds) < longest_len:
            input_inds.append(longest_inds[len(input_inds)])
            input_times.append(np.nan)

def align_cycles_inds_times(input_inds, input_times, ref_inds, longest_inds, longest_len, datetimes):
    while len(input_inds) < longest_len:
        for i in range(len(input_inds)):
            diff = input_inds[i] - ref_inds[i]
            if diff < 0:
                input_inds.insert(i, i)
                input_times.insert(i, np.nan)
                datetimes.insert(i, datetimes[i])
                break
        if len(input_inds) < longest_len:
            input_inds.append(longest_inds[len(input_inds)])
            input_times.append(np.nan)
            datetimes.append(datetimes[-1])


def clean_single_mold_data(single_mold_data):
    """
    Take in StrideLinx data download for a given period, and produce a dataframe
    of times and associated cycle times and operators.
    """
    # Load the data from .csv (make this general after testing is complete)
    df_raw = pd.read_csv(single_mold_data, parse_dates=["time"])

    # Drop the columns not relevant to cycle times
    df_raw = df_raw.drop(["Leak Time", "Leak Count", "Parts Count",
                        "Weekly Count", "Monthly Count", "Trash Count"], axis=1)

    # Sort by ascending time
    df_sorted = df_raw.sort_values(list(df_raw.columns), ascending=True)
    df_sorted = df_sorted.reset_index(drop=True)

    # Get rid of any rows with nan in all columns but time
    nan_indices = []
    for i in range(len(df_sorted)):
        if np.isnan(df_sorted["Layup Time"].iloc[i]):
            if np.isnan(df_sorted["Close Time"].iloc[i]):
                if np.isnan(df_sorted["Resin Time"].iloc[i]):
                    if np.isnan(df_sorted["Cycle Time"].iloc[i]):
                        if np.isnan(df_sorted["Lead"].iloc[i]):
                            if np.isnan(df_sorted["Assistant 1"].iloc[i]):
                                if np.isnan(df_sorted["Assistant 2"].iloc[i]):
                                    if np.isnan(df_sorted["Assistant 3"].iloc[i]):
                                        nan_indices.append(i)

    df_cleaned = df_sorted.drop(df_sorted.index[nan_indices])
    df_cleaned = df_cleaned.reset_index(drop=True)

    ### Collapse the rows together so corresponding cycle times are on the same row
    # Find the indices where there is a cycle time.
    cycle_inds = []
    not_nan_series = df_cleaned["Cycle Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            cycle_inds.append(i)

    # Find the indices where there is a resin time
    resin_inds = []
    not_nan_series = df_cleaned["Resin Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            resin_inds.append(i)

    # Find the indices where there is a close time
    close_inds = []
    not_nan_series = df_cleaned["Close Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            close_inds.append(i)

    # Find the indices where there is a layup time
    layup_inds = []
    not_nan_series = df_cleaned["Layup Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            layup_inds.append(i)

    # Find the indices where there is a lead number
    lead_inds = []
    not_nan_series = df_cleaned["Lead"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            lead_inds.append(i)
    lead_inds = np.array(lead_inds)

    # Find the indices where there is an assistant 1 number
    assistant1_inds = []
    not_nan_series = df_cleaned["Assistant 1"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            assistant1_inds.append(i)
    assistant1_inds = np.array(assistant1_inds)

    # Find the indices where there is an assistant 2 number
    assistant2_inds = []
    not_nan_series = df_cleaned["Assistant 2"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            assistant2_inds.append(i)
    assistant2_inds = np.array(assistant2_inds)

    # Find the indices where there is an assistant 3 number
    assistant3_inds = []
    not_nan_series = df_cleaned["Assistant 3"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            assistant3_inds.append(i)
    assistant3_inds = np.array(assistant3_inds)

    # Grab each datetime that corresponds to a logged cycle time
    cycle_datetimes = []
    for i, cycle_ind in enumerate(cycle_inds):
        cycle_datetimes.append(df_cleaned["time"].iloc[cycle_ind])
        
    # Grab each datetime that corresponds to a logged resin time
    resin_datetimes = []
    for i, resin_ind in enumerate(resin_inds):
        resin_datetimes.append(df_cleaned["time"].iloc[resin_ind])
        
    # Grab each datetime that corresponds to a logged close time
    close_datetimes = []
    for i, close_ind in enumerate(close_inds):
        close_datetimes.append(df_cleaned["time"].iloc[close_ind])
        
    # Grab each datetime that corresponds to a logged layup time
    layup_datetimes = []
    for i, layup_ind in enumerate(layup_inds):
        layup_datetimes.append(df_cleaned["time"].iloc[layup_ind])

    # Grab each cycle time
    cycle_times = []
    for i, cycle_ind in enumerate(cycle_inds):
        cycle_times.append(df_cleaned["Cycle Time"].iloc[cycle_ind])


    # Grab each resin time
    resin_times = []
    for i, resin_ind in enumerate(resin_inds):
        resin_times.append(df_cleaned["Resin Time"].iloc[resin_ind])

    # Grab each close time
    close_times = []
    for i, close_ind in enumerate(close_inds):
        close_times.append(df_cleaned["Close Time"].iloc[close_ind])

    # Grab each layup time
    layup_times = []
    for i, layup_ind in enumerate(layup_inds):
        layup_times.append(df_cleaned["Layup Time"].iloc[layup_ind])

    df_layup = align_operator_times(df_cleaned, layup_datetimes, "Layup Time",
                                    layup_inds, layup_times, lead_inds,
                                    assistant1_inds, assistant2_inds,
                                    assistant3_inds)
    df_close = align_operator_times(df_cleaned, close_datetimes, "Close Time",
                                    close_inds, close_times, lead_inds,
                                    assistant1_inds, assistant2_inds,
                                    assistant3_inds)
    df_resin = align_operator_times(df_cleaned, resin_datetimes, "Resin Time",
                                    resin_inds, resin_times, lead_inds,
                                    assistant1_inds, assistant2_inds,
                                    assistant3_inds)
    df_cycle = align_operator_times(df_cleaned, cycle_datetimes, "Cycle Time",
                                    cycle_inds, cycle_times, lead_inds,
                                    assistant1_inds, assistant2_inds,
                                    assistant3_inds)

    return df_layup, df_close, df_resin, df_cycle


def align_operator_times(df_cleaned, datetimes, timestring, time_inds, measured_times, lead_inds, assistant1_inds, assistant2_inds, assistant3_inds):
    # For each cycle time, determine the lead and assistant numbers
    leads = []
    assistant1s = []
    assistant2s = []
    assistant3s = []
    for i, ind in enumerate(time_inds):
        # Determine the closest previous index in the Lead column that contains a
        # lead number
        lead_idx = get_closest_operator(ind, lead_inds)
        leads.append(df_cleaned["Lead"].iloc[lead_idx])
        assistant1_idx = get_closest_operator(ind, assistant1_inds)
        assistant1s.append(df_cleaned["Assistant 1"].iloc[assistant1_idx])
        assistant2_idx = get_closest_operator(ind, assistant2_inds)
        assistant2s.append(df_cleaned["Assistant 2"].iloc[assistant2_idx])
        assistant3_idx = get_closest_operator(ind, assistant3_inds)
        assistant3s.append(df_cleaned["Assistant 3"].iloc[assistant3_idx])

    leads = [int(x) for x in leads]
    assistant1s = [int(x) for x in assistant1s]
    assistant2s = [int(x) for x in assistant2s]
    assistant3s = [int(x) for x in assistant3s]

    # Check if datetimes is longer than the rest of the data. If so, add NaN to
    # the end of all other vectors
    while len(datetimes) > len(measured_times):
        randint = np.random.randint(1,len(datetimes)-2)
        del datetimes[randint]
    while len(datetimes) < len(measured_times):
        datetimes.insert(-1, datetimes[-1])


    # Combine data
    aligned_data = {"time": datetimes, timestring: measured_times,
                    "Lead": leads, "Assistant 1": assistant1s,
                    "Assistant 2": assistant2s, "Assistant 3": assistant3s}
    df_aligned = pd.DataFrame.from_dict(aligned_data)

    return df_aligned


def get_operator_stats(df, timestring):
    startdate = df["time"].iloc[0].date()
    enddate = df["time"].iloc[-1].date()

    ### Get statistics on each operator in the data ###
    # Get lists of unique operator numbers for each category
    unique_leads = [int(x) for x in df["Lead"].unique()]
    if 0 in unique_leads:
        unique_leads.remove(0)
    unique_assistant1 = [int(x) for x in df["Assistant 1"].unique()]
    unique_assistant2 = [int(x) for x in df["Assistant 2"].unique()]
    unique_assistant3 = [int(x) for x in df["Assistant 3"].unique()]
    unique_assistants = unique_assistant1 + unique_assistant2 + unique_assistant3
    unique_assistants = list(np.unique(unique_assistants))
    if 0 in unique_assistants:
        unique_assistants.remove(0)


    operator_strings = []
    for operator in unique_leads:
        operator_strings.append("Lead {}".format(operator))
    for operator in unique_assistants:
        operator_strings.append("Assistant {}".format(operator))

    all_times = pd.DataFrame()

    # Go through each unique operator number and gather their data
    unique_operators = unique_leads + unique_assistants
    unique_operators = list(np.unique(unique_operators))

    directory = os.getcwd()

    for operator in unique_operators:
        df_operator = df.loc[(df["Lead"] == operator) |
                            (df["Assistant 1"] == operator) |
                            (df["Assistant 2"] == operator) |
                            (df["Assistant 3"] == operator)]

        df_lead = df.loc[df["Lead"] == operator]
        df_assistant = df.loc[(df["Assistant 1"] == operator) |
                                (df["Assistant 2"] == operator) |
                                (df["Assistant 3"] == operator)]

        # Append the cycle time data as a column to all_times
        lead_col = "Lead {}".format(operator)
        assistant_col = "Assistant {}".format(operator)
        operator_col = "All Operator {}".format(operator)
        all_times = pd.concat([all_times, df_lead[timestring].rename(lead_col)], axis=1)
        all_times = pd.concat([all_times, df_assistant[timestring].rename(assistant_col)], axis=1)

        # Compare the current operator against all cycle times
        lead_col = "Lead"
        assistant_col = "Assistant"
        operator_col = "All Operator {}".format(operator)
        operator_compare = pd.DataFrame()
        operator_compare = pd.concat([operator_compare, df_lead[timestring].rename(lead_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_assistant[timestring].rename(assistant_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_operator[timestring].rename(operator_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df[timestring].rename("Team")], axis=1)

        sns.set_theme(style="whitegrid")
        customPalette = sns.light_palette("lightblue", 4)
        flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
        sns.boxplot(x="variable", y="value", data=pd.melt(operator_compare), flierprops=flierprops, palette=customPalette)
        plt.title("Operator {} {}s: {} to {}".format(operator, timestring, startdate, enddate))
        plt.ylabel("{} (minutes)".format(timestring))
        plt.xlabel("")
        plotname = directory + "\\Operator_{}_{}.png".format(operator, timestring.replace(" ","_"))
        plt.savefig(plotname, dpi=300)
        plt.close()
        if timestring == "Cycle Time":
            cycles_logged = []
            cycles_logged.append(operator_compare[lead_col].count())
            cycles_logged.append(operator_compare[assistant_col].count())
            cycles_logged.append(operator_compare[operator_col].count())
            cycles_logged.append(operator_compare["Team"].count())
            # opcycles = operator_compare[operator_col].count()
            # allcycles = operator_compare["Team"].count()
            leadavg = np.around(operator_compare[lead_col].mean(),1)
            assistavg = np.around(operator_compare[assistant_col].mean(),1)
            opavg = np.around(operator_compare[operator_col].mean(),1)
            teamavg = np.around(operator_compare["Team"].mean(),1)
            averages = [leadavg, assistavg, opavg, teamavg]
            filename = "Operator_{}_{}_Stats_{}_to_{}.pdf".format(operator, timestring.replace(" ","_"), startdate, enddate)
            exportpath = os.getcwd()
            opname = lookup_operator_name(operator, "ID_data.xlsx")
            generate_operator_PDF(startdate, enddate, plotname, operator, opname, cycles_logged, averages, filename, exportpath)


def lookup_operator_name(opnum, IDfilepath):
    df = pd.read_excel(IDfilepath, None)
    df_lead = df["Personnel-Lead"]
    len_opnum = len(str(opnum))
    if len_opnum < 3:
        opnum_str = str(opnum).zfill(3)
    else:
        opnum_str = str(opnum)

    leadnum = "10" + opnum_str
    leadnum = int(leadnum)
    namerow = df_lead.loc[df_lead["ID"] == leadnum]
    opname = namerow.iloc[0][3]
    return opname

def analyze_single_mold(single_mold_data):
    df_layup, df_close, df_resin, df_cycle = clean_single_mold_data(single_mold_data)
    get_operator_stats(df_layup)
    get_operator_stats(df_close)
    get_operator_stats(df_resin)
    get_operator_stats(df_cycle)


def analyze_all_molds(mold_data_folder):
    """
    Take a list of CSV files containing mold data downloaded from StrideLinx.
    Combine the data into one large dataframe of cycle times and their
    associated operators, and get individual operator stats. Print a nice report
    for each individual operator number that includes their lead, assistant,
    and overall stats compared to all cycle times for the same period.
    """
    mold_data_files = []
    for root, dirs, files in os.walk(os.path.abspath(mold_data_folder)):
        for file in files:
            mold_data_files.append(os.path.join(root, file))

    layup_frames = []
    close_frames = []
    resin_frames = []
    cycle_frames = []
    for datafile in mold_data_files:
        df_layup, df_close, df_resin, df_cycle = clean_single_mold_data(datafile)
        layup_frames.append(df_layup)
        close_frames.append(df_close)
        resin_frames.append(df_resin)
        cycle_frames.append(df_cycle)

    all_layup = pd.concat(layup_frames)
    all_layup = all_layup.reset_index(drop=True)
    all_close = pd.concat(close_frames)
    all_close = all_close.reset_index(drop=True)
    all_resin = pd.concat(resin_frames)
    all_resin = all_resin.reset_index(drop=True)
    all_cycle = pd.concat(cycle_frames)
    all_cycle = all_cycle.reset_index(drop=True)
    
    
    # It might be necessary at this point to remove faulty duplicates. These
    # can be identified by finding consecutive rows where all columns are equal
    # except for time.
    # # Reorder each DataFrame by the datetime value in time column, then reindex
    # all_layup = all_layup.sort_values(by="time")
    # all_layup = all_layup.reset_index(drop=True)
    # all_close = all_close.sort_values(by="time")
    # all_close = all_close.reset_index(drop=True)
    # all_resin = all_resin.sort_values(by="time")
    # all_resin = all_resin.reset_index(drop=True)
    # all_cycle = all_cycle.sort_values(by="time")
    # all_cycle = all_cycle.reset_index(drop=True)
    
    # Remove faulty duplicates
    all_layup = clean_duplicate_times(all_layup)
    all_close = clean_duplicate_times(all_close)
    all_resin = clean_duplicate_times(all_resin)
    all_cycle = clean_duplicate_times(all_cycle)
    
    # dupinds_layup = []
    # dupinds_close = []
    # dupinds_resin = []
    # dupinds_cycle = []
    # for i in range(len(all_layup)):
    #     if i == 0:
    #         continue
    #     else:
    #         prev = all_layup.iloc[i-1,1:6]
    #         curr = all_layup.iloc[i,1:6]
    #         if prev.equals(curr):
    #             dupinds_layup.append(i)
                
    # all_layup = all_layup.drop(dupinds_layup)
    # all_layup = all_layup.reset_index(drop=True)
    
    
    numops_layup = compare_num_ops(all_layup, "Layup Time")
    numops_close = compare_num_ops(all_close, "Close Time")
    numops_resin = compare_num_ops(all_resin, "Resin Time")
    numops_cycle = compare_num_ops(all_cycle, "Cycle Time")
    
    # Calculate the regression parameters of each data category, then calculate
    # the adjusted values of cycle times, layup times, etc. to adjust for 
    # the number of people working on the mold.
    
    # # Add a column to each time type DataFrame to scale the data by the number
    # # of operators (not sure if this method is sound yet or not)
    # all_layup = adjust_data_by_num_operators(all_layup, numops_layup, "Layup Time", "Adjusted Layup Time")
    # all_close = adjust_data_by_num_operators(all_close, numops_close, "Close Time", "Adjusted Close Time")
    # all_resin = adjust_data_by_num_operators(all_resin, numops_resin, "Resin Time", "Adjusted Resin Time")
    # all_cycle = adjust_data_by_num_operators(all_cycle, numops_cycle, "Cycle Time", "Adjusted Cycle Time")

    get_operator_stats(all_layup, "Layup Time")
    get_operator_stats(all_close, "Close Time")
    get_operator_stats(all_resin, "Resin Time")
    get_operator_stats(all_cycle, "Cycle Time")
    
    return all_layup, all_close, all_resin, all_cycle

def clean_duplicate_times(df):
    dupinds = []
    # First pass to remove obvious duplicates
    for i in range(len(df)):
        if i == 0:
            continue
        else:
            prev = df.iloc[i-1,1:6]
            curr = df.iloc[i,1:6]
            if curr.equals(prev):
                dupinds.append(i)
                continue
            
            # Remove duplicates where the consecutive stage times are the same
            # and the time column doesn't show a realistic time difference.
            # This assumes that the consecutive times are on the same mold.
            # It is theoretically possible that the times came from different
            # molds, so this section may need to be removed.
            prevtime = df["time"][i-1]
            currtime = df["time"][i]
            difftime = currtime - prevtime
            difftime = difftime.total_seconds()
            
            prevstagetime = prev.iloc[0]
            currstagetime = curr.iloc[0]
            stagetimesec = 60*curr.iloc[0]
            
            if prevstagetime == currstagetime and stagetimesec > difftime:
                dupinds.append(i)
                continue
            
                
                
    df = df.drop(dupinds)
    df = df.reset_index(drop=True)
    
    return df

def adjust_data_by_num_operators(df, numops_df, input_col:str, output_col:str):
    df_normalized = df
    # Get rid of rows where there no operators clocked in to avoid throwing off
    # the linear regression model
    numops_df = numops_df[numops_df["N Operators"] != 0]
    x = np.array(numops_df["N Operators"]).reshape((-1, 1))
    y = np.array(numops_df[input_col])
    model = LinearRegression()
    model.fit(x, y)
    r_sq = model.score(x, y)
    print("R squared: {}".format(r_sq))
    b = model.intercept_
    a = float(model.coef_)
    
    singleop_df = numops_df[numops_df["N Operators"] == 1]
    single_median = singleop_df[input_col].median()
    
    normalized_list = []
    opcount = 0
    for i in range(len(df_normalized)):
        oplist = df.iloc[i,2:6]
        opcount = oplist.astype(bool).sum()
        if opcount == 0:
            normalized_list.append(np.NaN)
        else:
            # Adjust each cycle time by the amount in the linear regression to
            # make measurements level with the median of the single-operator
            # measurements
            t_meas = df[input_col].iloc[i]
            t_adjust = t_meas - a*opcount + a # NOTE: THIS IS A LINEAR SHIFT, AND DOES NOT ADJUST THE VARIANCE OF THE DATA. MORE METHODS MIGHT BE NEEDED TO TAKE VARIANCE INTO ACCOUNT.
            
            normalized_list.append(t_adjust)
            
            # normalized_list.append(df[input_col].iloc[i]*opcount)
    df_normalized[output_col] = normalized_list
    
    return df_normalized

def compare_num_ops(df, timestring:str):
    """
    Output a dataframe that has three columns: time, measured time of interest
    (Layup Time, Close Time, Resin Time, or Cycle Time), and the number of
    operators on the mold for that measured time. Output box plots for the
    data.

    Parameters
    ----------
    df : Pandas DataFrame
        DESCRIPTION.
        
    

    Returns
    -------
    df_num_ops: Pandas DataFrame
        3 columns: time, measured time of interest, and number of operators

    """
    df_num_ops = df
    opcounts = []
    opcount = 0
    for i in range(len(df_num_ops)):
        oplist = df_num_ops.iloc[i,2:6]
        opcount = oplist.astype(bool).sum()
        opcounts.append(opcount)
        
    # Add the list of opcounts as a column to df_num_ops
    df_num_ops["N Operators"] = opcounts
    
    # Drop unnecessary columns
    df_num_ops = df_num_ops.drop(columns=["Lead", "Assistant 1", "Assistant 2", "Assistant 3"])
    
    # # SORT BY NUM OPS HERE
    # df_num_ops = df_num_ops.sort_values("N Operators")
    # df_num_ops = df_num_ops.reset_index(drop=True)
    
    directory = os.getcwd()
    sns.set_theme(style="whitegrid")
    customPalette = sns.light_palette("lightblue", 5)
    flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
    ax = sns.boxplot(x="N Operators", y=timestring, data=df_num_ops, flierprops=flierprops, palette=customPalette)
    plt.title("Comparison of Operators on Mold: {}".format(timestring))
    
    # Annotate each boxplot with the number of samples
    # Calculate number of obs per group & median to position labels
    medians = df_num_ops.groupby(["N Operators"])[timestring].median().values
    counts = df_num_ops["N Operators"].value_counts()
    nobs = []
    for i in range(5):
        try:
            nobs.append(counts[i])
        except KeyError:
            continue
    nobs = [str(x) for x in nobs]
    nobs = ["n: " + i for i in nobs]
     
    # Add it to the plot
    pos = range(len(nobs))
    for tick,label in zip(pos,ax.get_xticklabels()):
        ax.text(pos[tick],
                medians[tick] + 0.03,
                nobs[tick],
                horizontalalignment='center',
                size='x-small',
                color='k',
                weight='semibold')
    
    
    # plt.ylabel("{} (minutes)".format(timestring))
    # plt.xlabel("")
    plotname = directory + "\\Operator_Number_Comparison_{}.png".format(timestring.replace(" ","_"))
    plt.savefig(plotname, dpi=300)
    plt.close()
    
    
    return df_num_ops
    

if __name__ == "__main__":
    datafolder = os.getcwd()
    datafolder = datafolder + "\\testdata"
    all_layup, all_close, all_resin, all_cycle = analyze_all_molds(datafolder)
