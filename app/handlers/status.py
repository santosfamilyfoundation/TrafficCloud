#!/usr/bin/env python

import tornado.web
from traffic_cloud_utils.statusHelper import StatusHelper
from baseHandler import BaseHandler

class StatusHandler(BaseHandler):

    """
    @api {get} /status/ Processing Status
    @apiName ProcessingStatus
    @apiVersion 0.1.0
    @apiGroup Status
    @apiDescription Calling this route will return the current status of any long-running processing that your project can perform, is performing or has performed. It returns a field for each possible long-running process whose value can be 0, 1 or 2. A status of 0 for a given field means that that type of processing has not been run on this project. A status of 1 means that that type of processing is currently running for this process. A status of 2 means that the type of processing has been completed for this project. You can poll this endpoint in order to know the status of processing so that you may call the next API call, such as returning results or performing subsequent analysis.

    @apiParam {String} identifier The identifier of the project on which to return status information.

    @apiSuccess {Integer} upload_homography The status of homography file uploading.
    @apiSuccess {Integer} configuration_test The status of the configuration test.
    @apiSuccess {Integer} object_tracking The status of object tracking.
    @apiSuccess {Integer} safety_analysis The status of performing safety analysis.
    @apiSuccess {Integer} highlight_video The status of creating the highlight video.

    @apiError error_message The error message to display. (Will return unique error message if object tracking has NOT been run on specified project)
    """
    def prepare(self):
        self.identifier = self.find_argument('identifier', str)
        self.project_exists(self.identifier)

    def get(self):
        status_dict = StatusHelper.get_status_raw(self.identifier)
        if status_dict != None:
        	self.write(status_dict)
        else:
            self.error_message = "Could not get project status"
            raise tornado.web.HTTPError(status_code = 500)
