class IvonaTTS(AbstractMp3TTSEngine):
    """
    Uses the Ivona Speech Cloud Services.
    Ivona is a multilingual Text-to-Speech synthesis platform developed by
    Amazon.
    """

    SLUG = "ivona-tts"

    def __init__(self, access_key='', secret_key='', region=None,
                 voice=None, speech_rate=None, sentence_break=None):
        super(self.__class__, self).__init__()
        self._pyvonavoice = pyvona.Voice(access_key, secret_key)
        self._pyvonavoice.codec = "mp3"
        if region:
            self._pyvonavoice.region = region
        if voice:
            self._pyvonavoice.voice_name = voice
        if speech_rate:
            self._pyvonavoice.speech_rate = speech_rate
        if sentence_break:
            self._pyvonavoice.sentence_break = sentence_break

    @classmethod
    def get_config(cls):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # HMM dir
        # Try to get hmm_dir from config
        profile_path = jasperpath.config('profile.yml')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'ivona-tts' in profile:
                    if 'access_key' in profile['ivona-tts']:
                        config['access_key'] = \
                            profile['ivona-tts']['access_key']
                    if 'secret_key' in profile['ivona-tts']:
                        config['secret_key'] = \
                            profile['ivona-tts']['secret_key']
                    if 'region' in profile['ivona-tts']:
                        config['region'] = profile['ivona-tts']['region']
                    if 'voice' in profile['ivona-tts']:
                        config['voice'] = profile['ivona-tts']['voice']
                    if 'speech_rate' in profile['ivona-tts']:
                        config['speech_rate'] = \
                            profile['ivona-tts']['speech_rate']
                    if 'sentence_break' in profile['ivona-tts']:
                        config['sentence_break'] = \
                            profile['ivona-tts']['sentence_break']
        return config

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                diagnose.check_python_import('pyvona') and
                diagnose.check_network_connection())

    def say(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmpfile = f.name
        self._pyvonavoice.fetch_voice(phrase, tmpfile)
        self.play_mp3(tmpfile)
        os.remove(tmpfile)
