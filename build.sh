mkdir lambda-releases && mkdir temp && mkdir temp/utils
rsync -av --progress events/ temp/
rsync -av --progress utils/ temp/utils/
cp get_events.py temp/get_events.py
cp log.py temp/log.py
cp requirements.txt temp/requirements.txt
cd temp
pip install -r requirements.txt -t .
zip -r ../lambda-releases/scrapers.zip .
cd ..
rm -rf temp/