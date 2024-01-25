# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 12:31:24 2024

@author: Ryan.Larson
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Sequence, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import pandas as pd
import numpy as np
from cycle_time_methods_v2 import load_raw_data_single_mold
import api_config_vars as api

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


def update_employee_shift(db_str, employee_id, new_shift):
    session, engine = open_session(db_str)
    try:
        # Get current employees
        current_employees = (
            session.query(Employee)
            .filter_by(end_date=None)
        )
        employee = current_employees.filter(Employee.employee_id == employee_id).first()
        
        if employee:
            # Update the employee shift and start dates
            current_shift = (
                session.query(ShiftHistory)
                .filter_by(employee_id=employee_id)
                .order_by(ShiftHistory.id.desc())
                .first()
            )
            
            shift_names = ['Day', 'Swing', 'Graveyard']
            
            if current_shift not in shift_names:
                raise Exception("New shift name {new_shift} is not a valid shift")
            elif current_shift == new_shift:
                raise Exception("New shift name {new_shift} is identical to current shift: {current_shift}")
            else:
                new_shift = ShiftHistory(employee_id=employee.employee_id,
                                         shift=new_shift,
                                         shift_start_date=datetime.utcnow)
                session.add(new_shift)
                session.commit()
                return True
        else:
            print(f"No employee found with employee_id {employee_id}.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        close_session(session, engine)

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
    test_moldbay_methods()