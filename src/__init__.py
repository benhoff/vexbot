import os

# Get the file dir
file_dir = os.path.realpath(os.path.dirname(__file__))
"""
# get the project dir
project_dir = os.path.join(file_dir, '..', '')
"""
# Get the config dir
config_dir = os.path.join(file_dir, '..', 'config')
# Create config dir if it does not exist yet
if not os.path.exists(config_dir):
    try:
        os.makedirs(config_dir)
    except OSError:
        self._logger.error("Could not create config dir: '%s'",
                           jasperpath.CONFIG_PATH, exc_info=True)
        raise

# Check if config dir is writable
if not os.access(config_dir, os.W_OK):
    self._logger.critical("Config dir %s is not writable. Jasper " +
                          "won't work correctly.",
                          config_dir)
