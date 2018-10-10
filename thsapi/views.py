import werkzeug.exceptions
from flask import jsonify, Response, request

from thsapi import app, couch, models, errors

from thsapi.models import Descriptor, db, taxonomy_table

db.create_all()

@app.route('/ths/tables/populate', methods=['GET'])
def tables_populate():
    ths_collection = couch.server['aaew_ths']
    view = couch.apply_view(ths_collection, 'ths/all_active_thsentry_objects')
    relations = {}
    # re-populate descriptor table
    Descriptor.query.delete()
    for doc in view:
        _id = doc.get('_id')
        obj = Descriptor(id=_id,
                name=doc.get('name'),
                type=doc.get('type') or 'undefined')
        relations[_id] = set()
        # prepare relationship insertions for next step
        for rel in doc.get('relations', []):
            # use only `partOf` relations
            if rel.get('type') == 'partOf' and rel.get('objectId') is not None:
                relations[_id].add(rel.get('objectId'))

        db.session.add(obj)

    db.session.commit()

    # re-populate relations table (taxonomy)
    db.session.execute(taxonomy_table.delete())
    insertions = []
    for child_id, parent_ids in relations.items():
        for parent_id in parent_ids:
            if parent_id in relations:
                insertions.append({
                    'parent_id': parent_id,
                    'child_id': child_id})
    db.session.execute(taxonomy_table.insert(),
            insertions)

    db.session.commit()
    return 'Populated descriptor table with {} entries'.format(len(relations))



def urlify(data, path, *args):
    """ looks up the array fields in `data` specified by the `*args` arguments, assumes those
    arrays contain actual descriptor IDs, and turns them into URLs using the given `path`. """
    for arg in args:
        if arg in data:
            data[arg] = ['{}{}{}'.format(request.host_url, path, i) for i in data.get(arg)]
    return data


@app.route('/ths/get/<string:thsid>', methods=['GET'])
def get_descriptor(thsid):
    """ see if argument value is within expected character count """
    arglengths = sorted([(a[:32], len(a)) for a in [thsid]],
            key=lambda al:al[1],
            reverse=True)
    if arglengths[0][1] > 26:
        raise werkzeug.exceptions.RequestURITooLarge(
                description='refused to compute: argument value `{}` too long ({} chars).'.format(*arglengths[0]))
    """ try and retrieve entry from database """
    entry = models.get(Descriptor, thsid)
    if entry:
        return jsonify(urlify(dict(entry), 'ths/get/', 'parents', 'children'))
    else:
       raise werkzeug.exceptions.NotFound(description='could not find entry with ID {}'.format(thsid))


@app.route('/ths/get/<string:thsid>/<string:field>', methods=['GET'])
def get_descriptor_field(thsid, field):
    """ see if requested field is in the model """
    if field not in [
            'name',
            'type',
            'parents',
            'children',
            'roots']:
        raise werkzeug.exceptions.NotImplemented(
                description='will not compute: `{}` not in data model.'.format(field))

    """ see if all argument values are within expected character count """
    arglengths = sorted([(a[:32], len(a)) for a in [thsid, field]],
            key=lambda al:al[1],
            reverse=True)
    if arglengths[0][1] > 26:
        raise werkzeug.exceptions.RequestURITooLarge(
                description='refused to compute: argument value `{}` too long ({} chars).'.format(*arglengths[0]))

    """ try and retrieve requested thesaurus entry from database """
    entry = models.get(Descriptor, thsid)
    if entry:
        if field in ['name', 'type']:
            return Response(entry.__dict__.get(field), mimetype='text/plain')
        elif field in ['parents', 'children', 'roots']:
            return jsonify(globals().get('get_descriptor_{}'.format(field))(entry))
    raise werkzeug.exceptions.NotFound(
            description='could not find find entry with ID {}'.format(thsid))



def make_simple_dict_list(entries):
    return [{
        'id': r.id,
        'name': r.name,
        'type': r.type} for r in entries]


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





@app.route('/ths/search', methods=['POST'])
def search_descriptors():
    if request.method == 'POST':
        """ check for correct content type, but then extract json from body no matter what. """
        if request.content_type == 'application/json':
            if request.content_length > 256:
                """ if body is huge, don't even bother. """
                raise werkzeug.exceptions.RequestEntityTooLarge(
                        description='content length of request body is {}. I won\'t accept that.' \
                                .format(request.content_length))
            data = request.get_json(force=True)
            """ type limit search=prefix|contains """
            if 'term' in data:
                term = data.get('term')
            else:
                """ require `term` field. """
                raise werkzeug.exceptions.BadRequest(
                        description='did not specify search `term` field in request body.')

            """ search mode defaults to prefix """
            mode = data.get('search', 'prefix')
            if mode not in ['prefix', 'contains']:
                """ only support these two modes for now. """
                raise werkzeug.exceptions.BadRequest(
                        description='unknown search mode `{}` - only `prefix` and `contains`' + \
                                ' are supported.'.format(mode))
            query_template = '%{}%' if mode == 'contains' else '{}%'

            """ need thesaurus entry types filter as a list of allowed types """
            typefilter = data.get('type', [])
            if type(typefilter) is not list:
                typefilter = [typefilter]

            """ use limit parameter if available, defaults to 50 """
            limit = data.get('limit', 50)
            if type(limit) is str:
                try:
                    limit = int(str)
                except:
                    raise werkzeug.exceptions.BadRequest(
                            description='`limit` value must be integer between 1 and 50.')
            limit = max(min(limit,50),1)

            
            """ do the actual searching now. """
            matches = Descriptor.query.filter(Descriptor.name.like(query_template.format(term))) \
                    .filter(db.or_(
                        *[Descriptor.type == type_ for type_ in typefilter])).all()
            results = sorted(matches, key=lambda m:m.name.lower())[:limit]

            """ assemble response """
            success = len(results) > 0
            return jsonify(
                    status = "success" if success else "fail",
                    message = "God's in HIS heaven all's right with the earth" if success else \
                            "No results for search term " + \
                            "'{}' and type filter(s) specified (if any).".format(term),
                    length = len(results),
                    result = make_simple_dict_list(results))
        else:
            raise werkzeug.exceptions.BadRequest(
                    description='request has invalid content-type (expected `application/json`):'+\
                            ' {}.'.format(request.content_type))



@app.route('/ths/search/<string:position>/<string:term>', methods=['GET'])
def search_for_term(term, position):

    """ retrieve matching entries from database """
    matches = Descriptor.query.filter(Descriptor.name.like('{}%'.format(term))).all()
    return jsonify(make_simple_dict_list(
        sorted(matches,
            key=lambda m:m.name.lower())[:50]))


@app.route('/ths/search/<string:type>/<string:position>/<string:term>', methods=['GET'])
def search_for_term_typed(term, type):

    matches = Descriptor.query.filter(Descriptor.name.like('{}%'.format(prefix))).filter_by(type=type)
    return jsonify(make_simple_dict_list(
        sorted(matches,
            key=lambda m:m.name.lower())[:50]))



@app.route('/ths/search/infix/<string:infix>', methods=['GET'])
def search_for_infix(infix):
    matches = Descriptor.query.filter(Descriptor.name.like('%{}%'.format(infix))).all()
    return jsonify(make_simple_dict_list(
        sorted(matches,
            key=lambda m:m.name)[:50]))


