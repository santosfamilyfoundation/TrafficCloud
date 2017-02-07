import tornado.web
import json
import traceback

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.error_message = None

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
