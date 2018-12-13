from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException
from flask_cors import CORS


app = Flask(__name__)
app.config.from_pyfile("../config.cfg", silent=False)
cors = CORS(app, resources={r"/ths/*": {"origins": "*"}})


@app.errorhandler(HTTPException)
def handle_error(error):
    response = {
        "header": {
            "status": "error",
            "code": error.code,
            "type": error.__class__.__name__,
            "description": error.get_description(),
        },
        "result": None,
    }
    return jsonify(response), error.code


class ApiResponse(Response):
    """ custom response class that allows for views to return a dict instead of json responses,
    and throws a few fields into the response which are expected by the client. """

    @classmethod
    def force_type(cls, view_response, environ=None):
        """ necessary in case a view returns a dict instead of the built-in response/view return
        types. This will be called by the framework in case the view return type is not supported.
        """
        response = {
            "header": {
                "status": "error",
                "object_base_url": "{}ths/get".format(request.host_url),
            },
            "result": {},
        }
        if type(view_response) is dict:
            response["result"] = view_response
            for key in ["status", "description"]:
                if key in view_response:
                    response["header"][key] = view_response.get(key)
                    del view_response[key]

        return super(ApiResponse, cls).force_type(jsonify(response), environ)


app.response_class = ApiResponse

from thsapi import views
