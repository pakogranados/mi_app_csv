"""Decoradores compartidos del sistema multi-tenant"""
from flask import session, abort, g, redirect, url_for, flash
from functools import wraps

def get_db():
    """Importación lazy para evitar circular imports"""
    from app import mysql
    return mysql

def require_login(f):
    """Decorador que requiere que el usuario esté logueado y carga contexto multi-tenant"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id") or not session.get("empresa_id") or not session.get("contratante_id"):
            flash('Debes iniciar sesión primero', 'warning')
            return redirect(url_for('auth.login'))
        
        g.user_id = int(session["user_id"])
        g.empresa_id = int(session["empresa_id"])
        g.contratante_id = int(session["contratante_id"])
        g.rango = int(session.get("rango", 4))
        g.empresas_acceso = session.get("empresas_acceso", [])
        g.puede_agregar_usuarios = session.get("puede_agregar_usuarios", False)
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(role):
    """Decorador que requiere un rol específico (admin/editor)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('rol') != role:
                flash('No tienes el rol necesario para esta acción', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorator
    return decorator

def require_rango(nivel_maximo):
    """
    Decorador que requiere un rango organizacional específico
    Niveles: 1=Director General, 2=Gerente, 3=Jefe Depto, 4=Empleado
    Nivel más bajo = más permisos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rango_actual = session.get('rango', 4)
            if rango_actual > nivel_maximo:
                flash('No tienes el nivel jerárquico necesario para esta acción', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_module(module_code):
    """
    Decorador que verifica que el módulo esté activo para la empresa actual
    Ejemplo: @require_module('VENTAS')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            empresa_id = session.get('empresa_id')
            if not empresa_id:
                flash('No tienes una empresa seleccionada', 'danger')
                return redirect(url_for('dashboard.index'))
            
            mysql = get_db()
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT em.activo 
                FROM empresa_modulos em
                JOIN catalogo_modulos cm ON em.modulo_id = cm.id
                WHERE em.empresa_id = %s AND cm.codigo = %s AND em.activo = TRUE
            """, (empresa_id, module_code))
            modulo = cur.fetchone()
            cur.close()
            
            if not modulo:
                flash(f'El módulo {module_code} no está activo para esta empresa', 'danger')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_contratante_activo(f):
    """Verifica que el contratante esté activo (suscripción vigente)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        contratante_id = session.get('contratante_id')
        if not contratante_id:
            flash('No tienes un contratante asignado', 'danger')
            return redirect(url_for('auth.login'))
        
        mysql = get_db()
        cur = mysql.connection.cursor()
        cur.execute("SELECT activo FROM contratantes WHERE id = %s", (contratante_id,))
        contratante = cur.fetchone()
        cur.close()
        
        if not contratante or not contratante['activo']:
            session.clear()
            flash('Tu cuenta ha sido suspendida. Contacta a soporte.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_empresa_access(f):
    """Verifica que el usuario tenga acceso a la empresa actual"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        empresa_id = session.get('empresa_id')
        empresas_acceso = session.get('empresas_acceso', [])
        
        if empresa_id not in empresas_acceso:
            flash('No tienes acceso a esta empresa', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_puede_crear_usuarios(f):
    """Verifica que el usuario tenga permiso para crear otros usuarios"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('puede_agregar_usuarios', False):
            flash('No tienes permiso para agregar usuarios', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def require_reportes_consolidados(f):
    """Verifica que el usuario pueda ver reportes consolidados (rangos 1 y 2)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        rango = session.get('rango', 4)
        if rango > 2:
            flash('No tienes permiso para ver reportes consolidados', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorador combinado: requiere login + rol admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash('Debes iniciar sesión primero', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('rol') != 'admin':
            flash('Requiere permisos de administrador', 'danger')
            return redirect(url_for('dashboard.index'))
        
        g.user_id = int(session["user_id"])
        g.empresa_id = int(session["empresa_id"])
        g.contratante_id = int(session["contratante_id"])
        
        return f(*args, **kwargs)
    return decorated_function

def require_super_admin(f):
    """Decorador para super administrador del sistema (ID = 1 o flag especial)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        
        mysql = get_db()
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT es_super_admin 
            FROM usuarios 
            WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        cur.close()
        
        if not user or not user.get('es_super_admin'):
            flash('Requiere permisos de super administrador', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def before_request_global():
    """
    Función para usar con @app.before_request
    Carga automáticamente el contexto multi-tenant en todas las peticiones
    """
    if session.get('user_id'):
        g.user_id = session.get('user_id')
        g.empresa_id = session.get('empresa_id')
        g.contratante_id = session.get('contratante_id')
        g.rango = session.get('rango', 4)
        g.empresas_acceso = session.get('empresas_acceso', [])
        g.puede_agregar_usuarios = session.get('puede_agregar_usuarios', False)
        g.user_name = session.get('user_name', '')
        g.user_email = session.get('user_email', '')