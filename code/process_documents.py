import click
from elasticsearch import BadRequestError
from flair.splitter import SegtokSentenceSplitter
from flair.models import SequenceTagger

from es_client import es_client

ner_models = {
    'english': "flair/ner",
    'dutch': "flair/ner-dutch",
}

@click.command()
@click.option('-i', '--index', help="Elasticsearch index name from which to request the training data", required=True)
@click.option('-f', '--field_name', help="The index field to process", default='text')
@click.option('-l', '--language', help='the language of the field', default='english')
def process_documents(index, field_name, language):
    es = es_client()
    add_annotated_field(es, index, field_name)
    documents = es.search(index=index)['hits']['hits']
    model = ner_models.get(language)
    tagger = SequenceTagger.load(model)
    for doc in documents:
        output = ''
        document = doc['_source'][field_name]
        splitter = SegtokSentenceSplitter()
        sentences = splitter(document)
        for sentence in sentences:
            tagger.predict(sentence)
            predicted = sentence.to_dict()
            for token in predicted['tokens']:
                # tokens have start_pos and end_pos, and so have entitites
                # entities may span multiple tokens
                label = next(
                    (ent for ent in predicted['labels'] if ent['end_pos'] > token['start_pos'] >= token['start_pos']), None)
                if label:
                    output += add_opening_tag(token)
                    if token['end_pos'] == label['end_pos']:
                        output += add_closing_tag(label)
                    else:
                        continue
                else:
                    output += token['text']
        es.update(index=index, id=doc['_id'], doc={
            annotated_field_name(field_name): output
        })


def add_opening_tag(token):
    return '[' + token['text']


def add_closing_tag(label):
    return '](' + label['value'] + ')'


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
