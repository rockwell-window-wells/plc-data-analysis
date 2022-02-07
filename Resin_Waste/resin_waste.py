"""resin_waste.py: Take a .csv file from StrideLinx and output useful charts
that show resin waste indications, breaking it down over time, by product, by
shift, etc.

NOTE: MAKES NO ASSUMPTIONS ABOUT TIME PERIOD OF DATA INPUT. IF YOU WANT PLOTS
      OR STATISTICS ABOUT A SPECIFIC WEEK, FEED THIS SCRIPT DATA ONLY FROM THAT
      WEEK.

"""

# import the necessary packages
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import datetime as dt
import seaborn as sns
import matplotlib.ticker as mtick

def perdelta(start, end, delta):
    """Given a start datetime, end datetime, and delta time, generate the
    new datetime for putting in a list.
    """
    curr = start
    while curr < end:
        yield curr
        curr += delta

# This works for taking exact file location as a command line argument
def main():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--input", type=str, required=True,
        help="path to csv file")
    ap.add_argument("-o", "--output", type=str, required=False,
        help="path to output Excel file")
    ap.add_argument("-s", "--showcharts", type=bool, required=False,
        help="enter False to turn off charts, otherwise plotting will occur")
    args = vars(ap.parse_args())

    # create a DataFrame from the csv file
    df = pd.read_csv(args["input"])

    # Rename columns to make them easier to work with
    color = str()
    for col in df.columns:
        if "Tan" in col:
            color = "Tan"
        elif "Gray" in col:
            color = "Gray"
        old = col
        if col == "time":
            col = col.replace("time","Datetime")
        col = col.replace(" ","_")
        col = col.replace("_","",1)
        col = col.replace("-","")
        col = col.replace("Tan_","")
        col = col.replace("Gray_","")
        df = df.rename(columns={old:col})

    # Set percent pigment and percent catalyst values based on color
    if color == "Tan":
        pct_pig = 0.0186
        pct_cat = 0.018
    elif color == "Gray":
        pct_pig = 0.0265
        pct_cat = 0.018
    else:
        print("ERROR: Color not recognized")

    # Separate date and time and convert to datetime.date and datetime.time
    df["Date"] = ""
    df["Time"] = ""
    for ind in df.index:
        d = df["Datetime"][ind]
        d = d.replace("-"," ")
        d = d.replace(":"," ")
        d = d.replace("."," ")
        d = dt.datetime.strptime(d,"%Y %m %d %H %M %S %f")
        df.loc[ind,"Date"] = d.date()
        df.loc[ind,"Time"] = d.time()

    # Create shifts DataFrame
    daystart = dt.time(6,0,0)
    dayend = dt.time(14,0,0)
    swingstart = dayend
    swingend = dt.time(22,0,0)
    nightstart = swingend
    nightend = daystart

    shifttimes = {"Shift": ["Day", "Swing", "Night"],
              "Start": [daystart, swingstart, nightstart],
              "End": [dayend, swingend, nightend]}

    shifts = pd.DataFrame(shifttimes)
    shifts = shifts.set_index("Shift")

    # Create shifts column to determine what measurements belong to which shift
    df["Shift"] = ""
    for ind in df.index:
        time = df["Time"][ind]
        if time > shifts.loc["Day","Start"] and time < shifts.loc["Day","End"]:
            df.loc[ind,"Shift"] = "Day"
        elif time > shifts.loc["Swing","Start"] and time < shifts.loc["Swing","End"]:
            df.loc[ind,"Shift"] = "Swing"
        elif time > shifts.loc["Night","Start"] or time < shifts.loc["Night","End"]:
            df.loc[ind,"Shift"] = "Night"
        else:
            print("ERROR: TIME IS ON A SHIFT CHANGE")


    # Create Product column to determine name of product
    df["Product"] = ""
    df["Excess_Resin_Percentage"] = ""
    wtgt = 1.0  # Target weight for the product
    for ind in df.index:
        num = int(df["1st_Part_Number"][ind])
        if num == 664436:
            df.loc[ind,"Product"] = "Elite 36"
            wtgt = 33.2
        elif num == 664448:
            df.loc[ind,"Product"] = "Elite 48"
            wtgt = 38.7
        elif num == 664460:
            df.loc[ind,"Product"] = "Elite 60"
            wtgt = 44.2
        elif num == 664472:
            df.loc[ind,"Product"] = "Elite 72"
            wtgt = 51.9
        elif num == 664484:
            df.loc[ind,"Product"] = "Elite 84"
            wtgt = 60.2
        elif num == 664496:
            df.loc[ind,"Product"] = "Elite 96"
            wtgt = 70.7
        elif num == 6644102:
            df.loc[ind,"Product"] = "Elite 102"
            wtgt = 80.9
        elif num == 422324:
            df.loc[ind,"Product"] = "Cascade 24"
            wtgt = 7.8
        elif num == 422336:
            df.loc[ind,"Product"] = "Cascade 36"
            wtgt = 12.2
        elif num == 422348:
            df.loc[ind,"Product"] = "Cascade 48"
            wtgt = 17.6
        elif num == 1111:
            df.loc[ind,"Product"] = "Additional Resin"
            wtgt = float("NaN") # This will force NaN value for percentage on additional resin
        else:
            print("ERROR: PRODUCT NUMBER NOT RECOGNIZED")

        wtgt = wtgt*(1 - pct_pig - pct_cat)     # Adjust nominal weight to only include resin weight
        df.loc[ind,"Excess_Resin_Percentage"] = 100.0*(df.loc[ind,"Excess_Resin_Weight"]/wtgt)


    # Sort DataFrame by Product so charts come out nicely
    df = df.sort_values(by="Product")

    # Ordered list of strings based on what products are in the data
    products = pd.DataFrame({"PartNumber": [664436, 664448, 664460, 664472,
                                            664484, 664496, 6644102, 422324,
                                            422336, 422348, 1111],
                    "Product": ["Elite 36", "Elite 48", "Elite 60", "Elite 72",
                                "Elite 84", "Elite 96", "Elite 102", "Cascade 24",
                                "Cascade 36", "Cascade 48", "Additional Resin"]})
    products = products.sort_values(by="PartNumber")
    hue_order = []
    for ind in products.index:
        current_product = products.loc[ind,"Product"]
        if df["Product"].str.contains(current_product).any():
            hue_order.append(current_product)

    #################### PLOTS ####################
    ### BOXPLOTS ###
    # Excess resin weight by product, all products
    plt.figure(1)
    sns.set_theme(style="whitegrid")
    ax1 = sns.boxplot(x="Product", y="Excess_Resin_Weight", data=df)
    # ax1 = sns.swarmplot(x="Product", y="Excess_Resin_Weight", data=df,color=".25")
    ax1 = sns.stripplot(x="Product", y="Excess_Resin_Weight", data=df, color=".25", jitter=0.25)
    titlestring = color + " Excess Resin, All Products: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Excess Resin Weight (lbs)"
    ax1.set(title=titlestring)
    ax1.set(ylabel=yaxisstring)
    ax1.set_xticklabels(ax1.get_xticklabels(),rotation=45)
    plt.subplots_adjust(right=0.925, bottom=0.175)

    print("\nStats for Excess Resin Weight by Product")
    wt_by_prdct_stats = df.groupby(["Product"])["Excess_Resin_Weight"].describe()
    print(wt_by_prdct_stats)

    # Excess resin percentage by product, all products
    plt.figure(2)
    sns.set_theme(style="whitegrid")
    ax2 = sns.boxplot(x="Product", y="Excess_Resin_Percentage", data=df)
    # ax2 = sns.swarmplot(x="Product", y="Excess_Resin_Percentage", data=df, color=".25")
    ax2 = sns.stripplot(x="Product", y="Excess_Resin_Percentage", data=df, color=".25", jitter=0.25)
    titlestring = color + " Excess Resin, All Products: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Excess Resin (%)"
    ax2.set(title=titlestring)
    ax2.set(ylabel=yaxisstring)
    fmt = '%.0f%%' # Format for the y ticks
    yticks = mtick.FormatStrFormatter(fmt)
    ax2.yaxis.set_major_formatter(yticks)
    ax2.set_xticklabels(ax2.get_xticklabels(),rotation=45)
    plt.subplots_adjust(right=0.925, bottom=0.175)

    print("\nStats for Excess Resin Percentage by Product")
    df_pct = df[["Product","Excess_Resin_Percentage"]]
    df_pct = df_pct.dropna()
    df_pct = df_pct.infer_objects()
    pct_by_prdct_stats = df_pct.groupby(["Product"])["Excess_Resin_Percentage"].describe()
    print(pct_by_prdct_stats)

    # Excess resin by Elite line only
    plt.figure(3)
    sns.set_theme(style="whitegrid")
    ax3 = sns.boxplot(x="Product", y="Excess_Resin_Weight", data=df,
                      order=["Elite 36", "Elite 48",
                            "Elite 60", "Elite 72",
                            "Elite 84", "Elite 96",
                            "Elite 102", "Additional Resin"])
    # ax3 = sns.swarmplot(x="Product", y="Excess_Resin_Weight", data=df,
    #                     order=["Elite 36", "Elite 48",
    #                           "Elite 60", "Elite 72",
    #                           "Elite 84", "Elite 96",
    #                           "Elite 102", "Additional Resin"],color=".25")
    ax3 = sns.stripplot(x="Product", y="Excess_Resin_Weight", data=df,
                        order=["Elite 36", "Elite 48",
                              "Elite 60", "Elite 72",
                              "Elite 84", "Elite 96",
                              "Elite 102", "Additional Resin"],color=".25",jitter=0.25)
    titlestring = color + " Excess Resin, Elite Only: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Excess Resin Weight (lbs)"
    ax3.set(title=titlestring)
    ax3.set(ylabel=yaxisstring)

    # Excess resin by shift
    plt.figure(4)
    sns.set_theme(style="whitegrid")
    ax4 = sns.boxplot(x="Shift", y="Excess_Resin_Weight", data=df,
                      order=["Day", "Swing", "Night"])
    # ax4 = sns.swarmplot(x="Shift", y="Excess_Resin_Weight", data=df,
    #                   order=["Day", "Swing", "Night"], color=".25")
    ax4 = sns.stripplot(x="Shift", y="Excess_Resin_Weight", data=df,
                      order=["Day", "Swing", "Night"], color=".25", jitter=0.15)
    titlestring = color + " Excess Resin by Shift: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Excess Resin Weight (lbs)"
    ax4.set(title=titlestring)
    ax4.set(ylabel=yaxisstring)

    print("\nStats for Excess Resin Weight by shift")
    wt_by_shift_stats = df.groupby(["Shift"])["Excess_Resin_Weight"].describe()
    print(wt_by_shift_stats)

    # Excess resin by shift and product together
    plt.figure(5)
    sns.set_theme(style="whitegrid")
    ax5 = sns.boxplot(x="Shift", y="Excess_Resin_Weight", data=df,
                      order=["Day", "Swing", "Night"],hue="Product",
                      hue_order=hue_order)
    titlestring = color + " Excess Resin by Shift and Product: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Excess Resin Weight (lbs)"
    ax5.set(title=titlestring)
    ax5.set(ylabel=yaxisstring)
    ax5.legend(bbox_to_anchor=(1.0,1.0))

    print("\nStats for Excess Resin Weight by shift")
    wt_by_shift_prdct_stats = df.groupby(["Shift","Product"])["Excess_Resin_Weight"].describe()
    wt_by_shift_prdct_stats = wt_by_shift_prdct_stats.sort_values(by="Product")
    print(wt_by_shift_prdct_stats)

    # Bar chart of average excess resin use by shift
    plt.figure(6)
    sns.set_theme(style="whitegrid")
    data = wt_by_shift_prdct_stats.reset_index()
    print("\nStats for Average Excess Resin Use by Shift")
    print(data)
    ax6 = sns.barplot(x="Shift", y="mean", data=data,
                    order=["Day", "Swing", "Night"],hue="Product",
                    hue_order=hue_order)
    titlestring = color + " Average Excess Resin: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Average Excess Resin per Part (lbs)"
    ax6.set(title=titlestring)
    ax6.set(ylabel=yaxisstring)
    ax6.legend(bbox_to_anchor=(1.0,1.0))

    # Bar chart of total excess resin use by shift
    daysum = 0.0
    swingsum = 0.0
    nightsum = 0.0

    for ind in df.index:
        shift = df["Shift"][ind]
        if shift == "Day":
            daysum += df["Excess_Resin_Weight"][ind]
        elif shift == "Swing":
            swingsum += df["Excess_Resin_Weight"][ind]
        elif shift == "Night":
            nightsum += df["Excess_Resin_Weight"][ind]
        else:
            print("ERROR: Shift not recognized")

    tot_wts = {"Shift": ["Day", "Swing", "Night"],
                "Total_Excess_Resin": [daysum, swingsum, nightsum]}

    plt.figure(7)
    sns.set_theme(style="whitegrid")
    ax7 = sns.barplot(x="Shift", y="Total_Excess_Resin", data=tot_wts,
                    order=["Day", "Swing", "Night"])
    titlestring = color + " Total Excess Resin: {} to {}".format(min(df.Date),max(df.Date))
    yaxisstring = "Total Excess Resin (lbs)"
    ax7.set(title=titlestring)
    ax7.set(ylabel=yaxisstring)


    ### TIME SERIES PLOTS ###
    # # Excess resin weight over time (not scaled by target weight)
    # df = df.sort_values(by="Datetime", ascending=False) # Resort data by time
    # plt.figure(8)
    # sns.set_theme(style="whitegrid")
    # # ax8 = sns.relplot(x="Datetime", y="Excess_Resin_Weight", kind="line", data=df)
    # ax8 = plt.plot(df["Datetime"],df["Excess_Resin_Weight"])
    #
    # # Calculations to make xticks easier to read
    # mindate = df["Date"][len(df)-1]
    # maxdate = df["Date"][0]
    # mintime = df["Time"][len(df)-1]
    # maxtime = df["Time"][0]
    # mindatetime = dt.datetime.combine(mindate, mintime)
    # maxdatetime = dt.datetime.combine(maxdate, maxtime)
    #
    # xticklabels = []
    # for ind in df.index:
    #     if ind == 0:
    #         xticklabels.append(df)
    #     if df.loc[ind,"Shift"] == "Day"









    #
    #
    # # Calculate the shift of the mintime
    # if mintime >= daystart and mintime < dayend:
    #     xtick_starttime = daystart
    # elif mintime >= swingstart and mintime < swingend:
    #     xtick_starttime = swingstart
    # else:
    #     xtick_starttime = nightstart
    #
    # xtick_start = dt.datetime.combine(mindate, xtick_starttime)
    # # print(xtick_start)
    #
    # # Calculate the shift of the maxtime
    # if maxtime >= daystart and maxtime < dayend:
    #     xtick_endtime = dayend
    # elif maxtime >= swingstart and maxtime < swingend:
    #     xtick_endtime = swingend
    # else:
    #     xtick_endtime = nightend
    #
    # xtick_end = dt.datetime.combine(maxdate, xtick_endtime)
    # # print(xtick_end)
    #
    # for result in perdelta(xtick_start, xtick_end, dt.timedelta(hours=8)):
    #     xticks.append(result)
    #     print(result)
    #
    # # print("\n",xticks)
    #
    #
    #
    #
    # ax8.set(xticklabels=xticklabels) # Figure out how to set this so the ticks only happen at the start of new days or shifts


    # Another way to look at the time series data could be to combine all
    # measurements for each shift by day, and plot as a line plot with variance
    # showing. This would show both shift patterns and time-variance patterns
    # (such as those potentially caused by seasonal temperature changes).



    if args["output"] is not None:
        outputfile = args["output"]
        print("Writing statistics to {}".format(outputfile))

        writer = pd.ExcelWriter(args["output"])
        # Write stats dataframes to different worksheets in Excel document
        wt_by_prdct_stats.to_excel(writer, sheet_name='Excess Resin Weight by Product')
        pct_by_prdct_stats.to_excel(writer, sheet_name='Excess Resin Percent by Product')
        wt_by_shift_stats.to_excel(writer, sheet_name='Excess Resin Weight by Shift')
        wt_by_shift_prdct_stats.to_excel(writer, sheet_name='Excess Resin Wt - Shft & Prd')

        # Close the Pandas Excel writer and output the Excel file
        writer.save()

    if args["showcharts"] is not None:
        print("\nCharts not displayed.\n")
    else:
        plt.show()



if __name__ == "__main__":
    main()
