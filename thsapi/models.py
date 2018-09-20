from flask_sqlalchemy import SQLAlchemy

from thsapi import app

db = SQLAlchemy(app)


taxonomy_table = db.Table('taxonomy', db.Model.metadata,
        db.Column('parent_id', db.String(24), db.ForeignKey('descriptor.id')),
        db.Column('child_id', db.String(24), db.ForeignKey('descriptor.id'))
        )
        


class Descriptor(db.Model):
    __tablename__ = 'descriptor'
    id = db.Column(db.String(24), unique=True, nullable=False, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(80), nullable=False)
    parents = db.relationship("Descriptor",
            secondary=taxonomy_table,
            primaryjoin=taxonomy_table.c.child_id==id,
            secondaryjoin=taxonomy_table.c.parent_id==id,
            backref="children")



def get_or_create(model, _id, **kwargs):
    try:
        obj = model.query.filter_by(id=_id).one()
        for key, value in kwargs:
            obj.__dict__[key] = value
    except:
        obj = model(id=_id, **kwargs)
    return obj


