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
    @apiVersion 0.1.0
    @apiGroup Results
    @apiDescription This route will retrieve any metadata associated with the project. This includes test video files and safety analysis results.

    @apiParam {String} identifier The identifier of the project to retrieve results from.

    @apiSuccess {File} results_zip The API will return all metadata (Images, Report, etc.) as a compressed archive.

    @apiError error_message The error message to display.
    """
    def prepare(self):
        self.identifier = self.find_argument('identifier', str)
        self.project_exists(self.identifier)
    
    def get(self):
        project_path = get_project_path(self.identifier)
        file_videos = os.path.join(project_path, 'final_videos')
        file_images = os.path.join(project_path, 'final_images')
        file_report = os.path.join(project_path, 'santosreport.pdf')
        self.file_name = os.path.join(project_path, 'results.zip')

        zipf = zipfile.ZipFile(self.file_name, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        # Write videos
        for root, dirs, files in os.walk(file_videos):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file)
        # Write images
        for root, dirs, files in os.walk(file_images):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file)
        # Write report, if there
        try:
            zipf.write(file_report, os.path.basename(file_report))
        except:
            status_code = 500
            self.error_message = "Report was not generated for sending. Try re-running generation."
            raise tornado.web.HTTPError(status_code = status_code)
        zipf.close()

        self.set_header('Content-Type', 'application/zip')
        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Content-Disposition', 'attachment; filename=' + self.file_name)
        self.write_file_stream(self.file_name)
        self.finish()

    def on_finish(self):
        os.remove(self.file_name)
