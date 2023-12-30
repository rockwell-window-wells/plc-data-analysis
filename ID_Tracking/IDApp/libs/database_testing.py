# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 08:14:12 2023

@author: Ryan Larson
"""

# import sqlalchemy as db
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Null, Sequence, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import pandas as pd

Base = declarative_base()

# class Employee(Base):
#     __tablename__ = 'employees'
#     short_id = Column(Integer, primary_key=True)
#     historical_short_id = Column(Integer)
#     historical_id_date = Column(DateTime)
#     lead_id = Column(Integer)
#     start_date = Column(DateTime, default=datetime.utcnow)
#     end_date = Column(DateTime, default=Null)
#     moldbay = relationship('Moldbay', back_populates='lead', uselist=False)

class Purple(Base):
    __tablename__ = 'purples'
    
    idx = Column(Integer, primary_key=True, autoincrement=True)
    purple_id = Column(Integer)
    moldbay_id = Column(Integer, ForeignKey('moldbays.moldbay_id'))
    date_created = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    moldbay = relationship('Moldbay', back_populates='purple', uselist=False)
    
def add_purple(session, purple_id, moldbay_id, date_created=datetime.now, active=True):
    new_entry = Purple(purple_id=purple_id, moldbay_id=moldbay_id, date_created=date_created, active=active)
    session.add(new_entry)
    session.commit()    # Should commit be here? Or should it be outside the scope of this function?
    # session.close()
    
class Bag(Base):
    __tablename__ = 'bags'
    
    idx = Column(Integer, Sequence('idx'), primary_key=True, autoincrement=True)
    bag_id = Column(Integer)
    moldbay_id = Column(Integer, ForeignKey('moldbays.moldbay_id'))
    date_created = Column(DateTime, default=datetime.utcnow)
    moldbay = relationship('Moldbay', back_populates='bag', uselist=False)
    
def add_bag(session, bag_id, moldbay_id, date_created=datetime.now, active=True):
    new_entry = Bag(bag_id=bag_id, moldbay_id=moldbay_id, date_created=date_created, active=active)
    session.add(new_entry)
    session.commit()    # Should commit be here? Or should it be outside the scope of this function?
    
    
class Moldbay(Base):
    __tablename__ = 'moldbays'
    
    moldbay_id = Column(Integer, primary_key=True)
    moldbay_name = Column(String)
    # lead = Column(Integer, ForeignKey('employees.lead_id'), unique=True)
    purple = relationship('Purple', back_populates='moldbay', uselist=False)
    bag = relationship('Bag', back_populates='moldbay', uselist=False)
    
    
# Establishing the database connection
# db_loc = "C:\Users\Ryan Larson\github\plc-data-analysis\ID_Tracking\IDApp\libs\"
db_name = "test.db"
db_str = "sqlite:///" + db_name
engine = create_engine(db_str, echo=False)

# ...

# Creating a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

try:
    Base.metadata.create_all(engine)

    # Sample DataFrame with purple data
    purple_data = {
        # 'idx': [0, 1, 2, 3, 4, 5, 6, 7],
        'purple_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'moldbay_id': [0, 0, 1, 2, 3, 4, 5, 6],
        'date_created': [datetime.now(), datetime.now(), datetime.now(),
                         datetime.now(), datetime.now(), datetime.now(),
                         datetime.now(), datetime.now()],
        'active': [True, True, True, True, True, True, True, True],
    }

    purple_df = pd.DataFrame(purple_data)

    # Adding data from DataFrame to the "purples" table
    purple_df.to_sql('purples', con=engine, if_exists='append', index=False)

    # Committing the changes to the database
    session.commit()

    # Call the add_purple function within the same session
    add_purple(session, 24, 0, datetime.now(), False)

    # Query and print the purples within the same session scope
    purples = session.query(Purple).all()
    for purple in purples:
        print([purple.idx, purple.purple_id, purple.moldbay_id, purple.date_created, purple.active])

except Exception as e:
    print(f"An error occurred: {e}")
    session.rollback()  # Rollback changes in case of an error

finally:
    # Close the session in the finally block
    session.close()
    engine.dispose()



# # Creating a session to interact with the database
# Session = sessionmaker(bind=engine)
# with Session() as session:
#     Base.metadata.create_all(engine)
#     # session = Session()
    
#     # # Sample DataFrame with purple data
#     # purple_data = {
#     #     'moldbay_id': [1, 2, 3],  # Adjust moldbay_id values as needed
#     # }
    
#     # Sample DataFrame with purple data
#     purple_data = { 'idx': [0,1,2,3,4,5,6,7],
#                     'purple_id': [1,2,3,4,5,6,7,8],
#                     'moldbay_id': [0,0,1,2,3,4,5,6],
#                     'date_created': [datetime.now(),datetime.now(),datetime.now(),
#                                     datetime.now(),datetime.now(),datetime.now(),
#                                     datetime.now(),datetime.now(),],
#                     'active': [True, True, True, True, True, True, True, True],
#                     }
    
#     purple_df = pd.DataFrame(purple_data)
    
#     # # Adding data from DataFrame to the "purples" table
#     purple_df.to_sql('purples', con=engine, if_exists='append', index=False)
    
#     # print(session.query(Purple).all())
#     # Committing the changes to the database
#     session.commit()
    


#     add_purple(session, 24, 0, datetime.now(), False)
    
#     purples = session.query(Purple).all()
#     for purple in purples:
#         print([purple.idx, purple.purple_id, purple.moldbay_id, purple.date_created, purple.active])



# # Closing the session
# session.close()
# engine.dispose()


###############################################################################


# # db_loc = "C:\Users\Ryan Larson\github\plc-data-analysis\ID_Tracking\IDApp\libs\"
# db_name = "test_db.db"
# db_str = "sqlite:///" + db_name
# engine = db.create_engine(db_str)
# conn = engine.connect()
# metadata = db.MetaData()

# Purples = db.Table('Purples', metadata,
#                    db.Column('id', db.Integer(), primary_key=True),
#                    db.Column('purple_number', db.Integer(), nullable=False),
#                    db.Column('cycles', db.Integer(), nullable=False, default=0)
#                    db.Column('repairs', db.Integer(), nullable=False, default=0)
#                    db.Column('active', db.Boolean(), default=False),
#                    db.Column(''))