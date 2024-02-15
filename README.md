# TextMiNER
TextMiNER is a collection of scripts to perform named entity recognition (NER) in text, using the Python library [spaCy](https://spacy.io/). The detected named entities are saved in an Elasticsearch [annotated-text](https://www.elastic.co/guide/en/elasticsearch/plugins/8.10/mapper-annotated-text.html) field.

## Requirements
- Python 3.10 or newer
- Elasticsearch 8 or newer
- Elasticsearch's annotated-field plugin. To install, run:
```
sudo bin/elasticsearch-plugin install mapper-annotated-text
```

## Docker
This repository contains Docker images and a `docker-compose` file for runnig and testing the scripts locally. `docker-compose` requires an `.env` file, to be created next to `docker-compose.yaml`, with the following values:
```
ES_HOST=elasticsearch
ELASTIC_ROOT_PASSWORD={password-of-your-choice}
```

## Usage
### Environment
Before running the script, define your environment variables to set correct values for `ES_HOST` if you don't run Elasticsearch on localhost, and `API_ID`, `API_KEY` and `CERTS_LOCATION`, if you access an Elasticsearch cluster using an API key.

### SpaCy models
Make sure you have the required SpaCy models for NER analysis by running
```
python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
```

### Run the script (without Docker)
To analyze data from an Elasticsearch index with SpaCy, and save this data back into an annotated field, change to the `code` directory (`cd code`) and then run the following command:
`python process_documents.py -i {index_name} -f {field_name} -l {language}`

To run this for an English language corpus indexed as "test", which has text data saved in field "content", you could run
`python process_documents.py -i test -f content -l english`

### Run the script locally (with Docker)
Altenatively, running with Docker, without changing to `code` first, run
`docker-compose run --rm backend python process_documents.py -i {index_name} -f {field_name} -l {language}`
