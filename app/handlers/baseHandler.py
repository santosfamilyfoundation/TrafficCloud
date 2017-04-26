import tornado.web
import json
import traceback
import os
from traffic_cloud_utils.app_config import get_project_path

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.error_message = None
        self.MB = 1024*1024
        self.GB = 1024*self.MB

    def project_exists(self, identifier):
        if identifier == None:
            self.error_message = 'Identifier required but none given!'
            raise tornado.web.HTTPError(status_code=400)
        if not os.path.exists(get_project_path(identifier)):
            self.error_message = 'Invalid Identifier {}. This project does not exist!'.format(identifier)
            raise tornado.web.HTTPError(status_code=404)

    def find_argument(self, arg_name, expected_type, default=None):
        method_type = self.request.method.lower()
        ret_val = None
        if method_type == 'post':
            # Try to get the arg from the body
            content_type = self.request.headers['Content-Type']
            if 'application/json' in content_type:
                # Grab from json
                try:
                    json = tornado.escape.json_decode(self.request.body)
                    ret_val = json[arg_name]
                    if ret_val == None:
                        ret_val = default
                except (ValueError,KeyError) as V :
                    ret_val = default
            elif 'x-www-form-urlencoded' in content_type:
                # Grab from form data
                if expected_type is list:
                    ret_val = self.get_body_arguments(arg_name)
                    if ret_val == []:
                        ret_val = default
                else:
                    ret_val = self.get_body_argument(arg_name, default=default)
            else:
                self.error_message = 'Content type {} is unsupported'.format(content_type)
                raise tornado.web.HTTPError(status_code=400)
        elif method_type == 'get':
            # Try to get the arg from the header instead
            if expected_type is list:
                ret_val = self.get_arguments(arg_name)
                if ret_val == []:
                    ret_val = default
            else:
                ret_val = self.get_argument(arg_name, default=default)
        else:
            # We don't currently support other method types
            self.error_message = 'Only GET and POST are supported methods for this API'
            raise tornado.web.HTTPError(status_code=405)

        if isinstance(ret_val, expected_type) or ret_val is None:
            return ret_val
        else:
            try:
                if expected_type is bool and isinstance(ret_val, basestring):
                    low = ret_val.lower()
                    if low == 'true' or low == '1':
                        return True
                    elif low == 'false' or low == '0':
                        return False
                    else:
                        return default
                return expected_type(ret_val)
            except:
                self.error_message = 'Improper type for argument {}. Expected {}, got {}'.format(arg_name,expected_type.__name__, type(ret_val).__name__)
                raise tornado.web.HTTPError(status_code=400)

    def write_error(self, status_code, **kwargs):
        self.set_header('Content-Type', 'application/json')

        error_dict = {
            'code': status_code
        }

        if self.error_message != None:
            error_dict['error_message'] = self.error_message
        else:
            error_dict['error_message'] = traceback.format_exception(*kwargs['exc_info'])[-1].strip()
        print("ERROR: "+error_dict['error_message'])

        if self.settings.get('serve_traceback') and 'exc_info' in kwargs:
            lines = []
            for line in traceback.format_exception(*kwargs['exc_info']):
                lines.append(line)
            error_dict['traceback'] = lines

        self.finish(json.dumps({
            'error': error_dict }))

    def write_file_stream(self, file_name, chunk_size = 2048):
        if not os.path.exists(file_name):
            self.error_message = "{} does not exist on the server".format(file_name)
            raise tornado.web.HTTPError(status_code=500)
        with open(file_name, 'rb') as f:
            try:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    self.write(data)
                    self.flush()
            except Exception as e:
                self.error_message = str(e)
                raise tornado.web.HTTPError(status_code=500)
