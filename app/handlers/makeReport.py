#!/usr/bin/env python

import os
import tornado.web
from traffic_cloud_utils.pdf_generate import makePdf
from traffic_cloud_utils.app_config import get_project_path

from baseHandler import BaseHandler

class MakeReportHandler(BaseHandler):
    """
    @api {get} /makeReport/ Make Report
    @apiName MakeReport
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a safety report for a specified project. When the report is created, an email will be sent to the project's user. This route requires running object tracking on the video, and then running safety analysis on the results of the object tracking beforehand. (Due to the potentially long duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project for which to create the report.
    @apiParam {Boolean} [regenerate] A boolean identifying whether the user counts image should be recreated.
    @apiParam {Integer} [speed_limit] speed limit of the intersection. Defaults to 25 mph.
    @apiParam {Boolean} [vehicle_only] Flag for specifying only vehicle speeds
    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def get(self):
        identifier = self.find_argument('identifier')
        regen_flag = bool(self.find_argument('regenerate', default=False))
        status_code = 200
        if regen_flag:
            vehicle_only = bool(self.find_argument('vehicle_only', default=True))
            speed_limit = int(self.find_argument('speed_limit', default=25))
            status_code, reason = CreateSpeedDistributionHandler.handler(identifier, speed_limit, vehicle_only)
            if status_code==200:
                status_code, reason = RoadUserCountsHandler.handler(identifier)
            if status_code==200:
                status_code, reason = MakeReportHandler.handler(identifier)
        if status_code == 200:
            report_path = os.path.join(\
                                    get_project_path(identifier),\
                                    'santosreport.pdf')
            self.set_header('Content-Disposition',\
                            'attachment; filename=santosreport.pdf')
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Description', 'File Transfer')
            self.write_file_stream(report_path)
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
