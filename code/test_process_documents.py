import pytest

from process_documents import add_annotated_field
import settings

def test_add_annotated_field(mock_es_client):
    add_annotated_field(mock_es_client, settings.TEST_INDEX, settings.TEST_FIELD_NAME)
    new_mapping = mock_es_client.indices.get_mapping(index=[settings.TEST_INDEX])
    assert annotated_field_name() in new_mapping.get(settings.TEST_INDEX)['mappings']['properties']

def test_add_annotated_text(mock_es_client):
    add_annotated_field(mock_es_client, settings.TEST_INDEX, settings.TEST_FIELD_NAME)
    analysis = mock_es_client.indices.analyze(
        index=settings.TEST_INDEX,
        field=annotated_field_name(),
        text="[Mortimer](Person) is from [London](Place)"
    )
    assert analysis['tokens'][0]['token'] == 'Person'
    assert analysis['tokens'][0]['type'] == 'annotation'
    assert analysis['tokens'][1]['token'] == 'mortimer'
    assert analysis['tokens'][-2]['token'] == 'Place'
    assert analysis['tokens'][-2]['type'] == 'annotation'
    assert analysis['tokens'][-1]['token'] == 'london'

def test_search_annotated_text(mock_es_client):
    add_annotated_field(mock_es_client, settings.TEST_INDEX, settings.TEST_FIELD_NAME)
    mock_es_client.update(
        index=settings.TEST_INDEX,
        id=settings.TEST_DOCUMENT_ID,
        doc={
            annotated_field_name(): "[Mortimer](Person) is from [London](Place)"
        }
    )
    search_response = mock_es_client.search(
        index=settings.TEST_INDEX,
        query={
            "term": {
                annotated_field_name(): "Person" 
            }
        }
    )
    assert search_response['hits']['total']['value'] == 1

def annotated_field_name():
    return '{}_ner'.format(settings.TEST_FIELD_NAME)