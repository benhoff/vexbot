import sys
import subprocess


class PluginWrapper:
    """
    don't want to have to think about how to activate
    a subprocess.
    """
    def __init__(self, module):
        self.module = module
        self._subprocess = None
        self._save_args = None
        self._service_name = None

    def activate(self,
                 invoke_args=None,
                 invoke_kwargs=None,
                 *args,
                 **kwargs):

        activate_args = [sys.executable,
                         self.module.__file__]
        if invoke_args is not None:
            activate_args.extend(invoke_args)
        # Please don't ask how this works. Pairs key/values from dict
        # in `kvkvkv` form
        if invoke_kwargs:
            flattened_dict = [item for sublist in invoke_kwargs.items()
                              for item in sublist]

            activate_args.extend(flattened_dict)

        self._save_args = (invoke_args, invoke_kwargs, args, kwargs)
        self._subprocess = subprocess.Popen(activate_args,
                                            stdout=subprocess.PIPE)

    def deactivate(self):
        # TODO: do terminate instead of kill, and schedule a callback to make
        # sure the process is terminated. Then kill
        self._subprocess.terminate()

    def restart(self):
        self.deactivate()
        self.activate(*self._save_args)
