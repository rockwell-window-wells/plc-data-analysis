# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 11:26:47 2024

@author: Ryan.Larson
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

class Moldbay(Base):
    __tablename__ = 'moldbays'

    id = Column(Integer, primary_key=True)
    moldbay_number = Column(Integer, unique=True, nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    current_employee = relationship('Employee')

# Example usage
engine = create_engine('sqlite:///example3.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Adding an Employee
employee = Employee(employee_id=1, name='John Doe')
session.add(employee)
employee2 = Employee(employee_id=1, name='John Deere')
session.add(employee2)
session.commit()

# Adding a Moldbay associated with the Employee
moldbay = Moldbay(moldbay_number=1, employee_id=employee.id)
session.add(moldbay)
session.commit()

# Retrieve the Moldbay and access the associated Employee's attributes
moldbay = session.query(Moldbay).first()

if moldbay.current_employee:
    print(f"Moldbay Number: {moldbay.moldbay_number}")
    print(f"Employee ID: {moldbay.current_employee.employee_id}")
    print(f"Employee Name: {moldbay.current_employee.name}")
