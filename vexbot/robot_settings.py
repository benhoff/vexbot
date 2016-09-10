import sqlalchemy as _alchy
from sqlalchemy.orm import relationship

from vexbot.sql_helper import Base


_T = _alchy.Table
_C = _alchy.Column
_AFK = _alchy.ForeignKey


adapter_robot_association_table = _T('adapter_robot_association',
                                     Base.metadata,
                                     _C('robot_settings_id',
                                        _alchy.Integer,
                                        _AFK('robot_settings.id')),
                                     _C('adapter_id',
                                        _alchy.Integer,
                                        _AFK('adapters.id')))


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

    startup_adapters = relationship('Adapter',
                                    secondary=adapter_robot_association_table,
                                    backref='contexts')


class Adapter(Base):
    __tablename__ = 'adapters'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    name = _alchy.Column(_alchy.String(length=100),
                         unique=True,
                         nullable=False)

    robots = relationship('RobotSettings',
                          secondary=adapter_robot_association_table,
                          back_populates='startup_adapters')


"""
class AdapterConfiguration(Base):
    __tablename__ = 'adapter_configuration'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    name = _alchy.Column(_alchy.String(length=100))
    attributes = relationship("AdapterAttributes")
    robot_settings = relationship("RobotSettings")
    robot_settings_id = _alchy.Column(_alchy.Integer,
                                      _alchy.ForeignKey('robot_settings.id'))


class AdapterAttributes(Base):
    __tablename__ = 'adapter_attributes'
    adapter_id = _alchy.Column(_alchy.Integer, primary_key=True)
    configuration_id = _alchy.Column(_alchy.Integer,
                                     _alchy.ForeignKey('adapter_configuration.id'))

    attribute_name = _alchy.Column(_alchy.String(length=20))
    attribut_value = _alchy.Column(_alchy.String(length=100))
"""
