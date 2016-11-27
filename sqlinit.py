import sys

sys.path.append('./sqlbase')

from sqlalchemy import create_engine
from sqlbase import Base, WeatherData

DB_Connection = 'postgresql://weather:weather@localhost:5432/weather'

engine = create_engine(DB_Connection)
Base.metadata.create_all(engine)
