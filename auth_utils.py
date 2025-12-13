# auth_utils.py

from functools import wraps
from flask import session, redirect, url_for, flash

# Si ya tienes require_role aquí, déjalo. Solo añade este decorador:

def require_login(f):
    """
    Decorador simple para exigir que el usuario haya iniciado sesión
    (usa session['usuario_id']).
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper
