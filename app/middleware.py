import uuid
from flask import request, g

class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_id = str(uuid.uuid4())
        environ['HTTP_X_REQUEST_ID'] = request_id

        def _start_response(status, headers, exc_info=None):
            headers.append(('X-Request-ID', request_id))
            return start_response(status, headers, exc_info)

        return self.app(environ, _start_response)

class ValidationMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if request.path == '/recommend':
            if not request.args.get('app_name'):
                return jsonify(error="Missing app_name parameter"), 400
        return self.app(environ, start_response)