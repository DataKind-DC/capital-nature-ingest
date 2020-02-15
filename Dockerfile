FROM python:3.6
# ENV NPS_KEY="<Uncomment and insert NPS_KEY here>""
# ENV EVENTBRITE_TOKEN="<Uncomment and insert Eventbrite Token here>"
COPY . /home/
RUN pip install -r /home/requirements.txt
CMD [ "python" , "/home/get_events.py"]