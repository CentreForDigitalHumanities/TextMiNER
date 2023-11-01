# TextMiNER
TextMiNER is a collection of scripts to perform named entity recognition (NER) in text, using the Python library [spaCy](https://spacy.io/). The detected named entities are saved in an Elasticsearch [annotated-text](https://www.elastic.co/guide/en/elasticsearch/plugins/8.10/mapper-annotated-text.html) field.

## Requirements
- Python 3.8 or newer
- Elasticsearch 7 or newer
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