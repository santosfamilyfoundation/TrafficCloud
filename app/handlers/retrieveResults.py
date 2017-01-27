#!/usr/bin/env python
import zipfile
import os
import tornado.web

from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections
import video
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
        identifier = self.request.body_arguments["identifier"]


    def get(self):
        identifier = self.request.body_arguments["identifier"]
        project_path = get_project_path(identifier)

        print 'creating archive'
        zf = zipfile.ZipFile(identifier+'_write.zip', mode='w')
        for subdir, dirs, files in os.walk(project_path):
            for file in files:
                try:
                    print 'Adding {}'.format(file)
                    zf.write(file)
                except Exception as e:
                    print e
                finally:
                    print 'closing'
                    zf.close()

        self.finish("Retrieve Results")


