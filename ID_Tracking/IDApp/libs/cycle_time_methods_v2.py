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
from natsort import natsorted
import matplotlib as mpl
import pytz

# If running as part of a compiled exe file (i.e. as the finalized ID &
# Evaluation Tool app), comment out the imports that contain "from . import"
import data_assets
import id_methods
import api_config_vars as api
# from . import data_assets
# from . import id_methods
# from . import api_config_vars as api

##### PDF Methods #####
class OperatorStatsPDF(FPDF):
    """
    Class definition, based on FPDF class, for producing cycle time reports.
    """
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

    def page_body(self, datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift):
        # Define the text inputs that are needed to produce the report
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
        
        # Add the images and text to the report
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
    """
    Checks the number of cycles logged for each category (Lead, Shift, and
    RockWell), and compares it to a threshold. Outputs text that indicates
    whether the number of cycles is sufficient for a fair report.

    Parameters
    ----------
    cycle_count : int
        The number of cycles counted for a given category.

    Returns
    -------
    cycles_text : str
        A string that includes the number of cycles logged and one of two
        statements about whether the number is sufficient for evaluation.

    """
    thresh = 100
    
    if cycle_count < thresh:
        cycles_text = "{}     Choose longer evaluation period".format(cycle_count)
    elif cycle_count >= thresh:
        cycles_text = "{}     OK for evaluation".format(cycle_count)
        
    return cycles_text
            

