#!/usr/bin/env python

import tornado.web
import os
from baseHandler import BaseHandler

from traffic_cloud_utils.app_config import get_project_path, get_project_video_path, update_config_without_sections, get_config_without_sections

class UploadMask(BaseHandler):

    @staticmethod
    def parse_request(files):
        name_body_dict = {}
        for k, v in files.iteritems():
            fileinfo = v[0]
            name_body_dict[k] = fileinfo['body']
        return name_body_dict

    """
    @api {post} /mask/ Upload Mask 
    @apiName UploadMask 
    @apiVersion 0.1.0
    @apiGroup Upload
    @apiDescription This route will upload files to a project (and create a new project if an old one is not specified). You may provide a project identifier if you would like to update the files from an old project. If you provide a project identifier for an old project, all of the parameters are optional. If you are creating a new project, all parameters are required. This route will always return a dictionary containing the project identifier.

    @apiParam {String} [identifier] The identifier of the project
    @apiParam {File} imagemask An image the same dimensions as the video, black pixels indicating areas to ignore in feature tracking, white pixels indicating areas to include. 

    @apiSuccess {String} project_identifier The project identifier. This will be used to reference the project in all other requests.

    @apiError error_message The error message to display.
    """
    def post(self):
        # TODO: Check for an existing project, and update only the existing files if so.
        identifier = self.get_body_argument('identifier')
        
        name_body_dict = self.parse_request(self.request.files)
        for fn, body in name_body_dict.iteritems():
            fpath = os.path.join(get_project_path(identifier), fn)
            with open(fpath, 'wb') as mask:
                mask.write(body)

        self.finish("Mask uploaded successfully")

