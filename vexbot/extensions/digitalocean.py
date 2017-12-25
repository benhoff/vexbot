import os
import digitalocean


_MANAGER = False
_DEFAULT_DROPLET = os.getenv('DIGITAL_OCEAN_DROPLET_ID')
_DIGITAL_OCEAN_KEY = os.getenv('DIGITAL_OCEAN_KEY')
if _DIGITAL_OCEAN_KEY:
    _MANAGER = digitalocean.Manager(token=_DIGITAL_OCEAN_KEY)


def get_size(*args, **kwargs):
    id_ = kwargs.get('id', _DEFAULT_DROPLET)
    if id_ is None:
        # FIXME: implement a way to pass this in as a config
        raise RuntimeError('Must pass in an `id_` or set the `DITIAL_OCEAN_DROPLET_ID` in your envirnoment')
    droplet = _MANAGER.get_droplet(id_)
    return droplet.size


def power_off(*args, **kwargs):
    id_ = kwargs.get('id', _DEFAULT_DROPLET)
    if id_ is None:
        # FIXME: implement a way to pass this in as a config
        raise RuntimeError('Must pass in an `id_` or set the `DITIAL_OCEAN_DROPLET_ID` in your envirnoment')
    droplet = _MANAGER.get_droplet(id_)
    droplet.power_off()


def power_on(*args, **kwargs):
    id_ = kwargs.get('id', _DEFAULT_DROPLET)
    if id_ is None:
        # FIXME: implement a way to pass this in as a config
        raise RuntimeError('Must pass in an `id_` or set the `DITIAL_OCEAN_DROPLET_ID` in your envirnoment')
    droplet = _MANAGER.get_droplet(id_)
    droplet.power_on()


def get_all_droplets(*args, **kwargs):
    droplets = _MANAGER.get_all_droplets()
    return ['{}: {}'.format(x.name, x.id) for x in droplets]
