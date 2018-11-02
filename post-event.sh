export ELASTICSEARCH_DOMAIN=XXX
curl -XPUT ${ELASTICSEARCH_DOMAIN}/capital_nature/event/1 \
  -d @./casey-trees-20181006.json \
  -H 'Content-Type: application/json'
