import sqlalchemy as _alchy
from sqlalchemy.ext.declarative import declarative_base as _declarative_base
import sqlalchemy.orm as _orm
from sqlalchemy import create_engine as _create_engine

from vexbot.robot_settings import RobotSettings
from vexbot.util.get_settings_database_filepath import get_settings_database_filepath

_Base = _declarative_base()


def _create_session(filepath):
    engine = _create_engine('sqlite:///{}'.format(filepath))
    _Base.metadata.bind = engine
    # TODO: decide if this is the best place to do this?
    _Base.metadata.create_all(engine)
    DBSession = _orm.sessionmaker(bind=engine)
    return DBSession()


class SettingsManager:
    def __init__(self, filepath=None):
        if filepath is None:
            filepath = get_settings_database_filepath()

        self.session = _create_session(filepath)

    def get_robot_settings(self, context='default'):
        pass

    def create_robot_settings(self, settings: dict):
        # TODO: Validate settings here instead of passing in directly
        new_robot = RobotSettings(**settings)
        self.session.add(new_robot)
        self.session.commit()
        # TODO: return validation errors, if any
