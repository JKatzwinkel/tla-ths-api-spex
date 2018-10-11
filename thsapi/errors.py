from flask import jsonify
from werkzeug.exceptions import HTTPException

from thsapi import app



@app.errorhandler(HTTPException)
def handle_error(error):
    response = {
            'status': "error",
            'error': {
                'code': error.code,
                'name': error.name,
                'type': error.__class__.__name__,
                'description': error.get_description(),
                },
            }
    return jsonify(response), error.code


