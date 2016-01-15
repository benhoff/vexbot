class MacOSXTTS(AbstractTTSEngine):
    """
    Uses the OS X built-in 'say' command
    """

    SLUG = "osx-tts"

    @classmethod
    def is_available(cls):
        return (platform.system().lower() == 'darwin' and
                diagnose.check_executable('say') and
                diagnose.check_executable('afplay'))

    def say(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        cmd = ['say', str(phrase)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)

    def play(self, filename):
        cmd = ['afplay', str(filename)]
        self._logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                     for arg in cmd]))
        with tempfile.TemporaryFile() as f:
            subprocess.call(cmd, stdout=f, stderr=f)
            f.seek(0)
            output = f.read()
            if output:
                self._logger.debug("Output was: '%s'", output)
