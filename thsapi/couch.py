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
    elif url:
        server = couchdb.Server(url)
        if user and passwd:
            server.resource.credentials = (user, passwd)
    else:
        return None
    try:
        server.stats()
    except couchdb.http.Unauthorized:
        server = None
    return server


def apply_view(collection, view_name):
    """ applies a saved view (like in stored on the server) to a server's
    collection object and returns a generator yielding the results. """
    for row in collection.view(view_name):
        if row.value.get("revisionState") == "published":
            yield row.value


def retrieve_ths_entries(user, passwd):
    """ connects to a couchdb server, opens the 'aaew_ths' collection,
    and queries a stored view that returns all public thesaurus entries in there.
    Might raise an exception (e.g. couchdb.http.Unauthorized)"""
    srv = connect(user=user, passwd=passwd)
    if srv:
        ths_collection = srv["aaew_ths"]
        yield from apply_view(ths_collection, "ths/all_active_thsentry_objects")
    else:
        print("could not connect to couchdb server")
        return []