def generate_operator_PDF(datestart, dateend, plot, opnum, opname, cycles_logged, medians, averages, shift, filename, exportpath):
    """
    Convenience function for creating a PDF report of an operator's cycle
    times.

    Parameters
    ----------
    datestart : datetime.date
        Starting date for the report period.
    dateend : datetime.date
        Ending date for the report period.
    plot : str
        Full filename and path to the plot, which is saved as a PNG image.
    opnum : int
        Integer operator number of up to 3 digits.
    opname : str
        Operator name.
    cycles_logged : list with length 3
        A list of integers that correspond to the number of cycles logged by
        the operator as lead, by the shift as a whole, and by the company as a
        whole.
    medians : list with length 3
        A list of floats that correspond to the median cycle time logged by
        the operator as lead, by the shift as a whole, and by the company as a
        whole.
    averages : list with length 3
        A list of floats that correspond to the average cycle time logged by
        the operator as lead, by the shift as a whole, and by the company as a
        whole.        
    shift : str
        String from one of the following options: "Day", "Swing", "Graveyard",
        or "N/A". Does not check that this is true. This is simply a text input
        that indicates the operator's shift on the final report.
    filename : str
        Name of the PDF file output.
    exportpath : str
        Path to the folder where filename will be placed.

    Returns
    -------
    None.

    """
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
    Take all PDFs in the output folder and merge them together.

    Parameters
    ----------
    exportfolder : str
        Path to the export folder.
    mergedfilepath : str
        Full filepath of the exported file. Should contain the path of
        exportfolder.

    Returns
    -------
    None.

    """
    x = [a for a in os.listdir(exportfolder) if a.endswith(".pdf")]
    x = natsorted(x)
    # print(x)
    x = [exportfolder + "\\" + a for a in x]    # List of strings at this point

    merger = PdfFileMerger()

    for pdf in x:
        with open(pdf, 'rb') as source:
            tmp = PdfFileReader(source)
            merger.append(tmp)

    with open(mergedfilepath, "wb") as fout:
        merger.write(fout)


def get_all_operator_stats(df):
    """
    Convenience function for getting cycle time reports on all operators.
    Essentially a special case of get_operator_stats_by_list.

    Parameters
    ----------
    df : Pandas DataFrame
        A DataFrame that has gone through the "cleaning" process by
        the functions load_operator_data and clean_duplicate_times.

    Returns
    -------
    None.

    """
    # Get operator list
    IDfilepath = data_assets.ID_data
    allnums = id_methods.get_all_employee_nums()
    operator_list = list(allnums["ID"])
    operator_list = [int(id) for id in operator_list]
    
    get_operator_stats_by_list(df, operator_list, "all")


def get_operator_stats_by_list(df, operator_list, shift=None):
    """
    Take in a cleaned DataFrame, df, and a list of integers of up to 3 digits,
    operator_list, and a shift indicator if necessary. Produce the cycle time
    reports for all operators in operator_list, and combine appropriately
    with a name indicated by the shift tag. Automatically opens the final PDF
    report when ready.
    
    Parameters
    ----------
    df : Pandas DataFrame
        A DataFrame that has gone through the "cleaning" process by
        the functions load_operator_data and clean_duplicate_times.
    operator_list : list of ints
        A list of integers of up to 3 digits. For operator numbers less than
        100, no preceding zeros are required.
    shift : str (optional)
        By default shift is None, but if a shift string is specified ("day",
        "swing", "graveyard") then the merged file will be named accordingly
        for convenience. A final option, "all", can be used to get the stats
        for all operators.

    Returns
    -------
    None.

    """

    startdate = df["time"].iloc[0].date()
    enddate = df["time"].iloc[-1].date()
    
    timestring = "Cycle Time"

    directory = data_assets.pdftempfolder
    
    # Get list of operator numbers on each shift by checking Excel data
    IDfilepath = data_assets.ID_data
    daylist, swinglist, gravelist = id_methods.get_shift_lists(IDfilepath)
    
    noperators = len(operator_list)

    for i,operator in enumerate(operator_list):
        print("\n{}% complete".format(np.around(i*100/noperators, 2)))
        # Get all rows where the current operator is in the lead list
        df_lead = df[pd.DataFrame(df.Lead.tolist()).isin([operator]).any(1).values]
        
        # Get all rows for the current operator's shift
        operator_shift = None
        if operator in daylist:
            operator_shift = "Day"
        elif operator in swinglist:
            operator_shift = "Swing"
        elif operator in gravelist:
            operator_shift = "Graveyard"
        else:
            operator_shift = "N/A"
            
        df_shift = df[pd.DataFrame(df.Shift.tolist()).isin([operator_shift]).any(1).values]
        
        # Remove rows where it's the first part on a Monday
        df_lead = df_lead[df_lead["First Monday Part"] != 1]
        df_shift = df_shift[df_shift["First Monday Part"] != 1]
        df_company = df[df["First Monday Part"] != 1]

        # Compare the current operator against all cycle times
        lead_col = "Lead"
        shift_col = "Shift"
        company_col = "RockWell"
        operator_compare = pd.DataFrame()
        operator_compare = pd.concat([operator_compare, df_lead[timestring].rename(lead_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_shift[timestring].rename("Shift")], axis=1)
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
            


    if shift is None and len(operator_list) > 1:
        mergefile = "List_Operators_{}_to_{}.pdf".format(startdate, enddate)
        mergedfilepath = data_assets.pdftempfolder + "\\" + mergefile
        merge_operator_PDFs(exportpath, mergedfilepath)
    elif shift is None and len(operator_list) == 1:
        # Copy merged file into Operator_Reports folder
        mergefile = filename
        mergedfilepath = data_assets.pdftempfolder + "\\" + filename
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
    
    print("\n100.0% complete")
    
    # Automatically open the merged file from its new location
    os.system(dest)


def merge_by_shift(startdate, enddate, shift, exportpath):
    """
    Combine all PDF files in the temp folder together and name them according
    to the chosen shift input.

    Parameters
    ----------
    startdate : datetime.date
        Starting date for the analysis period. Used to name the merged file.
    enddate : datetime.date
        Ending date for the analysis period. Used to name the merged file.
    shift : str
        Name of the shift for which the files will be merged. Can have any
        combination of capitalized letters, but the options only include:
            "day", "swing", "graveyard", and "all".
    exportpath : str
        Path to the export folder.

    Raises
    ------
    ValueError
        If no shift is specified, an error is raised.

    Returns
    -------
    mergefile : str
        Filename of the merged file, without the path to the file.
    mergedfilepath : str
        Complete filepath, including filename, of the merged file.

    """
    shift = shift.lower()
    if shift == "day":
        mergefile = "Day_Shift_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    elif shift == "swing":
        mergefile = "Swing_Shift_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    elif shift == "graveyard":
        mergefile = "Graveyard_Shift_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    elif shift == "all":
        mergefile = "All_Operators_Cycle_Times_{}_to_{}.pdf".format(startdate, enddate)
    else:
        raise ValueError("No shift specified")

    mergedfilepath = data_assets.pdftempfolder + "\\" + mergefile
    merge_operator_PDFs(exportpath, mergedfilepath)
    
    return mergefile, mergedfilepath


def get_single_operator_stats(df, opnum):
    """
    Convenience function for getting the cycle time statistics from one
    operator. Produces and saves the PDF report, and opens it when it's ready.

    Parameters
    ----------
    df : Pandas DataFrame
        A DataFrame that has gone through the "cleaning" process by
        the functions load_operator_data and clean_duplicate_times.
    opnum : int
        Operator number, of up to 3 digits. No preceding zeros.

    Returns
    -------
    None.

    """
    operator_list = [opnum]
    get_operator_stats_by_list(df, operator_list, shift=None)


def lookup_operator_name(opnum, IDfilepath):
    """
    Convenience function for producing an operator's name from their number.

    Parameters
    ----------
    opnum : int
        Operator number. Integer of up to 3 digits, no preceding zeros.
    IDfilepath : str
        Full filepath to the Excel file that contains the ID data for
        operators.

    Returns
    -------
    opname : str
        Operator name.

    """
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


def clean_duplicate_times(df):
    """
    Sometimes the PLCs will produce duplicate cycle time data. This occurs for
    various reasons, but it alters the cycle time statistics and must be
    filtered out of the raw data.

    Parameters
    ----------
    df : Pandas DataFrame
        Raw DataFrame as output by load_operator_data.

    Returns
    -------
    df : Pandas DataFrame
        The same DataFrame as the input, but with duplicate cycle times
        removed.

    """
    dupinds = []
    # First pass to remove obvious duplicates
    for i in range(len(df)):
        if i == 0:
            continue
        else:
            prev = df.iloc[i-1,1:5]
            curr = df.iloc[i,1:5]
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


# def compare_num_ops(df, timestring:str):
#     """
#     Output a dataframe that has three columns: time, measured time of interest
#     (Layup Time, Close Time, Resin Time, or Cycle Time), and the number of
#     operators on the mold for that measured time. Output box plots for the
#     data.

