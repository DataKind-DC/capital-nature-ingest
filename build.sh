mkdir lambda-releases
mkdir temp && mkdir temp/utils && mkdir temp/events
rsync -av --exclude __pycache__ --progress events/ temp/events/ 
rsync -av --exclude __pycache__ --progress utils/ temp/utils/ 
cp get_events.py temp/get_events.py
cp log.py temp/log.py
cp requirements.txt temp/requirements.txt
cd temp
pip install -r requirements.txt -t .
zip -r ../lambda-releases/scrapers.zip .
cd ..
rm -rf temp/