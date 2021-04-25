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

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from py4web.utils.form import Form, FormStyleBulma

url_signer = URLSigner(session)


@action('index')
@action.uses(db, auth.user, 'index.html')
def index():
    rows = db(db.contact.user_email == get_user_email()).select()
    return dict(rows=rows, url_signer=url_signer)


@action('add', method=["GET", "POST"])
@action.uses(db, session, auth.user, 'add.html')
def add():
    form = Form(db.contact, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('index'))
    return dict(form=form)


@action('edit/<contact_id:int>', method=['GET', 'POST'])
@action.uses(db, session, auth.user, 'edit.html')
def edit(contact_id=None):
    if contact_id is None:
        redirect(URL('index'))

    p = db.contact[contact_id]
    if p is None:
        redirect(URL('index'))

    form = Form(db.contact, record=p, csrf_session=session, deletable=False, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('index'))
    return dict(form=form)


@action('delete/<contact_id:int>')
@action.uses(db, session, auth.user)
def delete(contact_id=None):
    assert contact_id is not None
    contact = db.contact[contact_id]
    if contact is None:
        redirect(URL('index'))
    db(db.contact.id == contact_id).delete()
    redirect(URL('index'))



