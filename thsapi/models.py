from flask_sqlalchemy import SQLAlchemy

from . import app


db = SQLAlchemy(app)

print("Connected to database at {}.".format(db.engine.url))


taxonomy_table = db.Table(
    "taxonomy",
    db.Model.metadata,
    db.Column("parent_id", db.String(26), db.ForeignKey("descriptor.id")),
    db.Column("child_id", db.String(26), db.ForeignKey("descriptor.id")),
)


class Descriptor(db.Model):
    """ model for an entry in the TLA thesaurus, which is a controlled vocabulary made
    up of descriptors that are being used to describe metadata of ancient egyptian texts
    and artifacts. """

    __tablename__ = "descriptor"

    id = db.Column(db.String(26), unique=True, nullable=False, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(80), nullable=False)
    parents = db.relationship(
        "Descriptor",
        secondary=taxonomy_table,
        primaryjoin=taxonomy_table.c.child_id == id,
        secondaryjoin=taxonomy_table.c.parent_id == id,
        backref="children",
    )

    def __iter__(self):
        """ this is only so that instances can be converted into a dict() """
        for key in ["id", "name", "type"]:
            yield key, self.__dict__.get(key)
        yield "parents", [p.id for p in self.parents]
        yield "children", [c.id for c in self.children]


def get_or_create(model, _id, **kwargs):
    """ if an instance of the given model can be identified by the given id in the database,
    if will be retrieved and any remaining argument-value pairs are written into it.
    If the id is not in the database, a new instance will be created and filled with the
    values available, but not stored into the database just yet. """
    try:
        obj = model.query.filter_by(id=_id).one()
        for key, value in kwargs:
            obj.__dict__[key] = value
    except:
        obj = model(id=_id, **kwargs)
    return obj


def get(model, _id):
    """ just looks up the model instance going by given id in the database and returns the instance.
    If no such instance can be found, return null. """
    try:
        return model.query.filter_by(id=_id).one()
    except:
        return None


def fill_tables_from_couchdb(documents):
    """ processes all documents in the passed iterable and turns them
    into Descriptor instances and relations which are then stored into the tables
    where they are meant to go.
    Returns the number of descriptors saved to database. """
    relations = {}
    # re-populate descriptor table
    Descriptor.query.delete()
    for doc in documents:
        _id = doc.get("_id")
        obj = Descriptor(
            id=_id, name=doc.get("name"), type=doc.get("type") or "undefined"
        )
        relations[_id] = set()
        # prepare relationship insertions for next step
        for rel in doc.get("relations", []):
            # use only `partOf` relations
            if rel.get("type") == "partOf" and rel.get("objectId") is not None:
                relations[_id].add(rel.get("objectId"))

        db.session.add(obj)

    db.session.commit()

    # re-populate relations table (taxonomy)
    db.session.execute(taxonomy_table.delete())
    insertions = []
    for child_id, parent_ids in relations.items():
        for parent_id in parent_ids:
            if parent_id in relations:
                insertions.append({"parent_id": parent_id, "child_id": child_id})
    db.session.execute(taxonomy_table.insert(), insertions)
    db.session.commit()

    return len(relations)
