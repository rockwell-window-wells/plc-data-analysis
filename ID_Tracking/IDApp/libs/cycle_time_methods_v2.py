"""cycle_time_methods.py: Combining old employee_cycle_times.py and
data_request.py into a single module to avoid both modules calling each other.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cbook import boxplot_stats
import os
import requests
from fpdf import FPDF
from PyPDF2 import PdfFileMerger, PdfFileReader
import seaborn as sns
import datetime as dt
import shutil

import data_assets
import id_methods
import api_config_vars as api
# from . import data_assets
# from . import id_methods
# from . import api_config_vars as api

##### PDF Methods #####
class OperatorStatsPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297

    def header(self):
        # Custom logo and positioning
        self.image(data_assets.fulllogo, 10, 8, 33)
        self.set_font('Arial', 'B', 11)
        self.cell(self.WIDTH - 80)
        self.cell(60, 1, 'Mold Operator Stats', 0, 0, 'R')
        self.ln(20)

    def footer(self):
        pass
        # # Page numbers in the footer
        # self.set_y(-15)
        # self.set_font('Arial', 'I', 8)
        # self.set_text_color(128)
        # self.cell(0, 5, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def page_body(self, datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift):
        datetext = "Evaluation Period:"
        dateval = "{} to {}".format(str(datestart), str(dateend))
        
        leadcyclestext = "Lead Cycles:"
        leadcyclesval = get_cycles_text(cycles_logged[0])
        shiftcyclestext = "Shift Cycles:"
        shiftcyclesval = get_cycles_text(cycles_logged[1])
        companycyclestext = "RockWell Cycles:"
        companycyclesval = get_cycles_text(cycles_logged[2])
        nametext = "Operator Name:"
        numtext = "Operator Number:"
        shifttext = "Shift:"
        
        leadmed = medians[0]
        shiftmed = medians[1]
        companymed = medians[2]
        leadmedtext = "Lead Median:"
        shiftmedtext = "Shift Median:"
        companymedtext = "RockWell Median:"
        if np.isnan(leadmed):
            leadmedval = "N/A"
        else:
            leadmedval =   "{} min".format(leadmed)
        if np.isnan(shiftmed):
            shiftmedval = "N/A"
        else:
            shiftmedval = "{} min".format(shiftmed)
        # if np.isnan(companymed):
        #     companymedval = "N/A"
        # else:
        #     companymedval = "{} min".format(companymed)
        companymedval = "{} min".format(companymed)
        
        leadavg = averages[0]
        shiftavg = averages[1]
        companyavg = averages[2]
        leadavgtext = "Lead Average:"
        shiftavgtext = "Shift Average:"
        companyavgtext = "RockWell Average:"
        if np.isnan(leadavg):
            leadavgval = "N/A"
        else:
            leadavgval =   "{} min".format(leadavg)
        if np.isnan(shiftavg):
            shiftavgval = "N/A"
        else:
            shiftavgval = "{} min".format(shiftavg)
        # if np.isnan(opavg):
        #     opavgval = "N/A"
        # else:
        #     opavgval = "{} min".format(opavg)
        companyavgval = "{} min".format(companyavg)

        # Get the maximum text width and calculate the cell size accordingly
        texts = [datetext, leadcyclestext, shiftcyclestext, companycyclestext,
                 nametext, numtext, leadmedtext, shiftmedtext, companymedtext,
                 leadavgtext, shiftavgtext, companyavgtext]
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
        self.cell(cellwidth, 6, shifttext, 0, 0, 'L')
        self.cell(self.get_string_width(str(shift)), 6, str(shift), 0, 1, 'L')
        self.cell(cellwidth, 6, datetext, 0, 0, 'L')
        self.cell(self.get_string_width(dateval), 6, dateval, 0, 1, 'L')
        self.cell(40, 3, "", 0, 1, 'L')
        self.cell(cellwidth, 6, leadcyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(leadcyclesval), 6, leadcyclesval, 0, 1, 'L')
        self.cell(cellwidth, 6, shiftcyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(shiftcyclesval), 6, shiftcyclesval, 0, 1, 'L')
        self.cell(cellwidth, 6, companycyclestext, 0, 0, 'L')
        self.cell(self.get_string_width(companycyclesval), 6, companycyclesval, 0, 1, 'L')
        self.cell(40, 3, "", 0, 1, 'L')
        self.cell(cellwidth, 6, leadmedtext, 0, 0, 'L')
        self.cell(self.get_string_width(leadmedval), 6, leadmedval, 0, 1, 'L')
        self.cell(cellwidth, 6, shiftmedtext, 0, 0, 'L')
        self.cell(self.get_string_width(shiftmedval), 6, shiftmedval, 0, 1, 'L')
        self.cell(cellwidth, 6, companymedtext, 0, 0, 'L')
        self.cell(self.get_string_width(companymedval), 6, companymedval, 0, 1, 'L')
        self.cell(40, 3, "", 0, 1, 'L')
        self.cell(cellwidth, 6, leadavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(leadavgval), 6, leadavgval, 0, 1, 'L')
        self.cell(cellwidth, 6, shiftavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(shiftavgval), 6, shiftavgval, 0, 1, 'L')
        self.cell(cellwidth, 6, companyavgtext, 0, 0, 'L')
        self.cell(self.get_string_width(companyavgval), 6, companyavgval, 0, 1, 'L')


    def print_page(self, datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift):
        # Generates the report
        self.add_page()
        self.page_body(datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift)
        
def get_cycles_text(cycle_count):
    thresh = 100
    
    if cycle_count < thresh:
        cycles_text = "{}     Choose longer evaluation period".format(cycle_count)
    elif cycle_count >= thresh:
        cycles_text = "{}     OK for evaluation".format(cycle_count)
        
    return cycles_text
            

def generate_operator_PDF(datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift, filename, exportpath):
    pdf = OperatorStatsPDF()
    pdf.print_page(datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift)
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

def merge_operator_PDFs(exportfolder, mergedfilepath):
    """
    Take all PDF files in the output folder and merge them together.
    """
    x = [a for a in os.listdir(exportfolder) if a.endswith(".pdf")]
    # print(x)
    x = [exportfolder + "\\" + a for a in x]    # List of strings at this point

    merger = PdfFileMerger()

    for pdf in x:
        with open(pdf, 'rb') as source:
            tmp = PdfFileReader(source)
            merger.append(tmp)

    with open(mergedfilepath, "wb") as fout:
        merger.write(fout)

    # for pdf in x:
    #     pdf.close()

    # mergedfilepath.close()

    # # Automatically open the merged file
    # os.system(mergedfilepath)


##### Index Alignment Methods #####
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


def get_all_operator_stats(df, timestring):
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

    directory = data_assets.pdftempfolder

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
        operator_compare = pd.concat([operator_compare, df[timestring].rename("RockWell")], axis=1)

        sns.set_theme(style="whitegrid")
        customPalette = sns.light_palette("lightblue", 4)
        flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
        sns.boxplot(x="variable", y="value", data=pd.melt(operator_compare), flierprops=flierprops, palette=customPalette)
        plt.title("Operator {} {}s: {} to {}".format(operator, timestring, startdate, enddate))
        plt.ylabel("{} (minutes)".format(timestring))
        plt.xlabel("")
        plotname = directory + "\\Operator_{}_{}.png".format(operator, timestring.replace(" ","_"))
        plt.savefig(plotname, dpi=200)
        plt.close()
        if timestring == "Cycle Time":
            cycles_logged = []
            cycles_logged.append(operator_compare[lead_col].count())
            cycles_logged.append(operator_compare[assistant_col].count())
            cycles_logged.append(operator_compare[operator_col].count())
            cycles_logged.append(operator_compare["RockWell"].count())
            # opcycles = operator_compare[operator_col].count()
            # allcycles = operator_compare["RockWell"].count()
            leadmed = np.around(operator_compare[lead_col].median(),1)
            assistmed = np.around(operator_compare[assistant_col].median(),1)
            opmed = np.around(operator_compare[operator_col].mean(),1)
            teammed = np.around(operator_compare["RockWell"].median(),1)
            medians = [leadmed, assistmed, opmed, teammed]
            leadavg = np.around(operator_compare[lead_col].mean(),1)
            assistavg = np.around(operator_compare[assistant_col].mean(),1)
            opavg = np.around(operator_compare[operator_col].mean(),1)
            teamavg = np.around(operator_compare["RockWell"].mean(),1)
            averages = [leadavg, assistavg, opavg, teamavg]
            filename = "Operator_{}_{}_Stats_{}_to_{}.pdf".format(operator, timestring.replace(" ","_"), startdate, enddate)
            exportpath = data_assets.pdftempfolder
            opname = lookup_operator_name(operator, data_assets.ID_data)
            generate_operator_PDF(startdate, enddate, plotname, operator, opname, cycles_logged, medians, averages, shift, filename, exportpath)

    mergefile = "All_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    mergedfilepath = data_assets.pdftempfolder + "\\" + mergefile
    merge_operator_PDFs(exportpath, mergedfilepath)
    
    # Copy merged file into Operator_Reports folder
    dest = data_assets.pdfexportfolder + "\\" + mergefile
    shutil.copyfile(mergedfilepath, dest)

    # Delete all files from temp data holding folder
    files_in_directory = os.listdir(directory)
    for file in files_in_directory:
        path_to_file = os.path.join(directory, file)
        os.remove(path_to_file)
        
    # Automatically open the merged file from its new location
    # mergedfilepath = data_assets.pdfexportfolder + "\\" + mergefile
    os.system(dest)


def get_operator_stats_by_list(df, operator_list, shift=None):
    """

    Parameters
    ----------
    df : Pandas DataFrame
        DESCRIPTION.
    operator_list : list of ints
        DESCRIPTION.
    timestring : str
        DESCRIPTION.
    shift : str
        By default shift is None, but if a shift string is specified ("day",
        "swing", "graveyard") then the merged file will be named accordingly
        for convenience.


    Returns
    -------
    None.

    """

    startdate = df["time"].iloc[0].date()
    enddate = df["time"].iloc[-1].date()
    
    timestring = "Cycle Time"

    all_times = pd.DataFrame()

    directory = data_assets.pdftempfolder
    
    # Get list of operator numbers on each shift by checking Excel data
    IDfilepath = data_assets.ID_data
    daylist, swinglist, gravelist = id_methods.get_shift_lists(IDfilepath)

    for operator in operator_list:
        # df_operator = df.loc[(df["Lead"] == operator) |
        #                     (df["Assistant 1"] == operator) |
        #                     (df["Assistant 2"] == operator) |
        #                     (df["Assistant 3"] == operator)]
        
        # Get all rows where the current operator is in the lead list
        df_lead = df[pd.DataFrame(df.Lead.tolist()).isin([operator]).any(1).values]
        
        # Get all rows for the current operator's shift
        operator_shift = None
        if operator in daylist:
            operator_shift = "Day"
        elif operator in swinglist:
            operator_shift = "Swing"
        else:
            operator_shift = "Graveyard"
            
        df_shift = df[pd.DataFrame(df.Shift.tolist()).isin([operator_shift]).any(1).values]
        
        # Remove rows where it's the first part on a Monday
        df_lead = df_lead[df_lead["First Monday Part"] != 1]
        df_shift = df_shift[df_shift["First Monday Part"] != 1]
        df_company = df[df["First Monday Part"] != 1]

        # # Append the cycle time data as a column to all_times
        # lead_col = "Lead {}".format(operator)
        # # assistant_col = "Assistant {}".format(operator)
        # # operator_col = "All Operator {}".format(operator)
        # all_times = pd.concat([all_times, df_lead[timestring].rename(lead_col)], axis=1)
        # # all_times = pd.concat([all_times, df_assistant[timestring].rename(assistant_col)], axis=1)

        # Compare the current operator against all cycle times
        lead_col = "Lead"
        shift_col = "Shift"
        company_col = "RockWell"
        # assistant_col = "Assistant"
        # operator_col = "All Operator {}".format(operator)
        operator_compare = pd.DataFrame()
        operator_compare = pd.concat([operator_compare, df_lead[timestring].rename(lead_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_shift[timestring].rename("Shift")], axis=1)
        # operator_compare = pd.concat([operator_compare, df_assistant[timestring].rename(assistant_col)], axis=1)
        # operator_compare = pd.concat([operator_compare, df_operator[timestring].rename(operator_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_company[timestring].rename("RockWell")], axis=1)

        sns.set_theme(style="whitegrid")
        customPalette = sns.light_palette("lightblue", 3)
        flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
        sns.boxplot(x="variable", y="value", data=pd.melt(operator_compare), flierprops=flierprops, palette=customPalette)
        plt.title("Operator {} {}s: {} to {}".format(operator, timestring, startdate, enddate))
        plt.ylabel("{} (minutes)".format(timestring))
        plt.xlabel("")
        plotname = directory + "\\Operator_{}_{}.png".format(operator, timestring.replace(" ","_"))
        plt.savefig(plotname, dpi=200)
        plt.close()
        if timestring == "Cycle Time":
            cycles_logged = []
            cycles_logged.append(operator_compare[lead_col].count())
            cycles_logged.append(operator_compare[shift_col].count())
            cycles_logged.append(operator_compare[company_col].count())
            
            leadmed = np.around(operator_compare[lead_col].median(),1)
            shiftmed = np.around(operator_compare[shift_col].median(),1)
            companymed = np.around(operator_compare[company_col].median(),1)
            medians = [leadmed, shiftmed, companymed]
            
            leadavg = np.around(operator_compare[lead_col].mean(),1)
            shiftavg = np.around(operator_compare[shift_col].mean(),1)
            companyavg = np.around(operator_compare[company_col].mean(),1)
            averages = [leadavg, shiftavg, companyavg]
            filename = "Operator_{}_{}_Stats_{}_to_{}.pdf".format(operator, timestring.replace(" ","_"), startdate, enddate)
            exportpath = data_assets.pdftempfolder
            opname = lookup_operator_name(operator, data_assets.ID_data)
            generate_operator_PDF(startdate, enddate, plotname, operator, opname, cycles_logged, medians, averages, operator_shift, filename, exportpath)


    if shift is None:
        mergefile = "List_Operators_{}_to_{}.pdf".format(startdate, enddate)
        mergedfilepath = data_assets.pdftempfolder + "\\" + mergefile
        merge_operator_PDFs(exportpath, mergedfilepath)
    else:
        mergefile, mergedfilepath = merge_by_shift(startdate, enddate, shift, exportpath)
        
    # Copy merged file into Operator_Reports folder
    dest = data_assets.pdfexportfolder + "\\" + mergefile
    shutil.copyfile(mergedfilepath, dest)

    # Delete all files from temp data holding folder
    files_in_directory = os.listdir(directory)
    for file in files_in_directory:
        path_to_file = os.path.join(directory, file)
        os.remove(path_to_file)
        
    # Automatically open the merged file from its new location
    # mergedfilepath = data_assets.pdfexportfolder + "\\" + mergefile
    os.system(dest)


def merge_by_shift(startdate, enddate, shift, exportpath):
    shift = shift.lower()
    if shift == "day":
        mergefile = "Day_Shift_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    elif shift == "swing":
        mergefile = "Swing_Shift_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    elif shift == "graveyard":
        mergefile = "Graveyard_Shift_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    else:
        raise ValueError("No shift specified")

    mergedfilepath = data_assets.pdftempfolder + "\\" + mergefile
    merge_operator_PDFs(exportpath, mergedfilepath)
    
    return mergefile, mergedfilepath



def get_single_operator_stats(df, opnum, timestring):
    startdate = df["time"].iloc[0].date()
    enddate = df["time"].iloc[-1].date()

    all_times = pd.DataFrame()

    directory = data_assets.pdftempfolder

    df_operator = df.loc[(df["Lead"] == opnum) |
                        (df["Assistant 1"] == opnum) |
                        (df["Assistant 2"] == opnum) |
                        (df["Assistant 3"] == opnum)]

    df_lead = df.loc[df["Lead"] == opnum]
    df_assistant = df.loc[(df["Assistant 1"] == opnum) |
                            (df["Assistant 2"] == opnum) |
                            (df["Assistant 3"] == opnum)]

    # Append the cycle time data as a column to all_times
    lead_col = "Lead {}".format(opnum)
    assistant_col = "Assistant {}".format(opnum)
    operator_col = "All Operator {}".format(opnum)
    all_times = pd.concat([all_times, df_lead[timestring].rename(lead_col)], axis=1)
    all_times = pd.concat([all_times, df_assistant[timestring].rename(assistant_col)], axis=1)

    # Compare the current operator against all cycle times
    lead_col = "Lead"
    assistant_col = "Assistant"
    operator_col = "All Operator {}".format(opnum)
    operator_compare = pd.DataFrame()
    operator_compare = pd.concat([operator_compare, df_lead[timestring].rename(lead_col)], axis=1)
    operator_compare = pd.concat([operator_compare, df_assistant[timestring].rename(assistant_col)], axis=1)
    operator_compare = pd.concat([operator_compare, df_operator[timestring].rename(operator_col)], axis=1)
    operator_compare = pd.concat([operator_compare, df[timestring].rename("RockWell")], axis=1)

    sns.set_theme(style="whitegrid")
    customPalette = sns.light_palette("lightblue", 4)
    flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
    sns.boxplot(x="variable", y="value", data=pd.melt(operator_compare), flierprops=flierprops, palette=customPalette)
    plt.title("Operator {} {}s: {} to {}".format(opnum, timestring, startdate, enddate))
    plt.ylabel("{} (minutes)".format(timestring))
    plt.xlabel("")
    plotname = directory + "\\Operator_{}_{}.png".format(opnum, timestring.replace(" ","_"))
    plt.savefig(plotname, dpi=300)
    plt.close()
    if timestring == "Cycle Time":
        cycles_logged = []
        cycles_logged.append(operator_compare[lead_col].count())
        cycles_logged.append(operator_compare[assistant_col].count())
        cycles_logged.append(operator_compare[operator_col].count())
        cycles_logged.append(operator_compare["RockWell"].count())
        leadmed = np.around(operator_compare[lead_col].median(),1)
        assistmed = np.around(operator_compare[assistant_col].median(),1)
        opmed = np.around(operator_compare[operator_col].mean(),1)
        teammed = np.around(operator_compare["RockWell"].median(),1)
        medians = [leadmed, assistmed, opmed, teammed]
        leadavg = np.around(operator_compare[lead_col].mean(),1)
        assistavg = np.around(operator_compare[assistant_col].mean(),1)
        opavg = np.around(operator_compare[operator_col].mean(),1)
        teamavg = np.around(operator_compare["RockWell"].mean(),1)
        averages = [leadavg, assistavg, opavg, teamavg]
        filename = "Operator_{}_{}_Stats_{}_to_{}.pdf".format(opnum, timestring.replace(" ","_"), startdate, enddate)
        exportpath = data_assets.pdftempfolder
        opname = lookup_operator_name(opnum, data_assets.ID_data)
        generate_operator_PDF(startdate, enddate, plotname, opnum, opname, cycles_logged, medians, averages, shift, filename, exportpath)
        
    # Copy merged file into Operator_Reports folder
    filepath = data_assets.pdftempfolder + "\\" + filename
    dest = data_assets.pdfexportfolder + "\\" + filename
    shutil.copyfile(filepath, dest)

    # Delete all files from temp data holding folder
    files_in_directory = os.listdir(directory)
    for file in files_in_directory:
        path_to_file = os.path.join(directory, file)
        os.remove(path_to_file)
        
    # Automatically open the merged file from its new location
    # mergedfilepath = data_assets.pdfexportfolder + "\\" + mergefile
    os.system(dest)


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
    get_all_operator_stats(df_layup)
    get_all_operator_stats(df_close)
    get_all_operator_stats(df_resin)
    get_all_operator_stats(df_cycle)


def analyze_all_molds_api(dtstart, dtend):
    """Use API access methods to generate stat reports for given datetime range.
    """
    all_layup, all_close, all_resin, all_cycle = load_operator_data(dtstart, dtend)

    # Remove faulty duplicates
    # all_layup = clean_duplicate_times(all_layup)
    # all_close = clean_duplicate_times(all_close)
    # all_resin = clean_duplicate_times(all_resin)
    all_cycle = clean_duplicate_times(all_cycle)

    # compare_num_ops(all_layup, "Layup Time")
    # compare_num_ops(all_close, "Close Time")
    # compare_num_ops(all_resin, "Resin Time")
    compare_num_ops(all_cycle, "Cycle Time")

    # get_all_operator_stats(all_layup, "Layup Time")
    # get_all_operator_stats(all_close, "Close Time")
    # get_all_operator_stats(all_resin, "Resin Time")
    get_all_operator_stats(all_cycle, "Cycle Time")

    return all_layup, all_close, all_resin, all_cycle

# def analyze_all_molds(mold_data_folder):
#     """
#     Take a list of CSV files containing mold data downloaded from StrideLinx.
#     Combine the data into one large dataframe of cycle times and their
#     associated operators, and get individual operator stats. Print a nice report
#     for each individual operator number that includes their lead, assistant,
#     and overall stats compared to all cycle times for the same period.
#     """
#     mold_data_files = []
#     for root, dirs, files in os.walk(os.path.abspath(mold_data_folder)):
#         for file in files:
#             mold_data_files.append(os.path.join(root, file))

