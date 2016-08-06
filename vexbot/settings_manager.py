import sqlalchemy as _alchy
from sqlalchemy.ext.declarative import import declarative_base as _declarative_base
import sqlalchemy.orm as _orm
from sqlalchemy import import create_engine as _create_engine

_Base = _declarative_base()

def _create_session(filepath):
    engine = _create_engine('sqlite:///{}'.format(database_filepath))
    _Base.metadata.bind = engine
    DBSession = _orm.sessionmaker(bind=engine)
    return DBSession()


class SettingsManager:
    # FIXME: probably best to not pass in a filepath here
    # should be set elsewhere
    def __init__(self, database_filepath):
        self.session = _create_session(filepath)
