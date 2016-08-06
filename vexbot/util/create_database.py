from sqlalchemy import create_engine as _create_engine

import vexbot.robot_settings as _robot
import vexbot.adapters.shell as _shell

from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def create_database():
    bases = [_robot._Base,
            _shell._Base]

    database_filepath = get_settings_database_filepath()
    engine = _create_engine('sqlite:///{}'.format(database_filepath))

    for base in bases:
        base.metadata.create_all(engine)
