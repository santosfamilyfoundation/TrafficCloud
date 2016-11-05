#!/usr/bin/env python

import logging
import tornado.auth
import tornado.autoreload
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import auth

from tornado.options import define, options

# Import all of our custom routes
from handlers.upload import UploadHandler
from handlers.testFeatureTracking import TestFeatureTrackingHandler
from handlers.testObjectTracking import TestObjectTrackingHandler
from handlers.trajectoryAnalysis import TrajectoryAnalysisHandler
from handlers.safetyAnalysis import SafetyAnalysisHandler
from handlers.trajectoryAnalysisStatus import TrajectoryAnalysisStatusHandler
from handlers.safetyAnalysisStatus import SafetyAnalysisStatusHandler

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/upload", UploadHandler),
            (r"/test/featureTracking", TestFeatureTrackingHandler),
            (r"/test/objectTracking", TestObjectTrackingHandler),
            (r"/trajectoryAnalysis", TrajectoryAnalysisHandler),
            (r"/safetyAnalysis", SafetyAnalysisHandler),
            (r"/trajectoryAnalysis/status", SafetyAnalysisHandler),
            (r"/safetyAnalysis/status", SafetyAnalysisHandler),
        ]
        settings = dict(
            cookie_secret=auth.secret,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    ioloop = tornado.ioloop.IOLoop().instance()
    tornado.autoreload.start(ioloop)
    ioloop.start()

if __name__ == "__main__":
    main()
