#!/usr/bin/env python
import os
import subprocess
import shutil

import tornado.web

from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
from traffic_cloud_utils.emailHelper import EmailHelper
from traffic_cloud_utils import video

class TestConfigHandler(tornado.web.RequestHandler):
    """
    @api {post} /testConfig/ Test Configuration
    @apiName TestConfig
    @apiVersion 0.1.0
    @apiGroup Configuration
    @apiDescription Calling this route will test the video's configuration. When testing is done, an email will be sent to the project's user. This test consists of running object tracking on a small subset of the video, and producing a video showing the results of the tracking. (Due to the potentially long duration of testing, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} test_flag Flag to determine whether feature tracking or object tracking will be tested.
    @apiParam {String} identifier The identifier of the project to test configuration of.
    @apiParam {String} email The email address that should be notified when the object tracking is complete.
    @apiParam {Integer} [frame_start] The frame number to start the configuration test at. If no frame_start is provided, the configuration test will start at the beginning of the video.
    @apiParam {Integer} [num_frames] The number of frames to analyze. To keep configuration testing short, this parameter must be less than 200. If no num_frames is provided, a default value of 100 will be used.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """
    def post(self):

        identifier = self.get_body_argument("identifier")
        test_flag = self.get_body_argument("test_flag")
        print test_flag

        frame_start = int(self.get_body_argument("frame_start", default = 0))
        num_frames = int(self.get_body_argument("num_frames", default = 120))

        if test_flag == "feature":
            print "running feature"
            status_code, reason = self.runConfigTestFeature(identifier, frame_start, num_frames)
        elif test_flag == "object":
            print "running object"
            status_code, reason = self.runConfigTestObject(identifier, frame_start, num_frames)

        if status_code == 200:
            self.finish("Testing tracking")
        else:
            raise tornado.web.HTTPError(reason=reason, status_code=status_code)

    def runConfigTestFeature(self, identifier, frame_start, num_frames):
        project_path = get_project_path(identifier)
        if not os.path.exists(project_path):
           return (500, 'Project directory does not exist. Check your identifier?')

        tracking_path = os.path.join(project_path, "tracking.cfg")
        db_path = os.path.join(project_path, ".temp", "test", "test_feature", "test1.sqlite")
        if os.path.exists(db_path):
            os.remove(db_path)

        images_folder = "feature_images"
        video.delete_files(images_folder)        

        try:
            subprocess.call(["feature-based-tracking", tracking_path, "--tf", "--database-filename", db_path])
            subprocess.call(["display-trajectories.py", "-i", get_project_video_path(identifier), "-d", db_path, "-o", project_path + "/homography/homography.txt", "-t", "feature", "--save-images", "-f", str(frame_start), "--last-frame", str(frame_start+num_frames)])
        except Exception as err_msg:
            return (500, err_msg)

        video.move_files_to_folder(os.getcwd(),images_folder,'image-', '.png')

        return (200, "Success")

    def runConfigTestObject(self, identifier, frame_start, num_frames):
        project_path = get_project_path(identifier)
        if not os.path.exists(project_path):
           return (500, 'Project directory does not exist. Check your identifier?')


        tracking_path = os.path.join(project_path, "tracking.cfg")
        obj_db_path = os.path.join(project_path,".temp", "test", "test_object", "test1.sqlite")
        feat_db_path = os.path.join(project_path, ".temp", "test", "test_feature", "test1.sqlite")
        if os.path.exists(obj_db_path):
            os.remove(obj_db_path)
        shutil.copyfile(feat_db_path, obj_db_path)

        images_folder = "object_images"
        video.delete_files(images_folder)

        try:
            subprocess.call(["feature-based-tracking",tracking_path,"--gf","--database-filename",obj_db_path])
            subprocess.call(["classify-objects.py", "--cfg", tracking_path, "-d", obj_db_path])  # Classify road users
            subprocess.call(["display-trajectories.py", "-i", get_project_video_path(identifier),"-d", obj_db_path, "-o", project_path + "/homography/homography.txt", "-t", "object", "--save-images", "-f", str(frame_start), "--last-frame", str(frame_start+num_frames)])
        except Exception as err_msg:
            return (500, err_msg)

        video.move_files_to_folder(os.getcwd(),images_folder,'image-', '.png')

        return (200, "Success")

