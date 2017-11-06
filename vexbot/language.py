import mitie
import multiprocessing


class Language:
    def __init__(self, filename):
        self.classifier = None
        self.feature_extractor = None

    def get_intent(self, text: str, entities: dict, *args, **kwargs):
        # Text classification
        # Entity extraction
        tokens = self.tokenize(text)
        intent, confidence = self.classifier(tokens, self.feature_extractor)

        # text -> tokens
        # text -> entities
        # tokens + entites -> intent

        # total_word_feature_extractor
        pass

    def get_intent_no_entites(self):
        pass

    def train(self, examples: list):
        pass

    def train_classifier(self, examples: list):
        # FIXME: Add filename
        trainer = mitie.text_categorizer_trainer(filename)
        trainer.num_threads = multiprocessing.cpu_count()
        for example in examples:
            tokens = self.tokenize(example['text'])
            trainer.add_labeled_text(tokens, example['intent'])

        self.classifier = trainer.train()

    # https://github.com/RasaHQ/rasa_nlu/blob/master/rasa_nlu/extractors/mitie_entity_extractor.py
    def train_entity_extractor(self, examples: list):
        # FIXME: Add filename
        trainer = mitie.ner_trainer(filename)
        trainer.num_threads = multiprocessing.cpu_count()
        for example in examples:
            tokens = self.tokenize(example['text'])


    def tokenize(self, text: str):
        return text.split()

