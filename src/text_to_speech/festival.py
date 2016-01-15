class FestivalTTS(AbstractTTSEngine):
    """
    Uses the festival speech synthesizer
    Requires festival (text2wave) to be available
    """

    SLUG = 'festival-tts'

    @classmethod
    def is_available(cls):
        if (super(cls, cls).is_available() and
           diagnose.check_executable('text2wave') and
           diagnose.check_executable('festival')):

            logger = logging.getLogger(__name__)
            cmd = ['festival', '--pipe']
            with tempfile.SpooledTemporaryFile() as out_f:
                with tempfile.SpooledTemporaryFile() as in_f:
                    logger.debug('Executing %s', ' '.join([pipes.quote(arg)
                                                           for arg in cmd]))
                    subprocess.call(cmd, stdin=in_f, stdout=out_f,
                                    stderr=out_f)
                    out_f.seek(0)
                    output = out_f.read().strip()
                    if output:
                        logger.debug("Output was: '%s'", output)
                    return ('No default voice found' not in output)
        return False

    def say(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        cmd = ['text2wave']
        with tempfile.NamedTemporaryFile(suffix='.wav') as out_f:
            with tempfile.SpooledTemporaryFile() as in_f:
                in_f.write(phrase)
                in_f.seek(0)
                with tempfile.SpooledTemporaryFile() as err_f:
                    self._logger.debug('Executing %s',
                                       ' '.join([pipes.quote(arg)
                                                 for arg in cmd]))
                    subprocess.call(cmd, stdin=in_f, stdout=out_f,
                                    stderr=err_f)
                    err_f.seek(0)
                    output = err_f.read()
                    if output:
                        self._logger.debug("Output was: '%s'", output)
            self.play(out_f.name)
