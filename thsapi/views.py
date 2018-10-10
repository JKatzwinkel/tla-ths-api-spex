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
        return jsonify(
                id=entry.id,
                name=entry.name,
                type=entry.type,
                parents=[p.id for p in entry.parents],
                children=[c.id for c in entry.children])
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



def get_descriptor_listed_relatives(entries):
    return [{
        'id': r.id,
        'name': r.name,
        'type': r.type} for r in entries]


get_descriptor_parents = lambda entry: get_descriptor_listed_relatives(entry.parents)
get_descriptor_children = lambda entry: get_descriptor_listed_relatives(entry.children)


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
    return get_descriptor_listed_relatives(roots)





@app.route('/ths/get/<string:thsid>/<string:field>', methods=['GET'])
def get_descriptor_field(thsid, field):
    if len(field) > 24 or field not in [
            'name',
            'type',
            'parents',
            'children',
            'roots']:
        return 500
    entry = models.get(Descriptor, thsid)
    if entry:
        if field in ['name', 'type']:
            return entry.__dict__.get(field)
        elif field in ['parents', 'children', 'roots']:
            return jsonify(globals().get('get_descriptor_{}'.format(field))(entry))
    return '404'


@app.route('/ths/find/prefix/<string:prefix>', methods=['GET'])
def search_for_prefix(prefix):
    matches = Descriptor.query.filter(Descriptor.name.like('{}%'.format(prefix))).all()
    return jsonify(get_descriptor_listed_relatives(
        sorted(matches,
            key=lambda m:m.name.lower())[:50]))


@app.route('/ths/search/<string:type>/<string:position>/<string:term>', methods=['GET'])
def search_for_term_typed(term, type):

    matches = Descriptor.query.filter(Descriptor.name.like('{}%'.format(prefix))).filter_by(type=type)
    return jsonify(get_descriptor_listed_relatives(
        sorted(matches,
            key=lambda m:m.name.lower())[:50]))



@app.route('/ths/search/infix/<string:infix>', methods=['GET'])
def search_for_infix(infix):
    matches = Descriptor.query.filter(Descriptor.name.like('%{}%'.format(infix))).all()
    return jsonify(get_descriptor_listed_relatives(
        sorted(matches,
            key=lambda m:m.name)[:50]))


