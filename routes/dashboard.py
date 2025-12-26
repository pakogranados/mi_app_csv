from flask import Blueprint, render_template, session
from utils.decorators import require_login, require_contratante_activo
from app_multitenant import mysql

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@require_login
@require_contratante_activo
def index():
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT cm.codigo, cm.nombre, cm.icono, cm.color
        FROM empresa_modulos em
        JOIN catalogo_modulos cm ON em.modulo_id = cm.id
        WHERE em.empresa_id = %s AND em.activo = TRUE
        ORDER BY cm.orden
    """, (session['empresa_id'],))
    modulos_activos = cur.fetchall()
    
    cur.execute("""
        SELECT s.*, DATEDIFF(s.fecha_vencimiento, CURDATE()) as dias_restantes
        FROM suscripciones s
        WHERE s.contratante_id = %s AND s.estado = 'ACTIVA'
        ORDER BY s.fecha_vencimiento DESC
        LIMIT 1
    """, (session['contratante_id'],))
    suscripcion = cur.fetchone()
    
    cur.close()
    return render_template('dashboard.html', modulos=modulos_activos, suscripcion=suscripcion)