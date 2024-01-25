# -*- coding: utf-8 -*-
"""
Writes the initial database from an Excel file.

Created on Sat Dec 30 10:41:04 2023

@author: Ryan Larson
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Sequence, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import pandas as pd
import numpy as np

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
    
    purple = relationship('Purple', foreign_keys=[purple_id])
    lead = relationship('Employee', foreign_keys=[lead_id])
    bag = relationship('Bag', foreign_keys=[bag_id])
    
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
    
class ShiftHistory(Base):
    __tablename__ = 'shift_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'))
    shift = Column(String)
    shift_start_date = Column(DateTime, default=datetime.utcnow)
    employee = relationship('Employee')

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
        
    for index, row in df_shifthistory.iterrows():
        session.add(ShiftHistory(employee_id=row['employee_id'],
                                 shift=row['shift'],
                                 shift_start_date=row['shift_start_date']))
    
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