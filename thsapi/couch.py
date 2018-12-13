import couchdb

from thsapi import app


def _connect_default():
    if all(
        map(
            lambda k: k in app.config,
            ["COUCHDB_SERVER_URL", "COUCHDB_SERVER_USER", "COUCHDB_SERVER_PASS"],
        )
    ):
        server = couchdb.Server(app.config["COUCHDB_SERVER_URL"])
        server.resource.credentials = (
            app.config["COUCHDB_SERVER_USER"],
            app.config["COUCHDB_SERVER_PASS"],
        )
        return server


def connect(url=app.config.get("COUCHDB_SERVER_URL"), user=None, passwd=None):
    """ connects and authenticates to a running couchdb instances
    at the specified url, and returns a server object. """
    if not (user and passwd and url):
        server = _connect_default()
    elif url and not (url == app.config.get("COUCHDB_SERVER_URL")):
        server = couchdb.Server(url)
        if user and passwd:
            server.resource.credentials = (user, passwd)
    else:
        server = None
    return server


def apply_view(collection, view_name):
    """ applies a saved view (like in stored on the server) to a server's
    collection object and returns a generator yielding the results. """
    for row in collection.view(view_name):
        if row.value.get("revisionState") == "published":
            yield row.value
