#! python
import facebook, os, pytz, socketserver
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from ics import Calendar, Event

utc = pytz.UTC

access_token = os.environ['veda_facebook_key']
if access_token == '':
    print ("pass in veda_facebook_key as a docker secret")
    quit()

class facebook_events_to_ical:

    def __init__ (self, facebook_page_name):
        self.facebook_page_name = facebook_page_name

    def format_date(self, dt):
        return dt.strftime('%b %d %Y @ %H:%M')

    def get_facebook_event_property(self, event, property, default_value):
        try:
            return event[property]
        except:
            return default_value

    def get_ical(self):

        graph = facebook.GraphAPI(access_token=access_token, version="2.12")
        events = graph.request('/v3.2/%s/events' % self.facebook_page_name)
        eventList = events['data']

        # print ("Returned %d events" % len(eventList))
        # print (eventList)

        ical = Calendar()

        for e in eventList:
            start_time = datetime.strptime(e['start_time'], "%Y-%m-%dT%H:%M:%S%z" )

            try:
                if start_time <= utc.localize((datetime.now() - timedelta(days=1))):
                    pass
                else:
                    end_time = datetime.strptime(e['end_time'], "%Y-%m-%dT%H:%M:%S%z" )

                    ical_event = Event()
                    ical_event.name = self.get_facebook_event_property(e, 'name', '[Some Event]')
                    ical_event.begin = start_time
                    ical_event.end = end_time
                    ical_event.uid = self.get_facebook_event_property(e, 'id', '')
                    ical_event.url = 'https://www.facebook.com/events/%s' % self.get_facebook_event_property(e, 'id', '')
                    ical_event.description = '%s\n\n%s' % (ical_event.url, self.get_facebook_event_property(e, 'description', ''))

                    # print (ical_event)

                    ical.events.add(ical_event)
            except:
                raise
                # pass

        return ical


class iCalServer_RequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
        self.send_response(200)
 
        self.send_header('Content-type','text/calendar')
        self.end_headers()
 
        ical = facebook_events_to_ical('vedatemple').get_ical()
        self.wfile.write(bytes(str(ical), "utf8"))
        return

# ical = facebook_events_to_ical('vedatemple').get_ical()
# print (ical)

PORT = 8080
with socketserver.TCPServer(("", PORT), iCalServer_RequestHandler) as httpd:
    # print("serving at port", PORT)
    httpd.serve_forever()