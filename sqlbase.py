import os
import sys
from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
 
Base = declarative_base()

class WeatherData(Base):
    __tablename__ = 'wd'
    id              = Column(Integer, primary_key=True)
    timestamp       = Column(DateTime)
    wind_direction  = Column(Float)
    wind_speed      = Column(Float)
    wind_gust       = Column(Float)
    rain            = Column(Float)
    temperature_in  = Column(Float)
    pressure_in     = Column(Float)
    temperature_out = Column(Float)
    humidity        = Column(Float)


from sqlalchemy import create_engine
# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
#engine = create_engine('sqlite:///sqlalchemy_example.db')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
#Base.metadata.create_all(engine)
