#!/usr/bin/env python

import os
import tornado.web
from baseHandler import BaseHandler
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path
from traffic_cloud_utils.video import get_framerate
from traffic_cloud_utils.plotting.visualization import vel_cdf

import json
import traceback

class CreateSpeedCDFHandler(BaseHandler):
    """
    @api {post} /speedCDF/ Speed CDF
    @apiName SpeedCDF
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a graph of the speed CDF's from a specified project.

    @apiParam {String} identifier The identifier of the project to create a speed CDF for.
    @apiParam {Integer} [speed_limit] speed limit of the intersection. Defaults to 25 mph.
    @apiParam {Boolean} [vehicle_only] Flag for specifying only vehicle speeds

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def post(self):
        identifier = self.get_body_argument('identifier')
        speed_limit = int(self.get_body_argument('speed_limit', default=25))
        vehicle_only = bool(self.get_body_argument('vehicle_only', default=True))
        status_code, reason = CreateSpeedCDFHandler.handler(identifier, speed_limit, vehicle_only)
        if status_code == 200:
            self.finish("Create Speed CDF")
        else:
            raise tornado.web.HTTPError(reason=reason, status_code=status_code)

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

        vel_cdf(db, float(get_framerate(video_path)), speed_limit, final_images, vehicle_only)

        return (200, "Success")
