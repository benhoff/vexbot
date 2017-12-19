import sklearn_crfsuite
import spacy


class EntityExtraction:
    def __init__(self, language_model=None):
        values = {'algorithm': 'lbfgs',
                  # coefficient for L1 penalty
                  'c1': 1,
                  # coefficient for L2 penalty
                  'c2': 1e-3,
                  'max_iterations': 50,
                  # include transitions that are possible, but not observed
                  'all_possible_transitions': True}

        self.ent_tagger = sklearn_crfsuite.CRF(**values)
        self._language_model = language_model

    def train(self, data):
        # _sentence_to_features
        x_train = []
        # _sentence_to_labels
        y_train = []

        self.ent_tagger.fit(x_train, y_train)

    def get_entites(self, text: str, entities: list=None, *args, **kwargs):
        spacy_entities = self.get_spacy(text)
        # TODO: Implement
        duckling_entities = self.get_duckling_entities(text)
        custom_entities = self.get_custom_entities(text)

        # FIXME
        return spacy_entities

    def get_custom_entities(self, text: str) -> list:
        """
        Custom, Domain-specific entities
        Uses conditional random field
        Needs to be trained
        """
        # NOTE: MITIE uses structured SVM
        pass

    def get_duckling_entities(self, text: str) -> list:
        """
        Pretrained (duckling)
        Uses context-free grammer
        Dates, Amounts of Money, Druations, Distances, Ordinals
        """
        pass

    def get_spacy_entites(self, text: str) -> list:
        """
        Pretrained (spaCy)
        Uses averaged preceptron
        Places, dates, people, organizations
        """
        # NOTE: spaCy doc
        doc = self._language.language_model(text)

        entities = [{"entity": ent.label_,
                     "value": ent.text,
                     "start": ent.start_char,
                     "end": ent.end_char} for ent in doc.ents]

        return entities

    # NOTE: used for conditional random field training
    def _sentence_to_features(self, sentence: list):
        # type: (List[Tuple[Text, Text, Text, Text]]) -> List[Dict[Text, Any]]
        """Convert a word into discrete features in self.crf_features,
        including word before and word after."""

        sentence_features = []
        prefixes = ('-1', '0', '+1')

        for word_idx in range(len(sentence)):
            # word before(-1), current word(0), next word(+1)
            word_features = {}
            for i in range(3):
                if word_idx == len(sentence) - 1 and i == 2:
                    word_features['EOS'] = True
                    # End Of Sentence
                elif word_idx == 0 and i == 0:
                    word_features['BOS'] = True
                    # Beginning Of Sentence
                else:
                    word = sentence[word_idx - 1 + i]
                    prefix = prefixes[i]
                    features = self.crf_features[i]
                    for feature in features:
                        # append each feature to a feature vector
                        value = self.function_dict[feature](word)
                        word_features[prefix + ":" + feature] = value
            sentence_features.append(word_features)
        return sentence_features

    # NOTE: used for conditional random field training
    def _sentence_to_labels(self, sentence):
        # type: (List[Tuple[Text, Text, Text, Text]]) -> List[Text]

        return [label for _, _, label, _ in sentence]
