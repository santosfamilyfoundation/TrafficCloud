#!/usr/bin/env python

import os
import tornado.web
import tornado.escape
from traffic_cloud_utils.video import create_highlight_video, get_framerate
from storage import alterInteractionsWithRoadUserType, getNearMissFrames
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path
import baseHandler

# TODO: remove once pip's error request handler is written
class CreateHighlightVideoHandler(baseHandler.BaseHandler):
    """
    @api {post} /highlightVideo/ Highlight Video
    @apiName HighlightVideo
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a highlight video of dangerous interactions from a specified project. When the video is created, an email will be sent to the project's user. This route requires running object tracking on the video, and then running safety analysis on the results of the object tracking beforehand. (Due to the potentially long duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project to create a highlight video for.
    @apiParam {Float} [ttc_threshold] Threshold for determining whether an interaction is dangerous. Default 1.5 seconds.
    @apiParam {Integer} [vehicle_only] Flag for specifying only vehicle-vehicle interactions. Default to True.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def post(self):
        identifier = self.get_body_argument('identifier')
        ttc_threshold = float(self.get_body_argument('ttc_threshold', default=1.5))
        vehicle_only = bool(self.get_body_argument('vehicle_only', default=True))

        status_code, reason = CreateHighlightVideoHandler.handler(identifier, ttc_threshold, vehicle_only)
        if status_code == 200:
            self.finish("Create Highlight Video")
        else:
            raise tornado.web.HTTPError(reason=reason, status_code=status_code)

    @staticmethod
    def handler(identifier, ttc_threshold, vehicle_only):
        project_dir = get_project_path(identifier)
        if not os.path.exists(project_dir):
            return (500, 'Project directory does not exist. Check your identifier?')

        db = os.path.join(project_dir, 'run', 'results.sqlite')
        #TO-DO: Check to see if tables like "interactions" exist
        if not os.path.exists(db):
            return (500, 'Database file does not exist. Trajectory analysis needs to be called first ')

        video_path = get_project_video_path(identifier)
        if not os.path.exists(video_path):
            return (500, 'Source video file does not exist.  Was the video uploaded?')

        try:
            alterInteractionsWithRoadUserType(db)
        except Exception as error_message:
            return (500, "Alter Interactions Table with Road User Type failed\n" + error_message)

        ttc_threshold_frames = int(ttc_threshold * float(get_framerate(video_path)))

        try:
            near_misses = getNearMissFrames(db, ttc_threshold_frames, vehicle_only)
        except Exception as error_message:
            return (500, error_message)

        try:
            create_highlight_video(project_dir, video_path, near_misses)
        except Exception as error_message:
            return (500, error_message)


        return (200, "Success")



