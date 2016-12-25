import os
from sqlalchemy import create_engine as _create_engine

from vexbot.models import Base
import vexbot.adapters.models


from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def create_database():
    database_filepath = get_settings_database_filepath()
    directory = os.path.dirname(database_filepath)
    if not os.path.isdir(directory):
        os.mkdir(directory)
    engine = _create_engine('sqlite:///{}'.format(database_filepath))
    Base.metadata.create_all(engine)
