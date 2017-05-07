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
