from sqlalchemy import String, Integer, Column, ForeignKey, Table
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base as _declarative_base


Base = _declarative_base()


# Profiles to be used to load up a bunch of adapters/settings at once
class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    name = Colummn(String(50), nullable=False, unique=True)


class Adapter(Base):
    __tablename__ = 'adapters'
    id = Column(Integer, primary_key=True)
    service_name = Column(String(100), nullable=False)
    profile = Column(Integer, ForeignKey('profiles.id'))
