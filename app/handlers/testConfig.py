#!/usr/bin/env python
import os
import subprocess
import shutil

import tornado.web
import threading

from baseHandler import BaseHandler
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
from traffic_cloud_utils.emailHelper import EmailHelper
from traffic_cloud_utils.app_config import update_config_without_sections
from traffic_cloud_utils.statusHelper import StatusHelper, Status
from traffic_cloud_utils import video

class TestConfigHandler(BaseHandler):
    """
    @api {post} /testConfig/ Post Test Configuration
    @apiName PostTestConfig
    @apiVersion 0.1.0
    @apiGroup Configuration
    @apiDescription Calling this route will test the video's configuration. This test consists of running object tracking on a small subset of the video, and producing a video showing the results of the tracking. (Due to the potentially long duration of testing, it is infeasible to return the results as a response to the HTTP request. In order to check the status of the testing and view results, see the Status group of messages.)

    @apiParam {String} test_flag Flag to determine whether feature tracking or object tracking will be tested.
    @apiParam {String} identifier The identifier of the project to test configuration of.
    @apiParam {Integer} [frame_start] The frame number to start the configuration test at. If no frame_start is provided, the configuration test will start at the beginning of the video.
    @apiParam {Integer} [num_frames] The number of frames to analyze. To keep configuration testing short, this parameter must be less than 200. If no num_frames is provided, a default value of 100 will be used.

    @apiSuccess status_code The API will return a status code of 200 upon success.

    @apiError error_message The error message to display.
    """

    """
    @api {get} /testConfig/ Get Test Configuration
    @apiName GetTestConfig
    @apiVersion 0.1.0
    @apiGroup Configuration
    @apiDescription Calling this route will return the video created by testing the video's configuration.

    @apiParam {String} test_flag Flag to determine whether feature tracking or object tracking will be tested.
    @apiParam {String} identifier The identifier of the project to test configuration of.

    @apiSuccess file The API will return the generated test video as a video file.

    @apiError error_message The error message to display.
    """

    def prepare(self):
        self.identifier = self.find_argument('identifier')
        self.test_flag = self.find_argument('test_flag')
        status_dict = StatusHelper.get_status(self.identifier)
        if self.test_flag == "feature":
            status_type = Status.Type.FEATURE_TEST
            if status_dict[Status.Type.HOMOGRAPHY] != Status.Flag.COMPLETE:
                self.error_message = "Uploading homography did not complete successfully, try re-running it."
                status_code = 412
                raise tornado.web.HTTPError(status_code = status_code)
        elif self.test_flag == "object":
            status_type = Status.Type.OBJECT_TEST
            if status_dict[Status.Type.FEATURE_TEST] != Status.Flag.COMPLETE:
                self.error_message = "Feature testing did not complete successfully, try re-running it."
                status_code = 412
                raise tornado.web.HTTPError(status_code = status_code)
        if status_dict[Status.Type.FEATURE_TEST] == Status.Flag.IN_PROGRESS or status_dict[Status.Type.OBJECT_TEST] == Status.Flag.IN_PROGRESS:
            status_code = 423
            self.error_message = "Currently running a test. Please wait."
            raise tornado.web.HTTPError(status_code = status_code)

        request_type = self.request.method.lower()
        if request_type == 'post':
            StatusHelper.set_status(self.identifier, status_type, Status.Flag.IN_PROGRESS)
        elif request_type == 'get':
            if self.test_flag == "feature":
                if status_dict[Status.Type.FEATURE_TEST] != Status.Flag.COMPLETE:
                    status_code = 500
                    self.error_message = "Feature test not complete, try re-running it."
                    raise tornado.web.HTTPError(status_code = status_code)
            elif self.test_flag == "object":
                if status_dict[Status.Type.OBJECT_TEST] != Status.Flag.COMPLETE:
                    status_code = 500
                    self.error_message = "Object test not complete, try re-running it."
                    raise tornado.web.HTTPError(status_code = status_code)

    def post(self):
        frame_start = int(self.find_argument("frame_start", default = 0))
        num_frames = int(self.find_argument("num_frames", default = 120))
        if num_frames > 200:
            num_frames = 200

        status_code, reason = TestConfigHandler.handler(self.identifier, frame_start, num_frames, self.test_flag)

        if status_code == 200:
            self.finish("Testing tracking")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    def get(self):
        status = StatusHelper.get_status(self.identifier)
        project_path = get_project_path(self.identifier)
        if self.test_flag == "feature":
            self.file_name = os.path.join(project_path, 'feature_video', 'feature_video.mp4')
            self.set_header('Content-Disposition', 'attachment; filename=feature_video.mp4')
        elif self.test_flag == "object":
            self.file_name = os.path.join(project_path, 'object_video', 'object_video.mp4')
            self.set_header('Content-Disposition', 'attachment; filename=object_video.mp4')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Description', 'File Transfer')
        self.write_file_stream(self.file_name)
        self.finish()

    @staticmethod
    def handler(identifier, frame_start, num_frames, test_flag):
        if test_flag == "feature":
            status_type = Status.Type.FEATURE_TEST
        elif test_flag == "object":
            status_type = Status.Type.OBJECT_TEST

        project_path = get_project_path(identifier)
        if not os.path.exists(project_path):
            StatusHelper.set_status(identifier, status_type, Status.Flag.FAILURE)
            return (400, 'Project directory does not exist. Check your identifier?')

        if test_flag == "feature":
            print "running feature"
            TestConfigFeatureThread(identifier, frame_start, num_frames, TestConfigHandler.test_feature_callback).start()
        elif test_flag == "object":
            print "running object"
            feat_db_path = os.path.join(project_path, ".temp", "test", "test_feature", "test1.sqlite")
            if os.path.exists(feat_db_path):
                TestConfigObjectThread(identifier, frame_start, num_frames, TestConfigHandler.test_feature_callback).start()
            else:
                print "Feature tracking not run"
                StatusHelper.set_status(identifier, status_type, Status.Flag.FAILURE)
                return (400, "Testing of feature tracking did not produce the requird files. Try re-running it.")
        else:
            print "Incorrect flag passed: " + test_flag
            StatusHelper.set_status(identifier, status_type, Status.Flag.FAILURE)
            return (400, "Incorrect flag passed: " + test_flag)

        return (200, "Success")

    @staticmethod
    def test_feature_callback(status_code, response_message, identifier):
        print(status_code, response_message)

    @staticmethod
    def test_object_callback(status_code, response_message, identifier):
        print(status_code, response_message)


