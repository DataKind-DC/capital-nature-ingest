mkdir lambda-releases
rm lambda-releases/scrapers.zip
mkdir temp && mkdir temp/events && mkdir temp/tests
rsync -av --exclude __pycache__ --progress events/ temp/events/
cp tests/utils.py temp/tests/utils.py
cp get_events.py temp/get_events.py
cp lambda-requirements.txt temp/lambda-requirements.txt
cd temp
pip install -r lambda-requirements.txt -t .
# add pandas and numpy
bsdtar -xf ../layer/aws-lambda-py3.6-pandas-numpy.zip -s'|[^/]*/||'
rm -r *.dist-info __pycache__
# zip it all up
zip -r ../lambda-releases/scrapers.zip .
# clean up
cd ..
rm -rf temp/