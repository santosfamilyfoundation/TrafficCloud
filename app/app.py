#!/usr/bin/env python

import logging
import tornado.auth
import tornado.autoreload
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os

from tornado.options import define, options

# Import all of our custom routes

# Upload routes
from handlers.upload import UploadHandler
from handlers.uploadVideo import UploadVideoHandler
from handlers.uploadHomography import UploadHomographyHandler

# Configure routes
from handlers.config import ConfigHandler
from handlers.testConfig import TestConfigHandler

# Analysis routes
from handlers.analysis import AnalysisHandler
from handlers.objectTracking import ObjectTrackingHandler
from handlers.safetyAnalysis import SafetyAnalysisHandler

#Status Routes
from handlers.status import StatusHandler

# Results routes
from handlers.createHighlightVideo import CreateHighlightVideoHandler
from handlers.makeReport import MakeReportHandler
from handlers.roadUserCounts import RoadUserCountsHandler
from handlers.createSpeedCDF import CreateSpeedCDFHandler
from handlers.retrieveResults import RetrieveResultsHandler
from handlers.createHighlightVideo import CreateHighlightVideoHandler

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/upload", UploadHandler),
            (r"/uploadVideo", UploadVideoHandler),
            (r"/uploadHomography", UploadHomographyHandler),
            (r"/config", ConfigHandler),
            (r"/testConfig", TestConfigHandler),
            (r"/analysis", AnalysisHandler),
            (r"/objectTracking", ObjectTrackingHandler),
            (r"/safetyAnalysis", SafetyAnalysisHandler),
            (r"/status", StatusHandler),
            (r"/highlightVideo", CreateHighlightVideoHandler),
            (r"/makeReport", MakeReportHandler),
            (r"/roadUserCounts", RoadUserCountsHandler),
            (r"/speedCDF", CreateSpeedCDFHandler),
            (r"/retrieveResults", RetrieveResultsHandler)

        ]
        settings = dict(
            cookie_secret=os.environ.get('SANTOSCLOUD_SECRET_KEY'),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

def main():
    keys = ['SANTOSCLOUD_SECRET_KEY', 'SANTOSCLOUD_EMAIL', 'SANTOSCLOUD_EMAIL_PASSWORD']
    for key in keys:
        if os.environ.get(key) == None:
            print("Set the "+key+" environment variable")
            return

    if os.environ.get('SANTOSCLOUD_SECRET_KEY') == "DefaultSecretKey":
        print('WARNING: You are using the default secret key. This is insecure! Please create a secret key and set it on the SANTOSCLOUD_SECRET_KEY environment variable.')
    if os.environ.get('SANTOSCLOUD_EMAIL') == '' or os.environ.get('SANTOSCLOUD_EMAIL_PASSWORD') == '':
        print("WARNING: Running without email capabilities. Users won't be emailed when their processing completes. To fix this, set the SANTOSCLOUD_EMAIL and SANTOSCLOUD_EMAIL_PASSWORD environment variables.")

    if not os.path.exists(os.path.join(os.path.dirname(__file__),'..','.temp')):
        os.mkdir(os.path.join(os.path.dirname(__file__),'..','.temp'))
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port, max_buffer_size = (int)(1024*1024*1024*1.25))
    print('Listening on port '+str(options.port))
    ioloop = tornado.ioloop.IOLoop().instance()
    tornado.autoreload.start(ioloop)
    ioloop.start()

if __name__ == "__main__":
    main()
