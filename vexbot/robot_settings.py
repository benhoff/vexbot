import sqlalchemy as _alchy
from sqlalchemy.orm import relationship

from vexbot.sql_helper import Base

class SettingsToAdapters(Base):
    __tablename__ = 'settings_adapters'
    robot_id = _alchy.Column(_alchy.Integer,
                            _alchy.ForeignKey('robot_settings.id'),
                            primary_key=True)

    adapter_id = _alchy.Column(_alchy.Integer,
                             _alchy.ForeignKey('adapters.id'),
                             primary_key=True)

    adapter = relationship("Adapters",
                           back_populates="contexts")

    context = relationship("RobotSettings",
                           back_populates="startup_adapters")

class RobotSettings(Base):
    __tablename__ = 'robot_settings'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    # Robot context
    context = _alchy.Column(_alchy.String(length=50), unique=True)
    name = _alchy.Column(_alchy.String(length=100), default='vexbot')

    subscribe_address = _alchy.Column(_alchy.String(length=100),
                                      default='tcp://127.0.0.1:4001')

    publish_address = _alchy.Column(_alchy.String(length=100),
                                    default='tcp://127.0.0.1:4002')

    monitor_address = _alchy.Column(_alchy.String(length=100),
                                    default='tcp://127.0.0.1:4003')

    startup_adapters = relationship('SettingsToAdapters',
                                    back_populates='context')

class Adapters(Base):
    __tablename__ = 'adapters'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    name = _alchy.Column(_alchy.String(length=100), unique=True)

    contexts = relationship("SettingsToAdapters",
                            back_populates='adapter')
