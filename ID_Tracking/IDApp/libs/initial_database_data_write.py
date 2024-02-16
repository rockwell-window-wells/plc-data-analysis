# -*- coding: utf-8 -*-
"""
Writes the initial database from an Excel file.

Created on Sat Dec 30 10:41:04 2023

@author: Ryan Larson
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, DateTime, Sequence, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date
import pandas as pd
import numpy as np
from cycle_time_methods_v2 import load_raw_data_single_mold_all_data

Base = declarative_base()

class Bag(Base):
    __tablename__ = 'bags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bag_id = Column(Integer)
    # moldbay_id = Column(Integer, ForeignKey('moldbays.moldbay_id'))
    date_created = Column(DateTime, default=datetime.utcnow)
    date_repair1 = Column(DateTime, default=None)
    date_repair2 = Column(DateTime, default=None)
    date_repair3 = Column(DateTime, default=None)
    date_trashed = Column(DateTime, default=None)
    cycles = Column(Integer, default=0)
    # moldbay = relationship('Moldbay', uselist=False)
    
class Moldbay(Base):
    __tablename__ = 'moldbays'
    
    moldbay_id = Column(Integer, primary_key=True)
    moldbay_name = Column(String)
    # purple_id = Column(Integer, ForeignKey('purples.id'), unique=True)
    # lead_id = Column(Integer, ForeignKey('employees.id'), unique=True, nullable=True)
    # bag_id = Column(Integer, ForeignKey('bags.id'), unique=True)
    purple_id = Column(Integer, ForeignKey('purples.id'), nullable=True)
    lead_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    bag_id = Column(Integer, ForeignKey('bags.id'), nullable=True)
    
    UniqueConstraint(purple_id, name='unique_purple_ids')
    UniqueConstraint(lead_id, name='unique_lead_ids')
    UniqueConstraint(bag_id, name='unique_bag_ids')
    
    # purple = relationship('Purple', foreign_keys=[purple_id])
    # lead = relationship('Employee', foreign_keys=[lead_id])
    # bag = relationship('Bag', foreign_keys=[bag_id])
    
class Purple(Base):
    __tablename__ = 'purples'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    purple_id = Column(Integer)
    # moldbay_id = Column(Integer, ForeignKey('moldbays.moldbay_id'))
    date_created = Column(DateTime, default=datetime.now())
    date_trashed = Column(DateTime, default=None)
    repairs = Column(Integer, default=0)
    cycles = Column(Integer, default=0)

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer)
    lead_id = Column(Integer)
    rockwell_id = Column(Integer)
    historical_id = Column(Integer)
    name = Column(String)
    name_short = Column(String)
    start_date = Column(DateTime, default=None)
    end_date = Column(DateTime, default=None)
    # shift = Column(String)
    # shifts = relationship('ShiftHistory', back_populates='employee')
    # shift_start_date = Column(DateTime, default=None)
    # historical_shift = Column(String)
    # historical_shift_start_date = Column(DateTime, default=None)
    
# class ShiftHistory(Base):
#     __tablename__ = 'shift_history'
    
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     employee_id = Column(Integer, ForeignKey('employees.employee_id'))
#     shift = Column(String)
#     shift_start_date = Column(DateTime, default=datetime.utcnow)
#     # employee = relationship('Employee')
    
class BrownMoldRaw(Base):
    __tablename__ = 'brown_mold_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)
    leak_time = Column(Float, default=None)
    leak_count = Column(Integer, default=None)
    parts_count = Column(Integer, default=None)
    weekly_count = Column(Integer, default=None)
    monthly_count = Column(Integer, default=None)
    trash_count = Column(Integer, default=None)
    lead = Column(Integer, default=None)
    assistant_1 = Column(Integer, default=None)
    assistant_2 = Column(Integer, default=None)
    assistant_3 = Column(Integer, default=None)
    bag = Column(Integer, default=None)
    bag_days = Column(Integer, default=None)
    bag_cycles = Column(Integer, default=None)
    
class GreenMoldRaw(Base):
    __tablename__ = 'green_mold_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)
    leak_time = Column(Float, default=None)
    leak_count = Column(Integer, default=None)
    parts_count = Column(Integer, default=None)
    weekly_count = Column(Integer, default=None)
    monthly_count = Column(Integer, default=None)
    trash_count = Column(Integer, default=None)
    lead = Column(Integer, default=None)
    assistant_1 = Column(Integer, default=None)
    assistant_2 = Column(Integer, default=None)
    assistant_3 = Column(Integer, default=None)
    bag = Column(Integer, default=None)
    bag_days = Column(Integer, default=None)
    bag_cycles = Column(Integer, default=None)
    
class OrangeMoldRaw(Base):
    __tablename__ = 'orange_mold_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)
    leak_time = Column(Float, default=None)
    leak_count = Column(Integer, default=None)
    parts_count = Column(Integer, default=None)
    weekly_count = Column(Integer, default=None)
    monthly_count = Column(Integer, default=None)
    trash_count = Column(Integer, default=None)
    lead = Column(Integer, default=None)
    assistant_1 = Column(Integer, default=None)
    assistant_2 = Column(Integer, default=None)
    assistant_3 = Column(Integer, default=None)
    bag = Column(Integer, default=None)
    bag_days = Column(Integer, default=None)
    bag_cycles = Column(Integer, default=None)
    
class PinkMoldRaw(Base):
    __tablename__ = 'pink_mold_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)
    leak_time = Column(Float, default=None)
    leak_count = Column(Integer, default=None)
    parts_count = Column(Integer, default=None)
    weekly_count = Column(Integer, default=None)
    monthly_count = Column(Integer, default=None)
    trash_count = Column(Integer, default=None)
    lead = Column(Integer, default=None)
    assistant_1 = Column(Integer, default=None)
    assistant_2 = Column(Integer, default=None)
    assistant_3 = Column(Integer, default=None)
    bag = Column(Integer, default=None)
    bag_days = Column(Integer, default=None)
    bag_cycles = Column(Integer, default=None)
    
class PurpleMoldRaw(Base):
    __tablename__ = 'purple_mold_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)
    leak_time = Column(Float, default=None)
    leak_count = Column(Integer, default=None)
    parts_count = Column(Integer, default=None)
    weekly_count = Column(Integer, default=None)
    monthly_count = Column(Integer, default=None)
    trash_count = Column(Integer, default=None)
    lead = Column(Integer, default=None)
    assistant_1 = Column(Integer, default=None)
    assistant_2 = Column(Integer, default=None)
    assistant_3 = Column(Integer, default=None)
    bag = Column(Integer, default=None)
    bag_days = Column(Integer, default=None)
    bag_cycles = Column(Integer, default=None)
    
class RedMoldRaw(Base):
    __tablename__ = 'red_mold_raw'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)
    leak_time = Column(Float, default=None)
    leak_count = Column(Integer, default=None)
    parts_count = Column(Integer, default=None)
    weekly_count = Column(Integer, default=None)
    monthly_count = Column(Integer, default=None)
    trash_count = Column(Integer, default=None)
    lead = Column(Integer, default=None)
    assistant_1 = Column(Integer, default=None)
    assistant_2 = Column(Integer, default=None)
    assistant_3 = Column(Integer, default=None)
    bag = Column(Integer, default=None)
    bag_days = Column(Integer, default=None)
    bag_cycles = Column(Integer, default=None)
    
class BrownMoldCycles(Base):
    __tablename__ = 'brown_mold_cycles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)

class GreenMoldCycles(Base):
    __tablename__ = 'green_mold_cycles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)

class OrangeMoldCycles(Base):
    __tablename__ = 'orange_mold_cycles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)

class PinkMoldCycles(Base):
    __tablename__ = 'pink_mold_cycles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)

class PurpleMoldCycles(Base):
    __tablename__ = 'purple_mold_cycles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)

class RedMoldCycles(Base):
    __tablename__ = 'red_mold_cycles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=None)
    layup_time = Column(Float, default=None)
    close_time = Column(Float, default=None)
    resin_time = Column(Float, default=None)
    cycle_time = Column(Float, default=None)

# Get Excel file that contains bag data
# file = "Z:/Producftion/ID_Tracking/ID_numbers/id_data_seed_Jan2024.xlsx"
employees_csv = "Z:/Production/ID_Tracking/ID_numbers/employees.csv"
shifthistory_csv = "Z:/Production/ID_Tracking/ID_numbers/shifthistory.csv"
bags_csv = "Z:/Production/ID_Tracking/ID_numbers/bags.csv"
purples_csv = "Z:/Production/ID_Tracking/ID_numbers/purples.csv"
moldbays_csv = "Z:/Production/ID_Tracking/ID_numbers/moldbays.csv"
    
df_employees = pd.read_csv(employees_csv)
df_employees['start_date'] = pd.to_datetime(df_employees['start_date'], format='%m/%d/%Y')
df_employees['end_date'] = pd.to_datetime(df_employees['end_date'], format='%m/%d/%Y')
# df_employees['shift_start_date'] = pd.to_datetime(df_employees['shift_start_date'], format='%m/%d/%Y')
# df_employees['historical_shift_start_date'] = pd.to_datetime(df_employees['historical_shift_start_date'], format='%m/%d/%Y')

df_shifthistory = pd.read_csv(shifthistory_csv)
df_shifthistory['shift_start_date'] = pd.to_datetime(df_shifthistory['shift_start_date'], format='%m/%d/%Y')

df_bags = pd.read_csv(bags_csv)
df_bags['date_created'] = pd.to_datetime(df_bags['date_created'], format='%m/%d/%Y')
df_bags['date_repair1'] = pd.to_datetime(df_bags['date_repair1'], format='%m/%d/%Y')
df_bags['date_repair2'] = pd.to_datetime(df_bags['date_repair2'], format='%m/%d/%Y')
df_bags['date_repair3'] = pd.to_datetime(df_bags['date_repair3'], format='%m/%d/%Y')
df_bags['date_trashed'] = pd.to_datetime(df_bags['date_trashed'], format='%m/%d/%Y')
df_bags['date_repair1'].fillna(0)

df_purples = pd.read_csv(purples_csv)
df_purples['date_created'] = pd.to_datetime(df_purples['date_created'], format='%m/%d/%Y')
df_purples['date_trashed'] = pd.to_datetime(df_purples['date_trashed'], format='%m/%d/%Y')

df_moldbays = pd.read_csv(moldbays_csv)

# Get historical cycle time data, up through December 31st 2023
dtstart = datetime(2020,1,1,0,0,0)
dtend = datetime(2023,12,31,23,59,59)
dtstart = dtstart.strftime("%Y-%m-%dT%H:%M:%SZ")
dtend = dtend.strftime("%Y-%m-%dT%H:%M:%SZ")

def rename_stridelinx_columns(df):
    df = df.rename(columns={'Layup Time': 'layup_time',
                            'Close Time': 'close_time',
                            'Resin Time': 'resin_time',
                            'Cycle Time': 'cycle_time',
                            'Leak Time': 'leak_time',
                            'Leak Count': 'leak_count',
                            'Parts Count': 'parts_count',
                            'Weekly Count': 'weekly_count',
                            'Monthly Count': 'monthly_count',
                            'Trash Count': 'trash_count',
                            'Lead': 'lead',
                            'Assistant 1': 'assistant_1',
                            'Assistant 2': 'assistant_2',
                            'Assistant 3': 'assistant_3',
                            'Bag': 'bag',
                            'Bag Days': 'bag_days',
                            'Bag Cycles': 'bag_cycles'
                            })
    return df

df_brown = load_raw_data_single_mold_all_data(dtstart, dtend, "Brown")
df_brown = rename_stridelinx_columns(df_brown)
df_brown = df_brown.reindex(index=df_brown.index[::-1]) # Reverse the index so new entries will be added in the correct position
df_brown = df_brown.reset_index(drop=True)

df_green = load_raw_data_single_mold_all_data(dtstart, dtend, "Green")
df_green = rename_stridelinx_columns(df_green)
df_green = df_green.reindex(index=df_green.index[::-1]) # Reverse the index so new entries will be added in the correct position
df_green = df_green.reset_index(drop=True)

df_orange = load_raw_data_single_mold_all_data(dtstart, dtend, "Orange")
df_orange = rename_stridelinx_columns(df_orange)
df_orange = df_orange.reindex(index=df_orange.index[::-1]) # Reverse the index so new entries will be added in the correct position
df_orange = df_orange.reset_index(drop=True)

df_pink = load_raw_data_single_mold_all_data(dtstart, dtend, "Pink")
df_pink = rename_stridelinx_columns(df_pink)
df_pink = df_pink.reindex(index=df_brown.index[::-1]) # Reverse the index so new entries will be added in the correct position
df_pink = df_pink.reset_index(drop=True)

df_purple = load_raw_data_single_mold_all_data(dtstart, dtend, "Purple")
df_purple = rename_stridelinx_columns(df_purple)
df_purple = df_purple.reindex(index=df_purple.index[::-1]) # Reverse the index so new entries will be added in the correct position
df_purple = df_purple.reset_index(drop=True)

df_red = load_raw_data_single_mold_all_data(dtstart, dtend, "Red")
df_red = rename_stridelinx_columns(df_red)
df_red = df_red.reindex(index=df_red.index[::-1]) # Reverse the index so new entries will be added in the correct position
df_red = df_red.reset_index(drop=True)




# Establishing the database connection
db_name = "Z:/Production/ID_Tracking/ID_numbers/PLC_ID_database.db"
db_str = "sqlite:///" + db_name
engine = create_engine(db_str, echo=False)

# ...

# Creating a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

try:
    Base.metadata.create_all(engine)
    
    # moldbay_data = {
    #     'moldbay_id': [1,2,3,4,5,6],
    #     'moldbay_name': ['Brown','Pink','Purple','Orange','Red','Green'],
    #     'lead': [None, None, None, None, None, None],
    #     'purple': [None, None, None, None, None, None],
    #     'bag': [None, None, None, None, None, None],
    #     }
    
    # moldbay_df = pd.DataFrame(moldbay_data)
        
    for index, row in df_employees.iterrows():
        session.add(Employee(employee_id=row['employee_id'],
                             lead_id=row['lead_id'],
                             rockwell_id=row['rockwell_id'],
                             historical_id=row['historical_id'],
                             name=row['name'],
                             name_short=row['name_short'],
                             start_date=row['start_date']))
        
    # for index, row in df_shifthistory.iterrows():
    #     session.add(ShiftHistory(employee_id=row['employee_id'],
    #                              shift=row['shift'],
    #                              shift_start_date=row['shift_start_date']))
    
    for index, row in df_bags.iterrows():
        session.add(Bag(bag_id=row['bag_id'],
                        # moldbay_id=row['moldbay_id'],
                        date_created=row['date_created'],
                        cycles=row['cycles']))
        
    for index, row in df_purples.iterrows():
        session.add(Purple(purple_id=row['purple_id'],
                           # moldbay_id=row['moldbay_id'],
                           date_created=row['date_created'],
                           repairs=row['repairs'],
                           cycles=row['cycles']))
        
    for index, row in df_moldbays.iterrows():
        session.add(Moldbay(moldbay_id=row['moldbay_id'],
                            moldbay_name=row['moldbay_name'],
                            purple_id=row['purple_id'],
                            lead_id=row['lead_id'],
                            bag_id=row['bag_id']))
        
    for index, row in df_brown.iterrows():
        session.add(BrownMoldRaw(time=row['time'],
                                 layup_time=row['layup_time'],
                                 close_time=row['close_time'],
                                 resin_time=row['resin_time'],
                                 cycle_time=row['cycle_time'],
                                 leak_time=row['leak_time'],
                                 leak_count=row['leak_count'],
                                 parts_count=row['parts_count'],
                                 weekly_count=row['weekly_count'],
                                 monthly_count=row['monthly_count'],
                                 trash_count=row['trash_count'],
                                 lead=row['lead'],
                                 assistant_1=row['assistant_1'],
                                 assistant_2=row['assistant_2'],
                                 assistant_3=row['assistant_3'],
                                 bag=row['bag'],
                                 bag_days=row['bag_days'],
                                 bag_cycles=row['bag_cycles']))
        
    for index, row in df_green.iterrows():
        session.add(GreenMoldRaw(time=row['time'],
                                 layup_time=row['layup_time'],
                                 close_time=row['close_time'],
                                 resin_time=row['resin_time'],
                                 cycle_time=row['cycle_time'],
                                 leak_time=row['leak_time'],
                                 leak_count=row['leak_count'],
                                 parts_count=row['parts_count'],
                                 weekly_count=row['weekly_count'],
                                 monthly_count=row['monthly_count'],
                                 trash_count=row['trash_count'],
                                 lead=row['lead'],
                                 assistant_1=row['assistant_1'],
                                 assistant_2=row['assistant_2'],
                                 assistant_3=row['assistant_3'],
                                 bag=row['bag'],
                                 bag_days=row['bag_days'],
                                 bag_cycles=row['bag_cycles']))
        
    for index, row in df_orange.iterrows():
        session.add(OrangeMoldRaw(time=row['time'],
                                 layup_time=row['layup_time'],
                                 close_time=row['close_time'],
                                 resin_time=row['resin_time'],
                                 cycle_time=row['cycle_time'],
                                 leak_time=row['leak_time'],
                                 leak_count=row['leak_count'],
                                 parts_count=row['parts_count'],
                                 weekly_count=row['weekly_count'],
                                 monthly_count=row['monthly_count'],
                                 trash_count=row['trash_count'],
                                 lead=row['lead'],
                                 assistant_1=row['assistant_1'],
                                 assistant_2=row['assistant_2'],
                                 assistant_3=row['assistant_3'],
                                 bag=row['bag'],
                                 bag_days=row['bag_days'],
                                 bag_cycles=row['bag_cycles']))
        
    for index, row in df_pink.iterrows():
        session.add(PinkMoldRaw(time=row['time'],
                                 layup_time=row['layup_time'],
                                 close_time=row['close_time'],
                                 resin_time=row['resin_time'],
                                 cycle_time=row['cycle_time'],
                                 leak_time=row['leak_time'],
                                 leak_count=row['leak_count'],
                                 parts_count=row['parts_count'],
                                 weekly_count=row['weekly_count'],
                                 monthly_count=row['monthly_count'],
                                 trash_count=row['trash_count'],
                                 lead=row['lead'],
                                 assistant_1=row['assistant_1'],
                                 assistant_2=row['assistant_2'],
                                 assistant_3=row['assistant_3'],
                                 bag=row['bag'],
                                 bag_days=row['bag_days'],
                                 bag_cycles=row['bag_cycles']))
        
    for index, row in df_purple.iterrows():
        session.add(PurpleMoldRaw(time=row['time'],
                                 layup_time=row['layup_time'],
                                 close_time=row['close_time'],
                                 resin_time=row['resin_time'],
                                 cycle_time=row['cycle_time'],
                                 leak_time=row['leak_time'],
                                 leak_count=row['leak_count'],
                                 parts_count=row['parts_count'],
                                 weekly_count=row['weekly_count'],
                                 monthly_count=row['monthly_count'],
                                 trash_count=row['trash_count'],
                                 lead=row['lead'],
                                 assistant_1=row['assistant_1'],
                                 assistant_2=row['assistant_2'],
                                 assistant_3=row['assistant_3'],
                                 bag=row['bag'],
                                 bag_days=row['bag_days'],
                                 bag_cycles=row['bag_cycles']))
        
    for index, row in df_red.iterrows():
        session.add(RedMoldRaw(time=row['time'],
                                 layup_time=row['layup_time'],
                                 close_time=row['close_time'],
                                 resin_time=row['resin_time'],
                                 cycle_time=row['cycle_time'],
                                 leak_time=row['leak_time'],
                                 leak_count=row['leak_count'],
                                 parts_count=row['parts_count'],
                                 weekly_count=row['weekly_count'],
                                 monthly_count=row['monthly_count'],
                                 trash_count=row['trash_count'],
                                 lead=row['lead'],
                                 assistant_1=row['assistant_1'],
                                 assistant_2=row['assistant_2'],
                                 assistant_3=row['assistant_3'],
                                 bag=row['bag'],
                                 bag_days=row['bag_days'],
                                 bag_cycles=row['bag_cycles']))
    # df_employees.to_sql('employees', con=engine, if_exists='replace', index=False)
    # df_bags.to_sql('bags', con=engine, if_exists='replace', index=False)
    # df_purples.to_sql('purples', con=engine, if_exists='replace', index=False)
    # df_moldbays.to_sql('moldbays', con=engine, if_exists='replace', index=False)
    
    
    # # Adding data from DataFrame to the "purples" table
    # bag_df.to_sql('bags', con=engine, if_exists='replace', index=False)
    
    session.commit()
    
except Exception as e:
    print(f"An error occurred: {e}")
    session.rollback()
    
finally:
    session.close()
    engine.dispose()