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

    def write_file_stream(self, file_name, chunk_size = 2048):
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
