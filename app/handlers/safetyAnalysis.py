 #!/usr/bin/env python
import os
import subprocess

import tornado.web

import threading

from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
from traffic_cloud_utils.emailHelper import EmailHelper

class SafetyAnalysisHandler(tornado.web.RequestHandler):
    """
    @api {post} /safetyAnalysis/ Safety Analysis
    @apiName SafetyAnalysis
    @apiVersion 0.1.0
    @apiGroup Analysis
    @apiDescription Calling this route will perform safety analysis on a project that object tracking has already been run on. When the analysis is done, an email will be sent to the project's user. (Due to the potentially long run duration, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} identifier The identifier of the project on which to run safety analysis.
    @apiParam {String} email The email address that should be notified when the safety analysis is complete

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display. (Will return unique error message if object tracking has NOT been run on specified project)
    """
    def post(self):
        identifier = self.get_body_argument("identifier")
        email = self.get_body_argument("email")
        status_code, reason = SafetyAnalysisHandler.handler(identifier, email, SafetyAnalysisHandler.callback)

        if status_code == 200:
            self.finish("Safety Analysis")
        else:
            raise tornado.web.HTTPError(reason=reason, status_code=status_code)

    @staticmethod
    def callback(status_code, response_message, identifier, email):
        if status_code == 200:
            subject = "Your video has finished processing."
            message = "Hello,\n\tWe have finished looking through your data and identifying any dangerous interactions.\nThank you for your patience,\nThe Santos Team"

            EmailHelper.send_email(email, subject, message)

        print(status_code, response_message)


    @staticmethod
    def handler(identifier, email, callback, prediction_method=None):
        project_path = get_project_path(identifier)
        if not os.path.exists(project_path):
           return (500, 'Project directory does not exist. Check your identifier?')

        SafetyAnalysisThread(identifier, email, callback, prediction_method=prediction_method).start()

        return (200, "Success")


class SafetyAnalysisThread(threading.Thread):
    def __init__(self, identifier, email, callback, prediction_method=None):
        threading.Thread.__init__(self)
        self.identifier = identifier
        self.callback = callback
        self.email = email
        self.prediction_method = prediction_method

    def run(self):
        project_path = get_project_path(self.identifier)
        config_path = os.path.join(project_path, "tracking.cfg")
        db_path = os.path.join(project_path, "run", "results.sqlite")
        update_dict = {
            'video-filename': get_project_video_path(self.identifier), # use absolute path to video on server
            'database-filename': db_path # use absolute path to database
        }

        update_config_without_sections(config_path, update_dict)

        if self.prediction_method is None:
            self.prediction_method = 'cv' # default to the least resource intensive method

        # Predict Interactions between road users and compute safety metrics describing them
        try:
            print "Running safety analysis. Please wait as this may take a while."
            subprocess.call(["safety-analysis.py", "--cfg", config_path, "--prediction-method", self.prediction_method])
            self.callback(200, "Safety Analysis Done", self.identifier, self.email)
        except Exception as err_msg:
            self.callback(500, err_msg, self.identifier, self.email)



