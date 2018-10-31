import couchdb

from thsapi import app

if all(map(lambda k:k in app.config, ['COUCHDB_SERVER_URL', 'COUCHDB_SERVER_USER', 'COUCHDB_SERVER_PASS'])):
    server = couchdb.Server(app.config['COUCHDB_SERVER_URL'])
    server.resource.credentials = (app.config['COUCHDB_SERVER_USER'], app.config['COUCHDB_SERVER_PASS'])


def apply_view(collection, view_name):
    for row in collection.view(view_name):
        if row.value.get('revisionState') == 'published':
            yield row.value

