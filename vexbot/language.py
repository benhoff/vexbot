import code
import pickle
import logging
import multiprocessing

import numpy as np
import spacy

from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV

from vexbot.entity_extraction import EntityExtraction
from vexbot.util.get_classifier_filepath import (get_classifier_filepath,
                                                 get_entity_filepath)


MAX_CV_FOLDS = 5


class Language:
    def __init__(self, classifier_filepath: str=None, language: str='en'):
        if classifier_filepath is None:
            classifier_filepath = get_classifier_filepath()

        self._classifier_filepath = classifier_filepath
        self.label_encoder = LabelEncoder()
        self.feature_extractor = None
        self.logger = logging.getLogger(__name__)
        self.language_model = None
        self._language_model_loaded = False
        self.classifier = None
        self.synonyms = {}
        self.entity_extractor = EntityExtraction()

    def predict(self, X):
        pred_result = self.classifier.predict_proba(X)
        sorted_indicies = np.fliplr(np.argsort(pred_result, axis=1))
        return sorted_indicies, pred_result[:, sorted_indicies]

    def get_intent(self, text: str, entities: list=None, *args, **kwargs):
        # Text classification
        # Entity extraction
        if self.classifier is None:
            self.load_classifier()
        if not self._language_model_loaded:
            self._load_models()

        langague_features = self.language_model(text).vector
        langague_features = langague_features.reshape(1, -1)
        intents, probabilities = self.predict(langague_features)
        if intents.size > 0 and probabilities.size > 0:
            ranking = list(zip(list(intents), list(probabilities)))[:10]
            intent_ranking = [{"name": self.label_encoder.inverse_transform(intent_name), "confidence": score} for intent_name, score in ranking]
            first_name = intent_ranking[0]['name'][0]
            first_confidence = intent_ranking[0]['confidence'][0]
        else:
            first_name = None
            first_confidence = 0
        self.logger.debug('name: %s', first_name)
        self.logger.debug('confidence: %s', first_confidence)
        extracted = self.entity_extractor.get_entites(text, entities)
        # TODO: clean or merge entities here?

        return first_name, first_confidence, entities

        # text -> tokens
        # text -> entities
        # tokens + entites -> intent

        # total_word_feature_extractor

    # FIXME: currently unused
    def train(self, examples: dict):
        self.train_classifier(examples)
        # FIXME: Finish method
        # self.train_entity_extractor(examples)

    def _load_models(self):
        language = 'en'
        self.language_model = spacy.load(language, parser=False)
        self.entity_extractor._language_model = self.language_model
        self._language_model_loaded = True

    def load_classifier(self, filename: str=None):
        if filename is None:
            filename = self._classifier_filepath

        # FIXME: this code is super brittle for various reasons
        with open(filename, 'rb') as f:
            self.classifier = pickle.load(f)
        with open(filename + 'label', 'rb') as f:
            self.label_encoder = pickle.load(f)

    def get_spacy_text_features(self, text: str):
        # type: np.ndarray
        doc = self.language_model(text)
        vector = doc.vector
        return vector

    def train_classifier(self, examples: dict, filename: str=None, persist=True):
        # tokenizer_spacy -> Tokenizes -> Eh.
        # NOTE: this should keep track of a numpy list that is [#, 0/1] showing 
        # which known regex pattern and if it was found (1) or not found (0)
        # AKA a feature matrix

        # intent_entity_featurizer_regex |entity| -> regex

        # NOTE: Start here
        # nlp_spacy -> spacy language initializer -> Done
        # intent_featurizer_spacy -> adds text features -> Eh.

        # ner_crf |entity| -> conditional random field entity extraction -> crf_entity_extractor
        # ner_synonyms |entity| -> dict replacing the entity values bascially

        # intent_classifier_sklearn -> end of pipeline
        if not self._language_model_loaded:
            self._load_models()

        if filename is None:
            filename = self._classifier_filepath

        self.logger.debug('train classifier filepath: %s', filename)
        # - Y -
        numbers = []
        # text_features
        # - X -
        values = []
        for k, v in examples.items():
            self.logger.debug('intent: %s', k)
            # FIXME: I don't think I want this to be a callback.
            if v is None:
                continue
            for value in v:
                numbers.append(k)
                language_values = self.language_model(value)
                # get the vector from spacy
                values.append(language_values.vector)

        values = np.stack(values)
        # Y
        numbers = self.label_encoder.fit_transform(numbers)
        # aim for 5 examples in each fold
        cv_splits = max(2, 
                        min(MAX_CV_FOLDS,
                            np.min(np.bincount(numbers)) // 5))

        estimator = SVC(C=1, probability=True, class_weight='balanced')

        number_threads = multiprocessing.cpu_count()
        kernel = 'linear'
        # NOTE: the `kernel` parameter needs to be a list for sklearn
        tuned_parameters = [{'C': [1, 2, 5, 10, 20, 100],
                            'kernel': [kernel]}]
        # create the classifier
        self.classifier = GridSearchCV(estimator,
                                       param_grid=tuned_parameters,
                                       n_jobs=number_threads,
                                       cv=cv_splits,
                                       scoring='f1_weighted',
                                       verbose=1)

        # self.classifier.fit(X, y)
        self.classifier.fit(values, numbers)
        if persist:
            with open(filename, 'wb') as f:
                pickle.dump(self.classifier, f)
            with open(filename + 'label', 'wb') as f:
                pickle.dump(self.label_encoder, f)

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