#     Parameters
#     ----------
#     df : Pandas DataFrame
#         DESCRIPTION.



#     Returns
#     -------
#     df_num_ops: Pandas DataFrame
#         3 columns: time, measured time of interest, and number of operators

#     """
#     df_num_ops = df
#     opcounts = []
#     opcount = 0
#     for i in range(len(df_num_ops)):
#         oplist = df_num_ops.iloc[i,2:6]
#         opcount = oplist.astype(bool).sum()
#         opcounts.append(opcount)

#     # Add the list of opcounts as a column to df_num_ops
#     df_num_ops["N Operators"] = opcounts

#     # Drop unnecessary columns
#     df_num_ops = df_num_ops.drop(columns=["Lead", "Assistant 1", "Assistant 2", "Assistant 3"])

#     # # SORT BY NUM OPS HERE
#     # df_num_ops = df_num_ops.sort_values("N Operators")
#     # df_num_ops = df_num_ops.reset_index(drop=True)

#     directory = os.getcwd()
#     sns.set_theme(style="whitegrid")
#     customPalette = sns.light_palette("lightblue", 5)
#     flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
#     ax = sns.boxplot(x="N Operators", y=timestring, data=df_num_ops, flierprops=flierprops, palette=customPalette)
#     plt.title("Comparison of Operators on Mold: {}".format(timestring))

