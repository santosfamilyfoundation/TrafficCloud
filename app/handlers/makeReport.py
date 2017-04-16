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
    @apiDescription Calling this route will create a safety report for a specified project. The report is returned in the response body. This route requires running roadUserCounts and createSpeedDistribution to generate the report images.

    @apiParam {String} identifier The identifier of the project for which to create the report.

    @apiSuccess {File} report_pdf The API will return the created report upon success.

    @apiError error_message The error message to display.
    """
    def prepare(self):
        self.identifier = self.find_argument('identifier', str)
        self.project_exists(self.identifier)

    def get(self):
        
        if (not os.path.exists(os.path.join(project_dir,\
                                            'final_images',\
                                            'road_user_icon_counts.jpg'))):
            self.error_message = 'Road User Counts must be run before the report can be generated.'
            raise tornado.web.HTTPError(status_code=400)

        if (not os.path.exists(os.path.join(project_dir,\
                                            'final_images',\
                                            'velocityPDF.jpg'))):
            self.error_message = 'Speed Distribution must be run before the report can be generated.'
            raise tornado.web.HTTPError(status_code=400)

        status_code, reason = MakeReportHandler.handler(self.identifier)

        if status_code == 200:
            report_path = os.path.join(project_dir,\
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
