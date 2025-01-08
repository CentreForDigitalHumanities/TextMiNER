import re

from flair.data import Sentence
from flair.models import SequenceTagger

from process_documents import (
    add_annotated_field,
    add_filter_fields,
    dutch_tagger,
    filter_field_mappings,
    parse_prediction,
)
import settings

def test_add_annotated_field(mock_es_client):
    add_annotated_field(mock_es_client, settings.TEST_INDEX, settings.TEST_FIELD_NAME)
    mapping = mock_es_client.indices.get_mapping(index=settings.TEST_INDEX)[
        settings.TEST_INDEX
    ]['mappings']
    assert settings.TEST_FIELD_NAME in mapping['properties']


def test_add_filter_fields(mock_es_client):
    add_filter_fields(mock_es_client, settings.TEST_INDEX)
    mapping = mock_es_client.indices.get_mapping(index=settings.TEST_INDEX)[
        settings.TEST_INDEX
    ]['mappings']
    for field in filter_field_mappings.values():
        assert field in mapping['properties']


def annotated_field_name():
    return '{}:ner'.format(settings.TEST_FIELD_NAME)

def test_parse_prediction():
    test_sentence = Sentence('Wally was last seen in the Bermuda Triangle.')
    tagger = SequenceTagger.load('flair/ner-english')
    tagger.predict(test_sentence)
    output, entities = parse_prediction(test_sentence)
    assert output == '[Wally](PER) was last seen in the [Bermuda Triangle](LOC).'
    assert len(entities) == 2

def test_list_of_names():
    test_sentence = Sentence(
        'Voor hebben gestemd de heeren: Merkes van Gendt, de Sitter, du Marchie van Voorthuysen en de Voorzitter.')
    tagger = dutch_tagger()
    tagger.predict(test_sentence)
    output, _entities = parse_prediction(test_sentence)
    pattern = re.compile(r'\[\w+\]\(PER\)')
    assert len(pattern.findall(output)) == 4
