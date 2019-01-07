clean:
	rm -rf dist

dist:
	mkdir -p dist

requirements: dist requirements.txt
	pip install -r requirements.txt --target ./dist/ --no-cache-dir
	find ./dist -type d -name '__pycache__' | xargs rm -rf
	rm -rf dist/docutils

lambda: requirements
	cp lambda_function.py ./dist/
	cd dist && zip -r9 ../lambda.zip .
