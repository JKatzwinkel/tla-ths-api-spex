import couchdb

from thsapi import app

server = couchdb.Server(app.config['COUCHDB_SERVER_URL'])
server.resource.credentials = (app.config['COUCHDB_SERVER_USER'], app.config['COUCHDB_SERVER_PASS'])


def apply_view(collection, view_name):
    for row in collection.view(view_name):
        yield row.value