#     layup_frames = []
#     close_frames = []
#     resin_frames = []
#     cycle_frames = []
#     for datafile in mold_data_files:
#         df_layup, df_close, df_resin, df_cycle = clean_single_mold_data(datafile)
#         layup_frames.append(df_layup)
#         close_frames.append(df_close)
#         resin_frames.append(df_resin)
#         cycle_frames.append(df_cycle)

#     all_layup = pd.concat(layup_frames)
#     all_layup = all_layup.reset_index(drop=True)
#     all_close = pd.concat(close_frames)
#     all_close = all_close.reset_index(drop=True)
#     all_resin = pd.concat(resin_frames)
#     all_resin = all_resin.reset_index(drop=True)
#     all_cycle = pd.concat(cycle_frames)
#     all_cycle = all_cycle.reset_index(drop=True)

#     # Remove faulty duplicates
#     all_layup = clean_duplicate_times(all_layup)
#     all_close = clean_duplicate_times(all_close)
#     all_resin = clean_duplicate_times(all_resin)
#     all_cycle = clean_duplicate_times(all_cycle)

#     compare_num_ops(all_layup, "Layup Time")
#     compare_num_ops(all_close, "Close Time")
#     compare_num_ops(all_resin, "Resin Time")
#     compare_num_ops(all_cycle, "Cycle Time")

