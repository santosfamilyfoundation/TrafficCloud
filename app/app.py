#!/usr/bin/env python

import logging
import atexit
import tornado.auth
import tornado.autoreload
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os
import matplotlib
matplotlib.use('Agg')

from tornado.options import define, options

import cleanup

# Import all of our custom routes

# Upload routes
from handlers.upload import UploadHandler
from handlers.uploadVideo import UploadVideoHandler
from handlers.homography import HomographyHandler

# Configure routes
from handlers.config import ConfigHandler
from handlers.testConfig import TestConfigHandler
from handlers.defaultConfig import DefaultConfigHandler

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
from handlers.createSpeedDistribution import CreateSpeedDistributionHandler
from handlers.retrieveResults import RetrieveResultsHandler
from handlers.createHighlightVideo import CreateHighlightVideoHandler


MB = 1024*1024
define("port", default=8888, help="run on the given port", type=int)
define("max_body_size", default=100*MB, help="max size of content body", type=int)
define("max_buffer_size", default=100*MB, help="max size loaded into memory", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/upload", UploadHandler),
            (r"/uploadVideo", UploadVideoHandler),
            (r"/homography", HomographyHandler),
            (r"/config", ConfigHandler),
            (r"/testConfig", TestConfigHandler),
            (r"/defaultConfig", DefaultConfigHandler),
            (r"/analysis", AnalysisHandler),
            (r"/objectTracking", ObjectTrackingHandler),
            (r"/safetyAnalysis", SafetyAnalysisHandler),
            (r"/status", StatusHandler),
            (r"/highlightVideo", CreateHighlightVideoHandler),
            (r"/makeReport", MakeReportHandler),
            (r"/roadUserCounts", RoadUserCountsHandler),
            (r"/speedDistribution", CreateSpeedDistributionHandler),
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

    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port,\
               max_body_size = options.max_body_size,\
               max_buffer_size = options.max_buffer_size)
    print('Listening on port '+str(options.port))
    print('Max Body Size {} MB'.format(options.max_body_size/(MB)))
    print('Max Buffer Size {} MB'.format(options.max_buffer_size/(MB)))
    ioloop = tornado.ioloop.IOLoop().instance()
    tornado.autoreload.start(ioloop)
    ioloop.start()

if __name__ == "__main__":
    # If we're just starting the program, there shouldn't be anything already
    # running, so we should clean up, just in case something went terribly
    # wrong last time
    cleanup.cleanup_func()

    # Register for cleanup_func to be called after program exit
    atexit.register(cleanup.cleanup_func)

    main()

