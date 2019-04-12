FROM python:3.7
RUN pip install facebook-sdk ics pytz

RUN mkdir /app
COPY get_events.py /app

WORKDIR /app
EXPOSE 8080
ENTRYPOINT ["python", "get_events.py"]

# Build the docker image
# docker build -t aupasana/veda-events .

# Run the docker image, passing in the access token
# docker run -e veda_facebook_key=[KEY] -p 8080:8080 aupasana/veda-events

# Dev: Run the image, mounting the sources and running bash
# docker run -e veda_facebook_key=[KEY] -it --entrypoint bash -v "%cd%:/src" -p 8080:8080 aupasana/veda-events