class TestConfigFeatureThread(threading.Thread):
    def __init__(self, identifier, frame_start, num_frames, callback):
        threading.Thread.__init__(self)
        self.identifier = identifier
        self.frame_start = frame_start
        self.num_frames = num_frames
        self.callback = callback

    def run(self):
        project_path = get_project_path(self.identifier)
        tracking_path = os.path.join(project_path, "tracking.cfg")
        db_path = os.path.join(project_path, ".temp", "test", "test_feature", "test1.sqlite")
        if os.path.exists(db_path):
            os.remove(db_path)

        testing_dict = {
            'frame1': self.frame_start,
            'nframes': self.num_frames,
            'video-filename': get_project_video_path(self.identifier),
            'homography-filename': os.path.join(project_path, "homography", "homography.txt") }
        update_config_without_sections(tracking_path, testing_dict)

        images_folder = os.path.join(get_project_path(self.identifier), "feature_images")
        video.delete_files(images_folder)
        if not os.path.exists(images_folder):
            os.mkdir(images_folder)

        fbt_call = ["feature-based-tracking", tracking_path, "--tf", "--database-filename", db_path]
        mask_filename = os.path.join(get_project_path(self.identifier), "mask.jpg")
        if os.path.exists(mask_filename):
            fbt_call.extend(["--mask-filename", mask_filename])
        try:
            subprocess.check_call(fbt_call)
            subprocess.check_call(["display-trajectories.py", "-i", get_project_video_path(self.identifier), "-d", db_path, "-o", project_path + "/homography/homography.txt", "-t", "feature", "--save-images", "-f", str(self.frame_start), "--last-frame", str(self.frame_start + self.num_frames), "--output-directory", images_folder])
        except subprocess.CalledProcessError as err_msg:
            StatusHelper.set_status(self.identifier, Status.Type.FEATURE_TEST, Status.Flag.FAILURE)
            return self.callback(500, err_msg.output, self.identifier)

        videos_folder = os.path.join(get_project_path(self.identifier), "feature_video")
        video_filename = "feature_video.mp4"
        temp_image_prefix = 'image-'
        if os.path.exists(os.path.join(videos_folder, video_filename)):
            os.remove(os.path.join(videos_folder, video_filename))
        video.create_video_from_images(images_folder, temp_image_prefix, videos_folder, video_filename, video.get_framerate(get_project_video_path(self.identifier)), self.frame_start)

        video.delete_files(images_folder)
        os.rmdir(images_folder)

        StatusHelper.set_status(self.identifier, Status.Type.FEATURE_TEST, Status.Flag.COMPLETE)
        return self.callback(200, "Test config done", self.identifier)


class TestConfigObjectThread(threading.Thread):
    def __init__(self, identifier, frame_start, num_frames, callback):
        threading.Thread.__init__(self)
        self.identifier = identifier
        self.frame_start = frame_start
        self.num_frames = num_frames
        self.callback = callback

    def run(self):

        project_path = get_project_path(self.identifier)
        tracking_path = os.path.join(project_path, "tracking.cfg")
        obj_db_path = os.path.join(project_path,".temp", "test", "test_object", "test1.sqlite")
        feat_db_path = os.path.join(project_path, ".temp", "test", "test_feature", "test1.sqlite")
        if os.path.exists(obj_db_path):
            os.remove(obj_db_path)
        shutil.copyfile(feat_db_path, obj_db_path)

        testing_dict = {
            'frame1': self.frame_start,
            'nframes': self.num_frames,
            'video-filename': get_project_video_path(self.identifier),
            'homography-filename': os.path.join(project_path, "homography", "homography.txt") }
        update_config_without_sections(tracking_path, testing_dict)

        images_folder = os.path.join(get_project_path(self.identifier), "object_images")
        video.delete_files(images_folder)
        if not os.path.exists(images_folder):
            os.mkdir(images_folder)

        try:
            subprocess.check_call(["feature-based-tracking",tracking_path,"--gf","--database-filename",obj_db_path])
            subprocess.check_call(["classify-objects.py", "--cfg", tracking_path, "-d", obj_db_path])  # Classify road users
            subprocess.check_call(["display-trajectories.py", "-i", get_project_video_path(self.identifier),"-d", obj_db_path, "-o", project_path + "/homography/homography.txt", "-t", "object", "--save-images", "-f", str(self.frame_start), "--last-frame", str(self.frame_start + self.num_frames), "--output-directory", images_folder])
        except subprocess.CalledProcessError as err_msg:
            StatusHelper.set_status(self.identifier, Status.Type.OBJECT_TEST, Status.Flag.FAILURE)
            return self.callback(500, err_msg.output, self.identifier)

        videos_folder = os.path.join(get_project_path(self.identifier), "object_video")
        video_filename = "object_video.mp4"
        temp_image_prefix = 'image-'
        video.create_video_from_images(images_folder, temp_image_prefix, videos_folder, video_filename, video.get_framerate(get_project_video_path(self.identifier)), self.frame_start)

        video.delete_files(images_folder)
        os.rmdir(images_folder)

        StatusHelper.set_status(self.identifier, Status.Type.OBJECT_TEST, Status.Flag.COMPLETE)
        return self.callback(200, "Test config done", self.identifier)
