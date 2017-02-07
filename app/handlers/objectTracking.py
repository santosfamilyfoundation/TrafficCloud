#!/usr/bin/env python
import os
import subprocess
import shutil

import tornado.web

import threading

from baseHandler import BaseHandler

from traffic_cloud_utils.plotting.make_object_trajectories import main as db_make_objtraj
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
from traffic_cloud_utils.emailHelper import EmailHelper
from traffic_cloud_utils.statusHelper import StatusHelper
from traffic_cloud_utils import video


class ObjectTrackingHandler(BaseHandler):
    """
    @api {post} /objectTracking/ Object Tracking
    @apiName ObjectTracking
    @apiVersion 0.1.0
    @apiGroup Analysis
    @apiDescription Calling this route will perform object tracking on the video. When the analysis is done, an email will be sent to the project's user. (Due to the potentially long run duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project on which to run object tracking.
    @apiParam {String} email The email address that should be notified when the object tracking is complete.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """

    def post(self):
        # TODO: Implement rerun flag to prevent unnecessary computation
        identifier = self.get_body_argument("identifier")
        email = self.get_body_argument("email", default = None)
        status_code, reason = ObjectTrackingHandler.handler(identifier, email, ObjectTrackingHandler.callback)

        if status_code == 200:

            self.finish("Object Tracking")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    @staticmethod
    def callback(status_code, response_message, identifier, email):
        if status_code == 200:
            message = "Hello,\n\tWe have finished processing your video and identifying all objects.\nThank you for your patience,\nThe Santos Team"
            subject = "Your video has finished processing."

            EmailHelper.send_email(email, subject, message)

        print (status_code, response_message)

    @staticmethod
    def handler(identifier, email, callback):

        """
        Runs TrafficIntelligence trackers and support scripts.
        """
        project_path = get_project_path(identifier)
        if not os.path.exists(project_path):
           return (500, 'Project directory does not exist. Check your identifier?')

        ObjectTrackingThread(identifier, email, callback).start()

        return (200, "Success")

class ObjectTrackingThread(threading.Thread):
    def __init__(self, identifier, email, callback):
        threading.Thread.__init__(self)
        self.identifier = identifier
        self.callback = callback
        self.email = email

    def run(self):
        StatusHelper.set_status(self.identifier, "object_tracking", 1)
        project_path = get_project_path(self.identifier)
        tracking_path = os.path.join(project_path, "tracking.cfg")

        update_dict = {'frame1': 0,
            'nframes': 0,
            'database-filename': 'results.sqlite',
            'classifier-filename': os.path.join(project_path, "classifier.cfg"),
            'video-filename': get_project_video_path(self.identifier),
            'homography-filename': os.path.join(project_path, "homography", "homography.txt")}
        update_config_without_sections(tracking_path, update_dict)

        db_path = os.path.join(project_path, "run", "results.sqlite")

        if os.path.exists(db_path):  # If results database already exists,
            os.remove(db_path)  # then remove it--it'll be recreated.

        try:
            subprocess.check_output(["feature-based-tracking", tracking_path, "--tf", "--database-filename", db_path])
            subprocess.check_output(["feature-based-tracking", tracking_path, "--gf", "--database-filename", db_path])
            subprocess.check_output(["classify-objects.py", "--cfg", tracking_path, "-d", db_path])  # Classify road users
        except subprocess.CalledProcessError as excp:
            StatusHelper.set_status(self.identifier, "object_tracking", -1)

            return self.callback(500, excp.output, self.identifier, self.email)


        db_make_objtraj(db_path)  # Make our object_trajectories db table
        StatusHelper.set_status(self.identifier, "object_tracking", 2)
        return self.callback(200, "Success", self.identifier, self.email)

        # video.create_tracking_video(project_path, get_project_video_path(identifier))


