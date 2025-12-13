# utils/decorators.py
"""Decoradores compartidos del sistema"""
from flask import session, abort, g
from functools import wraps

def require_login(f):
    """Decorador que requiere que el usuario esté logueado y carga contexto"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("usuario_id") or not session.get("empresa_id"):
            abort(401)
        g.empresa_id = int(session["empresa_id"])
        g.usuario_id = int(session["usuario_id"])
        return f(*args, **kwargs)
    return decorated_function

def require_role(role):
    """Decorador que requiere un rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('rol') != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator