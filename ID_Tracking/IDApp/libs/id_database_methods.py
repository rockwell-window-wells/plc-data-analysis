# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 12:31:24 2024

@author: Ryan.Larson
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, DateTime, Sequence, Boolean, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import api_config_vars as api
from sklearn.cluster import KMeans
import time
import random

##### File and class references #####
Base = declarative_base()
db_file = "Z:\Production\ID_Tracking\ID_numbers\PLC_ID_database.db"
db_str = "sqlite:///" + db_file

##### Table definitions #####
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


##### Methods #####
# Session access methods
def open_session(db_str):
    engine = create_engine(db_str, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session, engine

def close_session(session, engine):
    session.close()
    engine.dispose()
    

# Purple methods
def add_purple(db_str, purple_id, moldbay_id=None, date_created=datetime.now()):
    session, engine = open_session(db_str)
    try:
        new_purple = Purple(purple_id=purple_id,
                            # moldbay_id=moldbay_id,
                            date_created=date_created)
        session.add(new_purple)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
def move_purple_from_moldbay(db_str, purple_id, new_moldbay_id):
    session, engine = open_session(db_str)
    try:
        # Fetch purple row by purple_id
        purple_row = (
            session.query(Purple)
            .filter_by(purple_id=purple_id)
            .order_by(Purple.id.desc())
            .first()
        )
        if purple_row:
            purple_row.update({'moldbay_id': new_moldbay_id})
            session.commit()
            return True
        else:
            print(f"Purple with id {purple_id} not found.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
def update_purple_cycles(db_str, purple_id, new_cycles):
    """
    Update the number of cycles on a specific purple. new_cycles must be
    greater than the existing value in the cycles column.

    Parameters
    ----------
    db_str : TYPE
        DESCRIPTION.
    purple_id : int
        DESCRIPTION.
    new_cycles : int
        DESCRIPTION.

    Returns
    -------
    bool
        Success or failure of method.

    """
    session, engine = open_session(db_str)
    try:
        # Fetch purple row by purple_id (assumes you want the latest purple
        # with the chosen purple_id number, which is a good assumption since 
        # purple numbers cycle only every several years)
        purple_row = (
            session.query(Purple)
            .filter_by(purple_id=purple_id)
            .order_by(Purple.id.desc())
            .first()
        )
        if purple_row:
            if new_cycles > purple_row.cycles:
                purple_row.cycles = new_cycles
                session.commit()
                return True
            else:
                print(f"Failed to update purple {purple_row.purple_id} from {purple_row.cycles} to {new_cycles}.")
                return False
        else:
            print(f"No purple found with purple id {purple_id}.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
        
def increment_purple_cycles(db_str, purple_id, quantity):
    session, engine = open_session(db_str)
    try:
        purple_row = (
            session.query(Purple)
            .filter_by(purple_id=purple_id)
            .order_by(Purple.id.desc())
            .first()
        )
        if purple_row:
            purple_row.cycles += quantity
            session.commit()
            return True
        else:
            print(f"Failed to increment purple {purple_row.purple_id} cycles")
            return False
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_session(session, engine)
        
        
        
# Bag methods
def add_bag(db_str, bag_id, moldbay_id=None, date_created=datetime.now):
    session, engine = open_session(db_str)
    try:
        new_bag = Bag(bag_id=bag_id,
                      moldbay_id=moldbay_id,
                      date_created=date_created)
        session.add(new_bag)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
def move_bag_from_moldbay(db_str, bag_id, new_moldbay_id): # FIXME: Need to update this method to match new database schema
    session, engine = open_session(db_str)
    try:
        # Fetch bag row by bag_id
        bag_row = (
            session.query(Bag)
            .filter_by(bag_id=bag_id)
            .order_by(Bag.id.desc())
            .first()
        )
        if bag_row:
            bag_row.update({'moldbay_id': new_moldbay_id})
            session.commit()
            return True
        else:
            print(f"Bag with id {bag_id} not found.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
def update_bag_cycles(db_str, bag_id, new_cycles):
    session, engine = open_session(db_str)
    try:
        # Fetch bag row by bag_id
        bag_row = (
            session.query(Bag)
            .filter_by(bag_id=bag_id)
            .order_by(Bag.id.desc())
            .first()
        )
        if bag_row:
            if new_cycles > bag_row.cycles:
                bag_row.cycles = new_cycles
                session.commit()
                return True
            else:
                print(f"Failed to update bag {bag_row.bag_id} from {bag_row.cycles} to {new_cycles}.")
                return False
        else:
            print(f"No bag found with bag id {bag_id}.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
def increment_bag_cycles(db_str, bag_id, quantity):
    session, engine = open_session(db_str)
    try:
        bag_row = (
            session.query(Bag)
            .filter_by(bag_id=bag_id)
            .order_by(Bag.id.desc())
            .first()
        )
        if bag_row:
            bag_row.cycles += quantity
            session.commit()
            return True
        else:
            print(f"Failed to increment bag {bag_row.bag_id} cycles")
            return False
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_session(session, engine)

def get_latest_id_from_bag_id(db_str, bag_id):
    session, engine = open_session(db_str)
    try:
        bag_row = (
            session.query(Bag)
            .filter_by(bag_id=bag_id)
            .order_by(Bag.id.desc())
            .first()
        )
        id_num = bag_row.id
        return id_num
    except:
        return None
    finally:
        close_session(session, engine)


# Employee methods
def add_employee(db_str, employee_id, rockwell_id, name, name_short, start_date, shift):
    session, engine = open_session(db_str)
    try:
        lead_id = employee_id + 10000
        new_employee = Employee(employee_id=employee_id,
                                lead_id=lead_id,
                                rockwell_id=rockwell_id,
                                historical_id=None,
                                name=name,
                                name_short=name_short,
                                start_date=start_date,
                                end_date=None)
        session.add(new_employee)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)


# def update_employee_shift(db_str, employee_id, new_shift):
#     session, engine = open_session(db_str)
#     try:
#         # Get current employees
#         current_employees = (
#             session.query(Employee)
#             .filter_by(end_date=None)
#         )
#         employee = current_employees.filter(Employee.employee_id == employee_id).first()
        
#         if employee:
#             # Update the employee shift and start dates
#             current_shift = (
#                 session.query(ShiftHistory)
#                 .filter_by(employee_id=employee_id)
#                 .order_by(ShiftHistory.id.desc())
#                 .first()
#             )
            
#             shift_names = ['Day', 'Swing', 'Graveyard']
            
#             if current_shift not in shift_names:
#                 raise Exception("New shift name {new_shift} is not a valid shift")
#             elif current_shift == new_shift:
#                 raise Exception("New shift name {new_shift} is identical to current shift: {current_shift}")
#             else:
#                 new_shift = ShiftHistory(employee_id=employee.employee_id,
#                                          shift=new_shift,
#                                          shift_start_date=datetime.utcnow)
#                 session.add(new_shift)
#                 session.commit()
#                 return True
#         else:
#             print(f"No employee found with employee_id {employee_id}.")
#             return False
#     except Exception as e:
#         print(f"Error: {e}")
#         session.rollback()
#     finally:
#         close_session(session, engine)

##### Moldbay Methods #####
def update_moldbay_lead(db_str, moldbay_id, new_lead_id):
    session, engine = open_session(db_str)
    try:
        # Fetch moldbay row by moldbay_id
        moldbay_row = (
            session.query(Moldbay)
            .filter_by(moldbay_id=moldbay_id)
        )
        # Fetch new_lead_id from Employee table to make sure it's valid
        employee_row = (
            session.query(Employee)
            .filter_by(lead_id=new_lead_id)
            .order_by(Employee.id.desc())
            .first()
        )
        if not employee_row:
            print(f"No employee found with lead_id={new_lead_id}.")
            return False
        else:
            if moldbay_row:
                moldbay_row.update({'lead': new_lead_id})
                session.commit()
                return True
            else:
                print(f"Mold bay with id {moldbay_id} not found.")
                return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)
        
def remove_bag_from_moldbay(db_str, moldbay_id):
    session, engine = open_session(db_str)
    try:
        moldbay_row = (
            session.query(Moldbay)
            .filter_by(moldbay_id=moldbay_id)
        )
        
        if moldbay_row:
            moldbay_row.update({'bag_id': None})
            session.commit()
            return True
        else:
            print(f"No moldbay {moldbay_id} found.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)


# def outer_function(db_str, query_func, func_process, **kwargs):
#     session, engine = open_session(db_str)
#     try:
#         row = query_func(session, **kwargs)
#         func_process(row, **kwargs)
#         session.commit()
#     except Exception as e:
#         print(f"Error: {e}")
#         session.rollback()
#     finally:
#         close_session(session, engine)
        
        
# def query_func(session, **kwargs):
#     bag_param = kwargs.get('bag_id', None)
#     purple_param = kwargs.get('purple_id', None)
#     moldbay_param = kwargs.get('moldbay_id', None)
    
#     row = None
    
#     if bag_param is not None:
#         row = (
#             session.query(Bag)
#             .filter_by(bag_id=bag_param)
#             .order_by(Bag.id.desc())
#             .first()
#         )
    
#     elif purple_param is not None:
#         row = (
#             session.query(Purple)
#             .filter_by(purple_id=purple_param)
#             .order_by(Purple.id.desc())
#             .first()
#         )
    
#     elif moldbay_param is not None:
#         row = (
#             session.query(Moldbay)
#             .filter_by(moldbay_id=moldbay_param)
#         )
    
#     if row:
#         return row
#     else:
#         return False
        
# def func_process(row, **kwargs):
#     bag_param = kwargs.get('bag_id', None)
#     purple_param = kwargs.get('purple_id', None)
#     moldbay_param = kwargs.get('moldbay_id', None)
    
#     if bag_param is not None:
        
    
        
def replace_bag_in_moldbay(db_str, moldbay_id, new_bag_id):
    # Note: new_bag should refer to the id number in the Bag table, not the bag_id
    session, engine = open_session(db_str)
    try:
        moldbay_row = (
            session.query(Moldbay)
            .filter_by(moldbay_id=moldbay_id)
        )
        
        new_bag = get_latest_id_from_bag_id(db_str, new_bag_id)
        
        if moldbay_row:
            moldbay_row.update({'bag_id': new_bag})
            session.commit()
            return True
        else:
            return False
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        
    finally:
        close_session(session, engine)
        

###############################################################################
########################## Machine Learning Methods ###########################
###############################################################################
def get_df_date_range(db_str, TableClass, datestart, dateend):
    session, engine = open_session(db_str)
    query = session.query(TableClass).filter(TableClass.time.between(datestart, dateend))
    df = pd.read_sql(query.statement, engine)
    
    # Fix types in output dataframe
    df['time'] = pd.to_datetime(df['time'])
    
    close_session(session, engine)
    return df

def operator_data_cleaning(df):
    # Create copy to work with
    df_copy = df.copy()
    
    # Drop unnecessary columns
    drop_cols = ['layup_time',
                 'close_time',
                 'resin_time',
                 'cycle_time',
                 'leak_time',
                 'leak_count',
                 'parts_count',
                 'weekly_count',
                 'monthly_count',
                 'trash_count',
                 'bag',
                 'bag_days',
                 'bag_cycles']
    df_copy.drop(drop_cols, axis=1, inplace=True)
    
    return df_copy
    
def update_operator_lists(df_cycles, df_operators, time_column, op_column, op_list):
    for i in range(len(df_cycles)):
        current_time = df_cycles.loc[i, time_column]
        operators = df_operators[(df_operators['time'] <= current_time) & (df_operators[op_column] == df_cycles.loc[i, op_column])]
        op_list[i] = list(operators[op_column].unique())


def cycle_time_feature_engineering(df):
    # Create copy to work with
    df_copy = df.copy()
    
    # Drop unnecessary columns
    drop_cols = ['leak_time',
                 'leak_count',
                 'parts_count',
                 'weekly_count',
                 'monthly_count',
                 'trash_count',
                 'lead',
                 'assistant_1',
                 'assistant_2',
                 'assistant_3',
                 'bag',
                 'bag_days',
                 'bag_cycles']
    df_copy.drop(drop_cols, axis=1, inplace=True)
    
    # # Calculate the time difference between consecutive rows
    # df_copy['time_since_last_event'] = df_copy['time'].diff().dt.total_seconds()
    # # Fill missing values with a large value (e.g., to distinguish between different events)
    # df_copy['time_since_last_event'].fillna(999999, inplace=True)
    
    # Row sequence features
    df_copy['row_number'] = range(1, len(df_copy) + 1)
    
    # Null indicator features
    null_indicator_cols = [f'{column}_not_null' for column in df_copy.columns]
    df_copy[null_indicator_cols] = (~df_copy[df_copy.columns].isnull()).astype(int)
    df_copy.drop(['id_not_null',
                  'time_not_null',
                  'row_number_not_null'], axis=1, inplace=True)
    
    # # Drop all rows that don't have a value in one of the cycle time columns
    # cols_to_check = ['layup_time_not_null',
    #                   'close_time_not_null',
    #                   'resin_time_not_null',
    #                   'cycle_time_not_null']
    
    # df_filtered = df_copy.copy()
    # df_filtered = df_filtered[df_filtered[cols_to_check].any(axis=1)]
    
    return df_copy
       
def cycle_time_cleaning(df_raw):
    """
    Prepare raw data only for aligning stage times, using k-means clustering.

    Parameters
    ----------
    df_raw : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Remove unnecessary columns
    df_copy = df_raw.copy()
    keep_cols = ['time', 'layup_time', 'close_time', 'resin_time', 'cycle_time']
    df_copy = df_copy[keep_cols]
    
    ##### Feature engineering to make clustering easier #####
    # Previous non-null value comparison feature
    columns_to_check = df_copy.columns
    
    for column in columns_to_check:
        non_null_mask = ~df_copy[column].isnull()
    
        # Identify the previous non-null value
        prev_non_null_value = df_copy[column].where(non_null_mask).shift()
    
        # Create a boolean column indicating if the current value is the same as the previous non-null value
        new_column_name = f'{column}_same_as_prev_non_null'
        df_copy[new_column_name] = (df_copy[column] == prev_non_null_value).astype(int)
        
    # Remove all rows that contain 0 in layup_time, close_time, resin_time, or
    # cycle_time
    
    return df_copy

def count_consecutive_unique_values(column):
    consecutive_count = 0
    unique_values = set()
    
    for value in column:
        if pd.notna(value):  # Ignore null values
            if value not in unique_values:
                consecutive_count += 1
                unique_values.add(value)
    
    return consecutive_count

def cycle_time_clustering(df):
    # Calculate the time difference between consecutive rows
    df['time_since_last_event'] = df['time'].diff().dt.total_seconds()/60
    # Fill missing values with a large value (e.g., to distinguish between different events)
    df['time_since_last_event'].fillna(999999, inplace=True)
    
    n_clusters = count_consecutive_unique_values(df['cycle_time'])
    
    df_copy = df.copy()
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_features = ['time']
    df_copy['cluster'] = kmeans.fit_predict(df_copy[['time']])
    
    # Group by the 'cluster' column and aggregate the values using appropriate functions
    agg_funcs = {
        'id': 'first',         # Take the first id within each cluster
        'time': 'first',       # Take the first time within each cluster
        'layup_time': 'max',   # Calculate the mean for layup_time within each cluster
        'close_time': 'max',   # Calculate the mean for close_time within each cluster
        'resin_time': 'max',   # Calculate the mean for resin_time within each cluster
        'cycle_time': 'max',   # Calculate the mean for cycle_time within each cluster
    }
    
    collapsed_df = df_copy.groupby('cluster').agg(agg_funcs).reset_index(drop=True)
    
    # Sort the collapsed DataFrame by the 'time' column in ascending order
    collapsed_df = collapsed_df.sort_values(by='time', ascending=True)
    
    return df_copy, collapsed_df

def post_process_collapsed(df):
    # Check if values are identical to the index above
    repeated_values_mask = (df[['layup_time', 'close_time', 'resin_time', 'cycle_time']] ==
                            df[['layup_time', 'close_time', 'resin_time', 'cycle_time']].shift()).all(axis=1)

    # Check for rows with only zeros and null values in selected columns
    selected_columns = ['layup_time', 'close_time', 'resin_time', 'cycle_time']
    zero_null_rows_mask = (df[selected_columns].eq(0) | df[selected_columns].isnull()).all(axis=1)

    # Reset the index before applying boolean indexing
    df = df.reset_index(drop=True)
    
    # Remove rows with repeated values and zero/null rows
    df = df.loc[~repeated_values_mask]
    df = df.loc[~zero_null_rows_mask]

    # Remove rows with any value being 0
    df = df.loc[(df[selected_columns] != 0).any(axis=1)]

    return df


def process_stage_columns(df):
    # List of columns to process
    stage_columns = ['layup_time', 'close_time', 'resin_time', 'cycle_time']

    # Initialize an empty list to store individual dataframes
    dfs = []

    for stage_column in stage_columns:
        # Create a mask for rows with non-null values in the chosen column
        mask = ~df[stage_column].isnull()

        # Create a new dataframe with relevant columns based on the mask
        stage_df = df.loc[mask, ['time', stage_column]].copy()

        # Create a new column 'stage_time' based on the chosen column
        stage_df['stage_time'] = stage_df[stage_column]

        # Create a new column 'stage_name' based on the column being processed
        stage_df['stage_name'] = stage_column.replace('_time', '')

        # Append the dataframe to the list
        dfs.append(stage_df)

    # Concatenate the dataframes
    result_df = pd.concat(dfs, ignore_index=True)

    # Remove rows with NaN or zero values in 'stage_time'
    result_df = result_df[(result_df['stage_time'].notnull()) & (result_df['stage_time'] != 0)]
    
    # Drop the original columns 'layup_time', 'close_time', 'resin_time', and 'cycle_time'
    result_df = result_df.drop(columns=stage_columns)

    # Reindex the dataframe by 'time' in ascending order
    result_df = result_df.sort_values(by='time').reset_index(drop=True)

    return result_df

def collapse_data(df):
    n_cycles = df['stage_name'].value_counts()['cycle']
    kmeans = KMeans(n_clusters=n_cycles, random_state=42)  # You can adjust the number of clusters
    df['cluster'] = kmeans.fit_predict(df[['time']])
    
    # Get the value counts for each value in Column A
    value_counts = df['cluster'].value_counts()
    
    # Filter the values that occur only once
    unique_values = value_counts[value_counts == 1].index.tolist()
    
    # Create a mask for rows with values that occur only once in Column A
    unique_values_mask = df['cluster'].isin(unique_values)
    
    # Get the row indices where the mask is True
    indices_of_unique_values = df.index[unique_values_mask].tolist()
    
    time_diff_threshold = 5.0   # Number of seconds allowed for maximum abs value of time_diff
    
    for j in indices_of_unique_values:
        preceding_count, following_count = consecutive_identical_values_count(df, 'cluster', j)
        cluster_val = df.loc[j, 'cluster']
        preceding_time_diff = 0
        following_time_diff = 0
        cluster_found = False
        for i in range(preceding_count):
            preceding_time_diff += np.abs((df.loc[j-i-1, 'time'] - df.loc[j-i, 'time']).total_seconds())
            
        following_time_diff = 0
        for i in range(following_count):
            following_time_diff += np.abs((df.loc[j+i+1, 'time'] - df.loc[j+i, 'time']).total_seconds())

        if preceding_count == following_count:
            if preceding_time_diff < following_time_diff:
                df.loc[j, 'cluster'] = df.loc[j-1, 'cluster']
            else:
                df.loc[j, 'cluster'] = df.loc[j+1, 'cluster']
                
        elif (preceding_count < following_count) and (preceding_time_diff < time_diff_threshold):
            df.loc[j, 'cluster'] = df.loc[j-1, 'cluster']
            
        elif (preceding_count > following_count) and (following_time_diff < time_diff_threshold):
            df.loc[j, 'cluster'] = df.loc[j+1, 'cluster']
        
        elif (preceding_count < 4) and (preceding_time_diff < time_diff_threshold) and (cluster_found == False):
            df.loc[j, 'cluster'] = df.loc[j-1, 'cluster']
            
        elif (following_count < 4) and (following_time_diff < time_diff_threshold) and (cluster_found == False):
            df.loc[j, 'cluster'] = df.loc[j+1, 'cluster']
        
        else:
            # print(f"Orphan row {j} did not find a matching group.")
            pass
            
            
    # Get rid of repeated values in clusters
    filtered_df = df.groupby(['cluster', 'stage_name']).head(1)
    
    # Initialize an empty DataFrame for the collapsed data
    print("Collapsing data")
    df_collapsed = pd.DataFrame()

    # Iterate over unique cluster values
    for cluster_value in df['cluster'].unique():
        # Filter rows based on the current cluster value
        cluster_data = df[df['cluster'] == cluster_value]

        # Find the row with the highest time value
        max_time_row = cluster_data.loc[cluster_data['time'].idxmax()]

        # Create a new row for df_collapsed with the time value from the max_time_row
        new_row = {'time': max_time_row['time']}

        # Iterate over stage_names and extract corresponding stage_time values
        for stage_name in ['layup', 'close', 'resin', 'cycle']:
            stage_time = cluster_data[cluster_data['stage_name'] == stage_name]['stage_time'].values

            # If there are stage_time values, use the first one; otherwise, set it to NaN
            new_row[f'{stage_name}_time'] = stage_time[0] if len(stage_time) > 0 else float('nan')

        # Append the new_row to df_collapsed
        df_collapsed = df_collapsed.append(new_row, ignore_index=True)
        
        
    # Impute missing values where possible
    # Iterate over rows and impute missing values
    for index, row in df_collapsed.iterrows():
        # Check if there is only a single NaN value in the specified columns
        if row[['layup_time', 'close_time', 'resin_time', 'cycle_time']].isna().sum() == 1:
            # Impute missing values based on the condition
            if np.isnan(df_collapsed.loc[index, 'layup_time']):
                df_collapsed.loc[index, 'layup_time'] = df_collapsed.loc[index, 'cycle_time'] - df_collapsed.loc[index, 'close_time'] - df_collapsed.loc[index, 'resin_time']
            elif np.isnan(df_collapsed.loc[index, 'close_time']):
                df_collapsed.loc[index, 'close_time'] = df_collapsed.loc[index, 'cycle_time'] - df_collapsed.loc[index, 'layup_time'] - df_collapsed.loc[index, 'resin_time']
            elif np.isnan(df_collapsed.loc[index, 'resin_time']):
                df_collapsed.loc[index, 'resin_time'] = df_collapsed.loc[index, 'cycle_time'] - df_collapsed.loc[index, 'layup_time'] - df_collapsed.loc[index, 'close_time']
            elif np.isnan(df_collapsed.loc[index, 'cycle_time']):
                df_collapsed.loc[index, 'cycle_time'] = df_collapsed.loc[index, 'layup_time'] + df_collapsed.loc[index, 'close_time'] + df_collapsed.loc[index, 'resin_time']
            else:
                raise ValueError("No nan value detected in row")
                
        else:
            df_collapsed.drop([index])
            
    # Specify the columns to consider for duplicates
    subset_columns = ['layup_time', 'close_time', 'resin_time', 'cycle_time']

    # Identify consecutive duplicates and keep only the first instance
    df_collapsed = df_collapsed.drop_duplicates(subset=subset_columns, keep='first')
    
    # Catch any rows that contain nan and remove them
    df_collapsed.dropna(axis=0, inplace=True)
    
    # Reindex after possibly removing rows
    df_collapsed.reset_index(inplace=True, drop=True)
    
    df_collapsed['sum'] = df_collapsed[['layup_time', 'close_time', 'resin_time']].sum(axis=1)
    df_collapsed['diff'] = np.abs(df_collapsed['cycle_time'] - df_collapsed['sum'])
    
    # If diff column has a value greater than 0.05, decide what to do based on
    # the value (usually indicates missing cells or a repeated value where 
    # there shouldn't be)
    high_diff_indices = df_collapsed.index[df_collapsed['diff'] > 0.05].tolist()
    for ind in high_diff_indices:
        if df_collapsed.loc[ind,'cycle_time'] == df_collapsed.loc[ind-1,'cycle_time']:
            df_collapsed.loc[ind,'cycle_time'] = df_collapsed.loc[ind,['layup_time', 'close_time', 'resin_time']].sum()
            # dataFrame['Sum_Result'] = dataFrame.loc[0 : 1,["Opening_Stock" , "Closing_Stock"]].sum(axis = 1)
        else:
            df_collapsed.loc[ind,'cycle_time'] = df_collapsed.loc[ind,['layup_time', 'close_time', 'resin_time']].sum()            
    df_collapsed['diff'] = np.abs(df_collapsed['cycle_time'] - df_collapsed['sum'])
    high_diff_indices = df_collapsed.index[df_collapsed['diff'] > 0.05].tolist()
    print(f"{len(high_diff_indices)} rows found with mismatched cycle times:")
    print(high_diff_indices)
    
    # Drop unneeded sum and diff columns
    df_collapsed.drop(columns=['sum', 'diff'], inplace=True)
    
    return df_collapsed


def consecutive_identical_values_count(dataframe, column_name, target_index):
    """
    Check how many identical consecutive values precede and follow a particular index in a specific column.

    Parameters:
    - dataframe: Pandas DataFrame
    - column_name: Name of the column in the DataFrame
    - target_index: Target index for which to check consecutive identical values

    Returns:
    - Tuple containing the count of preceding and following identical consecutive values
    """

    # Check if the target index is within the valid range
    if target_index < 0 or target_index >= len(dataframe):
        raise ValueError("Invalid target index")

    # Get the value at the target index
    target_value = dataframe.loc[target_index, column_name]

    # Count consecutive identical values preceding the target index
    preceding_count = 0
    i = target_index - 1
    preceding_val = dataframe.loc[i, column_name]
    while i >= 0 and dataframe.loc[i, column_name] == preceding_val:
        preceding_count += 1
        i -= 1

    # Count consecutive identical values following the target index
    following_count = 0
    i = target_index + 1
    following_val = dataframe.loc[i, column_name]
    while i < len(dataframe) and dataframe.loc[i, column_name] == following_val:
        following_count += 1
        i += 1

    return preceding_count, following_count


def get_condensed_cycle_times(db_str, moldrawclass, datestart, dateend):
    # start = time.time()
    df_cycles = get_df_date_range(db_str, moldrawclass, datestart, dateend)
    # end = time.time()
    # print(f"Single dataframe obtained in {end-start} seconds for {moldrawclass.__tablename__}")
    result_df = process_stage_columns(df_cycles)
    df_collapsed = collapse_data(result_df)

    # Filter saturated times
    df_collapsed.drop(df_collapsed.index[df_collapsed['layup_time'] >= 274.99], inplace=True)
    df_collapsed.drop(df_collapsed.index[df_collapsed['close_time'] >= 89.99], inplace=True)
    df_collapsed.drop(df_collapsed.index[df_collapsed['resin_time'] >= 179.99], inplace=True)
    df_collapsed.reset_index(drop=True, inplace=True)
    
    # Remove any rows with negative values
    df_collapsed.drop(df_collapsed.index[df_collapsed['layup_time'] < 0], inplace=True)
    df_collapsed.drop(df_collapsed.index[df_collapsed['close_time'] < 0], inplace=True)
    df_collapsed.drop(df_collapsed.index[df_collapsed['resin_time'] < 0], inplace=True)
    df_collapsed.drop(df_collapsed.index[df_collapsed['cycle_time'] < 0], inplace=True)
    return df_collapsed
    

def update_collapsed_cycle_tables(db_str, mold_cycles):
    moldrawclasses = [BrownMoldRaw, GreenMoldRaw, OrangeMoldRaw, PinkMoldRaw, PurpleMoldRaw, RedMoldRaw]
    moldcycleclasses = [BrownMoldCycles, GreenMoldCycles, OrangeMoldCycles, PinkMoldCycles, PurpleMoldCycles, RedMoldCycles]
    session, engine = open_session(db_str)
    
    for i in range(len(moldrawclasses)):
        # Get the minimum and maximum time values in the raw data tables
        # dtstart_raw = session.query(func.min(moldrawclasses[i].time)).scalar()
        dtend_raw = session.query(func.max(moldrawclasses[i].time)).scalar()
        dtend_cycles = session.query(func.max(moldcycleclasses[i].time)).scalar()
        # If raw data extends past the cycle time data, update the cycle time data
        if dtend_raw > dtend_cycles:
            df_later = mold_cycles[i][mold_cycles[i]['time'] > dtend_raw]
        
        if len(df_later) > 0:
            print(f"Cycles data is missing some raw data for {moldcycleclasses[i].__tablename__}")
                    
            try:
                for index, row in df_later.iterrows():
                    session.add(moldcycleclasses[i](time=row['time'],
                                             layup_time=row['layup_time'],
                                             close_time=row['close_time'],
                                             resin_time=row['resin_time'],
                                             cycle_time=row['cycle_time']))
                    
                session.commit()
            
            except Exception as e:
                print(f"An error occurred: {e}")
                session.rollback()
                
            finally:
                session.close()
                engine.dispose()
                
        else:
            print(f"Cycles data is fully up to date for {moldcycleclasses[i].__tablename__}")
            
            
def request_cycle_times_single_mold(db_str, moldcolor, datestart, dateend):
    moldcolor = moldcolor.lower() # Use string as a key to get the appropriate classes
    moldrawclasses = {"brown": BrownMoldRaw,
                      "green": GreenMoldRaw,
                      "orange": OrangeMoldRaw,
                      "pink": PinkMoldRaw,
                      "purple": PurpleMoldRaw,
                      "red": RedMoldRaw}
    moldcycleclasses = {"brown": BrownMoldCycles,
                        "green": GreenMoldCycles,
                        "orange": OrangeMoldCycles,
                        "pink": PinkMoldCycles,
                        "purple": PurpleMoldCycles,
                        "red": RedMoldCycles}
    
    # Check if moldcycleclasses has data to cover the desired date range
    session, engine = open_session(db_str)
    dtstart_cycle = session.query(func.min(moldcycleclasses[moldcolor].time)).scalar()
    dtend_cycle = session.query(func.max(moldcycleclasses[moldcolor].time)).scalar()
    threshold = timedelta(days=7)
    df = pd.DataFrame()
    if (datestart < dtstart_cycle) or (dateend > dtend_cycle):
        print("Issue with a selected date outside the range of the available cycle data")
        if dateend-dtend_cycle < threshold:
            pass
            # would need to see if cycles data can be updated here
    else:
        # Request the data
        query = session.query(moldcycleclasses[moldcolor]).filter(moldcycleclasses[moldcolor].time.between(datestart, dateend))
        df = pd.read_sql(query.statement, engine)
        df['mold'] = moldcolor
        close_session(session, engine)
        
    return df

def request_cycle_times_all_molds(db_str, datestart, dateend):
    moldcolors = ['brown', 'green', 'orange', 'pink', 'purple', 'red']
    dflist = []
    for moldcolor in moldcolors:
        df = request_cycle_times_single_mold(db_str, moldcolor, datestart, dateend)
        dflist.append(df)
    df = pd.concat(dflist)
    
    return df

def add_cycle_start_times(dfcycles):
    dfcycles['layup_timedelta'] = pd.to_timedelta(dfcycles['layup_time'], unit='m')
    dfcycles['close_timedelta'] = pd.to_timedelta(dfcycles['close_time'], unit='m')
    dfcycles['resin_timedelta'] = pd.to_timedelta(dfcycles['resin_time'], unit='m')
    dfcycles['cycle_timedelta'] = pd.to_timedelta(dfcycles['cycle_time'], unit='m')
    
    dfcycles['time'] = pd.to_datetime(dfcycles['time'])
    
    dfcycles['cycle_end'] = dfcycles['time']
    dfcycles['cycle_start'] = dfcycles['time'] - dfcycles['cycle_timedelta']
    dfcycles['resin_end'] = dfcycles['time']
    dfcycles['resin_start'] = dfcycles['time'] - dfcycles['resin_timedelta']
    dfcycles['close_end'] = dfcycles['resin_start']
    dfcycles['close_start'] = dfcycles['close_end'] - dfcycles['close_timedelta']
    dfcycles['layup_end'] = dfcycles['close_start']
    dfcycles['layup_start'] = dfcycles['layup_end'] - dfcycles['layup_timedelta']
    
    return dfcycles
    
def get_operator_stage_times(time_ranges, dfcycles):
    df = dfcycles.copy()
    # Step 2: Create new indicator columns for each stage using booleans
    for stage in ['layup', 'close', 'resin', 'cycle']:
        start_col = f'{stage}_start'
        end_col = f'{stage}_end'
        indicator_col = f'{stage}_indicator'
        
        df[indicator_col] = False
        
        for start, end in time_ranges:
            mask = (df[end_col] >= start) & (df[start_col] <= end)
            df.loc[mask, indicator_col] = True
    
    # Step 3: Use indicators to mask the original time columns and replace non-overlapping ranges with NaN
    stages = ['layup', 'close', 'resin', 'cycle']
    for stage in stages:
        indicator_col = f'{stage}_indicator'
        time_col = f'{stage}_time'
        df[time_col] = df[time_col].where(df[indicator_col])
    
    # Create a new DataFrame with only the masked time columns
    result_df = df[['time','layup_time', 'close_time', 'resin_time', 'cycle_time']]
    
    return result_df

###############################################################################
##### Testing methods #####
def test_purple_methods():
    purple_id = 24
    new_cycles = 351
    # update_purple_cycles(db_str, purple_id, new_cycles)
    increment_purple_cycles(db_str, purple_id, -10)
    
    
    # # Add purples
    # add_purple(db_str, 40)
    # add_purple(db_str, 41)
    
    # # Check if the purples were added by querying the purples
    # session, engine = open_session(db_str)
    # purples = session.query(Purple).all()
    # for purple in purples:
    #     print([purple.id,
    #            purple.purple_id,
    #            purple.date_created,
    #            purple.date_trashed,
    #            purple.repairs,
    #            purple.cycles])
        
    # close_session(session, engine)
    
def test_moldbay_methods():
    moldbay_id = 6
    new_bag_id = None
    # remove_bag_from_moldbay(db_str, moldbay_id)
    replace_bag_in_moldbay(db_str, moldbay_id, new_bag_id)
    
if __name__ == "__main__":
    # test_purple_methods()
    # test_moldbay_methods()
    
    datestart = datetime(2022,5,4) # datestart should be no earlier than 5/4/2022, when the new logging method was started
    dateend = datetime(2023,12,20,23,59,59)
    start = time.time()
    dfcycles = request_cycle_times_all_molds(db_str, datestart, dateend)
    
    dfcycles = add_cycle_start_times(dfcycles)
    
    time_ranges = [
        (datetime(2022, 5, 4, 3, 0, 0), datetime(2022, 5, 4, 4, 0, 0)),
        (datetime(2022, 5, 10, 0, 0, 0), datetime(2022, 5, 10, 2, 0, 0)),
        (datetime(2022, 8, 4, 0, 0, 0), datetime(2022, 8, 4, 10, 0, 0)),
        (datetime(2023, 5, 10, 0, 0, 0), datetime(2023, 5, 10, 2, 0, 0)),
        (datetime(2023, 5, 14, 0, 0, 0), datetime(2023, 5, 20, 2, 0, 0)),
        # Add more time ranges as needed
    ]
    df_operator = get_operator_stage_times(time_ranges, dfcycles)
    end = time.time()
    print(f"Elapsed time: {end-start}")
    
    # moldrawclasses = [BrownMoldRaw, GreenMoldRaw, OrangeMoldRaw, PinkMoldRaw, PurpleMoldRaw, RedMoldRaw]
    # mold_cycles = [get_condensed_cycle_times(db_str, moldrawclass, datestart, dateend) for moldrawclass in moldrawclasses]
    
    # update_collapsed_cycle_tables(db_str, mold_cycles)
    
    # # Save Excel files of unsaturated cycle times
    # mold_cycles[0].to_excel("brown_unsaturated.xlsx")
    # mold_cycles[1].to_excel("green_unsaturated.xlsx")
    # mold_cycles[2].to_excel("orange_unsaturated.xlsx")
    # mold_cycles[3].to_excel("pink_unsaturated.xlsx")
    # mold_cycles[4].to_excel("purple_unsaturated.xlsx")
    # mold_cycles[5].to_excel("red_unsaturated.xlsx")
    
    # # Remove cycle_time outliers and save again
    # mold_cycles_no_outliers = []
    # for mold in mold_cycles:
    #     df = mold.copy()
    #     cycle_std = np.std(df['cycle_time'])
    #     avg = np.mean(df['cycle_time'])
    #     df.drop(df.index[df['cycle_time'] > (avg + 3*cycle_std)], inplace=True)
    #     df.drop(df.index[df['cycle_time'] < (avg - 3*cycle_std)], inplace=True)
    #     df.reset_index(drop=True, inplace=True)
        
    #     mold_cycles_no_outliers.append(df)
        
    # mold_cycles_no_outliers[0].to_excel("brown_no_outliers.xlsx")
    # mold_cycles_no_outliers[1].to_excel("green_no_outliers.xlsx")
    # mold_cycles_no_outliers[2].to_excel("orange_no_outliers.xlsx")
    # mold_cycles_no_outliers[3].to_excel("pink_no_outliers.xlsx")
    # mold_cycles_no_outliers[4].to_excel("purple_no_outliers.xlsx")
    # mold_cycles_no_outliers[5].to_excel("red_no_outliers.xlsx")