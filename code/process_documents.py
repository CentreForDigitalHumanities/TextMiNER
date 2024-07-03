import click
import logging
from os.path import join
import pickle
import string

from elasticsearch import BadRequestError
from flair.splitter import SegtokSentenceSplitter
from flair.models import SequenceTagger
from flair.embeddings import TransformerWordEmbeddings
from torch import nn
import torch

from es_client import es_client

logger = logging.getLogger(__name__)

SOURCE_DATA_DIR = './data'


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
    add_filter_fields(es, index)
    initial_search = es.search(index=index, size=1000, scroll='1m')
    if not initial_search:
        es.clear_scroll(scroll_id='_all')
    documents = initial_search['hits']['hits']
    n_documents = len(documents)
    scroll_id = initial_search['_scroll_id']
    total_hits = initial_search['hits']['total']['value']
    tagger = ner_models.get(language)
    annotate_entities(documents, field_name, tagger, es, index)
    while n_documents < total_hits:
        documents = es.scroll(scroll_id=scroll_id, scroll='60m')[
            'hits']['hits']
        annotate_entities(documents, field_name, tagger, es, index)


def annotate_entities(documents, field_name, tagger, es_client, index):
    for doc in documents:
        output = ''
        entities = []
        document = doc['_source'][field_name]
        splitter = SegtokSentenceSplitter()
        sentences = splitter.split(document)
        for sentence in sentences:
            try:
                tagger.predict(sentence)
                output = parse_prediction(sentence, output, entities) + ' '
            except:
                logger.warning(
                    'Failed to parse the following sentence: {}'.format(sentence))
        save_entity_labels(entities, index, doc['_id'])
        es_client.update(index=index, id=doc['_id'], doc={
            annotated_field_name(field_name): output[:-1],
            **create_filter_content(entities)
        })


def parse_prediction(sentence, output, entities):
    predicted = sentence.to_dict()
    entities.extend(predicted['entities'])
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


def create_filter_content(entities) -> dict:
    document_fields = {}
    for ent in entities:
        for field in filter_field_mappings().keys():
            if field in [label['value'] for label in ent['labels']]:
                document_fields.update(
                    {filter_field_mappings()[field]: ent['text']})
    return document_fields


def save_entity_labels(entities, index_name, identifier):
    with open(join(SOURCE_DATA_DIR, f'{index_name}.pkl'), 'rb') as f:
        pickle.dump({identifier: entities}, f)


def add_opening_tag(entity, whitespace):
    return whitespace + '[' + entity['text']


def add_closing_tag(entity):
    return '](' + entity['labels'][0]['value'] + ')'


def annotated_field_name(field_name):
    return '{}:ner'.format(field_name)


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


def filter_field_mappings():
    return {
        'PER': 'ner:person',
        'LOC': 'ner:location',
        'ORG': 'ner:organization',
        'MISC': 'ner:miscellaneous'
    }


def add_filter_fields(es_client, index_name):
    try:
        es_client.indices.put_mapping(
            index=index_name,
            properties={field_name: {'type': 'keyword'}
                        for field_name in filter_field_mappings().values()
                        }
        )
    except BadRequestError:
        raise


if __name__ == '__main__':
    process_documents()
