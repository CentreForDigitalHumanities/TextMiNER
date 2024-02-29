import logging
import string

import click
from elasticsearch import BadRequestError
from flair.splitter import SegtokSentenceSplitter
from flair.models import SequenceTagger
from flair.embeddings import TransformerWordEmbeddings
from torch import nn
import torch

from es_client import es_client

logger = logging.getLogger(__name__)


def dutch_tagger():
    ''' The Dutch tokenizer was retrained after the Dutch NER model
    this results in index error due to different dimensions.
    This is a workaround until the time a new NER model has been trained
    '''
    tagger = SequenceTagger.load('flair/ner-dutch')
    embeddings = TransformerWordEmbeddings('GroNLP/bert-base-dutch-cased')
    new_embedding_tensor = torch.cat([tagger.embeddings.model.get_input_embeddings(
    ).weight, embeddings.model.get_input_embeddings().weight[tagger.embeddings.model.get_input_embeddings().num_embeddings:-1]])
    new_input_embeddings = nn.Embedding.from_pretrained(
        new_embedding_tensor, freeze=False)
    tagger.embeddings.model.set_input_embeddings(new_input_embeddings)
    tagger.embeddings.base_model_name = "GroNLP/bert-base-dutch-cased"
    tagger.save("ner-dutch-fixed.pt")
    return tagger

ner_models = {
    'english': SequenceTagger.load("flair/ner-english"),
    'dutch': dutch_tagger(),
}

@click.command()
@click.option('-i', '--index', help="Elasticsearch index name from which to request the training data", required=True)
@click.option('-f', '--field_name', help="The index field to process", default='text')
@click.option('-l', '--language', help='the language of the field', default='english')
def process_documents(index, field_name, language):
    es = es_client()
    add_annotated_field(es, index, field_name)
    documents = es.search(index=index, size=1000)['hits']['hits']
    tagger = ner_models.get(language)
    for doc in documents:
        output = ''
        document = doc['_source'][field_name]
        splitter = SegtokSentenceSplitter()
        sentences = splitter.split(document)
        for sentence in sentences:
            try:
                tagger.predict(sentence)
                output = parse_prediction(sentence, output) + ' '
            except:
                logger.warning(
                    'Failed to parse the following sentence: {}'.format(sentence))
        es.update(index=index, id=doc['_id'], doc={
            annotated_field_name(field_name): output[:-1]
        })


def parse_prediction(sentence, output):
    predicted = sentence.to_dict()
    tokens = predicted['tokens']
    for pos, token in enumerate(tokens):
        whitespace = '' if (
            pos == 0 or token['text'] in string.punctuation) else ' '
        # tokens have start_pos and end_pos, and so have entitites
        # entities may span multiple tokens
        entity = next(
            (ent for ent in predicted['entities'] if ent['end_pos'] > token['start_pos'] >= ent['start_pos']), None)
        if entity:
            if token['start_pos'] == entity['start_pos']:
                output += add_opening_tag(entity, whitespace)
            if token['end_pos'] == entity['end_pos']:
                output += add_closing_tag(entity)
        else:
            output += whitespace + token['text']
    return output


def add_opening_tag(entity, whitespace):
    return whitespace + '[' + entity['text']


def add_closing_tag(entity):
    return '](' + entity['labels'][0]['value'] + ')'


def annotated_field_name(field_name):
    return '{}_ner'.format(field_name)


def add_annotated_field(es_client, index_name, field_name):
    try:
        es_client.indices.put_mapping(
            index=index_name,
            properties={
                    annotated_field_name(field_name): {
                        'type': 'annotated_text'
                    }
                }
        )
    except BadRequestError:
        raise


if __name__ == '__main__':
    process_documents()