#     # Annotate each boxplot with the number of samples
#     # Calculate number of obs per group & median to position labels
#     medians = df_num_ops.groupby(["N Operators"])[timestring].median().values
#     counts = df_num_ops["N Operators"].value_counts()
#     nobs = []
#     for i in range(5):
#         try:
#             nobs.append(counts[i])
#         except KeyError:
#             continue
#     nobs = [str(x) for x in nobs]
#     nobs = ["n: " + i for i in nobs]

#     # Add it to the plot
#     pos = range(len(nobs))
#     for tick,label in zip(pos,ax.get_xticklabels()):
#         ax.text(pos[tick],
#                 medians[tick] + 0.03,
#                 nobs[tick],
#                 horizontalalignment='center',
#                 size='x-small',
#                 color='k',
#                 weight='semibold')

#     plotname = directory + "\\Operator_Number_Comparison_{}.png".format(timestring.replace(" ","_"))
#     plt.savefig(plotname, dpi=300)
#     plt.close()


def get_specific_operator_report(opnum, dtstart, dtend):
    """
    Convenience function to get cycle stats report for only one operator, by
    their number. This is used in the final ID & Evaluation app.

    Parameters
    ----------
    opnum : int
        Operator number of up to 3 digits, no preceding zeros.
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.

    Returns
    -------
    df_eval: Pandas DataFrame
        DataFrame containing the data that went into the report.

    """
    df_eval = load_operator_data(dtstart, dtend)[0]

    # Remove faulty duplicates
    df_eval = clean_duplicate_times(df_eval)

    get_single_operator_stats(df_eval, opnum)

    return df_eval


def get_operator_report_by_list(operator_list, shift, dtstart, dtend):
    """
    Convenience function to get cycle stats reports for a list of operators, by
    their numbers. This is used in the final ID & Evaluation app.

    Parameters
    ----------
    operator_list : list of ints
        List of operator numbers of up to 3 digits, no preceding zeros.
    shift : str
        String corresponding to the chosen shift, if desired. Can be None if
        operator_list doesn't correspond to a specific shift.
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.

    Returns
    -------
    df_eval : Pandas DataFrame
        DataFrame containing the data that went into the reports.

    """
    df_eval = load_operator_data(dtstart, dtend)[0]   
    
    # Remove faulty duplicates
    df_eval = clean_duplicate_times(df_eval)
    
    get_operator_stats_by_list(df_eval, operator_list, shift)
    
    return df_eval


def get_all_operator_reports(dtstart, dtend):
    """
    Convenience function to get cycle stats reports for all operators in the
    company. This is used in the final ID & Evaluation app.

    Parameters
    ----------
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.

    Returns
    -------
    df_eval : Pandas DataFrame
        DataFrame containing the data that went into the reports.

    """
    df_eval = load_operator_data(dtstart, dtend)[0]

    # Remove faulty duplicates
    df_eval = clean_duplicate_times(df_eval)

    get_all_operator_stats(df_eval)

    return df_eval


