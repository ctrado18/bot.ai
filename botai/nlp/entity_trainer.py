import random

from pathlib import Path
from spacy.gold import GoldParse

from botai.db.in_memory import InMemoryDb
from botai.nlp.english import English

learn_rate = 0.001
iterations = 1000


class EntityTrainer(object):
    def __init__(self, output_directory=Path('trained_model')):
        self.nlp = English.instance().nlp
        self.output_directory = output_directory
        self.db = InMemoryDb.instance()

    def train(self, expressions):
        entities = [(entity, expression.text) for expression in expressions for entity in expression.entities]
        pos_entities = filter(lambda e: e[0].type != 'intent', entities)
        unique_labels = list(set([entity[0].type for entity in pos_entities]))
        for label in unique_labels:
            self.nlp.entity.add_label(label)
        self.__train_ner(pos_entities)
        print('Entity recognizer trained')

    def __train_ner(self, pos_entities):
        self.__add_words_to_vocab(pos_entities)
        self.nlp.entity.model.learn_rate = learn_rate
        for itn in range(iterations):
            random.shuffle(pos_entities)
            loss = 0.
            for entity, text in pos_entities:
                doc = self.nlp.make_doc(text)
                gold = GoldParse(doc, entities=[(entity.start, entity.end, entity.type)])
                self.nlp.tagger(doc)
                loss += self.nlp.entity.update(doc, gold)
            if loss == 0:
                break
        self.nlp.end_training()
        if not self.output_directory:
            self.output_directory.mkdir()
        self.nlp.save_to_directory(self.output_directory)

    def __add_words_to_vocab(self, pos_entities):
        docs = [self.nlp.make_doc(entity.text) for entity, _ in pos_entities]
        _ = [self.nlp.vocab[word.orth] for doc in docs for word in doc]
