export ELASTICSEARCH_DOMAIN=XXX
#curl -XDELETE ${ELASTICSEARCH_DOMAIN}/capital_nature

curl -XPUT ${ELASTICSEARCH_DOMAIN}/capital_nature \
-d '{
  "mappings": {
    "event": {
      "properties": {
        "geo": {
          "type": "geo_point"
        }
      }
    }
  }
}' \
-H 'Content-Type: application/json'
