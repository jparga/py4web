from py4web import action
from py4web.utils.form import Form
from .common import db, session



@action("index", method=["GET", "POST"])
@action.uses("index.html", db, session)
def index():
    form = Form(db.thing)
    things = db(db.thing).select()
    return locals()
