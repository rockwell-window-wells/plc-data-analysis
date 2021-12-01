"""resin_waste.py: Take a .csv file from StrideLinx and output useful charts
that show resin waste indications, breaking it down over time, by product, by
shift, etc.

"""

# import the necessary packages
# import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import datetime as dt
import seaborn as sns


file = "tan-resin-tank_test_data.csv"   # test data in working folder
# file = "gray-resin-tank_test_data.csv"
# Create a DataFrame from the csv file
df = pd.read_csv(file)

color = str()

print(df.head())
# Rename columns to make them easier to work with
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

# print(df.head())

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
# print(shifts)

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
for ind in df.index:
    num = int(df["1st_Part_Number"][ind])
    if num == 664436:
        df.loc[ind,"Product"] = "Rockwell 36"
    elif num == 664448:
        df.loc[ind,"Product"] = "Rockwell 48"
    elif num == 664460:
        df.loc[ind,"Product"] = "Rockwell 60"
    elif num == 664472:
        df.loc[ind,"Product"] = "Rockwell 72"
    elif num == 664484:
        df.loc[ind,"Product"] = "Rockwell 84"
    elif num == 664496:
        df.loc[ind,"Product"] = "Rockwell 96"
    elif num == 422324:
        df.loc[ind,"Product"] = "Cascade 24"
    elif num == 422336:
        df.loc[ind,"Product"] = "Cascade 36"
    elif num == 1111:
        df.loc[ind,"Product"] = "Additional Resin"
    else:
        print("ERROR: PRODUCT NUMBER NOT RECOGNIZED")

df = df.sort_values(by="Product")

##### PLOTS #####
# Excess resin by product
plt.figure(1)
sns.set_theme(style="whitegrid")
ax1 = sns.boxplot(x="Product", y="Excess_Resin_Weight", data=df)
ax1 = sns.swarmplot(x="Product", y="Excess_Resin_Weight", data=df, color=".25")
titlestring = color + " Excess Resin Across All Products"
yaxisstring = "Excess Resin Weight (lbs)"
ax1.set(title=titlestring)
ax1.set(ylabel=yaxisstring)

# Excess resin by Rockwell line only
plt.figure(2)
sns.set_theme(style="whitegrid")
ax2 = sns.boxplot(x="Product", y="Excess_Resin_Weight", data=df,
                  order=["Rockwell 36", "Rockwell 48",
                        "Rockwell 60", "Rockwell 72",
                        "Rockwell 84", "Rockwell 96",
                        "Additional Resin"])
ax2 = sns.swarmplot(x="Product", y="Excess_Resin_Weight", data=df,
                    order=["Rockwell 36", "Rockwell 48",
                          "Rockwell 60", "Rockwell 72",
                          "Rockwell 84", "Rockwell 96",
                          "Additional Resin"],color=".25")
titlestring = color + " Excess Resin Across Rockwell Products"
yaxisstring = "Excess Resin Weight (lbs)"
ax2.set(title=titlestring)
ax2.set(ylabel=yaxisstring)

# ax1 = sns.boxplot(x="Product", y="Excess_Resin_Weight", data=df,
#                   order=["Rockwell 48", "Rockwell 60",
#                         "Rockwell 72", "Rockwell 84",
#                         "Additional Resin"])

# Excess resin by shift
plt.figure(3)
sns.set_theme(style="whitegrid")
ax3 = sns.boxplot(x="Shift", y="Excess_Resin_Weight", data=df,
                  order=["Day", "Swing", "Night"])
ax3 = sns.swarmplot(x="Shift", y="Excess_Resin_Weight", data=df,
                  order=["Day", "Swing", "Night"], color=".25")
titlestring = color + " Excess Resin by Shift"
yaxisstring = "Excess Resin Weight (lbs)"
ax3.set(title=titlestring)
ax3.set(ylabel=yaxisstring)

plt.figure(4)
sns.set_theme(style="whitegrid")
ax4 = sns.boxplot(x="Shift", y="Excess_Resin_Weight", data=df,
                  order=["Day", "Swing", "Night"],hue="Product")
# ax2 = sns.swarmplot(x="Shift", y="Excess_Resin_Weight", data=df,
#                  order=["Day", "Swing", "Night"], color=".25")
titlestring = color + " Excess Resin by Shift and Product"
yaxisstring = "Excess Resin Weight (lbs)"
ax4.set(title=titlestring)
ax4.set(ylabel=yaxisstring)
ax4.legend(bbox_to_anchor=(1.0,1.0))

plt.show()


# This works for taking exact file location as a command line argument
# def main():
#     # construct the argument parser and parse the arguments
#     ap = argparse.ArgumentParser()
#     ap.add_argument("-f", "--file", type=str, required=True,
#         help="path to csv file")
#     args = vars(ap.parse_args())

#     # create a DataFrame from the csv file
#     df = pd.read_csv(args["file"])
#     print(df.head())
#     print(df.info())


# if __name__ = "__main__":
    # main()