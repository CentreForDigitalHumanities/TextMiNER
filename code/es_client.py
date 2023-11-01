from elasticsearch import Elasticsearch

from settings import *

def es_client():
    node = {'host': ES_HOST,
        'port': ES_PORT,
    }
    kwargs = {
        'max_retries': 15,
        'retry_on_timeout': True,
        'request_timeout': 180
    }
    if API_ID and API_KEY and CERTS_LOCATION:
        node['scheme'] = 'https'
        kwargs['ca_certs'] = CERTS_LOCATION
        kwargs['api_key'] = (API_ID, API_KEY)
    else:
        node['scheme'] = 'http'
    return Elasticsearch([node], **kwargs)