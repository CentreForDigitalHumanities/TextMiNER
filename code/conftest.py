import pytest

from es_client import es_client
import settings

@pytest.fixture(scope='session')
def mock_es_client():
    """
    Initialise an elasticsearch client for the default elasticsearch cluster. Skip if no connection can be made.
    """

    client = es_client()
    client.indices.create(
        index=settings.TEST_INDEX,
        mappings={
            "properties": {
                settings.TEST_FIELD_NAME: {"type": "text"}
            }
        }
    )
    client.create(
        index=settings.TEST_INDEX,
        id=settings.TEST_DOCUMENT_ID,
        document={
            settings.TEST_FIELD_NAME: 'Mortimer is from London.'
        }
    )
    # check if client is available, else skip test
    try:
        client.info()
    except:
        pytest.skip('Cannot connect to elasticsearch server')

    yield client
    client.indices.delete(index=settings.TEST_INDEX)