#! python
import facebook, os, pytz, socketserver, urllib
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from ics import Calendar, Event
from copy import deepcopy

utc = pytz.UTC

access_token = os.environ['veda_facebook_key']
if access_token == '':
    print ("pass in veda_facebook_key as a docker secret")
    quit()

class facebook_events_to_ical:

    def __init__ (self, facebook_page_name):
        self.facebook_page_name = facebook_page_name
        self.page_number = 0
        self.max_pages = 5

        self.filter_begin = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=-3)
        self.filter_end = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=60)

    def format_date(self, dt):
        return dt.strftime('%b %d %Y @ %H:%M')

    def get_facebook_event_property(self, event, property, default_value):
        try:
            return event[property]
        except:
            return default_value

    def explode_event(self, event):
        try:
            DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
            for event_time in event['event_times']:
                start_time = datetime.strptime(
                    event_time['start_time'],
                    DATETIME_FORMAT,
                )
                end_time = datetime.strptime(
                    event_time['end_time'],
                    DATETIME_FORMAT,
                )

                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                if start_time >= now:
                    this_event = deepcopy(event)
                    del this_event['event_times']
                    this_event.update(event_time)
                    yield this_event

            yield event

        # Yield single event
        except KeyError:
            yield event

    def get_facebook_events(self, **args):
        self.page_number = self.page_number + 1
        if self.page_number >= self.max_pages:
            return

        graph = facebook.GraphAPI(access_token=access_token, version="2.12")

        path = '%s/events' % self.facebook_page_name
        params = urllib.parse.urlencode(args)

        print('GET /%s?%s', path, params)

        events = graph.get_object(path, **args)
        eventList = events['data']

        for e in eventList:
            yield e

        try:
            args.update(after=events['paging']['cursors']['after'])
            yield from self.get_facebook_events(**args)
        except KeyError:
            pass

    def get_facebook_events_exploded(self, eventList):
        for event in eventList:
            yield from self.explode_event(event)

    def get_filtered_events(self, eventList):
        for e in eventList:
            DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            start_time = datetime.strptime(
                        e['start_time'],
                        DATETIME_FORMAT,
                    )
            if start_time >= self.filter_begin and start_time <= self.filter_end:
                yield e

    def get_ical_event(self, e):
        ical_event = Event()
        ical_event.name = self.get_facebook_event_property(e, 'name', '[Some Event]')
        ical_event.begin = self.get_facebook_event_property(e, 'start_time', '')
        ical_event.end = self.get_facebook_event_property(e, 'end_time', '')
        ical_event.uid = self.get_facebook_event_property(e, 'id', '')
        ical_event.url = 'https://www.facebook.com/events/%s' % self.get_facebook_event_property(e, 'id', '')
        ical_event.description = '%s\n\n%s' % (ical_event.url, self.get_facebook_event_property(e, 'description', ''))
        return ical_event

    def get_ical_calendar(self):
        eventList = self.get_facebook_events()
        events_exploded = self.get_facebook_events_exploded(eventList)
        events_filtered = self.get_filtered_events(events_exploded)

        ical = Calendar()
        for e in events_filtered:
            ical_event = self.get_ical_event(e)
            ical.events.add(ical_event)

        return ical

class iCalServer_RequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
        self.send_response(200)
 
        self.send_header('Content-type','text/calendar')
        self.end_headers()
 
        ical = facebook_events_to_ical('vedatemple').get_ical_calendar()
        self.wfile.write(bytes(str(ical), "utf8"))
        return

if os.environ.get('dev'):
    ical = facebook_events_to_ical('vedatemple').get_ical_calendar()
    print (ical)
else:
    PORT = 8080
    with socketserver.TCPServer(("", PORT), iCalServer_RequestHandler) as httpd:
        httpd.serve_forever()
