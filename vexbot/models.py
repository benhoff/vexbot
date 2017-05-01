from sqlalchemy import String, Integer, Column, ForeignKey, Table
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base as _declarative_base


Base = _declarative_base()


robot_address = Table('robot_address',
                      Base.metadata,
                      Column('robot_model_id',
                             Integer,
                             ForeignKey('robot_models.id')),
                      Column('address_id',
                             Integer,
                             ForeignKey('zmq_addresses.id')))

adapter_address = Table('adapter_address',
                        Base.metadata,
                        Column('adapter_id',
                               Integer,
                               ForeignKey('adapters.id')),
                        Column('address_id',
                               Integer,
                               ForeignKey('zmq_addresses.id')))


def _zmq_address_stripper(address):
    if address.startswith('tcp://'):
        return address[6:]

    return address


class RobotModel(Base):
    __tablename__ = 'robot_models'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=100), default='vexbot')
    publish_address_id = Column(Integer, ForeignKey('zmq_addresses.id'))
    heartbeat_address_id = Column(Integer,
                                  ForeignKey('zmq_addresses.id'))

    publish_address = relationship('ZmqAddress',
                                   foreign_keys=[publish_address_id])

    heartbeat_address = relationship('ZmqAddress',
                                     foreign_keys=[heartbeat_address_id])

    subscribe_addresses = relationship('ZmqAddress', secondary=robot_address)

    @property
    def zmq_publish_address(self):
        if not self.publish_address:
            return None
        return self.publish_address.zmq_address

    @property
    def zmq_heartbeat_address(self):
        if not self.heartbeat_address:
            return None
        return self.heartbeat_address.zmq_address

    @property
    def zmq_subscription_addresses(self):
        if self.subscribe_addresses:
            return [x.zmq_address for x in self.subscribe_addresses]
        else:
            return list()


class ZmqAddress(Base):
    __tablename__ = 'zmq_addresses'
    id = Column(Integer, primary_key=True)
    address = Column(String(100), nullable=False, unique=True)

    @property
    def zmq_address(self):
        """
        default to tcp transport for now
        """
        return 'tcp://{}'.format(self.address)


class Module(Base):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)


class Adapter(Base):
    __tablename__ = 'adapters'
    id = Column(Integer, primary_key=True)
    module_name = Column(Integer, ForeignKey('modules.id'), nullable=False)
    service_name = Column(String(100), nullable=False)
    publish_address = Column(Integer, ForeignKey('zmq_addresses.id'))
    subscribe_addresses = relationship('ZmqAddress', secondary=adapter_address)
