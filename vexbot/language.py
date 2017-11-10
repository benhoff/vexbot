import code
import logging
import multiprocessing

import numpy as np
import spacy

from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV


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
        self.langague_model = None
        self._language_model_loaded = False
        self.classifier = None

    def predict(self, X):
        pred_result = self.classifier.predict_proba(X)
        sorted_indicies = np.fliplr(np.argsort(pred_result, axis=1))
        return sorted_indicies, pred_result[:, sorted_indicies]

    def get_intent(self, text: str, entities: dict, *args, **kwargs):
        # Text classification
        # Entity extraction
        if not self.classifier:
            return None, []

        langague_features = self.langague_model(text).vector
        langague_features = langague_features.reshape(1, -1)
        intents, probabilities = self.predict(langague_features)
        if intents.size > 0 and probabilities.size > 0:
            ranking = list(zip(list(intents), list(probabilities)))[:10]
            intent_ranking = [{"name": intent_name, "confidence": score} for intent_name, score in ranking]
        return intent_ranking

        # text -> tokens
        # text -> entities
        # tokens + entites -> intent

        # total_word_feature_extractor
        pass

    def train(self, examples: dict):
        self.train_classifier(examples)
        # FIXME: Finish method
        # self.train_entity_extractor(examples)

    def _load_models(self):
        language = 'en'
        self.langague_model = spacy.load(language, parser=False)
        self._language_model_loaded = True

    def train_classifier(self, examples: dict, filename: str=None):
        # nlp_spacy -> spacy language initializer -> Done
        # tokenizer_spacy -> Tokenizes -> Eh.
        # intent_featurizer_spacy -> adds text features -> Eh.

        # intent_entity_featurizer_regex |entity| -> regex
        # ner_crf |entity| -> conditional random field entity extraction
        # ner_synonyms |entity| -> 

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
                language_values = self.langague_model(value)
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
