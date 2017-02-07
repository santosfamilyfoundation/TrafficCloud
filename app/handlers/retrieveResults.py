#!/usr/bin/env python
import zipfile
import os
import tornado.web

from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
from traffic_cloud_utils import video
from traffic_cloud_utils.emailHelper import EmailHelper

class RetrieveResultsHandler(tornado.web.RequestHandler):
    """
    @api {get} /retrieveResults/ Retrieve Results
    @apiName RetrieveResults
    @apiVersion 0.0.0
    @apiGroup Results
    @apiDescription This route will retrieve any metadata associated with the project. This includes test video files and safety analysis results.

    @apiParam {String} identifier The identifier of the project to retrieve results from.

    @apiSuccess files The API will return all metadata since last retrieval as a compressed archive.

    @apiError error_message The error message to display.
    """

    def post(self):
        self.identifier = self.get_body_arguments("identifier")

    def get(self):
        identifier = self.get_body_arguments("identifier")
        project_path = get_project_path(identifier[0])
        file_path = os.path.join(project_path, 'final_videos')
        file_name = os.path.join(project_path, 'results.zip')

        zipf = zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(file_path):
            for file in files:
                zipf.write(os.path.join(file_path, file))
        zipf.close()
        # results_path = os.path.join(project_path, 'results.zip')

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Description', 'File Transfer')
        # TODO temporary
        # self.set_header('Content-Disposition', 'attachment; filename=' + results_path)
        self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
        # TODO temporary
        # with open(results_path, 'rb') as f:
        with open(file_name, 'rb') as f:
            try:
                while True:
                    data = f.read(2048)
                    if not data:
                        break
                    self.write(data)
                self.finish()
            except Exception as e:
                print e
