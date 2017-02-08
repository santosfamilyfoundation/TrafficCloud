#!/usr/bin/env python
import zipfile
import os
import tornado.web
from baseHandler import BaseHandler

from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
from traffic_cloud_utils import video
from traffic_cloud_utils.emailHelper import EmailHelper

class RetrieveResultsHandler(BaseHandler):
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

    def get(self):
        chunk_size = 2048
        identifier = self.get_body_arguments('identifier')
        project_path = get_project_path(identifier[0])
        file_videos = os.path.join(project_path, 'final_videos')
        file_images = os.path.join(project_path, 'final_images')
        file_name = os.path.join(project_path, 'results.zip')
        dir_len = len(project_path)

        zipf = zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(file_videos):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path[dir_len :])
        for root, dirs, files in os.walk(file_images):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path[dir_len :])
        zipf.close()

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
        with open(file_name, 'rb') as f:
            try:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    self.write(data)
                self.finish()
            except Exception as e:
                self.error_message = e
                raise tornado.web.HTTPError(status_code=500)
