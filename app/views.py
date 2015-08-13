#flask!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# views.py

from __future__ import print_function
from __future__ import division

import datetime

from app import app
from app.config import MAX_GRANTED_DAYS
from flask import render_template
from flask import jsonify
from flask import request
from flask import redirect
from flask import url_for

from app import models
from app import forms


@app.route('/')
@app.route('/index')
def index():
    return render_template('inicio.html')

@app.route('/users/')
def users():
    return render_template('users.html',
        title='Listado de usuarios',
        objects=models.User.query.all(),
        )

@app.route('/users/<int:id_user>/')
def user_detail(id_user):
    id_user = int(id_user)
    user = models.User.query.get(id_user)
    return render_template('user_detail.html',
        title=u'{} {}'.format(user.name, user.last_name),
        object=user,
        )

@app.route('/users/<int:id_user>/edit/', methods=('GET', 'POST'))
def user_edit(id_user):
    id_user = int(id_user)
    user = models.User.query.get(id_user)
    form = forms.UserEditForm(request.form, user)
    print('user: "{}"'.format(user))
    print('request.method: "{}"'.format(request.method))
    print('form.validate(): "{}"'.format(form.validate()))
    print('form.errors: "{}"'.format(form.errors))
    if request.method == 'POST' and form.validate():
        form.populate_obj(user)
        print('user (now): {}'.format(user))
        from app import db
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user_detail', id_user=id_user))
    else:
        return render_template('user_edit.html',
            title=u'{} {}'.format(user.name, user.last_name),
            object=user,
            form = form,
            )

#/
## Grupos / Groups
#/

@app.route('/groups/')
def groups():
    return render_template('groups.html',
        title='Listado de grupos',
        objects=models.Group.query.all(),
        )

@app.route('/groups/<id_group>/')
def group_detail(id_group):
    id_group = int(id_group)
    group = models.Group.query.get(id_group)
    return render_template('group_detail.html',
        title=group.name_group,
        object=group,
        )

#/
## Pagos / Payments
#/

@app.route('/payment/all/')
def payment_all():
    return render_template('payment.html',
        title='Listado de pagos',
        objects=models.Payment.query.all(),
        )


def _ok(result, **kwargs):
    response = {'status': 'ok', 'result': result}
    response.update(kwargs)
    return jsonify(response)

def _error(message, **kwargs):
    response = {'status': 'error', 'message': str(message)}
    response.update(kwargs)
    return jsonify(response)

@app.route('/api/1/device/<kind>/<code>/check')
def check_device(kind, code):
    try:
        device = models.Device.query.filter_by(kind=kind, code=code).first()
        if not device:
            return _ok(False,
                message='No existe el dispositivo [{}/{}]'.format(kind, code)
                )
        user = device.user
        today = datetime.date.today()
        month, year = today.month, today.year # current month
        payment = user.get_payment(month, year)
        if payment:
            return _ok(True, id_user=user.id_user, user_name=user.name, message=u'Bienvenido/a, {}'.format(user.name))

        # No payment
        msg = '{}: Pendiente abono {}/{}'.format(user.name, today.month, today.year)
        if today.day <= MAX_GRANTED_DAYS:
            # Previous month
            month, year = (month-1, year) if month > 1 else (12, year-1)
            payment = user.get_payment(month, year)
            if payment:
                return _ok(True, user_name=user.name, message=msg, id_user=user.id_user)
        # No day granted
        return _ok(False, message=msg, id_user=user.id_user, user_name=user.name)
    except Exception as err:
        return _error(err)

