import click
from elasticsearch import BadRequestError
import spacy

from es_client import es_client

spacy_models = {
    'english': "en_core_web_sm"
}

@click.command()
@click.option('-i', '--index', help="Elasticsearch index name from which to request the training data", required=True)
@click.option('-f', '--field_name', help="The index field to process", default='text')
@click.option('-l', '--language', help='the language of the field', default='english')
def process_documents(index, field_name, language):
    es = es_client()
    add_annotated_field(es, index, field_name)
    documents = es.search(index=index)['hits']['hits']
    model  = spacy_models.get(language)
    nlp = spacy.load(model)
    for doc in documents:
        output = []
        parsed = nlp(doc['_source'][field_name])
        for token in parsed:
            if token.ent_type_:
                output.append('[{}]({})'.format(token.text, token.ent_type_))
            else:
                output.append(token.text)
        es.update(index=index, id=doc['_id'], doc={
            annotated_field_name(field_name): ' '.join(output)
        })


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
