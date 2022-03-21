"""
This file defines the database models
"""

from .common import db, Field, T, session
from pydal.validators import *


def set_lang():
    try:
        T.select(session["idioma"])
    except:
        session["idioma"] = "_default"
        T.select(session["idioma"])
        pass
    return session["idioma"]


### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
db.commit()
#
