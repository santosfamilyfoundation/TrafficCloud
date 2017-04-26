#!/usr/bin/env python

import os
import tornado.web
from baseHandler import BaseHandler
from traffic_cloud_utils.app_config import get_project_path, get_project_video_path
from traffic_cloud_utils.video import get_framerate
from traffic_cloud_utils.plotting.visualization import compare_speeds

from traffic_cloud_utils.statusHelper import StatusHelper, Status

class CompareSpeedsHandler(BaseHandler):
    """
    @api {get} /compareSpeeds/ Visualize how speed distributions compare across projects
    @apiName compareSpeeds
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription Calling this route will create a graph of comparing the speed distributions of different project video data. The image will then be sent back in the response body. This route requires running object tracking on the video.
    @apiParam {String} identifier identifier of the parent project. This is used to decide in which project directory to save the compare speeds graph.
    @apiParam {JSON} identifiers_to_cmp A json array of the identifiers of the projects of which to compare speeds.
    @apiParam {JSON} labels_to_cmp A json array of the human readable string text for each of the projects in project_identifiers. These will be used in the legends and axes labels of the graph.
    @apiParam {Boolean} [only_show_85th] Control whether the graph will only compare the 85th percentile speeds. If you are comparing more than 4 projects, it is recommended to set this to True, for visual purposes. Defaults to False.

    @apiSuccess {File} image_jpg The API will return the created graph upon success.

    @apiError error_message The error message to display.
    """
    def prepare(self):
        self.identifier = self.find_argument('identifier', str)
        self.identifiers_to_cmp = self.find_argument('identifiers_to_cmp', list)
        self.labels_to_cmp = self.find_argument('labels_to_cmp', list)
        self.only_show_85th = self.find_argument('only_show_85th', bool, False)

        for identifier in self.identifiers_to_cmp:
            self.project_exists(identifier)

        status_dict = StatusHelper.get_status(self.identifier)
        if status_dict[Status.Type.OBJECT_TRACKING] != Status.Flag.COMPLETE:
            status_code = 412
            self.error_message = "Object Tracking did not complete successfully, try re-running it."
            raise tornado.web.HTTPError(status_code = status_code)

    def get(self):
        status_code, reason = CompareSpeedsHandler.handler(self.identifier,
                                                    self.identifiers_to_cmp,
                                                    self.labels_to_cmp,
                                                    self.only_show_85th)
        if status_code == 200:
            if self.only_show_85th:
                image_filename = 'compare85th.jpg'
            else:
                image_filename = 'comparePercentiles.jpg'
            image_path = os.path.join(\
                                    get_project_path(self.identifier),\
                                    'final_images',\
                                    image_filename)
            self.set_header('Content-Disposition',\
                            'attachment; filename={}'.format(image_filename))
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Description', 'File Transfer')
            self.write_file_stream(image_path)
            self.finish("Create Speed Comparison Chart")
        else:
            self.error_message = reason
            raise tornado.web.HTTPError(status_code=status_code)

    @staticmethod
    def handler(parent_identifier, identifiers_to_cmp, labels_to_cmp, only_show_85th):
        if not isinstance(identifiers_to_cmp, list) or not isinstance(labels_to_cmp, list):
            return (400, "identifiers_to_cmp and labels_to_cmp should be lists.")

        if len(identifiers_to_cmp) < 2 or len(labels_to_cmp) < 2:
            return (400, "identifiers_to_cmp and labels_to_cmp contained less than 2 elements. Requires at least 2 elements to compare.")

        if len(identifiers_to_cmp) != len(labels_to_cmp):
            return (400, "identifiers_to_cmp and labels_to_cmp were not the same length.")

        # Check if all the neccessary data in each project exists in order to be compared
        project_paths = []
        fps_list = []
        for identifier, label in zip(identifiers_to_cmp, labels_to_cmp):
            project_dir = get_project_path(identifier)
            if not os.path.exists(project_dir):
                return (500, 'Project directory does not exist for {}. Check your identifier?'.format(label))
            project_paths.append(project_dir)

            db = os.path.join(project_dir, 'run', 'results.sqlite')
            if not os.path.exists(db):
                return (500, 'Database file does not exist for {} \
                        Trajectory analysis needs to be called first'.format(label))


            video_path = get_project_video_path(identifier)
            if not os.path.exists(video_path):
                return (500, 'Source video file does not exist for {}.  Was the video uploaded?'.format(label))

            fps_list.append(float(get_framerate(video_path)))

        # Prepare to save in final_images folder of parent_identifier
        final_images = os.path.join(get_project_path(parent_identifier), 'final_images')
        if not os.path.exists(final_images):
            os.mkdir(final_images)

        compare_speeds(project_paths, labels_to_cmp, fps_list, only_show_85th, final_images)

        return (200, "Success")
