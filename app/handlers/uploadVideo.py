#!/usr/bin/env python

import tornado.web
from tornado.web import stream_request_body
from traffic_cloud_utils.pm import create_project
from traffic_cloud_utils.app_config import get_project_path
from baseHandler import BaseHandler

from uuid import uuid4
import os

from multipart_streamer import MultiPartStreamer

@stream_request_body
class UploadVideoHandler(BaseHandler):
    """
    @api {post} /uploadVideo/ Upload Video
    @apiName UploadVideo
    @apiVersion 0.2.0
    @apiGroup Upload
    @apiDescription This route will create a new project and upload a video to it.

    @apiParam {File} video The video file to analyze. This can have any file extension.
    
    @apiSuccess {String} identifier The project identifier. This will be used to reference the project in all other requests.

    @apiError error_message The error message to display.
    """
    def prepare(self):
        if self.request.method.lower() == "post":
            # Set this request's max_body_size to 20 GB
            self.request.connection.set_max_body_size(20*self.GB)
        try:
            total = int(self.request.headers.get("Content-Length","0"))
        except KeyError:
            total = 0
        self.ps = MultiPartStreamer(total)
        print 'Upload Video Prepared'

    def data_received(self, chunk):
        self.ps.data_received(chunk)

    def post(self):
        self.identifier = None
        try:
            self.ps.data_complete()
            # If multiple files called "video" are sent, we pick the first one
            video_part = self.ps.get_parts_by_name("video")[0]

            if video_part:
                self.identifier = str(uuid4())
                create_project(self.identifier, video_part)
            else:
                print "video_part was None"
                self.error_message = "Error decoding video upload"
                raise tornado.web.HTTPError(status_code = 400)

        except Exception as e:
            print "could not complete streaming of data parts"
            self.error_message = "Error uploading video: " + str(e)
            raise tornado.web.HTTPError(status_code = 400)

        finally:
            self.ps.release_parts()
            if self.identifier:
                self.write({'identifier': self.identifier})
            self.finish()
