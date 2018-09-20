from thsapi import app, couch

from thsapi.models import Descriptor, db, taxonomy_table


@app.route('/ths/tables/populate')
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
    


@app.route('/ths/get/<string:thsid>')
def get(thsid):
    matches = Descriptor.query.filter_by(id=thsid)
    if matches:
        return matches.first().name



