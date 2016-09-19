import sqlalchemy as _alchy
from sqlalchemy.orm import relationship

from vexbot.sql_helper import Base


class ShellSettings(Base):
    __tablename__ = 'shell_settings'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    history_filepath = _alchy.Column(_alchy.String(length=4096))
    robot_model = relationship("RobotModel")
    robot_model_id = _alchy.Column(_alchy.Integer,
                                   _alchy.ForeignKey('robot_models.id'))
