import pip
import pkg_resources
from vexbot.extensions import extend as _extend
from vexbot.extension_metadata import extensions as _meta_data


def get_installed_extensions(self, *args, **kwargs):
    verify_requirements = True
    name = 'vexbot_extensions'
    extensions = ['{}: {}'.format(x.name, _meta_data[x.name].get('short', 'NO DOC')) for x in pkg_resources.iter_entry_points(name)]
    return sorted(extensions, key=str.lower)


def _install(package) -> pkg_resources.Distribution:
    pip.main(['install', package.project_name])
    pkg_resources._initialize_master_working_set()
    return pkg_resources.get_distribution(package.project_name)


def add_extensions(self,
                   *args,
                   alias: list=None,
                   call_name=None,
                   hidden: bool=False,
                   update: bool=True,
                   **kwargs):

    not_found = set()
    # NOTE: The dist should be used to figure out which name we want, not by grabbing blindly
    entry_points = [x for x in pkg_resources.iter_entry_points('vexbot_extensions') if x.name in args]
    for entry in entry_points:
        entry.require(installer=_install)
        function = entry.resolve()
        values = {'alias': alias, 'call_name': call_name, 'hidden': hidden, 'kwargs': kwargs}
        self._config['extensions'][entry.name] = values
        self.extend(function, alias=alias, name=call_name, hidden=hidden, update=False)
    self._config.sync()
    update_method = getattr(self, 'update_commands')
    if update and update_method:
        update_method()
    if not_found:
        raise RuntimeError('Packages not found/installed: {}'.format(not_found))


def add_extensions_from_dict(self, extensions: dict):
    keys = tuple(extensions.keys())
    entry_points = [x for x in pkg_resources.iter_entry_points('vexbot_extensions') if x.name in keys]
    for entry in entry_points:
        entry.require(installer=_install)
        function = entry.resolve()
        values = dict(extensions[entry.name])
        kwargs = values.pop('kwargs', {})
        values.update(kwargs)
        name = values.pop('call_name', function.__name__)
        _extend(self.__class__, function, **values)


def get_extensions(self, *args, values: bool=False, **kwargs):
    if values:
        return self._config['extensions']
    return tuple(self._config['extensions'].keys())


def remove_extension(self, function_name: str, *args, **kwargs) -> str:
    popped = self._config['extensions'].pop(function_name)
    return 'Removed: {}'.format(popped)