def load_operator_data_single_mold(dtstart, dtend, moldcolor):
    """
    Load cycle time data via API for a single mold, identified by its publicID.

    Parameters
    ----------
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.
    moldcolor : str
        Mold station color. Options include:
            "Brown", "Purple", "Red", "Pink", "Orange", "Green"

    Returns
    -------
    df : Pandas DataFrame
        Data loaded from StrideLinx API for cycle times, operators, etc.

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
    """
    Load the data via API for all molds and export as a single DataFrame.

    Parameters
    ----------
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.

    Raises
    ------
    ValueError
        If an operator number isn't recognized as part of a shift, an error is
        raised.

    Returns
    -------
    df_eval : Pandas DataFrame
        DataFrame that is passed on to be cleaned of duplicate cycle times and
        then used to produce operator cycle time reports.
    df_manminutes : Pandas DataFrame
        DataFrame for calculating "man-minutes" contributed to each cycle time.

    """
    # Adjust dtstart and dtend to Central European Time for API compatibility
    mtn = pytz.timezone('US/Mountain')
    # utc = pytz.UTC
    cet = pytz.timezone('CET')
    
    dtstart = mtn.localize(dtstart)
    dtend = mtn.localize(dtend)
    
    dtstart = dtstart.astimezone(cet)
    dtend = dtend.astimezone(cet)
    
    # Subtract an hour from start (weird API behavior adjustment - end time
    # doesn't appear to be affected by this issue, so it's not a daylight
    # savings time thing)
    dtstart = dtstart - dt.timedelta(hours=1)
    dtend = dtend - dt.timedelta(hours=1)
    
    # Convert dtstart and dtend from datetimes to formatted strings
    dtstart = dtstart.strftime("%Y-%m-%dT%H:%M:%SZ")
    dtend = dtend.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # all_man_ratios = []
    # all_cycle_times = []
    
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
                assist2_between = between(assist2_inds, low, high)
                assist3_between = between(assist3_inds, low, high)
                
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
                
                # Get the IDs logged during the cycle
                low = cycle_inds[i-1]
                high = cyc_ind
                
                lead_between = between(lead_inds, low, high)
                leadIDs[i].extend(list_vals(df_cleaned["Lead"], lead_between))
                assist1_between = between(assist1_inds, low, high)
                assist2_between = between(assist2_inds, low, high)
                assist3_between = between(assist3_inds, low, high)
                
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
            
        # Find all instances of ID 2 and change to 999 (special case where
        # an operator changed numbers -- don't do this again!)
        for idlist in leadIDs:
            for i,id_int in enumerate(idlist):
                if id_int == 2.0:
                    idlist[i] = 999.0
            
        for i,minutes_list in enumerate(man_minutes):
            man_minutes[i] = sum(minutes_list)
        
        # Catch whether the part is the first part on a Monday
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

    return df_eval, df_manminutes


def between(l1, low, high):
    """
    Outputs a list of the values from l1 that are between low and high, minimum
    inclusive.

    Parameters
    ----------
    l1 : list
        List of ints or floats for filtering.
    low : int or float
        Lowest acceptable value for filtering l1. Assumed to be less than high.
    high : int or float
        Highest value (non-inclusive) for filtering l1. Assumed to be greater
        than low.

    Returns
    -------
    l2 : list
        Contains the values between low and high that are in l1.

    """
    l2 = [i for i in l1 if i >= low and i < high]
    return l2


def closest_before(input_idx, input_list):
    """
    Takes a chosen index and compares against a list of indices, input_list.
    Finds the closest previous index value to the chosen input_idx value.

    Parameters
    ----------
    input_idx : int
        The reference index value against which the function will compare.
    input_list : list of ints
        A list of integers that are indices. Assumed to be a list in ascending
        order, with no repeated values. (Ex: [3,6,10,22])

    Returns
    -------
    prev_idx : int
        The value from input_list that is the closest previous value to
        input_idx. If input_idx = 20 and input_list = [3,6,10,22], then
        prev_idx will be 10.

    """
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
    """
    Takes a Pandas DataFrame column, turns it into a list, and outputs only 
    the elements of that list indicated by a list of indices found in idx_list.

    Parameters
    ----------
    df_col : column of a Pandas DataFrame (called as df["col_name"])
        Any column of a Pandas DataFrame. Doesn't assume a type of data.
    idx_list : list of ints
        

    Returns
    -------
    res_list : list
        List of elements of df_col as chosen by indices in idx_list. Data type
        of elements will be the same as that of df_col.

    """
    col_list = list(df_col)
    res_list = [col_list[i] for i in idx_list]
    return res_list


def minutes_diff(datetime_start, datetime_end):
    """
    Convenience function for finding the decimal number of minutes between two
    datetime.datetime objects.

    Parameters
    ----------
    datetime_start : datetime.datetime
        Starting datetime. Assumed to be earlier than datetime_end.
    datetime_end : datetime.datetime
        Ending datetime. Assumed to be after datetime_start.

    Returns
    -------
    minutes : float
        The number of minutes, as a decimal, between datetime_start and
        datetime_end. This will work regardless of how many days are between
        the start and end of the period.

    """
    minutes = (datetime_end - datetime_start).total_seconds() / 60.0
    return minutes


def get_operator_list(shiftstr):
    """
    Get a list of integer operator numbers, based on selected shift.

    Parameters
    ----------
    shiftstr : str
        May be "Day", "Swing", or "Graveyard".

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
    """
    Plots a special chart of cycle time variability over time. Takes the
    upper and lower bounds of box plots (upper and lower whiskers) and the
    medians, as well as any outliers, and constructs a shaded line plot with
    outliers shown as dots. This is to visualize the daily effect of any
    process improvements on cycle time variability.

    Parameters
    ----------
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.

    Returns
    -------
    cycles : Pandas DataFrame
        A DataFrame with two columns: Date (datetime.date) and Cycle Time
        (float, in minutes).
    medians : Pandas Series
        Median Cycle Time indexed by date.
    dates : NumPy object array
        Datetime.dates for each date included in the data.

    """
    df_eval = load_operator_data(dtstart, dtend)[0]
    
    cycles = df_eval
    
    # Sort by time column
    cycles = cycles.sort_values(by="time", axis=0)
    # Reindex
    cycles = cycles.reset_index(drop=True)
    cycles["Date"] = pd.to_datetime(cycles["time"]).dt.date
    cycles = cycles[["Date", "Cycle Time"]]
    
    fig,ax=plt.subplots(dpi=300)
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
    
    # Skip labels so there are 5 at most on the plot, for readability
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
    """
    Function for finding all cycle time outliers, both as a whole and by mold.

    Parameters
    ----------
    dtstart : datetime.datetime
        Starting date and time for the period of interest.
    dtend : datetime.datetime
        Ending date and time for the period of interest.

    Returns
    -------
    all_outliers : Pandas DataFrame
        DataFrame of all identified outliers in the dataset when looking at the
        time period as a whole (not daily, as in the cycle_time_over_time
        function).
        Columns:
            time: datetime.datetime of when the cycle was logged
            Day: Integer day number (0 being Monday)
            First Monday Part: Integer indicator of whether the cycle time was
                from the first part on a mold on a Monday (0 or 1)
            Cycle Time: Float number of minutes in the cycle
            Lead: List of float ID numbers
            Shift: List of string shift names for operators that participated
                as lead on the cycle
    brown_outliers : Pandas DataFrame
        DataFrame of all identified outliers for the brown mold. A subset of
        the data in all_outliers.
        Columns: Same as all_outliers.
    purple_outliers : Pandas DataFrame
        DataFrame of all identified outliers for the purple mold. A subset of
        the data in all_outliers.
        Columns: Same as all_outliers.
    red_outliers : Pandas DataFrame
        DataFrame of all identified outliers for the red mold. A subset of
        the data in all_outliers.
        Columns: Same as all_outliers.
    pink_outliers : Pandas DataFrame
        DataFrame of all identified outliers for the pink mold. A subset of
        the data in all_outliers.
        Columns: Same as all_outliers.
    orange_outliers : Pandas DataFrame
        DataFrame of all identified outliers for the orange mold. A subset of
        the data in all_outliers.
        Columns: Same as all_outliers.
    green_outliers : Pandas DataFrame
        DataFrame of all identified outliers for the green mold. A subset of
        the data in all_outliers.
        Columns: Same as all_outliers.

    """
    # Load all operator data to determine what times the outliers took place
    all_cycle = load_operator_data(dtstart, dtend)[0]
    
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
        
        # Get the rows that match outliers in all_outliers
        for ind_all in all_outliers.index:
            for ind_mold in df_cycles.index:
                if df_cycles["time"][ind_mold] == all_outliers["time"][ind_all] and df_cycles["Cycle Time"][ind_mold] == all_outliers["Cycle Time"][ind_all]:
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

    return all_outliers, brown_outliers, purple_outliers, red_outliers, pink_outliers, orange_outliers, green_outliers
        
        
