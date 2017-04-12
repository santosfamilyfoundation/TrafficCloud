#!/usr/bin/env python

import os
import tornado.web
import tornado.escape

from traffic_cloud_utils.plotting.visualization import road_user_counts, road_user_icon_counts
from traffic_cloud_utils.app_config import get_project_path
from baseHandler import BaseHandler

#TODO(rlouie): replace with SantosBaseHandler class pip makes
class RoadUserCountsHandler(BaseHandler):
    """
    @api {post} /roadUserCounts/ Road User Counts
    @apiName RoadUserCounts
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a road user counts image from a specified project. When the image is created, an email will be sent to the project's user. This route requires running object tracking on the video, and then running safety analysis on the results of the object tracking beforehand. (Due to the potentially long duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project to create road user counts for.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def post(self):
        identifier = self.find_argument('identifier')
        status_code, reason = RoadUserCountsHandler.handler(identifier)
        print status_code
        print reason
        if status_code == 200:
            self.finish("Visualize Road User Counts")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    @staticmethod
    def handler(identifier):
        project_dir = get_project_path(identifier)
        if not os.path.exists(project_dir):
            return (500, 'Project directory does not exist. Check your identifier?')

        db = os.path.join(project_dir, 'run', 'results.sqlite')
        if not os.path.exists(db):
            return (500, 'Database file does not exist. Trajectory analysis needs to be called first ')

        final_images = os.path.join(project_dir, 'final_images')
        if not os.path.exists(final_images):
            os.mkdir(final_images)

        try:
            counts = road_user_counts(db)
        except Exception as err_msg:
            return (500, err_msg)

        try:
            road_user_icon_counts('Road User Counts',
                car=counts['car'],
                bike=counts['bicycle'],
                pedestrian=counts['pedestrian'],
                save_path=os.path.join(final_images, 'road_user_icon_counts.jpg'))
        except Exception as err_msg:
            return (500, err_msg)

        return (200, "Success")
