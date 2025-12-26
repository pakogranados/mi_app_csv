from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from utils.decorators import require_login, require_rango, require_puede_crear_usuarios
from werkzeug.security import generate_password_hash
from app_multitenant import mysql
import json

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/configuracion/contratante', methods=['GET', 'POST'])
@require_login
@require_rango(1)
def config_contratante():
    cur = get_mysql().connection.cursor()
    
    if request.method == 'POST':
        razon_social = request.form['razon_social']
        rfc = request.form['rfc']
        email_contacto = request.form['email_contacto']
        telefono = request.form.get('telefono', '')
        direccion = request.form.get('direccion', '')
        ciudad = request.form.get('ciudad', '')
        estado = request.form.get('estado', '')
        cp = request.form.get('cp', '')
        
        cur.execute("""
            UPDATE contratantes 
            SET razon_social = %s, rfc = %s, email_contacto = %s, telefono = %s,
                direccion = %s, ciudad = %s, estado = %s, cp = %s
            WHERE id = %s
        """, (razon_social, rfc, email_contacto, telefono, direccion, ciudad, estado, cp, g.contratante_id))
        get_mysql().connection.commit()
        flash('Información del contratante actualizada exitosamente', 'success')
    
    cur.execute("SELECT * FROM contratantes WHERE id = %s", (g.contratante_id,))
    contratante = cur.fetchone()
    cur.close()
    
    return render_template('admin/config_contratante.html', contratante=contratante)

@bp.route('/configuracion/empresas')
@require_login
@require_rango(1)
def config_empresas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM empresas WHERE contratante_id = %s ORDER BY nombre", (g.contratante_id,))
    empresas = cur.fetchall()
    cur.close()
    return render_template('admin/config_empresas.html', empresas=empresas)

@bp.route('/configuracion/empresas/nueva', methods=['POST'])
@require_login
@require_rango(1)
def nueva_empresa():
    nombre = request.form['nombre']
    rfc = request.form['rfc']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO empresas (contratante_id, nombre, rfc, puede_compartir_rfc, activo)
        VALUES (%s, %s, %s, TRUE, TRUE)
    """, (g.contratante_id, nombre, rfc))
    get_mysql().connection.commit()
    cur.close()
    
    flash('Empresa creada exitosamente', 'success')
    return redirect(url_for('admin.config_empresas'))

@bp.route('/configuracion/modulos')
@require_login
@require_rango(1)
def config_modulos():
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT * FROM empresas WHERE contratante_id = %s ORDER BY nombre", (g.contratante_id,))
    empresas = cur.fetchall()
    
    cur.execute("SELECT * FROM catalogo_modulos WHERE activo = TRUE ORDER BY orden")
    modulos = cur.fetchall()
    
    modulos_empresa = {}
    for empresa in empresas:
        cur.execute("""
            SELECT modulo_id, activo 
            FROM empresa_modulos 
            WHERE empresa_id = %s
        """, (empresa['id'],))
        modulos_empresa[empresa['id']] = {m['modulo_id']: m['activo'] for m in cur.fetchall()}
    
    cur.close()
    return render_template('admin/config_modulos.html', empresas=empresas, modulos=modulos, modulos_empresa=modulos_empresa)

@bp.route('/configuracion/modulos/toggle', methods=['POST'])
@require_login
@require_rango(1)
def toggle_modulo():
    data = request.json
    empresa_id = data['empresa_id']
    modulo_id = data['modulo_id']
    activo = data['activo']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id FROM empresa_modulos WHERE empresa_id = %s AND modulo_id = %s
    """, (empresa_id, modulo_id))
    existe = cur.fetchone()
    
    if existe:
        cur.execute("""
            UPDATE empresa_modulos SET activo = %s WHERE empresa_id = %s AND modulo_id = %s
        """, (activo, empresa_id, modulo_id))
    else:
        cur.execute("""
            INSERT INTO empresa_modulos (empresa_id, modulo_id, activo) VALUES (%s, %s, %s)
        """, (empresa_id, modulo_id, activo))
    
    get_mysql().connection.commit()
    cur.close()
    
    return jsonify({'success': True})

