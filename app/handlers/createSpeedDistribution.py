#!/usr/bin/env python

import os
import tornado.web
from baseHandler import BaseHandler
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path
from traffic_cloud_utils.video import get_framerate
from traffic_cloud_utils.plotting.visualization import vel_distribution

import json
import traceback

class CreateSpeedDistributionHandler(BaseHandler):
    """
    @api {get} /speedDistribution/ Speed Distribution
    @apiName SpeedDistribution
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a graph of the speed distribution from a specified project.
    @apiParam {String} identifier The identifier of the project to create a speed distribution for.
    @apiParam {Integer} [speed_limit] speed limit of the intersection. Defaults to 25 mph.
    @apiParam {Boolean} [vehicle_only] Flag for specifying only vehicle speeds

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def get(self):
        identifier = self.find_argument('identifier')
        vehicle_only = bool(self.find_argument('vehicle_only', default=True))
        speed_limit = int(self.find_argument('speed_limit', default=25))
        status_code, reason = CreateSpeedDistributionHandler.handler(identifier, speed_limit, vehicle_only)
        if status_code == 200:
            image_path = os.path.join(\
                                    get_project_path(identifier),\
                                    'final_images',\
                                    'velocityPDF.jpg')
            self.set_header('Content-Disposition',\
                            'attachment; filename=velocityPDF.jpg')
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Description', 'File Transfer')
            self.write_file_stream(image_path)
            self.finish("Create Speed Distribution")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    @staticmethod
    def handler(identifier, speed_limit, vehicle_only):
        project_dir = get_project_path(identifier)
        if not os.path.exists(project_dir):
            return (500, 'Project directory does not exist. Check your identifier?')

        db = os.path.join(project_dir, 'run', 'results.sqlite')
        if not os.path.exists(db):
            return (500, 'Database file does not exist. Trajectory analysis needs to be called first ')

        final_images = os.path.join(project_dir, 'final_images')
        if not os.path.exists(final_images):
            os.mkdir(final_images)

        video_path = get_project_video_path(identifier)
        if not os.path.exists(video_path):
            return (500, 'Source video file does not exist.  Was the video uploaded?')

        vel_distribution(db, float(get_framerate(video_path)), speed_limit, final_images, vehicle_only)

        return (200, "Success")