def plot_man_ratios(df_manminutes):
    """
    Function for interpreting man-minutes on the mold as an effective number
    of people. For example, 3 people may have helped during a given cycle.
    Operator 1 worked for the full cycle time, Operator 2 worked for the full
    cycle time, and Operator 3 worked for half the cycle time. The effective
    number of people for that cycle would be 2.5. This type of analysis should
    be tempered by how well operators accurately punch in and out of the molds.

    Parameters
    ----------
    df_manminutes : Pandas DataFrame
        DataFrame essentially the same as df_eval, but with Man-Minutes and 
        Man Ratio columns added in.

    Returns
    -------
    m : float
        Slope value of the linear best-fit line to the scatterplot of man ratio
        and cycle time.
    b : float
        Offset value of the linear best-fit line to the scatterplot of man
        ratio and cycle time.

    """
    mpl.rcParams['figure.dpi'] = 300
    man_minutes = list(df_manminutes["Man-Minutes"])
    man_ratios = list(df_manminutes["Man Ratio"])
    cycle_times= list(df_manminutes["Cycle Time"])
    
    reject_inds = []
    for i in range(len(man_minutes)):
        if man_minutes[i] == 0.0 or man_ratios[i] > 4 or man_ratios[i] < 1:
            reject_inds.append(i)
            
    man_minutes = [i for j,i in enumerate(man_minutes) if j not in reject_inds]
    man_ratios = [i for j,i in enumerate(man_ratios) if j not in reject_inds]
    cycle_times = [i for j,i in enumerate(cycle_times) if j not in reject_inds]
    
    m, b = np.polyfit(man_ratios, cycle_times, 1)
    x = np.asarray(man_ratios)
    
    plt.scatter(man_ratios, cycle_times)
    plt.plot(x, m*x+b, 'r')
    plt.title("Effectiveness of N operators on Mold")
    plt.xlabel("Synthetic number of people on mold")
    plt.ylabel("Cycle Times (min)")
    plt.show()
    return m, b


