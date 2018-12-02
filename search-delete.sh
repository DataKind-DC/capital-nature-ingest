curl -XPOST ${ELASTICSEARCH_DOMAIN}/capital_nature/_delete_by_query \
-d '{
  "query": { 
    "match": {
      "ingested_by": "https://github.com/DataKind-DC/capital-nature-ingest/blob/master/melaniechoukas-bradley.py"
    }
  }
}' \
-H 'Content-Type: application/json'
