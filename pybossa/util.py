# This file is part of PyBOSSA.
# 
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

import json
from flask import abort
from functools import wraps
from flaskext.wtf import Form, TextField, PasswordField, validators, ValidationError

def jsonpify(f):
    """Wraps JSONified output for JSONP"""
    from flask import request, current_app
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function

def authenticate(f):
    """Autenticate API based on api_key"""
    from flask import request, current_app
    import pybossa.model as model
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rules for anonymous visitors to allow to GET, PUT and POST tasks for
        # apps
        if request.endpoint == 'api.api_app' and request.method == 'GET': return f(*args, **kwargs)
        if request.endpoint == 'api.api_task' and request.method == 'GET': return f(*args, **kwargs)
        if request.endpoint == 'api.api_task' and request.method == 'PUT': return f(*args, **kwargs)
        if request.endpoint == 'api.api_taskrun' and request.method == 'POST': return f(*args, **kwargs)
        api_key = request.args.get('api_key')
        if api_key is None:
            return abort(403)
        else:
            # print "Validating API KEY:"
            # print api_key
            obj = model.Session.query(model.User).filter(model.User.api_key ==
                                                         api_key).first()
            if (obj == None): return abort(403)
            else: 
                return f(*args, **kwargs)
    return decorated_function

class Unique(object):
    """Validator that checks field uniqueness"""
    def __init__(self, session, model, field, message=None):
        self.session = session
        self.model = model
        self.field = field
        if not message:
            message = u'This item already exists'
        self.message = message

    def __call__(self, form, field):
        check = self.session.query(self.model).filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)