if __name__ == "__main__":
    dtstart = dt.datetime(2022,2,21,0,0,0)
    enddate = dt.date.today()
    # enddate = dt.date(2022,3,17)
    endtime = dt.time(23,59,59)
    dtend = dt.datetime.combine(enddate, endtime)

    # ndays = 21
    # enddate = dt.date.today()
    # endtime = dt.time(23,59,59)
    # dtend = dt.datetime.combine(enddate, endtime)
    # startdate = dt.date.today()
    # starttime = dt.time(0,0,0)
    # dtstart = dt.datetime.combine(startdate, starttime)
    
    # for i in range(0,ndays):
    #     df_eval, df_manminutes = load_operator_data(dtstart, dtend)
    
    #     m, b = plot_man_ratios(df_manminutes)
    #     print("m = {} for {} days".format(m, i+1))
    #     print("b = {} for {} days".format(b, i+1))
    #     print("")
        
    #     # Adjust start date
    #     startdate -= dt.timedelta(days=1)
    #     dtstart = dt.datetime.combine(startdate, starttime)
    
    # all_outliers, brown_outliers, purple_outliers, red_outliers, pink_outliers, orange_outliers, green_outliers = filter_outlier_cycles(dtstart, dtend)
    
    # cycles, medians, dates = cycle_time_over_time(dtstart, dtend)
    

    
    operator_list = [666]
    # shift = None
    # # get_operator_stats_by_list(df_eval, operator_list, shift=None)
    
    df_eval, df_manminutes = load_operator_data(dtstart, dtend)
    get_operator_stats_by_list(df_eval, operator_list)
    # get_all_operator_stats(df_eval)
    
    # opnum = 69
    # get_single_operator_stats(df_eval, opnum)
    
    # df_eval = get_operator_report_by_list(operator_list, shift, dtstart, dtend)