"""
This file defines the database models
"""

from .common import db, Field
from pydal.validators import *

### Define your table below

db.define_table(
    'thing',
    Field('name', required=True),
    Field('image', 'upload')
)
db.commit()
