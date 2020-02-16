FROM lambci/lambda:build-python3.6

COPY ./scrapers.zip /tmp/scrapers.zip

RUN unzip /tmp/scrapers.zip

RUN rm /tmp/scrapers.zip

CMD ["python", "get_events.py"]

