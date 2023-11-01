import os

ES_HOST = os.environ.get('ES_HOST', 'localhost')
ES_PORT = 9200
API_ID = os.environ.get('API_ID')
API_KEY = os.environ.get('API_KEY')
CERTS_LOCATION = os.environ.get('CERTS_LOCATION')
TEST_INDEX = 'some-test-index'
TEST_FIELD_NAME = 'text'
TEST_DOCUMENT_ID = 1