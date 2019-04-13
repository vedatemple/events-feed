# events-feed

Simple dockerized web app to output the vedatemple facebook events as an ical calendar

# one-time run

`docker run -e veda_facebook_key=$KEY -e dev=true aupasana/veda-events > events.ics`

# setup a web server exposing a web feed at / on port 80

`docker run -e veda_facebook_key=$KEY -p 80:8080 aupasana/veda-events`