#     get_all_operator_stats(all_layup, "Layup Time")
#     get_all_operator_stats(all_close, "Close Time")
#     get_all_operator_stats(all_resin, "Resin Time")
#     get_all_operator_stats(all_cycle, "Cycle Time")

#     return all_layup, all_close, all_resin, all_cycle

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


def get_specific_operator_report(opnum, dtstart, dtend):
    """Get cycle stats report for only one operator, by their number.

    Parameters
    ----------
    opnum : TYPE
        DESCRIPTION.
    dtstart : TYPE
        DESCRIPTION.
    dtend : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    all_layup, all_close, all_resin, all_cycle = load_operator_data(dtstart, dtend)

    # Remove faulty duplicates
    all_layup = clean_duplicate_times(all_layup)
    all_close = clean_duplicate_times(all_close)
    all_resin = clean_duplicate_times(all_resin)
    all_cycle = clean_duplicate_times(all_cycle)

    # # Remove any row in the all_* dataframes that doesn't contain opnum
    # all_layup = all_layup.loc[(all_layup["Lead"] == opnum) |
    #                           (all_layup["Assistant 1"] == opnum) |
    #                           (all_layup["Assistant 2"] == opnum) |
    #                           (all_layup["Assistant 3"] == opnum)]
    # all_close = all_close.loc[(all_close["Lead"] == opnum) |
    #                           (all_close["Assistant 1"] == opnum) |
    #                           (all_close["Assistant 2"] == opnum) |
    #                           (all_close["Assistant 3"] == opnum)]
    # all_resin = all_resin.loc[(all_resin["Lead"] == opnum) |
    #                           (all_resin["Assistant 1"] == opnum) |
    #                           (all_resin["Assistant 2"] == opnum) |
    #                           (all_resin["Assistant 3"] == opnum)]
    # all_cycle = all_cycle.loc[(all_cycle["Lead"] == opnum) |
    #                           (all_cycle["Assistant 1"] == opnum) |
    #                           (all_cycle["Assistant 2"] == opnum) |
    #                           (all_cycle["Assistant 3"] == opnum)]

    # get_single_operator_stats(all_layup, opnum, "Layup Time")
    # get_single_operator_stats(all_close, opnum, "Close Time")
    # get_single_operator_stats(all_resin, opnum, "Resin Time")
    get_single_operator_stats(all_cycle, opnum, "Cycle Time")

    return all_layup, all_close, all_resin, all_cycle


def get_operator_report_by_list(operator_list, shift, dtstart, dtend):
    """
    """
    df_eval = load_operator_data(dtstart, dtend)[0]

    # # Remove faulty duplicates
    # all_layup = clean_duplicate_times(all_layup)
    # all_close = clean_duplicate_times(all_close)
    # all_resin = clean_duplicate_times(all_resin)
    # all_cycle = clean_duplicate_times(all_cycle)
    
    get_operator_stats_by_list(all_cycle, operator_list, "Cycle Time", shift)


def load_operator_data_single_mold(dtstart, dtend, moldcolor):
    """Load data via API for a single mold, identified by its publicID
    """
    url = api.url

    publicID = api.publicIds[moldcolor]
    tags = api.operator_tags[moldcolor]

    payload = {
        "source": {"publicId": publicID},
        "tags": tags,
        "start": dtstart,
        "end": dtend,
        "timeZone": "America/Denver"
    }
    headers = api.operator_headers

    response = requests.request("POST", url, json=payload, headers=headers)

    # print(response.text)

    # Save the response as a string
    datastr = response.text
    # print(datastr)

    # Convert the data string to a Pandas DataFrame
    df = pd.DataFrame([x.split(',') for x in datastr.split('\n')])
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df header
    df = df.reset_index(drop=True)

    # Replace empty values with NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Fix last column name having a carriage return at the end of the string
    lastcolold = df.columns[-1]
    if lastcolold[-1] == "\r":
        # print("Carriage return found at the end of column name")
        lastcolnew = lastcolold[0:-1]
        df = df.rename(columns={lastcolold: lastcolnew})
    
    # Convert to the relevant data types
    for i,col in enumerate(df.columns):
        if col == "time":
            df[col] = pd.to_datetime(df[col])
        else:
            df[col] = df[col].astype(float)
    
    # Fix issue where some data is read in from the day before the date of
    # dtstart. Get rid of rows with a date earlier than daystart.
    dtstart = dt.datetime.strptime(dtstart, "%Y-%m-%dT%H:%M:%SZ")
    daystart = dt.datetime.date(dtstart)
    df = df.loc[pd.to_datetime(df["time"]).dt.date >= daystart]

    return df


def load_operator_data(dtstart, dtend):
    """Load the data via API for all molds and export as a single DataFrame.
    """
    # Convert dtstart and dtend from datetimes to formatted strings
    dtstart = dtstart.strftime("%Y-%m-%dT%H:%M:%SZ")
    dtend = dtend.strftime("%Y-%m-%dT%H:%M:%SZ")

    # operator_frames = []
    layup_frames = []
    close_frames = []
    resin_frames = []
    cycle_frames = []
    
    all_man_ratios = []
    all_cycle_times = []
    
    # Get list of operator numbers on each shift by checking Excel data
    IDfilepath = data_assets.ID_data
    daylist, swinglist, gravelist = id_methods.get_shift_lists(IDfilepath)
    
    df_eval = pd.DataFrame()
    df_manminutes = pd.DataFrame()

    for moldcolor in api.molds:
        df_raw = load_operator_data_single_mold(dtstart, dtend, moldcolor)
        # Clean the data here before sending to a list of dataframes
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
        
        # Make a new dataframe with only time, Cycle Time, LeadIDs,
        # AssistantIDs, LeadTimes, AssistantTimes columns. LeadTimes and
        # AssistantTimes columns are the individual elapsed times for each
        # operator on the mold. LeadIDs and AssistantIDs columns use a list
        # of the operator numbers instead of single values.
        
        # Find the indices where there is a cycle time.
        cycle_inds = []
        not_nan_series = df_cleaned["Cycle Time"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                cycle_inds.append(i)
                
        # Find the indices where there is a lead login
        lead_inds = []
        not_nan_series = df_cleaned["Lead"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                lead_inds.append(i)
                
        # Find the indices where there is an assistant 1 login
        assist1_inds = []
        not_nan_series = df_cleaned["Assistant 1"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                assist1_inds.append(i)
                
        # Find the indices where there is an assistant 2 login
        assist2_inds = []
        not_nan_series = df_cleaned["Assistant 2"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                assist2_inds.append(i)
                
        # Find the indices where there is an assistant 1 login
        assist3_inds = []
        not_nan_series = df_cleaned["Assistant 3"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                assist3_inds.append(i)
        
        leadIDs = [[] for ind in cycle_inds]
        # assistIDs = [[] for ind in cycle_inds]
        man_minutes = [[] for ind in cycle_inds]
        
        for i, cyc_ind in enumerate(cycle_inds):
            #### Get the lists of IDs associated with each cycle time ####
            
            # If no one clocked in exactly at the same time as the cycle time
            # was logged, get the closest previous ID number for each role and 
            # add the ID number to the appropriate list.
            if i == 0:
                low = 0
                high = cyc_ind
                
                lead_between = between(lead_inds, low, high)
                leadIDs[i].extend(list_vals(df_cleaned["Lead"], lead_between))
                assist1_between = between(assist1_inds, low, high)
                # assistIDs[i].extend(list_vals(df_cleaned["Assistant 1"], assist1_between))
                assist2_between = between(assist2_inds, low, high)
                # assistIDs[i].extend(list_vals(df_cleaned["Assistant 2"], assist2_between))
                assist3_between = between(assist3_inds, low, high)
                # assistIDs[i].extend(list_vals(df_cleaned["Assistant 3"], assist3_between))
                
                for j,idx in enumerate(lead_between):
                    curr_id = df_cleaned["Lead"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][0]                    
                    else:
                        prev_id = df_cleaned["Lead"][lead_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][lead_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                    
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Lead"][idx] != 0:
                            datetime_start = df_cleaned["time"][lead_between[j-1]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                    
                for j,idx in enumerate(assist1_between):
                    curr_id = df_cleaned["Assistant 1"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][0]
                    else:
                        prev_id = df_cleaned["Assistant 1"][assist1_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][assist1_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                    
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(assist1_between)-1:
                        if df_cleaned["Assistant 1"][idx] != 0:
                            datetime_start = df_cleaned["time"][assist1_between[j-1]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                    
                for j,idx in enumerate(assist2_between):
                    curr_id = df_cleaned["Assistant 2"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][0]
                    else:
                        prev_id = df_cleaned["Assistant 2"][assist2_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][assist2_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                     
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(assist2_between)-1:
                        if df_cleaned["Assistant 2"][idx] != 0:
                            datetime_start = df_cleaned["time"][assist2_between[j-1]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                        
                for j,idx in enumerate(assist3_between):
                    curr_id = df_cleaned["Assistant 3"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][0]
                    else:
                        prev_id = df_cleaned["Assistant 3"][assist3_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][assist3_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                     
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(assist3_between)-1:
                        if df_cleaned["Assistant 3"][idx] != 0:
                            datetime_start = df_cleaned["time"][assist3_between[j-1]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                        
            else:
                # If someone was already logged in before the cycle started,
                # count them.
                input_idx = cycle_inds[i-1]
                idx = closest_before(input_idx, lead_inds)
                leadIDs[i].append(df_cleaned["Lead"][idx])
                # idx = closest_before(input_idx, assist1_inds)
                # assistIDs[i].append(df_cleaned["Assistant 1"][idx])
                # idx = closest_before(input_idx, assist2_inds)
                # assistIDs[i].append(df_cleaned["Assistant 2"][idx])
                # idx = closest_before(input_idx, assist3_inds)
                # assistIDs[i].append(df_cleaned["Assistant 3"][idx])
                
                # Get the IDs logged during the cycle
                low = cycle_inds[i-1]
                high = cyc_ind
                
                lead_between = between(lead_inds, low, high)
                leadIDs[i].extend(list_vals(df_cleaned["Lead"], lead_between))
                assist1_between = between(assist1_inds, low, high)
                # assistIDs[i].extend(list_vals(df_cleaned["Assistant 1"], assist1_between))
                assist2_between = between(assist2_inds, low, high)
                # assistIDs[i].extend(list_vals(df_cleaned["Assistant 2"], assist2_between))
                assist3_between = between(assist3_inds, low, high)
                # assistIDs[i].extend(list_vals(df_cleaned["Assistant 3"], assist3_between))
                
                for j,idx in enumerate(lead_between):
                    if j == 0:
                        prev_idx = closest_before(idx, lead_inds)
                        prev_id = df_cleaned["Lead"][prev_idx]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][cycle_inds[i-1]]
                    else:
                        prev_id = df_cleaned["Lead"][lead_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][lead_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                    
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Lead"][idx] != 0:
                            datetime_start = df_cleaned["time"][lead_between[j]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                    
                for j,idx in enumerate(assist1_between):
                    if j == 0:
                        prev_idx = closest_before(idx, assist1_inds)
                        prev_id = df_cleaned["Assistant 1"][prev_idx]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][cycle_inds[i-1]]
                    else:
                        prev_id = df_cleaned["Assistant 1"][assist1_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][assist1_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                    
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(assist1_between)-1:
                        if df_cleaned["Assistant 1"][idx] != 0:
                            datetime_start = df_cleaned["time"][assist1_between[j]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                        
                for j,idx in enumerate(assist2_between):
                    if j == 0:
                        prev_idx = closest_before(idx, assist2_inds)
                        prev_id = df_cleaned["Assistant 2"][prev_idx]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][cycle_inds[i-1]]
                    else:
                        prev_id = df_cleaned["Assistant 2"][assist2_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][assist2_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                    
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(assist2_between)-1:
                        if df_cleaned["Assistant 2"][idx] != 0:
                            datetime_start = df_cleaned["time"][assist2_between[j]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
                    
                for j,idx in enumerate(assist3_between):
                    if j == 0:
                        prev_idx = closest_before(idx, assist3_inds)
                        prev_id = df_cleaned["Assistant 3"][prev_idx]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][cycle_inds[i-1]]
                    else:
                        prev_id = df_cleaned["Assistant 3"][assist3_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["time"][assist3_between[j-1]]
                    datetime_end = df_cleaned["time"][idx]
                    minutes = minutes_diff(datetime_start, datetime_end)
                    man_minutes[i].append(minutes)
                    
                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(assist3_between)-1:
                        if df_cleaned["Assistant 3"][idx] != 0:
                            datetime_start = df_cleaned["time"][assist3_between[j]]
                            datetime_end = df_cleaned["time"][cyc_ind]
                            minutes = minutes_diff(datetime_start, datetime_end)
                            man_minutes[i].append(minutes)
            
            
        # Get the unique IDs for each cycle time
        for i in range(len(leadIDs)):
            # Get unique lead IDs
            IDs = leadIDs[i]    # list of IDs
            IDs = list(np.unique(IDs))
            
            # Remove zeros for ID numbers
            if len(IDs) == 1 and IDs[0] == 0:
                pass
            else:
                IDs = [id for id in IDs if id != 0]
            
            if len(IDs) == 0:
                IDs = [0.0]
                
            leadIDs[i] = IDs
            
            # # Get unique assistant IDs
            # IDs = assistIDs[i]
            # IDs = list(np.unique(IDs))
            # assistIDs[i] = IDs
            
        for i,minutes_list in enumerate(man_minutes):
            man_minutes[i] = sum(minutes_list)
            
        cycle_times = list(df_cleaned["Cycle Time"][cycle_inds])
        datetimes = list(df_cleaned["time"][cycle_inds])
        weekdays = [date.weekday() for date in datetimes]
        firstflags = []
        for i,day in enumerate(weekdays):
            if i == 0 and day == 0:
                if datetimes[i].time() < dt.time(8,0,0):
                    firstflags.append(1)
                else:
                    firstflags.append(0)
            elif day == 0 and weekdays[i-1] != 0:
                firstflags.append(1)
            else:
                firstflags.append(0)
                
        shifts = []
        for i in range(len(leadIDs)):
            shifts.append([])
            for j in range(len(leadIDs[i])):
                if leadIDs[i][j] in daylist:
                    shifts[i].append("Day")
                elif leadIDs[i][j] in swinglist:
                    shifts[i].append("Swing")
                elif leadIDs[i][j] in gravelist:
                    shifts[i].append("Graveyard")
                elif leadIDs[i][j] == 0:
                    pass
                else:
                    raise ValueError("ID not recognized as part of a shift")
            
        
        # Create DataFrame for evaluations for current mold
        data_eval = {"time": datetimes, "Day": weekdays,
                     "First Monday Part": firstflags, "Cycle Time": cycle_times,
                     "Lead": leadIDs, "Shift": shifts
                     }
        
        df_eval_mold = pd.DataFrame(data=data_eval)
        
        # Create DataFrame for evaluating man-minutes and cycle times
        man_ratios = []
        for i in range(len(man_minutes)):
            ratio = man_minutes[i] / cycle_times[i]
            man_ratios.append(ratio)
            
        data_manminutes_mold = {"time": datetimes, "Day": weekdays,
                           "First Monday Part": firstflags, "Cycle Time": cycle_times,
                           "Shift": shifts, "Man-Minutes": man_minutes,
                           "Man Ratio": man_ratios
                           }
        
        df_manminutes_mold = pd.DataFrame(data=data_manminutes_mold)
        
        # Append mold data to larger DataFrame for all data
        df_eval = pd.concat([df_eval, df_eval_mold], ignore_index=True)
        df_manminutes = pd.concat([df_manminutes, df_manminutes_mold], ignore_index=True)
        
        # reject_inds = []
        # for i in range(len(man_minutes)):
        #     if man_minutes[i] == 0.0 or man_minutes[i] > 4*cycle_times[i]:
        #         reject_inds.append(i)
                
        # man_minutes = [i for j,i in enumerate(man_minutes) if j not in reject_inds]
        # cycle_times = [i for j,i in enumerate(cycle_times) if j not in reject_inds]
        
            
        # all_man_ratios.extend(man_ratios)
        # all_cycle_times.extend(cycle_times)
        
        # plt.scatter(man_ratios, cycle_times)
        # plt.title("{} Correlation".format(moldcolor))
        # plt.xlabel("Synthetic number of people on mold")
        # plt.ylabel("Cycle Times (min)")
        # plt.show()
    
    # m, b = np.polyfit(all_man_ratios, all_cycle_times, 1)
    # x = np.asarray(all_man_ratios)
    
    # plt.scatter(all_man_ratios, all_cycle_times)
    # plt.plot(x, m*x+b, 'r')
    # plt.title("Correlation with all data")
    # plt.xlabel("Synthetic number of people on mold")
    # plt.ylabel("Cycle Times (min)")
    # plt.show()
    
    # # Create dictionary of data for df_associate
    # data_associate = {"time": timedata_cycle}
    
    

    return df_eval, df_manminutes

def between(l1, low, high):
    l2 = [i for i in l1 if i >= low and i < high]
    return l2

def closest_before(input_idx, input_list):
    input_array = np.asarray(input_list)
    prev_array = input_array[input_array < input_idx]
    if len(prev_array) == 0:
        prev_idx = input_array[0]
    else:
        prev_idx = prev_array.max()
    return prev_idx

# def closest_after(input_idx, input_list):
#     input_array = np.asarray(input_list)
#     next_idx = input_array[input_array > input_idx].min()
#     return next_idx

def list_vals(df_col, idx_list):
    col_list = list(df_col)
    res_list = [col_list[i] for i in idx_list]
    return res_list

def minutes_diff(datetime_start, datetime_end):
    minutes = (datetime_end - datetime_start).total_seconds() / 60.0
    return minutes


def get_operator_list(shiftstr):
    """
    

    Parameters
    ----------
    shiftstr : TYPE
        DESCRIPTION.

    Returns
    -------
    operator_list : A list of integers corresponding to the operators of the
        chosen shift.

    """
    operator_list = []
    df = pd.read_excel(data_assets.ID_data, None)
    df_lead = df["Personnel-Lead"]
    df_shift = df_lead.loc[df_lead["Shift"] == shiftstr]
    ids = list(df_shift["ID"])
    ids = [str(id) for id in ids]
    ids = [id[2:] for id in ids]
    operator_list = [int(id) for id in ids]
    
    return operator_list

def cycle_time_over_time(dtstart, dtend):
    all_layup, all_close, all_resin, all_cycle = load_operator_data(dtstart, dtend)
    
    cycles = all_cycle.drop(labels=["Lead", "Assistant 1", "Assistant 2", "Assistant 3"], axis=1)
    
    # Sort by time column
    cycles = cycles.sort_values(by="time", axis=0)
    # Reindex
    cycles = cycles.reset_index(drop=True)
    cycles["Date"] = pd.to_datetime(cycles["time"]).dt.date
    cycles = cycles[["Date", "Cycle Time"]]
    
    fig,ax=plt.subplots(dpi=300)
    # boxdates = cycles["Date"].astype(str)
    # customPalette = sns.light_palette("lightblue", 1, reverse=True)
    # flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
    # # sns.boxplot(x="variable", y="value", data=pd.melt(operator_compare), flierprops=flierprops, palette=customPalette)
    # sns.boxplot(x=boxdates, y=cycles["Cycle Time"], flierprops=flierprops, palette=customPalette)
    medians = cycles.groupby(["Date"])["Cycle Time"].median()
    dates = cycles["Date"].unique()
    dates_str = [str(day) for day in dates]
    
    # Reorganize data for boxplot property calculation
    whiskers_hi = []
    whiskers_lo = []
    outliers = []
    for date in dates:
        df_day = cycles.loc[cycles["Date"] == date]
        cycle_data = list(df_day["Cycle Time"])
        stats = boxplot_stats(cycle_data)
        stats = stats[0]
        
        whishi = stats["whishi"]
        whislo = stats["whislo"]
        fliers = stats["fliers"]
        whiskers_hi.append(whishi)
        whiskers_lo.append(whislo)
        outliers.append(fliers)
        # print(whishi)
        # print(whislo)
        # print("")
    
    
    
    # Skip labels so there are 5 at most on the plot
    labelskip = 0
    dateticks = dates_str
    while len(dateticks) > 5:
        labelskip += 1
        dateticks = dates_str[::labelskip]
        
    datelabels = []
    for i,day in enumerate(dates_str):
        if day in dateticks:
            datelabels.append(day)
        else:
            datelabels.append("")
    
    # Make the plot
    sns.set_theme(style="ticks")
    sns.lineplot(x=dates, y=medians, linewidth=3)
    plt.plot(dates, whiskers_hi, 'b', alpha=0.5)
    plt.plot(dates, whiskers_lo, 'b', alpha=0.5)
    plt.fill_between(dates, whiskers_hi, whiskers_lo, alpha=0.2)
    for i,fliers in enumerate(outliers):
        if len(fliers) > 0:
            outlier_dates = [dates[i]] * len(fliers)
            sns.scatterplot(x=outlier_dates, y=fliers, color='b', marker='o', alpha=0.5, s=20)
    
    plt.xticks(dates, datelabels, rotation=90)
    plt.xlabel("Date")
    plt.title("Cycle Time Variability")
    
    return cycles, medians, dates


def filter_outlier_cycles(dtstart, dtend):
    # Load all operator data to determine what times the outliers took place
    all_cycle = load_operator_data(dtstart, dtend)[3]
    # all_cycle = all_cycle.drop(["Lead", "Assistant 1",
                                # "Assistant 2", "Assistant 3"], axis=1)
    
    stats = boxplot_stats(all_cycle["Cycle Time"])
    stats = stats[0]
    outliers = stats["fliers"]
    whisker_hi = stats["whishi"]
    whisker_lo = stats["whislo"]
    
    all_outliers = all_cycle.loc[(all_cycle["Cycle Time"]>whisker_hi) | (all_cycle["Cycle Time"]<whisker_lo)]
    all_outliers = all_outliers.reset_index(drop=True)
    
    # Load each dataframe by mold to check for outlier matches and 
    brown_outliers  = pd.DataFrame()
    purple_outliers = pd.DataFrame()
    red_outliers    = pd.DataFrame()
    pink_outliers   = pd.DataFrame()
    orange_outliers = pd.DataFrame()
    green_outliers  = pd.DataFrame()
    
    # Convert dtstart and dtend from datetimes to formatted strings
    dtstart = dtstart.strftime("%Y-%m-%dT%H:%M:%SZ")
    dtend = dtend.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    matchcount = 0
    
    for moldcolor in api.molds:
        df_raw = load_operator_data_single_mold(dtstart, dtend, moldcolor)
        
        # Drop the columns not relevant to cycle times
        # df_raw = df_raw.drop(["Weekly Count", "Monthly Count", "Trash Count"], axis=1)

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
        
        df_cycles = df_cleaned[~df_cleaned["Cycle Time"].isnull()]
        
        df_cycles = df_cycles.reset_index(drop=True)
        df_cycles = df_cycles.drop(["Layup Time", "Close Time", "Resin Time", "Lead", "Assistant 1", "Assistant 2", "Assistant 3"], axis=1)
        
        # print("\n####### Mold color: {} #########\n".format(moldcolor))
        
        # Get the rows that match outliers in all_outliers
        for ind_all in all_outliers.index:
            # print("\nall_outliers index: {}\n".format(ind_all))
            for ind_mold in df_cycles.index:
                # print("df_cycles index: {}".format(ind_mold))
                if df_cycles["time"][ind_mold] == all_outliers["time"][ind_all] and df_cycles["Cycle Time"][ind_mold] == all_outliers["Cycle Time"][ind_all]:
                    # print("Found a match!")
                    matchcount += 1
                    outlierrow = df_cycles.iloc[ind_mold]
                    if moldcolor == "Brown":
                        brown_outliers = brown_outliers.append(outlierrow, ignore_index=True)
                    elif moldcolor == "Purple":
                        purple_outliers = purple_outliers.append(outlierrow, ignore_index=True)
                    elif moldcolor == "Red":
                        red_outliers = red_outliers.append(outlierrow, ignore_index=True)
                    elif moldcolor == "Pink":
                        pink_outliers = pink_outliers.append(outlierrow, ignore_index=True)
                    elif moldcolor == "Orange":
                        orange_outliers = orange_outliers.append(outlierrow, ignore_index=True)
                    elif moldcolor == "Green":
                        green_outliers = green_outliers.append(outlierrow, ignore_index=True)
                        
                # else:
                    # print("...")
        
    # print("Matchcount: {}".format(matchcount))
    # print("")
    return all_outliers, brown_outliers, purple_outliers, red_outliers, pink_outliers, orange_outliers, green_outliers
        
        



if __name__ == "__main__":
    dtstart = dt.datetime(2022,3,1,0,0,0)
    today = dt.date.today()
    endtime = dt.time(23,59,59)
    dtend = dt.datetime.combine(today, endtime)

    df_eval, df_manminutes = load_operator_data(dtstart, dtend)
    
    operator_list = [217, 254, 666]
    get_operator_stats_by_list(df_eval, operator_list, shift=None)