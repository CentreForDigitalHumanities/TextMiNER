import click
from es_client import es_client

@click.command()
@click.option('-i', '--index', help="Elasticsearch index name from which to request the training data", required=True)
@click.option('-f', '--field_name', help="The index field to process", default='text')
def process_documents(index, field_name):
    es = es_client()
    add_annotated_field(es, index, field_name)

def add_annotated_field(es_client, index_name, field_name):
    es_client.indices.put_mapping(
        index=index_name,
        properties={
                '{}_ner'.format(field_name): {
                    'type': 'annotated_text'
                }
            }
    )

    

