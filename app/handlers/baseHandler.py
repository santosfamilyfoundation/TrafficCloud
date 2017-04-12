import tornado.web
import json
import traceback
import os

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.error_message = None
        self.MB = 1024*1024
        self.GB = 1024*self.MB

    def find_argument(self, arg_name, default=None):
        method_type = self.request.method.lower()
        ret_val = None
        if method_type == 'post':
            # Try to get the identifier from the body
            ret_val = self.get_body_argument(arg_name, default=default)
        elif method_type == 'get':
            # Try to get the identifier from the header instead
            ret_val = self.get_argument(arg_name, default=default)
        else:
            # We don't currently support other method types
            self.error_message = 'Only GET and POST are supported methods for this API'
            raise tornado.web.HTTPError(status_code=405)

        if ret_val:
            return ret_val
        else:
            return default

    def write_error(self, status_code, **kwargs):
        self.set_header('Content-Type', 'application/json')

        error_dict = {
            'code': status_code
        }

        if self.error_message != None:
            error_dict['message'] = self.error_message
            print("ERROR: "+self.error_message)

        if self.settings.get('serve_traceback') and 'exc_info' in kwargs:
            lines = []
            for line in traceback.format_exception(*kwargs['exc_info']):
                lines.append(line)
            error_dict['traceback'] = lines

        self.finish(json.dumps({
            'error': error_dict }))

    def write_file_stream(self, file_name, chunk_size = 2048):
        if not os.path.exists(file_name):
            self.error_message = "That file does not exist on the server"
            raise tornado.web.HTTPError(status_code=500)
        with open(file_name, 'rb') as f:
            try:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    self.write(data)
            except Exception as e:
                self.error_message = str(e)
                raise tornado.web.HTTPError(status_code=500)
