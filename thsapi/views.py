from thsapi import app, couch

from thsapi.models import Descriptor, db

@app.route('/tables/populate')
def tables_populate():
    ths_collection = couch.server['aaew_ths']
    view = couch.apply_view(ths_collection, 'ths/all_active_thsentry_objects')
    count = 0
    relations = {}
    for doc in view:
        count += 1
        _id = doc.get('_id')
        match = Descriptor.query.filter_by(id=_id).first()
        if not match:
            match = Descriptor(id=_id, name=doc.get('name'), type=doc.get('type') or 'undefined')
        else:
            match.name = doc.get('name')
            match.type = doc.get('type') or 'undefined'
        relations[_id] = []
        for rel in doc.get('relations', []):
            relations[_id].append(rel.get('objectId'))
        db.session.add(match)
    db.session.commit()
    return 'Populated table with {} entries'.format(count) 
    


@app.route('/get/<string:thsid>')
def get(thsid):
    matches = Descriptor.query.filter_by(id=thsid)
    if matches:
        return matches.first().name



