from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import json

bp = Blueprint('auth', __name__)




@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = get_mysql().connection.cursor()
        cur.execute("""
            SELECT u.*, c.activo as contratante_activo, c.razon_social, e.nombre as empresa_nombre
            FROM usuarios u
            LEFT JOIN contratantes c ON u.contratante_id = c.id
            LEFT JOIN empresas e ON u.empresa_id = e.id
            WHERE u.correo = %s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['contrasena'], password):
            if not user['activo']:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            if not user['contratante_activo']:
                flash('La cuenta del contratante está suspendida.', 'danger')
                return redirect(url_for('auth.login'))
            
            session['user_id'] = user['id']
            session['user_name'] = user['nombre']
            session['user_email'] = user['correo']
            session['contratante_id'] = user['contratante_id']
            session['empresa_id'] = user['empresa_id']
            session['rango'] = user['rango']
            session['puede_agregar_usuarios'] = user['puede_agregar_usuarios']
            session['empresas_acceso'] = json.loads(user['empresas_acceso']) if user['empresas_acceso'] else [user['empresa_id']]
            
            flash(f'Bienvenido {user["nombre"]}', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('auth.registro'))
        
        cur = get_mysql().connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE correo = %s", (email,))
        if cur.fetchone():
            flash('El email ya está registrado', 'danger')
            cur.close()
            return redirect(url_for('auth.registro'))
        
        hashed_password = generate_password_hash(password)
        cur.execute("""
            INSERT INTO usuarios (correo, contrasena, nombre, activo, rango, puede_agregar_usuarios, rol) 
            VALUES (%s, %s, %s, FALSE, 1, TRUE, 'admin')
        """, (email, hashed_password, 'Usuario Temporal'))
        get_mysql().connection.commit()
        user_id = cur.lastrowid
        cur.close()
        
        session['temp_user_id'] = user_id
        return redirect(url_for('onboarding.contratante'))
    
    return render_template('registro.html')

def get_mysql():
    """Importación lazy para evitar circular imports"""
    from app_multitenant import mysql
    return mysql


bp = Blueprint('auth', __name__)
