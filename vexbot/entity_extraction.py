import sklearn_crfsuite
import spacy


class EntityExtraction:
    # Pretrained (spaCy)
    # Places, dates, people, organizations -> averaged preceptron

    # Pretrained (duckling)
    # Dates, Amounts of Money, Druations, Distances, Ordinals -> context-free grammer

    # Custom, Domain-specific entities -> conditional random field
    # MITIE, provides structured SVM
    def __init__(self):
        values = {'algorithm': 'lbfgs',
                  # coefficient for L1 penalty
                  'c1': 1,
                  # coefficient for L2 penalty
                  'c2': 1e-3,
                  'max_iterations': 50,
                  # include transitions that are possible, but not observed
                  'all_possible_transitions': True}

        self.ent_tagger = sklearn_crfsuite.CRF(**values)
        self.duckling = DucklingWrapper()

    def train(self, data):
        # _sentence_to_features
        x_train = []
        # _sentence_to_labels
        y_train = []

        self.ent_tagger.fit(x_train, y_train)

    def get_spacy(self, data):
        # NOTE: spaCy doc
        doc = data.get('doc')

	entities = [{"entity": ent.label_,
                     "value": ent.text,
                     "start": ent.start_char,
                     "end": ent.end_char} for ent in doc.ents]

        return entities

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

    def _sentence_to_labels(self, sentence):
        # type: (List[Tuple[Text, Text, Text, Text]]) -> List[Text]

        return [label for _, _, label, _ in sentence]
