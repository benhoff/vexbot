import logging
import multiprocessing

import numpy as np
import spacy

from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV


from vexbot.util.get_classifier_filepath import get_classifier_filepath, get_entity_filepath


MAX_CV_FOLDS = 5


class Language:
    def __init__(self, classifier_filepath: str=None, language: str='en'):
        if classifier_filepath is None:
            classifier_filepath = get_classifier_filepath()

        self._classifier_filepath = classifier_filepath
        self.label_encoder = LabelEncoder()
        self.feature_extractor = None
        self.logger = logging.getLogger(__name__)
        self.langague_model = None

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

    def train(self, examples: dict):
        self.train_classifier(examples)
        # FIXME: Finish method
        # self.train_entity_extractor(examples)

    def train_classifier(self, examples: dict, filename: str=None):
        # nlp_spacy -> spacy language initializer -> Done
        # tokenizer_spacy -> Tokenizes -> Eh.
        # intent_featurizer_spacy -> adds text features -> Eh.

        # intent_entity_featurizer_regex |entity| -> regex
        # ner_crf |entity| -> conditional random field entity extraction
        # ner_synonyms |entity| -> 

        # intent_classifier_sklearn -> end of pipeline
        language = 'en'
        self.langague_model = spacy.load(language, parser=False)
        if filename is None:
            filename = self._classifier_filepath

        self.logger.debug('train classifier filepath: %s', filename)
        # - Y -
        numbers = []
        # text_features
        # - X -
        values = []
        for k, v in examples.items():
            for value in v:
                numbers.append(k)
                values.append(self.langague_model(value))

        kernel = 'linear'
        tune_parameters = [{'C': [1, 2, 5, 10, 20, 100], kernel: kernel}]
        number_threads = 1
        # Y
        numbers = self.label_encoder.inverse_transform(numbers)
        values = np.stack(values)
        # aim for 5 examples in each fold
        cv_splits = max(2, min(MAX_CV_FOLDS, np.min(np.bincount(numbers)) // 5))

        # craete the classifier
        self.classifier = GridSearchCV(SVC(C=1, probability=True, class_weight='balanced'),
                                       param_grid=tuned_parameters, n_jobs=number_threads,
                                       cv=cv_splits, scoring='f1_weighted', verbose=1)

        # self.classifier.fit(X, y)
        self.classifier.fit(values, numbers)

    def get_entities(self, text: str, *args, **kwargs):
        pass

    # FIXME: Finish
    # https://github.com/RasaHQ/rasa_nlu/blob/master/rasa_nlu/extractors/mitie_entity_extractor.py
    def train_entity_extractor(self, examples: list, filename: str=None):
        if filename is None:
            filename = get_entity_filepath() 

        trainer = mitie.ner_trainer(filename)
        trainer.num_threads = multiprocessing.cpu_count()
        for example in examples:
            tokens = self.tokenize(example['text'])
            for entity in example['entities']:
                pass


    def tokenize(self, text: str):
        return text.split()