@bp.route('/configuracion/usuarios')
@require_login
@require_rango(2)
def config_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.*, r.nombre as rango_nombre, e.nombre as empresa_nombre
        FROM usuarios u
        LEFT JOIN rangos_organizacionales r ON u.rango = r.nivel
        LEFT JOIN empresas e ON u.empresa_id = e.id
        WHERE u.contratante_id = %s
        ORDER BY u.rango, u.nombre
    """, (g.contratante_id,))
    usuarios = cur.fetchall()
    
    cur.execute("SELECT * FROM empresas WHERE contratante_id = %s ORDER BY nombre", (g.contratante_id,))
    empresas = cur.fetchall()
    
    cur.execute("SELECT * FROM rangos_organizacionales ORDER BY nivel")
    rangos = cur.fetchall()
    
    cur.close()
    return render_template('admin/config_usuarios.html', usuarios=usuarios, empresas=empresas, rangos=rangos)

@bp.route('/configuracion/usuarios/nuevo', methods=['POST'])
@require_login
@require_rango(2)
@require_puede_crear_usuarios
def nuevo_usuario():
    nombre = request.form['nombre']
    email = request.form['email']
    password = request.form['password']
    empresa_id = request.form['empresa_id']
    rango = request.form['rango']
    empresas_acceso = request.form.getlist('empresas_acceso[]')
    puede_agregar = 'puede_agregar_usuarios' in request.form
    rol = request.form.get('rol', 'editor')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE correo = %s", (email,))
    if cur.fetchone():
        flash('El email ya está registrado', 'danger')
        return redirect(url_for('admin.config_usuarios'))
    
    hashed_password = generate_password_hash(password)
    cur.execute("""
        INSERT INTO usuarios (contratante_id, empresa_id, nombre, correo, contrasena, rango, empresas_acceso, puede_agregar_usuarios, activo, rol)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
    """, (g.contratante_id, empresa_id, nombre, email, hashed_password, rango, json.dumps(empresas_acceso), puede_agregar, rol))
    get_mysql().connection.commit()
    cur.close()
    
    flash('Usuario creado exitosamente', 'success')
    return redirect(url_for('admin.config_usuarios'))

@bp.route('/configuracion/usuarios/editar/<int:usuario_id>', methods=['POST'])
@require_login
@require_rango(2)
def editar_usuario(usuario_id):
    nombre = request.form['nombre']
    empresa_id = request.form['empresa_id']
    rango = request.form['rango']
    empresas_acceso = request.form.getlist('empresas_acceso[]')
    puede_agregar = 'puede_agregar_usuarios' in request.form
    activo = 'activo' in request.form
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE usuarios 
        SET nombre = %s, empresa_id = %s, rango = %s, empresas_acceso = %s, 
            puede_agregar_usuarios = %s, activo = %s
        WHERE id = %s AND contratante_id = %s
    """, (nombre, empresa_id, rango, json.dumps(empresas_acceso), puede_agregar, activo, usuario_id, g.contratante_id))
    get_mysql().connection.commit()
    cur.close()
    
    flash('Usuario actualizado exitosamente', 'success')
    return redirect(url_for('admin.config_usuarios'))

@bp.route('/configuracion/usuarios/eliminar/<int:usuario_id>', methods=['POST'])
@require_login
@require_rango(1)
def eliminar_usuario(usuario_id):
    if usuario_id == g.user_id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.config_usuarios'))
    
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM usuarios 
        WHERE id = %s AND contratante_id = %s
    """, (usuario_id, g.contratante_id))
    mget_mysql().connection.commit()
    cur.close()
    
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('admin.config_usuarios'))


def get_mysql():
    """Importación lazy para evitar circular imports"""
    from app_multitenant import mysql
    return mysql