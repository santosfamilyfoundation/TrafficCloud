#!/usr/bin/env python

import os
import threading
import tornado.web
import tornado.escape

from storage import getNearMissFrames

from baseHandler import BaseHandler
from traffic_cloud_utils.video import create_highlight_video, get_framerate
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path
from traffic_cloud_utils.statusHelper import StatusHelper, Status
from traffic_cloud_utils.emailHelper import EmailHelper

class CreateHighlightVideoHandler(BaseHandler):
    """
    @api {post} /highlightVideo/ Post Highlight Video
    @apiName PostHighlightVideo
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a highlight video of dangerous interactions from a specified project. When the video is created, an email will be sent to the project's user. This route requires running object tracking on the video, and then running safety analysis on the results of the object tracking beforehand. (Due to the potentially long duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project to create a highlight video for.
    @apiParam {Float} [ttc_threshold] Threshold for determining whether an interaction is dangerous. Default 1.5 seconds.
    @apiParam {Integer} [num_near_misses_to_use] Number of near misses to use in creating the highlight video. If provided a value greater than 10, it will default to 10.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    """
    @api {get} /highlightVideo/ Get Highlight Video
    @apiName GetHighlightVideo
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will get the highlight video created by the hightlightVideo route and returns it in the response body. This route requires the video to be created beforehand.

    @apiParam {String} identifier The identifier of the project to create a highlight video for.

    @apiSuccess {File} video_mp4 The API will return the highlight video upon success.

    @apiError error_message The error message to display.
    """
    def prepare(self):
        self.identifier = self.find_argument('identifier', str)
        self.project_exists(self.identifier)

        status_dict = StatusHelper.get_status(self.identifier)
        if status_dict[Status.Type.HIGHLIGHT_VIDEO] == Status.Flag.IN_PROGRESS:
            status_code = 423
            self.error_message = "Currently creating a highlight video. Please wait."
            raise tornado.web.HTTPError(status_code = status_code)
        if status_dict[Status.Type.SAFETY_ANALYSIS] != Status.Flag.COMPLETE:
            status_code = 412
            self.error_message = "Safety analysis did not complete successfully, try re-running it."
            raise tornado.web.HTTPError(status_code = status_code)
        if self.request.method.lower() == "get" and status_dict[Status.Type.HIGHLIGHT_VIDEO] != Status.Flag.COMPLETE:
            self.error_message = "Highlight Video did not complete successfully, try re-running it."
            raise tornado.web.HTTPError(status_code = 500)
        StatusHelper.set_status(self.identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.IN_PROGRESS)

    def get(self):
        status = StatusHelper.get_status(self.identifier)
        project_path = get_project_path(self.identifier)
        file_name = os.path.join(project_path, 'final_videos', 'highlight.mp4')
        self.set_header('Content-Disposition', 'attachment; filename=highlight.mp4')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Description', 'File Transfer')
        self.write_file_stream(file_name)
        self.finish()

    def post(self):
        email = self.find_argument('email', str)
        ttc_threshold = self.find_argument('ttc_threshold', float, default=1.5)
        num_near_misses_to_use = self.find_argument('num_near_misses_to_use', int, default=10)
        status_code, reason = CreateHighlightVideoHandler.handler(self.identifier, email, ttc_threshold, num_near_misses_to_use)
        if status_code == 200:
            self.finish("Create Highlight Video")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    @staticmethod
    def handler(identifier, email, ttc_threshold, num_near_misses_to_use):

        project_dir = get_project_path(identifier)
        if not os.path.exists(project_dir):
            StatusHelper.set_status(identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.FAILURE, failure_message='Project directory does not exist.')
            return (500, 'Project directory does not exist. Check your identifier?')

        db = os.path.join(project_dir, 'run', 'results.sqlite')
        #TO-DO: Check to see if tables like "interactions" exist
        if not os.path.exists(db):
            StatusHelper.set_status(identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.FAILURE, failure_message='Trajectory analysis must be run before creating a highlight video.')
            return (500, 'Database file does not exist. Trajectory analysis needs to be called first ')

        video_path = get_project_video_path(identifier)
        if not os.path.exists(video_path):
            StatusHelper.set_status(identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.FAILURE, failure_message='The video file does not exist.')
            return (500, 'Source video file does not exist.  Was the video uploaded?')

        ttc_threshold_frames = int(ttc_threshold * float(get_framerate(video_path)))

        try:
            vehicle_only = True # dangerous near miss interactions involve a car + (bike or ped)
            near_misses = getNearMissFrames(db, ttc_threshold_frames, vehicle_only)
        except Exception as error_message:
            StatusHelper.set_status(identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.FAILURE, failure_message='Failed to get near miss frames.')
            return (500, str(error_message))

        num_near_misses_to_use = min(10, num_near_misses_to_use)
        if len(near_misses) > num_near_misses_to_use:
	    near_misses = near_misses[:num_near_misses_to_use]

        try:
            CreateHighlightVideoThread(identifier, project_dir, video_path, near_misses, email, CreateHighlightVideoHandler.callback).start()
        except Exception as error_message:
            StatusHelper.set_status(identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.FAILURE, failure_message='Error creating highlight video: '+str(error_message))
            return (500, str(error_message))

        return (200, "Success")

    @staticmethod
    def callback(status_code, response_message, email):
        if status_code == 200:
            subject = "Your video has been created."
            message = "Hello,\n\tWe have finished creating your output video.\nThank you for your patience,\nThe Santos Team"

            EmailHelper.send_email(email, subject, message)

        print(status_code, response_message)


class CreateHighlightVideoThread(threading.Thread):
    def __init__(self, identifier, project_dir, video_path, near_misses, email, callback):
        threading.Thread.__init__(self)
        self.identifier = identifier
        self.project_dir = project_dir
        self.video_path = video_path
        self.near_misses = near_misses
        self.callback = callback
        self.email = email

    def run(self):
        create_highlight_video(self.project_dir, self.video_path, self.near_misses)

        StatusHelper.set_status(self.identifier, Status.Type.HIGHLIGHT_VIDEO, Status.Flag.COMPLETE)
        return self.callback(200, "Highlight video complete.", self.email)


