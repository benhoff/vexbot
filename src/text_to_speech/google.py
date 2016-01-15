class GoogleTTS(AbstractMp3TTSEngine):
    """
    Uses the Google TTS online translator
    Requires pymad and gTTS to be available
    """

    SLUG = "google-tts"

    def __init__(self, language='en'):
        super(self.__class__, self).__init__()
        self.language = language

    @classmethod
    def is_available(cls):
        return (super(cls, cls).is_available() and
                diagnose.check_python_import('gtts') and
                diagnose.check_network_connection())

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
                if ('google-tts' in profile and
                   'language' in profile['google-tts']):
                    config['language'] = profile['google-tts']['language']

        return config

    @property
    def languages(self):
        langs = ['af', 'sq', 'ar', 'hy', 'ca', 'zh-CN', 'zh-TW', 'hr', 'cs',
                 'da', 'nl', 'en', 'eo', 'fi', 'fr', 'de', 'el', 'ht', 'hi',
                 'hu', 'is', 'id', 'it', 'ja', 'ko', 'la', 'lv', 'mk', 'no',
                 'pl', 'pt', 'ro', 'ru', 'sr', 'sk', 'es', 'sw', 'sv', 'ta',
                 'th', 'tr', 'vi', 'cy']
        return langs

    def say(self, phrase):
        self._logger.debug("Saying '%s' with '%s'", phrase, self.SLUG)
        if self.language not in self.languages:
            raise ValueError("Language '%s' not supported by '%s'",
                             self.language, self.SLUG)
        tts = gtts.gTTS(text=phrase, lang=self.language)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmpfile = f.name
        tts.save(tmpfile)
        self.play_mp3(tmpfile)
        os.remove(tmpfile)
