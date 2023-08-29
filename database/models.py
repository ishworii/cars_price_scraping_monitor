# models.py

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CarListing(Base):
    __tablename__ = "car_listings"

    id = Column(Integer, primary_key=True)
    year_make_model = Column(String)
    year = Column(String)
    make = Column(String)
    model = Column(String)
    damage = Column(String)
    buy_now_price = Column(Float)
    old_price = Column(Float, default=0)
    location = Column(String)
    title = Column(String)
    loss = Column(String)
    thumbnail = Column(String)
    details = Column(String)
    source = Column(String)
