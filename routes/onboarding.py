from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app_multitenant import mysql
from datetime import datetime, timedelta
import json

bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

@bp.route('/contratante', methods=['GET', 'POST'])
def contratante():
    if 'temp_user_id' not in session:
        return redirect(url_for('auth.registro'))
    
    if request.method == 'POST':
        razon_social = request.form['razon_social']
        rfc = request.form['rfc']
        email_contacto = request.form['email_contacto']
        telefono = request.form.get('telefono', '')
        direccion = request.form.get('direccion', '')
        ciudad = request.form.get('ciudad', '')
        estado = request.form.get('estado', '')
        cp = request.form.get('cp', '')
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO contratantes (razon_social, rfc, email_contacto, telefono, direccion, ciudad, estado, cp, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (razon_social, rfc, email_contacto, telefono, direccion, ciudad, estado, cp))
        mysql.connection.commit()
        contratante_id = cur.lastrowid
        cur.close()
        
        session['temp_contratante_id'] = contratante_id
        return redirect(url_for('onboarding.empresa'))
    
    return render_template('onboarding/contratante.html')

@bp.route('/empresa', methods=['GET', 'POST'])
def empresa():
    if 'temp_contratante_id' not in session:
        return redirect(url_for('onboarding.contratante'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        rfc = request.form['rfc']
        contratante_id = session['temp_contratante_id']
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO empresas (contratante_id, nombre, rfc, puede_compartir_rfc, activo)
            VALUES (%s, %s, %s, TRUE, TRUE)
        """, (contratante_id, nombre, rfc))
        mysql.connection.commit()
        empresa_id = cur.lastrowid
        cur.close()
        
        session['temp_empresa_id'] = empresa_id
        return redirect(url_for('onboarding.modulos'))
    
    return render_template('onboarding/empresa.html')

@bp.route('/modulos', methods=['GET', 'POST'])
def modulos():
    if 'temp_empresa_id' not in session:
        return redirect(url_for('onboarding.empresa'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM catalogo_modulos WHERE activo = TRUE ORDER BY orden")
    modulos_lista = cur.fetchall()
    
    if request.method == 'POST':
        modulos_seleccionados = request.form.getlist('modulos[]')
        empresa_id = session['temp_empresa_id']
        
        for modulo_id in modulos_seleccionados:
            cur.execute("""
                INSERT INTO empresa_modulos (empresa_id, modulo_id, activo)
                VALUES (%s, %s, TRUE)
            """, (empresa_id, modulo_id))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('onboarding.plan'))
    
    cur.close()
    return render_template('onboarding/modulos.html', modulos=modulos_lista)

@bp.route('/plan', methods=['GET', 'POST'])
def plan():
    if 'temp_empresa_id' not in session:
        return redirect(url_for('onboarding.modulos'))
    
    cur = mysql.connection.cursor()
    empresa_id = session['temp_empresa_id']
    contratante_id = session['temp_contratante_id']
    
    cur.execute("""
        SELECT cm.nombre, cm.precio_mensual, cm.precio_anual
        FROM empresa_modulos em
        JOIN catalogo_modulos cm ON em.modulo_id = cm.id
        WHERE em.empresa_id = %s AND em.activo = TRUE
    """, (empresa_id,))
    modulos_lista = cur.fetchall()
    
    subtotal_mensual = sum([float(m['precio_mensual']) for m in modulos_lista])
    subtotal_anual = sum([float(m['precio_anual']) for m in modulos_lista])
    
    if request.method == 'POST':
        tipo_plan = request.form['tipo_plan']
        
        if tipo_plan == 'MENSUAL':
            total = subtotal_mensual
            fecha_vencimiento = datetime.now() + timedelta(days=30)
        else:
            total = subtotal_anual
            fecha_vencimiento = datetime.now() + timedelta(days=365)
        
        cur.execute("""
            INSERT INTO suscripciones (contratante_id, tipo_plan, fecha_inicio, fecha_vencimiento, fecha_proximo_pago, subtotal, total, estado)
            VALUES (%s, %s, CURDATE(), %s, %s, %s, %s, 'ACTIVA')
        """, (contratante_id, tipo_plan, fecha_vencimiento, fecha_vencimiento, total, total))
        mysql.connection.commit()
        
        user_id = session['temp_user_id']
        cur.execute("""
            UPDATE usuarios 
            SET contratante_id = %s, empresa_id = %s, activo = TRUE, nombre = %s, empresas_acceso = %s
            WHERE id = %s
        """, (contratante_id, empresa_id, 'Director General', json.dumps([empresa_id]), user_id))
        mysql.connection.commit()
        cur.close()
        
        session.pop('temp_user_id', None)
        session.pop('temp_contratante_id', None)
        session.pop('temp_empresa_id', None)
        
        flash('¡Registro completado exitosamente! Por favor inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    cur.close()
    return render_template('onboarding/plan.html', modulos=modulos_lista, subtotal_mensual=subtotal_mensual, subtotal_anual=subtotal_anual)