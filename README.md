# capital-nature-ingest

Repository to store scripts for ingesting data for Capital Nature.

## What is Capital Nature?

New regional nonprofit that wants to highlight all the great nature events and experiences happening in the area.

## Getting started with ingest

```bash
pip install -r requirements.txt --user
```

### Casey Trees

```bash
export ELASTICSEARCH_DOMAIN=XXX
# At time of this writing this script just posts one event to elasticsearch.
python ingest_scripts/casey_trees.py
```
