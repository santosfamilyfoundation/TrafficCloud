#!/usr/bin/env python

import os
import tornado.web
from traffic_cloud_utils.pdf_generate import makePdf
from traffic_cloud_utils.app_config import get_project_path

from baseHandler import BaseHandler

class MakeReportHandler(BaseHandler):
    """
    @api {post} /makeReport/ Make Report
    @apiName MakeReport
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a safety report for a specified project. When the report is created, an email will be sent to the project's user. This route requires running object tracking on the video, and then running safety analysis on the results of the object tracking beforehand. (Due to the potentially long duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project for which to create the report.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def post(self):
        identifier = self.find_argument('identifier')
        status_code, reason = MakeReportHandler.handler(identifier)
        if status_code == 200:
            self.finish("Make PDF Report")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    @staticmethod
    def handler(identifier):
        project_dir = get_project_path(identifier)
        if not os.path.exists(project_dir):
            return (500, 'Project directory does not exist. Check your identifier?')

        final_images = os.path.join(project_dir, 'final_images')
        if not os.path.exists(final_images):
            os.mkdir(final_images)

        report_path = os.path.join(project_dir, 'santosreport.pdf')

        # Hardcoded image file name order, so that the ordering of visuals in the report is consistent
        image_fns = [
            os.path.join(final_images, 'road_user_icon_counts.jpg'),
            os.path.join(final_images, 'velocityPDF.jpg')
        ]

        makePdf(report_path, image_fns, final_images)

        return (200, 'Success')
