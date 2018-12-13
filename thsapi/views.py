import werkzeug.exceptions
from flask import jsonify, Response, request

from thsapi import app, couch, models
from thsapi import requires_auth

from thsapi.models import Descriptor, db, taxonomy_table

db.create_all()


DEFAULT_SEARCH_RESULT_LIMIT = 32


@app.route("/ths/tables/populate", methods=["GET"])
@requires_auth
def tables_populate(username=None, password=None):
    try:
        docs = couch.retrieve_ths_entries(username, password)
        descriptor_count = models.fill_tables_from_couchdb(docs)
        return "Populated descriptor table with {} entries".format(descriptor_count)
    except couch.couchdb.http.Unauthorized:
        raise werkzeug.exceptions.Forbidden()


@app.route("/ths/tables/status", methods=["GET"])
def tables_status():
    row_counts = {
        k: db.session.execute("SELECT count(*) FROM {}".format(tablename)).first()[0]
        for k, tablename in {
            "descriptors": Descriptor.__tablename__,
            "relations": "taxonomy",
        }.items()
    }
    return (
        dict(status="success", description="Database status", objects=row_counts),
        200,
    )


def urlify(data, path, *args):
    """ looks up the array fields in `data` specified by the `*args` arguments, assumes those
    arrays contain actual descriptor IDs, and turns them into URLs using the given `path`. """
    for arg in args:
        if arg in data:
            data[arg] = [
                "{}{}{}".format(request.host_url, path, i) for i in data.get(arg)
            ]
    return data


@app.route("/ths/get/<string:thsid>", methods=["GET"])
def get_descriptor(thsid):
    """ see if argument value is within expected character count """
    arglengths = sorted(
        [(a[:32], len(a)) for a in [thsid]], key=lambda al: al[1], reverse=True
    )
    if arglengths[0][1] > 26:
        raise werkzeug.exceptions.RequestURITooLarge(
            description="refused to compute: argument value `{}` too long ({} chars).".format(
                *arglengths[0]
            )
        )
    """ try and retrieve entry from database """
    entry = models.get(Descriptor, thsid)
    if entry:
        resp = urlify(dict(entry), "ths/get/", "parents", "children")
        resp["status"] = "success"
        return resp
    else:
        raise werkzeug.exceptions.NotFound(
            description="could not find entry with ID {}".format(thsid)
        )


@app.route("/ths/get/<string:thsid>/<string:field>", methods=["GET"])
def get_descriptor_field(thsid, field):
    """ see if requested field is in the model """
    if field not in ["name", "type", "parents", "children", "roots"]:
        raise werkzeug.exceptions.NotImplemented(
            description="will not compute: `{}` not in data model.".format(field)
        )

    """ see if all argument values are within expected character count """
    arglengths = sorted(
        [(a[:32], len(a)) for a in [thsid, field]], key=lambda al: al[1], reverse=True
    )
    if arglengths[0][1] > 26:
        raise werkzeug.exceptions.RequestURITooLarge(
            description="refused to compute: argument value `{}` too long ({} chars).".format(
                *arglengths[0]
            )
        )

    """ try and retrieve requested thesaurus entry from database """
    entry = models.get(Descriptor, thsid)
    if entry:
        if field in ["name", "type"]:
            return Response(entry.__dict__.get(field), mimetype="text/plain")
        elif field in ["parents", "children", "roots"]:
            return jsonify(globals().get("get_descriptor_{}".format(field))(entry))
    raise werkzeug.exceptions.NotFound(
        description="could not find find entry with ID {}".format(thsid)
    )


def make_simple_dict_list(entries):
    return [{"id": r.id, "name": r.name, "type": r.type} for r in entries]


get_descriptor_parents = lambda entry: make_simple_dict_list(entry.parents)
get_descriptor_children = lambda entry: make_simple_dict_list(entry.children)


def get_descriptor_roots(entry):
    frontier = entry.parents
    visited = set()
    roots = set()
    while len(frontier) > 0:
        parent = frontier.pop()
        if parent not in visited:
            if len(parent.parents) > 0:
                frontier.extend(parent.parents)
            else:
                roots.add(parent)
        visited.add(parent)
    return make_simple_dict_list(roots)


@app.route("/ths/search", methods=["GET", "POST"])
def search_descriptors():
    if request.method == "POST":
        """ check for correct content type, but then extract json from body no matter what. """
        if request.content_type == "application/json":
            if request.content_length > 256:
                """ if body is huge, don't even bother. """
                raise werkzeug.exceptions.RequestEntityTooLarge(
                    description="content length of request body is {}. I won't accept that.".format(
                        request.content_length
                    )
                )
            """ extract parameters from request body """
            data = request.get_json(force=True)
        else:
            raise werkzeug.exceptions.BadRequest(
                description="request has invalid content-type (expected `application/json`):"
                + " {}.".format(request.content_type)
            )
    else:
        """ http method GET """
        data = {
            param: request.args.get(param)
            for param in ["term", "mode", "limit", "type", "offset"]
            if param in request.args
        }
        if "type" in data:
            data["type"] = data.get("type").split(",")

    """ type limit search=prefix|contains """
    if "term" in data:
        term = data.get("term")
    else:
        """ require `term` field. """
        raise werkzeug.exceptions.BadRequest(
            description="did not specify search `term` field."
        )

    """ search mode defaults to prefix """
    mode = data.get("mode", "prefix")
    if mode not in ["prefix", "contains"]:
        """ only support these two modes for now. """
        raise werkzeug.exceptions.BadRequest(
            description="unknown search mode `{}` - only `prefix` and `contains`"
            + " are supported.".format(mode)
        )
    query_template = "%{}%" if mode == "contains" else "{}%"

    """ need thesaurus entry types filter as a list of allowed types """
    typefilter = data.get("type", [])
    if type(typefilter) is not list:
        typefilter = [typefilter]

    """ use limit parameter if available, defaults to DEFAULT_SEARCH_RESULT_LIMIT """
    limit = data.get("limit", DEFAULT_SEARCH_RESULT_LIMIT)
    if type(limit) is str:
        try:
            limit = int(limit)
        except Exception as e:
            raise werkzeug.exceptions.BadRequest(
                description="`limit` value must be integer between 1 and {} (got {}).".format(
                    DEFAULT_SEARCH_RESULT_LIMIT, limit
                )
            )
    limit = max(min(limit, DEFAULT_SEARCH_RESULT_LIMIT), 1)

    """ use offset if available """
    offset = data.get("offset", 0)
    if type(offset) is str:
        try:
            offset = int(offset)
        except:
            offset = 0

    """ do the actual searching now. """
    matches = (
        Descriptor.query.filter(Descriptor.name.like(query_template.format(term)))
        .filter(db.or_(*[Descriptor.type == type_ for type_ in typefilter]))
        .all()
    )
    results = sorted(matches, key=lambda m: m.name.lower())[offset:limit]

    """ assemble response """
    success = len(results) > 0
    return (
        dict(
            status="success" if success else "fail",
            total=len(results),
            offset=offset,
            description="Found {} results for search term '{}'.".format(
                len(results), term
            ),
            objects=make_simple_dict_list(results),
        ),
        200,
    )
