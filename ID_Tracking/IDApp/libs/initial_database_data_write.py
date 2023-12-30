# -*- coding: utf-8 -*-
"""
Writes the initial database from a few CSV files (may change later to be a
single Excel file with multiple sheets).

Created on Sat Dec 30 10:41:04 2023

@author: Ryan Larson
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Null, Sequence, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import pandas as pd
import numpy as np

Base = declarative_base()

class Bag(Base):
    __tablename__ = 'bags'
    
    idx = Column(Integer, Sequence('idx'), primary_key=True, autoincrement=True)
    bag_id = Column(Integer)
    moldbay_id = Column(Integer, ForeignKey('moldbays.moldbay_id'))
    date_created = Column(DateTime, default=datetime.utcnow)
    moldbay = relationship('Moldbay', back_populates='bag', uselist=False)
    
class Moldbay(Base):
    __tablename__ = 'moldbays'
    
    moldbay_id = Column(Integer, primary_key=True)
    moldbay_name = Column(String)
    # lead = Column(Integer, ForeignKey('employees.lead_id'), unique=True)
    # purple = relationship('Purple', back_populates='moldbay', uselist=False)
    bag = relationship('Bag', back_populates='moldbay', uselist=False)

# # Get CSV file that contains bag data
# bag_csv = "bag_data.csv"
# bag_df = pd.read_csv(bag_csv)

# Establishing the database connection
# db_loc = "C:\Users\Ryan Larson\github\plc-data-analysis\ID_Tracking\IDApp\libs\"
db_name = "PLC_ID_database.db"
db_str = "sqlite:///" + db_name
engine = create_engine(db_str, echo=False)

# ...

# Creating a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

try:
    Base.metadata.create_all(engine)
    
    moldbay_data = {
        'moldbay_id': [1,2,3,4,5,6,7],
        'moldbay_name': ['Brown','Pink','Purple','Orange','Red','Green','Offline'],
        'lead': [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        'purple': [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        'bag': [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        }
    
    moldbay_df = pd.DataFrame(moldbay_data)
    moldbay_df.to_sql('moldbays', con=engine, if_exists='replace', index=False)
    
    # # Adding data from DataFrame to the "purples" table
    # bag_df.to_sql('bags', con=engine, if_exists='replace', index=False)
    
    session.commit()
    
except Exception as e:
    print(f"An error occurred: {e}")
    session.rollback()
    
finally:
    session.close()
    engine.dispose()