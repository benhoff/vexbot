import pip
import pkg_resources


def get_installed_extensions(self, *args, **kwargs):
    verify_requirements = True
    name = 'vexbot_extensions'
    extensions = [x.name for x in pkg_resources.iter_entry_points(name)]
    return extensions


def _install(package) -> pkg_resources.Distribution:
    pip.main(['install', package.project_name])
    pkg_resources._initialize_master_working_set()
    return pkg_resources.get_distribution(package.project_name)


def add_extensions(self, *args, alias: list=None, call_name=None, hidden: bool=False, **kwargs):
    for arg in args:
        # NOTE: The dist should be used to figure out which name we want, not by grabbing blindly
        entry_point = [x for x in pkg_resources.iter_entry_points('vexbot_extensions', arg)][0]
        entry_point.require(installer=_install)
        function = entry_point.resolve()
        values = {'alias': alias, 'call_name': call_name, 'hidden': hidden, 'kwargs': kwargs}
        self._config['extensions'][arg] = values
        self.extend(function, alias=alias, name=call_name, hidden=hidden)
    self._config.sync()


def get_extensions(self, *args, **kwargs):
    return tuple(self._config['extensions'].keys())


def remove_extension(self, function_name: str, *args, **kwargs) -> str:
    popped = self._config['extensions'].pop(function_name)
    return 'Removed: {}'.format(popped)
