import os
import sys
from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
 
Base = declarative_base()

class WeatherData(Base):
    __tablename__ = 'wd'
    id          = Column(Integer, primary_key=True)
    datetime    = Column(DateTime)
    windspeed   = Column(Float)
    winddir     = Column(Integer)
    windgust    = Column(Float)
    barometer   = Column(Float)
    inhumidity  = Column(Integer)
    outhumidity = Column(Integer)
    intemp      = Column(Float)
    outtemp     = Column(Float)
    dewpoint    = Column(Float)
    heatindex   = Column(Float)
    windchill   = Column(Float)
    rain        = Column(Float)
