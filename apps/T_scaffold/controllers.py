"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL, Field
from py4web.utils.factories import Inject
from pydal.validators import IS_IN_SET
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A
from .common import (
    db,
    session,
    T,
    cache,
    auth,
    logger,
    authenticated,
    unauthenticated,
    flash,
)


@action("index")
@action.uses("index.html", auth, T, Inject(T=T))
def index():

    user = auth.get_user()
    message = T("Hello {first_name}".format(**user) if user else T("Hello"))
    actions = {"allowed_actions": auth.param.allowed_actions}
    return dict(message=message, actions=actions)


@action("language_selector", method=["GET", "POST"])
@action.uses("language_selector.html", T, Inject(T=T))
def language_selector():
    disponibles = ["es", "it"]
    seleccionado = "_default"
    details = request.POST.keys()
    return dict(details=details, seleccionado=seleccionado)


@action("language_form", method=["GET", "POST"])
@action.uses("language_form.html", T, Inject(T=T))
def language_form():
    disponibles = ["es", "it"]
    seleccionado = "_default"
    form = Form(
        [
            Field("languages", "string", requires=IS_IN_SET(disponibles)),
        ],
        keep_values=True,
    )
    if form.accepted:
        # Do something with form.vars['product_name'] and form.vars['product_quantity']
        T.select(form.vars["languages"])
        seleccionado = form.vars["languages"]
    if form.errors:
        # display message error
        T.select("_default")
    return dict(form=form, seleccionado=seleccionado)
