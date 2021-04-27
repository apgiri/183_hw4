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
from yatl.helpers import A, SPAN
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash, Field
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from py4web.utils.form import Form, FormStyleBulma

url_signer = URLSigner(session)


# main page
@action('index')
@action.uses(db, auth.user, 'index.html')
def index():
    rows = db(db.contact.user_email == get_user_email()).select()
    return dict(rows=rows, url_signer=url_signer)


# add contact
@action('add', method=["GET", "POST"])
@action.uses(db, session, auth.user, 'add.html')
def add():
    form = Form(db.contact, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL('index'))
    return dict(form=form)


# edit a contact
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


# delete a contact
@action('delete/<contact_id:int>')
@action.uses(db, session, auth.user)
def delete(contact_id=None):
    assert contact_id is not None
    contact = db.contact[contact_id]
    if contact is None:
        redirect(URL('index'))
    db(db.contact.id == contact_id).delete()
    redirect(URL('index'))


# routes to phone numbers page of a particular contact/ table of numbers
@action('edit_phones/<contact_id:int>')
@action.uses(db, session, auth.user, 'edit_phones.html')
def add_phone(contact_id=None):
    assert contact_id is not None
    contact_inf = db.contact[contact_id]
    first_name = contact_inf.first_name
    last_name = contact_inf.last_name
    name = f"{first_name} {last_name}"
    rows = db(
        (db.phone.contact_id == contact_id) &
        (db.contact.id == db.phone.contact_id)
    ).select()
    return dict(rows=rows, url_signer=url_signer, name=name, owner_id=contact_id)


# add a number for a particular contact
@action('add_phone/<contact_id:int>', method=['GET', 'POST'])
@action.uses(db, session, auth.user, 'add_phone.html')
def add_phone(contact_id):
    assert contact_id is not None
    # contact_id is the id of the contact for which we are inserting an additional number
    contact_inf = db.contact[contact_id]
    form = Form([Field('Phone', 'string'), Field('Kind', 'string')], csrf_session=session, formstyle=FormStyleBulma)
    form.param.sidecar.append(SPAN(" ", A("Back", _class="button", _href=URL('edit_phones', contact_id))))

    if form.accepted:
        # insert the number for that contact
        number = form.vars['Phone']
        phone_type = form.vars['Kind']
        db.phone.insert(
            contact_id=contact_id,
            number=number,
            phone_type=phone_type
        )
        redirect(URL('edit_phones', contact_id))
    contact_inf = db.contact[contact_id]
    first_name = contact_inf.first_name
    last_name = contact_inf.last_name
    name = f"{first_name} {last_name}"
    return dict(form=form, name=name)


# delete a specified number of a specified contact
@action('delete_phone/<contact_id:int>/<phone_id:int>')
@action.uses(db, session, auth.user)
def delete_phone(contact_id=None, phone_id=None):
    assert contact_id is not None
    assert phone_id is not None
    # match the phone owner's id as well as the number's id
    row = db(
        (db.phone.contact_id == contact_id) &
        (db.phone.id == phone_id)
    ).select().first()
    # row.id is the id of the phone number being targeted
    if row.id is None:
        redirect(URL('edit_phones', contact_id))
    db(
        db.phone.id == row.id
    ).delete()
    redirect(URL('edit_phones', contact_id))


# edit a specified number of a specified contact
@action('edit_phone/<contact_id:int>/<phone_id:int>', method=['GET', 'POST'])
@action.uses(db, session, auth.user, 'edit_phone.html')
def edit_phone(contact_id=None, phone_id=None):
    assert contact_id is not None
    assert phone_id is not None
    # match the phone owner's id as well as the number's id
    row = db(
        (db.phone.contact_id == contact_id) &
        (db.phone.id == phone_id)
    ).select().first()
    if row is None:
        redirect(URL('edit_phones', contact_id))

    form = Form([Field('Phone', 'string'), Field('Kind', 'string')],
                record=dict(Phone=row.number, Kind=row.phone_type), deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    form.param.sidecar.append(SPAN(" ", A("Back", _class="button", _href=URL('edit_phones', contact_id))))

    if form.accepted:
        # insert the number for that contact
        number = form.vars['Phone']
        phone_type = form.vars['Kind']
        db((db.phone.contact_id == contact_id) & (db.phone.id == phone_id)).update(
            number=number,
            phone_type=phone_type
        )
        redirect(URL('edit_phones', contact_id))

    contact_inf = db.contact[contact_id]
    first_name = contact_inf.first_name
    last_name = contact_inf.last_name
    name = f"{first_name} {last_name}"
    return dict(form=form, name=name)