"""
    app.py - Aplicación Flask para un sistema ERP básico.
    Incluye autenticación de usuarios, control de inventario y registro de compras.
"""

# ===== IMPORTS ESTÁNDAR =====
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, Blueprint, g
from flask_cors import CORS
from flask_mail import Mail, Message
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import jwt
from datetime import datetime, timedelta
import re
from functools import wraps
import bcrypt
from flask_mysqldb import MySQL
import secrets
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import csv
import sys

# ===== DETECTAR ENTORNO (PythonAnywhere vs Local) =====
if '/home/' in os.getcwd():
    try:
        from config_pythonanywhere import Config
    except:
        from config import Config
else:
    from config import Config

# ===== CARGAR VARIABLES DE ENTORNO =====
from dotenv import load_dotenv
load_dotenv()

# ===== CREAR LA APP DE FLASK =====
app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)

# ===== IMPORTS DE MÓDULOS LOCALES =====
from db import conexion_db
from utils.decorators import require_login, require_role

# Importar blueprints del sistema multi-tenant
try:
    from routes import auth, onboarding, dashboard, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(onboarding.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(admin.bp)
except ImportError:
    pass  # Los blueprints se cargarán más adelante en el código

# ===== IMPORTAR API BLUEPRINT =====
try:
    from api import api as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
except ImportError:
    pass


# ===== CONFIGURACIÓN DE MAIL (LEE DESDE .env) =====
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = os.environ.get('DEBUG', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'pakogranados1@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'rpar bqac dhmu ftjh')
app.config['MAIL_DEFAULT_SENDER'] = ('ERP Sistema', os.environ.get('MAIL_DEFAULT_SENDER', 'pakogranados1@gmail.com'))
app.config["API_JWT_SECRET"] = "%Interely8711"

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}


# Debug (solo en desarrollo)
if os.environ.get('FLASK_ENV') == 'development':
    print("=" * 60)
    print("🔧 DEBUG - Configuración cargada desde .env:")
    print(f"  DB_USER: {os.environ.get('DB_USER')}")
    print(f"  MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"  MAIL_PASSWORD: {'********' if app.config['MAIL_PASSWORD'] else '(no configurada)'}")
    print("=" * 60)

mail = Mail(app)

# ===== CORS =====
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ===== IMPORTAR DECORADORES DESDE UTILS =====
from utils.decorators import require_login, require_role


# ===== MAIL =====

def generar_token():
    """Genera un token seguro de 32 caracteres"""
    return secrets.token_urlsafe(32)

def enviar_email_confirmacion(correo, nombre, token):
    """Envía email de confirmación de registro"""
    try:
        link = url_for('confirmar_email', token=token, _external=True)
        
        msg = Message(
            subject='Confirma tu cuenta - ERP Sistema',
            recipients=[correo]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .content {{ padding: 30px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 ¡Bienvenido al ERP Sistema!</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre}</strong>,</p>
                    <p>Gracias por registrarte en nuestro sistema. Para completar tu registro y activar tu cuenta, por favor confirma tu correo electrónico haciendo clic en el siguiente botón:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{link}" class="button">Confirmar mi cuenta</a>
                    </p>
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="background: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
                        {link}
                    </p>
                    <p><strong>Este enlace es válido por 24 horas.</strong></p>
                </div>
                <div class="footer">
                    <p>Si no solicitaste esta cuenta, puedes ignorar este mensaje.</p>
                    <p>&copy; 2025 ERP Sistema. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email de confirmación: {e}")
        import traceback
        traceback.print_exc()
        return False

def enviar_email_reset_password(correo, nombre, token):
    """Envía email para recuperar contraseña"""
    try:
        link = url_for('reset_password', token=token, _external=True)
        
        msg = Message(
            subject='Recuperar contraseña - ERP Sistema',
            recipients=[correo]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .content {{ padding: 30px 0; }}
                .button {{ display: inline-block; background: #f5576c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Recuperar Contraseña</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre}</strong>,</p>
                    <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. Si no fuiste tú, puedes ignorar este mensaje.</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{link}" class="button">Cambiar mi contraseña</a>
                    </p>
                    <p>O copia y pega este enlace en tu navegador:</p>
                    <p style="background: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
                        {link}
                    </p>
                    <div class="warning">
                        <strong>⚠️ Importante:</strong> Este enlace es válido por solo <strong>1 hora</strong> por razones de seguridad.
                    </div>
                </div>
                <div class="footer">
                    <p>Si no solicitaste este cambio, ignora este mensaje y tu contraseña permanecerá sin cambios.</p>
                    <p>&copy; 2025 ERP Sistema. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email de reset: {e}")
        import traceback
        traceback.print_exc()
        return False

def require_token(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        
        if not auth.startswith("Bearer "):
            return jsonify({
                "ok": False,
                "error": "Token no proporcionado"
            }), 401

        token = auth.replace("Bearer ", "").strip()

        try:
            payload = jwt.decode(
                token,
                app.config["API_JWT_SECRET"],
                algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"ok": False, "error": "Token expirado"}), 401
        except Exception:
            return jsonify({"ok": False, "error": "Token inválido"}), 401

        request.api_user = payload
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper



# ===== FUNCIONES HELPER =====

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("usuario_id") or not session.get("empresa_id"):
            abort(401)
        g.empresa_id = int(session["empresa_id"])
        g.usuario_id = int(session["usuario_id"])
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    """Carga contexto multi-tenant automáticamente en cada petición"""
    # Variables básicas de sesión
    g.user_id = session.get('user_id')
    g.usuario_id = session.get('user_id')  # Compatibilidad con código existente
    g.empresa_id = session.get('empresa_id')
    g.contratante_id = session.get('contratante_id')
    g.rango = session.get('rango', 4)
    g.empresas_acceso = session.get('empresas_acceso', [])
    g.puede_agregar_usuarios = session.get('puede_agregar_usuarios', False)
    g.user_name = session.get('user_name', '')
    g.usuario_nombre = session.get('user_name', '')  # Compatibilidad
    g.user_email = session.get('user_email', '')
    g.rol = session.get('rol', 'editor')
    g.es_admin = session.get('rol') == 'admin'
    
    # Variables de empresa (se cargan dinámicamente)
    g.empresa_nombre = None
    g.empresa_logo = None
    g.empresas_usuario = []
    g.usuario_areas = []
    
    # Si el usuario está logueado, cargar información adicional
    if g.user_id and g.empresa_id:
        try:
            cur = mysql.connection.cursor()
            
            # Cargar info de la empresa actual
            cur.execute("""
                SELECT nombre, logo_url 
                FROM empresas 
                WHERE id = %s AND contratante_id = %s
            """, (g.empresa_id, g.contratante_id))
            empresa_actual = cur.fetchone()
            
            if empresa_actual:
                g.empresa_nombre = empresa_actual['nombre']
                g.empresa_logo = empresa_actual.get('logo_url')
            
            # Cargar áreas del usuario (si la tabla existe - compatibilidad)
            try:
                cur.execute("""
                    SELECT a.codigo, a.nombre, ua.rol_area
                    FROM usuario_areas ua
                    JOIN areas_sistema a ON a.id = ua.area_id
                    WHERE ua.usuario_id = %s 
                      AND ua.empresa_id = %s 
                      AND ua.activo = 1
                      AND a.activo = 1
                """, (g.user_id, g.empresa_id))
                areas = cur.fetchall()
                g.usuario_areas = [a['codigo'] for a in areas]
            except:
                # Si no existe la tabla usuario_areas, continuar
                g.usuario_areas = []
            
            # Admin tiene acceso a todo
            if g.es_admin or g.rango <= 2:
                g.usuario_areas = ['ADMIN', 'VENTAS', 'INVENTARIO', 'COMPRAS', 'CAJA', 
                                   'CXC', 'CXP', 'CONTABILIDAD', 'RRHH', 'GASTOS',
                                   'B2B_CLIENTE', 'B2B_PROVEEDOR', 'REPARTO', 
                                   'ADMINISTRACION', 'REPORTES', 'AUDITORIA']
            
            # Cargar lista de empresas del contratante (para selector)
            if g.rango <= 2:  # Director General o Gerente
                cur.execute("""
                    SELECT id, nombre 
                    FROM empresas 
                    WHERE contratante_id = %s AND activo = 1 
                    ORDER BY nombre
                """, (g.contratante_id,))
                g.empresas_usuario = cur.fetchall()
            else:
                # Usuarios de rango inferior solo ven las empresas a las que tienen acceso
                if g.empresas_acceso:
                    placeholders = ','.join(['%s'] * len(g.empresas_acceso))
                    cur.execute(f"""
                        SELECT id, nombre 
                        FROM empresas 
                        WHERE id IN ({placeholders}) AND activo = 1 
                        ORDER BY nombre
                    """, g.empresas_acceso)
                    g.empresas_usuario = cur.fetchall()
            
            cur.close()
                
        except Exception as e:
            print(f"⚠️ Error cargando contexto empresa: {e}")
            # En caso de error, asegurar valores por defecto
            g.empresa_nombre = None
            g.empresa_logo = None
            g.empresas_usuario = []
            g.usuario_areas = []

from routes import auth, onboarding, dashboard, admin



@app.context_processor
def inject_user():
    """Hace disponibles las variables de sesión en todos los templates"""
    return dict(
        user_id=g.get('user_id'),
        usuario_id=g.get('usuario_id'),
        user_name=g.get('user_name'),
        usuario_nombre=g.get('usuario_nombre'),
        user_email=g.get('user_email'),
        empresa_id=g.get('empresa_id'),
        empresa_nombre=g.get('empresa_nombre'),
        empresa_logo=g.get('empresa_logo'),
        contratante_id=g.get('contratante_id'),
        rango=g.get('rango'),
        rol=g.get('rol'),
        es_admin=g.get('es_admin'),
        puede_agregar_usuarios=g.get('puede_agregar_usuarios', False),
        empresas_usuario=g.get('empresas_usuario', []),
        usuario_areas=g.get('usuario_areas', [])
    )

            
@app.route('/cambiar-empresa/<int:empresa_id>', methods=['POST'])
@require_login
def cambiar_empresa(empresa_id):
    """Permite al usuario cambiar de empresa activa"""
    uid = g.usuario_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Verificar que la empresa existe y está activa
        cur.execute("""
            SELECT id, nombre 
            FROM empresas 
            WHERE id = %s AND activo = 1
        """, (empresa_id,))
        
        empresa = cur.fetchone()
        
        if empresa:
            session['empresa_id'] = empresa_id
            flash(f'✅ Cambiado a: {empresa["nombre"]}', 'success')
        else:
            flash('❌ Empresa no disponible', 'danger')
        
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(request.referrer or url_for('panel_de_control'))


# --- Caja de cobro (Flask) ---

def d(x):  # Decimal seguro
    try:
        return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except:
        return Decimal("0.00")

def _totales(carrito, aplica_iva=True):

    subtotal = Decimal("0.00")
    iva_total = Decimal("0.00")

    for r in carrito:
        cant = d(r.get("cant", 0))
        pu = d(r.get("pu", 0))
        desc = d(r.get("desc", 0))
        iva_rate = d(r.get("iva", 0))  # tasa guardada en el item (ej. 0.16)

        base = cant * pu - desc
        if base < 0:
            base = Decimal("0.00")

        if not aplica_iva:
            iva_rate = Decimal("0.00")

        iva_val = (base * iva_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += base
        iva_total += iva_val

    total = (subtotal + iva_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "subtotal": subtotal,
        "iva": iva_total,
        "total": total
    }

@app.post("/caja/agregar")
@require_login
def caja_agregar():
    # Asegura estructuras en sesión
    session.setdefault("carrito", [])

    # Datos desde el form
    mercancia_id = request.form.get("mercancia_id", type=int)
    nombre       = (request.form.get("nombre") or "").strip()
    cant_raw     = request.form.get("cant", "1")
    pu_raw       = request.form.get("pu")               # puede venir vacío o "0.00"
    iva_raw      = request.form.get("iva_rate", "0")
    desc_raw     = request.form.get("desc", "0")

    if not nombre:
        flash("Producto requerido", "warning")
        return redirect(url_for("caja"))

    # Normalización a Decimal (evita floats)
    from decimal import Decimal, InvalidOperation

    def d(x, fallback="0"):
        try:
            return Decimal(str(x))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(fallback)

    cant = d(cant_raw, "1")
    if cant <= 0:
        cant = Decimal("1")

    # Precio: si no viene o es 0, calcular según configuración PT de esta empresa
    pu = None
    try:
        pu_tmp = d(pu_raw, None) if pu_raw not in (None, "") else None
        if pu_tmp is not None and pu_tmp > 0:
            pu = pu_tmp
    except Exception:
        pu = None

    if pu is None:
        if mercancia_id:
            # Debes tener implementada esta función con empresa:
            # def precio_pt(mercancia_id: int, empresa_id: int) -> Decimal
            pu = precio_pt(mercancia_id, g.empresa_id)
        else:
            pu = Decimal("0.00")

    iva  = d(iva_raw, "0")
    desc = d(desc_raw, "0")
    if desc < 0:
        desc = Decimal("0")

    # Construir renglón con claves compatibles con tu _totales() y templates
    item = {
        "id": mercancia_id,              # usa "id" si tu flujo lo espera así
        "mercancia_id": mercancia_id,    # mantén ambos por compatibilidad
        "nombre": nombre,
        "cant": str(cant),               # guarda como texto; el template lo formatea
        "pu": str(pu.quantize(Decimal("0.01"))),
        "iva": str(iva),                 # si tu _totales usa esta clave
        "desc": str(desc),
    }

    session["carrito"].append(item)
    session.modified = True
    return redirect(url_for("caja"))

@app.post("/caja/eliminar/<int:idx>")
def caja_eliminar(idx):
    session.setdefault("carrito", [])
    if 0 <= idx < len(session["carrito"]):
        session["carrito"].pop(idx)
        session.modified = True
    return redirect(url_for("caja"))

@app.post("/caja/vaciar")
def caja_vaciar():
    session["carrito"] = []
    session.modified = True
    return redirect(url_for("caja"))

from decimal import Decimal

@app.post("/caja_cobrar")
@require_login
def caja_cobrar():
    eid = g.empresa_id
    uid = g.usuario_id

    carrito = session.get("carrito", [])
    aplica_iva = session.get("caja_aplica_iva", True)
    totals = _totales(carrito, aplica_iva)

    if not carrito:
        return redirect(url_for("caja"))

    total = totals.get("total", Decimal("0.00"))
    if not isinstance(total, Decimal):
        total = Decimal(str(total))
    total = total.quantize(Decimal("0.01"))

    tipo        = request.form.get("tipo") or "ticket"
    forma_pago  = request.form.get("forma_pago") or "Efectivo"
    metodo_pago = request.form.get("metodo_pago") or "PUE"

    raw_cobro = (request.form.get("monto_cobrado") or "").replace(",", "").strip()
    try:
        cobro = Decimal(raw_cobro) if raw_cobro else total
    except Exception:
        cobro = total
    cobro = cobro.quantize(Decimal("0.01"))

    cambio = cobro - total
    if cambio < Decimal("0"):
        cambio = Decimal("0.00")
    cambio = cambio.quantize(Decimal("0.01"))

    conn = None
    cur = None
    try:
        conn = conexion_db()
        cur = conn.cursor()

        # Encabezado (incluye empresa)
        cur.execute(
            """
            INSERT INTO caja_ventas (fecha, usuario_id, total, empresa_id)
            VALUES (NOW(), %s, %s, %s)
            """,
            (uid, total, eid)
        )
        venta_id = cur.lastrowid

        # Detalle (incluye empresa)
        for r in carrito:
            mercancia_id = r.get("id") or r.get("mercancia_id")
            if not mercancia_id:
                continue

            cant = Decimal(str(r.get("cant", 1) or 1))
            pu   = Decimal(str(r.get("pu", 0) or 0))
            desc = Decimal(str(r.get("desc", 0) or 0))

            if cant <= 0:
                cant = Decimal("1")
            if pu   < 0:
                pu = Decimal("0.00")
            if desc < 0:
                desc = Decimal("0.00")

            subtotal = (cant * pu - desc)
            if subtotal < Decimal("0"):
                subtotal = Decimal("0.00")
            subtotal = subtotal.quantize(Decimal("0.01"))
            pu = pu.quantize(Decimal("0.01"))

            cur.execute(
                """
                INSERT INTO caja_ventas_detalle
                  (venta_id, mercancia_id, cantidad, precio_unitario, subtotal, empresa_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (venta_id, mercancia_id, cant, pu, subtotal, eid)
            )

        conn.commit()

    finally:
        try:
            if cur: cur.close()
        except Exception:
            pass
        try:
            if conn: conn.close()
        except Exception:
            pass

    # Limpiar carrito
    session["carrito"] = []

    # Redirigir a ticket con cobro/cambio formateados
    return redirect(url_for(
        "caja_ticket",
        venta_id=venta_id,
        cobro=f"{cobro}",
        cambio=f"{cambio}"
    ))

@app.post("/caja/hold")
def caja_hold():
    carrito = session.get("carrito", [])
    if not carrito:
        flash("No hay nada que poner en espera.", "warning")
        return redirect(url_for("caja"))

    holds = session.get("caja_holds", [])

    hold_id = (max([h["id"] for h in holds]) + 1) if holds else 1

    totals = _totales(carrito)
    holds.append({
        "id": hold_id,
        "items": carrito,
        "total": str(totals["total"])
    })

    session["caja_holds"] = holds
    session["carrito"] = []
    session.modified = True

    flash(f"Venta en espera #{hold_id}", "info")
    return redirect(url_for("caja"))

@app.post("/caja/hold/resume/<int:hold_id>")
def caja_hold_resume(hold_id):
    holds = session.get("caja_holds", [])
    target = None
    for h in holds:
        if h["id"] == hold_id:
            target = h
            break

    if not target:
        flash("Venta en espera no encontrada.", "warning")
        return redirect(url_for("caja"))

    # cargar carrito desde hold
    session["carrito"] = target["items"]
    holds = [h for h in holds if h["id"] != hold_id]
    session["caja_holds"] = holds
    session.modified = True

    flash(f"Venta en espera #{hold_id} cargada.", "success")
    return redirect(url_for("caja"))

@app.post("/caja/pagar")
def caja_pagar():
    carrito = session.get("carrito", [])
    aplica_iva = session.get("caja_aplica_iva", True)
    totals = _totales(carrito, aplica_iva)

    if not carrito:
        return redirect(url_for("caja"))

    conn = conexion_db()
    cur = conn.cursor()

    # 1) Guardar encabezado de la venta
    usuario_id = session.get("usuario_id")  # si lo tienes, si no, pon NULL
    cur.execute(
        "INSERT INTO caja_ventas (fecha, usuario_id, total) VALUES (NOW(), %s, %s)",
        (usuario_id, totals["total"])
    )
    venta_id = cur.lastrowid   # este es tu folio consecutivo

    # 2) Guardar detalle
    for item in carrito:
        # Ajusta las claves según tu estructura real de carrito
        mercancia_id = item["id"]
        cantidad = item.get("cantidad", 1)
        precio = item["precio"]
        subtotal = cantidad * precio

        cur.execute(
            """
            INSERT INTO caja_ventas_detalle
            (venta_id, mercancia_id, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (venta_id, mercancia_id, cantidad, precio, subtotal)
        )

    conn.commit()
    cur.close()
    conn.close()

    # 3) Vaciar carrito para la siguiente venta
    session["carrito"] = []

    # 4) Mostrar ticket o regresar a caja mostrando el folio
    return redirect(url_for("caja_ticket", venta_id=venta_id))

@app.get("/caja/ticket/<int:venta_id>")
@require_login
def caja_ticket(venta_id):
    eid = g.empresa_id

    cobro = request.args.get("cobro")
    cambio = request.args.get("cambio")

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    # Encabezado: asegura pertenencia a la empresa
    cur.execute(
        """
        SELECT id, fecha, usuario_id, total
        FROM caja_ventas
        WHERE id = %s AND empresa_id = %s
        """,
        (venta_id, eid)
    )
    venta = cur.fetchone()
    if not venta:
        cur.close(); conn.close()
        return "Venta no encontrada", 404

    # Detalle: filtra por empresa para evitar cruces
    cur.execute(
        """
        SELECT d.cantidad,
               d.precio_unitario,
               d.subtotal,
               m.nombre AS producto
        FROM caja_ventas_detalle d
        JOIN mercancia m
          ON m.id = d.mercancia_id
         AND m.empresa_id = %s
        WHERE d.venta_id = %s
          AND d.empresa_id = %s
        """,
        (eid, venta_id, eid)
    )
    detalle = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "cobranza/caja_ticket.html",
        venta=venta,
        detalle=detalle,
        cobro=cobro,
        cambio=cambio
    )

@app.get("/caja/historial")
@require_login
def caja_historial():
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, fecha, total
        FROM caja_ventas
        WHERE empresa_id = %s
        ORDER BY id DESC
        LIMIT 100
    """, (eid,))
    ventas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("cobranza/caja_historial.html", ventas=ventas)

def precio_pt(mercancia_id: int, empresa_id: int = None) -> Decimal:
    """Calcula precio PT - FILTRADO POR EMPRESA"""
    eid = empresa_id or getattr(g, 'empresa_id', None) or session.get('empresa_id') or 1
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
          COALESCE(p.modo, 'auto') AS modo,
          COALESCE(p.markup_pct, 0.30) AS markup_pct,
          p.precio_manual
        FROM mercancia m
        LEFT JOIN pt_precios p ON p.mercancia_id = m.id AND p.empresa_id = %s
        WHERE m.id = %s AND m.empresa_id = %s
    """, (eid, mercancia_id, eid))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return Decimal("0.00")

    modo = row["modo"]
    markup_pct = Decimal(str(row["markup_pct"]))
    precio_manual = row["precio_manual"]
    costo = costo_pt(mercancia_id)

    if modo == "manual":
        if precio_manual is not None:
            return Decimal(str(precio_manual)).quantize(Decimal("0.01"))
        return (costo * (Decimal("1") + markup_pct)).quantize(Decimal("0.01"))

    pct_auto = markup_auto_para_costo(costo)
    return (costo * (Decimal("1") + pct_auto)).quantize(Decimal("0.01"))

@app.route('/test123')
def test123():
    return "<h1>FUNCIONA</h1><p>Session: " + str(session.get('username', 'No hay usuario')) + "</p>"





# -----   REGISTRO AL ERP  --------



@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registrar nuevo usuario con su propia empresa (modelo SaaS)"""
    
    if session.get('usuario_id'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nombre              = (request.form.get('nombre') or '').strip()
        nombre_empresa      = (request.form.get('nombre_empresa') or '').strip()
        correo              = (request.form.get('correo') or '').strip()
        confirmar_correo    = (request.form.get('confirmar_correo') or '').strip()
        contrasena          = (request.form.get('contrasena') or '').strip()
        confirmar_contrasena= (request.form.get('confirmar_contrasena') or '').strip()
        
        # Validaciones
        if not (nombre and nombre_empresa and correo and confirmar_correo and contrasena and confirmar_contrasena):
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('registro'))
        
        if correo != confirmar_correo:
            flash('Los correos electrónicos no coinciden.', 'danger')
            return redirect(url_for('registro'))
        
        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('registro'))
        
        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', correo):
            flash('El correo electrónico no es válido.', 'danger')
            return redirect(url_for('registro'))
        
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return redirect(url_for('registro'))
        
        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Verificar si el correo ya existe
            cursor.execute("SELECT id, email_confirmado FROM usuarios WHERE correo = %s", (correo,))
            usuario_existente = cursor.fetchone()
            
            if usuario_existente:
                if usuario_existente['email_confirmado']:
                    flash('Este correo ya está registrado. <a href="/login">Inicia sesión aquí</a>', 'warning')
                else:
                    flash('Este correo ya fue registrado pero no confirmado. Revisa tu bandeja de entrada.', 'warning')
                return redirect(url_for('login'))
            
            # Verificar si el nombre de empresa ya existe
            cursor.execute("SELECT id FROM empresas WHERE LOWER(nombre) = LOWER(%s)", (nombre_empresa,))
            empresa_existente = cursor.fetchone()
            
            if empresa_existente:
                flash('Ya existe una empresa con ese nombre. Por favor elige otro nombre.', 'warning')
                return redirect(url_for('registro'))
            
            # Crear empresa
            cursor.execute("""
                INSERT INTO empresas (nombre, activo, fecha_registro)
                VALUES (%s, 1, NOW())
            """, (nombre_empresa,))
            empresa_id = cursor.lastrowid
            
            print(f"✅ Empresa creada: {nombre_empresa} (ID: {empresa_id})")
            
            # Inicializar catálogos base de la empresa
            inicializar_empresa_nueva(cursor, empresa_id, nombre_empresa)
            
            # Código de 6 dígitos
            codigo = generar_codigo_confirmacion()
            
            # Hash de contraseña
            hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt())
            
            # Crear usuario
            cursor.execute("""
                INSERT INTO usuarios 
                (nombre, correo, contrasena, rol, tipo_usuario, empresa_id, 
                 email_confirmado, token_confirmacion, activo)
                VALUES (%s, %s, %s, 'admin', 'admin_empresa', %s, 0, %s, 1)
            """, (nombre, correo, hashed.decode('utf-8'), empresa_id, codigo))
            
            conn.commit()
            
            print(f"✅ Usuario creado: {nombre} ({correo}) - Código: {codigo}")
            
            # Enviar email con código
            try:
                msg = Message(
                    subject='Código de Confirmación - ERP Sistema',
                    recipients=[correo]
                )
                
                msg.body = f"""
    Hola {nombre},

    Tu código de confirmación es:

    {codigo}

    Este código es válido por 1 hora.

    Si no solicitaste esta cuenta, ignora este correo.

    Saludos,
    Equipo ERP
    """
                msg.html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; text-align: center; border-radius: 0 0 10px 10px; }}
            .codigo {{ font-size: 48px; font-weight: bold; color: #667eea; letter-spacing: 10px; margin: 30px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Confirma tu Cuenta</h1>
            </div>
            <div class="content">
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Tu empresa <strong>{nombre_empresa}</strong> ha sido creada exitosamente.</p>
                <p>Ingresa este código para confirmar tu cuenta:</p>
                <div class="codigo">{codigo}</div>
                <p style="color: #e74c3c; font-weight: bold;">⏰ Este código expirará en 1 hora</p>
            </div>
            <div class="footer">
                <p>© 2024 ERP Sistema. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
                print("📨 INTENTO ENVIO a:", correo)
                mail.send(msg)
                print("✅ ENVIO OK a:", correo)

                # Guardar correo en sesión temporal para la página de confirmación
                session['email_pendiente'] = correo
                session['nombre_temporal'] = nombre
                
                flash(f'Te hemos enviado un código de confirmación a {correo}', 'success')
                return redirect(url_for('confirmar_codigo'))
            
            except Exception as e:
                # OJO: aquí ya hiciste commit de empresa+usuario; 
                # no tiene sentido rollback, pero lo dejamos si quieres forzar consistencia.
                print(f"Error enviando email: {e}")
                import traceback
                traceback.print_exc()
                flash('Error al enviar el correo. Por favor intenta más tarde.', 'danger')
                return redirect(url_for('registro'))
        
        except Exception as e:
            conn.rollback()
            print(f"❌ Error en registro: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error al registrar: {e}', 'danger')
            return redirect(url_for('registro'))
        
        finally:
            cursor.close()
            conn.close()
    
    return render_template('registro/registro.html')

@app.route('/confirmar-email/<token>')
def confirmar_email(token):
    """Confirmar cuenta de usuario mediante token"""
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, nombre, correo, empresa_id, email_confirmado. rol
            FROM usuarios 
            WHERE token_confirmacion = %s
        """, (token,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash('❌ El enlace de confirmación no es válido o ya fue utilizado.', 'danger')
            return redirect(url_for('login'))
        
        if usuario['email_confirmado']:
            flash('✅ Tu cuenta ya está confirmada. Puedes iniciar sesión.', 'info')
            return redirect(url_for('login'))
        
        # Confirmar cuenta
        cursor.execute("""
            UPDATE usuarios 
            SET email_confirmado = 1, token_confirmacion = NULL 
            WHERE id = %s
        """, (usuario['id'],))
        conn.commit()
        
        print(f"✅ Email confirmado: {usuario['correo']}")
               
        # Guardar en sesión para auto-login
        session['usuario_id'] = usuario['id']
        session['empresa_id'] = usuario.get('empresa_id')
        session['username'] = usuario['nombre']
        session['rol'] = usuario.get('rol', 'admin')
        
        print(f"✅ Sesión creada: usuario_id={usuario['id']}, empresa_id={usuario['empresa_id']}")

        flash(f"🎉 ¡Cuenta confirmada exitosamente! Bienvenido {usuario['nombre']}. Ya puedes iniciar sesión.", 'success')
        
        
        return redirect(url_for('onboarding'))  # ← Redirigir a onboarding

    except Exception as e:
        conn.rollback()
        print(f"Error confirmando email: {e}")
        flash('Error al confirmar cuenta. Intenta nuevamente.', 'danger')
        import traceback
        traceback.print_exc()
        flash('Error al confirmar el correo.', 'danger')
        return redirect(url_for('login'))
        
    finally:
        cursor.close()
        conn.close()

def enviar_email_activacion(nombre, correo_destino, token):
    """Envía email de activación de cuenta"""
    link_activacion = f"http://127.0.0.1:5000/activar-cuenta/{token}"
    
    try:
        msg = Message(
            subject='Bienvenido al Sistema ERP',
            recipients=[correo_destino]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                .header {{ text-align: center; padding: 20px; background: #007bff; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Bienvenido al Sistema ERP</h1>
                </div>
                <div class="content">
                    <h2>Hola, {nombre}!</h2>
                    <p>Se ha creado una cuenta para ti en nuestro sistema ERP.</p>
                    <p>Para activar tu cuenta y crear tu contraseña, haz clic en el siguiente boton:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{link_activacion}" class="button">Activar mi Cuenta</a>
                    </p>
                    <p><small>O copia y pega este enlace en tu navegador:</small></p>
                    <p><small style="color: #666;">{link_activacion}</small></p>
                    <hr>
                    <p><strong>Tus datos de acceso:</strong></p>
                    <ul>
                        <li><strong>Usuario:</strong> {correo_destino}</li>
                        <li><strong>Contrasena:</strong> La crearas al activar tu cuenta</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        return True
    
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('usuario_id'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '').strip()
        
        if not correo or not contrasena:
            flash('Por favor completa todos los campos.', 'danger')
            return redirect(url_for('login'))
        
        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT id, nombre, correo, contrasena, rol, empresa_id, email_confirmado
                FROM usuarios 
                WHERE correo = %s AND activo = 1
            """, (correo,))
            usuario = cursor.fetchone()
            
            if not usuario:
                flash('Correo o contraseña incorrectos.', 'danger')
                return redirect(url_for('login'))
            
            # Verificar contraseña (soporta scrypt y bcrypt)
            password_valida = False
            hash_guardado = usuario['contrasena']
            
            if hash_guardado.startswith('scrypt:') or hash_guardado.startswith('pbkdf2:'):
                # Hash de werkzeug (usuarios nuevos)
                from werkzeug.security import check_password_hash
                password_valida = check_password_hash(hash_guardado, contrasena)
            elif hash_guardado.startswith('$2b$') or hash_guardado.startswith('$2a$'):
                # Hash de bcrypt (usuarios viejos)
                password_valida = bcrypt.checkpw(contrasena.encode('utf-8'), hash_guardado.encode('utf-8'))
            
            if not password_valida:
                flash('Correo o contraseña incorrectos.', 'danger')
                return redirect(url_for('login'))
            
            # ===== VERIFICAR EMAIL CONFIRMADO =====
            if not usuario['email_confirmado']:
                flash('⚠️ Debes confirmar tu correo antes de ingresar. Revisa tu bandeja de entrada.', 'warning')
                return redirect(url_for('login'))
            
            # Crear sesión
            session['usuario_id'] = usuario['id']
            session['empresa_id'] = usuario['empresa_id']
            session['username'] = usuario['nombre']
            session['rol'] = usuario.get('rol', 'admin')
            
            # Verificar si completó onboarding
            cursor.execute("""
                SELECT configuracion_completada 
                FROM empresa_configuracion 
                WHERE empresa_id = %s
            """, (usuario['empresa_id'],))
            config = cursor.fetchone()
            
            if not config or not config['configuracion_completada']:
                return redirect(url_for('onboarding'))
            
            flash(f'¡Bienvenido {usuario["nombre"]}!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error en login: {e}")
            flash('Error al iniciar sesión.', 'danger')
            return redirect(url_for('login'))
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/login.html')

@app.route('/onboarding', methods=['GET', 'POST'])
@require_login
def onboarding():
    """Configuración inicial de la empresa"""
    
    eid = g.empresa_id
    uid = g.usuario_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Verificar si ya completó el onboarding
        cur.execute("""
            SELECT configuracion_completada 
            FROM empresa_configuracion 
            WHERE empresa_id = %s
        """, (eid,))
        config_existente = cur.fetchone()
        
        if config_existente and config_existente['configuracion_completada']:
            flash('La configuración inicial ya fue completada.', 'info')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            empleados_rango = request.form.get('empleados_rango')
            tipo_comprobantes = request.form.get('tipo_comprobantes')
            tipo_mercancia = request.form.get('tipo_mercancia')
            frecuencia_inventario = request.form.get('frecuencia_inventario')
            frecuencia_inventario_desc = request.form.get('frecuencia_inventario_desc', '').strip()
            
            if not all([empleados_rango, tipo_comprobantes, tipo_mercancia, frecuencia_inventario]):
                flash('Por favor completa todas las preguntas.', 'danger')
                return redirect(url_for('onboarding'))
            
            # Validar descripción si eligió "otro"
            if frecuencia_inventario == 'otro' and not frecuencia_inventario_desc:
                flash('Por favor describe la frecuencia de inventario deseada.', 'danger')
                return redirect(url_for('onboarding'))
            
            # ===== LÓGICA DE CONFIGURACIÓN AUTOMÁTICA =====
            requiere_manufactura = (tipo_mercancia == 'materia_prima')
            requiere_wip = requiere_manufactura
            requiere_recetas = requiere_manufactura
            
            # Determinar nivel de complejidad
            if empleados_rango in ['1-5', '6-10']:
                nivel_complejidad = 'basico'
            elif empleados_rango in ['11-25', '26-99']:
                nivel_complejidad = 'intermedio'
            else:
                nivel_complejidad = 'avanzado'
            
            # Módulos habilitados
            modulo_wip = requiere_manufactura
            modulo_produccion = requiere_manufactura
            modulo_contabilidad = (tipo_comprobantes in ['solo_facturas', 'mixto'])
            
            # ===== GUARDAR CONFIGURACIÓN =====
            cur.execute("""
                INSERT INTO empresa_configuracion (
                    empresa_id, empleados_rango, tipo_comprobantes, tipo_mercancia,
                    requiere_manufactura, requiere_wip, requiere_recetas, nivel_complejidad,
                    modulo_compras, modulo_ventas, modulo_inventario_mp, modulo_inventario_wip,
                    modulo_inventario_pt, modulo_produccion, modulo_contabilidad,
                    frecuencia_inventario, frecuencia_inventario_desc,
                    configuracion_completada
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    empleados_rango = VALUES(empleados_rango),
                    tipo_comprobantes = VALUES(tipo_comprobantes),
                    tipo_mercancia = VALUES(tipo_mercancia),
                    requiere_manufactura = VALUES(requiere_manufactura),
                    requiere_wip = VALUES(requiere_wip),
                    requiere_recetas = VALUES(requiere_recetas),
                    nivel_complejidad = VALUES(nivel_complejidad),
                    modulo_inventario_wip = VALUES(modulo_inventario_wip),
                    modulo_produccion = VALUES(modulo_produccion),
                    modulo_contabilidad = VALUES(modulo_contabilidad),
                    frecuencia_inventario = VALUES(frecuencia_inventario),
                    frecuencia_inventario_desc = VALUES(frecuencia_inventario_desc),
                    configuracion_completada = VALUES(configuracion_completada)
            """, (
                eid, empleados_rango, tipo_comprobantes, tipo_mercancia,
                requiere_manufactura, requiere_wip, requiere_recetas, nivel_complejidad,
                True, True, True, modulo_wip, True, modulo_produccion, modulo_contabilidad,
                frecuencia_inventario, frecuencia_inventario_desc if frecuencia_inventario == 'otro' else None,
                True
            ))
            
            conn.commit()
            
            # Mensaje personalizado
            mensaje_config = f"✅ Configuración completada. "
            if requiere_manufactura:
                mensaje_config += "Tu ERP incluirá módulos de Producción y WIP. "
            else:
                mensaje_config += "Tu ERP se configuró para compra-venta directa. "
            
            # Agregar info de frecuencia de inventario
            frecuencias = {
                'turno': 'por turno',
                'diario': 'diaria',
                'semanal': 'semanal',
                'mensual': 'mensual',
                'anual': 'anual',
                'otro': frecuencia_inventario_desc
            }
            mensaje_config += f"Toma física de inventario: {frecuencias.get(frecuencia_inventario, frecuencia_inventario)}."
            
            flash(mensaje_config, 'success')
            return redirect(url_for('dashboard'))
        
    except Exception as e:
        conn.rollback()
        print(f"Error en onboarding: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error al guardar configuración: {e}', 'danger')
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('registro/onboarding.html')

def generar_codigo_confirmacion():
    """Genera un código de 6 dígitos para confirmación de email"""
    import random
    return str(random.randint(100000, 999999))

@app.route('/confirmar-codigo', methods=['GET', 'POST'])
def confirmar_codigo():
    """Página para ingresar código de confirmación"""
    
    email = session.get('email_pendiente')
    nombre = session.get('nombre_temporal')
    
    if not email:
        flash('Sesión expirada. Por favor regístrate de nuevo.', 'warning')
        return redirect(url_for('registro'))
    
    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo', '').strip()
        
        if not codigo_ingresado:
            flash('Por favor ingresa el código.', 'danger')
            return redirect(url_for('confirmar_codigo'))
        
        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Buscar usuario con este código
            cursor.execute("""
                SELECT id, nombre, empresa_id, token_confirmacion, email_confirmado, rol
                FROM usuarios 
                WHERE correo = %s AND token_confirmacion = %s
            """, (email, codigo_ingresado))
            usuario = cursor.fetchone()
            
            if not usuario:
                flash('❌ Código incorrecto. Por favor intenta de nuevo.', 'danger')
                return redirect(url_for('confirmar_codigo'))
            
            if usuario['email_confirmado']:
                flash('Tu correo ya está confirmado.', 'info')
                return redirect(url_for('login'))
            
            # Confirmar email
            cursor.execute("""
                UPDATE usuarios 
                SET email_confirmado = 1, token_confirmacion = NULL 
                WHERE id = %s
            """, (usuario['id'],))
            conn.commit()
            
            print(f"✅ Email confirmado con código: {email}")
            
            # Auto-login
            session.pop('email_pendiente', None)
            session.pop('nombre_temporal', None)
            session['usuario_id'] = usuario['id']
            session['empresa_id'] = usuario['empresa_id']
            session['username'] = usuario['nombre']
            session['rol'] = usuario.get('rol', 'admin')
            
            flash(f'🎉 ¡Cuenta confirmada! Bienvenido {usuario["nombre"]}', 'success')
            return redirect(url_for('onboarding'))
            
        except Exception as e:
            conn.rollback()
            print(f"Error confirmando código: {e}")
            flash('Error al confirmar el código.', 'danger')
            return redirect(url_for('confirmar_codigo'))
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('registro/confirmar_codigo.html', email=email, nombre=nombre)

def obtener_configuracion_empresa(empresa_id):
    """Obtiene la configuración de la empresa"""
    try:
        conn = conexion_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM empresa_configuracion WHERE empresa_id = %s
        """, (empresa_id,))
        config = cur.fetchone()
        cur.close()
        conn.close()
        return config
    except:
        return None

@app.route('/olvide-password', methods=['GET', 'POST'])
def olvide_password():
    """Solicitar restablecimiento de contraseña"""
    
    if session.get('usuario_id'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        
        if not correo:
            flash('Por favor ingresa tu correo electrónico.', 'danger')
            return redirect(url_for('olvide_password'))
        
        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Buscar usuario por correo
            cursor.execute("""
                SELECT id, nombre, correo, email_confirmado 
                FROM usuarios 
                WHERE correo = %s AND activo = 1
            """, (correo,))
            usuario = cursor.fetchone()
            
            if not usuario:
                flash('Si el correo existe, recibirás instrucciones para restablecer tu contraseña.', 'info')
                return redirect(url_for('login'))
            
            if not usuario['email_confirmado']:
                flash('Debes confirmar tu correo antes de restablecer la contraseña.', 'warning')
                return redirect(url_for('login'))
            
            # Generar token de reseteo
            token = generar_token()
            
            # Guardar token (usar nombres correctos)
            cursor.execute("""
                UPDATE usuarios 
                SET token_reset = %s, 
                    token_reset_expira = DATE_ADD(NOW(), INTERVAL 1 HOUR)
                WHERE id = %s
            """, (token, usuario['id']))
            conn.commit()
            
            # Enviar email
            try:
                msg = Message(
                    subject='Restablecer Contraseña - ERP Sistema',
                    recipients=[correo]
                )
                
                reset_url = url_for('reset_password', token=token, _external=True)
                
                msg.body = f"""
 Hola {usuario['nombre']},

 Recibimos una solicitud para restablecer tu contraseña.

 Haz clic en el siguiente enlace para crear una nueva contraseña:
 {reset_url}

 Este enlace expirará en 1 hora.

 Si no solicitaste este cambio, ignora este correo.

 Saludos,
 Equipo ERP
 """
                
                msg.html = f"""
 <!DOCTYPE html>
 <html>
 <head>
     <style>
         body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
         .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
         .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
         .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
         .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
         .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
     </style>
 </head>
 <body>
     <div class="container">
         <div class="header">
             <h1>🔐 Restablecer Contraseña</h1>
         </div>
         <div class="content">
             <p>Hola <strong>{usuario['nombre']}</strong>,</p>
             <p>Recibimos una solicitud para restablecer tu contraseña.</p>
             <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
             <p style="text-align: center;">
                 <a href="{reset_url}" class="button">Restablecer Contraseña</a>
             </p>
             <p style="color: #666; font-size: 14px;">
                 O copia y pega este enlace en tu navegador:<br>
                 <a href="{reset_url}">{reset_url}</a>
             </p>
             <p style="color: #e74c3c; font-weight: bold;">⏰ Este enlace expirará en 1 hora.</p>
             <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>
         </div>
         <div class="footer">
             <p>© 2024 ERP Sistema. Todos los derechos reservados.</p>
         </div>
     </div>
 </body>
 </html>
 """
                
                mail.send(msg)
                
                flash('Te hemos enviado un correo con instrucciones para restablecer tu contraseña.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                conn.rollback()
                print(f"Error enviando email de reseteo: {e}")
                import traceback
                traceback.print_exc()
                flash('Error al enviar el correo. Por favor intenta más tarde.', 'danger')
                return redirect(url_for('olvide_password'))
                
        except Exception as e:
            conn.rollback()
            print(f"Error en olvide_password: {e}")
            import traceback
            traceback.print_exc()
            flash('Error al procesar la solicitud.', 'danger')
            return redirect(url_for('olvide_password'))
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/olvide_password.html')
   
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña con token"""
    
    if session.get('usuario_id'):
        return redirect(url_for('dashboard'))
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verificar token (usar nombres correctos)
        cursor.execute("""
            SELECT id, nombre, correo, token_reset, token_reset_expira
            FROM usuarios 
            WHERE token_reset = %s 
            AND activo = 1
            AND token_reset_expira > NOW()
        """, (token,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash('El enlace es inválido o ha expirado. Solicita uno nuevo.', 'danger')
            return redirect(url_for('olvide_password'))
        
        if request.method == 'POST':
            nueva_contrasena = request.form.get('contrasena', '').strip()
            confirmar_contrasena = request.form.get('confirmar_contrasena', '').strip()
            
            # Validaciones
            if not nueva_contrasena or not confirmar_contrasena:
                flash('Todos los campos son obligatorios.', 'danger')
                return redirect(url_for('reset_password', token=token))
            
            if nueva_contrasena != confirmar_contrasena:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('reset_password', token=token))
            
            if len(nueva_contrasena) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
                return redirect(url_for('reset_password', token=token))
            
            # Hash de la nueva contraseña
            hashed = bcrypt.hashpw(nueva_contrasena.encode('utf-8'), bcrypt.gensalt())
            
            # Actualizar contraseña (usar nombres correctos)
            cursor.execute("""
                UPDATE usuarios 
                SET contrasena = %s, 
                    token_reset = NULL, 
                    token_reset_expira = NULL 
                WHERE id = %s
            """, (hashed.decode('utf-8'), usuario['id']))
            conn.commit()
            
            flash('✅ Contraseña restablecida correctamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
            
    except Exception as e:
        conn.rollback()
        print(f"Error en reset_password: {e}")
        import traceback
        traceback.print_exc()
        flash('Error al restablecer la contraseña.', 'danger')
        return redirect(url_for('olvide_password'))
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template('auth/reset_password.html', token=token)

# =============================================
# 1. REGISTRO DE USUARIOS (Admin agrega correos/nombres)
# =============================================

@app.route('/admin/usuarios/agregar', methods=['POST'])
@require_login
def admin_agregar_usuario():
    """Admin agrega un nuevo usuario con áreas asignadas y envía invitación."""
    eid = g.empresa_id
    uid = g.usuario_id
    
    correo = (request.form.get('correo') or '').strip().lower()
    nombre = (request.form.get('nombre') or '').strip()
    puesto = (request.form.get('puesto') or '').strip()
    areas_seleccionadas = request.form.getlist('areas')  # Lista de IDs de áreas
    
    if not correo or not nombre:
        flash('Correo y nombre son requeridos', 'warning')
        return redirect(url_for('admin_gestion_usuarios'))  # ✅ CAMBIO 1
    
    if not areas_seleccionadas:
        flash('Debes asignar al menos un área al usuario', 'warning')
        return redirect(url_for('admin_gestion_usuarios'))  # ✅ CAMBIO 2
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar correo no exista
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            flash('Este correo ya está registrado', 'danger')
            return redirect(url_for('admin_gestion_usuarios'))  # ✅ CAMBIO 3
        
        # Token invitación + expiración
        token = secrets.token_urlsafe(32)
        expira = datetime.now() + timedelta(hours=24)
        
        # Crear usuario invitado (sin contraseña aún)
        cursor.execute("""
            INSERT INTO usuarios
            (nombre, correo, puesto, empresa_id,
             estado_registro, rol,
             contrasena, activo,
             email_confirmado,
             token_invitacion, fecha_invitacion, fecha_token_expira,
             invitado_por)
            VALUES
            (%s, %s, %s, %s,
             'invitado', 'editor',
             '', 1,
             0,
             %s, NOW(), %s,
             %s)
        """, (nombre, correo, puesto, eid, token, expira, uid))
        
        usuario_id = cursor.lastrowid
        
        # Asignar áreas seleccionadas
        for area_id in areas_seleccionadas:
            cursor.execute("""
                INSERT INTO usuario_areas (usuario_id, area_id, empresa_id, rol_area, activo)
                VALUES (%s, %s, %s, 'operador', 1)
            """, (usuario_id, int(area_id), eid))
        
        db.commit()
        
        # Link para crear contraseña
        link = url_for('completar_registro', token=token, _external=True)
        
        # Obtener nombres de áreas asignadas para el correo
        cursor.execute("""
            SELECT GROUP_CONCAT(a.nombre SEPARATOR ', ') as areas
            FROM usuario_areas ua
            JOIN areas_produccion a ON a.id = ua.area_id  # ✅ CAMBIO 4: areas_sistema → areas_produccion
            WHERE ua.usuario_id = %s
        """, (usuario_id,))
        areas_nombres = cursor.fetchone()['areas'] or 'Sin áreas'
        
        msg = Message(
            subject='Invitación a ERP - Crea tu contraseña',
            recipients=[correo]
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .btn {{ display: inline-block; background: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .areas {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>¡Bienvenido al ERP!</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre}</strong>,</p>
                    <p>Has sido invitado a formar parte del equipo. Para comenzar, crea tu contraseña haciendo clic en el siguiente botón:</p>
                    
                    <div class="areas">
                        <strong>📋 Áreas asignadas:</strong><br>
                        {areas_nombres}
                    </div>
                    
                    <center>
                        <a href="{link}" class="btn">Crear mi Contraseña</a>
                    </center>
                    
                    <p><small>Este enlace expira en 24 horas.</small></p>
                    <p>Si no puedes hacer clic en el botón, copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; font-size: 12px; color: #666;">{link}</p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no respondas.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        flash(f'✅ Usuario {nombre} agregado. Invitación enviada a {correo}', 'success')
        
    except Exception as e:
        db.rollback()
        print(f"Error agregando usuario: {e}")
        flash(f'Error al agregar usuario: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('admin_gestion_usuarios'))  # ✅ CAMBIO 5

@app.route('/admin/usuarios/<int:usuario_id>/editar', methods=['POST'])
@require_login
def admin_editar_usuario(usuario_id):
    """Editar datos básicos de usuario"""
    eid = g.empresa_id
    
    nombre = request.form.get('nombre', '').strip()
    puesto = request.form.get('puesto', '').strip()
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE usuarios SET nombre = %s, puesto = %s
        WHERE id = %s AND empresa_id = %s
    """, (nombre, puesto, usuario_id, eid))
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('Usuario actualizado', 'success')
    return redirect(url_for('admin_registro_usuarios'))

@app.route('/admin/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
@require_login
def admin_eliminar_usuario(usuario_id):
    """Eliminar o desactivar usuario según su estado"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    # No permitir eliminarse a sí mismo
    if usuario_id == uid:
        flash('No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for('admin_registro_usuarios'))
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, nombre, estado_registro FROM usuarios 
        WHERE id = %s AND empresa_id = %s
    """, (usuario_id, eid))
    usuario = cursor.fetchone()
    
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        cursor.close()
        db.close()
        return redirect(url_for('admin_registro_usuarios'))
    
    if usuario['estado_registro'] in ('pendiente', 'invitado'):
        # Eliminar completamente (nunca usó el sistema)
        cursor.execute("DELETE FROM usuario_areas WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM notificaciones_usuario WHERE usuario_destino_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        db.commit()
        flash(f'Usuario "{usuario["nombre"]}" eliminado', 'success')
    else:
        # Desactivar (tiene historial en el sistema)
        cursor.execute("""
            UPDATE usuarios SET activo = 0 WHERE id = %s
        """, (usuario_id,))
        cursor.execute("""
            UPDATE usuario_areas SET activo = 0 WHERE usuario_id = %s
        """, (usuario_id,))
        db.commit()
        flash(f'Usuario "{usuario["nombre"]}" desactivado', 'info')
    
    cursor.close()
    db.close()
    
    return redirect(url_for('admin_registro_usuarios'))

@app.route('/aceptar-invitacion/<token>', methods=['GET', 'POST'])
def aceptar_invitacion(token):
    db = conexion_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, nombre, correo, estado_registro, fecha_token_expira
        FROM usuarios
        WHERE token_invitacion = %s
    """, (token,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        db.close()
        abort(404)

    if usuario['fecha_token_expira'] and usuario['fecha_token_expira'] < datetime.now():
        cursor.close()
        db.close()
        flash('El enlace ha expirado.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        contrasena = request.form.get('contrasena')
        confirmar  = request.form.get('confirmar')

        if not contrasena or contrasena != confirmar:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('registro/crear_contrasena.html', usuario=usuario)

        hashed = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt())

        cursor.execute("""
            UPDATE usuarios
            SET contrasena = %s,
                estado_registro = 'activo',
                email_confirmado = 1,
                token_invitacion = NULL,
                fecha_token_expira = NULL
            WHERE id = %s
        """, (hashed.decode(), usuario['id']))

        db.commit()
        cursor.close()
        db.close()

        flash('Cuenta activada correctamente. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    cursor.close()
    db.close()
    return render_template('registro/crear_contrasena.html', usuario=usuario)

# =============================================
# GESTIÓN DE USUARIOS (UNIFICADA)
# Reemplaza: admin_registro_usuarios y admin_usuario_areas
# =============================================

@app.route('/admin/usuarios')
@require_login
def admin_gestion_usuarios():
    """Gestión unificada de usuarios y áreas"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener usuarios con sus áreas
    cursor.execute("""
        SELECT 
            u.id,
            u.nombre,
            u.correo,
            u.puesto,
            u.estado_registro,
            u.fecha_registro,
            GROUP_CONCAT(DISTINCT a.nombre ORDER BY a.nombre SEPARATOR ', ') as areas_nombres,
            COUNT(DISTINCT ua.area_id) as num_areas
        FROM usuarios u
        LEFT JOIN usuario_areas ua ON ua.usuario_id = u.id AND ua.activo = 1
        LEFT JOIN areas_sistema a ON a.id = ua.area_id AND a.activo = 1
        WHERE u.empresa_id = %s
        GROUP BY u.id
        ORDER BY 
            CASE u.estado_registro 
                WHEN 'pendiente' THEN 1 
                WHEN 'invitado' THEN 2 
                WHEN 'activo' THEN 3 
                ELSE 4 
            END,
            u.nombre
    """, (eid,))
    usuarios = cursor.fetchall()
    
    # Conteos por estado
    cursor.execute("""
        SELECT 
            COALESCE(estado_registro, 'activo') as estado,
            COUNT(*) as total
        FROM usuarios 
        WHERE empresa_id = %s
        GROUP BY estado_registro
    """, (eid,))
    conteos_raw = cursor.fetchall()
    conteo = {
        'pendientes': 0,
        'invitados': 0,
        'activos': 0
    }
    for c in conteos_raw:
        if c['estado'] == 'pendiente':
            conteo['pendientes'] = c['total']
        elif c['estado'] == 'invitado':
            conteo['invitados'] = c['total']
        elif c['estado'] in ['activo', None]:
            conteo['activos'] += c['total']
    
    # Total de áreas
    cursor.execute("""
        SELECT COUNT(*) as total FROM areas_sistema 
        WHERE empresa_id = %s AND activo = 1
    """, (eid,))
    total_areas = cursor.fetchone()['total']
    
    cursor.close()
    db.close()
    
    return render_template('admin/gestion_usuarios.html', 
                          usuarios=usuarios, 
                          conteo=conteo,
                          total_areas=total_areas)


# =============================================
# RUTAS AUXILIARES (mantener las existentes)
# =============================================

# POST /admin/usuarios/agregar - Agregar usuario
# POST /admin/usuarios/<id>/editar - Editar usuario
# POST /admin/usuarios/<id>/eliminar - Eliminar usuario
# POST /admin/usuarios/<id>/reenviar_invitacion - Reenviar
# GET /admin/usuario/<id>/areas - Asignar áreas a usuario


# =============================================
# ACTUALIZAR SIDEBAR
# =============================================
# Cambiar el link de:
#   - "Registro de Usuarios" → /admin/usuarios
#   - "Usuarios y Áreas" → ELIMINAR (ya no es necesario)
#
# El menú Administración queda:
#   - Gestión de Usuarios (/admin/usuarios)
#   - Áreas del Sistema (/admin/areas)

# =============================================
# 2. ASIGNACIÓN DE ÁREAS CON BUSCADOR
# =============================================

@app.route('/admin/areas/<int:area_id>/asignar', methods=['GET', 'POST'])
@require_login
def admin_area_asignar(area_id):
    """Asignar responsable y supervisor a un área"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener área
    cursor.execute("""
        SELECT * FROM areas_sistema WHERE id = %s AND empresa_id = %s
    """, (area_id, eid))
    area = cursor.fetchone()
    
    if not area:
        flash('Área no encontrada', 'danger')
        return redirect(url_for('admin_areas'))
    
    if request.method == 'POST':
        responsable_id = request.form.get('responsable_id')
        supervisor_id = request.form.get('supervisor_id')
        operadores_ids = request.form.getlist('operadores[]')
        
        # Desactivar asignaciones anteriores
        cursor.execute("""
            UPDATE usuario_areas SET activo = 0 
            WHERE area_id = %s AND empresa_id = %s
        """, (area_id, eid))
        
        usuarios_a_invitar = []
        
        # Asignar responsable
        if responsable_id:
            asignar_usuario_area(cursor, eid, responsable_id, area_id, 'responsable', uid)
            usuarios_a_invitar.append((responsable_id, 'responsable'))
        
        # Asignar supervisor
        if supervisor_id and supervisor_id != responsable_id:
            asignar_usuario_area(cursor, eid, supervisor_id, area_id, 'supervisor', uid)
            usuarios_a_invitar.append((supervisor_id, 'supervisor'))
        
        # Asignar operadores
        for op_id in operadores_ids:
            if op_id and op_id not in [responsable_id, supervisor_id]:
                asignar_usuario_area(cursor, eid, op_id, area_id, 'operador', uid)
                usuarios_a_invitar.append((op_id, 'operador'))
        
        db.commit()
        
        # Enviar invitaciones a usuarios pendientes
        for user_id, rol in usuarios_a_invitar:
            enviar_invitacion_si_pendiente(cursor, db, user_id, area, rol, uid, eid)
        
        db.commit()
        
        flash(f'✅ Equipo asignado a {area["nombre"]}', 'success')
        
        cursor.close()
        db.close()
        return redirect(url_for('admin_areas'))
    
    # GET: Obtener datos
    # Usuarios disponibles para asignar
    cursor.execute("""
        SELECT id, nombre, correo, puesto, estado_registro
        FROM usuarios 
        WHERE empresa_id = %s AND activo = 1
        ORDER BY nombre
    """, (eid,))
    usuarios = cursor.fetchall()
    
    # Asignaciones actuales
    cursor.execute("""
        SELECT ua.usuario_id, ua.rol_area, u.nombre
        FROM usuario_areas ua
        JOIN usuarios u ON u.id = ua.usuario_id
        WHERE ua.area_id = %s AND ua.activo = 1
    """, (area_id,))
    asignaciones = cursor.fetchall()
    
    asignados = {a['rol_area']: a for a in asignaciones}
    operadores_actuales = [a['usuario_id'] for a in asignaciones if a['rol_area'] == 'operador']
    
    cursor.close()
    db.close()
    
    return render_template('admin/area_asignar_v2.html', 
                          area=area, 
                          usuarios=usuarios,
                          asignados=asignados,
                          operadores_actuales=operadores_actuales)


def asignar_usuario_area(cursor, empresa_id, usuario_id, area_id, rol, asignado_por):
    """Helper para asignar usuario a área"""
    # Verificar si ya existe
    cursor.execute("""
        SELECT id FROM usuario_areas WHERE usuario_id = %s AND area_id = %s
    """, (usuario_id, area_id))
    existente = cursor.fetchone()
    
    puede_autorizar = 1 if rol in ('responsable', 'supervisor') else 0
    puede_editar = 1 if rol != 'consulta' else 0
    puede_eliminar = 1 if rol == 'responsable' else 0
    
    if existente:
        cursor.execute("""
            UPDATE usuario_areas SET 
                rol_area = %s, puede_autorizar = %s, puede_editar = %s, 
                puede_eliminar = %s, activo = 1
            WHERE id = %s
        """, (rol, puede_autorizar, puede_editar, puede_eliminar, existente['id']))
    else:
        cursor.execute("""
            INSERT INTO usuario_areas 
            (empresa_id, usuario_id, area_id, rol_area, puede_autorizar, 
             puede_editar, puede_eliminar, asignado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (empresa_id, usuario_id, area_id, rol, puede_autorizar, 
              puede_editar, puede_eliminar, asignado_por))
    
    # Registrar en historial
    cursor.execute("""
        INSERT INTO historial_asignaciones_area 
        (empresa_id, usuario_id, area_id, rol_nuevo, accion, realizado_por)
        VALUES (%s, %s, %s, %s, 'asignado', %s)
    """, (empresa_id, usuario_id, area_id, rol, asignado_por))


def enviar_invitacion_si_pendiente(cursor, db, usuario_id, area, rol, invitado_por, empresa_id):
    """
    Envía invitación SOLO si el usuario está en estado 'pendiente'
    """

    cursor.execute("""
        SELECT id, nombre, correo, estado_registro
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))
    usuario = cursor.fetchone()

    if not usuario:
        return

    # ─────────────────────────────────────────────
    # CASO 1: usuario pendiente → enviar invitación
    # ─────────────────────────────────────────────
    if usuario['estado_registro'] == 'pendiente':

        token = generar_token_invitacion()
        fecha_expira = datetime.now() + timedelta(days=1)  # 24 horas reales

        cursor.execute("""
            UPDATE usuarios
            SET estado_registro    = 'invitado',
                token_invitacion   = %s,
                fecha_invitacion   = NOW(),
                fecha_token_expira = %s,
                invitado_por       = %s
            WHERE id = %s
        """, (token, fecha_expira, invitado_por, usuario_id))

        db.commit()

        # 🔗 Link CORRECTO (público, GET)
        link = url_for(
            'completar_registro',
            token=token,
            _external=True
        )

        try:
            enviar_correo_invitacion_v2(
                usuario=usuario,
                area=area,
                rol=rol,
                link=link
            )
        except Exception as e:
            print("❌ Error enviando invitación:", e)
            print(f"🔗 Link manual para {usuario['correo']}: {link}")

    # ─────────────────────────────────────────────
    # CASO 2: usuario ya activo → mensaje interno
    # ─────────────────────────────────────────────
    elif usuario['estado_registro'] == 'activo':
        crear_mensaje_bienvenida(
            cursor=cursor,
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            area=area,
            rol=rol,
            invitado_por=invitado_por
        )


def enviar_correo_invitacion_v2(usuario, area, rol, link):
    """Envía correo de invitación con detalles del área"""
    try:
        msg = Message(
            subject=f'Invitación al Sistema ERP - {area["nombre"]}',
            sender=app.config.get('MAIL_USERNAME'),
            recipients=[usuario['correo']]
        )
        
        rol_descripcion = {
            'responsable': 'Serás el responsable principal de esta área, con autoridad para tomar decisiones y aprobar operaciones.',
            'supervisor': 'Supervisarás las operaciones del área, podrás aprobar y revisar el trabajo del equipo.',
            'operador': 'Ejecutarás las tareas diarias del área según los procedimientos establecidos.'
        }
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">¡Hola {usuario['nombre']}!</h2>
            
            <p>Has sido invitado a formar parte del equipo en el sistema ERP.</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: {area['color']};">
                    <i class="{area['icono']}"></i> {area['nombre']}
                </h3>
                <p><strong>Tu rol:</strong> {rol.upper()}</p>
                <p style="color: #666;">{rol_descripcion.get(rol, '')}</p>
            </div>
            
            <p>Haz clic en el siguiente botón para completar tu registro:</p>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{link}" 
                   style="background-color: #007bff; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Aceptar y Completar Registro
                </a>
            </p>
            
            <p style="color: #666; font-size: 14px;">
                Este link expira en 7 días.<br>
                Si no esperabas esta invitación, ignora este correo.
            </p>
        </div>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        raise e


# =============================================
# 3. COMPLETAR REGISTRO (Usuario acepta invitación)
# =============================================

@app.route('/registro/completar/<token>', methods=['GET', 'POST'])
def completar_registro(token):
    """Usuario completa su registro después de aceptar invitación"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Buscar usuario por token
    cursor.execute("""
        SELECT u.*, e.nombre as empresa_nombre
        FROM usuarios u
        JOIN empresas e ON e.id = u.empresa_id
        WHERE u.token_invitacion = %s
    """, (token,))
    usuario = cursor.fetchone()
    
    if not usuario:
        flash('Link de invitación inválido', 'danger')
        return redirect(url_for('login'))
    
    if usuario['estado_registro'] == 'activo':
        flash('Ya completaste tu registro. Inicia sesión.', 'info')
        return redirect(url_for('login'))
    
    if usuario['fecha_token_expira'] and usuario['fecha_token_expira'] < datetime.now():
        flash('Este link ha expirado. Contacta al administrador.', 'danger')
        return redirect(url_for('login'))
    
    # Obtener áreas asignadas
    cursor.execute("""
        SELECT a.nombre, a.descripcion, a.icono, a.color, ua.rol_area
        FROM usuario_areas ua
        JOIN areas_sistema a ON a.id = ua.area_id
        WHERE ua.usuario_id = %s AND ua.activo = 1
    """, (usuario['id'],))
    areas = cursor.fetchall()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        contrasena = request.form.get('contrasena', '')
        confirmar = request.form.get('confirmar_contrasena', '')
        
        if not nombre:
            flash('El nombre es requerido', 'warning')
            return render_template('completar_registro.html', usuario=usuario, areas=areas)
        
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'warning')
            return render_template('completar_registro.html', usuario=usuario, areas=areas)
        
        if contrasena != confirmar:
            flash('Las contraseñas no coinciden', 'warning')
            return render_template('completar_registro.html', usuario=usuario, areas=areas)
        
        from werkzeug.security import generate_password_hash
        contrasena_hash = generate_password_hash(contrasena)
        
        # Actualizar usuario
        cursor.execute("""
            UPDATE usuarios SET 
                nombre = %s,
                usuario = %s,
                contrasena = %s,
                estado_registro = 'activo',
                token_invitacion = NULL,
                email_confirmado = 1
            WHERE id = %s
        """, (nombre, usuario['correo'].split('@')[0], contrasena_hash, usuario['id']))
        
        # Crear mensaje de bienvenida para cada área
        for area in areas:
            crear_mensaje_bienvenida_completo(cursor, usuario['empresa_id'], usuario['id'], area)
        
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ ¡Registro completado! Ya puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    cursor.close()
    db.close()
    
    return render_template('completar_registro.html', usuario=usuario, areas=areas)


# =============================================
# 4. MENSAJES DE BIENVENIDA A INCIDENCIAS
# =============================================

def crear_mensaje_bienvenida(cursor, empresa_id, usuario_id, area, rol, asignado_por):
    """Crea mensaje de bienvenida al asignar área"""
    
    mensajes_rol = {
        'responsable': f"""
            <h4>¡Felicidades! Has sido asignado como <strong>Responsable</strong> del área {area['nombre']}.</h4>
            <p>Como responsable, tus funciones principales son:</p>
            <ul>
                <li>Supervisar todas las operaciones del área</li>
                <li>Autorizar operaciones críticas (descuentos, anulaciones, etc.)</li>
                <li>Gestionar al equipo de trabajo</li>
                <li>Reportar al área de Administración</li>
                <li>Tomar decisiones estratégicas del área</li>
            </ul>
            <p>Tienes acceso completo a todas las funciones del área.</p>
        """,
        'supervisor': f"""
            <h4>Has sido asignado como <strong>Supervisor</strong> del área {area['nombre']}.</h4>
            <p>Como supervisor, tus funciones principales son:</p>
            <ul>
                <li>Supervisar las operaciones diarias</li>
                <li>Aprobar solicitudes del equipo</li>
                <li>Revisar y validar el trabajo realizado</li>
                <li>Apoyar al responsable del área</li>
                <li>Reportar incidencias</li>
            </ul>
            <p>Tienes acceso para editar y aprobar operaciones.</p>
        """,
        'operador': f"""
            <h4>Has sido asignado como <strong>Operador</strong> del área {area['nombre']}.</h4>
            <p>Como operador, tus funciones principales son:</p>
            <ul>
                <li>Ejecutar las tareas diarias del área</li>
                <li>Registrar operaciones en el sistema</li>
                <li>Seguir los procedimientos establecidos</li>
                <li>Reportar cualquier incidencia a tu supervisor</li>
            </ul>
            <p>Tienes acceso para crear y editar registros.</p>
        """
    }
    
    cursor.execute("""
        INSERT INTO incidencias 
        (empresa_id, usuario_destino_id, usuario_origen_id, tipo, titulo, mensaje, importante)
        VALUES (%s, %s, %s, 'bienvenida', %s, %s, 1)
    """, (
        empresa_id, 
        usuario_id, 
        asignado_por,
        f'Bienvenido al área {area["nombre"]}',
        mensajes_rol.get(rol, mensajes_rol['operador'])
    ))


def crear_mensaje_bienvenida_completo(cursor, empresa_id, usuario_id, area):
    """Crea mensaje de bienvenida completo al completar registro"""
    
    cursor.execute("""
        INSERT INTO incidencias 
        (empresa_id, usuario_destino_id, tipo, titulo, mensaje, importante)
        VALUES (%s, %s, 'bienvenida', %s, %s, 1)
    """, (
        empresa_id, 
        usuario_id,
        f'¡Bienvenido al equipo!',
        f"""
        <h4>¡Bienvenido al Sistema ERP!</h4>
        <p>Tu registro ha sido completado exitosamente.</p>
        <p>Has sido asignado al área <strong>{area['nombre']}</strong> como <strong>{area['rol_area'].upper()}</strong>.</p>
        <p><em>{area['descripcion']}</em></p>
        <hr>
        <p>Para comenzar:</p>
        <ol>
            <li>Explora el menú lateral para conocer las opciones disponibles</li>
            <li>Revisa las tareas pendientes en tu dashboard</li>
            <li>Si tienes dudas, contacta a tu supervisor</li>
        </ol>
        <p>¡Éxito en tu nuevo rol!</p>
        """
    ))


# =============================================
# 5. INCIDENCIAS (Bandeja de mensajes)
# =============================================

@app.route('/incidencias')
@require_login
def incidencias():
    """Bandeja de incidencias/mensajes del usuario"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT i.*, u.nombre as origen_nombre
        FROM incidencias i
        LEFT JOIN usuarios u ON u.id = i.usuario_origen_id
        WHERE i.empresa_id = %s AND i.usuario_destino_id = %s
        ORDER BY i.importante DESC, i.leida ASC, i.created_at DESC
    """, (eid, uid))
    mensajes = cursor.fetchall()
    
    # Contar no leídos
    cursor.execute("""
        SELECT COUNT(*) as no_leidos
        FROM incidencias
        WHERE empresa_id = %s AND usuario_destino_id = %s AND leida = 0
    """, (eid, uid))
    no_leidos = cursor.fetchone()['no_leidos']
    
    cursor.close()
    db.close()
    
    return render_template('incidencias.html', mensajes=mensajes, no_leidos=no_leidos)


@app.route('/incidencias/<int:inc_id>/leer', methods=['POST'])
@require_login
def incidencia_leer(inc_id):
    """Marcar incidencia como leída"""
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE incidencias SET leida = 1, fecha_lectura = NOW()
        WHERE id = %s AND usuario_destino_id = %s
    """, (inc_id, uid))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})


@app.route('/api/incidencias/count')
@require_login
def api_incidencias_count():
    """API para contar incidencias no leídas"""
    uid = g.usuario_id
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM incidencias
        WHERE empresa_id = %s AND usuario_destino_id = %s AND leida = 0
    """, (eid, uid))
    
    result = cursor.fetchone()
    cursor.close()
    db.close()
    
    return jsonify({'count': result['count'] if result else 0})


# =============================================
# 6. API BÚSQUEDA DE USUARIOS
# =============================================

@app.route('/api/usuarios/buscar')
@require_login
def api_buscar_usuarios():
    """API para buscar usuarios (usado en el buscador de áreas)"""
    eid = g.empresa_id
    q = request.args.get('q', '').strip()
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, nombre, correo, puesto, estado_registro
        FROM usuarios
        WHERE empresa_id = %s AND activo = 1
          AND (nombre LIKE %s OR correo LIKE %s)
        ORDER BY nombre
        LIMIT 20
    """, (eid, f'%{q}%', f'%{q}%'))
    
    usuarios = cursor.fetchall()
    cursor.close()
    db.close()
    
    return jsonify(usuarios)


# =============================================
# 7. CONTEXT PROCESSOR PARA INCIDENCIAS
# =============================================

@app.context_processor
def inject_incidencias_count():
    """Inyecta contador de incidencias no leídas"""
    if hasattr(g, 'usuario_id') and g.usuario_id:
        try:
            db = conexion_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as count FROM incidencias
                WHERE usuario_destino_id = %s AND leida = 0
            """, (g.usuario_id,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            return {'incidencias_count': result['count'] if result else 0}
        except:
            pass
    return {'incidencias_count': 0}


# =============================================
# 8. REENVIAR INVITACIÓN
# =============================================

@app.route('/admin/usuarios/<int:usuario_id>/reenviar_invitacion', methods=['GET', 'POST'])
@require_login
def admin_reenviar_invitacion(usuario_id):
    """Reenvía invitación a usuario pendiente"""
    
    # Si es GET, redirigir (alguien accedió directo a la URL)
    if request.method == 'GET':
        return redirect(url_for('admin_registro_usuarios'))
    
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM usuarios 
        WHERE id = %s AND empresa_id = %s AND estado_registro IN ('pendiente', 'invitado')
    """, (usuario_id, eid))
    usuario = cursor.fetchone()
    
    if not usuario:
        flash('Usuario no encontrado o ya está activo', 'danger')
        cursor.close()
        db.close()
        return redirect(url_for('admin_registro_usuarios'))
    
    # Generar nuevo token
    token = generar_token_invitacion()
    fecha_expira = datetime.now() + timedelta(days=7)
    
    cursor.execute("""
        UPDATE usuarios SET 
            token_invitacion = %s,
            fecha_invitacion = NOW(),
            fecha_token_expira = %s,
            estado_registro = 'invitado'
        WHERE id = %s
    """, (token, fecha_expira, usuario_id))
    
    db.commit()
    
    link = url_for('completar_registro', token=token, _external=True)
    
    flash(f'✅ Nueva invitación generada para {usuario["nombre"]}', 'success')
    flash(f'Link: {link}', 'info')
    
    cursor.close()
    db.close()
    
    return redirect(url_for('admin_registro_usuarios'))

# =============================================
# SISTEMA DE INVITACIONES
# Agregar a app.py
# =============================================



def generar_token_invitacion():
    """Genera token único para invitación"""
    return secrets.token_urlsafe(32)


@app.route('/admin/invitaciones')
@require_login
def admin_invitaciones():
    """Panel de invitaciones"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener invitaciones
    cursor.execute("""
        SELECT i.*, u.nombre as creada_por_nombre,
               uc.nombre as usuario_creado_nombre
        FROM invitaciones i
        JOIN usuarios u ON u.id = i.creada_por
        LEFT JOIN usuarios uc ON uc.id = i.usuario_creado_id
        WHERE i.empresa_id = %s
        ORDER BY i.fecha_creacion DESC
    """, (eid,))
    invitaciones = cursor.fetchall()
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as total
        FROM invitaciones
        WHERE empresa_id = %s
        GROUP BY estado
    """, (eid,))
    estados = {row['estado']: row['total'] for row in cursor.fetchall()}
    
    cursor.close()
    db.close()
    
    return render_template('admin/invitaciones.html', 
                          invitaciones=invitaciones,
                          estados=estados)


@app.route('/admin/invitaciones/nueva', methods=['GET', 'POST'])
@require_login
def admin_invitacion_nueva():
    """Crear nueva invitación"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()
        nombre_sugerido = request.form.get('nombre', '').strip()
        rol = request.form.get('rol', 'operador')
        areas_ids = request.form.getlist('areas[]')
        dias_expiracion = int(request.form.get('dias_expiracion', 7))
        notas = request.form.get('notas', '')
        
        # Validar correo no esté registrado
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            flash('Este correo ya está registrado en el sistema', 'danger')
            return redirect(url_for('admin_invitacion_nueva'))
        
        # Validar no exista invitación pendiente
        cursor.execute("""
            SELECT id FROM invitaciones 
            WHERE correo = %s AND empresa_id = %s AND estado = 'pendiente'
        """, (correo, eid))
        if cursor.fetchone():
            flash('Ya existe una invitación pendiente para este correo', 'warning')
            return redirect(url_for('admin_invitaciones'))
        
        # Crear invitación
        token = generar_token_invitacion()
        fecha_expiracion = datetime.now() + timedelta(days=dias_expiracion)
        
        # Preparar áreas como JSON
        areas_json = json.dumps(areas_ids) if areas_ids else None
        
        cursor.execute("""
            INSERT INTO invitaciones 
            (empresa_id, correo, nombre_sugerido, rol, areas_asignadas, token, 
             creada_por, fecha_expiracion, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, correo, nombre_sugerido, rol, areas_json, token, 
              uid, fecha_expiracion, notas))
        
        db.commit()
        
        # Generar link de invitación
        link_invitacion = url_for('registro_invitacion', token=token, _external=True)
        
        # Intentar enviar correo
        try:
            enviar_correo_invitacion(correo, nombre_sugerido, link_invitacion, dias_expiracion)
            flash(f'✅ Invitación enviada a {correo}', 'success')
        except Exception as e:
            # Si falla el correo, mostrar el link para copiarlo manualmente
            flash(f'⚠️ No se pudo enviar el correo. Comparte este link manualmente:', 'warning')
            flash(link_invitacion, 'info')
        
        cursor.close()
        db.close()
        return redirect(url_for('admin_invitaciones'))
    
    # GET: Mostrar formulario
    # Obtener áreas disponibles
    cursor.execute("""
        SELECT id, codigo, nombre, icono, color 
        FROM areas_sistema 
        WHERE empresa_id = %s AND activa = 1
        ORDER BY orden
    """, (eid,))
    areas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin/invitacion_nueva.html', areas=areas)


def enviar_correo_invitacion(correo, nombre, link, dias):
    """Envía correo de invitación"""
    try:
        msg = Message(
            subject='Invitación al Sistema ERP',
            sender=app.config.get('MAIL_USERNAME'),
            recipients=[correo]
        )
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">¡Hola{' ' + nombre if nombre else ''}!</h2>
            <p>Has sido invitado a unirte al sistema ERP.</p>
            <p>Haz clic en el siguiente botón para completar tu registro:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{link}" 
                   style="background-color: #007bff; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Aceptar Invitación
                </a>
            </p>
            <p style="color: #666; font-size: 14px;">
                Este link expira en {dias} días.<br>
                Si no solicitaste esta invitación, ignora este correo.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
                Si el botón no funciona, copia este link en tu navegador:<br>
                <a href="{link}">{link}</a>
            </p>
        </div>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        raise e


@app.route('/registro/invitacion/<token>', methods=['GET', 'POST'])
def registro_invitacion(token):
    """Página de registro por invitación"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Buscar invitación válida
    cursor.execute("""
        SELECT i.*, e.nombre as empresa_nombre
        FROM invitaciones i
        JOIN empresas e ON e.id = i.empresa_id
        WHERE i.token = %s
    """, (token,))
    invitacion = cursor.fetchone()
    
    if not invitacion:
        flash('Link de invitación inválido', 'danger')
        return redirect(url_for('login'))
    
    if invitacion['estado'] == 'aceptada':
        flash('Esta invitación ya fue utilizada', 'warning')
        return redirect(url_for('login'))
    
    if invitacion['estado'] == 'cancelada':
        flash('Esta invitación fue cancelada', 'danger')
        return redirect(url_for('login'))
    
    if invitacion['fecha_expiracion'] and invitacion['fecha_expiracion'] < datetime.now():
        cursor.execute("UPDATE invitaciones SET estado = 'expirada' WHERE id = %s", (invitacion['id'],))
        db.commit()
        flash('Esta invitación ha expirado', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        contrasena = request.form.get('contrasena', '')
        confirmar = request.form.get('confirmar_contrasena', '')
        
        # Validaciones
        if not nombre:
            flash('El nombre es requerido', 'warning')
            return render_template('registro_invitacion.html', invitacion=invitacion)
        
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'warning')
            return render_template('registro_invitacion.html', invitacion=invitacion)
        
        if contrasena != confirmar:
            flash('Las contraseñas no coinciden', 'warning')
            return render_template('registro_invitacion.html', invitacion=invitacion)
        
        # Crear usuario
        from werkzeug.security import generate_password_hash
        contrasena_hash = generate_password_hash(contrasena)
        
        cursor.execute("""
            INSERT INTO usuarios 
            (nombre, usuario, correo, contrasena, rol, empresa_id, activo, email_confirmado)
            VALUES (%s, %s, %s, %s, %s, %s, 1, 1)
        """, (nombre, invitacion['correo'].split('@')[0], invitacion['correo'], 
              contrasena_hash, invitacion['rol'], invitacion['empresa_id']))
        
        usuario_id = cursor.lastrowid
        
        # Asignar áreas si las hay
        if invitacion['areas_asignadas']:
            areas = json.loads(invitacion['areas_asignadas'])
            for area_id in areas:
                cursor.execute("""
                    INSERT INTO usuario_areas 
                    (empresa_id, usuario_id, area_id, rol_area, asignado_por)
                    VALUES (%s, %s, %s, 'operador', %s)
                """, (invitacion['empresa_id'], usuario_id, area_id, invitacion['creada_por']))
        
        # Marcar invitación como aceptada
        cursor.execute("""
            UPDATE invitaciones 
            SET estado = 'aceptada', fecha_aceptacion = NOW(), usuario_creado_id = %s
            WHERE id = %s
        """, (usuario_id, invitacion['id']))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ ¡Registro exitoso! Ya puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    cursor.close()
    db.close()
    
    return render_template('registro_invitacion.html', invitacion=invitacion)


@app.route('/admin/invitaciones/<int:inv_id>/cancelar', methods=['POST'])
@require_login
def admin_invitacion_cancelar(inv_id):
    """Cancelar invitación pendiente"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE invitaciones SET estado = 'cancelada'
        WHERE id = %s AND empresa_id = %s AND estado = 'pendiente'
    """, (inv_id, eid))
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('Invitación cancelada', 'success')
    return redirect(url_for('admin_invitaciones'))


@app.route('/admin/invitaciones/<int:inv_id>/reenviar', methods=['POST'])
@require_login
def admin_invitacion_reenviar(inv_id):
    """Reenviar invitación y renovar token"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM invitaciones 
        WHERE id = %s AND empresa_id = %s AND estado = 'pendiente'
    """, (inv_id, eid))
    invitacion = cursor.fetchone()
    
    if not invitacion:
        flash('Invitación no encontrada', 'danger')
        return redirect(url_for('admin_invitaciones'))
    
    # Generar nuevo token y extender expiración
    nuevo_token = generar_token_invitacion()
    nueva_expiracion = datetime.now() + timedelta(days=7)
    
    cursor.execute("""
        UPDATE invitaciones SET token = %s, fecha_expiracion = %s
        WHERE id = %s
    """, (nuevo_token, nueva_expiracion, inv_id))
    
    db.commit()
    
    link = url_for('registro_invitacion', token=nuevo_token, _external=True)
    
    try:
        enviar_correo_invitacion(invitacion['correo'], invitacion['nombre_sugerido'], link, 7)
        flash(f'✅ Invitación reenviada a {invitacion["correo"]}', 'success')
    except:
        flash(f'⚠️ Comparte este link: {link}', 'info')
    
    cursor.close()
    db.close()
    
    return redirect(url_for('admin_invitaciones'))


@app.route('/admin/invitaciones/<int:inv_id>/copiar_link')
@require_login
def admin_invitacion_copiar_link(inv_id):
    """Obtener link de invitación para copiar"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT token FROM invitaciones 
        WHERE id = %s AND empresa_id = %s AND estado = 'pendiente'
    """, (inv_id, eid))
    inv = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if inv:
        link = url_for('registro_invitacion', token=inv['token'], _external=True)
        return jsonify({'success': True, 'link': link})
    
    return jsonify({'success': False, 'error': 'Invitación no encontrada'})


# =============================================
# SISTEMA DE ÁREAS Y RESPONSABILIDADES
# Agregar a app.py
# =============================================

@app.route('/admin/areas')
@require_login
def admin_areas():
    """Administración de áreas del sistema"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar si existen áreas, si no, crearlas
    cursor.execute("SELECT COUNT(*) as total FROM areas_sistema WHERE empresa_id = %s", (eid,))
    if cursor.fetchone()['total'] == 0:
        # Insertar áreas predefinidas
        areas_predefinidas = [
            ('VENTAS', 'Ventas / Punto de Venta', 'Gestión de ventas, caja y atención al cliente', 'ventas', 'fas fa-cash-register', '#28a745', 1),
            ('INVENTARIO', 'Almacén / Inventario', 'Control de mercancía, entradas, salidas y existencias', 'inventario', 'fas fa-boxes', '#ffc107', 2),
            ('COMPRAS', 'Compras', 'Órdenes de compra y relación con proveedores', 'compras', 'fas fa-shopping-cart', '#17a2b8', 3),
            ('CAJA', 'Caja y Tesorería', 'Manejo de efectivo, cortes y flujo de caja', 'caja', 'fas fa-money-bill-wave', '#20c997', 4),
            ('CXC', 'Cuentas por Cobrar', 'Cartera de clientes y cobranza', 'cxc', 'fas fa-hand-holding-usd', '#28a745', 5),
            ('CXP', 'Cuentas por Pagar', 'Deudas con proveedores y programación de pagos', 'cxp', 'fas fa-file-invoice-dollar', '#dc3545', 6),
            ('CONTABILIDAD', 'Contabilidad', 'Registros contables, pólizas y estados financieros', 'contabilidad', 'fas fa-calculator', '#6f42c1', 7),
            ('RRHH', 'Recursos Humanos', 'Gestión de personal, nómina y prestaciones', 'nomina', 'fas fa-users', '#e83e8c', 8),
            ('GASTOS', 'Control de Gastos', 'Registro y autorización de gastos operativos', 'gastos', 'fas fa-receipt', '#fd7e14', 9),
            ('B2B_CLIENTE', 'B2B Como Cliente', 'Órdenes de compra y recepción de mercancía B2B', 'b2b', 'fas fa-building', '#007bff', 10),
            ('B2B_PROVEEDOR', 'B2B Como Proveedor', 'Pedidos, facturación y entregas B2B', 'b2b', 'fas fa-industry', '#6610f2', 11),
            ('REPARTO', 'Logística y Reparto', 'Entregas, rutas y distribución', 'reparto', 'fas fa-truck', '#795548', 12),
            ('ADMINISTRACION', 'Administración General', 'Supervisión general y toma de decisiones', 'admin', 'fas fa-cogs', '#343a40', 13),
            ('REPORTES', 'Reportes y Análisis', 'Generación de reportes y análisis de datos', 'reportes', 'fas fa-chart-bar', '#17a2b8', 14),
            ('AUDITORIA', 'Auditoría', 'Revisión de operaciones y cumplimiento', 'auditoria', 'fas fa-search', '#6c757d', 15),
        ]
        
        for area in areas_predefinidas:
            cursor.execute("""
                INSERT INTO areas_sistema 
                (empresa_id, codigo, nombre, descripcion, modulo_relacionado, icono, color, orden)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (eid, *area))
        
        db.commit()
        flash('✅ Áreas del sistema inicializadas', 'success')
    
    # Obtener áreas con sus responsables
    cursor.execute("""
        SELECT 
            a.*,
            GROUP_CONCAT(
                CASE WHEN ua.rol_area = 'responsable' THEN u.nombre END
                SEPARATOR ', '
            ) as responsables,
            GROUP_CONCAT(
                CASE WHEN ua.rol_area = 'supervisor' THEN u.nombre END
                SEPARATOR ', '
            ) as supervisores,
            COUNT(DISTINCT ua.usuario_id) as total_asignados
        FROM areas_sistema a
        LEFT JOIN usuario_areas ua ON ua.area_id = a.id AND ua.activo = 1
        LEFT JOIN usuarios u ON u.id = ua.usuario_id
        WHERE a.empresa_id = %s
        GROUP BY a.id
        ORDER BY a.orden
    """, (eid,))
    areas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin/areas.html', areas=areas)


@app.route('/admin/areas/toggle/<int:area_id>', methods=['POST'])
@require_login
def admin_area_toggle(area_id):
    """Activar/desactivar área"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE areas_sistema SET activa = NOT activa 
        WHERE id = %s AND empresa_id = %s
    """, (area_id, eid))
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('Estado del área actualizado', 'success')
    return redirect(url_for('admin_areas'))


@app.route('/admin/usuario-areas')
@require_login
def admin_usuario_areas():
    """Vista de asignaciones por usuario"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener usuarios con sus áreas asignadas
    cursor.execute("""
        SELECT 
            u.id as usuario_id,
            u.nombre as usuario,
            u.puesto,
            GROUP_CONCAT(
                CONCAT(a.nombre, ' (', ua.rol_area, ')')
                ORDER BY a.orden
                SEPARATOR ', '
            ) as areas_asignadas,
            COUNT(ua.id) as num_areas
        FROM usuarios u
        LEFT JOIN usuario_areas ua ON ua.usuario_id = u.id AND ua.activo = 1
        LEFT JOIN areas_sistema a ON a.id = ua.area_id AND a.activo = 1
        WHERE u.empresa_id = %s AND u.activo = 1
        GROUP BY u.id
        ORDER BY u.nombre
    """, (eid,))
    usuarios = cursor.fetchall()
    
    # Contar áreas totales
    cursor.execute("""
        SELECT COUNT(*) as total FROM areas_sistema WHERE empresa_id = %s AND activo = 1
    """, (eid,))
    total_areas = cursor.fetchone()['total']
    
    cursor.close()
    db.close()
    
    return render_template('admin/usuario_areas.html', usuarios=usuarios, total_areas=total_areas)

@app.route('/admin/usuarios/nuevo')
@require_login
def admin_usuario_nuevo():
    """Página para agregar nuevo usuario con selección de áreas"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener áreas disponibles
    cursor.execute("""
        SELECT id, nombre, codigo, icono, color, descripcion
        FROM areas_sistema
        WHERE activo = 1 AND empresa_id = %s
        ORDER BY orden, nombre
    """, (eid,))
    areas = cursor.fetchall()
    
    # ✅ DEBUG - IMPRIME EN LOGS
    import sys
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🔍 DEBUG admin_usuario_nuevo", file=sys.stderr)
    print(f"   Empresa ID: {eid}", file=sys.stderr)
    print(f"   Áreas encontradas: {len(areas)}", file=sys.stderr)
    if areas:
        print(f"   Primera área: {areas[0]}", file=sys.stderr)
    else:
        print(f"   ⚠️ NINGUNA ÁREA ENCONTRADA", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    cursor.close()
    db.close()
    
    return render_template('admin/usuario_nuevo.html', areas=areas)

@app.route('/admin/usuario/<int:usuario_id>/areas', methods=['GET', 'POST'])
@require_login
def admin_usuario_asignar_areas(usuario_id):
    """Asignar áreas del sistema a un usuario específico (por empresa)"""
    eid = g.empresa_id
    uid = g.usuario_id

    db = conexion_db()
    cursor = db.cursor(dictionary=True)

    # Obtener usuario (solo de la empresa actual)
    cursor.execute("""
        SELECT id, nombre
        FROM usuarios
        WHERE id = %s AND empresa_id = %s
        LIMIT 1
    """, (usuario_id, eid))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        db.close()
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin_registro_usuarios'))  # ajusta si tu endpoint es otro

    if request.method == 'POST':
        area_ids = request.form.getlist('area_id[]')

        # Desactivar asignaciones anteriores SOLO de esta empresa
        cursor.execute("""
            UPDATE usuario_areas
               SET activo = 0
             WHERE usuario_id = %s
               AND empresa_id = %s
        """, (usuario_id, eid))

        # Crear / reactivar asignaciones
        for area_id in area_ids:
            if not area_id:
                continue

            area_id = int(area_id)

            rol = request.form.get(f'rol_{area_id}', 'operador')
            puede_autorizar = (request.form.get(f'autorizar_{area_id}') == '1')

            # Buscar existente filtrando por empresa (importante)
            cursor.execute("""
                SELECT id
                  FROM usuario_areas
                 WHERE empresa_id = %s
                   AND usuario_id = %s
                   AND area_id = %s
                 LIMIT 1
            """, (eid, usuario_id, area_id))
            existente = cursor.fetchone()

            if existente:
                cursor.execute("""
                    UPDATE usuario_areas
                       SET rol_area = %s,
                           puede_autorizar = %s,
                           activo = 1
                     WHERE id = %s
                """, (rol, puede_autorizar, existente['id']))
            else:
                cursor.execute("""
                    INSERT INTO usuario_areas
                        (empresa_id, usuario_id, area_id, rol_area, puede_autorizar, asignado_por, activo)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, 1)
                """, (eid, usuario_id, area_id, rol, puede_autorizar, uid))

        db.commit()
        cursor.close()
        db.close()

        flash(f'✅ Áreas asignadas a {usuario["nombre"]}', 'success')
        return redirect(url_for('admin_registro_usuarios'))  # o admin_usuario_areas si esa ruta existe

    # GET: áreas del sistema + estado de asignación (por empresa)
    cursor.execute("""
        SELECT a.*,
               ua.rol_area,
               ua.puede_autorizar,
               CASE WHEN ua.id IS NOT NULL AND ua.activo = 1 THEN 1 ELSE 0 END AS asignada
          FROM areas_sistema a
          LEFT JOIN usuario_areas ua
                 ON ua.area_id = a.id
                AND ua.usuario_id = %s
                AND ua.empresa_id = %s
                AND ua.activo = 1
         WHERE a.empresa_id = %s
           AND a.activo = 1
         ORDER BY a.orden
    """, (usuario_id, eid, eid))
    areas = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('admin/usuario_asignar_areas.html', usuario=usuario, areas=areas)


# =============================================
# HELPER: Verificar permiso de usuario en área
# =============================================

def usuario_tiene_permiso(usuario_id, area_codigo, permiso='acceso'):
    """
    Verifica si un usuario tiene permiso en un área específica.
    
    Permisos: 'acceso', 'editar', 'eliminar', 'autorizar'
    """
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT ua.* FROM usuario_areas ua
        JOIN areas_sistema a ON a.id = ua.area_id
        WHERE ua.usuario_id = %s AND a.codigo = %s AND ua.activo = 1 AND a.activo = 1
    """, (usuario_id, area_codigo))
    
    asignacion = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not asignacion:
        return False
    
    if permiso == 'acceso':
        return True
    elif permiso == 'editar':
        return asignacion['puede_editar'] == 1
    elif permiso == 'eliminar':
        return asignacion['puede_eliminar'] == 1
    elif permiso == 'autorizar':
        return asignacion['puede_autorizar'] == 1
    elif permiso == 'responsable':
        return asignacion['rol_area'] in ('responsable', 'supervisor')
    
    return False


def obtener_areas_usuario(usuario_id):
    """Obtiene lista de códigos de áreas asignadas al usuario"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.codigo, a.nombre, ua.rol_area, ua.puede_autorizar
        FROM usuario_areas ua
        JOIN areas_sistema a ON a.id = ua.area_id
        WHERE ua.usuario_id = %s AND ua.activo = 1 AND a.activo = 1
    """, (usuario_id,))
    
    areas = cursor.fetchall()
    cursor.close()
    db.close()
    
    return areas


# =============================================
# SISTEMA DE NOTIFICACIONES DE USUARIO
# Agregar a app.py (reemplaza las funciones de incidencias)
# =============================================

# =============================================
# NOTIFICACIONES (Bandeja de mensajes)
# =============================================

@app.route('/notificaciones')
@require_login
def notificaciones():
    """Bandeja de notificaciones del usuario"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT n.*, u.nombre as origen_nombre
        FROM notificaciones_usuario n
        LEFT JOIN usuarios u ON u.id = n.usuario_origen_id
        WHERE n.empresa_id = %s AND n.usuario_destino_id = %s
        ORDER BY n.importante DESC, n.leida ASC, n.created_at DESC
    """, (eid, uid))
    mensajes = cursor.fetchall()
    
    # Contar no leídos
    cursor.execute("""
        SELECT COUNT(*) as no_leidos
        FROM notificaciones_usuario
        WHERE empresa_id = %s AND usuario_destino_id = %s AND leida = 0
    """, (eid, uid))
    no_leidos = cursor.fetchone()['no_leidos']
    
    cursor.close()
    db.close()
    
    return render_template('notificaciones.html', mensajes=mensajes, no_leidos=no_leidos)


@app.route('/notificaciones/<int:notif_id>/leer', methods=['POST'])
@require_login
def notificacion_leer(notif_id):
    """Marcar notificación como leída"""
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE notificaciones_usuario SET leida = 1, fecha_lectura = NOW()
        WHERE id = %s AND usuario_destino_id = %s
    """, (notif_id, uid))
    
    db.commit()
    cursor.close()
    db.close()
    
    return jsonify({'success': True})


@app.route('/api/notificaciones/count')
@require_login
def api_notificaciones_count():
    """API para contar notificaciones no leídas"""
    uid = g.usuario_id
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM notificaciones_usuario
        WHERE empresa_id = %s AND usuario_destino_id = %s AND leida = 0
    """, (eid, uid))
    
    result = cursor.fetchone()
    cursor.close()
    db.close()
    
    return jsonify({'count': result['count'] if result else 0})


# =============================================
# CONTEXT PROCESSOR PARA NOTIFICACIONES
# =============================================

@app.context_processor
def inject_notificaciones_count():
    """Inyecta contador de notificaciones no leídas"""
    if hasattr(g, 'usuario_id') and g.usuario_id:
        try:
            db = conexion_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as count FROM notificaciones_usuario
                WHERE usuario_destino_id = %s AND leida = 0
            """, (g.usuario_id,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            return {'notificaciones_count': result['count'] if result else 0}
        except:
            pass
    return {'notificaciones_count': 0}


# =============================================
# FUNCIONES HELPER PARA NOTIFICACIONES
# =============================================

def crear_notificacion(cursor, empresa_id, usuario_destino_id, titulo, mensaje, tipo='mensaje', usuario_origen_id=None, importante=0):
    """Crea una notificación para un usuario"""
    cursor.execute("""
        INSERT INTO notificaciones_usuario 
        (empresa_id, usuario_destino_id, usuario_origen_id, tipo, titulo, mensaje, importante)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (empresa_id, usuario_destino_id, usuario_origen_id, tipo, titulo, mensaje, importante))


def crear_mensaje_bienvenida(cursor, empresa_id, usuario_id, area, rol, asignado_por):
    """Crea mensaje de bienvenida al asignar área"""
    
    mensajes_rol = {
        'responsable': f"""
            <h4>¡Felicidades! Has sido asignado como <strong>Responsable</strong> del área {area['nombre']}.</h4>
            <p>Como responsable, tus funciones principales son:</p>
            <ul>
                <li>Supervisar todas las operaciones del área</li>
                <li>Autorizar operaciones críticas (descuentos, anulaciones, etc.)</li>
                <li>Gestionar al equipo de trabajo</li>
                <li>Reportar al área de Administración</li>
                <li>Tomar decisiones estratégicas del área</li>
            </ul>
            <p>Tienes acceso completo a todas las funciones del área.</p>
        """,
        'supervisor': f"""
            <h4>Has sido asignado como <strong>Supervisor</strong> del área {area['nombre']}.</h4>
            <p>Como supervisor, tus funciones principales son:</p>
            <ul>
                <li>Supervisar las operaciones diarias</li>
                <li>Aprobar solicitudes del equipo</li>
                <li>Revisar y validar el trabajo realizado</li>
                <li>Apoyar al responsable del área</li>
                <li>Reportar incidencias</li>
            </ul>
            <p>Tienes acceso para editar y aprobar operaciones.</p>
        """,
        'operador': f"""
            <h4>Has sido asignado como <strong>Operador</strong> del área {area['nombre']}.</h4>
            <p>Como operador, tus funciones principales son:</p>
            <ul>
                <li>Ejecutar las tareas diarias del área</li>
                <li>Registrar operaciones en el sistema</li>
                <li>Seguir los procedimientos establecidos</li>
                <li>Reportar cualquier incidencia a tu supervisor</li>
            </ul>
            <p>Tienes acceso para crear y editar registros.</p>
        """
    }
    
    crear_notificacion(
        cursor, 
        empresa_id, 
        usuario_id, 
        f'Bienvenido al área {area["nombre"]}',
        mensajes_rol.get(rol, mensajes_rol['operador']),
        tipo='bienvenida',
        usuario_origen_id=asignado_por,
        importante=1
    )


def crear_mensaje_bienvenida_completo(cursor, empresa_id, usuario_id, area):
    """Crea mensaje de bienvenida completo al completar registro"""
    
    mensaje = f"""
        <h4>¡Bienvenido al Sistema ERP!</h4>
        <p>Tu registro ha sido completado exitosamente.</p>
        <p>Has sido asignado al área <strong>{area['nombre']}</strong> como <strong>{area['rol_area'].upper()}</strong>.</p>
        <p><em>{area['descripcion']}</em></p>
        <hr>
        <p>Para comenzar:</p>
        <ol>
            <li>Explora el menú lateral para conocer las opciones disponibles</li>
            <li>Revisa las tareas pendientes en tu dashboard</li>
            <li>Si tienes dudas, contacta a tu supervisor</li>
        </ol>
        <p>¡Éxito en tu nuevo rol!</p>
    """
    
    crear_notificacion(
        cursor, 
        empresa_id, 
        usuario_id, 
        '¡Bienvenido al equipo!',
        mensaje,
        tipo='bienvenida',
        importante=1
    )

# =============================================
# SISTEMA DE NOTIFICACIONES WHATSAPP - TWILIO
# Agregar a app.py
# =============================================
#
# INSTALACIÓN: pip install twilio --break-system-packages
#
# CONFIGURACIÓN EN .env o config:
# TWILIO_ACCOUNT_SID=tu_account_sid
# TWILIO_AUTH_TOKEN=tu_auth_token
# TWILIO_WHATSAPP_FROM=whatsapp:+14155238886  (número sandbox o aprobado)
#
# =============================================

#from twilio.rest import Client
#import os

# Configuración Twilio (agregar a tu config)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

# Flag para activar/desactivar WhatsApp
WHATSAPP_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)


def enviar_whatsapp(telefono, mensaje):
    """
    Envía mensaje de WhatsApp usando Twilio.
    Retorna True si se envió correctamente.
    """
    if not WHATSAPP_ENABLED:
        print(f"⚠️ WhatsApp deshabilitado. Mensaje no enviado a {telefono}")
        return False
    
    if not telefono:
        return False
    
    # Limpiar y formatear número
    telefono_limpio = ''.join(filter(str.isdigit, str(telefono)))
    
    # Agregar código de país si no lo tiene (México por defecto)
    if len(telefono_limpio) == 10:
        telefono_limpio = '52' + telefono_limpio
    
    telefono_whatsapp = f'whatsapp:+{telefono_limpio}'
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            body=mensaje,
            to=telefono_whatsapp
        )
        
        print(f"✅ WhatsApp enviado a {telefono_whatsapp}: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando WhatsApp a {telefono_whatsapp}: {e}")
        return False


def obtener_telefonos_rol(empresa_id, rol):
    """
    Obtiene los teléfonos de usuarios con un rol específico que tengan notificaciones activas.
    """
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    rol_columna = f'es_{rol}'
    
    cursor.execute(f"""
        SELECT u.nombre, r.telefono_whatsapp
        FROM roles_b2b_empresa r
        JOIN usuarios u ON u.id = r.usuario_id
        WHERE r.empresa_id = %s 
          AND r.{rol_columna} = 1 
          AND r.notificar_whatsapp = 1
          AND r.telefono_whatsapp IS NOT NULL
          AND r.telefono_whatsapp != ''
          AND r.activo = 1
    """, (empresa_id,))
    
    usuarios = cursor.fetchall()
    cursor.close()
    db.close()
    
    return usuarios


def notificar_rol_whatsapp(empresa_id, rol, mensaje):
    """
    Envía notificación WhatsApp a todos los usuarios con un rol específico.
    Retorna cantidad de mensajes enviados.
    """
    usuarios = obtener_telefonos_rol(empresa_id, rol)
    enviados = 0
    
    for usuario in usuarios:
        mensaje_personalizado = f"Hola {usuario['nombre']},\n\n{mensaje}"
        if enviar_whatsapp(usuario['telefono_whatsapp'], mensaje_personalizado):
            enviados += 1
    
    return enviados


def registrar_whatsapp_enviado(alerta_id):
    """Marca una alerta como notificada por WhatsApp."""
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE alertas_b2b 
        SET whatsapp_enviado = 1, whatsapp_fecha = NOW()
        WHERE id = %s
    """, (alerta_id,))
    
    db.commit()
    cursor.close()
    db.close()


# =============================================
# FUNCIÓN MEJORADA DE CREAR ALERTA CON WHATSAPP
# =============================================
# Reemplaza tu función crear_alerta_b2b existente con esta:

def crear_alerta_b2b(empresa_id, rol_destino, tipo, titulo, mensaje, referencia_tipo=None, referencia_id=None, usuario_id=None, enviar_whatsapp_notif=True):
    """
    Crea una alerta B2B y opcionalmente envía notificación por WhatsApp.
    """
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            INSERT INTO alertas_b2b 
            (empresa_id, usuario_id, rol_destino, tipo, titulo, mensaje, referencia_tipo, referencia_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (empresa_id, usuario_id, rol_destino, tipo, titulo, mensaje, referencia_tipo, referencia_id))
        
        alerta_id = cursor.lastrowid
        db.commit()
        
        # Enviar WhatsApp si está habilitado
        if enviar_whatsapp_notif and WHATSAPP_ENABLED:
            mensaje_whatsapp = f"🔔 *{titulo}*\n\n{mensaje}\n\n📱 Revisa el sistema para más detalles."
            enviados = notificar_rol_whatsapp(empresa_id, rol_destino, mensaje_whatsapp)
            
            if enviados > 0:
                registrar_whatsapp_enviado(alerta_id)
                print(f"📱 WhatsApp enviado a {enviados} usuario(s) con rol {rol_destino}")
        
        cursor.close()
        db.close()
        return alerta_id
        
    except Exception as e:
        print(f"Error creando alerta: {e}")
        db.rollback()
        cursor.close()
        db.close()
        return None


# =============================================
# MENSAJES PREDEFINIDOS POR TIPO DE ALERTA
# =============================================

MENSAJES_WHATSAPP = {
    'orden_compra_nueva': {
        'titulo': '📦 Nueva Orden de Compra',
        'plantilla': 'Se ha generado la orden {folio} por ${total:.2f}.\nRequiere tu aprobación.'
    },
    'orden_compra_enviada': {
        'titulo': '📤 Orden Enviada',
        'plantilla': 'La orden {folio} ha sido enviada al proveedor.\nTotal: ${total:.2f}'
    },
    'pedido_recibido': {
        'titulo': '📥 Nuevo Pedido',
        'plantilla': 'Has recibido un nuevo pedido de {cliente}.\nOrden: {folio}\nTotal: ${total:.2f}'
    },
    'factura_emitida': {
        'titulo': '📄 Factura Emitida',
        'plantilla': 'Se ha emitido la factura {folio}.\nCliente: {cliente}\nTotal: ${total:.2f}'
    },
    'preparar_almacen': {
        'titulo': '🏭 Preparar Mercancía',
        'plantilla': 'Hay mercancía lista para preparar.\nFactura: {folio}\nCliente: {cliente}'
    },
    'listo_reparto': {
        'titulo': '🚚 Listo para Reparto',
        'plantilla': 'La factura {folio} está lista para entrega.\nCliente: {cliente}'
    },
    'en_camino': {
        'titulo': '🚛 Mercancía en Camino',
        'plantilla': 'Tu pedido {folio} está en camino.\nProveedor: {proveedor}'
    },
    'entrega_completada': {
        'titulo': '✅ Entrega Completada',
        'plantilla': 'La factura {folio} ha sido entregada al cliente {cliente}.'
    },
    'mercancia_recibida': {
        'titulo': '📦 Mercancía Recibida',
        'plantilla': 'El cliente ha confirmado la recepción de {folio}.\nTotal: ${total:.2f}'
    },
    'pago_recibido': {
        'titulo': '💰 Pago Recibido',
        'plantilla': 'Se ha recibido un pago de ${monto:.2f}.\nMétodo: {metodo}'
    },
    'cuenta_vencida': {
        'titulo': '⚠️ Cuenta Vencida',
        'plantilla': 'La cuenta de {cliente} tiene un saldo vencido de ${saldo:.2f}.'
    }
}


def notificar_evento_b2b(empresa_id, rol, tipo_evento, datos):
    """
    Función helper para enviar notificaciones predefinidas.
    
    Ejemplo de uso:
    notificar_evento_b2b(
        empresa_id=1,
        rol='supervisor',
        tipo_evento='orden_compra_nueva',
        datos={'folio': 'OC-001', 'total': 5000.00}
    )
    """
    if tipo_evento not in MENSAJES_WHATSAPP:
        print(f"⚠️ Tipo de evento desconocido: {tipo_evento}")
        return 0
    
    config = MENSAJES_WHATSAPP[tipo_evento]
    
    try:
        mensaje = config['plantilla'].format(**datos)
        titulo = config['titulo']
        mensaje_completo = f"*{titulo}*\n\n{mensaje}"
        
        return notificar_rol_whatsapp(empresa_id, rol, mensaje_completo)
    except KeyError as e:
        print(f"❌ Falta dato para mensaje: {e}")
        return 0


# =============================================
# RUTA PARA PROBAR WHATSAPP
# =============================================

@app.route('/b2b/test_whatsapp', methods=['GET', 'POST'])
@require_login
def test_whatsapp():
    """Página para probar envío de WhatsApp"""
    resultado = None
    
    if request.method == 'POST':
        telefono = request.form.get('telefono')
        mensaje = request.form.get('mensaje', 'Mensaje de prueba desde ERP B2B')
        
        if enviar_whatsapp(telefono, mensaje):
            resultado = {'exito': True, 'mensaje': f'Mensaje enviado a {telefono}'}
        else:
            resultado = {'exito': False, 'mensaje': 'Error al enviar. Verifica la configuración de Twilio.'}
    
    return render_template('b2b/test_whatsapp.html', 
                          resultado=resultado,
                          whatsapp_enabled=WHATSAPP_ENABLED)


# =============================================
# CONFIGURACIÓN DE WHATSAPP POR EMPRESA
# =============================================

@app.route('/b2b/configurar_whatsapp', methods=['GET', 'POST'])
@require_login
def configurar_whatsapp_b2b():
    """Configurar notificaciones WhatsApp por empresa"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Actualizar configuración de cada usuario
        usuario_ids = request.form.getlist('usuario_id[]')
        
        for uid in usuario_ids:
            telefono = request.form.get(f'telefono_{uid}', '')
            notificar = request.form.get(f'notificar_{uid}') == '1'
            
            cursor.execute("""
                UPDATE roles_b2b_empresa 
                SET telefono_whatsapp = %s, notificar_whatsapp = %s
                WHERE empresa_id = %s AND usuario_id = %s
            """, (telefono, 1 if notificar else 0, eid, uid))
        
        db.commit()
        flash('✅ Configuración de WhatsApp guardada', 'success')
    
    # Obtener usuarios con roles B2B
    cursor.execute("""
        SELECT u.id, u.nombre, r.telefono_whatsapp, r.notificar_whatsapp,
               r.es_supervisor, r.es_ventas, r.es_cxc, r.es_cxp, r.es_almacen, r.es_reparto
        FROM roles_b2b_empresa r
        JOIN usuarios u ON u.id = r.usuario_id
        WHERE r.empresa_id = %s AND r.activo = 1
        ORDER BY u.nombre
    """, (eid,))
    usuarios = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/configurar_whatsapp.html', 
                          usuarios=usuarios,
                          whatsapp_enabled=WHATSAPP_ENABLED)


# --- Catálogo PT: helpers ---



from flask import session, request, redirect, url_for, flash

def d(x):
    try: return Decimal(str(x))
    except: return Decimal("0")

def costo_pt(mercancia_id):
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT SUM(cantidad*costo_unitario) imp, SUM(cantidad) qty
        FROM movimientos_inventario
        WHERE producto_id=%s AND UPPER(tipo) IN ('COMPRA','ENTRADA')
    """, (mercancia_id,))
    r = cur.fetchone() or {}
    cur.close(); conn.close()
    imp = d(r.get('imp') or 0); qty = d(r.get('qty') or 0)
    return (imp/qty if qty>0 else d(0)).quantize(Decimal("0.01"))

def markup_auto_para_costo(costo):
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT markup_pct FROM pt_reglas_markup
        WHERE %s BETWEEN costo_min AND costo_max
        ORDER BY costo_min LIMIT 1
    """, (str(costo),))
    r = cur.fetchone()
    cur.close(); conn.close()
    return d(r['markup_pct']) if r else d("0.30")

def precio_con_modo(costo, modo, manual_pct):
    pct = manual_pct if modo=='manual' else markup_auto_para_costo(costo)
    return (costo*(d(1)+pct)).quantize(Decimal("0.01")), pct

from decimal import Decimal

def _pt_items_all():
    """Catálogo PT de la empresa activa - CORREGIDO"""
    eid = getattr(g, "empresa_id", session.get("empresa_id"))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            m.id,
            m.nombre,
            COALESCE(m.orden, 9999) AS orden,
            COALESCE(p.modo, 'auto') AS modo,
            COALESCE(p.markup_pct, 0.30) AS markup_pct,
            p.alias,
            p.precio_manual
        FROM mercancia m
        LEFT JOIN pt_precios p ON p.mercancia_id = m.id AND p.empresa_id = %s
        WHERE m.tipo_inventario_id = 3
          AND m.empresa_id = %s
          AND m.activo = 1
        ORDER BY orden ASC, COALESCE(p.alias, m.nombre) ASC
    """, (eid, eid))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    def D(x, fb="0"):
        try:
            return Decimal(str(x))
        except Exception:
            return Decimal(fb)

    items = []
    for r in rows:
        mid = r["id"]
        nombre = r["nombre"]
        modo = r["modo"]
        alias = r.get("alias")
        markup_pct = D(r.get("markup_pct") or "0")
        precio_manual = r.get("precio_manual")
        label = alias or nombre

        costo = D(costo_pt(mid))

        if modo == "manual" and precio_manual is not None:
            precio = D(precio_manual).quantize(Decimal("0.01"))
            pct_usado = (precio / costo - Decimal("1")) if costo > 0 else Decimal("0")
        else:
            if modo == "manual":
                pct = markup_pct
            else:
                pct = D(markup_auto_para_costo(costo))
            precio = (costo * (Decimal("1") + pct)).quantize(Decimal("0.01"))
            pct_usado = pct

        items.append({
            "id": mid,
            "nombre": nombre,
            "alias": alias,
            "label": label,
            "modo": modo,
            "costo": costo,
            "precio": precio,
            "pct_usado": pct_usado,
            "markup_pct": markup_pct,
            "precio_manual": precio_manual,
        })

    return items

@app.route('/test_apertura')
def test_apertura():
    return "<h1>TEST OK - La ruta funciona</h1>"

def obtener_tipo_cambio_actual():
    """Obtiene el tipo de cambio del turno abierto"""
    try:
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT tipo_cambio FROM turnos WHERE estado = 'abierto' ORDER BY fecha_apertura DESC LIMIT 1"
        )
        turno = cursor.fetchone()
        cursor.close()
        db.close()
        
        if turno:
            return float(turno['tipo_cambio'])
        
        return 20.0  # Valor por defecto
    except Exception as e:
        print(f"Error obteniendo tipo de cambio: {e}")
        return 20.0

@app.route('/apertura_turno', methods=['GET', 'POST'])
@require_login
def apertura_turno():
    """Apertura de turno con fondo de caja, inventario y tipo de cambio"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar si ya hay un turno abierto PARA ESTA EMPRESA
        cursor.execute("""
            SELECT * FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            ORDER BY fecha_apertura DESC LIMIT 1
        """, (uid, eid))
        turno_abierto = cursor.fetchone()
        
        if request.method == 'GET':
            # Obtener productos PT de ESTA EMPRESA
            cursor.execute("""
                SELECT m.id, m.nombre, COALESCE(p.precio_manual, 0) as precio
                FROM mercancia m
                LEFT JOIN pt_precios p ON p.mercancia_id = m.id AND p.empresa_id = %s
                WHERE m.tipo = 'PT' AND m.activo = 1 AND m.empresa_id = %s
                ORDER BY m.nombre
            """, (eid, eid))
            productos = cursor.fetchall()
            
            fondo_sugerido = 500.00
            tipo_cambio_sugerido = 20.00
            
            cursor.execute("""
                SELECT tipo_cambio FROM turnos 
                WHERE empresa_id = %s 
                ORDER BY fecha_apertura DESC LIMIT 1
            """, (eid,))
            ultimo_tc = cursor.fetchone()
            if ultimo_tc:
                tipo_cambio_sugerido = ultimo_tc['tipo_cambio']
            
            cursor.close()
            db.close()
            
            return render_template(
                'cobranza/apertura_turno.html',
                turno_abierto=turno_abierto,
                productos=productos,
                fondo_sugerido=fondo_sugerido,
                tipo_cambio_sugerido=tipo_cambio_sugerido,
                fecha_actual=datetime.now().strftime('%d/%m/%Y'),
                hora_actual=datetime.now().strftime('%H:%M')
            )
        
        # POST - Procesar apertura
        if turno_abierto:
            cursor.close()
            db.close()
            flash('Ya tienes un turno abierto', 'warning')
            return redirect(url_for('caja'))
        
        fondo_inicial = float(request.form.get('fondo_inicial', 0))
        tipo_cambio = float(request.form.get('tipo_cambio', 20.0))
        notas = request.form.get('notas', '')
        
        if fondo_inicial < 0 or tipo_cambio < 0:
            cursor.close()
            db.close()
            flash('Los valores no pueden ser negativos', 'danger')
            return redirect(url_for('apertura_turno'))
        
        # Insertar turno CON EMPRESA_ID
        cursor.execute("""
            INSERT INTO turnos 
            (empresa_id, usuario_id, usuario_nombre, fecha_apertura, fondo_inicial, tipo_cambio, estado, notas)
            VALUES (%s, %s, %s, %s, %s, %s, 'abierto', %s)
        """, (eid, uid, session.get('username', 'Admin'), datetime.now(), fondo_inicial, tipo_cambio, notas))
        turno_id = cursor.lastrowid
        
        # Guardar inventario inicial
        producto_ids = request.form.getlist('producto_id[]')
        producto_nombres = request.form.getlist('producto_nombre[]')
        cantidades = request.form.getlist('cantidad[]')
        
        for pid, pnombre, cant in zip(producto_ids, producto_nombres, cantidades):
            if cant and cant.strip():
                cursor.execute("""
                    INSERT INTO turno_inventario 
                    (turno_id, producto_id, producto_nombre, cantidad_inicial, empresa_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (turno_id, int(pid), pnombre, float(cant), eid))
        
        db.commit()
        session['turno_actual'] = turno_id
        
        flash(f'✅ Turno #{turno_id} abierto exitosamente', 'success')
        return redirect(url_for('caja'))
        
    except Exception as e:
        print(f"ERROR apertura_turno: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except:
            pass
        flash(f'Error al abrir turno: {str(e)}', 'danger')
        return redirect(url_for('apertura_turno'))
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            db.close()
        except:
            pass

@app.get("/caja")
@require_login
def caja():
    """Interfaz principal de caja/POS (multiempresa)"""
    uid = g.usuario_id
    eid = g.empresa_id

    print("=" * 60)
    print("🔍 DEBUG CAJA - INICIO")
    print(f"UID={uid}  EID={eid}")
    print("=" * 60)

    db = None
    cursor = None
    try:
        # Verificar turno abierto del usuario en su empresa
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        print("✅ Conexión a BD exitosa")

        cursor.execute(
            """
            SELECT *
            FROM turnos
            WHERE usuario_id = %s
              AND empresa_id = %s
              AND estado = 'abierto'
            LIMIT 1
            """,
            (uid, eid)
        )
        turno_abierto = cursor.fetchone()
        print(f"✅ Turno encontrado: {turno_abierto is not None}")

        # Cerrar pronto la conexión
        cursor.close(); cursor = None
        db.close(); db = None

        if not turno_abierto:
            print("❌ No hay turno abierto, redirigiendo...")
            flash('⚠️ Debes abrir un turno antes de usar la caja', 'warning')
            return redirect(url_for('apertura_turno'))

        # Sesión POS
        print("✅ Inicializando sesión...")
        session.setdefault("carrito", [])
        session.setdefault("pos_sel", [])
        session.setdefault("caja_holds", [])
        aplica_iva = session.get("caja_aplica_iva", True)

        carrito = session["carrito"]
        print(f"✅ Carrito: {len(carrito)} items")

        print("✅ Calculando totales...")
        totals = _totales(carrito, aplica_iva)

        print("✅ Obteniendo items PT (filtrados por empresa dentro de _pt_items_all)...")
        items_all = _pt_items_all()  # esta función debe usar g.empresa_id internamente
        print(f"✅ Items disponibles: {len(items_all)}")

        sel_ids = set(int(x) for x in session.get("pos_sel", []))
        print(f"✅ Items seleccionados en sesión: {len(sel_ids)}")

        items_pos = [it for it in items_all if it["id"] in sel_ids]
        print(f"✅ Items POS finales: {len(items_pos)}")

        # Tipo de cambio del turno actual (ajusta el nombre de columna si difiere)
        tipo_cambio = turno_abierto.get('tipo_cambio', 20.0)

        print("✅ Renderizando template...")
        return render_template(
            "cobranza/caja.html",
            carrito=carrito,
            totals=totals,
            tipo_cambio=tipo_cambio,
            items_pos=items_pos,
            items_all=items_all,
            sel_ids=sel_ids,
            holds=session.get("caja_holds", []),
            aplica_iva=aplica_iva
        )

    except Exception as e:
        print("=" * 60)
        print(f"❌ ERROR EN CAJA: {str(e)}")
        print("=" * 60)
        import traceback; traceback.print_exc()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('apertura_turno'))

    finally:
        # Limpieza segura
        try:
            if cursor: cursor.close()
        except: pass
        try:
            if db: db.close()
        except: pass

@app.post("/caja/iva_toggle")
def caja_iva_toggle():
    aplica = session.get("caja_aplica_iva", True)
    session["caja_aplica_iva"] = not aplica
    session.modified = True
    return redirect(url_for("caja"))

@app.route('/caja/pos_config', methods=['POST'])
def caja_pos_config():
    """Guardar selección de artículos en sesión"""
    sel = request.form.getlist('sel[]')
    session['pos_sel'] = sel
    session.modified = True
    flash(f'✅ Configuración guardada: {len(sel)} artículos', 'success')
    return redirect(url_for('caja'))

@app.route('/agregar_consumo', methods=['POST'])
@require_login
def agregar_consumo():
    """Agregar un consumo propio - CON EMPRESA"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar turno abierto DE ESTA EMPRESA
        cursor.execute("""
            SELECT id FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        producto_id = int(request.form.get('producto_id'))
        cantidad = float(request.form.get('cantidad', 1))
        notas = request.form.get('notas', '')
        
        # Obtener info del producto VALIDANDO EMPRESA
        cursor.execute("""
            SELECT m.nombre, COALESCE(p.precio_manual, 0) as precio
            FROM mercancia m
            LEFT JOIN pt_precios p ON p.mercancia_id = m.id AND p.empresa_id = %s
            WHERE m.id = %s AND m.empresa_id = %s
        """, (eid, producto_id, eid))
        producto = cursor.fetchone()

        if not producto:
            cursor.close()
            db.close()
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('consumos_propios'))

        precio_unitario = float(producto['precio'])
        subtotal = cantidad * precio_unitario
        
        # Registrar consumo CON EMPRESA
        cursor.execute("""
            INSERT INTO consumos_propios 
            (empresa_id, turno_id, fecha, producto_id, producto_nombre, cantidad, 
             precio_unitario, subtotal, usuario_id, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], datetime.now(), producto_id, producto['nombre'], 
              cantidad, precio_unitario, subtotal, uid, notas))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ Consumo registrado: {producto["nombre"]} x {cantidad}', 'success')
        return redirect(url_for('consumos_propios'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error al registrar consumo: {str(e)}', 'danger')
        return redirect(url_for('consumos_propios'))

@app.route('/agregar_merma', methods=['POST'])
@require_login
def agregar_merma():
    """Agregar merma al turno actual - CON EMPRESA"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        producto_id = int(request.form.get('producto_id'))
        cantidad = float(request.form.get('cantidad', 0))
        motivo = request.form.get('motivo', '')
        
        # Validar producto pertenece a empresa
        cursor.execute("""
            SELECT nombre FROM mercancia 
            WHERE id = %s AND empresa_id = %s
        """, (producto_id, eid))
        producto = cursor.fetchone()
        
        if not producto:
            flash('Producto no válido', 'danger')
            return redirect(url_for('cerrar_turno'))
        
        cursor.execute("""
            INSERT INTO turno_mermas 
            (empresa_id, turno_id, producto_id, producto_nombre, cantidad, motivo, fecha, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], producto_id, producto['nombre'], cantidad, motivo, 
              datetime.now(), uid))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ Merma registrada: {cantidad} unidades', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

# =============================================
# RUTAS AJAX PARA MERMAS Y GASTOS (SIN RECARGAR)
# =============================================

@app.route('/agregar_merma_ajax', methods=['POST'])
@require_login
def agregar_merma_ajax():
    """Agregar merma via AJAX - no recarga página"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    try:
        data = request.get_json()
        producto_id = int(data.get('producto_id'))
        producto_nombre = data.get('producto_nombre', '')
        cantidad = float(data.get('cantidad', 0))
        motivo = data.get('motivo', '')
        
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Buscar turno abierto
        cursor.execute("""
            SELECT id FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close(); db.close()
            return jsonify({'success': False, 'error': 'No hay turno abierto'})
        
        # Insertar merma
        cursor.execute("""
            INSERT INTO turno_mermas 
            (empresa_id, turno_id, producto_id, producto_nombre, cantidad, motivo, fecha, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], producto_id, producto_nombre, cantidad, motivo, datetime.now(), uid))
        
        merma_id = cursor.lastrowid
        db.commit()
        cursor.close(); db.close()
        
        return jsonify({'success': True, 'id': merma_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/eliminar_merma_ajax', methods=['POST'])
@require_login
def eliminar_merma_ajax():
    """Eliminar merma via AJAX"""
    eid = g.empresa_id
    
    try:
        data = request.get_json()
        merma_id = int(data.get('id'))
        
        db = conexion_db()
        cursor = db.cursor()
        
        cursor.execute("""
            DELETE FROM turno_mermas 
            WHERE id = %s AND empresa_id = %s
        """, (merma_id, eid))
        
        db.commit()
        cursor.close(); db.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/agregar_gasto_ajax', methods=['POST'])
@require_login
def agregar_gasto_ajax():
    """Agregar gasto via AJAX - no recarga página"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    try:
        data = request.get_json()
        tipo = data.get('tipo', 'gasto')
        concepto = data.get('concepto', '')
        monto = float(data.get('monto', 0))
        notas = data.get('notas', '')
        
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Buscar turno abierto
        cursor.execute("""
            SELECT id FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close(); db.close()
            return jsonify({'success': False, 'error': 'No hay turno abierto'})
        
        # Insertar gasto
        cursor.execute("""
            INSERT INTO turno_gastos 
            (empresa_id, turno_id, tipo, concepto, monto, notas, fecha, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], tipo, concepto, monto, notas, datetime.now(), uid))
        
        gasto_id = cursor.lastrowid
        db.commit()
        cursor.close(); db.close()
        
        return jsonify({'success': True, 'id': gasto_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/eliminar_gasto_ajax', methods=['POST'])
@require_login
def eliminar_gasto_ajax():
    """Eliminar gasto via AJAX"""
    eid = g.empresa_id
    
    try:
        data = request.get_json()
        gasto_id = int(data.get('id'))
        
        db = conexion_db()
        cursor = db.cursor()
        
        cursor.execute("""
            DELETE FROM turno_gastos 
            WHERE id = %s AND empresa_id = %s
        """, (gasto_id, eid))
        
        db.commit()
        cursor.close(); db.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/eliminar_merma/<int:merma_id>', methods=['POST'])
@require_login
def eliminar_merma(merma_id):
    """Eliminar una merma del turno - VALIDANDO EMPRESA"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            DELETE FROM turno_mermas 
            WHERE id = %s AND empresa_id = %s
        """, (merma_id, eid))
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Merma eliminada', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

# ==================== HISTORIAL DE TICKETS ====================

@app.route('/historial_tickets')
@require_login
def historial_tickets():
    eid = g.empresa_id
    
    fecha_filtro = request.args.get('fecha')
    buscar = request.args.get('buscar', '').strip()
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT 
                id,
                folio,
                total,
                metodo_pago,
                efectivo_recibido,
                cambio,
                DATE_FORMAT(fecha, '%%Y-%%m-%%d %%H:%%i') as fecha_formateada,
                DATE_FORMAT(fecha, '%%Y-%%m-%%d') as fecha_corta
            FROM caja_ventas
            WHERE empresa_id = %s
        """
        params = [eid]
        
        if fecha_filtro:
            query += " AND DATE(fecha) = %s"
            params.append(fecha_filtro)
        
        if buscar:
            query += " AND (folio LIKE %s OR id LIKE %s)"
            params.extend([f'%{buscar}%', f'%{buscar}%'])
        
        query += " ORDER BY fecha DESC LIMIT 100"
        
        cur.execute(query, params)
        tickets = cur.fetchall()
        
        # Calcular totales
        total_tickets = len(tickets)
        total_ventas = sum(t['total'] or 0 for t in tickets)
        
    finally:
        cur.close()
        conn.close()
    
    return render_template(
        'cobranza/historial_tickets.html',
        tickets=tickets,
        fecha_filtro=fecha_filtro,
        buscar=buscar,
        total_tickets=total_tickets,
        total_ventas=total_ventas
    )

@app.route('/ticket/<int:ticket_id>')
@require_login
def ver_ticket(ticket_id):
    """Ver detalle de un ticket específico - FILTRADO POR EMPRESA"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener venta VALIDANDO EMPRESA
    cursor.execute("""
        SELECT 
            v.*,
            u.nombre as cajero
        FROM caja_ventas v
        LEFT JOIN usuarios u ON v.usuario_id = u.id
        WHERE v.id = %s AND v.empresa_id = %s
    """, (ticket_id, eid))
    venta = cursor.fetchone()
    
    if not venta:
        cursor.close()
        db.close()
        flash('Ticket no encontrado', 'danger')
        return redirect(url_for('historial_tickets'))
    
    # Obtener detalle FILTRADO
    cursor.execute("""
        SELECT 
            d.*,
            m.nombre as producto
        FROM caja_ventas_detalle d
        LEFT JOIN mercancia m ON d.mercancia_id = m.id
        WHERE d.venta_id = %s AND d.empresa_id = %s
    """, (ticket_id, eid))
    detalle = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('cobranza/ver_ticket.html', venta=venta, detalle=detalle)


# ==================== RETIRO PARCIAL DE EFECTIVO ====================

@app.route('/registrar_retiro', methods=['POST'])
@require_login
def registrar_retiro():
    """Registrar retiro parcial de efectivo - CON EMPRESA"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id FROM turnos 
        WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
        LIMIT 1
    """, (uid, eid))
    turno = cursor.fetchone()
    
    if not turno:
        cursor.close()
        db.close()
        flash('⚠️ No hay un turno abierto', 'warning')
        return redirect(url_for('apertura_turno'))
    
    try:
        monto = float(request.form.get('monto', 0))
        motivo = request.form.get('motivo', '')
        notas = request.form.get('notas', '')
        
        if monto <= 0:
            flash('El monto debe ser mayor a cero', 'danger')
            return redirect(url_for('caja'))
        
        # Registrar retiro CON EMPRESA
        cursor.execute("""
            INSERT INTO retiros_efectivo 
            (empresa_id, turno_id, fecha, monto, motivo, notas, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], datetime.now(), monto, motivo, notas, uid))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ Retiro de ${monto:.2f} registrado exitosamente', 'success')
        return redirect(url_for('caja'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('caja'))

@app.route('/historial_retiros')
@require_login
def historial_retiros():
    """Ver historial de retiros - FILTRADO POR EMPRESA"""
    eid = g.empresa_id
    turno_id = request.args.get('turno_id', '')
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT 
            r.*,
            u.nombre as usuario,
            t.usuario_nombre as cajero_turno
        FROM retiros_efectivo r
        LEFT JOIN usuarios u ON r.usuario_id = u.id
        LEFT JOIN turnos t ON r.turno_id = t.id
        WHERE r.empresa_id = %s
    """
    params = [eid]
    
    if turno_id:
        query += " AND r.turno_id = %s"
        params.append(turno_id)
    
    query += " ORDER BY r.fecha DESC LIMIT 100"
    
    cursor.execute(query, params)
    retiros = cursor.fetchall()
    
    # Obtener turnos DE ESTA EMPRESA para filtro
    cursor.execute("""
        SELECT id, usuario_nombre, fecha_apertura 
        FROM turnos 
        WHERE empresa_id = %s
        ORDER BY fecha_apertura DESC 
        LIMIT 50
    """, (eid,))
    turnos = cursor.fetchall()
    
    total_retiros = sum(r['monto'] for r in retiros)
    
    cursor.close()
    db.close()
    
    return render_template(
        'cobranza/historial_retiros.html',
        retiros=retiros,
        turnos=turnos,
        total_retiros=total_retiros,
        turno_id=turno_id
    )

@app.route('/agregar_gasto', methods=['POST'])
@require_login
def agregar_gasto():
    """Agregar gasto o compra al turno actual - CON EMPRESA"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        concepto = request.form.get('concepto', '')
        monto = float(request.form.get('monto', 0))
        tipo = request.form.get('tipo', 'gasto')
        notas = request.form.get('notas', '')
        
        cursor.execute("""
            INSERT INTO turno_gastos 
            (empresa_id, turno_id, fecha, concepto, monto, tipo, notas, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], datetime.now(), concepto, monto, tipo, notas, uid))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ {tipo.capitalize()} registrado: ${monto:.2f}', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

@app.route('/eliminar_gasto/<int:gasto_id>', methods=['POST'])
@require_login
def eliminar_gasto(gasto_id):
    """Eliminar un gasto del turno - VALIDANDO EMPRESA"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Solo eliminar si pertenece a la empresa
        cursor.execute("""
            DELETE FROM turno_gastos 
            WHERE id = %s AND empresa_id = %s
        """, (gasto_id, eid))
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Gasto eliminado', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

@app.route('/cerrar_turno', methods=['GET', 'POST'])
@require_login
def cerrar_turno():
    """Cierre de turno - FILTRADO POR EMPRESA"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        if request.method == 'GET':
            # Obtener productos PT de ESTA EMPRESA
            cursor.execute("""
                SELECT m.id, m.nombre, COALESCE(p.precio_manual, 0) as precio
                FROM mercancia m
                LEFT JOIN pt_precios p ON p.mercancia_id = m.id AND p.empresa_id = %s
                WHERE m.tipo = 'PT' AND m.activo = 1 AND m.empresa_id = %s
                ORDER BY m.nombre
            """, (eid, eid))
            productos = cursor.fetchall()
            
            # Obtener retiros DE ESTA EMPRESA
            cursor.execute("""
                SELECT COALESCE(SUM(monto), 0) as total_retiros
                FROM retiros_efectivo 
                WHERE turno_id = %s AND empresa_id = %s
            """, (turno['id'], eid))
            retiros = cursor.fetchone()
            
            # Obtener gastos
            cursor.execute("""
                SELECT * FROM turno_gastos 
                WHERE turno_id = %s AND empresa_id = %s 
                ORDER BY fecha DESC
            """, (turno['id'], eid))
            gastos = cursor.fetchall()
            total_gastos = sum(g['monto'] for g in gastos)
            
            # Obtener mermas
            cursor.execute("""
                SELECT * FROM turno_mermas 
                WHERE turno_id = %s AND empresa_id = %s 
                ORDER BY fecha DESC
            """, (turno['id'], eid))
            mermas = cursor.fetchall()
            
            ya_validado = session.get(f'turno_{turno["id"]}_validado', False)
            
            cursor.close()
            db.close()
            
            return render_template(
                'cobranza/cerrar_turno.html',
                turno=turno,
                productos=productos,
                retiros=retiros,
                gastos=gastos,
                total_gastos=total_gastos,
                mermas=mermas,
                ya_validado=ya_validado
            )
        
        # POST - Procesar
        ya_validado = session.get(f'turno_{turno["id"]}_validado', False)
        
        if not ya_validado:
            diferencias_inventario = []
            producto_ids = request.form.getlist('producto_id[]')
            producto_nombres = request.form.getlist('producto_nombre[]')
            producto_precios = request.form.getlist('producto_precio[]')
            cantidades_finales = request.form.getlist('cantidad_final[]')
            
            for pid, pnombre, pprecio, cant_final in zip(producto_ids, producto_nombres, producto_precios, cantidades_finales):
                if not cant_final or not cant_final.strip():
                    continue
                
                pid = int(pid)
                cant_final = float(cant_final)
                pprecio = float(pprecio)
                
                cursor.execute("""
                    SELECT cantidad_inicial FROM turno_inventario
                    WHERE turno_id = %s AND producto_id = %s AND empresa_id = %s
                """, (turno['id'], pid, eid))
                inicial = cursor.fetchone()
                cant_inicial = float(inicial['cantidad_inicial']) if inicial else 0
                
                cursor.execute("""
                    SELECT COALESCE(SUM(cantidad), 0) as total_consumos
                    FROM consumos_propios
                    WHERE turno_id = %s AND producto_id = %s AND empresa_id = %s
                """, (turno['id'], pid, eid))
                consumos = cursor.fetchone()
                cant_consumos = float(consumos['total_consumos'])
                
                cursor.execute("""
                    SELECT COALESCE(SUM(cantidad), 0) as total_mermas
                    FROM turno_mermas
                    WHERE turno_id = %s AND producto_id = %s AND empresa_id = %s
                """, (turno['id'], pid, eid))
                mermas_prod = cursor.fetchone()
                cant_mermas = float(mermas_prod['total_mermas'])
                
                ventas_teoricas = cant_inicial - cant_consumos - cant_mermas - cant_final
                valor_diferencia = abs(ventas_teoricas) * pprecio
                
                if valor_diferencia > 70:
                    diferencias_inventario.append({
                        'producto': pnombre,
                        'diferencia': ventas_teoricas,
                        'valor': valor_diferencia
                    })
            
            if diferencias_inventario:
                session[f'turno_{turno["id"]}_validado'] = True
                flash('⚠️ ATENCIÓN: Favor de verificar el conteo.', 'warning')
                for dif in diferencias_inventario:
                    flash(f"• {dif['producto']}: Diferencia de {dif['diferencia']:.2f} unidades (${dif['valor']:.2f})", 'warning')
                flash('Presiona "Cerrar Turno" nuevamente para confirmar.', 'info')
                cursor.close()
                db.close()
                return redirect(url_for('cerrar_turno'))
            else:
                session[f'turno_{turno["id"]}_validado'] = True
        
        # CERRAR DEFINITIVAMENTE
        producto_ids = request.form.getlist('producto_id[]')
        producto_nombres = request.form.getlist('producto_nombre[]')
        producto_precios = request.form.getlist('producto_precio[]')
        cantidades_finales = request.form.getlist('cantidad_final[]')
        
        ventas_por_producto = []
        total_ventas_calculado = 0
        
        for pid, pnombre, pprecio, cant_final in zip(producto_ids, producto_nombres, producto_precios, cantidades_finales):
            if not cant_final or not cant_final.strip():
                continue
            
            pid = int(pid)
            cant_final = float(cant_final)
            pprecio = float(pprecio)
            
            # Guardar inventario final CON EMPRESA
            cursor.execute("""
                INSERT INTO turno_inventario_final 
                (empresa_id, turno_id, producto_id, producto_nombre, cantidad_final)
                VALUES (%s, %s, %s, %s, %s)
            """, (eid, turno['id'], pid, pnombre, cant_final))
            
            cursor.execute("""
                SELECT cantidad_inicial FROM turno_inventario
                WHERE turno_id = %s AND producto_id = %s AND empresa_id = %s
            """, (turno['id'], pid, eid))
            inicial = cursor.fetchone()
            cant_inicial = float(inicial['cantidad_inicial']) if inicial else 0
            
            cursor.execute("""
                SELECT COALESCE(SUM(cantidad), 0) as total
                FROM consumos_propios
                WHERE turno_id = %s AND producto_id = %s AND empresa_id = %s
            """, (turno['id'], pid, eid))
            consumos = cursor.fetchone()
            cant_consumos = float(consumos['total'])
            
            cursor.execute("""
                SELECT COALESCE(SUM(cantidad), 0) as total
                FROM turno_mermas
                WHERE turno_id = %s AND producto_id = %s AND empresa_id = %s
            """, (turno['id'], pid, eid))
            mermas = cursor.fetchone()
            cant_mermas = float(mermas['total'])
            
            unidades_vendidas = cant_inicial - cant_consumos - cant_mermas - cant_final
            importe_venta = unidades_vendidas * pprecio
            total_ventas_calculado += importe_venta
            
            if unidades_vendidas != 0:
                ventas_por_producto.append({
                    'producto': pnombre,
                    'inicial': cant_inicial,
                    'consumos': cant_consumos,
                    'mermas': cant_mermas,
                    'final': cant_final,
                    'vendidas': unidades_vendidas,
                    'precio': pprecio,
                    'importe': importe_venta
                })
        
        # Arqueo CON EMPRESA
        billetes_20 = int(request.form.get('billetes_20', 0))
        billetes_50 = int(request.form.get('billetes_50', 0))
        billetes_100 = int(request.form.get('billetes_100', 0))
        billetes_200 = int(request.form.get('billetes_200', 0))
        billetes_500 = int(request.form.get('billetes_500', 0))
        dolares = float(request.form.get('dolares', 0))
        monedas = float(request.form.get('monedas', 0))
        
        tipo_cambio = float(turno['tipo_cambio'])
        total_billetes = (billetes_20 * 20 + billetes_50 * 50 + billetes_100 * 100 + 
                         billetes_200 * 200 + billetes_500 * 500)
        total_dolares_pesos = dolares * tipo_cambio
        conteo_final = total_billetes + total_dolares_pesos + monedas
        
        cursor.execute("""
            INSERT INTO turno_arqueo 
            (empresa_id, turno_id, billetes_20, billetes_50, billetes_100, billetes_200, 
             billetes_500, dolares, monedas, total_efectivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, turno['id'], billetes_20, billetes_50, billetes_100, billetes_200,
              billetes_500, dolares, monedas, conteo_final))
        
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total FROM retiros_efectivo
            WHERE turno_id = %s AND empresa_id = %s
        """, (turno['id'], eid))
        total_retiros = float(cursor.fetchone()['total'])
        
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total FROM turno_gastos
            WHERE turno_id = %s AND empresa_id = %s
        """, (turno['id'], eid))
        total_gastos = float(cursor.fetchone()['total'])
        
        total_corte = total_ventas_calculado
        efectivo_deberia_haber = total_ventas_calculado - total_retiros - total_gastos
        diferencia_efectivo = conteo_final - efectivo_deberia_haber
        
        notas_cierre = request.form.get('notas_cierre', '')
        
        cursor.execute("""
            UPDATE turnos 
            SET estado = 'cerrado',
                fecha_cierre = %s,
                fondo_final = %s,
                total_ventas = %s,
                diferencia = %s,
                notas = CONCAT(COALESCE(notas, ''), '\nCierre: ', %s)
            WHERE id = %s AND empresa_id = %s
        """, (datetime.now(), conteo_final + float(turno['fondo_inicial']),
              total_ventas_calculado, diferencia_efectivo, notas_cierre, turno['id'], eid))
        
        db.commit()
        cursor.close()
        db.close()
        
        session.pop(f'turno_{turno["id"]}_validado', None)
        session.pop('turno_actual', None)
        
        return render_template(
            'cobranza/resumen_cierre.html',
            turno=turno,
            ventas_por_producto=ventas_por_producto,
            total_ventas=total_ventas_calculado,
            total_retiros=total_retiros,
            total_gastos=total_gastos,
            conteo_final=conteo_final,
            total_corte=total_corte,
            diferencia=diferencia_efectivo
        )
        
    except Exception as e:
        print(f"ERROR cerrar_turno: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('apertura_turno'))

# ==================== CONSUMOS PROPIOS ====================

@app.route('/consumos_propios')
@require_login
def consumos_propios():
    """Interfaz para registrar consumos propios - FILTRADO POR EMPRESA"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    try:
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Verificar turno abierto DE ESTA EMPRESA
        cursor.execute("""
            SELECT * FROM turnos 
            WHERE usuario_id = %s AND empresa_id = %s AND estado = 'abierto' 
            LIMIT 1
        """, (uid, eid))
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        # Obtener productos PT de ESTA EMPRESA
        cursor.execute("""
            SELECT 
                m.id, 
                m.nombre, 
                COALESCE(p.precio_manual, 0) as precio,
                0 as existencias
            FROM mercancia m
            LEFT JOIN pt_precios p ON p.mercancia_id = m.id AND p.empresa_id = %s
            WHERE m.tipo = 'PT' AND m.activo = 1 AND m.empresa_id = %s
            ORDER BY m.nombre
        """, (eid, eid))
        productos = cursor.fetchall()
        
        # Obtener consumos del turno FILTRADOS
        cursor.execute("""
            SELECT 
                c.*,
                u.nombre as usuario
            FROM consumos_propios c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.turno_id = %s AND c.empresa_id = %s
            ORDER BY c.fecha DESC
        """, (turno['id'], eid))
        consumos = cursor.fetchall()
        
        total_consumos = sum(c['subtotal'] for c in consumos)
        
        cursor.close()
        db.close()
        
        return render_template(
            'cobranza/consumos_propios.html',
            turno=turno,
            productos=productos,
            consumos=consumos,
            total_consumos=total_consumos
        )
    
    except Exception as e:
        print(f"ERROR consumos_propios: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('apertura_turno'))
   
@app.route('/eliminar_consumo/<int:consumo_id>', methods=['POST'])
@require_login
def eliminar_consumo(consumo_id):
    """Eliminar un consumo propio - VALIDANDO EMPRESA"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            DELETE FROM consumos_propios 
            WHERE id = %s AND empresa_id = %s
        """, (consumo_id, eid))
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Consumo eliminado', 'success')
        return redirect(url_for('consumos_propios'))
        
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('consumos_propios'))


# --- Vistas ---

@app.get("/pt/catalogo")
@require_login
def pt_catalogo():
    """Catálogo de Productos Terminados (solo de la empresa activa)"""
    eid = g.empresa_id

    # Obtiene los productos filtrados por empresa
    items = _pt_items_all()  # Esta función ya debe filtrar por empresa internamente

    return render_template(
        "inventarios/PT/pt_catalogo.html",
        items=items
    )

@app.post("/pt/catalogo_guardar")
@require_login
def pt_catalogo_guardar():
    eid            = g.empresa_id

    ids            = request.form.getlist("id[]")
    modos          = request.form.getlist("modo[]")
    markups        = request.form.getlist("manual_pct[]")
    precios_manual = request.form.getlist("precio_manual[]")
    aliases        = request.form.getlist("alias[]")

    print("=" * 60)
    print("🔍 DEBUG pt_catalogo_guardar  EID=", eid)
    print(f"Total productos recibidos: {len(ids)}")
    print("=" * 60)

    conn = conexion_db()
    cur  = conn.cursor()

    for i, mid in enumerate(ids):
        mid = int(mid)

        modo  = (modos[i] if i < len(modos) else "auto") or "auto"
        alias = (aliases[i].strip() or None) if i < len(aliases) else None

        # % manual (texto → Decimal fraccional). Si vacío ⇒ 0
        mk_raw = markups[i].strip() if i < len(markups) else ""
        mk_val = d(mk_raw) / d(100) if mk_raw not in ("", None) else d("0")

        # precio manual (solo se usa en MANUAL). Si vacío ⇒ None
        pm_raw = precios_manual[i].strip() if i < len(precios_manual) else ""
        pm_val = d(pm_raw) if pm_raw not in ("", None, "") else None

        # Normaliza por modo
        if modo == "auto":
            precio_manual = None
            markup_pct    = mk_val
        else:
            precio_manual = pm_val
            markup_pct    = mk_val

        if markup_pct is None:
            markup_pct = d("0")

        # UPSERT por empresa + producto
        cur.execute("""
            INSERT INTO pt_precios
              (empresa_id, mercancia_id, modo, markup_pct, precio_manual, alias)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              modo          = VALUES(modo),
              markup_pct    = VALUES(markup_pct),
              precio_manual = VALUES(precio_manual),
              alias         = VALUES(alias)
        """, (
            eid,
            mid,
            modo,
            str(markup_pct),
            str(precio_manual) if precio_manual is not None else None,
            alias
        ))

    conn.commit()
    cur.close(); conn.close()

    flash("Catálogo PT actualizado.", "success")
    return redirect(url_for("pt_catalogo"))

@app.route('/pt/nuevo', methods=['GET', 'POST'])
@require_login
def pt_nuevo():
    """Agregar nuevo Producto Terminado (PT) para la empresa activa"""
    eid = g.empresa_id
    rol = session.get('rol')

    # Solo admin puede crear PT
    if rol != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        try:
            nombre = (request.form.get('nombre') or '').strip()
            if not nombre:
                flash('⚠️ El nombre es obligatorio', 'warning')
                return redirect(url_for('pt_nuevo'))

            # Evitar duplicado en esta empresa (PT = tipo_inventario_id=3)
            cursor.execute("""
                SELECT id, nombre
                FROM mercancia
                WHERE empresa_id = %s
                  AND tipo_inventario_id = 3
                  AND UPPER(TRIM(nombre)) = UPPER(%s)
                LIMIT 1
            """, (eid, nombre))
            duplicado = cursor.fetchone()
            if duplicado:
                flash(f"⚠️ Ya existe '{duplicado['nombre']}' (ID: {duplicado['id']})", 'warning')
                return redirect(url_for('pt_nuevo'))

            # Insertar PT (ajusta columnas por tu esquema real)
            cursor.execute("""
                INSERT INTO mercancia
                  (empresa_id, nombre, tipo_inventario_id, precio, unidad_id, cont_neto, iva, ieps, activo, tipo, orden)
                VALUES
                  (%s, %s, 3, 0.00, 1, 1, 0, 0, 1, 'PT', 9999)
            """, (eid, nombre))
            mid = cursor.lastrowid

            # Inventario inicial del PT (si tu tabla inventario tiene empresa_id)
            cursor.execute("""
                INSERT IGNORE INTO inventario
                  (empresa_id, mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base)
                VALUES
                  (%s, %s, 0, 0, 0, 0, 0)
            """, (eid, mid))

            # Configuración de precio inicial (modo AUTO) por empresa
            cursor.execute("""
                INSERT INTO pt_precios
                  (empresa_id, mercancia_id, modo, markup_pct)
                VALUES
                  (%s, %s, 'auto', 0.30)
                ON DUPLICATE KEY UPDATE
                  modo = VALUES(modo),
                  markup_pct = VALUES(markup_pct)
            """, (eid, mid))

            db.commit()
            flash(f'✅ Producto "{nombre}" creado correctamente', 'success')
            return redirect(url_for('pt_catalogo'))

        except Exception as e:
            db.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')
            return redirect(url_for('pt_nuevo'))

        finally:
            try: cursor.close()
            except: pass
            try: db.close()
            except: pass

    # GET
    return render_template('inventarios/PT/pt_nuevo.html')

@app.get("/apí/inventario/<int:mercancia_id>/movimientos")
def inventario_movimientos_api(mercancia_id):
        
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, fecha, tipo_inventario_id, tipo_movimiento, unidades, precio_unitario, referencia
        FROM inventario_movimientos
        WHERE mercancia_id = %s
        ORDER BY fecha ASC, id ASC
    """, (mercancia_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)


# -------------------- Helpers de catálogo contable --------------------

def r2(x):
    return Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def tipo_from_code(code: str) -> str:
    a = int(code.split('-')[0])
    if 100 <= a < 200:
        return 'Activo'
    if 200 <= a < 300:
        return 'Pasivo'
    if 300 <= a < 400:
        return 'Patrimonio'
    if 400 <= a < 500:
        return 'Ingresos'
    # 500 y 600 los tratamos como Gastos (no hay 'Costos' en el enum)
    if 500 <= a < 700:
        return 'Gastos'
    return 'Gastos'

def naturaleza_from_tipo(tipo: str) -> str:
    # regla contable estándar
    if tipo in ('Activo', 'Gastos'):
        return 'Deudora'
    # Pasivo, Patrimonio, Ingresos
    return 'Acreedora'

def nivel_from_code(code: str) -> int:
    _, b, c = code.split('-')
    if b == '000' and c == '000':
        return 1
    if c == '000':
        return 2
    return 3

def parent_code_of(code: str) -> str | None:
    a, b, c = code.split('-')
    n = nivel_from_code(code)
    if n == 1:
        return None
    if n == 2:
        return f"{a}-000-000"
    return f"{a}-{b}-000"

def get_id_by_code(cursor, code: str) -> int | None:
    cursor.execute("SELECT id FROM cuentas_contables WHERE codigo=%s", (code,))
    row = cursor.fetchone()
    return row["id"] if row else None

def ensure_account(cursor, conn, code: str, name: str, permite_sub: bool = False, parent_override: str | None = None) -> int:
    """
    Crea o actualiza una cuenta. Asigna tipo/naturaleza/nivel/padre automáticamente.
    parent_override permite forzar el código del padre.
    Retorna id.
    """
    cursor.execute("SELECT id, nombre FROM cuentas_contables WHERE codigo=%s", (code,))
    row = cursor.fetchone()

    tipo = tipo_from_code(code)
    naturaleza = naturaleza_from_tipo(tipo)
    n = nivel_from_code(code)

    pcode = parent_code_of(code)
    if parent_override:
        pcode = parent_override
    pid = get_id_by_code(cursor, pcode) if pcode else None

    if row:
        # 🚨 No actualizar nombre si está en el bloque 600-001-001 … 600-001-026
        if code.startswith("600-001-"):
            cursor.execute(
                "UPDATE cuentas_contables "
                "SET tipo=%s, naturaleza=%s, nivel=%s, padre_id=%s, permite_subcuentas=%s "
                "WHERE id=%s",
                (tipo, naturaleza, n, pid, 1 if permite_sub else 0, row["id"])
            )
        else:
            cursor.execute(
                "UPDATE cuentas_contables "
                "SET nombre=%s, tipo=%s, naturaleza=%s, nivel=%s, padre_id=%s, permite_subcuentas=%s "
                "WHERE id=%s",
                (name, tipo, naturaleza, n, pid, 1 if permite_sub else 0, row["id"])
            )
        conn.commit()
        return row["id"]

    # Insertar por primera vez con el nombre fijo
    cursor.execute(
        "INSERT INTO cuentas_contables (codigo, nombre, tipo, naturaleza, nivel, padre_id, permite_subcuentas) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (code, name, tipo, naturaleza, n, pid, 1 if permite_sub else 0)
    )
    conn.commit()
    return cursor.lastrowid

def next_lvl3_code(cursor, parent_id: int) -> str:
    cursor.execute(
        "SELECT codigo FROM cuentas_contables WHERE id=%s", (parent_id,))
    padre = cursor.fetchone()
    if not padre:
        raise ValueError("Padre inexistente")
    a, b, _ = padre["codigo"].split('-')

    cursor.execute(
        "SELECT codigo FROM cuentas_contables WHERE padre_id=%s AND nivel=3 ORDER BY codigo DESC LIMIT 1",
        (parent_id,)
    )
    row = cursor.fetchone()
    nxt = f"{int(row['codigo'].split('-')[2]) + 1:03d}" if row else "001"
    return f"{a}-{b}-{nxt}"

def create_lvl3_account_for_product(cursor, conn, nombre_producto: str, parent_id: int) -> tuple[int, str]:
    """
    Crea (o reutiliza si ya existe con mismo nombre bajo el padre) una subcuenta nivel 3
    para el producto. Retorna (id, codigo).
    """
    # validar que el padre permita subcuentas
    cursor.execute(
        "SELECT codigo, permite_subcuentas FROM cuentas_contables WHERE id=%s", (parent_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Cuenta padre inexistente")
    if not row["permite_subcuentas"]:
        raise ValueError("La cuenta padre no permite subcuentas")

    nombre_up = nombre_producto.strip().upper()

    cursor.execute(
        "SELECT id, codigo FROM cuentas_contables WHERE nivel=3 AND padre_id=%s AND UPPER(nombre)=%s",
        (parent_id, nombre_up)
    )
    ex = cursor.fetchone()
    if ex:
        return ex["id"], ex["codigo"]

    new_code = next_lvl3_code(cursor, parent_id)
    ensure_id = ensure_account(
        cursor, conn, code=new_code, name=nombre_up, permite_sub=False)
    cursor.execute(
        "SELECT codigo FROM cuentas_contables WHERE id=%s", (ensure_id,))
    new_row = cursor.fetchone()
    return ensure_id, new_row["codigo"]

def get_default_inventory_parent(cursor, conn) -> int:
    """
    Devuelve el id de la cuenta padre (nivel 2) para crear subcuentas de productos.
    #1) Busca alguna 112-xxx-000 con permite_subcuentas=1 (p.ej. 112-001-000).
    #2) Si no existe, garantiza la cadena:
       #100-000-000 (ACTIVO, nivel 1)
       #110-000-000 (ACTIVO CIRCULANTE, nivel 1)
       #112-000-000 (INVENTARIOS, nivel 1)
       #112-001-000 (MERCANCÍAS, nivel 2, permite_subcuentas=1)
    #3) Devuelve el id de 112-001-000.
    """
    # 1) ¿Ya existe algún padre válido?
    cursor.execute("""
        SELECT id
        FROM cuentas_contables
        WHERE nivel = 2
          AND permite_subcuentas = 1
          AND codigo LIKE '112-%-000'
        ORDER BY codigo
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        return row["id"]

    # 2) Garantizar cadena mínima
    ensure_account(cursor, conn, code="100-000-000",
                   name="ACTIVO", permite_sub=False)
    ensure_account(cursor, conn, code="110-000-000",
                   name="ACTIVO CIRCULANTE", permite_sub=False)
    ensure_account(cursor, conn, code="112-000-000",
                   name="INVENTARIOS", permite_sub=False)
    ensure_account(cursor, conn, code="112-001-000", name="MERCANCÍAS",
                   permite_sub=True, parent_override="112-000-000")

    cursor.execute(
        "SELECT id FROM cuentas_contables WHERE codigo=%s", ("112-001-000",))
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(
            "No se pudo crear/obtener 112-001-000 como padre por defecto.")
    return row["id"]

import uuid

def registrar_movimiento(
    mercancia_id,
    tipo_inventario_id,
    tipo_movimiento,
    unidades,
    precio_unitario=0,
    referencia=None,
    fecha=None
):
    """Registra un movimiento de inventario CON EMPRESA"""
    from datetime import date as _date
    
    eid = getattr(g, "empresa_id", None) or session.get("empresa_id") or 1
    uid = getattr(g, "usuario_id", None) or session.get("usuario_id")

    if fecha is None:
        fecha = _date.today()

    conn = conexion_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventario_movimientos
            (empresa_id, usuario_id, tipo_inventario_id, mercancia_id,
             fecha, tipo_movimiento, unidades, precio_unitario, referencia)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (eid, uid, tipo_inventario_id, mercancia_id, fecha,
          tipo_movimiento, unidades, precio_unitario, referencia))

    conn.commit()
    cur.close()
    conn.close()

def get_or_create_catalogo(cur, conn, nombre: str, tipo: str = 'MP') -> int:
    nombre = (nombre or '').strip()
    if not nombre:
        raise ValueError("Nombre de catálogo vacío")

    # Busca sin importar mayúsculas/minúsculas
    cur.execute(
        "SELECT id FROM catalogo_inventario WHERE tipo=%s AND UPPER(nombre)=UPPER(%s) LIMIT 1",
        (tipo, nombre)
    )
    row = cur.fetchone()
    if row:
        return row['id']

    # Crea activo=1
    cur.execute(
        "INSERT INTO catalogo_inventario (nombre, tipo, activo) VALUES (%s, %s, 1)",
        (nombre, tipo)
    )
    conn.commit()
    return cur.lastrowid

def salida_peps(tipo_inventario_id: int, mercancia_id: int, unidades_salida, referencia: str):
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # Tomar primero las entradas más antiguas (PEPS)
        cursor.execute("""
            SELECT id, unidades, precio_unitario
            FROM inventario_movimientos
            WHERE tipo_inventario_id = %s
              AND mercancia_id = %s
              AND LOWER(tipo_movimiento) IN ('entrada','compra')
              AND unidades > 0
            ORDER BY fecha ASC, id ASC
        """, (tipo_inventario_id, mercancia_id))

        lotes = cursor.fetchall()
        unidades_restantes = float(unidades_salida)
        costo_total = 0.0

        for lote in lotes:
            if unidades_restantes <= 0:
                break

            disponibles = float(lote['unidades'])
            usar = min(disponibles, unidades_restantes)
            costo_total += usar * float(lote['precio_unitario'])

            # Restar del lote de entrada
            cursor.execute(
                "UPDATE inventario SET unidades = unidades - %s WHERE id = %s",
                (usar, lote['id'])
            )

            # Registrar la salida como movimiento
            registrar_movimiento(
                tipo_inventario_id=tipo_inventario_id,
                mercancia_id=mercancia_id,
                tipo_movimiento='salida',
                unidades=usar,
                precio_unitario=float(lote['precio_unitario']),
                referencia=referencia
            )

            unidades_restantes -= usar

        conn.commit()
        return costo_total

    finally:
        cursor.close()
        conn.close()
    
def _render_inventario_por_almacen(almacen_id, tipo_merc, titulo):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    # 1) map tipo → id
    tipo_map = {'MP': 1, 'WIP': 2, 'PT': 3}
    tipo_inventario_id = tipo_map.get(tipo_merc)
    if tipo_inventario_id is None:
        raise ValueError(f"tipo_merc inválido: {tipo_merc}")

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # 2) Base filtrada por tipo; filtra inventario por almacén
        cur.execute("""
            SELECT 
                COALESCE(i.id, 0)               AS id,
                m.id                             AS mercancia_id,
                m.nombre                         AS producto,
                COALESCE(i.inventario_inicial,0) AS inventario_inicial,
                COALESCE(i.entradas,0)           AS entradas,
                COALESCE(i.salidas,0)            AS salidas,
                COALESCE(i.aprobado,0)           AS aprobado
            FROM mercancia m
            LEFT JOIN inventario i 
                   ON i.mercancia_id = m.id
                  
            WHERE m.tipo_inventario_id = %s
                AND (
                        EXISTS (
                        SELECT 1 FROM movimientos_inventario mi
                        WHERE mi.producto_id = m.id        -- ✅ solo esto
                        )
                        OR i.id IS NOT NULL
                    )
            ORDER BY m.nombre ASC
        """, (tipo_inventario_id,))
        inventario_base = cur.fetchall()

        inventario_final = []
        for prod in inventario_base:
            mercancia_id = prod['mercancia_id']

            # Entradas
            cur.execute("""
                SELECT COALESCE(SUM(cantidad),0) AS total_entradas
                FROM movimientos_inventario
                WHERE producto_id = %s
                    AND UPPER(tipo) IN ('COMPRA','ENTRADA')

            """, (mercancia_id,))
            total_entradas = float(cur.fetchone()['total_entradas'] or 0)

            # Salidas #
            cur.execute("""
                SELECT COALESCE(SUM(cantidad),0) AS total_salidas
                FROM movimientos_inventario
                WHERE producto_id = %s
                    AND UPPER(tipo) = 'SALIDA'

            """, (mercancia_id,))
            total_salidas = float(cur.fetchone()['total_salidas'] or 0)

            # Disponible
            disponible = float(prod['inventario_inicial'] or 0) + total_entradas - total_salidas

            # FIFO
            cur.execute("""
                SELECT cantidad, costo_unitario
                FROM movimientos_inventario
                WHERE producto_id = %s
                  AND UPPER(tipo) IN ('COMPRA','ENTRADA')
                ORDER BY fecha ASC, id ASC

            """, (mercancia_id,))
            entradas_fifo = cur.fetchall()

            unidades_pendientes = disponible
            valor_inventario = 0.0
            for entrada in entradas_fifo:
                if unidades_pendientes <= 0:
                    break
                u = float(entrada['cantidad'] or 0)
                pu = float(entrada['costo_unitario'] or 0)
                usa = min(u, unidades_pendientes)
                valor_inventario += usa * pu
                unidades_pendientes -= usa

            inventario_final.append({
                'id': prod['id'],
                'mercancia_id': mercancia_id,
                'producto': prod['producto'],
                'inventario_inicial': prod['inventario_inicial'],
                'entradas': total_entradas,
                'salidas': total_salidas,
                'disponible': disponible,
                'valor_inventario': valor_inventario,
                'aprobado': prod['aprobado']
            })
    finally:
        cur.close(); conn.close()

    return render_template('inventarios/pt/inventario.html',
                           inventario=inventario_final,
                           titulo=titulo,
                           almacen_id=almacen_id,
                           tipo_merc=tipo_merc,
                           tipo_inventario_id=tipo_inventario_id)

def get_mp_id():
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        # 1) lee parámetro guardado
        cur.execute("SELECT valor FROM parametros WHERE clave='MP_TIPO_ID'")
        r = cur.fetchone()
        if r and r['valor']:
            return int(r['valor'])
        # 2) fallback inteligente: busca columna textual disponible
        cur.execute("""
          SELECT COLUMN_NAME
          FROM INFORMATION_SCHEMA.COLUMNS
          WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='tipos_inventario'
        """)
        cols = {c['COLUMN_NAME'].lower() for c in cur.fetchall()}
        label = None
        for c in ('nombre','descripcion','clave','codigo','titulo'):
            if c in cols:
                label = c; break
        if label:
            cur.execute(f"""
              SELECT id FROM tipos_inventario
              WHERE UPPER({label}) IN ('MATERIAS PRIMAS','MATERIA PRIMA','MP')
              LIMIT 1
            """)
            r = cur.fetchone()
            if r: return int(r['id'])
        # 3) último recurso: por mercancia.tipo
        cur.execute("""
          SELECT DISTINCT tipo_inventario_id AS id
          FROM mercancia
          WHERE UPPER(tipo) IN ('MP','MATERIA PRIMA','MATERIAS PRIMAS')
          LIMIT 1
        """)
        r = cur.fetchone()
        if r and r['id']: return int(r['id'])
        return None
    finally:
        cur.close(); conn.close()

def resolver_mercancia(cur, nombre: str | None, mid_s: str | None) -> int:
    # 1) por id
    if mid_s and str(mid_s).isdigit():
        mid = int(mid_s)
        cur.execute("SELECT id FROM mercancia WHERE id=%s", (mid,))
        if cur.fetchone():
            return mid

    # 2) exacto por nombre
    n = (nombre or "").strip()
    if not n:
        raise LookupError("Nombre de mercancía vacío")
    cur.execute("SELECT id FROM mercancia WHERE nombre=%s LIMIT 1", (n,))
    r = cur.fetchone()
    if r:
        return r["id"]

    # 3) flexible por tokens
    tokens = [t for t in n.lower().split() if t]
    patron = "%" + "%".join(tokens) + "%"
    cur.execute("""
        SELECT id FROM mercancia
        WHERE LOWER(nombre) LIKE %s
        ORDER BY LENGTH(nombre) ASC
        LIMIT 1
    """, (patron,))
    r = cur.fetchone()
    if r:
        return r["id"]

    raise LookupError(f'El producto "{n}" no está registrado')

def calcular_precio_promedio_periodo(mercancia_id, dias=60, metodo='promedio_ponderado'):
    """
    Calcula el precio promedio de una mercancía basado en compras recientes
    
    Args:
        mercancia_id: ID de la mercancía
        dias: Días hacia atrás para considerar (default: 60)
        metodo: 'promedio_ponderado', 'promedio_simple', 'ultima_compra'
    
    Returns:
        float: Precio promedio calculado
    """
    from datetime import date, timedelta
    
    conn = conexion_db()  # ✅ Ya está disponible en app.py
    cur = conn.cursor(dictionary=True)
    
    fecha_inicio = date.today() - timedelta(days=dias)
    
    try:
        if metodo == 'promedio_ponderado':
            # OPCIÓN 1: Promedio ponderado
            cur.execute("""
                SELECT 
                    COALESCE(SUM(unidades * precio_unitario), 0) as valor_total,
                    COALESCE(SUM(unidades), 0) as unidades_total
                FROM inventario_movimientos
                WHERE mercancia_id = %s
                AND tipo_movimiento IN ('compra', 'entrada')
                AND precio_unitario > 0
                AND fecha >= %s
            """, (mercancia_id, fecha_inicio))
            
            result = cur.fetchone()
            valor_total = float(result['valor_total'])
            unidades_total = float(result['unidades_total'])
            
            precio = (valor_total / unidades_total) if unidades_total > 0 else 0
        
        elif metodo == 'promedio_simple':
            # OPCIÓN 2: Promedio simple
            cur.execute("""
                SELECT AVG(precio_unitario) as precio_promedio
                FROM inventario_movimientos
                WHERE mercancia_id = %s
                AND tipo_movimiento IN ('compra', 'entrada')
                AND precio_unitario > 0
                AND fecha >= %s
            """, (mercancia_id, fecha_inicio))
            
            result = cur.fetchone()
            precio = float(result['precio_promedio']) if result['precio_promedio'] else 0
        
        elif metodo == 'ultima_compra':
            # OPCIÓN 3: Última compra
            cur.execute("""
                SELECT precio_unitario
                FROM inventario_movimientos
                WHERE mercancia_id = %s
                AND tipo_movimiento IN ('compra', 'entrada')
                AND precio_unitario > 0
                AND fecha >= %s
                ORDER BY fecha DESC, id DESC
                LIMIT 1
            """, (mercancia_id, fecha_inicio))
            
            result = cur.fetchone()
            precio = float(result['precio_unitario']) if result else 0
        
        else:
            precio = 0
        
        return precio
    
    finally:
        cur.close()
        conn.close()



ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# -------------------- Definiciones de catálogo base --------------------


# Agrupaciones entre bloques (para sumarización por niveles, si las usas luego)
AGRUPACIONES_NIVEL1 = {
    "111-000-000": "110-000-000",
    "112-000-000": "110-000-000",
    "113-000-000": "110-000-000",
    "114-000-000": "110-000-000",
    "110-000-000": "100-000-000",
    "130-000-000": "100-000-000",
    "151-000-000": "150-000-000",
    "150-000-000": "100-000-000",

    "211-000-000": "210-000-000",
    "212-000-000": "210-000-000",
    "221-000-000": "220-000-000",
    "210-000-000": "200-000-000",
    "220-000-000": "200-000-000",

    "301-000-000": "300-000-000",
    "401-000-000": "400-000-000",
    "402-000-000": "400-000-000",
    "501-000-000": "500-000-000",
    "502-000-000": "500-000-000",
}

# Base (código, nombre, permite_subcuentas)
CATALOGO_BASE = [
    ("100-000-000", "ACTIVO", False),
    ("110-000-000", "ACTIVO CIRCULANTE", False),

    ("111-000-000", "EFECTIVO Y EQUIVALENTES", False),
    ("111-001-000", "CAJA", False),
    ("111-002-000", "BANCOS", False),
    ("111-003-000", "CUENTAS DE TERCEROS", True),   # verde
    ("111-004-000", "OTROS EFECTIVOS", False),

    ("112-000-000", "INVENTARIOS", False),
    # ← padre por defecto para productos
    ("112-001-000", "MERCANCÍAS", True),
    ("112-002-000", "MATERIAS PRIMAS", True),
    ("112-003-000", "PRODUCTOS EN PROCESO", True),

    ("113-000-000", "CUENTAS POR COBRAR", False),
    ("113-001-000", "CLIENTES", True),
    ("113-002-000", "DEUDORES DIVERSOS", True),

    ("114-000-000", "OTROS ACTIVOS CIRCULANTES", False),
    ("114-001-000", "ANTICIPOS", True),
    ("114-002-000", "IMPUESTOS A FAVOR", True),

    ("130-000-000", "INVENTARIOS (ALTERNOS)", False),
    ("130-001-000", "MERCANCÍAS A", True),
    ("130-002-000", "MERCANCÍAS B", True),
    ("130-003-000", "MERCANCÍAS C", True),
    ("130-004-000", "MERCANCÍAS D", True),
    ("130-005-000", "MERCANCÍAS E", True),
    ("130-006-000", "MERCANCÍAS F", True),
    ("130-007-000", "MERCANCÍAS G", True),
    ("130-008-000", "MERCANCÍAS H", True),

    ("150-000-000", "ACTIVO NO CIRCULANTE", False),
    ("151-000-000", "ACTIVOS FIJOS", False),
    ("151-001-000", "MOBILIARIO Y EQUIPO", True),
    ("151-002-000", "EQUIPO DE CÓMPUTO", True),
    ("151-003-000", "EQUIPO DE TRANSPORTE", True),
    ("151-004-000", "OTROS ACTIVOS FIJOS", True),

    ("200-000-000", "PASIVO", False),
    ("210-000-000", "PASIVO CIRCULANTE", False),
    ("211-000-000", "PROVEEDORES Y ACREEDORES", False),
    ("211-001-000", "PROVEEDORES", True),
    ("211-002-000", "ACREEDORES", True),

    ("212-000-000", "PASIVOS ACUMULADOS", False),
    ("212-001-000", "IMPUESTOS POR PAGAR", True),
    ("212-002-000", "OTROS PASIVOS", False),

    ("220-000-000", "PASIVO A LARGO PLAZO", False),
    ("221-000-000", "CRÉDITOS DE LARGO PLAZO", False),
    ("221-001-000", "CRÉDITOS BANCARIOS", True),

    ("300-000-000", "PATRIMONIO", False),
    ("301-000-000", "CAPITAL SOCIAL Y RESULTADOS", False),
    ("301-001-000", "CAPITAL SOCIAL", False),
    ("301-002-000", "RESERVAS", False),
    ("301-003-000", "RESULTADOS ACUMULADOS", False),
    ("301-004-000", "RESULTADO DEL EJERCICIO", False),

    ("400-000-000", "INGRESOS", False),
    ("401-000-000", "INGRESOS ORDINARIOS", False),
    ("401-001-000", "VENTAS", True),
    ("402-000-000", "OTROS INGRESOS", False),
    ("402-001-000", "OTROS PRODUCTOS", True),

    ("500-000-000", "COSTOS Y CUENTAS RELACIONADAS", False),
    ("501-000-000", "COSTO DE VENTAS", False),
    ("501-001-000", "COSTO MERCANCÍAS", True),
    ("501-002-000", "OTROS COSTOS", True),
    ("502-000-000", "CLIENTES / CUENTAS RELACIONADAS", True),

    ("600-000-000", "GASTOS", True)
]

SUBS_212_002 = [f"212-002-{i:03d}" for i in range(1, 11)]
SUBS_301_003 = ["301-003-001"]
SUBS_301_004 = [f"301-004-{i:03d}" for i in range(1, 10)]



#   ADMIN     #
#    HOME  PANEL DE CONTROL    LOGIN    SIDEBAR    #



@app.route('/')
def home():
    """
    Muestra la página de inicio con accesos a los módulos principales del ERP.
    """
    return render_template('home.html')

@app.route("/panel_de_control")
@require_login
def panel_de_control():
    eid = g.empresa_id
    conn = conexion_db(); cur = conn.cursor(dictionary=True)

    # Inventario: inicial + entradas - salidas (solo de la empresa)
    cur.execute("""
        SELECT COUNT(*) AS total_items,
               COALESCE(SUM(inventario_inicial + entradas - salidas),0) AS total_stock
        FROM inventario
        WHERE empresa_id = %s
    """, (eid,))
    inventario = cur.fetchone() or {"total_items": 0, "total_stock": 0}

    # Órdenes en proceso (production debe tener empresa_id)
    cur.execute("""
        SELECT COUNT(*) AS en_proceso
        FROM orden_produccion
        WHERE empresa_id = %s
        AND estado IN ('pendiente', 'en_proceso')
    """, (eid,))
    produccion = cur.fetchone() or {"en_proceso": 0}

    # Terminados vía movimientos tipo_inventario_id=3 (filtrados por empresa)
    cur.execute("""
        SELECT
          COALESCE(
            SUM(CASE WHEN UPPER(tipo_movimiento)='ENTRADA' THEN unidades ELSE 0 END)
            - SUM(CASE WHEN UPPER(tipo_movimiento)='SALIDA'  THEN unidades ELSE 0 END), 0
          ) AS terminados
        FROM inventario_movimientos
        WHERE empresa_id = %s
          AND tipo_inventario_id = 3
    """, (eid,))
    terminados = cur.fetchone() or {"terminados": 0}

    cur.close(); conn.close()
    return render_template("panel_de_control.html",
                           inventario=inventario,
                           produccion=produccion,
                           terminados=terminados)


    if session.get('usuario_id'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '').strip()
        
        if not correo or not contrasena:
            flash('Por favor completa todos los campos.', 'danger')
            return redirect(url_for('login'))
        
        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT id, nombre, correo, contrasena, rol, empresa_id, email_confirmado
                FROM usuarios 
                WHERE correo = %s AND activo = 1
            """, (correo,))
            usuario = cursor.fetchone()
            
            if not usuario:
                flash('Correo o contraseña incorrectos.', 'danger')
                return redirect(url_for('login'))
            
            # Verificar contraseña
            if not bcrypt.checkpw(contrasena.encode('utf-8'), usuario['contrasena'].encode('utf-8')):
                flash('Correo o contraseña incorrectos.', 'danger')
                return redirect(url_for('login'))
            
            # ===== VERIFICAR EMAIL CONFIRMADO =====
            if not usuario['email_confirmado']:
                flash('⚠️ Debes confirmar tu correo antes de ingresar. Revisa tu bandeja de entrada.', 'warning')
                return redirect(url_for('login'))
            
            # Crear sesión
            session['usuario_id'] = usuario['id']
            session['empresa_id'] = usuario['empresa_id']
            session['username'] = usuario['nombre']
            session['rol'] = usuario.get('rol', 'admin')
            
            # Verificar si completó onboarding
            cursor.execute("""
                SELECT configuracion_completada 
                FROM empresa_configuracion 
                WHERE empresa_id = %s
            """, (usuario['empresa_id'],))
            config = cursor.fetchone()
            
            if not config or not config['configuracion_completada']:
                return redirect(url_for('onboarding'))
            
            flash(f'¡Bienvenido {usuario["nombre"]}!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error en login: {e}")
            flash('Error al iniciar sesión.', 'danger')
            return redirect(url_for('login'))
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/login.html')

@app.route('/panel')
def panel():
    """
    Muestra un mensaje de bienvenida y redirige según el rol.
    """
    if 'rol' not in session:
        return redirect('/login')

    if session['rol'] == 'admin':
        mensaje = 'Bienvenido al panel de administrador. Redirigiendo al panel de control...'
    elif session['rol'] == 'editor':
        mensaje = 'Bienvenido al panel de editor. Redirigiendo al corte_diario...'
    else:
        return 'Acceso no permitido.'

    return f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="2;url=/panel_de_control">
    </head>
    <body>
        <p>{mensaje}</p>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    """Cerrar sesión del usuario"""
    try:
        # Limpiar todas las variables de sesión
        session.clear()
        flash('Has cerrado sesión exitosamente.', 'success')
    except Exception as e:
        print(f"Error en logout: {e}")
    
    # Redirigir al login
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_login
def dashboard():
    """Dashboard principal con métricas en tiempo real"""
    from datetime import datetime
    
    eid = g.empresa_id
    uid = g.usuario_id
    
    # Valores por defecto
    inv_mp = {"total_items": 0, "stock": 0, "valor": 0}
    wip = {"ordenes": 0, "unidades": 0}
    pt = {"total_items": 0, "stock": 0, "valor": 0}
    ventas = {"tickets": 0, "hoy": 0, "promedio": 0}
    compras_recientes = []
    ordenes_produccion = []
    empresa_nombre = 'Sin empresa'
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # ===== MÉTRICAS INVENTARIO MP =====
        cur.execute("""
            SELECT 
                COUNT(DISTINCT m.id) as total_items,
                COALESCE(SUM(i.inventario_inicial + i.entradas - i.salidas), 0) as stock
            FROM mercancia m
            LEFT JOIN inventario i ON i.mercancia_id = m.id AND i.empresa_id = %s
            WHERE m.tipo_inventario_id = 1 
              AND m.empresa_id = %s
        """, (eid, eid))
        row = cur.fetchone()
        if row:
            inv_mp = {
                "total_items": int(row['total_items'] or 0),
                "stock": float(row['stock'] or 0),
                "valor": 0
            }
        
        # ===== MÉTRICAS WIP =====
        cur.execute("""
            SELECT 
                COUNT(*) as ordenes,
                COALESCE(SUM(cantidad), 0) as unidades
            FROM orden_produccion
            WHERE estado = 'abierta'
              AND empresa_id = %s
        """, (eid,))
        row = cur.fetchone()
        if row:
            wip = {
                "ordenes": int(row['ordenes'] or 0),
                "unidades": float(row['unidades'] or 0)
            }
        
        # ===== MÉTRICAS PT =====
        cur.execute("""
            SELECT COUNT(*) as total_items
            FROM mercancia
            WHERE tipo_inventario_id = 3
              AND empresa_id = %s
        """, (eid,))
        row = cur.fetchone()
        if row:
            pt = {
                "total_items": int(row['total_items'] or 0),
                "stock": 0,
                "valor": 0
            }
        
        # ===== MÉTRICAS VENTAS HOY =====
        cur.execute("""
            SELECT 
                COUNT(*) as tickets,
                COALESCE(SUM(total), 0) as hoy
            FROM caja_ventas
            WHERE DATE(fecha) = CURDATE()
              AND empresa_id = %s
        """, (eid,))
        row = cur.fetchone()
        if row:
            tickets = int(row['tickets'] or 0)
            hoy = float(row['hoy'] or 0)
            ventas = {
                "tickets": tickets,
                "hoy": hoy,
                "promedio": (hoy / tickets) if tickets > 0 else 0
            }
        
        # ===== ÚLTIMAS COMPRAS =====
        # ===== ÚLTIMAS COMPRAS =====
        cur.execute("""
            SELECT 
                id,
                proveedor,
                fecha,
                numero_factura,
                total
            FROM listado_compras
            WHERE empresa_id = %s
            ORDER BY fecha DESC
            LIMIT 5
        """, (eid,))
        compras_recientes = cur.fetchall()
        
        # Formatear fechas en Python
        for compra in compras_recientes:
            if compra.get('fecha'):
                compra['fecha_fmt'] = compra['fecha'].strftime('%d/%m/%Y')
            else:
                compra['fecha_fmt'] = ''
        
        # ===== ÓRDENES DE PRODUCCIÓN =====
        cur.execute("""
            SELECT 
                op.id,
                m.nombre as producto,
                op.fecha,
                op.cantidad as cantidad_programada,
                op.estado
            FROM orden_produccion op
            JOIN mercancia m ON m.id = op.pt_mercancia_id
            WHERE op.estado = 'abierta'
              AND op.empresa_id = %s
            ORDER BY op.fecha DESC
            LIMIT 5
        """, (eid,))
        ordenes_produccion = cur.fetchall()
        
        # Formatear fechas en Python
        for orden in ordenes_produccion:
            if orden.get('fecha'):
                orden['fecha_fmt'] = orden['fecha'].strftime('%d/%m/%Y')
            else:
                orden['fecha_fmt'] = ''
        
        # ===== EMPRESA =====
        cur.execute("SELECT nombre FROM empresas WHERE id = %s", (eid,))
        empresa = cur.fetchone()
        if empresa:
            empresa_nombre = empresa['nombre']
        
    except Exception as e:
        print(f"❌ Error en dashboard: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
    
    return render_template('dashboard.html',
        metricas={
            'inventario_mp': inv_mp,
            'wip': wip,
            'pt': pt,
            'ventas': ventas
        },
        compras_recientes=compras_recientes,
        ordenes_produccion=ordenes_produccion,
        empresa_nombre=empresa_nombre,
        fecha_actual=datetime.now().strftime('%d de %B, %Y'),
        hora_actual=datetime.now().strftime('%H:%M')
    )

@app.route('/admin/responsables/nuevo', methods=['GET', 'POST'])
@require_role('admin')
def nuevo_responsable():
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cur.execute("""
            INSERT INTO responsables_area (area_id, rol, jefe_directo, nombre, telefono, correo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            request.form['area_id'],
            request.form['rol'],
            request.form.get('jefe_directo'),
            request.form['nombre'],
            request.form.get('telefono'),
            request.form.get('correo')
        ))
        conn.commit()
        flash('Responsable registrado correctamente.', 'success')
        return redirect(url_for('nuevo_responsable'))

    cur.execute("SELECT id, nombre FROM areas_produccion ORDER BY nombre")
    areas = cur.fetchall()
    cur.close(); conn.close()

    return render_template('admin/responsables_form.html', areas=areas)

def inicializar_empresa_nueva(cursor, empresa_id, nombre_empresa):
    """Inicializa catálogos y datos básicos para una empresa nueva"""
    try:
        # ===== CATÁLOGO DE CUENTAS CONTABLES =====
        cuentas_basicas = [
            # (codigo, nombre, tipo, naturaleza, nivel, padre_id, permite_subcuentas)
            ('1000', 'ACTIVO', 'Activo', 'Deudora', 1, None, 1),
            ('1100', 'ACTIVO CIRCULANTE', 'Activo', 'Deudora', 2, None, 1),
            ('1101', 'Caja', 'Activo', 'Deudora', 3, None, 0),
            ('1102', 'Bancos', 'Activo', 'Deudora', 3, None, 0),
            ('1103', 'Clientes', 'Activo', 'Deudora', 3, None, 0),
            ('1104', 'Inventarios', 'Activo', 'Deudora', 3, None, 0),
            ('1200', 'ACTIVO FIJO', 'Activo', 'Deudora', 2, None, 1),
            ('1201', 'Mobiliario y Equipo', 'Activo', 'Deudora', 3, None, 0),
            ('2000', 'PASIVO', 'Pasivo', 'Acreedora', 1, None, 1),
            ('2100', 'PASIVO CIRCULANTE', 'Pasivo', 'Acreedora', 2, None, 1),
            ('2101', 'Proveedores', 'Pasivo', 'Acreedora', 3, None, 0),
            ('2102', 'Acreedores Diversos', 'Pasivo', 'Acreedora', 3, None, 0),
            ('2103', 'Impuestos por Pagar', 'Pasivo', 'Acreedora', 3, None, 0),
            ('3000', 'CAPITAL', 'Patrimonio', 'Acreedora', 1, None, 1),
            ('3101', 'Capital Social', 'Patrimonio', 'Acreedora', 2, None, 0),
            ('3102', 'Utilidades Retenidas', 'Patrimonio', 'Acreedora', 2, None, 0),
            ('3103', 'Utilidad del Ejercicio', 'Patrimonio', 'Acreedora', 2, None, 0),
            ('4000', 'INGRESOS', 'Ingresos', 'Acreedora', 1, None, 1),
            ('4101', 'Ventas', 'Ingresos', 'Acreedora', 2, None, 0),
            ('4102', 'Otros Ingresos', 'Ingresos', 'Acreedora', 2, None, 0),
            ('5000', 'COSTOS', 'Gastos', 'Deudora', 1, None, 1),
            ('5101', 'Costo de Ventas', 'Gastos', 'Deudora', 2, None, 0),
            ('5102', 'Costo de Producción', 'Gastos', 'Deudora', 2, None, 0),
            ('6000', 'GASTOS', 'Gastos', 'Deudora', 1, None, 1),
            ('6101', 'Gastos de Operación', 'Gastos', 'Deudora', 2, None, 0),
            ('6102', 'Gastos de Administración', 'Gastos', 'Deudora', 2, None, 0),
            ('6103', 'Gastos Financieros', 'Gastos', 'Deudora', 2, None, 0),
        ]
        
        for cuenta in cuentas_basicas:
            cursor.execute("""
                INSERT IGNORE INTO cuentas_contables 
                (codigo, nombre, tipo, naturaleza, nivel, padre_id, permite_subcuentas, empresa_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (cuenta[0], cuenta[1], cuenta[2], cuenta[3], cuenta[4], cuenta[5], cuenta[6], empresa_id))
        
        # ===== UNIDADES DE MEDIDA BÁSICAS =====
        unidades_basicas = ['Pieza', 'Kilogramo', 'Gramo', 'Litro', 'Mililitro', 'Metro', 'Caja', 'Paquete', 'Unidad']
        
        for unidad in unidades_basicas:
            cursor.execute("""
                INSERT IGNORE INTO unidades_medida (nombre, empresa_id)
                VALUES (%s, %s)
            """, (unidad, empresa_id))
        
        # ===== TIPOS DE INVENTARIO =====
        tipos_inventario = [
            (1, 'MP', 'Materia Prima'),
            (2, 'WIP', 'Trabajo en Proceso'),
            (3, 'PT', 'Producto Terminado'),
            (4, 'INS', 'Insumos'),
            (5, 'MER', 'Mercancía'),
        ]
        
        for tipo in tipos_inventario:
            cursor.execute("""
                INSERT IGNORE INTO tipos_inventario (id, clave, nombre, empresa_id)
                VALUES (%s, %s, %s, %s)
            """, (tipo[0], tipo[1], tipo[2], empresa_id))
        
        print(f"✅ Empresa '{nombre_empresa}' inicializada con catálogos básicos")
        return True
        
    except Exception as e:
        print(f"⚠️ Error inicializando empresa: {e}")
        import traceback
        traceback.print_exc()
        return False
        
@app.route('/admin/areas_produccion')
@require_login
@require_role('admin')
def listar_areas():
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM areas_produccion 
        WHERE empresa_id = %s 
        ORDER BY nombre
    """, (eid,))
    areas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('inventarios/WIP/areas_list.html', areas=areas)


# ==================== NUEVA ÁREA ====================
@app.route('/admin/areas_produccion/nueva', methods=['GET', 'POST'])
@require_login
@require_role('admin')
def nueva_area():
    eid = g.empresa_id
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        conn = conexion_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO areas_produccion (empresa_id, nombre, activo) 
            VALUES (%s, %s, TRUE)
        """, (eid, nombre))
        conn.commit()
        cur.close()
        conn.close()
        flash('Área registrada correctamente.', 'success')
        return redirect(url_for('listar_areas'))
    return render_template('inventarios/WIP/areas_form.html')


# ==================== EDITAR ÁREA ====================
@app.route('/admin/areas_produccion/editar/<int:id>', methods=['GET', 'POST'])
@require_login
@require_role('admin')
def editar_area(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        activo = 'activo' in request.form
        cur.execute("""
            UPDATE areas_produccion 
            SET nombre=%s, activo=%s 
            WHERE id=%s AND empresa_id=%s
        """, (nombre, activo, id, eid))
        conn.commit()
        cur.close()
        conn.close()
        flash('Área actualizada correctamente.', 'success')
        return redirect(url_for('listar_areas'))
    
    cur.execute("""
        SELECT * FROM areas_produccion 
        WHERE id=%s AND empresa_id=%s
    """, (id, eid))
    area = cur.fetchone()
    cur.close()
    conn.close()
    
    if not area:
        flash('Área no encontrada', 'warning')
        return redirect(url_for('listar_areas'))
    
    return render_template('inventarios/WIP/areas_form.html', area=area)

@app.route('/_routes')
def _routes():
    rutas = []
    for rule in app.url_map.iter_rules():
        rutas.append({
            "endpoint": rule.endpoint,
            "methods": sorted([m for m in rule.methods if m in {"GET","POST","PUT","DELETE","PATCH"}]),
            "rule": str(rule)
        })
    rutas = sorted(rutas, key=lambda x: x["rule"])
    return jsonify(rutas)


@app.route('/_debug_listado')
def _debug_listado():
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
          id,
          DATE_FORMAT(fecha, '%d/%m/%Y') AS fecha_fmt,
          numero_factura,
          proveedor,
          total
        FROM listado_compras
        ORDER BY fecha DESC, id DESC
    """)
    compras = cur.fetchall()
    cur.close(); conn.close()
    return render_template("compras/listado_compras.html", compras=compras)
    

# =============================================
# SISTEMA DE ALERTAS B2B
# Agregar a app.py
# =============================================

# =============================================
# FUNCIONES AUXILIARES DE ALERTAS
# =============================================

def crear_alerta_b2b(empresa_id, rol_destino, tipo, titulo, mensaje, referencia_tipo=None, referencia_id=None, usuario_id=None):
    """
    Crea una alerta B2B (ON)
    
    Roles: supervisor, ventas, cxc, cxp, almacen, reparto
    Tipos: orden_compra, factura, preparacion, entrega, recepcion, pago
    """
    try:
        db = conexion_db()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO alertas_b2b 
            (empresa_id, usuario_id, rol_destino, tipo, titulo, mensaje, referencia_tipo, referencia_id, activa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (empresa_id, usuario_id, rol_destino, tipo, titulo, mensaje, referencia_tipo, referencia_id))
        
        alerta_id = cursor.lastrowid
        db.commit()
        cursor.close()
        db.close()
        
        print(f"✅ ALERTA CREADA: {rol_destino} - {titulo}")
        return alerta_id
        
    except Exception as e:
        print(f"❌ Error crear alerta: {e}")
        return None


def cerrar_alerta_b2b(referencia_tipo, referencia_id, rol_destino=None, empresa_id=None):
    """
    Cierra alertas relacionadas a un documento (OFF)
    """
    try:
        db = conexion_db()
        cursor = db.cursor()
        
        sql = """
            UPDATE alertas_b2b 
            SET activa = 0, fecha_cierre = NOW()
            WHERE referencia_tipo = %s AND referencia_id = %s
        """
        params = [referencia_tipo, referencia_id]
        
        if rol_destino:
            sql += " AND rol_destino = %s"
            params.append(rol_destino)
        
        if empresa_id:
            sql += " AND empresa_id = %s"
            params.append(empresa_id)
        
        cursor.execute(sql, params)
        db.commit()
        
        filas = cursor.rowcount
        cursor.close()
        db.close()
        
        print(f"✅ ALERTAS CERRADAS: {filas} alertas para {referencia_tipo} #{referencia_id}")
        return filas
        
    except Exception as e:
        print(f"❌ Error cerrar alerta: {e}")
        return 0


def obtener_alertas_usuario(empresa_id, usuario_id):
    """
    Obtiene alertas activas para un usuario según sus roles
    """
    try:
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Obtener roles del usuario
        cursor.execute("""
            SELECT es_supervisor, es_ventas, es_cxc, es_cxp, es_almacen, es_reparto
            FROM roles_b2b_empresa
            WHERE empresa_id = %s AND usuario_id = %s AND activo = 1
        """, (empresa_id, usuario_id))
        roles = cursor.fetchone()
        
        if not roles:
            cursor.close()
            db.close()
            return []
        
        # Construir lista de roles activos
        roles_activos = []
        if roles.get('es_supervisor'): roles_activos.append('supervisor')
        if roles.get('es_ventas'): roles_activos.append('ventas')
        if roles.get('es_cxc'): roles_activos.append('cxc')
        if roles.get('es_cxp'): roles_activos.append('cxp')
        if roles.get('es_almacen'): roles_activos.append('almacen')
        if roles.get('es_reparto'): roles_activos.append('reparto')
        
        if not roles_activos:
            cursor.close()
            db.close()
            return []
        
        # Obtener alertas para esos roles
        placeholders = ','.join(['%s'] * len(roles_activos))
        cursor.execute(f"""
            SELECT a.*, 
                   TIMESTAMPDIFF(MINUTE, a.fecha_creacion, NOW()) as minutos_transcurridos
            FROM alertas_b2b a
            WHERE a.empresa_id = %s 
              AND a.activa = 1
              AND a.rol_destino IN ({placeholders})
            ORDER BY a.fecha_creacion DESC
        """, [empresa_id] + roles_activos)
        
        alertas = cursor.fetchall()
        cursor.close()
        db.close()
        
        return alertas
        
    except Exception as e:
        print(f"❌ Error obtener alertas: {e}")
        return []


def contar_alertas_activas(empresa_id, usuario_id):
    """
    Cuenta alertas activas no leídas para mostrar en badge
    """
    try:
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Obtener roles del usuario
        cursor.execute("""
            SELECT es_supervisor, es_ventas, es_cxc, es_cxp, es_almacen, es_reparto
            FROM roles_b2b_empresa
            WHERE empresa_id = %s AND usuario_id = %s AND activo = 1
        """, (empresa_id, usuario_id))
        roles = cursor.fetchone()
        
        if not roles:
            cursor.close()
            db.close()
            return 0
        
        roles_activos = []
        if roles.get('es_supervisor'): roles_activos.append('supervisor')
        if roles.get('es_ventas'): roles_activos.append('ventas')
        if roles.get('es_cxc'): roles_activos.append('cxc')
        if roles.get('es_cxp'): roles_activos.append('cxp')
        if roles.get('es_almacen'): roles_activos.append('almacen')
        if roles.get('es_reparto'): roles_activos.append('reparto')
        
        if not roles_activos:
            cursor.close()
            db.close()
            return 0
        
        placeholders = ','.join(['%s'] * len(roles_activos))
        cursor.execute(f"""
            SELECT COUNT(*) as total
            FROM alertas_b2b
            WHERE empresa_id = %s 
              AND activa = 1 
              AND leida = 0
              AND rol_destino IN ({placeholders})
        """, [empresa_id] + roles_activos)
        
        resultado = cursor.fetchone()
        cursor.close()
        db.close()
        
        return resultado['total'] if resultado else 0
        
    except Exception as e:
        print(f"❌ Error contar alertas: {e}")
        return 0


# =============================================
# INYECTAR CONTADOR DE ALERTAS EN TODAS LAS PÁGINAS
# =============================================

@app.context_processor
def inject_alertas():
    """Inyecta el contador de alertas en todas las plantillas"""
    if 'usuario_id' in session and 'empresa_id' in session:
        try:
            total = contar_alertas_activas(session['empresa_id'], session['usuario_id'])
            return {'alertas_count': total}
        except:
            return {'alertas_count': 0}
    return {'alertas_count': 0}


# =============================================
# RUTAS DE ALERTAS
# =============================================

@app.route('/alertas')
@require_login
def alertas_panel():
    """Panel de alertas del usuario"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    alertas = obtener_alertas_usuario(eid, uid)
    
    # Agrupar por tipo
    alertas_por_tipo = {}
    for a in alertas:
        tipo = a['tipo']
        if tipo not in alertas_por_tipo:
            alertas_por_tipo[tipo] = []
        alertas_por_tipo[tipo].append(a)
    
    return render_template(
        'alertas/panel.html',
        alertas=alertas,
        alertas_por_tipo=alertas_por_tipo,
        total_alertas=len(alertas)
    )


@app.route('/alertas/marcar_leida/<int:alerta_id>', methods=['POST'])
@require_login
def marcar_alerta_leida(alerta_id):
    """Marca una alerta como leída"""
    eid = g.empresa_id
    
    try:
        db = conexion_db()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE alertas_b2b 
            SET leida = 1, fecha_lectura = NOW()
            WHERE id = %s AND empresa_id = %s
        """, (alerta_id, eid))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/alertas/marcar_todas_leidas', methods=['POST'])
@require_login
def marcar_todas_leidas():
    """Marca todas las alertas como leídas"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    try:
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Obtener roles del usuario
        cursor.execute("""
            SELECT es_supervisor, es_ventas, es_cxc, es_cxp, es_almacen, es_reparto
            FROM roles_b2b_empresa
            WHERE empresa_id = %s AND usuario_id = %s AND activo = 1
        """, (eid, uid))
        roles = cursor.fetchone()
        
        if roles:
            roles_activos = []
            if roles.get('es_supervisor'): roles_activos.append('supervisor')
            if roles.get('es_ventas'): roles_activos.append('ventas')
            if roles.get('es_cxc'): roles_activos.append('cxc')
            if roles.get('es_cxp'): roles_activos.append('cxp')
            if roles.get('es_almacen'): roles_activos.append('almacen')
            if roles.get('es_reparto'): roles_activos.append('reparto')
            
            if roles_activos:
                placeholders = ','.join(['%s'] * len(roles_activos))
                cursor.execute(f"""
                    UPDATE alertas_b2b 
                    SET leida = 1, fecha_lectura = NOW()
                    WHERE empresa_id = %s 
                      AND activa = 1 
                      AND leida = 0
                      AND rol_destino IN ({placeholders})
                """, [eid] + roles_activos)
        
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Todas las alertas marcadas como leídas', 'success')
        return redirect(url_for('alertas_panel'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('alertas_panel'))


@app.route('/api/alertas/count')
@require_login
def api_alertas_count():
    """API para obtener el conteo de alertas (para actualización en tiempo real)"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    total = contar_alertas_activas(eid, uid)
    return jsonify({'count': total})


# =============================================
# CONFIGURACIÓN DE ROLES B2B
# =============================================

@app.route('/b2b/configurar_roles', methods=['GET', 'POST'])
@require_login
def configurar_roles_b2b():
    """Configurar roles B2B para usuarios de la empresa"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        usuario_id = int(request.form.get('usuario_id'))
        
        es_supervisor = 1 if request.form.get('es_supervisor') else 0
        es_ventas = 1 if request.form.get('es_ventas') else 0
        es_cxc = 1 if request.form.get('es_cxc') else 0
        es_cxp = 1 if request.form.get('es_cxp') else 0
        es_almacen = 1 if request.form.get('es_almacen') else 0
        es_reparto = 1 if request.form.get('es_reparto') else 0
        telefono = request.form.get('telefono_whatsapp', '')
        
        cursor.execute("""
            INSERT INTO roles_b2b_empresa 
            (empresa_id, usuario_id, es_supervisor, es_ventas, es_cxc, es_cxp, es_almacen, es_reparto, telefono_whatsapp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                es_supervisor = VALUES(es_supervisor),
                es_ventas = VALUES(es_ventas),
                es_cxc = VALUES(es_cxc),
                es_cxp = VALUES(es_cxp),
                es_almacen = VALUES(es_almacen),
                es_reparto = VALUES(es_reparto),
                telefono_whatsapp = VALUES(telefono_whatsapp)
        """, (eid, usuario_id, es_supervisor, es_ventas, es_cxc, es_cxp, es_almacen, es_reparto, telefono))
        
        db.commit()
        flash('✅ Roles actualizados correctamente', 'success')
        return redirect(url_for('configurar_roles_b2b'))
    
    # GET - Obtener usuarios y sus roles
    cursor.execute("""
        SELECT u.id, u.nombre, u.email,
               r.es_supervisor, r.es_ventas, r.es_cxc, r.es_cxp, r.es_almacen, r.es_reparto,
               r.telefono_whatsapp
        FROM usuarios u
        LEFT JOIN roles_b2b_empresa r ON r.usuario_id = u.id AND r.empresa_id = %s
        WHERE u.empresa_id = %s AND u.activo = 1
        ORDER BY u.nombre
    """, (eid, eid))
    usuarios = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/configurar_roles.html', usuarios=usuarios)


# =============================================
# CONFIGURAR RELACIONES COMERCIALES B2B
# =============================================

@app.route('/b2b/relaciones', methods=['GET', 'POST'])
@require_login
def relaciones_b2b():
    """Configurar qué empresas son proveedores/clientes"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'agregar':
            tipo = request.form.get('tipo')  # proveedor o cliente
            otra_empresa_id = int(request.form.get('empresa_id'))
            dias_credito = int(request.form.get('dias_credito', 0))
            
            if tipo == 'proveedor':
                # Nosotros somos el cliente
                cursor.execute("""
                    INSERT INTO relaciones_b2b (empresa_proveedor_id, empresa_cliente_id, dias_credito, fecha_inicio)
                    VALUES (%s, %s, %s, CURDATE())
                    ON DUPLICATE KEY UPDATE activa = 1, dias_credito = VALUES(dias_credito)
                """, (otra_empresa_id, eid, dias_credito))
            else:
                # Nosotros somos el proveedor
                cursor.execute("""
                    INSERT INTO relaciones_b2b (empresa_proveedor_id, empresa_cliente_id, dias_credito, fecha_inicio)
                    VALUES (%s, %s, %s, CURDATE())
                    ON DUPLICATE KEY UPDATE activa = 1, dias_credito = VALUES(dias_credito)
                """, (eid, otra_empresa_id, dias_credito))
            
            db.commit()
            flash('✅ Relación comercial agregada', 'success')
        
        elif accion == 'eliminar':
            relacion_id = int(request.form.get('relacion_id'))
            cursor.execute("UPDATE relaciones_b2b SET activa = 0 WHERE id = %s", (relacion_id,))
            db.commit()
            flash('✅ Relación desactivada', 'success')
        
        return redirect(url_for('relaciones_b2b'))
    
    # GET - Obtener relaciones actuales
    # Como proveedores (nosotros vendemos)
    cursor.execute("""
        SELECT r.*, e.nombre as cliente_nombre
        FROM relaciones_b2b r
        JOIN empresas e ON e.id = r.empresa_cliente_id
        WHERE r.empresa_proveedor_id = %s AND r.activa = 1
    """, (eid,))
    como_proveedor = cursor.fetchall()
    
    # Como clientes (nosotros compramos)
    cursor.execute("""
        SELECT r.*, e.nombre as proveedor_nombre
        FROM relaciones_b2b r
        JOIN empresas e ON e.id = r.empresa_proveedor_id
        WHERE r.empresa_cliente_id = %s AND r.activa = 1
    """, (eid,))
    como_cliente = cursor.fetchall()
    
    # Otras empresas disponibles
    cursor.execute("""
        SELECT id, nombre FROM empresas 
        WHERE id != %s AND activo = 1
        ORDER BY nombre
    """, (eid,))
    otras_empresas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/relaciones.html',
        como_proveedor=como_proveedor,
        como_cliente=como_cliente,
        otras_empresas=otras_empresas
    )

# =============================================
# ÓRDENES DE COMPRA B2B
# Agregar a app.py
# =============================================

def generar_folio_oc(empresa_id):
    """Genera folio único para orden de compra: OC-EMP-YYYYMMDD-###"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    fecha = datetime.now().strftime('%Y%m%d')
    prefijo = f"OC-{empresa_id}-{fecha}"
    
    cursor.execute("""
        SELECT COUNT(*) + 1 as siguiente
        FROM ordenes_compra_b2b 
        WHERE folio LIKE %s
    """, (f"{prefijo}%",))
    
    resultado = cursor.fetchone()
    siguiente = resultado['siguiente'] if resultado else 1
    
    cursor.close()
    db.close()
    
    return f"{prefijo}-{siguiente:03d}"


@app.route('/b2b/ordenes_compra')
@require_login
def ordenes_compra_b2b():
    """Listado de órdenes de compra (como cliente)"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Órdenes donde somos el cliente
    cursor.execute("""
        SELECT o.*, 
               ep.nombre as proveedor_nombre,
               u.nombre as solicitado_por_nombre
        FROM ordenes_compra_b2b o
        JOIN empresas ep ON ep.id = o.empresa_proveedor_id
        LEFT JOIN usuarios u ON u.id = o.solicitado_por_usuario_id
        WHERE o.empresa_cliente_id = %s
        ORDER BY o.fecha_solicitud DESC
        LIMIT 100
    """, (eid,))
    ordenes = cursor.fetchall()
    
    # Proveedores disponibles
    cursor.execute("""
        SELECT e.id, e.nombre
        FROM relaciones_b2b r
        JOIN empresas e ON e.id = r.empresa_proveedor_id
        WHERE r.empresa_cliente_id = %s AND r.activa = 1
    """, (eid,))
    proveedores = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/ordenes_compra.html',
        ordenes=ordenes,
        proveedores=proveedores
    )


@app.route('/b2b/orden_compra/nueva', methods=['GET', 'POST'])
@require_login
def nueva_orden_compra_b2b():
    """Crear nueva orden de compra manual"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        proveedor_id = int(request.form.get('proveedor_id'))
        notas = request.form.get('notas', '')
        
        # Obtener productos del formulario
        productos_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        
        if not productos_ids or not any(float(c) > 0 for c in cantidades if c):
            flash('Debe agregar al menos un producto', 'warning')
            return redirect(url_for('nueva_orden_compra_b2b'))
        
        # Crear orden
        folio = generar_folio_oc(eid)
        
        cursor.execute("""
            INSERT INTO ordenes_compra_b2b 
            (empresa_cliente_id, empresa_proveedor_id, folio, fecha_solicitud, 
             estado, solicitado_por_usuario_id, notas)
            VALUES (%s, %s, %s, NOW(), 'borrador', %s, %s)
        """, (eid, proveedor_id, folio, uid, notas))
        
        orden_id = cursor.lastrowid
        
        # Insertar detalle
        subtotal = 0
        for i, prod_id in enumerate(productos_ids):
            if not prod_id:
                continue
            cantidad = float(cantidades[i]) if cantidades[i] else 0
            if cantidad <= 0:
                continue
            
            # Obtener precio del producto
            cursor.execute("""
                SELECT nombre, precio_venta 
                FROM mercancia 
                WHERE id = %s
            """, (prod_id,))
            producto = cursor.fetchone()
            
            if producto:
                precio = float(producto['precio_venta'] or 0)
                importe = cantidad * precio
                subtotal += importe
                
                cursor.execute("""
                    INSERT INTO ordenes_compra_b2b_detalle
                    (orden_id, mercancia_id, descripcion, cantidad_solicitada, precio_unitario, importe)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (orden_id, prod_id, producto['nombre'], cantidad, precio, importe))
        
        # Actualizar totales
        iva = subtotal * 0.16
        total = subtotal + iva
        
        cursor.execute("""
            UPDATE ordenes_compra_b2b 
            SET subtotal = %s, iva = %s, total = %s
            WHERE id = %s
        """, (subtotal, iva, total, orden_id))
        
        db.commit()
        
        flash(f'✅ Orden de compra {folio} creada', 'success')
        return redirect(url_for('ver_orden_compra_b2b', orden_id=orden_id))
    
    # GET - Mostrar formulario
    # Proveedores disponibles
    cursor.execute("""
        SELECT e.id, e.nombre
        FROM relaciones_b2b r
        JOIN empresas e ON e.id = r.empresa_proveedor_id
        WHERE r.empresa_cliente_id = %s AND r.activa = 1
    """, (eid,))
    proveedores = cursor.fetchall()
    
    # Productos disponibles
    cursor.execute("""
        SELECT id, nombre, precio_venta, unidad_medida
        FROM mercancia 
        WHERE empresa_id = %s AND activo = 1
        ORDER BY nombre
    """, (eid,))
    productos = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/orden_compra_nueva.html',
        proveedores=proveedores,
        productos=productos
    )


@app.route('/b2b/orden_compra/<int:orden_id>')
@require_login
def ver_orden_compra_b2b(orden_id):
    """Ver detalle de orden de compra"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener orden
    cursor.execute("""
        SELECT o.*, 
               ec.nombre as cliente_nombre,
               ep.nombre as proveedor_nombre,
               us.nombre as solicitado_por_nombre,
               ua.nombre as aprobado_por_nombre
        FROM ordenes_compra_b2b o
        JOIN empresas ec ON ec.id = o.empresa_cliente_id
        JOIN empresas ep ON ep.id = o.empresa_proveedor_id
        LEFT JOIN usuarios us ON us.id = o.solicitado_por_usuario_id
        LEFT JOIN usuarios ua ON ua.id = o.aprobado_por_usuario_id
        WHERE o.id = %s AND (o.empresa_cliente_id = %s OR o.empresa_proveedor_id = %s)
    """, (orden_id, eid, eid))
    orden = cursor.fetchone()
    
    if not orden:
        flash('Orden no encontrada', 'danger')
        return redirect(url_for('ordenes_compra_b2b'))
    
    # Obtener detalle
    cursor.execute("""
        SELECT d.*, m.unidad_medida
        FROM ordenes_compra_b2b_detalle d
        LEFT JOIN mercancia m ON m.id = d.mercancia_id
        WHERE d.orden_id = %s
    """, (orden_id,))
    detalle = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    # Determinar si somos cliente o proveedor
    es_cliente = orden['empresa_cliente_id'] == eid
    es_proveedor = orden['empresa_proveedor_id'] == eid
    
    return render_template(
        'b2b/orden_compra_ver.html',
        orden=orden,
        detalle=detalle,
        es_cliente=es_cliente,
        es_proveedor=es_proveedor
    )


@app.route('/b2b/orden_compra/<int:orden_id>/enviar', methods=['POST'])
@require_login
def enviar_orden_compra_b2b(orden_id):
    """Enviar orden de compra al proveedor (Supervisor aprueba)"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar orden
    cursor.execute("""
        SELECT * FROM ordenes_compra_b2b 
        WHERE id = %s AND empresa_cliente_id = %s AND estado = 'borrador'
    """, (orden_id, eid))
    orden = cursor.fetchone()
    
    if not orden:
        flash('Orden no válida o ya enviada', 'warning')
        return redirect(url_for('ordenes_compra_b2b'))
    
    # Actualizar estado
    cursor.execute("""
        UPDATE ordenes_compra_b2b 
        SET estado = 'enviada', 
            aprobado_por_usuario_id = %s,
            fecha_aprobacion = NOW()
        WHERE id = %s
    """, (uid, orden_id))
    
    # Cerrar alerta del supervisor (cliente)
    cerrar_alerta_b2b('orden_compra_b2b', orden_id, 'supervisor', eid)
    
    # Crear alerta para VENTAS del proveedor
    crear_alerta_b2b(
        empresa_id=orden['empresa_proveedor_id'],
        rol_destino='ventas',
        tipo='orden_compra',
        titulo=f'Nueva Orden de Compra {orden["folio"]}',
        mensaje=f'Pedido por ${orden["total"]:.2f}',
        referencia_tipo='orden_compra_b2b',
        referencia_id=orden_id
    )
    
    db.commit()
    cursor.close()
    db.close()
    
    flash(f'✅ Orden {orden["folio"]} enviada al proveedor', 'success')
    return redirect(url_for('ver_orden_compra_b2b', orden_id=orden_id))


@app.route('/b2b/orden_compra/<int:orden_id>/cancelar', methods=['POST'])
@require_login
def cancelar_orden_compra_b2b(orden_id):
    """Cancelar orden de compra"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE ordenes_compra_b2b 
        SET estado = 'cancelada'
        WHERE id = %s AND empresa_cliente_id = %s AND estado IN ('borrador', 'enviada')
    """, (orden_id, eid))
    
    # Cerrar alertas relacionadas
    cerrar_alerta_b2b('orden_compra_b2b', orden_id)
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('Orden cancelada', 'success')
    return redirect(url_for('ordenes_compra_b2b'))


# =============================================
# PEDIDOS RECIBIDOS (Como Proveedor)
# =============================================

@app.route('/b2b/pedidos_recibidos')
@require_login
def pedidos_recibidos_b2b():
    """Listado de pedidos recibidos (como proveedor)"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Órdenes donde somos el proveedor
    cursor.execute("""
        SELECT o.*, 
               ec.nombre as cliente_nombre,
               u.nombre as solicitado_por_nombre
        FROM ordenes_compra_b2b o
        JOIN empresas ec ON ec.id = o.empresa_cliente_id
        LEFT JOIN usuarios u ON u.id = o.solicitado_por_usuario_id
        WHERE o.empresa_proveedor_id = %s AND o.estado != 'borrador'
        ORDER BY o.fecha_solicitud DESC
        LIMIT 100
    """, (eid,))
    pedidos = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/pedidos_recibidos.html', pedidos=pedidos)


@app.route('/b2b/pedido/<int:orden_id>/procesar', methods=['POST'])
@require_login
def procesar_pedido_b2b(orden_id):
    """Ventas procesa el pedido y lo envía a CxC para facturar"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar orden
    cursor.execute("""
        SELECT * FROM ordenes_compra_b2b 
        WHERE id = %s AND empresa_proveedor_id = %s AND estado = 'enviada'
    """, (orden_id, eid))
    orden = cursor.fetchone()
    
    if not orden:
        flash('Pedido no válido', 'warning')
        return redirect(url_for('pedidos_recibidos_b2b'))
    
    # Actualizar estado
    cursor.execute("""
        UPDATE ordenes_compra_b2b 
        SET estado = 'recibida'
        WHERE id = %s
    """, (orden_id,))
    
    # Cerrar alerta de VENTAS
    cerrar_alerta_b2b('orden_compra_b2b', orden_id, 'ventas', eid)
    
    # Crear alerta para CxC (emitir factura)
    crear_alerta_b2b(
        empresa_id=eid,
        rol_destino='cxc',
        tipo='factura',
        titulo=f'Emitir Factura para OC {orden["folio"]}',
        mensaje=f'Cliente solicita ${orden["total"]:.2f}',
        referencia_tipo='orden_compra_b2b',
        referencia_id=orden_id
    )
    
    db.commit()
    cursor.close()
    db.close()
    
    flash(f'✅ Pedido {orden["folio"]} procesado, enviado a Facturación', 'success')
    return redirect(url_for('pedidos_recibidos_b2b'))


# =============================================
# GENERAR OC DESDE CIERRE DE TURNO
# =============================================

def generar_orden_compra_desde_turno(turno_id, empresa_cliente_id, usuario_id, productos_faltantes):
    """
    Genera automáticamente una orden de compra al cerrar turno.
    productos_faltantes: lista de dicts [{mercancia_id, cantidad, nombre}, ...]
    """
    if not productos_faltantes:
        return None
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Buscar proveedor por defecto (primer proveedor activo)
        cursor.execute("""
            SELECT empresa_proveedor_id
            FROM relaciones_b2b
            WHERE empresa_cliente_id = %s AND activa = 1
            LIMIT 1
        """, (empresa_cliente_id,))
        relacion = cursor.fetchone()
        
        if not relacion:
            print("⚠️ No hay proveedor configurado para esta empresa")
            cursor.close()
            db.close()
            return None
        
        proveedor_id = relacion['empresa_proveedor_id']
        
        # Crear orden
        folio = generar_folio_oc(empresa_cliente_id)
        
        cursor.execute("""
            INSERT INTO ordenes_compra_b2b 
            (empresa_cliente_id, empresa_proveedor_id, turno_id, folio, fecha_solicitud, 
             estado, solicitado_por_usuario_id, notas)
            VALUES (%s, %s, %s, %s, NOW(), 'borrador', %s, %s)
        """, (empresa_cliente_id, proveedor_id, turno_id, folio, usuario_id, 
              'Generada automáticamente desde cierre de turno'))
        
        orden_id = cursor.lastrowid
        
        # Insertar productos
        subtotal = 0
        for prod in productos_faltantes:
            mercancia_id = prod.get('mercancia_id')
            cantidad = float(prod.get('cantidad', 0))
            nombre = prod.get('nombre', '')
            
            if cantidad <= 0:
                continue
            
            # Obtener precio
            cursor.execute("""
                SELECT precio_venta FROM mercancia WHERE id = %s
            """, (mercancia_id,))
            merc = cursor.fetchone()
            precio = float(merc['precio_venta']) if merc and merc['precio_venta'] else 0
            importe = cantidad * precio
            subtotal += importe
            
            cursor.execute("""
                INSERT INTO ordenes_compra_b2b_detalle
                (orden_id, mercancia_id, descripcion, cantidad_solicitada, precio_unitario, importe)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (orden_id, mercancia_id, nombre, cantidad, precio, importe))
        
        # Actualizar totales
        iva = subtotal * 0.16
        total = subtotal + iva
        
        cursor.execute("""
            UPDATE ordenes_compra_b2b 
            SET subtotal = %s, iva = %s, total = %s
            WHERE id = %s
        """, (subtotal, iva, total, orden_id))
        
        # Crear alerta para SUPERVISOR
        crear_alerta_b2b(
            empresa_id=empresa_cliente_id,
            rol_destino='supervisor',
            tipo='orden_compra',
            titulo=f'Aprobar Orden de Compra {folio}',
            mensaje=f'Generada desde cierre de turno - ${total:.2f}',
            referencia_tipo='orden_compra_b2b',
            referencia_id=orden_id
        )
        
        db.commit()
        cursor.close()
        db.close()
        
        print(f"✅ Orden de compra {folio} generada automáticamente")
        return orden_id
        
    except Exception as e:
        print(f"❌ Error generando OC: {e}")
        db.rollback()
        cursor.close()
        db.close()
        return None

# =============================================
# FACTURAS B2B - EMISIÓN Y GESTIÓN
# Agregar a app.py
# =============================================

def generar_folio_factura_b2b(empresa_id):
    """Genera folio único para factura B2B: FB-EMP-YYYYMMDD-###"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    fecha = datetime.now().strftime('%Y%m%d')
    prefijo = f"FB-{empresa_id}-{fecha}"
    
    cursor.execute("""
        SELECT COUNT(*) + 1 as siguiente
        FROM facturas_b2b 
        WHERE folio LIKE %s
    """, (f"{prefijo}%",))
    
    resultado = cursor.fetchone()
    siguiente = resultado['siguiente'] if resultado else 1
    
    cursor.close()
    db.close()
    
    return f"{prefijo}-{siguiente:03d}"


@app.route('/b2b/facturas_emitidas')
@require_login
def facturas_emitidas_b2b():
    """Listado de facturas emitidas (como proveedor)"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT f.*, 
               er.nombre as receptor_nombre,
               u.nombre as emitida_por_nombre
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        LEFT JOIN usuarios u ON u.id = f.emitida_por_usuario_id
        WHERE f.empresa_emisora_id = %s
        ORDER BY f.fecha_emision DESC
        LIMIT 100
    """, (eid,))
    facturas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/facturas_emitidas.html', facturas=facturas)


@app.route('/b2b/facturas_recibidas')
@require_login
def facturas_recibidas_b2b():
    """Listado de facturas recibidas (como cliente)"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT f.*, 
               ee.nombre as emisor_nombre,
               u.nombre as emitida_por_nombre
        FROM facturas_b2b f
        JOIN empresas ee ON ee.id = f.empresa_emisora_id
        LEFT JOIN usuarios u ON u.id = f.emitida_por_usuario_id
        WHERE f.empresa_receptora_id = %s
        ORDER BY f.fecha_emision DESC
        LIMIT 100
    """, (eid,))
    facturas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/facturas_recibidas.html', facturas=facturas)


@app.route('/b2b/emitir_factura/<int:orden_id>', methods=['GET', 'POST'])
@require_login
def emitir_factura_b2b(orden_id):
    """CxC emite factura desde orden de compra"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar orden pendiente de facturar
    cursor.execute("""
        SELECT o.*, ec.nombre as cliente_nombre
        FROM ordenes_compra_b2b o
        JOIN empresas ec ON ec.id = o.empresa_cliente_id
        WHERE o.id = %s AND o.empresa_proveedor_id = %s AND o.estado = 'recibida'
    """, (orden_id, eid))
    orden = cursor.fetchone()
    
    if not orden:
        flash('Orden no válida o ya facturada', 'warning')
        return redirect(url_for('pedidos_recibidos_b2b'))
    
    # Obtener detalle de la orden
    cursor.execute("""
        SELECT * FROM ordenes_compra_b2b_detalle WHERE orden_id = %s
    """, (orden_id,))
    detalle_orden = cursor.fetchall()
    
    if request.method == 'POST':
        # Crear factura
        folio = generar_folio_factura_b2b(eid)
        dias_credito = int(request.form.get('dias_credito', 0))
        fecha_vencimiento = datetime.now() + timedelta(days=dias_credito) if dias_credito > 0 else None
        notas = request.form.get('notas', '')
        
        cursor.execute("""
            INSERT INTO facturas_b2b 
            (empresa_emisora_id, empresa_receptora_id, orden_compra_id, folio, 
             fecha_emision, fecha_vencimiento, subtotal, iva, total,
             estado, estado_almacen, emitida_por_usuario_id, notas_recepcion)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, 'emitida', 'pendiente', %s, %s)
        """, (eid, orden['empresa_cliente_id'], orden_id, folio,
              fecha_vencimiento, orden['subtotal'], orden['iva'], orden['total'],
              uid, notas))
        
        factura_id = cursor.lastrowid
        
        # Copiar detalle de la orden a la factura
        for item in detalle_orden:
            cursor.execute("""
                INSERT INTO facturas_b2b_detalle 
                (factura_id, mercancia_id, descripcion, cantidad_facturada, 
                 precio_unitario, importe)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (factura_id, item['mercancia_id'], item['descripcion'],
                  item['cantidad_solicitada'], item['precio_unitario'], item['importe']))
            
            detalle_id = cursor.lastrowid
            
            # Crear registros de checklist para cada rol
            for rol in ['almacen_proveedor', 'reparto', 'almacen_cliente']:
                empresa_checklist = eid if rol != 'almacen_cliente' else orden['empresa_cliente_id']
                cursor.execute("""
                    INSERT INTO factura_b2b_checklist 
                    (factura_id, detalle_id, rol, empresa_id)
                    VALUES (%s, %s, %s, %s)
                """, (factura_id, detalle_id, rol, empresa_checklist))
        
        # Actualizar estado de la orden
        cursor.execute("""
            UPDATE ordenes_compra_b2b SET estado = 'facturada' WHERE id = %s
        """, (orden_id,))
        
        # Registrar tracking
        cursor.execute("""
            INSERT INTO factura_b2b_tracking 
            (factura_id, estado_nuevo, usuario_id, usuario_nombre, rol, empresa_id, accion)
            VALUES (%s, 'emitida', %s, %s, 'cxc', %s, 'Factura emitida')
        """, (factura_id, uid, g.usuario_nombre, eid))
        
        # Cerrar alerta de CxC
        cerrar_alerta_b2b('orden_compra_b2b', orden_id, 'cxc', eid)
        
        # Crear alerta para ALMACÉN (preparar mercancía)
        crear_alerta_b2b(
            empresa_id=eid,
            rol_destino='almacen',
            tipo='preparacion',
            titulo=f'Preparar Factura {folio}',
            mensaje=f'Cliente: {orden["cliente_nombre"]} - ${orden["total"]:.2f}',
            referencia_tipo='factura_b2b',
            referencia_id=factura_id
        )
        
        # Notificar al cliente (SUPERVISOR)
        crear_alerta_b2b(
            empresa_id=orden['empresa_cliente_id'],
            rol_destino='supervisor',
            tipo='factura',
            titulo=f'Factura Recibida {folio}',
            mensaje=f'Proveedor ha emitido factura por ${orden["total"]:.2f}',
            referencia_tipo='factura_b2b',
            referencia_id=factura_id
        )
        
        db.commit()
        
        flash(f'✅ Factura {folio} emitida correctamente', 'success')
        return redirect(url_for('ver_factura_b2b', factura_id=factura_id))
    
    # GET - Mostrar formulario
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/emitir_factura.html',
        orden=orden,
        detalle=detalle_orden
    )


@app.route('/b2b/factura/<int:factura_id>')
@require_login
def ver_factura_b2b(factura_id):
    """Ver detalle de factura B2B con checklist"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener factura
    cursor.execute("""
        SELECT f.*, 
               ee.nombre as emisor_nombre,
               er.nombre as receptor_nombre,
               ue.nombre as emitida_por_nombre,
               ur.nombre as recibida_por_nombre
        FROM facturas_b2b f
        JOIN empresas ee ON ee.id = f.empresa_emisora_id
        JOIN empresas er ON er.id = f.empresa_receptora_id
        LEFT JOIN usuarios ue ON ue.id = f.emitida_por_usuario_id
        LEFT JOIN usuarios ur ON ur.id = f.recibida_por_usuario_id
        WHERE f.id = %s AND (f.empresa_emisora_id = %s OR f.empresa_receptora_id = %s)
    """, (factura_id, eid, eid))
    factura = cursor.fetchone()
    
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('facturas_emitidas_b2b'))
    
    # Obtener detalle con checklist
    cursor.execute("""
        SELECT d.*, m.unidad_medida,
               c_alm.verificado as verificado_almacen,
               c_alm.usuario_nombre as verificado_almacen_por,
               c_rep.verificado as verificado_reparto,
               c_rep.usuario_nombre as verificado_reparto_por,
               c_cli.verificado as verificado_cliente,
               c_cli.usuario_nombre as verificado_cliente_por
        FROM facturas_b2b_detalle d
        LEFT JOIN mercancia m ON m.id = d.mercancia_id
        LEFT JOIN factura_b2b_checklist c_alm ON c_alm.detalle_id = d.id AND c_alm.rol = 'almacen_proveedor'
        LEFT JOIN factura_b2b_checklist c_rep ON c_rep.detalle_id = d.id AND c_rep.rol = 'reparto'
        LEFT JOIN factura_b2b_checklist c_cli ON c_cli.detalle_id = d.id AND c_cli.rol = 'almacen_cliente'
        WHERE d.factura_id = %s
    """, (factura_id,))
    detalle = cursor.fetchall()
    
    # Obtener tracking
    cursor.execute("""
        SELECT * FROM factura_b2b_tracking 
        WHERE factura_id = %s ORDER BY fecha ASC
    """, (factura_id,))
    tracking = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    # Determinar rol del usuario
    es_emisor = factura['empresa_emisora_id'] == eid
    es_receptor = factura['empresa_receptora_id'] == eid
    
    return render_template(
        'b2b/factura_ver.html',
        factura=factura,
        detalle=detalle,
        tracking=tracking,
        es_emisor=es_emisor,
        es_receptor=es_receptor
    )


@app.route('/b2b/ordenes_por_facturar')
@require_login
def ordenes_por_facturar_b2b():
    """Listado de órdenes pendientes de facturar (para CxC)"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT o.*, ec.nombre as cliente_nombre
        FROM ordenes_compra_b2b o
        JOIN empresas ec ON ec.id = o.empresa_cliente_id
        WHERE o.empresa_proveedor_id = %s AND o.estado = 'recibida'
        ORDER BY o.fecha_solicitud ASC
    """, (eid,))
    ordenes = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/ordenes_por_facturar.html', ordenes=ordenes)


# =============================================
# CUENTAS POR COBRAR
# =============================================

@app.route('/b2b/cuentas_por_cobrar')
@require_login
def cuentas_por_cobrar_b2b():
    """Listado de cuentas por cobrar (cartera)"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.*, e.nombre as cliente_nombre
        FROM cuentas_por_cobrar c
        JOIN empresas e ON e.id = c.empresa_cliente_id
        WHERE c.empresa_id = %s
        ORDER BY c.fecha_vencimiento ASC
    """, (eid,))
    cuentas = cursor.fetchall()
    
    # Totales
    cursor.execute("""
        SELECT 
            SUM(saldo) as total_saldo,
            SUM(CASE WHEN fecha_vencimiento < CURDATE() THEN saldo ELSE 0 END) as vencido
        FROM cuentas_por_cobrar
        WHERE empresa_id = %s AND estado NOT IN ('pagada', 'cancelada')
    """, (eid,))
    totales = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/cuentas_por_cobrar.html',
        cuentas=cuentas,
        totales=totales
    )


# =============================================
# CUENTAS POR PAGAR
# =============================================

@app.route('/b2b/cuentas_por_pagar')
@require_login
def cuentas_por_pagar_b2b():
    """Listado de cuentas por pagar"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.*, e.nombre as proveedor_nombre
        FROM cuentas_por_pagar c
        JOIN empresas e ON e.id = c.empresa_proveedor_id
        WHERE c.empresa_id = %s
        ORDER BY c.fecha_vencimiento ASC
    """, (eid,))
    cuentas = cursor.fetchall()
    
    # Totales
    cursor.execute("""
        SELECT 
            SUM(saldo) as total_saldo,
            SUM(CASE WHEN fecha_vencimiento < CURDATE() THEN saldo ELSE 0 END) as vencido
        FROM cuentas_por_pagar
        WHERE empresa_id = %s AND estado NOT IN ('pagada', 'cancelada')
    """, (eid,))
    totales = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/cuentas_por_pagar.html',
        cuentas=cuentas,
        totales=totales
    )


def registrar_cuenta_por_cobrar(factura_id, empresa_proveedor_id, empresa_cliente_id, total, fecha_vencimiento):
    """Registra automáticamente en CxC al confirmar entrega"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Obtener nombre del cliente
        cursor.execute("SELECT nombre FROM empresas WHERE id = %s", (empresa_cliente_id,))
        cliente = cursor.fetchone()
        
        cursor.execute("""
            INSERT INTO cuentas_por_cobrar 
            (empresa_id, factura_b2b_id, empresa_cliente_id, cliente_nombre,
             monto_original, saldo, fecha_emision, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 'pendiente')
        """, (empresa_proveedor_id, factura_id, empresa_cliente_id, 
              cliente['nombre'] if cliente else '', total, total, fecha_vencimiento))
        
        db.commit()
        cursor.close()
        db.close()
        return True
    except Exception as e:
        print(f"Error registrando CxC: {e}")
        return False


def registrar_cuenta_por_pagar(factura_id, empresa_cliente_id, empresa_proveedor_id, total, fecha_vencimiento):
    """Registra automáticamente en CxP al confirmar recepción"""
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Obtener nombre del proveedor
        cursor.execute("SELECT nombre FROM empresas WHERE id = %s", (empresa_proveedor_id,))
        proveedor = cursor.fetchone()
        
        cursor.execute("""
            INSERT INTO cuentas_por_pagar 
            (empresa_id, factura_b2b_id, empresa_proveedor_id, proveedor_nombre,
             monto_original, saldo, fecha_emision, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 'pendiente')
        """, (empresa_cliente_id, factura_id, empresa_proveedor_id,
              proveedor['nombre'] if proveedor else '', total, total, fecha_vencimiento))
        
        db.commit()
        cursor.close()
        db.close()
        return True
    except Exception as e:
        print(f"Error registrando CxP: {e}")
        return False

# =============================================
# ALMACÉN Y REPARTO B2B
# Agregar a app.py
# =============================================

@app.route('/b2b/almacen_preparacion')
@require_login
def almacen_preparacion_b2b():
    """Listado de facturas pendientes de preparar en almacén"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Facturas emitidas por nosotros pendientes de preparar
    cursor.execute("""
        SELECT f.*, er.nombre as cliente_nombre,
               (SELECT COUNT(*) FROM factura_b2b_checklist c 
                WHERE c.factura_id = f.id AND c.rol = 'almacen_proveedor' AND c.verificado = 1) as items_listos,
               (SELECT COUNT(*) FROM factura_b2b_checklist c 
                WHERE c.factura_id = f.id AND c.rol = 'almacen_proveedor') as items_total
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        WHERE f.empresa_emisora_id = %s 
          AND f.estado_almacen IN ('pendiente', 'preparando')
          AND f.estado != 'cancelada'
        ORDER BY f.fecha_emision ASC
    """, (eid,))
    facturas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/almacen_preparacion.html', facturas=facturas)


@app.route('/b2b/almacen_preparar/<int:factura_id>', methods=['GET', 'POST'])
@require_login
def almacen_preparar_factura(factura_id):
    """Pantalla de preparación con checklist"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar factura
    cursor.execute("""
        SELECT f.*, er.nombre as cliente_nombre
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        WHERE f.id = %s AND f.empresa_emisora_id = %s
    """, (factura_id, eid))
    factura = cursor.fetchone()
    
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('almacen_preparacion_b2b'))
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'verificar_item':
            checklist_id = int(request.form.get('checklist_id'))
            cantidad = float(request.form.get('cantidad', 0))
            
            cursor.execute("""
                UPDATE factura_b2b_checklist 
                SET verificado = 1, 
                    cantidad_verificada = %s,
                    usuario_id = %s,
                    usuario_nombre = %s,
                    fecha_verificacion = NOW()
                WHERE id = %s AND empresa_id = %s
            """, (cantidad, uid, g.usuario_nombre, checklist_id, eid))
            db.commit()
            
        elif accion == 'completar':
            # Verificar que todos los items estén listos
            cursor.execute("""
                SELECT COUNT(*) as pendientes
                FROM factura_b2b_checklist
                WHERE factura_id = %s AND rol = 'almacen_proveedor' AND verificado = 0
            """, (factura_id,))
            pendientes = cursor.fetchone()['pendientes']
            
            if pendientes > 0:
                flash(f'Aún hay {pendientes} artículos sin verificar', 'warning')
            else:
                # Marcar como listo
                cursor.execute("""
                    UPDATE facturas_b2b 
                    SET estado_almacen = 'listo',
                        almacen_completado_por = %s,
                        almacen_completado_fecha = NOW()
                    WHERE id = %s
                """, (uid, factura_id))
                
                # Registrar tracking
                cursor.execute("""
                    INSERT INTO factura_b2b_tracking 
                    (factura_id, estado_anterior, estado_nuevo, usuario_id, usuario_nombre, rol, empresa_id, accion)
                    VALUES (%s, 'preparando', 'listo', %s, %s, 'almacen', %s, 'Mercancía preparada')
                """, (factura_id, uid, g.usuario_nombre, eid))
                
                # Cerrar alerta de almacén
                cerrar_alerta_b2b('factura_b2b', factura_id, 'almacen', eid)
                
                # Crear alerta para REPARTO
                crear_alerta_b2b(
                    empresa_id=eid,
                    rol_destino='reparto',
                    tipo='entrega',
                    titulo=f'Recoger Factura {factura["folio"]}',
                    mensaje=f'Cliente: {factura["cliente_nombre"]} - Listo para envío',
                    referencia_tipo='factura_b2b',
                    referencia_id=factura_id
                )
                
                db.commit()
                flash('✅ Mercancía lista para reparto', 'success')
                return redirect(url_for('almacen_preparacion_b2b'))
        
        return redirect(url_for('almacen_preparar_factura', factura_id=factura_id))
    
    # GET - Obtener detalle con checklist
    cursor.execute("""
        SELECT d.*, c.id as checklist_id, c.verificado, c.cantidad_verificada, 
               c.usuario_nombre as verificado_por, c.fecha_verificacion
        FROM facturas_b2b_detalle d
        JOIN factura_b2b_checklist c ON c.detalle_id = d.id AND c.rol = 'almacen_proveedor'
        WHERE d.factura_id = %s
    """, (factura_id,))
    detalle = cursor.fetchall()
    
    # Actualizar estado a preparando si estaba pendiente
    if factura['estado_almacen'] == 'pendiente':
        cursor.execute("""
            UPDATE facturas_b2b SET estado_almacen = 'preparando' WHERE id = %s
        """, (factura_id,))
        db.commit()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/almacen_preparar.html',
        factura=factura,
        detalle=detalle
    )


# =============================================
# REPARTO
# =============================================

@app.route('/b2b/reparto')
@require_login
def reparto_b2b():
    """Listado de facturas para reparto"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Facturas listas para reparto o en camino
    cursor.execute("""
        SELECT f.*, er.nombre as cliente_nombre,
               u.nombre as repartidor_nombre
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        LEFT JOIN usuarios u ON u.id = f.reparto_asignado_a
        WHERE f.empresa_emisora_id = %s 
          AND f.estado_almacen = 'listo'
          AND f.estado_reparto IN ('pendiente', 'en_camino')
          AND f.estado != 'cancelada'
        ORDER BY f.almacen_completado_fecha ASC
    """, (eid,))
    facturas = cursor.fetchall()
    
    # Repartidores disponibles
    cursor.execute("""
        SELECT u.id, u.nombre
        FROM usuarios u
        JOIN roles_b2b_empresa r ON r.usuario_id = u.id AND r.empresa_id = %s
        WHERE r.es_reparto = 1 AND r.activo = 1
    """, (eid,))
    repartidores = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reparto.html',
        facturas=facturas,
        repartidores=repartidores
    )


@app.route('/b2b/reparto/asignar/<int:factura_id>', methods=['POST'])
@require_login
def reparto_asignar(factura_id):
    """Asignar repartidor a factura"""
    eid = g.empresa_id
    
    repartidor_id = int(request.form.get('repartidor_id'))
    
    db = conexion_db()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE facturas_b2b 
        SET reparto_asignado_a = %s
        WHERE id = %s AND empresa_emisora_id = %s
    """, (repartidor_id, factura_id, eid))
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('✅ Repartidor asignado', 'success')
    return redirect(url_for('reparto_b2b'))


@app.route('/b2b/reparto/iniciar/<int:factura_id>', methods=['POST'])
@require_login
def reparto_iniciar(factura_id):
    """Marcar factura como en camino"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar factura
    cursor.execute("""
        SELECT f.*, er.nombre as cliente_nombre
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        WHERE f.id = %s AND f.empresa_emisora_id = %s AND f.estado_almacen = 'listo'
    """, (factura_id, eid))
    factura = cursor.fetchone()
    
    if not factura:
        flash('Factura no válida', 'danger')
        return redirect(url_for('reparto_b2b'))
    
    cursor.execute("""
        UPDATE facturas_b2b 
        SET estado_reparto = 'en_camino',
            reparto_recogido_fecha = NOW()
        WHERE id = %s
    """, (factura_id,))
    
    # Registrar tracking
    cursor.execute("""
        INSERT INTO factura_b2b_tracking 
        (factura_id, estado_anterior, estado_nuevo, usuario_id, usuario_nombre, rol, empresa_id, accion)
        VALUES (%s, 'pendiente', 'en_camino', %s, %s, 'reparto', %s, 'Salió a reparto')
    """, (factura_id, uid, g.usuario_nombre, eid))
    
    # Notificar al cliente que va en camino
    crear_alerta_b2b(
        empresa_id=factura['empresa_receptora_id'],
        rol_destino='almacen',
        tipo='recepcion',
        titulo=f'Mercancía en camino - {factura["folio"]}',
        mensaje='Prepárese para recibir la entrega',
        referencia_tipo='factura_b2b',
        referencia_id=factura_id
    )
    
    db.commit()
    cursor.close()
    db.close()
    
    flash('✅ Reparto iniciado', 'success')
    return redirect(url_for('reparto_b2b'))


@app.route('/b2b/reparto/entregar/<int:factura_id>', methods=['GET', 'POST'])
@require_login
def reparto_entregar(factura_id):
    """Pantalla de entrega con checklist de reparto"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar factura
    cursor.execute("""
        SELECT f.*, er.nombre as cliente_nombre
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        WHERE f.id = %s AND f.empresa_emisora_id = %s AND f.estado_reparto = 'en_camino'
    """, (factura_id, eid))
    factura = cursor.fetchone()
    
    if not factura:
        flash('Factura no válida', 'danger')
        return redirect(url_for('reparto_b2b'))
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'verificar_item':
            checklist_id = int(request.form.get('checklist_id'))
            
            cursor.execute("""
                UPDATE factura_b2b_checklist 
                SET verificado = 1,
                    usuario_id = %s,
                    usuario_nombre = %s,
                    fecha_verificacion = NOW()
                WHERE id = %s
            """, (uid, g.usuario_nombre, checklist_id))
            db.commit()
            
        elif accion == 'completar_entrega':
            # Verificar que todos estén listos
            cursor.execute("""
                SELECT COUNT(*) as pendientes
                FROM factura_b2b_checklist
                WHERE factura_id = %s AND rol = 'reparto' AND verificado = 0
            """, (factura_id,))
            pendientes = cursor.fetchone()['pendientes']
            
            if pendientes > 0:
                flash(f'Aún hay {pendientes} artículos sin verificar', 'warning')
            else:
                # Marcar como entregado
                cursor.execute("""
                    UPDATE facturas_b2b 
                    SET estado_reparto = 'entregado',
                        reparto_entregado_fecha = NOW()
                    WHERE id = %s
                """, (factura_id,))
                
                # Registrar tracking
                cursor.execute("""
                    INSERT INTO factura_b2b_tracking 
                    (factura_id, estado_anterior, estado_nuevo, usuario_id, usuario_nombre, rol, empresa_id, accion)
                    VALUES (%s, 'en_camino', 'entregado', %s, %s, 'reparto', %s, 'Entregado al cliente')
                """, (factura_id, uid, g.usuario_nombre, eid))
                
                # Cerrar alerta de reparto
                cerrar_alerta_b2b('factura_b2b', factura_id, 'reparto', eid)
                
                db.commit()
                flash('✅ Entrega completada', 'success')
                return redirect(url_for('reparto_b2b'))
        
        return redirect(url_for('reparto_entregar', factura_id=factura_id))
    
    # GET - Obtener detalle con checklist de reparto
    cursor.execute("""
        SELECT d.*, c.id as checklist_id, c.verificado, c.usuario_nombre as verificado_por
        FROM facturas_b2b_detalle d
        JOIN factura_b2b_checklist c ON c.detalle_id = d.id AND c.rol = 'reparto'
        WHERE d.factura_id = %s
    """, (factura_id,))
    detalle = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reparto_entregar.html',
        factura=factura,
        detalle=detalle
    )


# =============================================
# RECEPCIÓN DE MERCANCÍA (Cliente)
# =============================================

@app.route('/b2b/recepcion_mercancia')
@require_login
def recepcion_mercancia_b2b():
    """Listado de facturas pendientes de recibir"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Facturas donde somos el receptor y están en camino o entregadas (pendientes de confirmar)
    cursor.execute("""
        SELECT f.*, ee.nombre as proveedor_nombre
        FROM facturas_b2b f
        JOIN empresas ee ON ee.id = f.empresa_emisora_id
        WHERE f.empresa_receptora_id = %s 
          AND f.estado_reparto IN ('en_camino', 'entregado')
          AND f.estado != 'recibida'
        ORDER BY f.reparto_entregado_fecha DESC, f.fecha_emision DESC
    """, (eid,))
    facturas = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('b2b/recepcion_mercancia.html', facturas=facturas)


@app.route('/b2b/recepcion/<int:factura_id>', methods=['GET', 'POST'])
@require_login
def recepcion_verificar(factura_id):
    """Verificar y recibir mercancía"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar factura
    cursor.execute("""
        SELECT f.*, ee.nombre as proveedor_nombre
        FROM facturas_b2b f
        JOIN empresas ee ON ee.id = f.empresa_emisora_id
        WHERE f.id = %s AND f.empresa_receptora_id = %s
    """, (factura_id, eid))
    factura = cursor.fetchone()
    
    if not factura:
        flash('Factura no encontrada', 'danger')
        return redirect(url_for('recepcion_mercancia_b2b'))
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        
        if accion == 'verificar_item':
            checklist_id = int(request.form.get('checklist_id'))
            cantidad = float(request.form.get('cantidad', 0))
            tiene_diferencia = request.form.get('tiene_diferencia') == '1'
            tipo_diferencia = request.form.get('tipo_diferencia', '')
            notas = request.form.get('notas', '')
            
            cursor.execute("""
                UPDATE factura_b2b_checklist 
                SET verificado = 1,
                    cantidad_verificada = %s,
                    tiene_diferencia = %s,
                    tipo_diferencia = %s,
                    notas = %s,
                    usuario_id = %s,
                    usuario_nombre = %s,
                    fecha_verificacion = NOW()
                WHERE id = %s AND empresa_id = %s
            """, (cantidad, 1 if tiene_diferencia else 0, tipo_diferencia, notas,
                  uid, g.usuario_nombre, checklist_id, eid))
            db.commit()
            
        elif accion == 'confirmar_recepcion':
            # Verificar que todos estén listos
            cursor.execute("""
                SELECT COUNT(*) as pendientes
                FROM factura_b2b_checklist
                WHERE factura_id = %s AND rol = 'almacen_cliente' AND verificado = 0
            """, (factura_id,))
            pendientes = cursor.fetchone()['pendientes']
            
            if pendientes > 0:
                flash(f'Aún hay {pendientes} artículos sin verificar', 'warning')
            else:
                # Verificar si hay diferencias
                cursor.execute("""
                    SELECT COUNT(*) as con_diferencias
                    FROM factura_b2b_checklist
                    WHERE factura_id = %s AND rol = 'almacen_cliente' AND tiene_diferencia = 1
                """, (factura_id,))
                diferencias = cursor.fetchone()['con_diferencias']
                
                estado_final = 'con_diferencias' if diferencias > 0 else 'recibida'
                
                # Actualizar factura
                cursor.execute("""
                    UPDATE facturas_b2b 
                    SET estado = %s,
                        estado_entrega = 'completada',
                        fecha_recepcion = NOW(),
                        recibida_por_usuario_id = %s,
                        cliente_almacen_usuario_id = %s,
                        cliente_almacen_fecha = NOW()
                    WHERE id = %s
                """, (estado_final, uid, uid, factura_id))
                
                # Registrar tracking
                cursor.execute("""
                    INSERT INTO factura_b2b_tracking 
                    (factura_id, estado_nuevo, usuario_id, usuario_nombre, rol, empresa_id, accion)
                    VALUES (%s, %s, %s, %s, 'almacen', %s, 'Mercancía recibida')
                """, (factura_id, estado_final, uid, g.usuario_nombre, eid))
                
                # Cerrar alertas del cliente
                cerrar_alerta_b2b('factura_b2b', factura_id, 'almacen', eid)
                cerrar_alerta_b2b('factura_b2b', factura_id, 'supervisor', eid)
                
                # Registrar en CxP del cliente
                registrar_cuenta_por_pagar(
                    factura_id, eid, factura['empresa_emisora_id'],
                    float(factura['total']), factura['fecha_vencimiento']
                )
                
                # Registrar en CxC del proveedor
                registrar_cuenta_por_cobrar(
                    factura_id, factura['empresa_emisora_id'], eid,
                    float(factura['total']), factura['fecha_vencimiento']
                )
                
                # Notificar al proveedor (CxC)
                crear_alerta_b2b(
                    empresa_id=factura['empresa_emisora_id'],
                    rol_destino='cxc',
                    tipo='pago',
                    titulo=f'Factura {factura["folio"]} confirmada',
                    mensaje='El cliente confirmó la recepción. Factura agregada a cartera.',
                    referencia_tipo='factura_b2b',
                    referencia_id=factura_id
                )
                
                # Notificar a CxP del cliente
                crear_alerta_b2b(
                    empresa_id=eid,
                    rol_destino='cxp',
                    tipo='pago',
                    titulo=f'Nueva cuenta por pagar - {factura["folio"]}',
                    mensaje=f'Programar pago por ${factura["total"]:.2f}',
                    referencia_tipo='factura_b2b',
                    referencia_id=factura_id
                )
                
                db.commit()
                
                if diferencias > 0:
                    flash(f'⚠️ Mercancía recibida con {diferencias} diferencias reportadas', 'warning')
                else:
                    flash('✅ Mercancía recibida correctamente', 'success')
                
                return redirect(url_for('recepcion_mercancia_b2b'))
        
        return redirect(url_for('recepcion_verificar', factura_id=factura_id))
    
    # GET - Obtener detalle con checklist del cliente
    cursor.execute("""
        SELECT d.*, c.id as checklist_id, c.verificado, c.cantidad_verificada,
               c.tiene_diferencia, c.tipo_diferencia, c.notas,
               c.usuario_nombre as verificado_por
        FROM facturas_b2b_detalle d
        JOIN factura_b2b_checklist c ON c.detalle_id = d.id AND c.rol = 'almacen_cliente'
        WHERE d.factura_id = %s
    """, (factura_id,))
    detalle = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/recepcion_verificar.html',
        factura=factura,
        detalle=detalle
    )


#  CUNETAS CONTABLES  #



@app.route('/cuenta_contable/bootstrap', methods=['POST'])
def cuentas_contables_bootstrap():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('catalogo_cuentas'))
   

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1) Base
        for code, name, ok_sub in CATALOGO_BASE:
            parent_override = AGRUPACIONES_NIVEL1.get(code)
            ensure_account(cursor, conn, code=code, name=name,
                           permite_sub=ok_sub, parent_override=parent_override)

        # 2) Subcuentas específicas
        # Diccionario con nombres fijos para las cuentas de gasto
        NOMBRES_FIJOS_600 = {
            "600-001-001": "Sueldos y Salarios",
            "600-001-002": "Horas Extras",
            "600-001-003": "Comisiones de venta",
            "600-001-004": "Renta",
            "600-001-005": "Mejoras en Imagen",
            "600-001-006": "Luz",
            "600-001-007": "Agua",
            "600-001-008": "Gas",
            "600-001-009": "Aseguranza",
            "600-001-010": "Articulos de limpieza",
            "600-001-011": "Mantenimiento de equipo",
            "600-001-012": "Suministro de oficina",
            "600-001-013": "Gasolina",
            "600-001-014": "Publicidad",
            "600-001-015": "Reclutamiento",
            "600-001-016": "Capacitación",
            "600-001-017": "Gastos de Transporte",
            "600-001-018": "Comida empleados",
            "600-001-019": "Cortesias empleados",
            "600-001-020": "Gastos Varios",
            "600-001-021": "Gastos Corporativos",
            "600-001-022": "Intereses financieros",
            "600-001-023": "Comisiones bancarias",
            "600-001-024": "ISR",
            "600-001-025": "IEPS",
            "600-001-026": "IVA"
        }

        # Generar las cuentas de gasto con nombres fijos
        for code, nombre in NOMBRES_FIJOS_600.items():
            ensure_account(cursor, conn, code=code, name=nombre, permite_sub=False)

        
        for code in SUBS_212_002:
            ensure_account(cursor, conn, code=code,
                           name=f"OTRO PASIVO {code[-3:]}", permite_sub=False)

        for code in SUBS_301_003:
            ensure_account(cursor, conn, code=code,
                           name="RESULTADOS ACUMULADOS DETALLE", permite_sub=False)

        for code in SUBS_301_004:
            ensure_account(cursor, conn, code=code,
                           name=f"RESULTADO {code[-3:]}", permite_sub=False)

        flash('Catálogo contable generado/actualizado con éxito.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al generar catálogo: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('catalogo_cuentas'))

@app.route('/catalogo_cuentas', methods=['GET'])
@require_login
def catalogo_cuentas():
    eid = g.empresa_id
    q = (request.args.get('q') or '').strip()

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # Nota: Si cuentas_contables tiene empresa_id, agregar filtro
    sql = """
        SELECT
          id, codigo, nombre, tipo, naturaleza, nivel,
          permite_subcuentas, padre_id, padre_codigo, padre_nombre, hijos
        FROM vw_cuentas_contables
        WHERE empresa_id = %s
    """
    params = [eid]
    if q:
        sql += " AND (codigo LIKE %s OR nombre LIKE %s OR padre_codigo LIKE %s OR padre_nombre LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like, like])
    sql += " ORDER BY codigo"

    cursor.execute(sql, params)
    cuentas = cursor.fetchall()
    cursor.close()
    conn.close()

    def _nivel_from_codigo(code):
        if not code:
            return None
        try:
            _, b, c = code.split('-')
        except ValueError:
            return None
        if b == '000' and c == '000':
            return 1
        if c == '000':
            return 2
        return 3

    filas = []
    for r in cuentas:
        col_cuenta = col_mayor = col_sub = col_subsub = ''
        parent_level = _nivel_from_codigo(r.get('padre_codigo'))

        if r['nivel'] == 1:
            col_cuenta = r['nombre']
        elif r['nivel'] == 2:
            if parent_level == 1 or parent_level is None:
                col_mayor = r['nombre']
            else:
                col_sub = r['nombre']
        else:
            col_subsub = r['nombre']

        filas.append({
            'id': r['id'],
            'codigo': r['codigo'],
            'cuenta': col_cuenta,
            'cuenta_mayor': col_mayor,
            'subcuenta': col_sub,
            'subsubcuenta': col_subsub
        })

    return render_template('catalogo_cuentas.html', filas=filas, q=q)

@app.route('/editar_cuenta_contable/<int:id>', methods=['GET', 'POST'])
def editar_cuenta_contable(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip().upper()
        numero_cuenta = request.form['numero_cuenta'].strip()  # viene del form
        tipo = request.form['tipo'].strip().upper()

        # Traer la cuenta actual para validar nivel/padre
        cursor.execute("""
            SELECT id, nombre, codigo AS numero_cuenta, tipo, nivel, padre_id
            FROM cuentas_contables
            WHERE id=%s
        """, (id,))
        actual = cursor.fetchone()
        if not actual:
            cursor.close()
            conn.close()
            flash('Cuenta no encontrada.', 'warning')
            return redirect(url_for('cuentas_contables'))

        # 1) Formato ###-###-###
        if not re.match(r'^\d{3}-\d{3}-\d{3}$', numero_cuenta):
            cursor.close()
            conn.close()
            flash('El número de cuenta debe tener el formato ###-###-###', 'danger')
            return redirect(url_for('editar_cuenta_contable', id=id))

        # 2) Duplicado (otro registro con el mismo codigo)
        cursor.execute("""
            SELECT 1
            FROM cuentas_contables
            WHERE codigo=%s AND id <> %s
        """, (numero_cuenta, id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash('Ese número de cuenta ya está registrado en otra cuenta.', 'warning')
            return redirect(url_for('editar_cuenta_contable', id=id))

        # 3) Validaciones por nivel/padre
        a, b, c = numero_cuenta.split('-')
        nivel = actual['nivel']
        padre_id = actual['padre_id']

        if nivel == 1:
            # Sin padre y formato AAA-000-000; tipo debe concordar con prefijo
            if padre_id is not None:
                cursor.close()
                conn.close()
                flash('Las cuentas de nivel 1 no deben tener padre.', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))
            if not (b == '000' and c == '000'):
                cursor.close()
                conn.close()
                flash('Nivel 1 debe ser AAA-000-000.', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))
            prefijo = int(a)
            esperado = 'ACTIVO' if prefijo == 100 else 'PASIVO' if prefijo == 200 else 'CAPITAL' if prefijo == 300 else None
            if esperado is None or tipo != esperado:
                cursor.close()
                conn.close()
                flash(
                    f'Para {a}-000-000 el tipo debe ser {esperado}.', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))

        else:
            # Debe tener padre, mismo tipo que el padre, y respetar patrón
            if padre_id is None:
                cursor.close()
                conn.close()
                flash('Las cuentas de nivel 2/3 requieren padre.', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))

            cursor.execute("""
                SELECT codigo AS numero_cuenta, tipo, nivel
                FROM cuentas_contables
                WHERE id=%s
            """, (padre_id,))
            padre = cursor.fetchone()
            if not padre:
                cursor.close()
                conn.close()
                flash('Padre inválido.', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))
            if padre['nivel'] != (nivel - 1):
                cursor.close()
                conn.close()
                flash(f'El padre debe ser de nivel {nivel-1}.', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))
            if tipo != padre['tipo'].upper():
                cursor.close()
                conn.close()
                flash(
                    f'El tipo debe coincidir con el del padre ({padre["tipo"]}).', 'danger')
                return redirect(url_for('editar_cuenta_contable', id=id))

            pa, pb, pc = padre['numero_cuenta'].split('-')
            if nivel == 2:
                # AAA-BBB-000 con AAA del padre y BBB != 000
                if not (a == pa and b != '000' and c == '000'):
                    cursor.close()
                    conn.close()
                    flash('Nivel 2: AAA-BBB-000 y AAA igual al padre.', 'danger')
                    return redirect(url_for('editar_cuenta_contable', id=id))
            if nivel == 3:
                # AAA-BBB-CCC con AAA-BBB del padre y CCC != 000
                if not (a == pa and b == pb and c != '000'):
                    cursor.close()
                    conn.close()
                    flash('Nivel 3: AAA-BBB-CCC y AAA-BBB igual al padre.', 'danger')
                    return redirect(url_for('editar_cuenta_contable', id=id))

        # 4) Actualizar (usa columna 'codigo', sin espacios en %s)
        try:
            cursor.execute("""
                UPDATE cuentas_contables
                SET nombre=%s, codigo=%s, tipo=%s
                WHERE id=%s
            """, (nombre, numero_cuenta, tipo, id))
            conn.commit()
            flash('Cuenta contable actualizada con éxito', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar la cuenta: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('cuentas_contables'))

    # GET: mostrar datos existentes (alias para que el template siga usando numero_cuenta)
    cursor.execute("""
        SELECT id, nombre, codigo AS numero_cuenta, tipo, nivel, padre_id
        FROM cuentas_contables
        WHERE id=%s
    """, (id,))
    cuenta = cursor.fetchone()
    cursor.close()
    conn.close()

    if not cuenta:
        flash('Cuenta no encontrada.', 'warning')
        return redirect(url_for('cuentas_contables'))

    return render_template('editar_cuenta_contable.html', cuenta=cuenta)

@app.route('/subcuentas_contables', methods=['GET', 'POST'])
def subcuentas_contables():
    """
    Crea subcuentas(nivel 2 o 3) dentro de la misma tabla 'cuentas_contables',
    enlazadas a su cuenta padre vía 'padre_id'.
    """
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':


        nombre = request.form['nombre'].strip().upper()
        numero_cuenta = request.form['numero_cuenta'].strip()
        tipo = request.form['tipo'].strip().upper()
        nivel = int(request.form['nivel'])           # debe ser 2 o 3
        padre_id_raw = request.form.get('padre_id')
        padre_id = int(padre_id_raw) if padre_id_raw else None

        # Validaciones básicas
        if nivel not in (2, 3):
            cursor.close()
            conn.close()
            flash('Solo se pueden crear subcuentas de nivel 2 o 3.', 'danger')
            return redirect(url_for('subcuentas_contables'))

        if not re.match(r'^\d{3}-\d{3}-\d{3}$', numero_cuenta):
            cursor.close()
            conn.close()
            flash('El número de cuenta debe tener el formato ###-###-###.', 'danger')
            return redirect(url_for('subcuentas_contables'))

        # Duplicado por 'codigo'
        cursor.execute(
            "SELECT 1 FROM cuentas_contables WHERE codigo=%s", (numero_cuenta,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash('Ese número de cuenta ya existe.', 'warning')
            return redirect(url_for('subcuentas_contables'))

        # Padre requerido y coherente
        if padre_id is None:
            cursor.close()
            conn.close()
            flash('Debes seleccionar una cuenta padre.', 'danger')
            return redirect(url_for('subcuentas_contables'))

        cursor.execute("""
            SELECT id, codigo AS numero_cuenta, tipo, nivel
            FROM cuentas_contables
            WHERE id=%s
        """, (padre_id,))
        padre = cursor.fetchone()
        if not padre:
            cursor.close()
            conn.close()
            flash('Cuenta padre inválida.', 'danger')
            return redirect(url_for('subcuentas_contables'))

        if padre['nivel'] != (nivel - 1):
            cursor.close()
            conn.close()
            flash(f'El padre debe ser de nivel {nivel - 1}.', 'danger')
            return redirect(url_for('subcuentas_contables'))

        if tipo != padre['tipo'].upper():
            cursor.close()
            conn.close()
            flash(
                f'El tipo debe coincidir con el del padre ({padre["tipo"]}).', 'danger')
            return redirect(url_for('subcuentas_contables'))

        # Validar patrón AAA-BBB-000 (nivel 2) o AAA-BBB-CCC (nivel 3)
        a, b, c = _split_code(numero_cuenta)
        pa, pb, pc = _split_code(padre['numero_cuenta'])

        if nivel == 2:
            if not (a == pa and b != '000' and c == '000'):
                cursor.close()
                conn.close()
                flash(
                    'Nivel 2: debe ser AAA-BBB-000 y AAA igual al del padre.', 'danger')
                return redirect(url_for('subcuentas_contables'))

        if nivel == 3:
            if not (a == pa and b == pb and c != '000'):
                cursor.close()
                conn.close()
                flash(
                    'Nivel 3: debe ser AAA-BBB-CCC y AAA-BBB igual al del padre.', 'danger')
                return redirect(url_for('subcuentas_contables'))

        # Insertar subcuenta
        try:
            cursor.execute("""
                INSERT INTO cuentas_contables(nombre, codigo, tipo, nivel, padre_id)
                VALUES ( %s, %s, %s, %s, %s)
            """, (nombre, numero_cuenta, tipo, nivel, padre_id))
            conn.commit()
            flash('Subcuenta creada con éxito.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error al crear la subcuenta: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('subcuentas_contables'))

    # GET: listar subcuentas y ofrecer padres válidos
    cursor.execute("""
        SELECT id, nombre, codigo AS numero_cuenta, tipo, nivel
        FROM cuentas_contables
        WHERE nivel IN (2, 3)
        ORDER BY codigo
    """)
    subcuentas = cursor.fetchall()

    cursor.execute("""
        SELECT id, nombre, codigo AS numero_cuenta, tipo, nivel
        FROM cuentas_contables
        WHERE nivel IN(1, 2)
        ORDER BY codigo
    """)
    cuentas = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('subcuentas_contables.html', subcuentas=subcuentas, cuentas=cuentas)

@app.route('/unidades_medida', methods=['GET', 'POST'])
@require_login
def unidades_medida():
    eid = g.empresa_id
    
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        if not nombre:
            flash('Nombre requerido.', 'warning')
            return redirect(url_for('unidades_medida'))

        conn = conexion_db()
        cursor = conn.cursor()
        try:
            # Unidades de medida son globales, pero validamos duplicado
            cursor.execute("""
                SELECT 1 FROM unidades_medida 
                WHERE UPPER(nombre)=UPPER(%s)
            """, (nombre,))
            if cursor.fetchone():
                flash('La unidad ya existe.', 'warning')
                return redirect(url_for('unidades_medida'))

            cursor.execute("INSERT INTO unidades_medida (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            flash('Unidad registrada con éxito', 'success')
            return redirect(url_for('unidades_medida'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('unidades_medida'))
        finally:
            cursor.close()
            conn.close()

    # GET
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM unidades_medida ORDER BY nombre")
    unidades = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('unidades_medida.html', unidades=unidades)

@app.route('/unidades_medida/<int:id>/editar', methods=['POST'])
@require_login
def editar_unidad(id):
    """Editar unidad de medida"""
    eid = g.empresa_id
    nombre = request.form.get('nombre', '').strip()
    
    if not nombre:
        flash('El nombre es requerido', 'warning')
        return redirect(url_for('unidades_medida'))
    
    conn = conexion_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE unidades_medida 
            SET nombre = %s 
            WHERE id = %s AND empresa_id = %s
        """, (nombre, id, eid))
        conn.commit()
        flash('Unidad actualizada correctamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('unidades_medida'))

@app.route('/unidades_medida/<int:id>/eliminar', methods=['POST'])
@require_login
def eliminar_unidad(id):
    """Eliminar unidad de medida"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT COUNT(*) as total FROM mercancia 
            WHERE unidad_id = %s AND empresa_id = %s
        """, (id, eid))
        resultado = cur.fetchone()
        en_uso = resultado['total'] if resultado else 0
        
        if en_uso > 0:
            flash(f'No se puede eliminar: la unidad está en uso por {en_uso} producto(s)', 'warning')
        else:
            cur.execute("""
                DELETE FROM unidades_medida 
                WHERE id = %s AND empresa_id = %s
            """, (id, eid))
            conn.commit()
            flash('Unidad eliminada correctamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('unidades_medida'))

def _split_code(code: str):
    a, b, c = code.split('-')
    return a, b, c





#       INVENTARIOS      MP        #





@app.route('/admin/ubicaciones/config', methods=['GET', 'POST'])
@require_login
def ubicaciones_config():
    """Configurar niveles de ubicación por empresa (multiempresa)"""
    
    # Solo admin
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')
    
    # Empresa actual
    empresa_id = getattr(g, 'empresa_id', None) or session.get('empresa_id') or 1
    
    # ----- POST: guardar configuración -----
    if request.method == 'POST':
        db = conexion_db()
        cursor = db.cursor()
        try:
            for nivel in range(1, 5):
                activo = 1 if request.form.get(f'activo_{nivel}') == 'on' else 0
                nombre = (request.form.get(f'nombre_{nivel}') or '').strip()
                
                cursor.execute("""
                    UPDATE ubicaciones_config 
                    SET activo = %s, nombre_personalizado = %s
                    WHERE empresa_id = %s AND nivel = %s
                """, (activo, nombre, empresa_id, nivel))
            
            db.commit()
            flash('✅ Configuración guardada correctamente', 'success')
            return redirect(url_for('ubicaciones_config'))
        
        except Exception as e:
            db.rollback()
            flash(f'❌ Error: {str(e)}', 'danger')
            return redirect(url_for('ubicaciones_config'))
        
        finally:
            cursor.close()
            db.close()
    
    # ----- GET: mostrar configuración actual -----
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT nivel, activo, nombre_nivel, nombre_personalizado
            FROM ubicaciones_config
            WHERE empresa_id = %s
            ORDER BY nivel
        """, (empresa_id,))
        niveles = cursor.fetchall()
    finally:
        cursor.close()
        db.close()
    
    return render_template('inventarios/MP/ubicaciones_config.html', niveles=niveles)  # ✅ CAMBIO AQUÍ

@app.after_request
def no_cache(r):
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@app.route('/inventario/mp')
def inventario_mp_view():
    inventario = _inventario_por_tipo(1)   # MP
    return render_template('inventarios/mp/inventario.html',
                           inventario=inventario)

def _inventario_por_tipo(tipo_inventario_id: int):
    """Inventario filtrado por tipo Y por empresa"""
    eid = getattr(g, 'empresa_id', None) or session.get('empresa_id') or 1
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
                pb.id AS id,
                pb.nombre AS producto,
                COALESCE(SUM(i.inventario_inicial),0) AS inventario_inicial,
                COALESCE(SUM(i.entradas),0) AS entradas,
                COALESCE(SUM(i.salidas),0) AS salidas,
                COALESCE(SUM(i.inventario_inicial+i.entradas-i.salidas),0) AS disponible,
                NULL AS valor_inventario,
                MAX(i.aprobado) AS aprobado,
                MIN(m.id) AS mercancia_id
            FROM producto_base pb
            JOIN mercancia m ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id = m.id
            WHERE pb.activo = 1
              AND m.tipo_inventario_id = %s
              AND m.empresa_id = %s
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre ASC
        """, (tipo_inventario_id, eid))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

@app.route('/inventario')
@require_login
def mostrar_inventario():
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
                pb.id AS id,
                pb.nombre AS producto,
                COALESCE(SUM(i.inventario_inicial), 0) AS inventario_inicial,
                COALESCE(SUM(i.entradas), 0) AS entradas,
                COALESCE(SUM(i.salidas), 0) AS salidas,
                COALESCE(SUM(i.inventario_inicial + i.entradas - i.salidas), 0) AS disponible,
                NULL AS valor_inventario,
                MAX(i.aprobado) AS aprobado,
                MIN(m.id) AS mercancia_id
            FROM producto_base pb
            JOIN mercancia m ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id = m.id
            WHERE pb.activo = 1 AND m.empresa_id = %s
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre ASC
        """, (eid,))
        inventario = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template('inventarios/pt/inventario.html', inventario=inventario)


@app.route('/inventarios/movimientos/<int:mercancia_id>')
def inventario_movimientos(mercancia_id):
    # ... checks ...

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 1) nombre
    cursor.execute("SELECT nombre FROM mercancia WHERE id=%s", (mercancia_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        flash('Mercancía no encontrada.', 'warning')
        return redirect(url_for('mostrar_inventario_mp'))
    producto = row['nombre']

    almacen_s = (request.args.get('almacen') or '').strip()
    almacen_id = int(almacen_s) if almacen_s.isdigit() else None

    # 2) query por almacén
    if almacen_id == 1:
        sql = """
        SELECT * FROM (
            SELECT lc.fecha AS fecha_raw, DATE_FORMAT(lc.fecha,'%d/%b/%y') AS fecha_fmt,
                   lc.numero_factura AS documento, lc.proveedor AS fuente,
                   dc.unidades, dc.contenido_neto_total,
                   CASE WHEN dc.contenido_neto_total>0
                        THEN dc.precio_total/dc.contenido_neto_total ELSE NULL END AS precio_unitario,
                   dc.precio_total AS importe, dc.producto AS detalle, dc.compra_id,
                   'compra' AS tipo_movimiento
            FROM detalle_compra dc
            JOIN listado_compras lc ON dc.compra_id = lc.id
            WHERE dc.mercancia_id = %s
            UNION ALL
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%y') AS fecha_fmt,
                im.referencia AS documento, '' AS fuente, im.unidades,
                NULL AS contenido_neto_total, im.precio_unitario,
                (im.unidades*im.precio_unitario) AS importe,
                NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id = %s 
            AND im.tipo_inventario_id = 1
            AND UPPER(im.tipo_movimiento) <> 'COMPRA'
            AND im.unidades > 0
            AND im.tipo_movimiento IS NOT NULL
            AND im.tipo_movimiento <> ''
        ) t
        ORDER BY t.fecha_raw ASC, t.documento ASC
        """
        cursor.execute(sql, (mercancia_id, mercancia_id))
        movimientos = cursor.fetchall()

    elif almacen_id in (2, 3):
        cursor.execute("""
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%y') AS fecha_fmt,
                   im.referencia AS documento, '' AS fuente, im.unidades,
                   NULL AS contenido_neto_total, im.precio_unitario,
                   (im.unidades*im.precio_unitario) AS importe, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id = %s AND im.tipo_inventario_id = %s
            ORDER BY im.fecha ASC, im.id ASC
        """, (mercancia_id, almacen_id))
        movimientos = cursor.fetchall()

    else:
        sql = """
        SELECT * FROM (
            SELECT lc.fecha AS fecha_raw, DATE_FORMAT(lc.fecha,'%d/%b/%y') AS fecha_fmt,
                   lc.numero_factura AS documento, lc.proveedor AS fuente,
                   dc.unidades, dc.contenido_neto_total,
                   CASE WHEN dc.contenido_neto_total>0
                        THEN dc.precio_total/dc.contenido_neto_total ELSE NULL END AS precio_unitario,
                   dc.precio_total AS importe, dc.producto AS detalle, dc.compra_id,
                   'compra' AS tipo_movimiento
            FROM detalle_compra dc
            JOIN listado_compras lc ON dc.compra_id = lc.id
            WHERE dc.mercancia_id = %s
            UNION ALL
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%y') AS fecha_fmt,
                   im.referencia AS documento, '' AS fuente, im.unidades,
                   NULL AS contenido_neto_total, im.precio_unitario,
                   (im.unidades*im.precio_unitario) AS importe,
                   NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id = %s
              AND UPPER(im.tipo_movimiento) <> 'COMPRA'
        ) t
        ORDER BY t.fecha_raw ASC, t.documento ASC
        """
        cursor.execute(sql, (mercancia_id, mercancia_id))
        movimientos = cursor.fetchall()

    # 3) construir tablas
    rows = []
    saldo_u = 0.0
    saldo_mx = 0.0
    for m in movimientos:
        tipo = (m.get('tipo_movimiento') or '').strip().lower()
        es_entrada = tipo in ('entrada','compra')
        contenido = m.get('contenido_neto_total')
        entrada_u = float(contenido) if (es_entrada and contenido and float(contenido)>0) else (float(m.get('unidades') or 0.0) if es_entrada else 0.0)
        salida_u  = float(m.get('unidades') or 0.0) if tipo == 'salida' else 0.0
        entrada_mx = float(m.get('importe') or 0.0) if es_entrada else 0.0
        salida_mx  = float(m.get('importe') or 0.0) if tipo == 'salida' else 0.0
        saldo_u  += entrada_u - salida_u
        saldo_mx += entrada_mx - salida_mx
        if es_entrada and entrada_u>0:
            pu = entrada_mx/entrada_u
        elif tipo=='salida':
            pu = float(m.get('precio_unitario') or 0.0)
        else:
            pu = 0.0
        rows.append({
            "fecha": m.get("fecha_fmt"),
            "documento": m.get("documento"),
            "fuente": m.get("fuente"),
            "entrada_u": entrada_u, "salida_u": salida_u, "saldo_u": saldo_u,
            "entrada_mx": entrada_mx, "salida_mx": salida_mx, "saldo_mx": saldo_mx,
            "pu": pu,
        })

    tabla_unidades = [{"fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
                       "entrada": r["entrada_u"], "salida": r["salida_u"], "saldo": r["saldo_u"]} for r in rows]
    tabla_pesos    = [{"fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
                       "entrada": r["entrada_mx"], "salida": r["salida_mx"], "saldo": r["saldo_mx"], "pu": r["pu"]} for r in rows]

    # ✅ CALCULAR TOTALES
    total_entradas_u = sum(r["entrada_u"] for r in rows)
    total_salidas_u = sum(r["salida_u"] for r in rows)
    total_entradas_mx = sum(r["entrada_mx"] for r in rows)
    total_salidas_mx = sum(r["salida_mx"] for r in rows)
    
    saldo_final_u = rows[-1]["saldo_u"] if rows else 0.0
    saldo_final_mx = rows[-1]["saldo_mx"] if rows else 0.0
    pu_final = rows[-1]["pu"] if rows else 0.0

    cursor.close()
    conn.close()

    return render_template('inventarios/inventario_movimientos.html',
                           producto=producto,
                           tabla_unidades=tabla_unidades,
                           tabla_pesos=tabla_pesos,
                           total_entradas_u=total_entradas_u,
                           total_salidas_u=total_salidas_u,
                           saldo_final_u=saldo_final_u,
                           total_entradas_mx=total_entradas_mx,
                           total_salidas_mx=total_salidas_mx,
                           saldo_final_mx=saldo_final_mx,
                           pu_final=pu_final,
                           back_endpoint='mostrar_inventario_mp')


@app.route('/inventarios/movimientos-producto-base/<int:producto_base_id>')
@require_login
def inventario_movimientos_producto_base(producto_base_id):
    """Movimientos agrupados por producto base (filtrado por empresa)"""
    eid = g.empresa_id  # ✅ Empresa activa
    
    if 'rol' not in session:
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 1) Obtener nombre del producto base y mercancías (FILTRADO)
    cursor.execute("""
        SELECT pb.nombre as producto_base_nombre,
               GROUP_CONCAT(m.id) as mercancia_ids,
               GROUP_CONCAT(m.nombre SEPARATOR ', ') as mercancias_nombres
        FROM producto_base pb
        LEFT JOIN mercancia m ON m.producto_base_id = pb.id AND m.empresa_id = %s
        WHERE pb.id = %s
        GROUP BY pb.id, pb.nombre
    """, (eid, producto_base_id))
    
    row = cursor.fetchone()
    if not row or not row['mercancia_ids']:
        cursor.close()
        conn.close()
        flash('Producto base no encontrado o sin mercancías asociadas.', 'warning')
        return redirect(url_for('mostrar_inventario_mp'))
    
    producto = row['producto_base_nombre']
    mercancia_ids = [int(x) for x in row['mercancia_ids'].split(',')]
    
    almacen_s = (request.args.get('almacen') or '').strip()
    almacen_id = int(almacen_s) if almacen_s.isdigit() else None

    # 2) Query FILTRADO POR EMPRESA
    if almacen_id == 1:
        placeholders = ','.join(['%s'] * len(mercancia_ids))
        sql = f"""
        SELECT * FROM (
            SELECT lc.fecha AS fecha_raw, DATE_FORMAT(lc.fecha,'%d/%b/%Y') AS fecha_fmt,
                   lc.numero_factura AS documento, lc.proveedor AS fuente,
                   dc.unidades, dc.contenido_neto_total,
                   CASE WHEN dc.contenido_neto_total>0
                        THEN dc.precio_total/dc.contenido_neto_total ELSE NULL END AS precio_unitario,
                   dc.precio_total AS importe, dc.producto AS detalle, dc.compra_id,
                   'compra' AS tipo_movimiento
            FROM detalle_compra dc
            JOIN listado_compras lc ON dc.compra_id = lc.id
            WHERE dc.mercancia_id IN ({placeholders})
              AND dc.empresa_id = %s
              AND lc.empresa_id = %s
            UNION ALL
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                im.referencia AS documento, '' AS fuente, im.unidades,
                NULL AS contenido_neto_total, im.precio_unitario,
                (im.unidades*im.precio_unitario) AS importe,
                NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders})
            AND im.tipo_inventario_id = 1
            AND im.empresa_id = %s
            AND UPPER(im.tipo_movimiento) <> 'COMPRA'
            AND im.unidades > 0
            AND im.tipo_movimiento IS NOT NULL
            AND im.tipo_movimiento <> ''
        ) t
        ORDER BY t.fecha_raw ASC, t.documento ASC
        """
        cursor.execute(sql, mercancia_ids + [eid, eid] + mercancia_ids + [eid])
        movimientos = cursor.fetchall()

    elif almacen_id in (2, 3):
        placeholders = ','.join(['%s'] * len(mercancia_ids))
        cursor.execute(f"""
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                   im.referencia AS documento, '' AS fuente, im.unidades,
                   NULL AS contenido_neto_total, im.precio_unitario,
                   (im.unidades*im.precio_unitario) AS importe, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders}) 
              AND im.tipo_inventario_id = %s
              AND im.empresa_id = %s
            ORDER BY im.fecha ASC, im.id ASC
        """, mercancia_ids + [almacen_id, eid])
        movimientos = cursor.fetchall()

    else:
        placeholders = ','.join(['%s'] * len(mercancia_ids))
        sql = f"""
        SELECT * FROM (
            SELECT lc.fecha AS fecha_raw, DATE_FORMAT(lc.fecha,'%d/%b/%Y') AS fecha_fmt,
                   lc.numero_factura AS documento, lc.proveedor AS fuente,
                   dc.unidades, dc.contenido_neto_total,
                   CASE WHEN dc.contenido_neto_total>0
                        THEN dc.precio_total/dc.contenido_neto_total ELSE NULL END AS precio_unitario,
                   dc.precio_total AS importe, dc.producto AS detalle, dc.compra_id,
                   'compra' AS tipo_movimiento
            FROM detalle_compra dc
            JOIN listado_compras lc ON dc.compra_id = lc.id
            WHERE dc.mercancia_id IN ({placeholders})
              AND dc.empresa_id = %s
              AND lc.empresa_id = %s
            UNION ALL
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                   im.referencia AS documento, '' AS fuente, im.unidades,
                   NULL AS contenido_neto_total, im.precio_unitario,
                   (im.unidades*im.precio_unitario) AS importe,
                   NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders})
              AND im.empresa_id = %s
              AND UPPER(im.tipo_movimiento) <> 'COMPRA'
        ) t
        ORDER BY t.fecha_raw ASC, t.documento ASC
        """
        cursor.execute(sql, mercancia_ids + [eid, eid] + mercancia_ids + [eid])
        movimientos = cursor.fetchall()

    # 3) Construir tablas (sin cambios en lógica)
    rows = []
    pu = 0.0
    saldo_u = 0.0
    saldo_mx = 0.0
    for m in movimientos:
        tipo = (m.get('tipo_movimiento') or '').strip().lower()
        es_entrada = tipo in ('entrada','compra')
        contenido = m.get('contenido_neto_total')
        
        if es_entrada:
            entrada_u = float(contenido) if (contenido and float(contenido) > 0) else float(m.get('unidades') or 0.0)
            pu_entrada = float(m.get('precio_unitario') or 0.0)
            entrada_mx = entrada_u * pu_entrada
            
            saldo_u += entrada_u
            saldo_mx += entrada_mx
            pu = saldo_mx / saldo_u if saldo_u > 0 else 0.0
            
            salida_u = 0.0
            salida_mx = 0.0
        
        elif tipo == 'salida':
            salida_u = float(m.get('unidades') or 0.0)
            salida_mx = salida_u * pu
            
            saldo_u -= salida_u
            saldo_mx -= salida_mx
            
            entrada_u = 0.0
            entrada_mx = 0.0
        else:
            entrada_u = salida_u = entrada_mx = salida_mx = 0.0
            
        rows.append({
            "fecha": m.get("fecha_fmt"),
            "documento": m.get("documento"),
            "fuente": m.get("fuente", ""),
            "entrada_u": entrada_u, "salida_u": salida_u, "saldo_u": saldo_u,
            "entrada_mx": entrada_mx, "salida_mx": salida_mx, "saldo_mx": saldo_mx,
            "pu": pu,
        })

    tabla_unidades = [{"fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
                       "entrada": r["entrada_u"], "salida": r["salida_u"], "saldo": r["saldo_u"]} for r in rows]
    tabla_pesos = [{"fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
                    "entrada": r["entrada_mx"], "salida": r["salida_mx"], "saldo": r["saldo_mx"], "pu": r["pu"]} for r in rows]

    total_entradas_u = sum(r["entrada_u"] for r in rows)
    total_salidas_u = sum(r["salida_u"] for r in rows)
    total_entradas_mx = sum(r["entrada_mx"] for r in rows)
    total_salidas_mx = sum(r["salida_mx"] for r in rows)
    
    saldo_final_u = rows[-1]["saldo_u"] if rows else 0.0
    saldo_final_mx = rows[-1]["saldo_mx"] if rows else 0.0
    pu_final = rows[-1]["pu"] if rows else 0.0

    cursor.close()
    conn.close()
    
    return render_template('inventarios/inventario_movimientos.html',
                           producto=producto,
                           tabla_unidades=tabla_unidades,
                           tabla_pesos=tabla_pesos,
                           total_entradas_u=total_entradas_u,
                           total_salidas_u=total_salidas_u,
                           saldo_final_u=saldo_final_u,
                           total_entradas_mx=total_entradas_mx,
                           total_salidas_mx=total_salidas_mx,
                           saldo_final_mx=saldo_final_mx,
                           pu_final=pu_final,
                           back_endpoint='mostrar_inventario_mp')

@app.route('/inventarios/comprar_mp', methods=['GET', 'POST'])
def comprar_mp():
    if 'rol' not in session or session.get('rol') != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        try:
            mercancia_id = int(request.form['mercancia_id'])
            unidades = request.form['unidades']
            precio_unitario = request.form['precio_unitario']
            ref = request.form.get('referencia') or 'Compra MP'
            # Fase MP = 1
            registrar_movimiento(
                tipo_inventario_id=1,
                mercancia_id=mercancia_id,
                tipo_movimiento='entrada',
                unidades=unidades,
                precio_unitario=precio_unitario,
                referencia=ref,
                usuario_id=session.get('usuario_id')
            )
            flash('Compra MP registrada.', 'success')
            return redirect(url_for('mostrar_inventario'))  # o a donde prefieras
        except Exception as e:
            flash(f'Error al registrar compra MP: {e}', 'danger')
            return redirect(url_for('comprar_mp'))

    # GET: llenar el select
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
    mercancias = cur.fetchall()
    cur.close(); conn.close()
    return render_template('inventarios/comprar_mp.html', mercancias=mercancias)


@app.route('/venta', methods=['GET', 'POST'])
def vender_producto():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        unidades = float(request.form['unidades'])

        costo_total = salida_peps(3, producto_id, unidades, 'Venta')
        flash(f'Venta registrada. Costo total: {costo_total}', 'success')
        return redirect('/inventario')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM productos_terminados")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('inventarios/venta.html', productos=productos)

@app.route('/inventarios/produccion/nueva', methods=['GET', 'POST'])
def nueva_produccion():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # Obtener catálogo de MP y PT
    cursor.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
    materias_primas = cursor.fetchall()

    cursor.execute("SELECT id, nombre FROM productos_terminados ORDER BY nombre")
    productos_terminados = cursor.fetchall()

    if request.method == 'POST':
        producto_terminado_id = request.form['producto_terminado_id']
        cantidad_producida = float(request.form['cantidad_producida'])
        fecha = request.form['fecha'] or date.today()

        # Insertar producción
        cursor.execute("""
            INSERT INTO produccion (fecha, producto_terminado_id, cantidad_producida)
            VALUES (%s, %s, %s)
        """, (fecha, producto_terminado_id, cantidad_producida))
        produccion_id = cursor.lastrowid

        # Insertar consumo de MP
        for mp_id, qty in zip(request.form.getlist('mp_id'), request.form.getlist('cantidad_mp')):
            if qty and float(qty) > 0:
                cursor.execute("""
                    INSERT INTO produccion_detalle_mp (produccion_id, mercancia_id, cantidad_usada)
                    VALUES (%s, %s, %s)
                """, (produccion_id, mp_id, float(qty)))

                # Genera salida en movimientos (si manejas inventario por movimientos)
                cursor.execute("""
                    INSERT INTO inventario_movimientos
                    (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
                    VALUES (1, %s, 'SALIDA', %s, 0, %s, %s)
                """, (mp_id, float(qty), f'Producción {produccion_id}', fecha))


        # Actualizar inventario PT (entradas)
        cursor.execute("""
            INSERT INTO inventario_pt (producto_id, entradas)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE entradas = entradas + VALUES(entradas)
        """, (producto_terminado_id, cantidad_producida))

        conn.commit()
        flash('Producción registrada correctamente.', 'success')
        return redirect(url_for('listar_produccion'))

    cursor.close()
    conn.close()
    return render_template('inventarios/produccion.html',
                           materias_primas=materias_primas,
                           productos_terminados=productos_terminados)

@app.route('/inventarios/materias_primas')
@require_login
def mostrar_inventario_mp():
    """Inventario de Materias Primas (filtrado por empresa)"""
    eid = g.empresa_id  # ✅ Empresa activa
    
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # ✅ OBTENER TODOS LOS PRODUCTOS BASE (FILTRADO POR EMPRESA)
        cur.execute("""
            SELECT
                pb.id AS producto_base_id,
                pb.id AS id,
                pb.nombre AS producto,
                MIN(m.id) AS mercancia_id,
                GROUP_CONCAT(m.id) AS mercancia_ids,
                COALESCE(MAX(i.inventario_inicial), 0) AS inventario_inicial,
                MAX(i.aprobado) AS aprobado
            FROM producto_base pb
            JOIN mercancia m ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id = m.id AND i.empresa_id = %s
            WHERE pb.activo = 1 
              AND m.tipo = 'MP'
              AND m.empresa_id = %s
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre
        """, (eid, eid))
        inventario = cur.fetchall()
        
        # ✅ CALCULAR SALDO FINAL CON COSTEO PROMEDIO PONDERADO (FILTRADO)
        for item in inventario:
            mercancia_ids = [int(x) for x in item['mercancia_ids'].split(',')]
            placeholders = ','.join(['%s'] * len(mercancia_ids))
            
            # Query con filtro de empresa
            sql = f"""
            SELECT * FROM (
                SELECT lc.fecha AS fecha_raw,
                       dc.contenido_neto_total,
                       CASE WHEN dc.contenido_neto_total>0
                            THEN dc.precio_total/dc.contenido_neto_total ELSE NULL END AS precio_unitario,
                       'compra' AS tipo_movimiento
                FROM detalle_compra dc
                JOIN listado_compras lc ON dc.compra_id = lc.id
                WHERE dc.mercancia_id IN ({placeholders})
                  AND dc.empresa_id = %s
                  AND lc.empresa_id = %s
                UNION ALL
                SELECT im.fecha AS fecha_raw,
                    im.unidades,
                    im.precio_unitario,
                    im.tipo_movimiento
                FROM inventario_movimientos im
                WHERE im.mercancia_id IN ({placeholders})
                AND im.tipo_inventario_id = 1
                AND im.empresa_id = %s
                AND UPPER(im.tipo_movimiento) <> 'COMPRA'
                AND im.unidades > 0
                AND im.tipo_movimiento IS NOT NULL
                AND im.tipo_movimiento <> ''
            ) t
            ORDER BY t.fecha_raw ASC
            """
            cur.execute(sql, mercancia_ids + [eid, eid] + mercancia_ids + [eid])
            movimientos = cur.fetchall()
            
            # ✅ COSTEO PROMEDIO PONDERADO
            pu = 0.0
            saldo_u = float(item['inventario_inicial'])
            saldo_mx = 0.0
            entradas_total = 0.0
            salidas_total = 0.0
            
            for m in movimientos:
                tipo = (m.get('tipo_movimiento') or '').strip().lower()
                es_entrada = tipo in ('entrada', 'compra')
                contenido = m.get('contenido_neto_total')
                
                if es_entrada:
                    entrada_u = float(contenido) if (contenido and float(contenido) > 0) else float(m.get('unidades') or 0.0)
                    pu_entrada = float(m.get('precio_unitario') or 0.0)
                    entrada_mx = entrada_u * pu_entrada
                    
                    saldo_u += entrada_u
                    saldo_mx += entrada_mx
                    entradas_total += entrada_u
                    
                    pu = saldo_mx / saldo_u if saldo_u > 0 else 0.0
                    
                elif tipo == 'salida':
                    salida_u = float(m.get('unidades') or 0.0)
                    salida_mx = salida_u * pu
                    
                    saldo_u -= salida_u
                    saldo_mx -= salida_mx
                    salidas_total += salida_u
            
            item['entradas'] = entradas_total
            item['salidas'] = salidas_total
            item['disponible'] = saldo_u
            item['valor_inventario'] = saldo_mx
            
    finally:
        cur.close()
        conn.close()

    return render_template('inventarios/mp/inventario.html', inventario=inventario)
    
@app.route('/inventarios/produccion/listar')
@require_login
def listar_produccion():
    eid = g.empresa_id
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, p.fecha, pt.nombre AS producto, p.cantidad_producida, p.estado
        FROM produccion p
        JOIN productos_terminados pt ON pt.id = p.producto_terminado_id
        WHERE p.empresa_id = %s
        ORDER BY p.fecha ASC
    """, (eid,))
    producciones = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('inventarios/listar_produccion.html', producciones=producciones)

@app.route('/inventarios/productos_terminados', methods=['GET', 'POST'])
def inventario_productos_terminados():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            pt.id,
            pt.nombre,
            COALESCE(e.total_entradas, 0) AS entradas_calc,
            COALESCE(s.total_salidas, 0) AS salidas_calc,
            (COALESCE(e.total_entradas, 0) - COALESCE(s.total_salidas, 0)) AS disponible_calc
        FROM productos_terminados pt
        LEFT JOIN (
            SELECT producto_terminado_id, SUM(cantidad) AS total_entradas
            FROM produccion
            GROUP BY producto_terminado_id
        ) e ON e.producto_terminado_id = pt.id
        LEFT JOIN (
            SELECT producto_terminado_id, SUM(unidades) AS total_salidas
            FROM detalle_venta
            GROUP BY producto_terminado_id
        ) s ON s.producto_terminado_id = pt.id
        ORDER BY pt.nombre ASC
    """)
    inventario_pt = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('inventarios/productos_terminados.html', inventario=inventario_pt)

@app.route('/inventarios/cerrar_produccion', methods=['POST'])
def cerrar_produccion():

    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    producto_id = request.form['producto_id']

    # Salida desde WIP (tipo 2)
    costo_wip = salida_peps(2, producto_id, 1, 'Cierre Producción')

    # Calcular precio unitario del producto terminado
    cantidad_producida = float(request.form['cantidad_producida'])
    precio_unitario = costo_wip / 1  # si siempre es una unidad, ajusta si es más

    # Entrada en PT (tipo 3) con precio unitario
    conn = conexion_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inventario_pt (producto_id, entradas, precio_unitario)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            entradas = entradas + VALUES(entradas),
            precio_unitario = VALUES(precio_unitario)
    """, (producto_id, cantidad_producida, precio_unitario))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Producción cerrada y producto terminado ingresado', 'success')
    return redirect(url_for('inventario_productos_terminados'))

@app.route('/inventarios/venta', methods=['GET', 'POST'])
def venta_productos_terminados():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # Cargar lista de productos terminados disponibles
    cursor.execute("SELECT id, nombre FROM productos_terminados ORDER BY nombre")
    productos = cursor.fetchall()

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        unidades = float(request.form['unidades'])

        # 🔹 Calcular costo con PEPS
        cursor.execute("""
            SELECT id, entradas AS unidades, precio_unitario
            FROM inventario_pt
            WHERE producto_id = %s AND entradas > 0
            ORDER BY id ASC
        """, (producto_id,))
        lotes = cursor.fetchall()

        unidades_pendientes = unidades
        costo_total = 0

        for lote in lotes:
            if unidades_pendientes <= 0:
                break
            if lote['unidades'] <= unidades_pendientes:
                costo_total += lote['unidades'] * lote['precio_unitario']
                unidades_pendientes -= lote['unidades']
                # Marcar lote como consumido
                cursor.execute("UPDATE inventario_pt SET entradas = 0 WHERE id = %s", (lote['id'],))
            else:
                costo_total += unidades_pendientes * lote['precio_unitario']
                cursor.execute("""
                    UPDATE inventario_pt
                    SET entradas = entradas - %s
                    WHERE id = %s
                """, (unidades_pendientes, lote['id']))
                unidades_pendientes = 0

        # Registrar en detalle_venta
        cursor.execute("""
            INSERT INTO detalle_venta (producto_terminado_id, unidades, precio_unitario, fecha)
            VALUES (%s, %s, %s, CURDATE())
        """, (producto_id, unidades, costo_total / unidades if unidades > 0 else 0))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Venta registrada. Costo total: {costo_total:.2f}", "success")
        return redirect('/inventarios/productos_terminados')

    cursor.close()
    conn.close()
    return render_template('inventarios/venta.html', productos=productos)

@app.route('/inventario/<int:producto_id>/ajustar', methods=['GET', 'POST'])
def ajustar_inventario(producto_id):
    if request.method == 'POST':
        cantidad = request.form['cantidad']
        conn = conexion_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inventario
            SET inventario_inicial = %s
            WHERE id = %s
        """, (cantidad, producto_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Inventario ajustado correctamente', 'success')
        return redirect(url_for('mostrar_inventario'))

    return render_template('inventarios/ajustar.html', producto_id=producto_id)






#     WIP    INVENTORY         #




@app.route('/inventarios/wip')
@require_login
def mostrar_inventario_wip():
    """Inventario WIP (Trabajo en Proceso) - FILTRADO POR EMPRESA"""
    eid = g.empresa_id  # ✅ Empresa activa
    
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # ✅ OBTENER TODOS LOS PRODUCTOS WIP (FILTRADO POR EMPRESA)
        cur.execute("""
            SELECT
                pb.id AS producto_base_id,
                pb.id AS id,
                pb.nombre AS producto,
                MIN(m.id) AS mercancia_id,
                GROUP_CONCAT(m.id) AS mercancia_ids,
                COALESCE(MAX(i.inventario_inicial), 0) AS inventario_inicial,
                MAX(i.aprobado) AS aprobado
            FROM producto_base pb
            JOIN mercancia m ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id = m.id AND i.empresa_id = %s
            WHERE pb.activo = 1 
              AND m.tipo = 'WIP'
              AND m.empresa_id = %s
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre
        """, (eid, eid))
        inventario = cur.fetchall()
        
        # ✅ CALCULAR SALDO FINAL CON COSTEO PROMEDIO PONDERADO
        for item in inventario:
            mercancia_ids = [int(x) for x in item['mercancia_ids'].split(',')]
            placeholders = ','.join(['%s'] * len(mercancia_ids))
            
            # ✅ Query para movimientos de WIP (FILTRADO POR EMPRESA)
            sql = f"""
            SELECT im.fecha AS fecha_raw,
                   im.tipo_movimiento,
                   im.unidades,
                   im.precio_unitario
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders})
              AND im.tipo_inventario_id = 2
              AND im.empresa_id = %s
              AND im.unidades > 0
              AND im.tipo_movimiento IS NOT NULL
              AND im.tipo_movimiento <> ''
            ORDER BY im.fecha ASC, im.id ASC
            """
            cur.execute(sql, mercancia_ids + [eid])
            movimientos = cur.fetchall()
            
            # ✅ APLICAR COSTEO PROMEDIO PONDERADO
            pu = 0.0
            saldo_u = float(item['inventario_inicial'])
            saldo_mx = 0.0
            entradas_total = 0.0
            salidas_total = 0.0
            
            for m in movimientos:
                tipo = (m.get('tipo_movimiento') or '').strip().lower()
                es_entrada = tipo in ('entrada', 'compra')
                
                if es_entrada:
                    entrada_u = float(m.get('unidades') or 0.0)
                    pu_entrada = float(m.get('precio_unitario') or 0.0)
                    entrada_mx = entrada_u * pu_entrada
                    
                    saldo_u += entrada_u
                    saldo_mx += entrada_mx
                    entradas_total += entrada_u
                    
                    # Recalcular precio promedio ponderado
                    pu = saldo_mx / saldo_u if saldo_u > 0 else 0.0
                    
                elif tipo == 'salida':
                    salida_u = float(m.get('unidades') or 0.0)
                    salida_mx = salida_u * pu  # ✅ USA EL COSTO PROMEDIO
                    
                    saldo_u -= salida_u
                    saldo_mx -= salida_mx
                    salidas_total += salida_u
            
            # ✅ ASIGNAR VALORES FINALES
            item['entradas'] = entradas_total
            item['salidas'] = salidas_total
            item['disponible'] = saldo_u
            item['valor_inventario'] = saldo_mx
            
    finally:
        cur.close()
        conn.close()

    return render_template('inventarios/wip/inventario.html', inventario=inventario)

@app.route('/inventarios/movimientos-wip/<int:producto_base_id>')
def inventario_movimientos_wip(producto_base_id):
    """Movimientos de WIP por producto base"""
    if 'rol' not in session:
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 1) Obtener nombre del producto base y mercancías asociadas
    cursor.execute("""
        SELECT pb.nombre as producto_base_nombre,
               GROUP_CONCAT(m.id) as mercancia_ids
        FROM producto_base pb
        LEFT JOIN mercancia m ON m.producto_base_id = pb.id
        WHERE pb.id = %s
        GROUP BY pb.id, pb.nombre
    """, (producto_base_id,))
    
    row = cursor.fetchone()
    if not row or not row['mercancia_ids']:
        cursor.close()
        conn.close()
        flash('Producto no encontrado.', 'warning')
        return redirect(url_for('mostrar_inventario_wip'))
    
    producto = row['producto_base_nombre']
    mercancia_ids = [int(x) for x in row['mercancia_ids'].split(',')]
    
    almacen_id = int(request.args.get('almacen', 2))  # Default 2 para WIP

    # 2) Query movimientos WIP
    placeholders = ','.join(['%s'] * len(mercancia_ids))
    cursor.execute(f"""
        SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
               im.referencia AS documento, '' AS fuente, im.unidades,
               NULL AS contenido_neto_total, im.precio_unitario,
               (im.unidades*im.precio_unitario) AS importe, im.tipo_movimiento
        FROM inventario_movimientos im
        WHERE im.mercancia_id IN ({placeholders}) AND im.tipo_inventario_id = %s
        ORDER BY im.fecha ASC, im.id ASC
    """, mercancia_ids + [almacen_id])
    movimientos = cursor.fetchall()

    # 3) Construir tablas con costeo promedio
    rows = []
    pu = 0.0
    saldo_u = 0.0
    saldo_mx = 0.0
    
    for m in movimientos:
        tipo = (m.get('tipo_movimiento') or '').strip().lower()
        es_entrada = tipo in ('entrada', 'compra')
        
        if es_entrada:
            entrada_u = float(m.get('unidades') or 0.0)
            pu_entrada = float(m.get('precio_unitario') or 0.0)
            entrada_mx = entrada_u * pu_entrada
            
            saldo_u += entrada_u
            saldo_mx += entrada_mx
            
            pu = saldo_mx / saldo_u if saldo_u > 0 else 0.0
            
            salida_u = 0.0
            salida_mx = 0.0
        
        elif tipo == 'salida':
            salida_u = float(m.get('unidades') or 0.0)
            salida_mx = salida_u * pu
            
            saldo_u -= salida_u
            saldo_mx -= salida_mx
            
            entrada_u = 0.0
            entrada_mx = 0.0
        else:
            entrada_u = salida_u = entrada_mx = salida_mx = 0.0
            
        rows.append({
            "fecha": m.get("fecha_fmt"),
            "documento": m.get("documento"),
            "fuente": m.get("fuente", ""),
            "entrada_u": entrada_u, "salida_u": salida_u, "saldo_u": saldo_u,
            "entrada_mx": entrada_mx, "salida_mx": salida_mx, "saldo_mx": saldo_mx,
            "pu": pu,
        })

    tabla_unidades = [{"fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
                       "entrada": r["entrada_u"], "salida": r["salida_u"], "saldo": r["saldo_u"]} for r in rows]
    tabla_pesos = [{"fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
                    "entrada": r["entrada_mx"], "salida": r["salida_mx"], "saldo": r["saldo_mx"], "pu": r["pu"]} for r in rows]

    # Totales
    total_entradas_u = sum(r["entrada_u"] for r in rows)
    total_salidas_u = sum(r["salida_u"] for r in rows)
    total_entradas_mx = sum(r["entrada_mx"] for r in rows)
    total_salidas_mx = sum(r["salida_mx"] for r in rows)
    
    saldo_final_u = rows[-1]["saldo_u"] if rows else 0.0
    saldo_final_mx = rows[-1]["saldo_mx"] if rows else 0.0
    pu_final = rows[-1]["pu"] if rows else 0.0

    cursor.close()
    conn.close()
    
    return render_template('inventarios/inventario_movimientos.html',
                           producto=producto,
                           tabla_unidades=tabla_unidades,
                           tabla_pesos=tabla_pesos,
                           total_entradas_u=total_entradas_u,
                           total_salidas_u=total_salidas_u,
                           saldo_final_u=saldo_final_u,
                           total_entradas_mx=total_entradas_mx,
                           total_salidas_mx=total_salidas_mx,
                           saldo_final_mx=saldo_final_mx,
                           pu_final=pu_final,
                           back_endpoint='mostrar_inventario_wip')

@app.route('/inventarios/produccion', methods=['GET', 'POST'])
def crear_produccion():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        producto_id = request.form['producto_id']

        # Convertir los campos usos[ID] en lista de diccionarios
        materiales = []
        for key, value in request.form.items():
            if key.startswith("usos[") and value.strip():
                mercancia_id = key.split("[")[1].strip("]")
                unidades = float(value)
                materiales.append({
                    "mercancia_id": mercancia_id,
                    "unidades": unidades
                })

        # Calcular costo total y registrar salida de cada materia prima
        costo_total = 0
        for mat in materiales:
            costo_total += salida_peps(
                1,  # ID de almacén origen
                mat['mercancia_id'],
                mat['unidades'],
                'Producción WIP'
            )

        # Registrar entrada del producto terminado en WIP
        registrar_movimiento(
            2,  # ID de almacén destino
            producto_id,
            'entrada',
            1,  # Cantidad fabricada (puedes hacer dinámico si lo agregas al form)
            costo_total,
            'Inicio Producción'
        )

        flash('Producción iniciada', 'success')
        return redirect('/inventarios/produccion/listar')

    # GET: renderiza la vista con datos
    return render_template('inventarios/produccion.html')


@app.route('/production/<int:orden_id>')
@require_login
def orden_detalle(orden_id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        # Datos principales VALIDANDO EMPRESA
        cur.execute("""
            SELECT op.id, op.fecha_creacion, op.cantidad_programada, op.estado,
                   op.observaciones, m.nombre AS producto
            FROM orden_produccion op
            JOIN mercancia m ON op.producto_id = m.id
            WHERE op.id = %s AND op.empresa_id = %s
        """, (orden_id, eid))
        orden = cur.fetchone()

        if not orden:
            flash('Orden de producción no encontrada.', 'warning')
            return redirect(url_for('list_production'))

        # Fases asociadas
        cur.execute("""
            SELECT a.nombre AS area, f.descripcion, f.duracion, f.estado
            FROM orden_fase f
            JOIN areas_produccion a ON f.area_id = a.id
            WHERE f.orden_id = %s AND a.empresa_id = %s
            ORDER BY f.id ASC
        """, (orden_id, eid))
        fases = cur.fetchall()

        # Materias primas
        cur.execute("""
            SELECT mp.nombre, om.cantidad_usada, om.costo_unitario
            FROM orden_material om
            JOIN mercancia mp ON om.mp_id = mp.id
            WHERE om.orden_id = %s AND mp.empresa_id = %s
            ORDER BY mp.nombre
        """, (orden_id, eid))
        materiales = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    return render_template(
        'inventarios/WIP/orden_detalle.html',
        orden=orden,
        fases=fases,
        materiales=materiales
    )

@app.route('/production/new', methods=['GET', 'POST'])
@require_login
def new_production():
    eid = g.empresa_id
    
    if request.method == 'POST':
        producto_id = (request.form.get('pt_id') or request.form.get('finished_product_id') or '').strip()
        cantidad_planificada = (request.form.get('planned_quantity') or '').strip()
        fecha = (request.form.get('date') or '').strip()

        if not producto_id.isdigit():
            flash('Selecciona un Producto Terminado válido del listado.', 'danger')
            return redirect(url_for('new_production'))
        if not fecha:
            flash('La fecha es obligatoria.', 'danger')
            return redirect(url_for('new_production'))
        try:
            cantidad = float(cantidad_planificada)
            if cantidad <= 0:
                raise ValueError()
        except Exception:
            flash('La cantidad planificada debe ser mayor que 0.', 'danger')
            return redirect(url_for('new_production'))

        conn = conexion_db()
        cur = conn.cursor(dictionary=True)
        try:
            # Verificar producto PERTENECE A EMPRESA
            cur.execute("""
                SELECT 1 FROM mercancia 
                WHERE id=%s AND tipo='PT' AND empresa_id=%s 
                LIMIT 1
            """, (producto_id, eid))
            if not cur.fetchone():
                flash('El producto seleccionado no existe o no es de tipo PT.', 'danger')
                return redirect(url_for('new_production'))

            # Verificar proceso definido
            cur.execute("""
                SELECT 1 FROM procesos 
                WHERE pt_id=%s AND activo=1 AND empresa_id=%s 
                LIMIT 1
            """, (producto_id, eid))
            if not cur.fetchone():
                flash('Define el proceso de producción antes de crear la orden.', 'warning')
                return redirect(url_for('recetas_proceso', pt_id=producto_id))

            # Crear orden CON EMPRESA
            cur.execute("""
                INSERT INTO orden_produccion (empresa_id, producto_id, cantidad_programada, fecha_creacion, estado)
                VALUES (%s, %s, %s, %s, 'pendiente')
            """, (eid, producto_id, cantidad, fecha))
            conn.commit()

            flash('Orden de producción creada correctamente.', 'success')
            return redirect(url_for('list_production'))

        except Exception as e:
            conn.rollback()
            flash(f'Error al crear la orden: {e}', 'danger')
            return redirect(url_for('new_production'))
        finally:
            cur.close()
            conn.close()

    # GET - Mostrar formulario
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, nombre
        FROM mercancia
        WHERE tipo='PT' AND empresa_id=%s
        ORDER BY nombre
    """, (eid,))
    productos = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('inventarios/WIP/orden_nueva.html', productos=productos)

@app.route('/production')
@require_login
def list_production():
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT op.id,
                   op.fecha_creacion,
                   m.nombre AS producto,
                   op.cantidad_programada,
                   op.estado
            FROM orden_produccion op
            JOIN mercancia m ON op.producto_id = m.id
            WHERE op.empresa_id = %s
            ORDER BY op.fecha_creacion DESC, op.id DESC
        """, (eid,))
        ordenes = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template('inventarios/WIP/orden_list.html', ordenes=ordenes)

def costo_promedio_mp(cur, mercancia_id):
    cur.execute("""
      SELECT SUM(CASE WHEN tipo_movimiento IN ('COMPRA','ENTRADA') THEN unidades*precio_unitario ELSE 0 END) /
             NULLIF(SUM(CASE WHEN tipo_movimiento IN ('COMPRA','ENTRADA') THEN unidades ELSE 0 END),0)
      AS pu
      FROM inventario_movimientos
      WHERE mercancia_id=%s AND tipo_inventario_id=1
    """, (mercancia_id,))
    r = cur.fetchone()
    return float(r['pu'] or 0) or 0.0

def consumir_mp_paso(cur, orden_id, paso_id):
    # obtiene orden, proceso, batch_size y materiales del paso
    cur.execute("""SELECT o.cantidad_programada, p.batch_size
                   FROM prod_orden o JOIN prod_proceso p ON p.id=o.proceso_id
                   WHERE o.id=%s""", (orden_id,))
    ord_ = cur.fetchone()
    factor = float(ord_['cantidad_programada']) / float(ord_['batch_size'])

    cur.execute("""SELECT insumo_id, cantidad_base FROM prod_paso_material WHERE paso_id=%s""",(paso_id,))
    for mat in cur.fetchall():
        insumo = mat['insumo_id']
        unidades = float(mat['cantidad_base']) * factor
        pu = costo_promedio_mp(cur, insumo)

        # SALIDA MP
        cur.execute("""
          INSERT INTO inventario_movimientos
          (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
          VALUES (1, %s, 'SALIDA', %s, %s, %s, CURDATE())
        """, (insumo, unidades, pu, f"OP{orden_id}-PASO{paso_id}"))

        # ENTRADA WIP
        cur.execute("""
          INSERT INTO inventario_movimientos
          (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
          VALUES (2, %s, 'ENTRADA', %s, %s, %s, CURDATE())
        """, (insumo, unidades, pu, f"OP{orden_id}-PASO{paso_id}"))

def cerrar_op(cur, orden_id):
    # producto terminado de la OP
    cur.execute("""SELECT pp.producto_salida_id, pp.merma_pct, o.cantidad_programada
                   FROM prod_orden o JOIN prod_proceso pp ON pp.id=o.proceso_id
                   WHERE o.id=%s""",(orden_id,))
    r = cur.fetchone()
    pt_id = r['producto_salida_id']
    merma = float(r['merma_pct'] or 0)/100.0
    qty_pt = float(r['cantidad_programada']) * (1 - merma)

    # costo acumulado en WIP (sum entradas WIP - salidas WIP)
    cur.execute("""
      SELECT 
        COALESCE(SUM(CASE WHEN tipo_movimiento='ENTRADA' THEN unidades*precio_unitario END),0) -
        COALESCE(SUM(CASE WHEN tipo_movimiento='SALIDA'  THEN unidades*precio_unitario END),0) AS costo
      FROM inventario_movimientos
      WHERE tipo_inventario_id=2 AND referencia LIKE %s
    """, (f"OP{orden_id}%",))
    costo_wip = float(cur.fetchone()['costo'] or 0)
    pu_pt = (costo_wip/qty_pt) if qty_pt>0 else 0

    # SALIDA WIP (total unidades efectivas)#
    cur.execute("""
      INSERT INTO inventario_movimientos
      (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
      VALUES (2, %s, 'SALIDA', %s, %s, %s, CURDATE())
    """, (pt_id, qty_pt, pu_pt, f"OP{orden_id}-CIERRE"))

    # ENTRADA PT#
    cur.execute("""
      INSERT INTO inventario_movimientos
      (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
      VALUES (3, %s, 'ENTRADA', %s, %s, %s, CURDATE())
    """, (pt_id, qty_pt, pu_pt, f"OP{orden_id}-CIERRE"))



# ======================================================
# 3. UTILITARIOS (mantener, solo ajustar nombres de tabla)
# ======================================================

def costo_promedio_mp(cur, mercancia_id):
    cur.execute("""
      SELECT SUM(CASE WHEN tipo_movimiento IN ('COMPRA','ENTRADA') THEN unidades*precio_unitario ELSE 0 END) /
             NULLIF(SUM(CASE WHEN tipo_movimiento IN ('COMPRA','ENTRADA') THEN unidades ELSE 0 END),0)
      AS pu
      FROM inventario_movimientos
      WHERE mercancia_id=%s AND tipo_inventario_id=1
    """, (mercancia_id,))
    r = cur.fetchone()
    return float(r['pu'] or 0) or 0.0


def consumir_mp_paso(cur, orden_id, fase_id):
    cur.execute("""SELECT op.cantidad_programada, pf.batch_size
                   FROM orden_produccion op
                   JOIN orden_fase pf ON pf.orden_id=op.id
                   WHERE op.id=%s""", (orden_id,))
    ord_ = cur.fetchone()
    factor = float(ord_['cantidad_programada']) / float(ord_['batch_size'])

    cur.execute("""SELECT mp_id, cantidad_base 
                   FROM orden_material WHERE fase_id=%s""", (fase_id,))
    for mat in cur.fetchall():
        insumo = mat['mp_id']
        unidades = float(mat['cantidad_base']) * factor
        pu = costo_promedio_mp(cur, insumo)

        # SALIDA MP
        cur.execute("""
          INSERT INTO inventario_movimientos
          (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
          VALUES (1, %s, 'SALIDA', %s, %s, %s, CURDATE())
        """, (insumo, unidades, pu, f"OP{orden_id}-FASE{fase_id}"))

        # ENTRADA WIP
        cur.execute("""
          INSERT INTO inventario_movimientos
          (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
          VALUES (2, %s, 'ENTRADA', %s, %s, %s, CURDATE())
        """, (insumo, unidades, pu, f"OP{orden_id}-FASE{fase_id}"))


def cerrar_op(cur, orden_id):
    cur.execute("""SELECT op.producto_id, op.cantidad_programada, SUM(pw.unidades*pw.precio_unitario) AS costo_wip
                   FROM orden_produccion op
                   JOIN inventario_movimientos pw ON pw.referencia LIKE %s
                   WHERE op.id=%s
                """, (f"OP{orden_id}%", orden_id))
    r = cur.fetchone()
    pt_id = r['producto_id']
    qty_pt = float(r['cantidad_programada'])
    costo_total = float(r['costo_wip'] or 0)
    pu_pt = (costo_total/qty_pt) if qty_pt > 0 else 0

    cur.execute("""
      INSERT INTO inventario_movimientos
      (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
      VALUES (2, %s, 'SALIDA', %s, %s, %s, CURDATE())
    """, (pt_id, qty_pt, pu_pt, f"OP{orden_id}-CIERRE"))

    cur.execute("""
      INSERT INTO inventario_movimientos
      (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
      VALUES (3, %s, 'ENTRADA', %s, %s, %s, CURDATE())
    """, (pt_id, qty_pt, pu_pt, f"OP{orden_id}-CIERRE"))


@app.route('/production/<int:orden_id>/close', methods=['POST'])
@require_login
def cerrar_orden_produccion(orden_id):
    """Cierra una orden de producción - VALIDANDO EMPRESA"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        # Verificar orden PERTENECE A EMPRESA
        cur.execute("""
            SELECT op.id, op.estado, op.cantidad_programada, m.id AS producto_id, m.nombre AS producto
            FROM orden_produccion op
            JOIN mercancia m ON op.producto_id = m.id
            WHERE op.id = %s AND op.empresa_id = %s
        """, (orden_id, eid))
        orden = cur.fetchone()

        if not orden:
            flash('Orden no encontrada.', 'warning')
            return redirect(url_for('list_production'))

        if orden['estado'] == 'cerrada':
            flash('Esta orden ya está cerrada.', 'info')
            return redirect(url_for('list_production'))

        # Calcular costo WIP
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN tipo_movimiento='ENTRADA' THEN unidades * precio_unitario END),0)
                - COALESCE(SUM(CASE WHEN tipo_movimiento='SALIDA' THEN unidades * precio_unitario END),0) AS costo_total
            FROM inventario_movimientos
            WHERE tipo_inventario_id = 2
              AND empresa_id = %s
              AND referencia LIKE %s
        """, (eid, f"OP{orden_id}%"))
        costo_wip = float(cur.fetchone()['costo_total'] or 0)

        cantidad_final = float(orden['cantidad_programada'])
        pu_pt = (costo_wip / cantidad_final) if cantidad_final > 0 else 0

        # Salida WIP
        cur.execute("""
            INSERT INTO inventario_movimientos
            (empresa_id, tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
            VALUES (%s, 2, %s, 'SALIDA', %s, %s, %s, NOW())
        """, (eid, orden['producto_id'], cantidad_final, pu_pt, f"OP{orden_id}-CIERRE"))

        # Entrada PT
        cur.execute("""
            INSERT INTO inventario_movimientos
            (empresa_id, tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
            VALUES (%s, 3, %s, 'ENTRADA', %s, %s, %s, NOW())
        """, (eid, orden['producto_id'], cantidad_final, pu_pt, f"OP{orden_id}-CIERRE"))

        # Cerrar orden
        cur.execute("UPDATE orden_produccion SET estado='cerrada' WHERE id=%s", (orden_id,))
        conn.commit()

        flash(f"Orden #{orden_id} cerrada. Costo total: ${costo_wip:,.2f}", 'success')
        return redirect(url_for('list_production'))

    except Exception as e:
        conn.rollback()
        flash(f"Error al cerrar la orden: {e}", 'danger')
        return redirect(url_for('orden_detalle', orden_id=orden_id))
    finally:
        cur.close()
        conn.close()

# ---------- PROCESOS ----------
# ---------- /admin/procesos ----------


#        PRODUCCION   EN   PROCESO      #


# ---------- DETALLE DE PROCESO: ficha con tabs ----------
@app.route('/admin/procesos/<int:id>', methods=['GET','POST'], endpoint='admin_proceso_detalle')
@require_login
def admin_proceso_detalle(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True, buffered=True)
    try:
        if request.method == 'POST':
            a = request.form.get('accion')

            if a == 'add_insumo':
                cantidad = r2(request.form['cantidad'])
                merma = r2(request.form.get('merma_pct') or 0)
                cur.execute("""
                    INSERT INTO procesos_insumos
                       (empresa_id, proceso_id, mercancia_id, unidad, cantidad, merma_pct)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (eid, id, request.form['mercancia_id'],
                      request.form.get('unidad', ''), str(cantidad), str(merma)))
                conn.commit()
                flash('Insumo agregado', 'success')

            elif a == 'del_insumo':
                cur.execute("""
                    DELETE FROM procesos_insumos 
                    WHERE id=%s AND proceso_id=%s AND empresa_id=%s
                """, (request.form['item_id'], id, eid))
                conn.commit()
                flash('Insumo eliminado', 'info')

            elif a == 'add_operacion':
                orden = int(request.form.get('orden', 1) or 1)
                dur_min = int(request.form.get('duracion_minutos', 0) or 0)
                depende_de = request.form.get('depende_de') or None
                cur.execute("""
                    INSERT INTO procesos_etapas
                       (empresa_id, proceso_id, orden, area_id, nombre, descripcion, duracion_minutos, depende_de, instrucciones)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (eid, id, orden, request.form['area_id'],
                      request.form.get('nombre', ''), request.form.get('descripcion', ''),
                      dur_min, depende_de, request.form.get('instrucciones', '')))
                conn.commit()
                flash('Operación agregada', 'success')

            elif a == 'del_operacion':
                cur.execute("""
                    DELETE FROM procesos_etapas 
                    WHERE id=%s AND proceso_id=%s AND empresa_id=%s
                """, (request.form['etapa_id'], id, eid))
                conn.commit()
                flash('Operación eliminada', 'info')

            elif a == 'add_check':
                cur.execute("""
                    INSERT INTO procesos_etapas_checklist(empresa_id, etapa_id, texto, orden)
                    VALUES (%s, %s, %s,
                      COALESCE((SELECT MAX(orden)+1
                                  FROM procesos_etapas_checklist
                                 WHERE etapa_id=%s), 0)
                    )
                """, (eid, request.form['etapa_id'], request.form['texto'], request.form['etapa_id']))
                conn.commit()
                flash('Checklist agregado', 'success')

        # Cabecera VALIDANDO EMPRESA
        cur.execute("""
            SELECT id, nombre, descripcion FROM procesos 
            WHERE id=%s AND empresa_id=%s
        """, (id, eid))
        proceso = cur.fetchone()
        if not proceso:
            flash('Proceso no encontrado', 'warning')
            return redirect(url_for('admin_procesos'))

        # Áreas del proceso
        cur.execute("""
            SELECT a.id, a.nombre
            FROM procesos_areas pa
            JOIN areas_produccion a ON a.id = pa.area_id
            WHERE pa.proceso_id = %s AND a.empresa_id = %s
            ORDER BY a.nombre
        """, (id, eid))
        areas_proc = cur.fetchall()

        # Catálogos FILTRADOS
        cur.execute("""
            SELECT id, nombre FROM areas_produccion 
            WHERE empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        areas = cur.fetchall()

        cur.execute("""
            SELECT id, nombre FROM mercancia 
            WHERE tipo='MP' AND empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        mercancias = cur.fetchall()

        # Componentes FILTRADOS
        cur.execute("""
            SELECT
                pi.id,
                pi.unidad,
                ROUND(pi.cantidad, 2) AS cantidad,
                ROUND(pi.merma_pct, 2) AS merma_pct,
                m.id AS mercancia_id,
                m.nombre AS mercancia,
                (SELECT ROUND(mov.costo_unitario, 2)
                 FROM movimientos_inventario mov
                 WHERE mov.producto_id = pi.mercancia_id
                 ORDER BY mov.fecha DESC, mov.id DESC
                 LIMIT 1) AS costo_ref
            FROM procesos_insumos pi
            JOIN mercancia m ON m.id = pi.mercancia_id
            WHERE pi.proceso_id = %s AND pi.empresa_id = %s
            ORDER BY pi.id
        """, (id, eid))
        componentes = cur.fetchall()

        # Operaciones FILTRADAS
        cur.execute("""
            SELECT pe.id, pe.orden, pe.nombre, pe.descripcion, pe.duracion_minutos,
                   pe.depende_de, dep.nombre AS depende_de_nombre,
                   a.nombre AS area, pe.instrucciones
            FROM procesos_etapas pe
            JOIN areas_produccion a ON a.id = pe.area_id
            LEFT JOIN procesos_etapas dep ON dep.id = pe.depende_de
            WHERE pe.proceso_id = %s AND pe.empresa_id = %s
            ORDER BY pe.orden, pe.id
        """, (id, eid))
        operaciones = cur.fetchall()

        # Checklist FILTRADO
        cur.execute("""
            SELECT c.id, c.etapa_id, c.texto, c.done, c.orden
            FROM procesos_etapas_checklist c
            WHERE c.empresa_id = %s
              AND c.etapa_id IN (SELECT id FROM procesos_etapas WHERE proceso_id = %s AND empresa_id = %s)
            ORDER BY c.etapa_id, c.orden, c.id
        """, (eid, id, eid))
        checklist = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    return render_template(
        'admin/procesos/detail.html',
        proceso=proceso, areas_proc=areas_proc,
        areas=areas, mercancias=mercancias,
        componentes=componentes, operaciones=operaciones,
        checklist=checklist
    )

# APIs ligeras
@app.route('/admin/operaciones/reordenar', methods=['POST'])
def admin_operaciones_reordenar():
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'ok': False}), 403
    data = request.get_json(force=True)  # {'pares': [{'id':1,'orden':1}, ...]}
    conn = conexion_db()
    cur = conn.cursor()
    try:
        for par in data.get('pares', []):
            cur.execute("UPDATE procesos_etapas SET orden=%s WHERE id=%s", (par['orden'], par['id']))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/checklist/toggle', methods=['POST'])
def admin_checklist_toggle():
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'ok': False}), 403
    cid = request.form['check_id']
    conn = conexion_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE procesos_etapas_checklist SET done = 1 - done WHERE id=%s", (cid,))
        conn.commit()
        return jsonify({'ok': True})
    finally:
        cur.close()
        conn.close()

@app.route('/admin/procesos', methods=['GET','POST'], endpoint='admin_procesos')
@require_login
def admin_procesos():
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            accion = request.form.get('accion')

            if accion == 'add_proceso':
                nombre = request.form['nombre'].strip()
                descripcion = request.form.get('descripcion','').strip()
                pt_id_raw = request.form.get('pt_id')
                pt_id = int(pt_id_raw) if pt_id_raw and pt_id_raw.isdigit() else None

                if pt_id is not None:
                    cur.execute("""
                        SELECT id FROM mercancia 
                        WHERE id=%s AND empresa_id=%s
                    """, (pt_id, eid))
                    if not cur.fetchone():
                        flash('Producto terminado no válido', 'danger')
                        return redirect(url_for('admin_procesos'))

                cur.execute("""
                    INSERT INTO procesos (empresa_id, pt_id, nombre, descripcion)
                    VALUES (%s, %s, %s, %s)
                """, (eid, pt_id, nombre, descripcion))
                conn.commit()
                proc_id = cur.lastrowid

                for a in request.form.getlist('areas[]'):
                    if a:
                        cur.execute("""
                            INSERT IGNORE INTO procesos_areas(proceso_id, area_id, empresa_id) 
                            VALUES(%s, %s, %s)
                        """, (proc_id, a, eid))

                ims_id = request.form.getlist('insumo_mercancia_id[]')
                ims_udm = request.form.getlist('insumo_unidad[]')
                ims_qty = request.form.getlist('insumo_cantidad[]')
                ims_mer = request.form.getlist('insumo_merma[]')
                for mid, udm, qty, mer in zip(ims_id, ims_udm, ims_qty, ims_mer):
                    if mid and qty:
                        cur.execute("""
                            INSERT INTO procesos_insumos(empresa_id, proceso_id, mercancia_id, unidad, cantidad, merma_pct)
                            VALUES(%s, %s, %s, %s, %s, %s)
                        """, (eid, proc_id, mid, (udm or ''), qty, (mer or 0)))
                conn.commit()
                return redirect(url_for('admin_proceso_detalle', id=proc_id))

            elif accion == 'add_insumo':
                cantidad = r2(request.form['cantidad'])
                merma = r2(request.form.get('merma_pct') or 0)
                cur.execute("""
                    INSERT INTO procesos_insumos
                    (empresa_id, proceso_id, mercancia_id, unidad, cantidad, merma_pct)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (eid, request.form['proceso_id'], request.form['mercancia_id'],
                      request.form.get('unidad', ''), str(cantidad), str(merma)))
                conn.commit()
                flash('Insumo agregado', 'success')

            elif accion == 'del_insumo':
                cur.execute("""
                    DELETE FROM procesos_insumos 
                    WHERE id=%s AND proceso_id=%s AND empresa_id=%s
                """, (request.form['item_id'], request.form['proceso_id'], eid))
                conn.commit()
                flash('Insumo eliminado', 'info')

        # GET - Catálogos FILTRADOS
        cur.execute("""
            SELECT id, nombre FROM areas_produccion 
            WHERE empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        areas = cur.fetchall()

        cur.execute("""
            SELECT id, nombre FROM mercancia 
            WHERE tipo='MP' AND empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        mercancias = cur.fetchall()

        cur.execute("""
            SELECT id, nombre FROM mercancia 
            WHERE tipo='PT' AND empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        pts = cur.fetchall()

        # Procesos + áreas FILTRADOS
        cur.execute("""
            SELECT p.id, p.nombre, p.descripcion,
                   COALESCE(GROUP_CONCAT(a.nombre ORDER BY a.nombre SEPARATOR ' + '), '—') AS areas_txt
            FROM procesos p
            LEFT JOIN procesos_areas pa ON pa.proceso_id = p.id
            LEFT JOIN areas_produccion a ON a.id = pa.area_id
            WHERE p.empresa_id = %s
            GROUP BY p.id, p.nombre, p.descripcion
            ORDER BY areas_txt, p.nombre
        """, (eid,))
        procesos = cur.fetchall()

        # Insumos FILTRADOS
        cur.execute("""
            SELECT pi.id, pi.proceso_id, pi.unidad, pi.cantidad, pi.merma_pct,
                   m.id AS mercancia_id, m.nombre AS mercancia,
                   (SELECT mi.costo_unitario
                      FROM movimientos_inventario mi
                     WHERE mi.producto_id = pi.mercancia_id
                     ORDER BY mi.fecha DESC, mi.id DESC
                     LIMIT 1) AS costo_ref
            FROM procesos_insumos pi
            JOIN mercancia m ON m.id = pi.mercancia_id
            WHERE pi.empresa_id = %s
            ORDER BY m.nombre
        """, (eid,))
        items = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    return render_template(
        'admin/procesos/list.html',
        procesos=procesos, areas=areas,
        mercancias=mercancias, items=items, pts=pts
    )


# ---------- ETAPAS DEL PROCESO ----------
# ---------- /admin/procesos/<id>/etapas ----------
@app.route('/admin/procesos/<int:id>/etapas', methods=['GET','POST'], endpoint='admin_procesos_etapas')
def admin_procesos_etapas(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado','danger'); return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            cur.execute("""INSERT INTO procesos_etapas
                           (proceso_id, orden, area_id, nombre, descripcion)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (id,
                         request.form['orden'],
                         request.form['area_id'],
                         request.form.get('nombre',''),
                         request.form.get('descripcion','')))
            conn.commit()
            flash('Etapa agregada','success')

        cur.execute("SELECT id, nombre, descripcion FROM procesos WHERE id=%s", (id,))
        proceso = cur.fetchone()

        cur.execute("""SELECT pe.id, pe.orden, pe.nombre, a.nombre AS area
                       FROM procesos_etapas pe
                       JOIN areas_produccion a ON a.id = pe.area_id
                       WHERE pe.proceso_id=%s
                       ORDER BY pe.orden""", (id,))
        etapas = cur.fetchall()

        cur.execute("SELECT id, nombre FROM areas_produccion ORDER BY nombre")
        areas = cur.fetchall()
    finally:
        cur.close(); conn.close()

    return render_template('admin/procesos/etapas_form.html',
                           proceso=proceso, etapas=etapas, areas=areas)

# ---------- RECETA POR ETAPA ----------
# ---------- /admin/etapas/<etapa_id>/receta ----------
@app.route('/admin/etapas/<int:etapa_id>/receta', methods=['GET','POST'], endpoint='admin_etapa_receta')
def admin_etapa_receta(etapa_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado','danger'); return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            cur.execute("""INSERT INTO etapas_insumos
                           (etapa_id, mercancia_id, unidad, cantidad, merma_pct)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (etapa_id,
                         request.form['mercancia_id'],
                         request.form.get('unidad',''),
                         request.form['cantidad'],
                         request.form.get('merma_pct', 0)))
            conn.commit()
            flash('Insumo agregado','success')

        cur.execute("""SELECT pe.id, pe.nombre, pe.orden, p.nombre AS proceso
                       FROM procesos_etapas pe
                       JOIN procesos p ON p.id = pe.proceso_id
                       WHERE pe.id=%s""", (etapa_id,))
        etapa = cur.fetchone()

        cur.execute("""SELECT ei.id, m.nombre AS mercancia, ei.unidad, ei.cantidad, ei.merma_pct
                       FROM etapas_insumos ei
                       JOIN mercancia m ON m.id = ei.mercancia_id
                       WHERE ei.etapa_id=%s
                       ORDER BY ei.id""", (etapa_id,))
        items = cur.fetchall()

        cur.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
        mercancias = cur.fetchall()
    finally:
        cur.close(); conn.close()

    return render_template('admin/procesos/receta_form.html',
                           etapa=etapa, items=items, mercancias=mercancias)

# asumo: from flask import render_template, request, redirect, url_for, flash
# asumo: función conexion_db() ya existe y session['rol']=='admin' para admin


@app.route("/admin/procesos/<int:proceso_id>", methods=["GET"])
def ver_proceso(proceso_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger'); return redirect('/login')

    conn = conexion_db(); cur = conn.cursor(dictionary=True)

    # Proceso
    cur.execute("SELECT id, nombre, descripcion FROM procesos WHERE id=%s", (proceso_id,))
    p = cur.fetchone()
    if not p:
        cur.close(); conn.close()
        flash("Proceso no encontrado","warning"); return redirect(url_for("listar_procesos"))

    # Componentes (insumos)
    cur.execute("""
      SELECT pi.id, m.id AS mercancia_id, m.nombre AS componente,
             pi.unidad, pi.cantidad, pi.merma_pct,
             (SELECT mi.costo_unitario
                FROM movimientos_inventario mi
               WHERE mi.producto_id = pi.mercancia_id
               ORDER BY mi.fecha DESC, mi.id DESC LIMIT 1) AS costo_ref
      FROM procesos_insumos pi
      JOIN mercancia m ON m.id = pi.mercancia_id
      WHERE pi.proceso_id = %s
      ORDER BY m.nombre
    """, (proceso_id,))
    componentes = cur.fetchall()

    # Operaciones
    cur.execute("""
      SELECT id, nombre_operacion, tiempo_min, area_id
      FROM procesos_operaciones
      WHERE proceso_id=%s
      ORDER BY orden ASC, id ASC
    """, (proceso_id,))
    operaciones = cur.fetchall()

    # Subproductos
    cur.execute("""
      SELECT id, nombre, unidad, cantidad
      FROM procesos_subproductos
      WHERE proceso_id=%s
      ORDER BY id
    """, (proceso_id,))
    subproductos = cur.fetchall()

    cur.close(); conn.close()
    return render_template(
        "admin/procesos/proceso_detalle.html",
        p=p, componentes=componentes, operaciones=operaciones, subproductos=subproductos
    )


@app.route("/admin/procesos/nuevo", methods=["GET","POST"])
def nuevo_proceso():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger'); return redirect('/login')
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        descripcion = request.form.get("descripcion","").strip()
        conn = conexion_db(); cur = conn.cursor()
        cur.execute("INSERT INTO procesos (nombre, descripcion) VALUES (%s,%s)", (nombre, descripcion))
        conn.commit(); nid = cur.lastrowid; cur.close(); conn.close()
        flash("Proceso creado", "success"); return redirect(url_for("ver_proceso", proceso_id=nid))
    return render_template("admin/procesos/procesos_form.html", modo="nuevo")

@app.route("/admin/procesos/editar/<int:proceso_id>", methods=["GET","POST"])
def editar_proceso(proceso_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger'); return redirect('/login')
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        descripcion = request.form.get("descripcion","").strip()
        activo = 1 if request.form.get("activo")=="1" else 0
        cur.execute("UPDATE procesos SET nombre=%s, descripcion=%s, activo=%s WHERE id=%s",
                    (nombre, descripcion, activo, proceso_id))
        conn.commit(); cur.close(); conn.close()
        flash("Proceso actualizado", "success"); return redirect(url_for("ver_proceso", proceso_id=proceso_id))
    cur.execute("SELECT * FROM procesos WHERE id=%s", (proceso_id,))
    p = cur.fetchone(); cur.close(); conn.close()
    if not p:
        flash("Proceso no encontrado", "warning"); return redirect(url_for("listar_procesos"))
    return render_template("admin/procesos_form.html", modo="editar", p=p)








#   PT    INVENTORY 




# === RECETAS → ahora “Procesos de producción” por PT ===

@app.route('/recetas')
def recetas_legacy_redirect():
    return redirect(url_for('recetas_list'), code=301)

# ==================== RECETAS LIST ====================
@app.get('/pt/recetas')
@require_login
def recetas_list():
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT 
                m.id   AS pt_id,
                m.nombre AS pt_nombre,
                COUNT(p.id) AS procesos_totales,
                SUM(CASE WHEN p.activo = 1 THEN 1 ELSE 0 END) AS procesos_activos
            FROM mercancia m
            LEFT JOIN procesos p ON p.pt_id = m.id AND p.empresa_id = %s
            WHERE m.tipo = 'PT' AND m.empresa_id = %s
            GROUP BY m.id, m.nombre
            ORDER BY m.nombre
        """, (eid, eid))
        pts = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template('inventarios/PT/recetas_list.html', pts=pts)


# ==================== RECETAS PROCESO ====================
@app.route('/recetas/<int:pt_id>', methods=['GET','POST'])
@require_login
def recetas_proceso(pt_id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # PT - VALIDAR EMPRESA
        cur.execute("""
            SELECT id, nombre FROM mercancia 
            WHERE id=%s AND tipo='PT' AND empresa_id=%s
        """, (pt_id, eid))
        pt = cur.fetchone()
        if not pt:
            flash("PT no encontrado.", "danger")
            return redirect(url_for('recetas_list'))

        if request.method == 'POST':
            nombre = (request.form.get('nombre') or '').strip() or f"Proceso de {pt['nombre']}"
            descripcion = (request.form.get('descripcion') or '').strip()
            
            cur.execute("""
                SELECT id FROM procesos 
                WHERE pt_id=%s AND empresa_id=%s
            """, (pt_id, eid))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE procesos SET nombre=%s, descripcion=%s, activo=1 
                    WHERE id=%s AND empresa_id=%s
                """, (nombre, descripcion, row['id'], eid))
            else:
                cur.execute("""
                    INSERT INTO procesos (empresa_id, pt_id, nombre, descripcion, activo) 
                    VALUES (%s, %s, %s, %s, 1)
                """, (eid, pt_id, nombre, descripcion))
            conn.commit()
            flash("Proceso guardado.", "success")
            return redirect(url_for('recetas_proceso', pt_id=pt_id))

        # GET: cargar proceso + pasos + insumos
        cur.execute("""
            SELECT * FROM procesos 
            WHERE pt_id=%s AND empresa_id=%s
        """, (pt_id, eid))
        proceso = cur.fetchone()

        pasos, areas, mps, ums = [], [], [], []
        if proceso:
            cur.execute("""
                SELECT pp.*, a.nombre AS area_nombre
                FROM proceso_pasos pp
                LEFT JOIN areas_produccion a ON a.id=pp.area_id
                WHERE pp.proceso_id=%s
                ORDER BY pp.orden, pp.id
            """, (proceso['id'],))
            pasos = cur.fetchall()

            for p in pasos:
                cur.execute("""
                    SELECT pin.id, pin.cantidad_por_lote,
                           m.nombre AS mp_nombre, m.id AS mp_id,
                           u.nombre AS unidad
                    FROM paso_insumos pin
                    JOIN mercancia m ON m.id=pin.mp_id
                    LEFT JOIN unidades_medida u ON u.id=pin.unidad_id
                    WHERE pin.paso_id=%s AND m.empresa_id=%s
                """, (p['id'], eid))
                p['insumos'] = cur.fetchall()

        # Catálogos FILTRADOS
        cur.execute("""
            SELECT id, nombre FROM areas_produccion 
            WHERE empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        areas = cur.fetchall()
        
        cur.execute("""
            SELECT id, nombre FROM mercancia 
            WHERE tipo='MP' AND empresa_id=%s AND activo=1 
            ORDER BY nombre
        """, (eid,))
        mps = cur.fetchall()
        
        cur.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        ums = cur.fetchall()

        return render_template('inventarios/WIP/recetas_proceso.html',
                               pt=pt, proceso=proceso, pasos=pasos,
                               areas=areas, mps=mps, ums=ums)
    finally:
        cur.close()
        conn.close()


# ==================== AGREGAR PASO ====================
@app.post('/recetas/<int:pt_id>/pasos/agregar')
@require_login
def recetas_paso_agregar(pt_id):
    eid = g.empresa_id
    
    nombre = (request.form.get('nombre') or '').strip() or 'Paso'
    area_id_s = (request.form.get('area_id') or '').strip()
    requiere = 1 if (request.form.get('requiere_validez') == '1') else 0
    minutos_s = (request.form.get('minutos_estimados') or '').strip()
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT id FROM procesos 
            WHERE pt_id=%s AND empresa_id=%s
        """, (pt_id, eid))
        proc = cur.fetchone()
        if not proc:
            flash("Primero guarda el encabezado del proceso.", "warning")
            return redirect(url_for('recetas_proceso', pt_id=pt_id))

        area_id = int(area_id_s) if area_id_s.isdigit() else None
        minutos = int(minutos_s) if minutos_s.isdigit() else None

        cur.execute("""
            SELECT COALESCE(MAX(orden),0)+1 AS nexto 
            FROM proceso_pasos WHERE proceso_id=%s
        """, (proc['id'],))
        nexto = cur.fetchone()['nexto']
        
        cur.execute("""
            INSERT INTO proceso_pasos (proceso_id, orden, nombre, area_id, requiere_validez, minutos_estimados)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (proc['id'], nexto, nombre, area_id, requiere, minutos))
        conn.commit()
        flash("Paso agregado.", "success")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('recetas_proceso', pt_id=pt_id))


# ==================== AGREGAR INSUMO A PASO ====================
@app.post('/recetas/pasos/<int:paso_id>/insumos/agregar')
@require_login
def recetas_paso_insumo_agregar(paso_id):
    eid = g.empresa_id
    
    mp_id_s = (request.form.get('mp_id') or '').strip()
    cant_s = (request.form.get('cantidad_por_lote') or '').strip()
    um_s = (request.form.get('unidad_id') or '').strip()
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT pp.id, pr.pt_id
            FROM proceso_pasos pp
            JOIN procesos pr ON pr.id=pp.proceso_id
            WHERE pp.id=%s AND pr.empresa_id=%s
        """, (paso_id, eid))
        row = cur.fetchone()
        if not row:
            flash("Paso no encontrado.", "danger")
            return redirect(url_for('recetas_list'))

        if not (mp_id_s.isdigit() and cant_s):
            flash("Selecciona MP y cantidad.", "danger")
            return redirect(url_for('recetas_proceso', pt_id=row['pt_id']))

        # Validar MP pertenece a empresa
        cur.execute("""
            SELECT id FROM mercancia 
            WHERE id=%s AND empresa_id=%s
        """, (int(mp_id_s), eid))
        if not cur.fetchone():
            flash("Materia prima no válida.", "danger")
            return redirect(url_for('recetas_proceso', pt_id=row['pt_id']))

        um_id = int(um_s) if um_s.isdigit() else None
        cur.execute("""
            INSERT INTO paso_insumos (paso_id, mp_id, cantidad_por_lote, unidad_id)
            VALUES (%s, %s, %s, %s)
        """, (paso_id, int(mp_id_s), float(cant_s), um_id))
        conn.commit()
        flash("Insumo agregado.", "success")
        return redirect(url_for('recetas_proceso', pt_id=row['pt_id']))
    finally:
        cur.close()
        conn.close()


# ==================== ELIMINAR PASO ====================
@app.post('/recetas/pasos/<int:paso_id>/eliminar')
@require_login
def recetas_paso_eliminar(paso_id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT pr.pt_id
            FROM proceso_pasos pp
            JOIN procesos pr ON pr.id=pp.proceso_id
            WHERE pp.id=%s AND pr.empresa_id=%s
        """, (paso_id, eid))
        row = cur.fetchone()
        
        if row:
            cur.execute("DELETE FROM proceso_pasos WHERE id=%s", (paso_id,))
            conn.commit()
            flash("Paso eliminado.", "success")
            return redirect(url_for('recetas_proceso', pt_id=row['pt_id']))
        else:
            flash("Paso no encontrado.", "warning")
            return redirect(url_for('recetas_list'))
    finally:
        cur.close()
        conn.close()


# ==================== ELIMINAR RECETA ====================
@app.route('/recetas/<int:id>/eliminar', methods=['POST'])
@require_login
def eliminar_receta(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM recipes 
            WHERE id=%s AND empresa_id=%s
        """, (id, eid))
        conn.commit()
        flash('Ingrediente eliminado de la receta.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'No se pudo eliminar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('recetas_list'))


# ==================== EDITAR RECETA ====================
@app.route('/recetas/<int:id>/editar', methods=['GET','POST'])
@require_login
def editar_receta(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        material_id = request.form['material_id']
        quantity = request.form['quantity']
        unit = request.form['unit']
        try:
            cur.execute("""
                UPDATE recipes
                SET product_id=%s, material_id=%s, quantity=%s, unit=%s
                WHERE id=%s AND empresa_id=%s
            """, (product_id, material_id, quantity, unit, id, eid))
            conn.commit()
            flash('Receta actualizada.', 'success')
            return redirect(url_for('recetas_list'))
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar: {e}', 'danger')
        finally:
            cur.close()
            conn.close()
            return redirect(url_for('editar_receta', id=id))

    # GET
    cur.execute("""
        SELECT id, product_id, material_id, quantity, unit 
        FROM recipes WHERE id=%s AND empresa_id=%s
    """, (id, eid))
    receta = cur.fetchone()
    if not receta:
        cur.close()
        conn.close()
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('recetas_list'))

    # Catálogos FILTRADOS
    cur.execute("""
        SELECT id, nombre FROM mercancia 
        WHERE tipo='PT' AND empresa_id=%s 
        ORDER BY nombre
    """, (eid,))
    productos = cur.fetchall()
    
    cur.execute("""
        SELECT id, nombre FROM mercancia 
        WHERE tipo='MP' AND empresa_id=%s 
        ORDER BY nombre
    """, (eid,))
    materiales = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('inventarios/PT/recetas_editar.html',
                           receta=receta, productos=productos, materiales=materiales)

@app.route("/productos_terminados", methods=["GET", "POST"])
@require_login
def productos_terminados():
    """Agregar y listar Productos Terminados (PT)"""
    eid = g.empresa_id
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        
        if not nombre:
            flash("⚠️ El nombre no puede estar vacío", "warning")
            return redirect(url_for("productos_terminados"))

        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT id, nombre FROM mercancia 
                WHERE UPPER(TRIM(nombre)) = UPPER(%s) AND empresa_id = %s
                LIMIT 1
            """, (nombre, eid))
            duplicado = cursor.fetchone()
            
            if duplicado:
                flash(f"⚠️ Ya existe '{duplicado['nombre']}' (ID: {duplicado['id']})", 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for("productos_terminados"))
            
            cursor.execute("""
                INSERT INTO mercancia 
                (nombre, tipo, tipo_inventario_id, precio, unidad_id, cont_neto, iva, ieps, activo, empresa_id)
                VALUES (%s, 'PT', 3, 0.00, 1, 1, 0, 0, 1, %s)
            """, (nombre, eid))
            
            mid = cursor.lastrowid
            
            cursor.execute("""
                INSERT IGNORE INTO inventario
                (mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base, empresa_id)
                VALUES (%s, 0, 0, 0, 0, 0, %s)
            """, (mid, eid))
            
            cursor.execute("""
                INSERT INTO pt_precios (mercancia_id, modo, markup_pct)
                VALUES (%s, 'auto', 0.30)
            """, (mid,))
            
            conn.commit()
            flash(f"✅ Producto '{nombre}' agregado correctamente", "success")
            
        except Exception as e:
            conn.rollback()
            flash(f"❌ Error: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for("productos_terminados"))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nombre, precio
        FROM mercancia 
        WHERE tipo_inventario_id = 3 AND empresa_id = %s AND activo = 1
        ORDER BY nombre
    """, (eid,))
    productos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("inventarios/PT/productos_terminados.html", productos=productos)





#        PRODUCTO     TERMINADO      #




@app.route('/inventario/pt')
def inventario_pt_view():
    inventario = _inventario_por_tipo(3)   # PT
    return render_template('inventarios/pt/inventario.html',
                           inventario=inventario)

@app.post("/pt/catalogo/set_modo_masivo")
def pt_set_modo_masivo():
    modo = request.form.get("modo")
    ids  = request.form.getlist("ids[]")

    if not ids or modo not in ("manual", "auto"):
        flash("Selecciona al menos un producto y un modo válido.", "warning")
        return redirect(url_for("pt_catalogo"))

    ids_int = [int(x) for x in ids]

    conn = conexion_db()
    cur = conn.cursor()

    fmt = ",".join(["%s"] * len(ids_int))

    # actualizar modo
    cur.execute(f"""
        UPDATE pt_precios
        SET modo = %s
        WHERE mercancia_id IN ({fmt})
    """, (modo, *ids_int))

    # asegurar filas faltantes
    cur.execute(f"""
        INSERT INTO pt_precios (mercancia_id, modo)
        SELECT m.id, %s
        FROM mercancia m
        LEFT JOIN pt_precios p ON p.mercancia_id = m.id
        WHERE m.id IN ({fmt}) AND p.mercancia_id IS NULL
    """, (modo, *ids_int))

    conn.commit()
    cur.close()
    conn.close()

    flash(f"{len(ids_int)} productos actualizados a {modo.upper()}.", "success")
    return redirect(url_for("pt_catalogo"))

@app.route('/mercancia/pt')
def mercancia_pt():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db(); cur = conn.cursor(dictionary=True)

    # Productos Terminados
    cur.execute("""
        SELECT p.id, p.nombre, p.cont_neto,
               u.nombre  AS unidad,
               p.iva, p.ieps,
               c.codigo  AS codigo_padre,  c.nombre  AS nombre_padre,
               sc.id AS subcuenta_id,
               sc.codigo AS codigo_sub,    sc.nombre AS nombre_sub,
               CONCAT(sc.codigo, ' - ', sc.nombre) AS cuenta_asignada
        FROM mercancia p
        LEFT JOIN unidades_medida u    ON p.unidad_id    = u.id
        LEFT JOIN cuentas_contables c  ON p.cuenta_id    = c.id
        LEFT JOIN cuentas_contables sc ON p.subcuenta_id = sc.id
        WHERE p.tipo = 'PT'
        ORDER BY p.nombre ASC
    """)
    productos = cur.fetchall()

    # Presentaciones
    cur.execute("""
        SELECT mercancia_id,
               GROUP_CONCAT(CONCAT(contenido_neto,' ',unidad) ORDER BY contenido_neto SEPARATOR ', ') AS presentaciones
        FROM presentaciones
        GROUP BY mercancia_id
    """)
    pres_map = {r['mercancia_id']: r['presentaciones'] for r in cur.fetchall()}
    for it in productos:
        it['presentaciones'] = pres_map.get(it['id'], '')

    cur.close(); conn.close()
    return render_template('mercancia.html',
                           titulo='Productos Terminados (PT)',
                           solo_listado=True,
                           unidades=[],
                           productos=productos,
                           cuentas_catalogo=[])

@app.post("/pt/catalogo_reordenar")
@require_login
def pt_catalogo_reordenar():
    """Actualiza el orden de productos PT por empresa."""
    data = request.get_json() or []
    eid = g.empresa_id  # ← empresa activa en sesión

    conn = conexion_db()
    cur = conn.cursor()
    for row in data:
        cur.execute("""
            UPDATE pt_precios
            SET orden_pos = %s
            WHERE mercancia_id = %s AND empresa_id = %s
        """, (int(row["orden_pos"]), int(row["id"]), eid))
    conn.commit()
    cur.close()
    conn.close()
    return "ok"




#   VENTAS  #




@app.route('/productos_venta')
@require_login
def productos_venta():
    eid = g.empresa_id
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nombre, precio 
        FROM mercancia 
        WHERE empresa_id = %s AND activo = 1
        ORDER BY nombre
    """, (eid,))
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('productos_venta.html', productos=productos)

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d %B %Y'):
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d')
    return value.strftime(format)



#    COMPRAS    #




def registrar_asiento_compra(cursor, conn, concepto, movimientos):
    cursor.execute("""
        INSERT INTO asientos_contables (fecha, concepto)
        VALUES (NOW(), %s)
    """, (concepto,))
    asiento_id = cursor.lastrowid

    for mov in movimientos:
        cursor.execute("""
            INSERT INTO asientos_detalle (asiento_id, cuenta_id, debe, haber)
            VALUES (%s, %s, %s, %s)
        """, (asiento_id, mov["cuenta_id"], mov["debe"], mov["haber"]))

    # NO hacer commit aquí
    return asiento_id

@app.route('/nueva_compra', methods=['GET', 'POST'])
@require_login
def nueva_compra():
    """Registrar nueva compra - MULTIEMPRESA"""
    
    # Solo admin
    if session.get('rol') != 'admin':
        flash('Acceso denegado. Solo el administrador puede registrar compras.', 'danger')
        return redirect('/login')

    eid = g.empresa_id
    uid = g.usuario_id

    if request.method == 'POST':
        proveedor      = (request.form.get('proveedor') or '').strip()
        fecha          = (request.form.get('fecha') or '').strip()
        numero_factura = (request.form.get('numero_factura') or '').strip()
        metodo_pago    = (request.form.get('metodo_pago') or 'efectivo').strip()
        observaciones  = (request.form.get('observaciones') or '').strip()

        nombres  = request.form.getlist('mercancia_nombre[]')
        mids     = request.form.getlist('mercancia_id[]')
        unidades = request.form.getlist('unidades[]')
        precios  = request.form.getlist('precio_unitario[]')
        totales  = request.form.getlist('precio_total[]')

        if not proveedor or not fecha or not numero_factura:
            flash('Proveedor, fecha y número de factura son obligatorios.', 'danger')
            return redirect(url_for('nueva_compra'))

        conn = conexion_db()
        cur = conn.cursor(dictionary=True)
        
        try:
            items = []
            productos_fallidos = []

            # ✅ VALIDAR PROVEEDOR PERTENECE A LA EMPRESA
            cur.execute("""
                SELECT id, nombre 
                FROM proveedores 
                WHERE nombre = %s AND empresa_id = %s
            """, (proveedor, eid))
            prov = cur.fetchone()
            if not prov:
                flash(f'⚠️ El proveedor "{proveedor}" no existe en tu empresa. Regístralo primero.', 'warning')
                return redirect(url_for('nueva_compra'))

            # ✅ PROCESAR ITEMS
            for i in range(max(len(nombres), len(unidades), len(precios), len(totales))):
                nom  = (nombres[i]  if i < len(nombres)  else "").strip()
                midS = (mids[i]     if i < len(mids)     else "").strip()
                undS = (unidades[i] if i < len(unidades) else "").strip()
                puS  = (precios[i]  if i < len(precios)  else "").strip()
                ptS  = (totales[i]  if i < len(totales)  else "").strip()

                # Saltar filas vacías
                if not nom and not undS and not puS and not ptS:
                    continue

                # ✅ RESOLVER MERCANCÍA CON VALIDACIÓN DE EMPRESA
                try:
                    if midS and midS.isdigit():
                        mercancia_id = int(midS)
                    else:
                        # Buscar por nombre en esta empresa
                        cur.execute("""
                            SELECT id FROM mercancia 
                            WHERE nombre = %s AND empresa_id = %s AND tipo = 'MP' AND activo = 1
                            LIMIT 1
                        """, (nom, eid))
                        m = cur.fetchone()
                        if not m:
                            productos_fallidos.append(f"'{nom}': No encontrado en catálogo")
                            continue
                        mercancia_id = m['id']

                    # ✅ VALIDAR PERTENENCIA A EMPRESA Y PRODUCTO_BASE
                    cur.execute("""
                        SELECT m.id, m.nombre, m.producto_base_id, m.cont_neto, pb.nombre AS pb_nombre
                        FROM mercancia m
                        LEFT JOIN producto_base pb ON pb.id = m.producto_base_id
                        WHERE m.id = %s AND m.empresa_id = %s AND m.tipo = 'MP'
                    """, (mercancia_id, eid))
                    merc = cur.fetchone()
                    
                    if not merc:
                        productos_fallidos.append(f"'{nom}': No pertenece a tu empresa")
                        continue
                    if not merc['producto_base_id']:
                        productos_fallidos.append(f"'{nom}': Sin producto base asignado")
                        continue

                except Exception as e:
                    productos_fallidos.append(f"'{nom}': {str(e)}")
                    continue

                # ✅ CALCULAR CANTIDADES
                try:
                    cont_neto = float(merc['cont_neto'] or 1)
                    if cont_neto <= 0:
                        cont_neto = 1
                except:
                    cont_neto = 1

                try:
                    und = float(undS or 0)
                    pu  = float(puS or 0)
                    pt  = float(ptS or (und * pu))
                except ValueError:
                    productos_fallidos.append(f"'{nom}': Valores numéricos inválidos")
                    continue

                if und <= 0 or pu <= 0:
                    productos_fallidos.append(f"'{nom}': Unidades y precio deben ser mayores a 0")
                    continue

                items.append({
                    "mercancia_id": mercancia_id,
                    "nombre": merc['nombre'],
                    "unidades_base": und,
                    "contenido_neto_total": und * cont_neto,
                    "precio_unitario": pu,
                    "precio_total": pt
                })

            # ✅ VALIDAR QUE HAY ITEMS
            if productos_fallidos:
                flash(f"⚠️ Productos omitidos: {', '.join(productos_fallidos)}", "warning")

            if not items:
                conn.rollback()
                flash("No hay productos válidos para registrar.", "danger")
                return redirect(url_for('nueva_compra'))

            # ✅ CALCULAR TOTALES
            subtotal = sum(x["precio_total"] for x in items)
            iva = subtotal * 0.16  # Ajustar según tu país
            total_general = subtotal + iva

            # ✅ INSERTAR ENCABEZADO DE COMPRA
            cur.execute("""
                INSERT INTO listado_compras 
                (empresa_id, usuario_id, proveedor, fecha, numero_factura, subtotal, iva, total, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (eid, uid, proveedor, fecha, numero_factura, subtotal, iva, total_general, observaciones))
            compra_id = cur.lastrowid

            # ✅ REGISTRAR CRÉDITO SI APLICA
            if metodo_pago == 'credito':
                cur.execute("""
                    INSERT INTO compras_credito
                    (empresa_id, usuario_id, compra_id, fecha, numero_documento, proveedor, importe, iva, total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (eid, uid, compra_id, fecha, numero_factura, proveedor, subtotal, iva, total_general))

            # ✅ ASIENTO CONTABLE (si la función lo soporta)
            try:
                cuenta_pago = 30 if metodo_pago == "efectivo" else 40 if metodo_pago == "banco" else 30
                movimientos = [
                    {"cuenta_id": 10, "debe": float(total_general), "haber": 0},
                    {"cuenta_id": cuenta_pago, "debe": 0, "haber": float(total_general)}
                ]
                registrar_asiento_compra(cur, conn, f"Compra {numero_factura}", movimientos)
            except Exception as e:
                print(f"⚠️ Advertencia asiento contable: {e}")

            # ✅ INSERTAR DETALLE + ACTUALIZAR INVENTARIO
            for x in items:
                # Detalle de compra
                cur.execute("""
                    INSERT INTO detalle_compra
                    (empresa_id, usuario_id, compra_id, mercancia_id, producto, unidades, 
                     contenido_neto_total, precio_unitario, precio_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (eid, uid, compra_id, x["mercancia_id"], x["nombre"], x["unidades_base"],
                      x["contenido_neto_total"], x["precio_unitario"], x["precio_total"]))

                # Actualizar stock (tabla inventario)
                cur.execute("""
                    INSERT INTO inventario
                    (empresa_id, mercancia_id, inventario_inicial, entradas, salidas, aprobado)
                    VALUES (%s, %s, 0, %s, 0, 0)
                    ON DUPLICATE KEY UPDATE
                    entradas = entradas + VALUES(entradas)
                """, (eid, x["mercancia_id"], x["contenido_neto_total"]))

                # Movimiento de inventario (MP = tipo_inventario_id=1)
                cur.execute("""
                    INSERT INTO inventario_movimientos
                    (empresa_id, usuario_id, tipo_inventario_id, mercancia_id, tipo_movimiento, 
                     unidades, precio_unitario, referencia, fecha)
                    VALUES (%s, %s, 1, %s, 'COMPRA', %s, %s, %s, %s)
                """, (eid, uid, x["mercancia_id"], x["contenido_neto_total"], 
                      x["precio_unitario"], f"Compra {numero_factura}", fecha))

            conn.commit()
            flash(f"✅ Compra #{compra_id} registrada exitosamente. Stock actualizado.", "success")
            return redirect(url_for('detalle_compra', id=compra_id))

        except Exception as e:
            conn.rollback()
            print(f"[ERROR] /nueva_compra POST: {e}")
            import traceback
            traceback.print_exc()
            flash(f"❌ Error al registrar compra: {e}", "danger")
            return redirect(url_for('nueva_compra'))
            
        finally:
            try:
                cur.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass

    # ========== GET ==========
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # ✅ CATÁLOGOS FILTRADOS POR EMPRESA
        cur.execute("""
            SELECT nombre 
            FROM proveedores 
            WHERE empresa_id = %s AND activo = 1
            ORDER BY nombre
        """, (eid,))
        proveedores = cur.fetchall()
        
        cur.execute("""
            SELECT m.id, m.nombre, pb.nombre as producto_base_nombre
            FROM mercancia m
            JOIN producto_base pb ON pb.id = m.producto_base_id
            WHERE m.empresa_id = %s
              AND m.tipo = 'MP'
              AND m.producto_base_id IS NOT NULL
              AND m.activo = 1
            ORDER BY m.nombre
        """, (eid,))
        productos = cur.fetchall()
        
    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

    return render_template('nueva_compra.html', proveedores=proveedores, productos=productos)
    
@app.route('/detalle_compra/<int:id>')
@require_login
def detalle_compra(id):
    """Detalle de una compra - VALIDADO POR EMPRESA"""
    
    # Solo admin
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ ENCABEZADO (validar pertenencia a la empresa)
        cursor.execute("""
            SELECT 
                id,
                proveedor,
                DATE_FORMAT(fecha, '%%d %%b %%Y') AS fecha_fmt,
                fecha,
                numero_factura,
                subtotal,
                iva,
                total,
                COALESCE(tipo_cambio, 1) as tipo_cambio,
                COALESCE(moneda, 'MXN') as moneda,
                observaciones
            FROM listado_compras
            WHERE id = %s
              AND empresa_id = %s
        """, (id, eid))
        compra = cursor.fetchone()

        if not compra:
            flash('Compra no encontrada o no pertenece a tu empresa.', 'warning')
            return redirect(url_for('listado_compras'))

        # ✅ DETALLE (filtrado por empresa)
        cursor.execute("""
            SELECT
                dc.id,
                COALESCE(m.nombre, dc.producto) AS producto,
                dc.unidades,
                dc.contenido_neto_total,
                dc.precio_unitario,
                dc.precio_total,
                dc.iva as iva_detalle,
                um.nombre as unidad_medida,
                um.abreviatura as unidad_abrev
            FROM detalle_compra dc
            LEFT JOIN mercancia m ON m.id = dc.mercancia_id
            LEFT JOIN unidades_medida um ON um.id = dc.unidad_medida_id
            WHERE dc.compra_id = %s
              AND dc.empresa_id = %s
            ORDER BY dc.id
        """, (id, eid))
        detalles = cursor.fetchall()

    except Exception as e:
        print(f"[ERROR] /detalle_compra/{id}: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error cargando detalle de compra: {e}", "danger")
        return redirect(url_for('listado_compras'))
        
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

    return render_template('detalle_compra_popup.html',
                           compra=compra,
                           detalles=detalles)

@app.route('/listado_compras')
@require_login
def listado_compras():
    """Listado de compras - FILTRADO POR EMPRESA"""
    eid = g.empresa_id  # ✅ Empresa activa
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # ✅ FILTRAR POR EMPRESA
        cur.execute("""
            SELECT
                id,
                DATE_FORMAT(fecha, '%%d %%b %%Y') AS fecha_fmt,
                proveedor,
                numero_factura,
                total
            FROM listado_compras
            WHERE empresa_id = %s
            ORDER BY id DESC
        """, (eid,))
        compras = cur.fetchall()
        
    except Exception as e:
        print(f"[ERROR] /listado_compras: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Error consultando compras: {e}", "danger")
        compras = []
        
    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

    return render_template('compras/listado_compras.html', compras=compras)

@app.route('/editar_compra/<int:id>', methods=['GET', 'POST'])
@require_login
def editar_compra(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        proveedor = request.form['proveedor']
        fecha = request.form['fecha']
        numero_factura = request.form['numero_factura']
        total = request.form['total']

        cursor.execute("""
            UPDATE listado_compras
            SET proveedor=%s, fecha=%s, numero_factura=%s, total=%s
            WHERE id=%s AND empresa_id=%s
        """, (proveedor, fecha, numero_factura, total, id, eid))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Compra actualizada correctamente.', 'success')
        return redirect('/listado_compras')

    cursor.execute("""
        SELECT * FROM listado_compras 
        WHERE id = %s AND empresa_id = %s
    """, (id, eid))
    compra = cursor.fetchone()
    cursor.close()
    conn.close()

    if not compra:
        flash('Compra no encontrada.', 'warning')
        return redirect('/listado_compras')

    return render_template('editar_compra.html', compra=compra)

@app.route('/eliminar_compra/<int:id>', methods=['POST'])
@require_login
def eliminar_compra(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar pertenencia
        cursor.execute("""
            SELECT numero_factura FROM listado_compras 
            WHERE id = %s AND empresa_id = %s
        """, (id, eid))
        compra = cursor.fetchone()
        
        if not compra:
            flash('Compra no encontrada.', 'warning')
            return redirect('/listado_compras')

        numero_factura = compra['numero_factura']

        # Restar entradas del inventario
        cursor.execute("""
            UPDATE inventario i
            JOIN detalle_compra dc ON dc.mercancia_id = i.mercancia_id AND dc.empresa_id = i.empresa_id
            SET i.entradas = GREATEST(0, i.entradas - dc.contenido_neto_total)
            WHERE dc.compra_id = %s AND dc.empresa_id = %s
        """, (id, eid))

        # Eliminar movimientos
        cursor.execute("""
            DELETE FROM inventario_movimientos 
            WHERE tipo_movimiento = 'COMPRA' 
              AND referencia = %s
              AND empresa_id = %s
        """, (numero_factura, eid))

        # Eliminar detalles
        cursor.execute("""
            DELETE FROM detalle_compra 
            WHERE compra_id = %s AND empresa_id = %s
        """, (id, eid))

        # Eliminar crédito
        cursor.execute("""
            DELETE FROM compras_credito 
            WHERE compra_id = %s AND empresa_id = %s
        """, (id, eid))

        # Eliminar encabezado
        cursor.execute("""
            DELETE FROM listado_compras 
            WHERE id = %s AND empresa_id = %s
        """, (id, eid))

        conn.commit()
        flash('✅ Compra eliminada completamente.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect('/listado_compras')

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_producto():
    """
    Permite al admin agregar un nuevo producto manualmente.
    """
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado. Solo el administrador puede agregar productos.', 'danger')
        return redirect('/inventario')

    if request.method == 'POST':
        producto = request.form['producto']
        inicial = int(request.form['inicial'])
        entradas = int(request.form['entradas'])
        salidas = int(request.form['salidas'])
        conn = conexion_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventario (producto, inventario_inicial, entradas, salidas) VALUES (%s, %s, %s, %s)",
            (producto, inicial, entradas, salidas))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/inventario')

    return render_template('agregar.html')

from flask import jsonify  # si faltaba

@app.route("/check_producto/<path:nombre>", methods=["GET"], endpoint="check_producto_api")
def check_producto_api(nombre):
    n = (nombre or "").strip()
    if not n:
        return jsonify({"existe": False})

    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        # exacto
        cur.execute("SELECT 1 FROM mercancia WHERE nombre=%s LIMIT 1", (n,))
        if cur.fetchone():
            return jsonify({"existe": True})

        # flexible por tokens
        tokens = [t for t in n.split() if t]
        patron = "%" + "%".join(tokens) + "%"
        cur.execute("SELECT 1 FROM mercancia WHERE nombre LIKE %s LIMIT 1", (patron,))
        return jsonify({"existe": bool(cur.fetchone())})
    finally:
        cur.close(); conn.close()





#   COMPRAS - MERCANCIA  #




# 1) LISTAR / CREAR MERCANCÍA
@app.route('/mercancia', methods=['GET', 'POST'])
@require_login
def mercancia():
    eid = g.empresa_id
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        
        # Validar duplicado EN ESTA EMPRESA
        cursor.execute("""
            SELECT id, nombre 
            FROM mercancia 
            WHERE UPPER(TRIM(nombre)) = UPPER(%s) AND empresa_id = %s
            LIMIT 1
        """, (nombre, eid))
        duplicado = cursor.fetchone()
        
        if duplicado:
            flash(f"⚠️ Ya existe '{duplicado['nombre']}' (ID: {duplicado['id']})", 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('mercancia'))
        
        cont_s = (request.form.get('cont_neto') or '0').strip()
        unidad_id = int(request.form['unidad_id'])
        iva = int(request.form.get('iva') or 0)
        ieps = int(request.form.get('ieps') or 0)
        catalogo_id_s = request.form.get('catalogo_id') or ''
        catalogo_nuevo = (request.form.get('catalogo_nuevo') or '').strip()
        producto_base_id = (
            int(request.form['producto_base_id'])
            if request.form.get('producto_base_id') and request.form['producto_base_id'].isdigit()
            else None
        )
        producto_base_nuevo = (request.form.get('producto_base_nuevo') or '').strip()

        try:
            try:
                cont_neto = Decimal(cont_s)
                if cont_neto <= 0:
                    raise InvalidOperation
            except InvalidOperation:
                raise ValueError("Contenido Neto inválido")

            cursor.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
            if not cursor.fetchone():
                raise ValueError("Unidad de medida inválida")

            catalogo_id = int(catalogo_id_s) if catalogo_id_s.isdigit() else None
            if not catalogo_id and catalogo_nuevo:
                catalogo_id = get_or_create_catalogo(cursor, conn, catalogo_nuevo, tipo='MP')

            if not producto_base_id and producto_base_nuevo:
                cursor.execute("""
                    INSERT INTO producto_base (empresa_id, nombre, unidad_id, activo)
                    VALUES (%s, %s, %s, 1)
                """, (eid, producto_base_nuevo, unidad_id))
                conn.commit()
                producto_base_id = cursor.lastrowid

            cursor.execute("""
                SELECT id FROM cuentas_contables
                WHERE nivel=2 AND empresa_id = %s
                ORDER BY codigo
                LIMIT 1
            """, (eid,))
            row = cursor.fetchone()
            cuenta_padre_id = row["id"] if row else None

            # Obtener mínimo de existencia
            minimo_existencia = request.form.get('minimo_existencia', '0').strip()
            try:
                minimo_existencia = Decimal(minimo_existencia) if minimo_existencia else Decimal('0')
            except:
                minimo_existencia = Decimal('0')

            # Obtener máximo de existencia
            maximo_existencia = request.form.get('maximo_existencia', '0').strip()
            try:
                maximo_existencia = Decimal(maximo_existencia) if maximo_existencia else Decimal('0')
            except:
                maximo_existencia = Decimal('0')

            # INSERT CON EMPRESA_ID
            cursor.execute("""
                INSERT INTO mercancia
                    (empresa_id, nombre, tipo, unidad_id, cont_neto, iva, ieps,
                     cuenta_id, subcuenta_id, catalogo_id, producto_base_id, 
                     minimo_existencia, maximo_existencia)
                VALUES (%s, %s, 'MP', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (eid, nombre, unidad_id, str(cont_neto), iva, ieps,
                  cuenta_padre_id, None, catalogo_id, producto_base_id, 
                  str(minimo_existencia), str(maximo_existencia)))
            mid = cursor.lastrowid

            cursor.execute("""
                INSERT IGNORE INTO inventario
                    (empresa_id, mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base)
                VALUES (%s, %s, 0, 0, 0, 0, 0)
            """, (eid, mid))

            cursor.execute("SELECT nombre FROM unidades_medida WHERE id=%s", (unidad_id,))
            um = cursor.fetchone()
            unidad_nombre = (um['nombre'] if um else '').lower()
            desc = f"{nombre} {cont_neto} {unidad_nombre}" if unidad_nombre else f"{nombre} {cont_neto}"
            cursor.execute("""
                INSERT IGNORE INTO presentaciones
                    (empresa_id, mercancia_id, descripcion, contenido_neto, unidad, factor_conversion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (eid, mid, desc, str(cont_neto), unidad_nombre, str(cont_neto)))

            conn.commit()
            flash(f'✅ Producto registrado correctamente.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'❌ No se pudo registrar el producto: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('mercancia'))

    # GET: Listas FILTRADAS POR EMPRESA
    try:
        cursor.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        unidades = cursor.fetchall()

        cursor.execute("""
            SELECT p.id, p.nombre, p.cont_neto,
                   u.nombre AS unidad, p.iva, p.ieps,
                   p.catalogo_id, p.producto_base_id,
                   p.minimo_existencia, p.maximo_existencia,
                   sc.id AS subcuenta_id,
                   CONCAT(sc.codigo, ' - ', sc.nombre) AS cuenta_asignada
            FROM mercancia p
            LEFT JOIN unidades_medida u ON p.unidad_id = u.id
            LEFT JOIN cuentas_contables sc ON p.subcuenta_id = sc.id
            WHERE p.empresa_id = %s
            ORDER BY p.nombre ASC
        """, (eid,))
        productos = cursor.fetchall()

        cursor.execute("""
            SELECT id, nombre
            FROM catalogo_inventario
            WHERE activo=1 AND tipo='MP' AND empresa_id = %s
            ORDER BY nombre
        """, (eid,))
        catalogos = cursor.fetchall()

        cursor.execute("""
            SELECT id, nombre
            FROM producto_base
            WHERE activo=1 AND empresa_id = %s
            ORDER BY nombre
        """, (eid,))
        productos_base = cursor.fetchall()

        cursor.execute("""
            SELECT id, CONCAT(codigo, ' - ', nombre) AS etiqueta
            FROM cuentas_contables
            WHERE nivel = 3 AND empresa_id = %s
            ORDER BY codigo
        """, (eid,))
        cuentas_catalogo = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('mercancia.html',
                           unidades=unidades,
                           productos=productos,
                           cuentas_catalogo=cuentas_catalogo,
                           catalogos=catalogos,
                           productos_base=productos_base)

## 2) ACTUALIZAR MERCANCÍA (tu bloque, sin cambios funcionales)
@app.route('/mercancia/<int:id>', methods=['POST'], endpoint='actualizar_mercancia')
@require_login
def actualizar_mercancia(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        nombre = request.form['nombre'].strip()
        unidad_id = int(request.form['unidad_id'])
        iva_s = str(request.form.get('iva', '0')).strip()
        ieps_s = str(request.form.get('ieps', '0')).strip()
        cont_s = (request.form.get('cont_neto') or '0').strip()
        sub_s = request.form.get('subcuenta_id') or ''

        cur.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
        if not cur.fetchone():
            raise ValueError("Unidad de medida inválida")

        try:
            cont_neto = Decimal(cont_s)
            if cont_neto <= 0:
                raise InvalidOperation
        except InvalidOperation:
            raise ValueError("Contenido Neto inválido")

        iva = int(iva_s) if iva_s.isdigit() else 0
        ieps = int(ieps_s) if ieps_s.isdigit() else 0
        subcuenta_id = int(sub_s) if sub_s.isdigit() else None

        cuenta_padre_id = None
        if subcuenta_id:
            cur.execute("SELECT padre_id FROM cuentas_contables WHERE id=%s", (subcuenta_id,))
            r = cur.fetchone()
            if r and r['padre_id']:
                cuenta_padre_id = r['padre_id']

        catalogo_id_s = request.form.get('catalogo_id') or ''
        catalogo_nuevo = (request.form.get('catalogo_nuevo') or '').strip()
        catalogo_id = int(catalogo_id_s) if catalogo_id_s.isdigit() else None
        if not catalogo_id and catalogo_nuevo:
            catalogo_id = get_or_create_catalogo(cur, conn, catalogo_nuevo, tipo='MP')

        producto_base_id = (
            int(request.form['producto_base_id'])
            if request.form.get('producto_base_id') and request.form['producto_base_id'].isdigit()
            else None
        )
        producto_base_nuevo = (request.form.get('producto_base_nuevo') or '').strip()
        
        if not producto_base_id and producto_base_nuevo:
            cur.execute("""
                INSERT INTO producto_base (empresa_id, nombre, unidad_id, activo)
                VALUES (%s, %s, %s, 1)
            """, (eid, producto_base_nuevo, unidad_id))
            conn.commit()
            producto_base_id = cur.lastrowid

        # Obtener mínimo de existencia
        minimo_existencia = request.form.get('minimo_existencia', '0').strip()
        try:
            minimo_existencia = Decimal(minimo_existencia) if minimo_existencia else Decimal('0')
        except:
            minimo_existencia = Decimal('0')

        # Obtener máximo de existencia
        maximo_existencia = request.form.get('maximo_existencia', '0').strip()
        try:
            maximo_existencia = Decimal(maximo_existencia) if maximo_existencia else Decimal('0')
        except:
            maximo_existencia = Decimal('0')

        # UPDATE VALIDANDO EMPRESA
        cur.execute("""
            UPDATE mercancia
            SET nombre=%s,
                cont_neto=%s,
                unidad_id=%s,
                iva=%s,
                ieps=%s,
                subcuenta_id=%s,
                cuenta_id=COALESCE(%s, cuenta_id),
                catalogo_id=%s,
                producto_base_id=%s,
                minimo_existencia=%s,
                maximo_existencia=%s
            WHERE id=%s AND empresa_id=%s
        """, (nombre, str(cont_neto), unidad_id, iva, ieps, subcuenta_id,
              cuenta_padre_id, catalogo_id, producto_base_id, 
              str(minimo_existencia), str(maximo_existencia), id, eid))

        cur.execute("""
            INSERT IGNORE INTO inventario
                (empresa_id, mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base)
            VALUES (%s, %s, 0, 0, 0, 0, 0)
        """, (eid, id))

        cur.execute("SELECT nombre FROM unidades_medida WHERE id=%s", (unidad_id,))
        um = cur.fetchone()
        unidad_nombre = (um['nombre'] if um else '').lower()
        desc = f"{nombre} {cont_neto} {unidad_nombre}" if unidad_nombre else f"{nombre} {cont_neto}"
        cur.execute("""
            INSERT IGNORE INTO presentaciones
                (empresa_id, mercancia_id, descripcion, contenido_neto, unidad, factor_conversion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (eid, id, desc, str(cont_neto), unidad_nombre, str(cont_neto)))

        conn.commit()
        flash('✅ Mercancía actualizada correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'❌ No se pudo actualizar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('mercancia'))

@app.route('/mercancia/<int:id>/eliminar', methods=['POST'])
@require_login
def eliminar_mercancia(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor()
    try:
        # Validar pertenencia
        cur.execute("SELECT 1 FROM mercancia WHERE id=%s AND empresa_id=%s", (id, eid))
        if not cur.fetchone():
            flash('Producto no encontrado.', 'warning')
            return redirect(url_for('mercancia'))
        
        cur.execute("DELETE FROM inventario_movimientos WHERE mercancia_id=%s AND empresa_id=%s", (id, eid))
        cur.execute("DELETE FROM detalle_compra WHERE mercancia_id=%s AND empresa_id=%s", (id, eid))
        cur.execute("DELETE FROM presentaciones WHERE mercancia_id=%s AND empresa_id=%s", (id, eid))
        cur.execute("DELETE FROM inventario WHERE mercancia_id=%s AND empresa_id=%s", (id, eid))
        cur.execute("DELETE FROM mercancia WHERE id=%s AND empresa_id=%s", (id, eid))

        conn.commit()
        flash('Producto eliminado.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'No se pudo eliminar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('mercancia'))

@app.route('/registrar_proveedor', methods=['GET', 'POST'])
@require_login
def registrar_proveedor():
    eid = g.empresa_id
    buscar = request.args.get('buscar', '').strip()
    
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        direccion = request.form.get('direccion', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        telefono = request.form.get('telefono', '').strip()

        if not nombre:
            flash('El nombre del proveedor es obligatorio.', 'danger')
            return redirect(url_for('registrar_proveedor'))

        cursor.execute("""
            INSERT INTO proveedores (nombre, direccion, ciudad, telefono, empresa_id, activo)
            VALUES (%s, %s, %s, %s, %s, 1)
        """, (nombre, direccion, ciudad, telefono, eid))
        conn.commit()
        flash('Proveedor registrado correctamente.', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('registrar_proveedor'))

    query = "SELECT * FROM proveedores WHERE empresa_id = %s AND activo = 1"
    params = [eid]
    
    if buscar:
        query += " AND (nombre LIKE %s OR ciudad LIKE %s OR telefono LIKE %s)"
        params.extend([f'%{buscar}%', f'%{buscar}%', f'%{buscar}%'])
    
    query += " ORDER BY nombre ASC"
    
    cursor.execute(query, params)
    proveedores = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('registrar_proveedor.html', proveedores=proveedores, buscar=buscar)

@app.route('/editar_proveedor/<int:id>', methods=['POST'])
@require_login
def editar_proveedor(id):
    eid = g.empresa_id
    nombre = request.form.get('nombre', '').strip()
    direccion = request.form.get('direccion', '').strip()
    ciudad = request.form.get('ciudad', '').strip()
    telefono = request.form.get('telefono', '').strip()

    if not nombre:
        flash('El nombre del proveedor es obligatorio.', 'danger')
        return redirect(url_for('registrar_proveedor'))

    conn = conexion_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE proveedores 
        SET nombre = %s, direccion = %s, ciudad = %s, telefono = %s
        WHERE id = %s AND empresa_id = %s
    """, (nombre, direccion, ciudad, telefono, id, eid))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Proveedor actualizado correctamente.', 'success')
    return redirect(url_for('registrar_proveedor'))

@app.route('/eliminar_proveedor/<int:id>', methods=['POST'])
@require_login
def eliminar_proveedor(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE proveedores SET activo = 0 WHERE id = %s AND empresa_id = %s", (id, eid))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Proveedor eliminado correctamente.', 'success')
    return redirect(url_for('registrar_proveedor'))

# ==================== CATÁLOGO MP CORREGIDO ====================
# ==================== CATÁLOGO MP CORREGIDO ====================
@app.route('/catalogo_mp')
@require_login
def catalogo_mp():
    """Catálogo de Materia Prima - FILTRADO POR EMPRESA"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    q = request.args.get('q', '').strip()
    
    if q:
        cur.execute("""
            SELECT m.*, u.nombre AS unidad_nombre
            FROM mercancia m
            LEFT JOIN unidades_medida u ON u.id = m.unidad_id
            WHERE m.tipo_inventario_id = 1
              AND m.empresa_id = %s
              AND m.nombre LIKE %s
            ORDER BY m.nombre
        """, (eid, f'%{q}%'))
    else:
        cur.execute("""
            SELECT m.*, u.nombre AS unidad_nombre
            FROM mercancia m
            LEFT JOIN unidades_medida u ON u.id = m.unidad_id
            WHERE m.tipo_inventario_id = 1
              AND m.empresa_id = %s
            ORDER BY m.nombre
        """, (eid,))
    
    productos = cur.fetchall()
    
    # Catálogo de unidades
    cur.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
    unidades = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template(
        'inventarios/MP/catalogo_mp.html',
        productos=productos,
        unidades=unidades,
        q=q
    )

@app.route('/catalogo_mp/toggle/<int:id>', methods=['POST'])
@require_login
def catalogo_mp_toggle(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE producto_base SET activo = 1 - activo 
            WHERE id=%s AND empresa_id=%s
        """, (id, eid))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"No se pudo cambiar el estado: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('catalogo_mp'))

@app.route('/catalogo_mp/editar/<int:id>', methods=['GET', 'POST'])
@require_login
def catalogo_mp_editar(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            nombre = (request.form.get('nombre') or '').strip()
            unidad_id_s = (request.form.get('unidad_id') or '').strip()
            activo = 1 if (request.form.get('activo') == '1') else 0

            if not nombre:
                flash("El nombre es obligatorio", "danger")
                return redirect(url_for('catalogo_mp_editar', id=id))

            if unidad_id_s.isdigit():
                unidad_id = int(unidad_id_s)
                cur.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
                if not cur.fetchone():
                    flash("Unidad de medida inválida.", "danger")
                    return redirect(url_for('catalogo_mp_editar', id=id))
            else:
                cur.execute("SELECT id FROM unidades_medida ORDER BY id LIMIT 1")
                r = cur.fetchone()
                unidad_id = r['id'] if r else 1

            # Duplicado EN ESTA EMPRESA
            cur.execute("""
                SELECT id FROM producto_base
                WHERE UPPER(nombre)=UPPER(%s) AND id<>%s AND empresa_id=%s
                LIMIT 1
            """, (nombre, id, eid))
            if cur.fetchone():
                flash("Ya existe otro producto base con ese nombre.", "warning")
                return redirect(url_for('catalogo_mp_editar', id=id))

            cur.execute("""
                UPDATE producto_base
                SET nombre=%s, unidad_id=%s, activo=%s
                WHERE id=%s AND empresa_id=%s
            """, (nombre, unidad_id, activo, id, eid))
            conn.commit()
            flash("Producto base actualizado", "success")
            return redirect(url_for('catalogo_mp'))

        # GET: cargar item VALIDANDO EMPRESA
        cur.execute("""
            SELECT * FROM producto_base 
            WHERE id=%s AND empresa_id=%s
        """, (id, eid))
        item = cur.fetchone()
        cur.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        unidades = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    if not item:
        flash("Ítem no encontrado", "danger")
        return redirect(url_for('catalogo_mp'))

    return render_template("inventarios/MP/catalogo_mp_editar.html", item=item, unidades=unidades)

@app.post('/catalogo_mp/<int:id>/eliminar')
@require_login
def catalogo_mp_eliminar(id):
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor()
    try:
        # Validar pertenencia
        cur.execute("""
            SELECT 1 FROM producto_base 
            WHERE id=%s AND empresa_id=%s
        """, (id, eid))
        if not cur.fetchone():
            flash('Producto no encontrado.', 'warning')
            return redirect(url_for('catalogo_mp'))
        
        cur.execute("""
            SELECT 1 FROM mercancia 
            WHERE producto_base_id=%s AND empresa_id=%s 
            LIMIT 1
        """, (id, eid))
        if cur.fetchone():
            flash('No se puede eliminar: hay mercancías ligadas.', 'warning')
        else:
            cur.execute("""
                DELETE FROM producto_base 
                WHERE id=%s AND empresa_id=%s
            """, (id, eid))
            conn.commit()
            flash('Eliminado.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('catalogo_mp'))

@app.route('/catalogo_mp/nuevo', methods=['POST'])
@require_login
def catalogo_mp_nuevo():
    eid = g.empresa_id
    
    nombre = (request.form.get('nombre') or '').strip()
    unidad_id_s = (request.form.get('unidad_id') or '').strip()
    
    if not nombre:
        flash("Nombre obligatorio.", "danger")
        return redirect(url_for('catalogo_mp') + '#nuevo')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        if not unidad_id_s.isdigit():
            cur.execute("SELECT id FROM unidades_medida ORDER BY id LIMIT 1")
            r = cur.fetchone()
            unidad_id = r["id"] if r else 1
        else:
            unidad_id = int(unidad_id_s)
            cur.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
            if not cur.fetchone():
                flash("Unidad inválida.", "danger")
                return redirect(url_for('catalogo_mp') + '#nuevo')

        # Verificar duplicado EN ESTA EMPRESA
        cur.execute("""
            SELECT id FROM producto_base 
            WHERE UPPER(nombre)=UPPER(%s) AND empresa_id=%s 
            LIMIT 1
        """, (nombre, eid))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE producto_base SET activo=1, unidad_id=%s 
                WHERE id=%s AND empresa_id=%s
            """, (unidad_id, row['id'], eid))
            flash("Producto base reactivado.", "info")
        else:
            cur.execute("""
                INSERT INTO producto_base (empresa_id, nombre, unidad_id, activo) 
                VALUES (%s, %s, %s, 1)
            """, (eid, nombre, unidad_id))
            flash("Producto base agregado.", "success")

        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('catalogo_mp'))

@app.route('/mercancia/wip')
def mercancia_wip():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db(); cur = conn.cursor(dictionary=True)

    # Productos WIP
    cursor.execute("""
        SELECT p.id, p.nombre, p.cont_neto,
            u.nombre AS unidad, p.iva, p.ieps,
            p.catalogo_id, p.producto_base_id,
            sc.id AS subcuenta_id,
            CONCAT(sc.codigo, ' - ', sc.nombre) AS cuenta_asignada
        FROM mercancia p
        LEFT JOIN unidades_medida u ON p.unidad_id = u.id
        LEFT JOIN cuentas_contables sc ON p.subcuenta_id = sc.id
        WHERE p.tipo = 'MP'
        ORDER BY p.nombre ASC
    """)
    productos = cur.fetchall()

    # Presentaciones
    cur.execute("""
        SELECT mercancia_id,
               GROUP_CONCAT(CONCAT(contenido_neto,' ',unidad) ORDER BY contenido_neto SEPARATOR ', ') AS presentaciones
        FROM presentaciones
        GROUP BY mercancia_id
    """)
    pres_map = {r['mercancia_id']: r['presentaciones'] for r in cur.fetchall()}
    for it in productos:
        it['presentaciones'] = pres_map.get(it['id'], '')

    cur.close(); conn.close()
    # Reutiliza tu template, pero en modo solo listado
    return render_template('mercancia.html',
                           titulo='Producción en Proceso (WIP)',
                           solo_listado=True,
                           unidades=[],              # no se usa en modo listado
                           productos=productos,
                           cuentas_catalogo=[])





# ==================== GESTIÓN USUARIO-ÁREAS ====================



@app.route('/test-email')
def test_email():
    """Ruta temporal para probar envío de email"""
    try:
        msg = Message(
            subject='✅ Prueba de Email - ERP',
            recipients=['pakogranados1@gmail.com']
        )
        msg.body = 'Si recibes este mensaje, el email funciona!'
        msg.html = '<h1>✅ Email funcionando!</h1><p>Sistema configurado correctamente.</p>'
            
        mail.send(msg)
        return '<h1>✅ Email enviado correctamente!</h1><p>Revisa tu bandeja (y spam)</p>'
            
    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(f"❌ Error enviando email: {error_completo}")
        return f'<h1>❌ Error al enviar email:</h1><pre>{error_completo}</pre>'


# =====================================================
# MÓDULO: REGISTROS HISTÓRICOS DE VENTAS
# Agregar estas rutas a app.py antes de la línea:
# # ===== REGISTRO DE BLUEPRINTS =====
# =====================================================

# -------------------- DASHBOARD REGISTROS HISTÓRICOS --------------------
@app.route('/registros_historicos')
@require_login
def registros_historicos_dashboard():
    """Dashboard de registros históricos - vista por mes"""
    eid = g.empresa_id
    
    # Obtener mes/año del parámetro o usar actual
    from datetime import datetime, timedelta
    import calendar
    
    mes = request.args.get('mes', type=int, default=datetime.now().month)
    anio = request.args.get('anio', type=int, default=datetime.now().year)
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener todos los días del mes con sus totales
        primer_dia = f"{anio}-{mes:02d}-01"
        ultimo_dia = f"{anio}-{mes:02d}-{calendar.monthrange(anio, mes)[1]}"
        
        # Resumen por día
        cur.execute("""
            SELECT 
                DATE(fecha) as fecha,
                COUNT(*) as num_ventas,
                SUM(subtotal) as total_ventas
            FROM ventas_historicas
            WHERE empresa_id = %s 
              AND fecha BETWEEN %s AND %s
            GROUP BY DATE(fecha)
            ORDER BY fecha DESC
        """, (eid, primer_dia, ultimo_dia))
        ventas_por_dia = {row['fecha']: row for row in cur.fetchall()}
        
        # Mermas por día
        cur.execute("""
            SELECT 
                DATE(fecha) as fecha,
                COUNT(*) as num_mermas,
                SUM(costo_total) as total_mermas
            FROM mermas
            WHERE empresa_id = %s 
              AND fecha BETWEEN %s AND %s
            GROUP BY DATE(fecha)
        """, (eid, primer_dia, ultimo_dia))
        mermas_por_dia = {row['fecha']: row for row in cur.fetchall()}
        
        # Consumos por día
        cur.execute("""
            SELECT 
                DATE(fecha) as fecha,
                COUNT(*) as num_consumos,
                SUM(costo_total) as total_consumos
            FROM consumos_internos
            WHERE empresa_id = %s 
              AND fecha BETWEEN %s AND %s
            GROUP BY DATE(fecha)
        """, (eid, primer_dia, ultimo_dia))
        consumos_por_dia = {row['fecha']: row for row in cur.fetchall()}
        
        # Registros cerrados
        cur.execute("""
            SELECT fecha, cerrado
            FROM registros_diarios
            WHERE empresa_id = %s 
              AND fecha BETWEEN %s AND %s
        """, (eid, primer_dia, ultimo_dia))
        registros_cerrados = {row['fecha']: row['cerrado'] for row in cur.fetchall()}
        
        # Construir calendario del mes
        from datetime import date
        dias_mes = []
        num_dias = calendar.monthrange(anio, mes)[1]
        
        for dia in range(1, num_dias + 1):
            fecha = date(anio, mes, dia)
            info = {
                'fecha': fecha,
                'dia': dia,
                'dia_semana': fecha.strftime('%a'),
                'es_futuro': fecha > date.today(),
                'es_hoy': fecha == date.today(),
                'cerrado': registros_cerrados.get(fecha, 0),
                'ventas': ventas_por_dia.get(fecha, {'num_ventas': 0, 'total_ventas': 0}),
                'mermas': mermas_por_dia.get(fecha, {'num_mermas': 0, 'total_mermas': 0}),
                'consumos': consumos_por_dia.get(fecha, {'num_consumos': 0, 'total_consumos': 0})
            }
            dias_mes.append(info)
        
        # Totales del mes
        totales = {
            'ventas': sum((d['ventas']['total_ventas'] or 0) for d in dias_mes),
            'mermas': sum((d['mermas']['total_mermas'] or 0) for d in dias_mes),
            'consumos': sum((d['consumos']['total_consumos'] or 0) for d in dias_mes),
            'num_ventas': sum((d['ventas']['num_ventas'] or 0) for d in dias_mes),
            'num_mermas': sum((d['mermas']['num_mermas'] or 0) for d in dias_mes),
            'num_consumos': sum((d['consumos']['num_consumos'] or 0) for d in dias_mes)
        }
        
        # Navegación de meses
        mes_anterior = mes - 1 if mes > 1 else 12
        anio_anterior = anio if mes > 1 else anio - 1
        mes_siguiente = mes + 1 if mes < 12 else 1
        anio_siguiente = anio if mes < 12 else anio + 1
        
        nombre_mes = calendar.month_name[mes]
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('registros_historicos/dashboard.html',
                           dias_mes=dias_mes,
                           mes=mes,
                           anio=anio,
                           nombre_mes=nombre_mes,
                           totales=totales,
                           mes_anterior=mes_anterior,
                           anio_anterior=anio_anterior,
                           mes_siguiente=mes_siguiente,
                           anio_siguiente=anio_siguiente)


# -------------------- REGISTRO DE UN DÍA ESPECÍFICO --------------------
@app.route('/registros_historicos/<fecha>')
@require_login
def registro_dia(fecha):
    """Ver/editar registro de un día específico"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    from datetime import datetime, date
    
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        flash('Fecha inválida', 'danger')
        return redirect(url_for('registros_historicos_dashboard'))
    
    # No permitir fechas futuras
    if fecha_obj > date.today():
        flash('No se pueden registrar ventas de fechas futuras', 'warning')
        return redirect(url_for('registros_historicos_dashboard'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Verificar/crear registro del día
        cur.execute("""
            SELECT id, cerrado, notas
            FROM registros_diarios
            WHERE empresa_id = %s AND fecha = %s
        """, (eid, fecha))
        registro = cur.fetchone()
        
        if not registro:
            cur.execute("""
                INSERT INTO registros_diarios (empresa_id, fecha, usuario_id)
                VALUES (%s, %s, %s)
            """, (eid, fecha, uid))
            conn.commit()
            registro_id = cur.lastrowid
            registro = {'id': registro_id, 'cerrado': 0, 'notas': ''}
        else:
            registro_id = registro['id']
        
        # Obtener ventas del día
        cur.execute("""
            SELECT v.*, u.nombre as usuario_nombre
            FROM ventas_historicas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.empresa_id = %s AND v.fecha = %s
            ORDER BY v.id DESC
        """, (eid, fecha))
        ventas = cur.fetchall()
        
        # Obtener mermas del día
        cur.execute("""
            SELECT m.*, u.nombre as usuario_nombre
            FROM mermas m
            LEFT JOIN usuarios u ON m.usuario_id = u.id
            WHERE m.empresa_id = %s AND m.fecha = %s
            ORDER BY m.id DESC
        """, (eid, fecha))
        mermas = cur.fetchall()
        
        # Obtener consumos del día
        cur.execute("""
            SELECT c.*, u.nombre as usuario_nombre
            FROM consumos_internos c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.empresa_id = %s AND c.fecha = %s
            ORDER BY c.id DESC
        """, (eid, fecha))
        consumos = cur.fetchall()
        
        # Obtener productos para el formulario
        cur.execute("""
            SELECT id, nombre, precio as precio_venta
            FROM mercancia
            WHERE empresa_id = %s
            ORDER BY nombre
        """, (eid,))
        productos = cur.fetchall()
        
        # Calcular totales
        totales = {
            'ventas': sum(v['subtotal'] or 0 for v in ventas),
            'mermas': sum(m['costo_total'] or 0 for m in mermas),
            'consumos': sum(c['costo_total'] or 0 for c in consumos),
            'num_ventas': len(ventas),
            'num_mermas': len(mermas),
            'num_consumos': len(consumos)
        }
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('registros_historicos/registro_dia.html',
                           fecha=fecha,
                           fecha_obj=fecha_obj,
                           registro=registro,
                           ventas=ventas,
                           mermas=mermas,
                           consumos=consumos,
                           productos=productos,
                           totales=totales)


# -------------------- AGREGAR VENTA HISTÓRICA --------------------
@app.route('/registros_historicos/<fecha>/venta', methods=['POST'])
@require_login
def agregar_venta_historica(fecha):
    """Agregar una venta histórica"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=float, default=1)
    precio_unitario = request.form.get('precio_unitario', type=float, default=0)
    metodo_pago = request.form.get('metodo_pago', 'efectivo')
    notas = request.form.get('notas', '').strip()
    
    if not producto_id or cantidad <= 0:
        flash('Datos inválidos', 'danger')
        return redirect(url_for('registro_dia', fecha=fecha))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener registro_id
        cur.execute("""
            SELECT id, cerrado FROM registros_diarios
            WHERE empresa_id = %s AND fecha = %s
        """, (eid, fecha))
        registro = cur.fetchone()
        
        if registro and registro['cerrado']:
            flash('Este día ya está cerrado', 'warning')
            return redirect(url_for('registro_dia', fecha=fecha))
        
        registro_id = registro['id'] if registro else None
        
        # Obtener nombre del producto
        cur.execute("SELECT nombre FROM mercancia WHERE id = %s", (producto_id,))
        prod = cur.fetchone()
        producto_nombre = prod['nombre'] if prod else ''
        
        subtotal = round(cantidad * precio_unitario, 2)
        
        cur.execute("""
            INSERT INTO ventas_historicas 
            (empresa_id, registro_id, fecha, producto_id, producto_nombre, 
             cantidad, precio_unitario, subtotal, metodo_pago, notas, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, registro_id, fecha, producto_id, producto_nombre,
              cantidad, precio_unitario, subtotal, metodo_pago, notas, uid))
        conn.commit()
        
        flash(f'✅ Venta registrada: {producto_nombre} x {cantidad}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('registro_dia', fecha=fecha))


# -------------------- AGREGAR MERMA --------------------
@app.route('/registros_historicos/<fecha>/merma', methods=['POST'])
@require_login
def agregar_merma_historica(fecha):
    """Agregar una merma"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=float, default=1)
    costo_unitario = request.form.get('costo_unitario', type=float, default=0)
    motivo = request.form.get('motivo', 'otro')
    descripcion = request.form.get('descripcion', '').strip()
    
    if not producto_id or cantidad <= 0:
        flash('Datos inválidos', 'danger')
        return redirect(url_for('registro_dia', fecha=fecha))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener registro_id
        cur.execute("""
            SELECT id, cerrado FROM registros_diarios
            WHERE empresa_id = %s AND fecha = %s
        """, (eid, fecha))
        registro = cur.fetchone()
        
        if registro and registro['cerrado']:
            flash('Este día ya está cerrado', 'warning')
            return redirect(url_for('registro_dia', fecha=fecha))
        
        registro_id = registro['id'] if registro else None
        
        # Obtener nombre del producto
        cur.execute("SELECT nombre FROM mercancia WHERE id = %s", (producto_id,))
        prod = cur.fetchone()
        producto_nombre = prod['nombre'] if prod else ''
        
        costo_total = round(cantidad * costo_unitario, 2)
        
        cur.execute("""
            INSERT INTO mermas 
            (empresa_id, registro_id, fecha, producto_id, producto_nombre, 
             cantidad, costo_unitario, costo_total, motivo, descripcion, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, registro_id, fecha, producto_id, producto_nombre,
              cantidad, costo_unitario, costo_total, motivo, descripcion, uid))
        conn.commit()
        
        flash(f'✅ Merma registrada: {producto_nombre} x {cantidad}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('registro_dia', fecha=fecha))


# -------------------- AGREGAR CONSUMO INTERNO --------------------
@app.route('/registros_historicos/<fecha>/consumo', methods=['POST'])
@require_login
def agregar_consumo_historico(fecha):
    """Agregar un consumo interno"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=float, default=1)
    costo_unitario = request.form.get('costo_unitario', type=float, default=0)
    responsable = request.form.get('responsable', '').strip()
    motivo = request.form.get('motivo', '').strip()
    
    if not producto_id or cantidad <= 0:
        flash('Datos inválidos', 'danger')
        return redirect(url_for('registro_dia', fecha=fecha))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener registro_id
        cur.execute("""
            SELECT id, cerrado FROM registros_diarios
            WHERE empresa_id = %s AND fecha = %s
        """, (eid, fecha))
        registro = cur.fetchone()
        
        if registro and registro['cerrado']:
            flash('Este día ya está cerrado', 'warning')
            return redirect(url_for('registro_dia', fecha=fecha))
        
        registro_id = registro['id'] if registro else None
        
        # Obtener nombre del producto
        cur.execute("SELECT nombre FROM mercancia WHERE id = %s", (producto_id,))
        prod = cur.fetchone()
        producto_nombre = prod['nombre'] if prod else ''
        
        costo_total = round(cantidad * costo_unitario, 2)
        
        cur.execute("""
            INSERT INTO consumos_internos 
            (empresa_id, registro_id, fecha, producto_id, producto_nombre, 
             cantidad, costo_unitario, costo_total, responsable, motivo, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (eid, registro_id, fecha, producto_id, producto_nombre,
              cantidad, costo_unitario, costo_total, responsable, motivo, uid))
        conn.commit()
        
        flash(f'✅ Consumo registrado: {producto_nombre} x {cantidad}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('registro_dia', fecha=fecha))


# -------------------- ELIMINAR REGISTROS --------------------
@app.route('/registros_historicos/eliminar/<tipo>/<int:id>', methods=['POST'])
@require_login
def eliminar_registro_historico(tipo, id):
    """Eliminar venta, merma o consumo"""
    eid = g.empresa_id
    fecha = request.form.get('fecha')
    
    tablas = {
        'venta': 'ventas_historicas',
        'merma': 'mermas',
        'consumo': 'consumos_internos'
    }
    
    if tipo not in tablas:
        flash('Tipo inválido', 'danger')
        return redirect(url_for('registros_historicos_dashboard'))
    
    conn = conexion_db()
    cur = conn.cursor()
    
    try:
        cur.execute(f"""
            DELETE FROM {tablas[tipo]}
            WHERE id = %s AND empresa_id = %s
        """, (id, eid))
        conn.commit()
        flash('✅ Registro eliminado', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    if fecha:
        return redirect(url_for('registro_dia', fecha=fecha))
    return redirect(url_for('registros_historicos_dashboard'))


# -------------------- CERRAR/ABRIR DÍA --------------------
@app.route('/registros_historicos/<fecha>/cerrar', methods=['POST'])
@require_login
def cerrar_dia_historico(fecha):
    """Cerrar o abrir un día para edición"""
    eid = g.empresa_id
    accion = request.form.get('accion', 'cerrar')
    
    conn = conexion_db()
    cur = conn.cursor()
    
    try:
        if accion == 'cerrar':
            cur.execute("""
                UPDATE registros_diarios
                SET cerrado = 1, fecha_cierre = NOW()
                WHERE empresa_id = %s AND fecha = %s
            """, (eid, fecha))
            flash('✅ Día cerrado correctamente', 'success')
        else:
            cur.execute("""
                UPDATE registros_diarios
                SET cerrado = 0, fecha_cierre = NULL
                WHERE empresa_id = %s AND fecha = %s
            """, (eid, fecha))
            flash('✅ Día reabierto para edición', 'success')
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('registro_dia', fecha=fecha))


# -------------------- API: OBTENER PRECIO PRODUCTO --------------------
@app.route('/api/producto/<int:producto_id>/precio')
@require_login
def api_precio_producto(producto_id):
    """Obtener precio de un producto"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT id, nombre, precio as precio_venta, 
                   COALESCE(precio, 0) as costo
            FROM mercancia
            WHERE id = %s AND empresa_id = %s
        """, (producto_id, eid))
        producto = cur.fetchone()
        
        if producto:
            return jsonify({
                'success': True,
                'producto': producto
            })
        return jsonify({'success': False, 'error': 'Producto no encontrado'})
    finally:
        cur.close()
        conn.close()

@app.get("/api/mercancia")
@require_token
def api_mercancia():
    """
    Devuelve el catálogo de mercancia ACTIVA.
    Usa el token para identificar empresa_id (cuando lo uses).
    """
    user = getattr(request, "api_user", {})
    empresa_id = user.get("empresa_id", None)

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    # Por ahora:
    # - si empresa_id es NULL en el token, devolvemos TODO lo activo
    # - más adelante podemos filtrar por empresa
    if empresa_id is None:
        sql = """
            SELECT
                m.id,
                m.nombre,
                m.precio,
                m.precio_venta,
                m.unidad_base,
                m.tipo,
                m.iva,
                m.ieps,
                m.graba_iva,
                m.graba_ieps,
                m.activo,
                m.producto_base_id,
                m.tipo_inventario_id
            FROM mercancia m
            WHERE m.activo = 1
            ORDER BY m.nombre ASC
        """
        cur.execute(sql)
    else:
        sql = """
            SELECT
                m.id,
                m.nombre,
                m.precio,
                m.precio_venta,
                m.unidad_base,
                m.tipo,
                m.iva,
                m.ieps,
                m.graba_iva,
                m.graba_ieps,
                m.activo,
                m.producto_base_id,
                m.tipo_inventario_id
            FROM mercancia m
            WHERE m.activo = 1
              AND (m.empresa_id = %s OR m.empresa_id IS NULL)
            ORDER BY m.nombre ASC
        """
        cur.execute(sql, (empresa_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "ok": True,
        "total": len(rows),
        "data": rows
    })

@app.route("/api_test_mercancia")
def api_test_mercancia():
    # Página sencilla para probar /api/mercancia desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Mercancia</title>
    </head>
    <body>
      <h2>Prueba /api/mercancia (con TOKEN)</h2>

      <p>Pega aquí el token JWT que te devolvió /api/login:</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <br><br>
      <button id="btnProbar">Probar /api/mercancia</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:900px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token  = document.getElementById('token').value.trim();
          const salida = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/mercancia...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }

          try {
            const resp = await fetch('/api/mercancia', {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

@app.get("/api/ventas")
@require_token
def api_ventas_listado():
    """
    Devuelve el listado de ventas (tabla ventas).
    Por ahora: últimas 50 ventas, de más reciente a más antigua.
    Si el token tiene empresa_id, se filtra por esa empresa.
    """
    user = getattr(request, "api_user", {})
    empresa_id = user.get("empresa_id", None)

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    if empresa_id is None:
        sql = """
            SELECT
                v.id,
                v.empresa_id,
                v.turno_id,
                v.fecha,
                v.subtotal,
                v.iva,
                v.total,
                v.metodo_pago,
                v.estado,
                v.usuario_id
            FROM ventas v
            ORDER BY v.fecha DESC, v.id DESC
            LIMIT 50
        """
        cur.execute(sql)
    else:
        sql = """
            SELECT
                v.id,
                v.empresa_id,
                v.turno_id,
                v.fecha,
                v.subtotal,
                v.iva,
                v.total,
                v.metodo_pago,
                v.estado,
                v.usuario_id
            FROM ventas v
            WHERE v.empresa_id = %s
            ORDER BY v.fecha DESC, v.id DESC
            LIMIT 50
        """
        cur.execute(sql, (empresa_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "ok": True,
        "total": len(rows),
        "data": rows
    })

@app.route("/api_test_ventas")
def api_test_ventas():
    # Página sencilla para probar /api/ventas desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Ventas</title>
    </head>
    <body>
      <h2>Prueba /api/ventas (con TOKEN)</h2>

      <p>Pega aquí el token JWT que te devolvió /api/login:</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <br><br>
      <button id="btnProbar">Probar /api/ventas</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:900px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token  = document.getElementById('token').value.trim();
          const salida = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/ventas...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }

          try {
            const resp = await fetch('/api/ventas', {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

@app.get("/api/caja_ventas")
@require_token
def api_caja_ventas_listado():
    """
    Devuelve el listado de tickets de caja (caja_ventas).
    Por ahora: últimos 50 tickets, de más reciente a más antiguo.
    Si el token tiene empresa_id, se filtra por esa empresa.
    No muestra tickets cancelados (cancelada = 1).
    """
    user = getattr(request, "api_user", {})
    empresa_id = user.get("empresa_id", None)

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    if empresa_id is None:
        sql = """
            SELECT
                v.id,
                v.empresa_id,
                v.turno_id,
                v.usuario_id,
                v.folio,
                v.fecha,
                v.subtotal,
                v.iva,
                v.total,
                v.metodo_pago,
                v.estado,
                v.cliente_nombre,
                v.efectivo_recibido,
                v.cambio,
                v.descuento,
                v.cancelada
            FROM caja_ventas v
            WHERE v.cancelada = 0
            ORDER BY v.fecha DESC, v.id DESC
            LIMIT 50
        """
        cur.execute(sql)
    else:
        sql = """
            SELECT
                v.id,
                v.empresa_id,
                v.turno_id,
                v.usuario_id,
                v.folio,
                v.fecha,
                v.subtotal,
                v.iva,
                v.total,
                v.metodo_pago,
                v.estado,
                v.cliente_nombre,
                v.efectivo_recibido,
                v.cambio,
                v.descuento,
                v.cancelada
            FROM caja_ventas v
            WHERE v.cancelada = 0
              AND (v.empresa_id = %s OR v.empresa_id IS NULL)
            ORDER BY v.fecha DESC, v.id DESC
            LIMIT 50
        """
        cur.execute(sql, (empresa_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "ok": True,
        "total": len(rows),
        "data": rows
    })



# =====================================================
# RUTAS DE FACTURACIÓN B2B Y CFDI
# Agregar este código en app.py ANTES de:
# # ===== REGISTRO DE BLUEPRINTS =====
# (aproximadamente línea 8705)
# =====================================================

# ===== FACTURACIÓN - DASHBOARD =====
@app.route('/facturacion')
@require_login
def facturacion_dashboard():
    """Dashboard principal del módulo de facturación"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # KPI: Ventas hoy (caja)
        cur.execute("""
            SELECT COALESCE(SUM(total), 0) as ventas, COUNT(*) as tickets
            FROM ventas 
            WHERE empresa_id = %s AND DATE(fecha) = CURDATE()
        """, (eid,))
        ventas_hoy = cur.fetchone()
        
        # KPI: Facturas B2B emitidas (este mes)
        cur.execute("""
            SELECT COUNT(*) as cantidad, COALESCE(SUM(total), 0) as monto
            FROM facturas_b2b 
            WHERE empresa_emisora_id = %s 
            AND MONTH(fecha_emision) = MONTH(CURDATE())
            AND YEAR(fecha_emision) = YEAR(CURDATE())
            AND estado != 'cancelada'
        """, (eid,))
        b2b_emitidas = cur.fetchone()
        
        # KPI: Facturas B2B pendientes de recibir
        cur.execute("""
            SELECT COUNT(*) as cantidad
            FROM facturas_b2b 
            WHERE empresa_receptora_id = %s 
            AND estado IN ('emitida', 'pendiente', 'en_revision')
        """, (eid,))
        b2b_pendientes = cur.fetchone()
        
        # KPI: Cuentas por cobrar
        cur.execute("""
            SELECT COALESCE(SUM(saldo), 0) as total, COUNT(*) as documentos
            FROM cuentas_por_cobrar 
            WHERE empresa_id = %s AND estado IN ('pendiente', 'parcial')
        """, (eid,))
        cxc = cur.fetchone()
        
        kpis = {
            'ventas_hoy': float(ventas_hoy['ventas'] or 0),
            'tickets_hoy': ventas_hoy['tickets'] or 0,
            'b2b_emitidas': b2b_emitidas['cantidad'] or 0,
            'b2b_emitidas_monto': float(b2b_emitidas['monto'] or 0),
            'b2b_pendientes': b2b_pendientes['cantidad'] or 0,
            'por_cobrar': float(cxc['total'] or 0),
            'cxc_pendientes': cxc['documentos'] or 0
        }
        
        # Últimas facturas emitidas
        cur.execute("""
            SELECT f.id, f.folio, f.total, f.estado, f.fecha_emision,
                   e.nombre as cliente_nombre
            FROM facturas_b2b f
            JOIN empresas e ON e.id = f.empresa_receptora_id
            WHERE f.empresa_emisora_id = %s AND f.estado != 'cancelada'
            ORDER BY f.fecha_emision DESC
            LIMIT 5
        """, (eid,))
        ultimas_emitidas = cur.fetchall()
        for f in ultimas_emitidas:
            f['fecha_fmt'] = f['fecha_emision'].strftime('%d/%m/%Y') if f['fecha_emision'] else ''
            f['cliente'] = f['cliente_nombre']
        
        # Facturas pendientes de recibir
        cur.execute("""
            SELECT f.id, f.folio, f.total, f.fecha_emision,
                   e.nombre as proveedor_nombre
            FROM facturas_b2b f
            JOIN empresas e ON e.id = f.empresa_emisora_id
            WHERE f.empresa_receptora_id = %s 
            AND f.estado IN ('emitida', 'pendiente')
            ORDER BY f.fecha_emision DESC
            LIMIT 5
        """, (eid,))
        pendientes_recibir = cur.fetchall()
        for f in pendientes_recibir:
            f['fecha_fmt'] = f['fecha_emision'].strftime('%d/%m/%Y') if f['fecha_emision'] else ''
            f['proveedor'] = f['proveedor_nombre']
        
    except Exception as e:
        print(f"Error en facturacion_dashboard: {e}")
        kpis = {
            'ventas_hoy': 0, 'tickets_hoy': 0, 'b2b_emitidas': 0,
            'b2b_emitidas_monto': 0, 'b2b_pendientes': 0, 'por_cobrar': 0, 'cxc_pendientes': 0
        }
        ultimas_emitidas = []
        pendientes_recibir = []
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/facturacion_dashboard.html',
                          kpis=kpis,
                          ultimas_emitidas=ultimas_emitidas,
                          pendientes_recibir=pendientes_recibir)


# ===== FACTURACIÓN B2B - NUEVA =====
@app.route('/facturacion/b2b/nueva', methods=['GET', 'POST'])
@require_login
def facturacion_b2b_nueva():
    """Crear nueva factura B2B"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            empresa_receptora_id = int(request.form.get('empresa_receptora_id'))
            subtotal = Decimal(request.form.get('subtotal', '0'))
            iva = Decimal(request.form.get('iva', '0'))
            total = Decimal(request.form.get('total', '0'))
            forma_pago = request.form.get('forma_pago', 'Transferencia')
            metodo_pago = request.form.get('metodo_pago', 'PUE')
            fecha_vencimiento = request.form.get('fecha_vencimiento') or None
            condiciones_pago = request.form.get('condiciones_pago', '')
            
            # Generar folio
            cur.execute("""
                SELECT COUNT(*) + 1 as siguiente 
                FROM facturas_b2b 
                WHERE empresa_emisora_id = %s
            """, (eid,))
            num = cur.fetchone()['siguiente']
            folio = f"B2B-{eid}-{num:06d}"
            
            # Insertar factura
            cur.execute("""
                INSERT INTO facturas_b2b 
                (empresa_emisora_id, empresa_receptora_id, folio, fecha_emision, fecha_vencimiento,
                 subtotal, iva, total, forma_pago, metodo_pago, condiciones_pago, estado, emitida_por_usuario_id)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, 'emitida', %s)
            """, (eid, empresa_receptora_id, folio, fecha_vencimiento, subtotal, iva, total, 
                  forma_pago, metodo_pago, condiciones_pago, uid))
            factura_id = cur.lastrowid
            
            # Insertar detalle de productos
            i = 0
            while f'productos[{i}][mercancia_id]' in request.form:
                mercancia_id = int(request.form.get(f'productos[{i}][mercancia_id]'))
                descripcion = request.form.get(f'productos[{i}][descripcion]', '')
                cantidad = Decimal(request.form.get(f'productos[{i}][cantidad]', '0'))
                precio = Decimal(request.form.get(f'productos[{i}][precio]', '0'))
                iva_rate = Decimal(request.form.get(f'productos[{i}][iva_rate]', '0.16'))
                importe = Decimal(request.form.get(f'productos[{i}][importe]', '0'))
                
                cur.execute("""
                    INSERT INTO facturas_b2b_detalle 
                    (factura_id, mercancia_id, descripcion, cantidad_facturada, precio_unitario, iva_rate, importe)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (factura_id, mercancia_id, descripcion, cantidad, precio, iva_rate, importe))
                i += 1
            
            # Crear notificación para el receptor
            cur.execute("""
                INSERT INTO facturas_notificaciones 
                (empresa_destino_id, tipo_origen, origen_id, tipo_notificacion, mensaje)
                VALUES (%s, 'b2b', %s, 'nueva', %s)
            """, (empresa_receptora_id, factura_id, f'Nueva factura {folio} recibida'))
            
            conn.commit()
            flash(f'✅ Factura {folio} emitida correctamente', 'success')
            return redirect(url_for('facturacion_b2b_emitidas'))
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Error al emitir factura: {e}', 'danger')
    
    # GET: Mostrar formulario
    try:
        # Empresas disponibles (todas menos la actual)
        cur.execute("""
            SELECT id, nombre, rfc 
            FROM empresas 
            WHERE id != %s AND activo = 1
            ORDER BY nombre
        """, (eid,))
        empresas_disponibles = cur.fetchall()
        
        # Productos de la empresa
        cur.execute("""
            SELECT id, nombre, precio_venta as precio 
            FROM mercancia 
            WHERE empresa_id = %s AND activo = 1
            ORDER BY nombre
        """, (eid,))
        productos = cur.fetchall()
        
        # Empresa actual
        cur.execute("SELECT nombre, rfc FROM empresas WHERE id = %s", (eid,))
        empresa_actual = cur.fetchone()
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/b2b_nueva.html',
                          empresas_disponibles=empresas_disponibles,
                          productos=productos,
                          empresa_actual=empresa_actual)


# ===== FACTURACIÓN B2B - EMITIDAS =====
@app.route('/facturacion/b2b/emitidas')
@require_login
def facturacion_b2b_emitidas():
    """Listado de facturas B2B emitidas"""
    eid = g.empresa_id
    
    filtro_estado = request.args.get('estado', '')
    filtro_desde = request.args.get('desde', '')
    filtro_hasta = request.args.get('hasta', '')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT f.id, f.folio, f.total, f.estado, f.fecha_emision,
                   e.nombre as cliente_nombre, e.rfc as cliente_rfc
            FROM facturas_b2b f
            JOIN empresas e ON e.id = f.empresa_receptora_id
            WHERE f.empresa_emisora_id = %s
        """
        params = [eid]
        
        if filtro_estado:
            query += " AND f.estado = %s"
            params.append(filtro_estado)
        if filtro_desde:
            query += " AND DATE(f.fecha_emision) >= %s"
            params.append(filtro_desde)
        if filtro_hasta:
            query += " AND DATE(f.fecha_emision) <= %s"
            params.append(filtro_hasta)
        
        query += " ORDER BY f.fecha_emision DESC"
        
        cur.execute(query, params)
        facturas = cur.fetchall()
        
        for f in facturas:
            f['fecha_fmt'] = f['fecha_emision'].strftime('%d/%m/%Y') if f['fecha_emision'] else ''
            
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/b2b_emitidas.html',
                          facturas=facturas,
                          filtro_estado=filtro_estado,
                          filtro_desde=filtro_desde,
                          filtro_hasta=filtro_hasta)


# ===== FACTURACIÓN B2B - RECIBIDAS =====
@app.route('/facturacion/b2b/recibidas')
@require_login
def facturacion_b2b_recibidas():
    """Bandeja de facturas B2B recibidas"""
    eid = g.empresa_id
    
    filtro_estado = request.args.get('estado', 'pendiente')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Conteos por estado
        cur.execute("""
            SELECT 
                SUM(CASE WHEN estado IN ('emitida', 'pendiente') THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'en_revision' THEN 1 ELSE 0 END) as en_revision
            FROM facturas_b2b 
            WHERE empresa_receptora_id = %s
        """, (eid,))
        conteos = cur.fetchone()
        conteo_pendientes = conteos['pendientes'] or 0
        conteo_revision = conteos['en_revision'] or 0
        
        # Query principal
        query = """
            SELECT f.id, f.folio, f.total, f.estado, f.fecha_emision, f.fecha_vencimiento,
                   f.fecha_recepcion, e.nombre as proveedor_nombre,
                   (SELECT COUNT(*) FROM facturas_b2b_detalle WHERE factura_id = f.id) as items_count
            FROM facturas_b2b f
            JOIN empresas e ON e.id = f.empresa_emisora_id
            WHERE f.empresa_receptora_id = %s
        """
        params = [eid]
        
        if filtro_estado and filtro_estado != 'todas':
            if filtro_estado == 'pendiente':
                query += " AND f.estado IN ('emitida', 'pendiente')"
            else:
                query += " AND f.estado = %s"
                params.append(filtro_estado)
        
        query += " ORDER BY f.fecha_emision DESC"
        
        cur.execute(query, params)
        facturas = cur.fetchall()
        
        for f in facturas:
            f['fecha_fmt'] = f['fecha_emision'].strftime('%d/%m/%Y') if f['fecha_emision'] else ''
            f['fecha_vencimiento_fmt'] = f['fecha_vencimiento'].strftime('%d/%m/%Y') if f['fecha_vencimiento'] else ''
            f['fecha_recepcion_fmt'] = f['fecha_recepcion'].strftime('%d/%m/%Y') if f['fecha_recepcion'] else ''
            
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/b2b_recibidas.html',
                          facturas=facturas,
                          filtro_estado=filtro_estado,
                          conteo_pendientes=conteo_pendientes,
                          conteo_revision=conteo_revision)


# ===== FACTURACIÓN B2B - RECIBIR (CHECKLIST) =====
@app.route('/facturacion/b2b/recibir/<int:id>', methods=['GET', 'POST'])
@require_login
def facturacion_b2b_recibir(id):
    """Checklist para recibir mercancía de factura B2B"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Verificar que la factura es para esta empresa
        cur.execute("""
            SELECT f.*, e.nombre as proveedor_nombre
            FROM facturas_b2b f
            JOIN empresas e ON e.id = f.empresa_emisora_id
            WHERE f.id = %s AND f.empresa_receptora_id = %s
        """, (id, eid))
        factura = cur.fetchone()
        
        if not factura:
            flash('❌ Factura no encontrada', 'danger')
            return redirect(url_for('facturacion_b2b_recibidas'))
        
        factura['fecha_fmt'] = factura['fecha_emision'].strftime('%d/%m/%Y') if factura['fecha_emision'] else ''
        
        if request.method == 'POST':
            accion = request.form.get('accion', '')
            tipo_recepcion = request.form.get('tipo_recepcion', 'completa')
            notas_recepcion = request.form.get('notas_recepcion', '')
            
            hay_diferencias = False
            
            # Procesar cada item
            cur.execute("SELECT id FROM facturas_b2b_detalle WHERE factura_id = %s", (id,))
            items = cur.fetchall()
            
            for item in items:
                item_id = item['id']
                verificado = request.form.get(f'items[{item_id}][verificado]') == '1'
                cantidad_recibida = request.form.get(f'items[{item_id}][cantidad_recibida]', '0')
                notas = request.form.get(f'items[{item_id}][notas]', '')
                tipo_diferencia = request.form.get(f'items[{item_id}][tipo_diferencia]', '')
                
                try:
                    cantidad_recibida = Decimal(cantidad_recibida)
                except:
                    cantidad_recibida = Decimal('0')
                
                # Verificar si hay diferencia
                cur.execute("SELECT cantidad_facturada FROM facturas_b2b_detalle WHERE id = %s", (item_id,))
                det = cur.fetchone()
                tiene_diferencia = abs(det['cantidad_facturada'] - cantidad_recibida) > Decimal('0.001')
                
                if tiene_diferencia:
                    hay_diferencias = True
                
                cur.execute("""
                    UPDATE facturas_b2b_detalle 
                    SET verificado = %s, cantidad_recibida = %s, notas_verificacion = %s,
                        tiene_diferencia = %s, tipo_diferencia = %s,
                        verificado_por_usuario_id = %s, fecha_verificacion = NOW()
                    WHERE id = %s
                """, (verificado, cantidad_recibida, notas, tiene_diferencia, 
                      tipo_diferencia if tiene_diferencia else None, uid, item_id))
            
            if accion == 'guardar_progreso':
                # Solo guardar progreso, cambiar estado a en_revision
                cur.execute("""
                    UPDATE facturas_b2b 
                    SET estado = 'en_revision', notas_recepcion = %s
                    WHERE id = %s
                """, (notas_recepcion, id))
                conn.commit()
                flash('✅ Progreso guardado', 'success')
                return redirect(url_for('facturacion_b2b_recibir', id=id))
            else:
                # Confirmar recepción
                estado_final = 'con_diferencias' if hay_diferencias else 'recibida'
                
                cur.execute("""
                    UPDATE facturas_b2b 
                    SET estado = %s, fecha_recepcion = NOW(), recibida_por_usuario_id = %s,
                        notas_recepcion = %s
                    WHERE id = %s
                """, (estado_final, uid, notas_recepcion, id))
                
                # Crear cuenta por pagar
                cur.execute("""
                    INSERT INTO cuentas_por_pagar 
                    (empresa_id, factura_b2b_id, proveedor_empresa_id, tipo_documento, 
                     numero_documento, fecha_documento, fecha_vencimiento,
                     monto_original, saldo, estado, autorizado_por_usuario_id, fecha_autorizacion)
                    VALUES (%s, %s, %s, 'factura_b2b', %s, %s, %s, %s, %s, 'pendiente', %s, NOW())
                """, (eid, id, factura['empresa_emisora_id'], factura['folio'], 
                      factura['fecha_emision'], factura['fecha_vencimiento'],
                      factura['total'], factura['total'], uid))
                
                # Crear entrada al inventario MP por cada item recibido
                cur.execute("""
                    SELECT d.mercancia_id, d.cantidad_recibida, d.descripcion
                    FROM facturas_b2b_detalle d
                    WHERE d.factura_id = %s AND d.verificado = 1 AND d.cantidad_recibida > 0
                """, (id,))
                items_recibidos = cur.fetchall()
                
                for item in items_recibidos:
                    # Verificar si el producto existe en inventario MP
                    cur.execute("""
                        SELECT id FROM inventario_mp 
                        WHERE mercancia_id = %s AND empresa_id = %s
                    """, (item['mercancia_id'], eid))
                    inv = cur.fetchone()
                    
                    if inv:
                        # Actualizar existencia
                        cur.execute("""
                            UPDATE inventario_mp 
                            SET cantidad = cantidad + %s, fecha_actualizacion = NOW()
                            WHERE id = %s
                        """, (item['cantidad_recibida'], inv['id']))
                    else:
                        # Crear registro en inventario
                        cur.execute("""
                            INSERT INTO inventario_mp (empresa_id, mercancia_id, cantidad, fecha_actualizacion)
                            VALUES (%s, %s, %s, NOW())
                        """, (eid, item['mercancia_id'], item['cantidad_recibida']))
                    
                    # Registrar movimiento
                    cur.execute("""
                        INSERT INTO movimientos_inventario 
                        (empresa_id, mercancia_id, tipo_movimiento, cantidad, referencia, usuario_id, fecha)
                        VALUES (%s, %s, 'entrada', %s, %s, %s, NOW())
                    """, (eid, item['mercancia_id'], item['cantidad_recibida'], 
                          f'Factura B2B: {factura["folio"]}', uid))
                
                # Notificar al emisor
                cur.execute("""
                    INSERT INTO facturas_notificaciones 
                    (empresa_destino_id, tipo_origen, origen_id, tipo_notificacion, mensaje)
                    VALUES (%s, 'b2b', %s, 'recibida', %s)
                """, (factura['empresa_emisora_id'], id, 
                      f'Factura {factura["folio"]} fue {"recibida con diferencias" if hay_diferencias else "recibida conforme"}'))
                
                conn.commit()
                flash(f'✅ Factura recibida {"con diferencias" if hay_diferencias else "correctamente"}', 
                      'warning' if hay_diferencias else 'success')
                return redirect(url_for('facturacion_b2b_recibidas'))
        
        # GET: Mostrar checklist
        cur.execute("""
            SELECT d.*, m.nombre as mercancia_nombre
            FROM facturas_b2b_detalle d
            LEFT JOIN mercancia m ON m.id = d.mercancia_id
            WHERE d.factura_id = %s
            ORDER BY d.id
        """, (id,))
        detalle = cur.fetchall()
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/b2b_recibir.html',
                          factura=factura,
                          detalle=detalle)


# ===== FACTURACIÓN B2B - VER DETALLE =====
@app.route('/facturacion/b2b/<int:id>')
@require_login
def facturacion_b2b_ver(id):
    """Ver detalle de factura B2B"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener factura
        cur.execute("""
            SELECT f.*,
                   ee.nombre as emisor_nombre, ee.rfc as emisor_rfc,
                   er.nombre as receptor_nombre, er.rfc as receptor_rfc
            FROM facturas_b2b f
            JOIN empresas ee ON ee.id = f.empresa_emisora_id
            JOIN empresas er ON er.id = f.empresa_receptora_id
            WHERE f.id = %s AND (f.empresa_emisora_id = %s OR f.empresa_receptora_id = %s)
        """, (id, eid, eid))
        factura = cur.fetchone()
        
        if not factura:
            flash('❌ Factura no encontrada', 'danger')
            return redirect(url_for('facturacion_dashboard'))
        
        factura['fecha_fmt'] = factura['fecha_emision'].strftime('%d/%m/%Y') if factura['fecha_emision'] else ''
        factura['fecha_vencimiento_fmt'] = factura['fecha_vencimiento'].strftime('%d/%m/%Y') if factura['fecha_vencimiento'] else ''
        factura['fecha_recepcion_fmt'] = factura['fecha_recepcion'].strftime('%d/%m/%Y') if factura['fecha_recepcion'] else ''
        
        es_emisor = factura['empresa_emisora_id'] == eid
        
        # Obtener detalle
        cur.execute("""
            SELECT * FROM facturas_b2b_detalle WHERE factura_id = %s ORDER BY id
        """, (id,))
        detalle = cur.fetchall()
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/b2b_ver.html',
                          factura=factura,
                          detalle=detalle,
                          es_emisor=es_emisor)


# ===== FACTURACIÓN B2B - CANCELAR =====
@app.route('/facturacion/b2b/<int:id>/cancelar', methods=['POST'])
@require_login
def facturacion_b2b_cancelar(id):
    """Cancelar factura B2B"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Verificar que la factura es de esta empresa y está en estado cancelable
        cur.execute("""
            SELECT * FROM facturas_b2b 
            WHERE id = %s AND empresa_emisora_id = %s AND estado = 'emitida'
        """, (id, eid))
        factura = cur.fetchone()
        
        if not factura:
            flash('❌ No se puede cancelar esta factura', 'danger')
            return redirect(url_for('facturacion_b2b_emitidas'))
        
        motivo = request.form.get('motivo_cancelacion', '')
        
        cur.execute("""
            UPDATE facturas_b2b 
            SET estado = 'cancelada', notas_recepcion = %s, fecha_actualizacion = NOW()
            WHERE id = %s
        """, (f'CANCELADA: {motivo}', id))
        
        # Notificar al receptor
        cur.execute("""
            INSERT INTO facturas_notificaciones 
            (empresa_destino_id, tipo_origen, origen_id, tipo_notificacion, mensaje)
            VALUES (%s, 'b2b', %s, 'cancelada', %s)
        """, (factura['empresa_receptora_id'], id, f'Factura {factura["folio"]} fue cancelada: {motivo}'))
        
        conn.commit()
        flash(f'✅ Factura {factura["folio"]} cancelada', 'info')
        
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('facturacion_b2b_emitidas'))


# ===== CFDI - IMPORTAR =====
@app.route('/cfdi/importar', methods=['GET', 'POST'])
@require_login
def cfdi_importar():
    """Importar archivos XML de CFDI"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        archivos = request.files.getlist('archivos[]')
        importados = 0
        errores = 0
        
        for archivo in archivos:
            if archivo and archivo.filename.lower().endswith('.xml'):
                try:
                    contenido = archivo.read().decode('utf-8')
                    
                    # Parsear XML (simplificado - en producción usar lxml)
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(contenido)
                    
                    # Namespace CFDI
                    ns = {
                        'cfdi': 'http://www.sat.gob.mx/cfd/4',
                        'cfdi3': 'http://www.sat.gob.mx/cfd/3',
                        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
                    }
                    
                    # Intentar CFDI 4.0 primero, luego 3.3
                    comprobante = root if 'Comprobante' in root.tag else None
                    
                    # Extraer datos principales
                    tipo_comprobante = root.get('TipoDeComprobante', 'I')
                    fecha_emision = root.get('Fecha', '')[:10]
                    subtotal = Decimal(root.get('SubTotal', '0'))
                    descuento = Decimal(root.get('Descuento', '0') or '0')
                    total = Decimal(root.get('Total', '0'))
                    forma_pago = root.get('FormaPago', '')
                    metodo_pago = root.get('MetodoPago', '')
                    moneda = root.get('Moneda', 'MXN')
                    
                    # Emisor
                    emisor = root.find('.//cfdi:Emisor', ns) or root.find('.//cfdi3:Emisor', ns)
                    rfc_emisor = emisor.get('Rfc', '') if emisor is not None else ''
                    nombre_emisor = emisor.get('Nombre', '') if emisor is not None else ''
                    
                    # Receptor
                    receptor = root.find('.//cfdi:Receptor', ns) or root.find('.//cfdi3:Receptor', ns)
                    rfc_receptor = receptor.get('Rfc', '') if receptor is not None else ''
                    nombre_receptor = receptor.get('Nombre', '') if receptor is not None else ''
                    uso_cfdi = receptor.get('UsoCFDI', '') if receptor is not None else ''
                    
                    # TimbreFiscalDigital (UUID)
                    timbre = root.find('.//tfd:TimbreFiscalDigital', ns)
                    uuid = timbre.get('UUID', '') if timbre is not None else ''
                    fecha_timbrado = timbre.get('FechaTimbrado', '')[:10] if timbre is not None else ''
                    
                    if not uuid:
                        errores += 1
                        continue
                    
                    # Determinar si es emitido o recibido
                    cur.execute("SELECT rfc FROM empresas WHERE id = %s", (eid,))
                    emp = cur.fetchone()
                    mi_rfc = emp['rfc'] if emp else ''
                    
                    es_emitido = (rfc_emisor.upper() == mi_rfc.upper()) if mi_rfc else False
                    
                    # Calcular IVA (simplificado)
                    iva = total - subtotal + descuento
                    
                    # Verificar duplicado
                    cur.execute("SELECT id FROM cfdi_importados WHERE uuid = %s", (uuid,))
                    if cur.fetchone():
                        errores += 1
                        continue
                    
                    # Insertar CFDI
                    cur.execute("""
                        INSERT INTO cfdi_importados 
                        (empresa_id, uuid, tipo_comprobante, es_emitido,
                         rfc_emisor, nombre_emisor, rfc_receptor, nombre_receptor,
                         fecha_emision, fecha_timbrado, subtotal, descuento, iva, total,
                         forma_pago, metodo_pago, moneda, uso_cfdi, estado_sat, xml_contenido)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'vigente', %s)
                    """, (eid, uuid, tipo_comprobante, es_emitido,
                          rfc_emisor, nombre_emisor, rfc_receptor, nombre_receptor,
                          fecha_emision, fecha_timbrado, subtotal, descuento, iva, total,
                          forma_pago, metodo_pago, moneda, uso_cfdi, contenido))
                    
                    cfdi_id = cur.lastrowid
                    
                    # Extraer conceptos
                    conceptos = root.findall('.//cfdi:Concepto', ns) or root.findall('.//cfdi3:Concepto', ns)
                    for concepto in conceptos:
                        cur.execute("""
                            INSERT INTO cfdi_importados_detalle 
                            (cfdi_id, clave_prod_serv, clave_unidad, descripcion, cantidad, valor_unitario, descuento, importe)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (cfdi_id, 
                              concepto.get('ClaveProdServ', ''),
                              concepto.get('ClaveUnidad', ''),
                              concepto.get('Descripcion', ''),
                              Decimal(concepto.get('Cantidad', '0')),
                              Decimal(concepto.get('ValorUnitario', '0')),
                              Decimal(concepto.get('Descuento', '0') or '0'),
                              Decimal(concepto.get('Importe', '0'))))
                    
                    importados += 1
                    
                except Exception as e:
                    print(f"Error procesando XML: {e}")
                    errores += 1
        
        conn.commit()
        
        if importados > 0:
            flash(f'✅ {importados} CFDI importados correctamente', 'success')
        if errores > 0:
            flash(f'⚠️ {errores} archivos no pudieron importarse (duplicados o errores)', 'warning')
        
        return redirect(url_for('cfdi_listado'))
    
    # GET: Mostrar formulario
    try:
        cur.execute("""
            SELECT id, uuid, es_emitido, nombre_emisor, rfc_emisor, fecha_emision, total
            FROM cfdi_importados 
            WHERE empresa_id = %s 
            ORDER BY fecha_creacion DESC 
            LIMIT 5
        """, (eid,))
        ultimos_cfdi = cur.fetchall()
        for c in ultimos_cfdi:
            c['fecha_fmt'] = c['fecha_emision'].strftime('%d/%m/%Y') if c['fecha_emision'] else ''
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/cfdi_importar.html', ultimos_cfdi=ultimos_cfdi)


# ===== CFDI - LISTADO =====
@app.route('/cfdi')
@require_login
def cfdi_listado():
    """Listado de CFDI importados"""
    eid = g.empresa_id
    
    filtro_tipo = request.args.get('tipo', '')
    filtro_comprobante = request.args.get('comprobante', '')
    filtro_estado = request.args.get('estado_sat', '')
    filtro_desde = request.args.get('desde', '')
    filtro_hasta = request.args.get('hasta', '')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Resumen
        cur.execute("""
            SELECT 
                COUNT(*) as total_cfdi,
                SUM(CASE WHEN es_emitido = 0 THEN 1 ELSE 0 END) as recibidos,
                SUM(CASE WHEN es_emitido = 1 THEN 1 ELSE 0 END) as emitidos,
                SUM(CASE WHEN conciliado = 0 THEN 1 ELSE 0 END) as sin_conciliar
            FROM cfdi_importados 
            WHERE empresa_id = %s
        """, (eid,))
        resumen = cur.fetchone()
        
        # Query principal
        query = """
            SELECT * FROM cfdi_importados 
            WHERE empresa_id = %s
        """
        params = [eid]
        
        if filtro_tipo == 'recibido':
            query += " AND es_emitido = 0"
        elif filtro_tipo == 'emitido':
            query += " AND es_emitido = 1"
        
        if filtro_comprobante:
            query += " AND tipo_comprobante = %s"
            params.append(filtro_comprobante)
        
        if filtro_estado:
            query += " AND estado_sat = %s"
            params.append(filtro_estado)
        
        if filtro_desde:
            query += " AND DATE(fecha_emision) >= %s"
            params.append(filtro_desde)
        if filtro_hasta:
            query += " AND DATE(fecha_emision) <= %s"
            params.append(filtro_hasta)
        
        query += " ORDER BY fecha_emision DESC"
        
        cur.execute(query, params)
        cfdis = cur.fetchall()
        
        for c in cfdis:
            c['fecha_fmt'] = c['fecha_emision'].strftime('%d/%m/%Y') if c['fecha_emision'] else ''
            
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/cfdi_listado.html',
                          cfdis=cfdis,
                          resumen=resumen,
                          filtro_tipo=filtro_tipo,
                          filtro_comprobante=filtro_comprobante,
                          filtro_estado=filtro_estado,
                          filtro_desde=filtro_desde,
                          filtro_hasta=filtro_hasta)


# ===== CFDI - VER DETALLE =====
@app.route('/cfdi/<int:id>')
@require_login
def cfdi_ver(id):
    """Ver detalle de CFDI"""
    eid = g.empresa_id
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT * FROM cfdi_importados 
            WHERE id = %s AND empresa_id = %s
        """, (id, eid))
        cfdi = cur.fetchone()
        
        if not cfdi:
            flash('❌ CFDI no encontrado', 'danger')
            return redirect(url_for('cfdi_listado'))
        
        cfdi['fecha_emision_fmt'] = cfdi['fecha_emision'].strftime('%d/%m/%Y') if cfdi['fecha_emision'] else ''
        cfdi['fecha_timbrado_fmt'] = cfdi['fecha_timbrado'].strftime('%d/%m/%Y %H:%M') if cfdi['fecha_timbrado'] else ''
        
        cur.execute("SELECT * FROM cfdi_importados_detalle WHERE cfdi_id = %s", (id,))
        detalle = cur.fetchall()
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('cobranza/cfdi_ver.html', cfdi=cfdi, detalle=detalle)


# ===== CFDI - CONCILIAR =====
@app.route('/cfdi/<int:id>/conciliar', methods=['POST'])
@require_login
def cfdi_conciliar(id):
    """Conciliar CFDI con compra o venta"""
    eid = g.empresa_id
    
    tipo = request.form.get('tipo_documento', '')
    documento_id = request.form.get('documento_id', '')
    
    if not tipo or not documento_id:
        flash('⚠️ Selecciona un documento', 'warning')
        return redirect(url_for('cfdi_ver', id=id))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        if tipo == 'compra':
            cur.execute("""
                UPDATE cfdi_importados 
                SET conciliado = 1, compra_id = %s 
                WHERE id = %s AND empresa_id = %s
            """, (documento_id, id, eid))
        else:
            cur.execute("""
                UPDATE cfdi_importados 
                SET conciliado = 1, venta_id = %s 
                WHERE id = %s AND empresa_id = %s
            """, (documento_id, id, eid))
        
        conn.commit()
        flash('✅ CFDI conciliado correctamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('cfdi_ver', id=id))


# ===== API - DOCUMENTOS SIN CFDI =====
@app.route('/api/documentos-sin-cfdi')
@require_login
def api_documentos_sin_cfdi():
    """API para obtener documentos sin CFDI vinculado"""
    eid = g.empresa_id
    tipo = request.args.get('tipo', '')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        if tipo == 'compra':
            cur.execute("""
                SELECT c.id, c.folio, c.total, p.nombre as proveedor
                FROM compras c
                LEFT JOIN proveedores p ON p.id = c.proveedor_id
                WHERE c.empresa_id = %s 
                AND c.id NOT IN (SELECT COALESCE(compra_id, 0) FROM cfdi_importados WHERE empresa_id = %s)
                ORDER BY c.fecha DESC
                LIMIT 50
            """, (eid, eid))
        else:
            cur.execute("""
                SELECT v.id, v.id as folio, v.total, 'Público General' as cliente
                FROM ventas v
                WHERE v.empresa_id = %s 
                AND v.id NOT IN (SELECT COALESCE(venta_id, 0) FROM cfdi_importados WHERE empresa_id = %s)
                ORDER BY v.fecha DESC
                LIMIT 50
            """, (eid, eid))
        
        documentos = cur.fetchall()
        
        # Convertir Decimal a float para JSON
        for d in documentos:
            d['total'] = float(d['total']) if d['total'] else 0
        
    finally:
        cur.close()
        conn.close()
    
    return jsonify(documentos)

@app.post("/api/login")
def api_login():
    """
    Endpoint de login para la API.
    Recibe JSON: { "usuario": "...", "password": "..." }
    - usuario: aquí usaremos el CORREO (admin@miapp.com, etc.)
    - password: contraseña en texto plano, se compara con bcrypt.
    """
    data = request.get_json(silent=True) or {}

    # El campo "usuario" de la API será el correo
    correo  = (data.get("usuario") or data.get("correo") or "").strip()
    password = (data.get("password") or "").strip()

    if not correo or not password:
        return jsonify({
            "ok": False,
            "error": "Faltan usuario (correo) o password"
        }), 400

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    # Buscamos por CORREO, no por usuario
    sql = """
        SELECT 
            u.id,
            u.usuario,
            u.nombre,
            u.correo,
            u.empresa_id,
            u.rol,
            u.activo,
            u.contrasena
        FROM usuarios u
        WHERE u.correo = %s
          AND u.activo = 1
        LIMIT 1
    """
    cur.execute(sql, (correo,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return jsonify({
            "ok": False,
            "error": "Usuario o contraseña incorrectos"
        }), 401

    # Verificamos la contraseña con bcrypt
    try:
        hash_bytes = row["contrasena"].encode("utf-8")
        ok_pwd = bcrypt.checkpw(password.encode("utf-8"), hash_bytes)
    except Exception:
        ok_pwd = False

    if not ok_pwd:
        return jsonify({
            "ok": False,
            "error": "Usuario o contraseña incorrectos"
        }), 401

    # Crear token JWT válido por 24 horas
    payload = {
        "id":         row["id"],
        "correo":     row["correo"],
        "rol":        row["rol"],
        "empresa_id": row["empresa_id"],
        "exp":        datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(
        payload,
        app.config["API_JWT_SECRET"],
        algorithm="HS256"
    )

    # Éxito: NO devolvemos la contraseña
    return jsonify({
        "ok": True,
        "token": token,
        "usuario": {
            "id":         row["id"],
            "usuario":    row["usuario"],
            "nombre":     row["nombre"],
            "correo":     row["correo"],
            "empresa_id": row["empresa_id"],
            "rol":        row["rol"],
            "activo":     row["activo"],
        }
    })

@app.get("/api/compras")
@require_token
def api_compras_listado():
    """
    Devuelve el listado de compras (tabla listado_compras).
    Por ahora: últimas 50 compras, ordenadas de más reciente a más antigua.
    Si el token tiene empresa_id, se filtra por esa empresa.
    """
    user = getattr(request, "api_user", {})
    empresa_id = user.get("empresa_id", None)

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    if empresa_id is None:
        sql = """
            SELECT
                c.id,
                c.fecha,
                c.numero_factura,
                c.proveedor,
                c.total,
                c.empresa_id
            FROM listado_compras c
            ORDER BY c.fecha DESC, c.id DESC
            LIMIT 50
        """
        cur.execute(sql)
    else:
        sql = """
            SELECT
                c.id,
                c.fecha,
                c.numero_factura,
                c.proveedor,
                c.total,
                c.empresa_id
            FROM listado_compras c
            WHERE c.empresa_id = %s
            ORDER BY c.fecha DESC, c.id DESC
            LIMIT 50
        """
        cur.execute(sql, (empresa_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "ok": True,
        "total": len(rows),
        "data": rows
    })

@app.route("/api_test_compras")
def api_test_compras():
    # Página sencilla para probar /api/compras desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Compras</title>
    </head>
    <body>
      <h2>Prueba /api/compras (con TOKEN)</h2>

      <p>Pega aquí el token JWT que te devolvió /api/login:</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <br><br>
      <button id="btnProbar">Probar /api/compras</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:900px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token  = document.getElementById('token').value.trim();
          const salida = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/compras...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }

          try {
            const resp = await fetch('/api/compras', {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

@app.get("/api/compras/<int:compra_id>")
@require_token
def api_compra_detalle(compra_id):
    """
    Devuelve encabezado + detalle de una compra.
    Encabezado: listado_compras
    Detalle: detalle_compra
    """
    user = getattr(request, "api_user", {})
    empresa_id = user.get("empresa_id", None)

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    # 1) Encabezado
    if empresa_id is None:
        sql_enc = """
            SELECT
                c.id,
                c.fecha,
                c.numero_factura,
                c.proveedor,
                c.total,
                c.empresa_id
            FROM listado_compras c
            WHERE c.id = %s
            LIMIT 1
        """
        cur.execute(sql_enc, (compra_id,))
    else:
        sql_enc = """
            SELECT
                c.id,
                c.fecha,
                c.numero_factura,
                c.proveedor,
                c.total,
                c.empresa_id
            FROM listado_compras c
            WHERE c.id = %s
              AND c.empresa_id = %s
            LIMIT 1
        """
        cur.execute(sql_enc, (compra_id, empresa_id))

    encabezado = cur.fetchone()

    if not encabezado:
        cur.close()
        conn.close()
        return jsonify({
            "ok": False,
            "error": "Compra no encontrada"
        }), 404

    # 2) Detalle
    sql_det = """
        SELECT
            d.id,
            d.compra_id,
            d.mercancia_id,
            d.producto,
            d.unidades,
            d.precio_unitario,
            d.precio_total
        FROM detalle_compra d
        WHERE d.compra_id = %s
        ORDER BY d.id ASC
    """
    cur.execute(sql_det, (compra_id,))
    detalles = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "ok": True,
        "compra": encabezado,
        "detalles": detalles
    })

@app.route("/api_test_compra_detalle")
def api_test_compra_detalle():
    # Página sencilla para probar /api/compras/<id> desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Compra Detalle</title>
    </head>
    <body>
      <h2>Prueba /api/compras/&lt;id&gt; (con TOKEN)</h2>

      <p>Token JWT (de /api/login):</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <p>ID de la compra (por ejemplo 39):</p>
      <input type="number" id="compra_id" value="39">

      <br><br>
      <button id="btnProbar">Probar /api/compras/&lt;id&gt;</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:900px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token    = document.getElementById('token').value.trim();
          const compraId = document.getElementById('compra_id').value.trim();
          const salida   = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/compras/' + compraId + '...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }
          if (!compraId) {
            salida.textContent = 'Falta el ID de la compra';
            return;
          }

          try {
            const resp = await fetch('/api/compras/' + compraId, {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

@app.route("/api_test_caja_ventas")
def api_test_caja_ventas():
    # Página sencilla para probar /api/caja_ventas desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Caja Ventas</title>
    </head>
    <body>
      <h2>Prueba /api/caja_ventas (con TOKEN)</h2>

      <p>Pega aquí el token JWT que te devolvió /api/login:</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <br><br>
      <button id="btnProbar">Probar /api/caja_ventas</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:900px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token  = document.getElementById('token').value.trim();
          const salida = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/caja_ventas...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }

          try {
            const resp = await fetch('/api/caja_ventas', {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

@app.get("/api/caja_ventas/<int:venta_id>")
@require_token
def api_caja_venta_detalle(venta_id):
    """
    Devuelve encabezado + detalle de un ticket de caja.
    Encabezado: caja_ventas
    Detalle: caja_ventas_detalle (con nombre de mercancia si existe).
    """
    user = getattr(request, "api_user", {})
    empresa_id = user.get("empresa_id", None)

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    # 1) Encabezado del ticket
    if empresa_id is None:
        sql_enc = """
            SELECT
                v.id,
                v.empresa_id,
                v.turno_id,
                v.usuario_id,
                v.folio,
                v.fecha,
                v.subtotal,
                v.iva,
                v.total,
                v.metodo_pago,
                v.estado,
                v.cliente_nombre,
                v.notas,
                v.efectivo_recibido,
                v.cambio,
                v.descuento,
                v.cancelada
            FROM caja_ventas v
            WHERE v.id = %s
            LIMIT 1
        """
        cur.execute(sql_enc, (venta_id,))
    else:
        sql_enc = """
            SELECT
                v.id,
                v.empresa_id,
                v.turno_id,
                v.usuario_id,
                v.folio,
                v.fecha,
                v.subtotal,
                v.iva,
                v.total,
                v.metodo_pago,
                v.estado,
                v.cliente_nombre,
                v.notas,
                v.efectivo_recibido,
                v.cambio,
                v.descuento,
                v.cancelada
            FROM caja_ventas v
            WHERE v.id = %s
              AND (v.empresa_id = %s OR v.empresa_id IS NULL)
            LIMIT 1
        """
        cur.execute(sql_enc, (venta_id, empresa_id))

    encabezado = cur.fetchone()

    if not encabezado:
        cur.close()
        conn.close()
        return jsonify({
            "ok": False,
            "error": "Venta de caja no encontrada"
        }), 404

    # 2) Detalle del ticket
    # Incluimos nombre de mercancia si existe
    sql_det = """
        SELECT
            d.id,
            d.venta_id,
            d.mercancia_id,
            m.nombre AS mercancia_nombre,
            d.cantidad,
            d.precio_unitario,
            d.subtotal
        FROM caja_ventas_detalle d
        LEFT JOIN mercancia m ON m.id = d.mercancia_id
        WHERE d.venta_id = %s
        ORDER BY d.id ASC
    """
    cur.execute(sql_det, (venta_id,))
    detalles = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "ok": True,
        "venta": encabezado,
        "detalles": detalles
    })

@app.route("/api_test_caja_venta_detalle")
def api_test_caja_venta_detalle():
    # Página sencilla para probar /api/caja_ventas/<id> desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Caja Venta Detalle</title>
    </head>
    <body>
      <h2>Prueba /api/caja_ventas/&lt;id&gt; (con TOKEN)</h2>

      <p>Token JWT (de /api/login):</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <p>ID de la venta de caja (por ejemplo 5):</p>
      <input type="number" id="venta_id" value="5">

      <br><br>
      <button id="btnProbar">Probar /api/caja_ventas/&lt;id&gt;</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:900px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token   = document.getElementById('token').value.trim();
          const ventaId = document.getElementById('venta_id').value.trim();
          const salida  = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/caja_ventas/' + ventaId + '...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }
          if (!ventaId) {
            salida.textContent = 'Falta el ID de la venta';
            return;
          }

          try {
            const resp = await fetch('/api/caja_ventas/' + ventaId, {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

# =============================================
# REPORTES B2B
# Agregar a app.py
# =============================================

@app.route('/b2b/reportes')
@require_login
def reportes_b2b():
    """Página principal de reportes B2B"""
    return render_template('b2b/reportes.html')


@app.route('/b2b/reporte/compras')
@require_login
def reporte_compras_b2b():
    """Reporte de compras a proveedores"""
    eid = g.empresa_id
    
    # Filtros
    fecha_inicio = request.args.get('fecha_inicio', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
    proveedor_id = request.args.get('proveedor_id', '')
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Query base
    query = """
        SELECT f.*, ee.nombre as proveedor_nombre
        FROM facturas_b2b f
        JOIN empresas ee ON ee.id = f.empresa_emisora_id
        WHERE f.empresa_receptora_id = %s
          AND f.fecha_emision BETWEEN %s AND %s
          AND f.estado != 'cancelada'
    """
    params = [eid, fecha_inicio, fecha_fin]
    
    if proveedor_id:
        query += " AND f.empresa_emisora_id = %s"
        params.append(proveedor_id)
    
    query += " ORDER BY f.fecha_emision DESC"
    
    cursor.execute(query, params)
    facturas = cursor.fetchall()
    
    # Totales
    cursor.execute("""
        SELECT 
            COUNT(*) as num_facturas,
            COALESCE(SUM(subtotal), 0) as total_subtotal,
            COALESCE(SUM(iva), 0) as total_iva,
            COALESCE(SUM(total), 0) as total_general
        FROM facturas_b2b
        WHERE empresa_receptora_id = %s
          AND fecha_emision BETWEEN %s AND %s
          AND estado != 'cancelada'
    """ + (" AND empresa_emisora_id = %s" if proveedor_id else ""), 
        params)
    totales = cursor.fetchone()
    
    # Compras por proveedor
    cursor.execute("""
        SELECT ee.nombre as proveedor, 
               COUNT(*) as num_facturas,
               SUM(f.total) as total
        FROM facturas_b2b f
        JOIN empresas ee ON ee.id = f.empresa_emisora_id
        WHERE f.empresa_receptora_id = %s
          AND f.fecha_emision BETWEEN %s AND %s
          AND f.estado != 'cancelada'
        GROUP BY ee.id, ee.nombre
        ORDER BY total DESC
    """, (eid, fecha_inicio, fecha_fin))
    por_proveedor = cursor.fetchall()
    
    # Lista de proveedores para filtro
    cursor.execute("""
        SELECT DISTINCT e.id, e.nombre
        FROM relaciones_b2b r
        JOIN empresas e ON e.id = r.empresa_proveedor_id
        WHERE r.empresa_cliente_id = %s AND r.activa = 1
    """, (eid,))
    proveedores = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reporte_compras.html',
        facturas=facturas,
        totales=totales,
        por_proveedor=por_proveedor,
        proveedores=proveedores,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        proveedor_id=proveedor_id
    )


@app.route('/b2b/reporte/ventas')
@require_login
def reporte_ventas_b2b():
    """Reporte de ventas a clientes B2B"""
    eid = g.empresa_id
    
    # Filtros
    fecha_inicio = request.args.get('fecha_inicio', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
    cliente_id = request.args.get('cliente_id', '')
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Query base
    query = """
        SELECT f.*, er.nombre as cliente_nombre
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        WHERE f.empresa_emisora_id = %s
          AND f.fecha_emision BETWEEN %s AND %s
          AND f.estado != 'cancelada'
    """
    params = [eid, fecha_inicio, fecha_fin]
    
    if cliente_id:
        query += " AND f.empresa_receptora_id = %s"
        params.append(cliente_id)
    
    query += " ORDER BY f.fecha_emision DESC"
    
    cursor.execute(query, params)
    facturas = cursor.fetchall()
    
    # Totales
    cursor.execute("""
        SELECT 
            COUNT(*) as num_facturas,
            COALESCE(SUM(subtotal), 0) as total_subtotal,
            COALESCE(SUM(iva), 0) as total_iva,
            COALESCE(SUM(total), 0) as total_general
        FROM facturas_b2b
        WHERE empresa_emisora_id = %s
          AND fecha_emision BETWEEN %s AND %s
          AND estado != 'cancelada'
    """ + (" AND empresa_receptora_id = %s" if cliente_id else ""), 
        params)
    totales = cursor.fetchone()
    
    # Ventas por cliente
    cursor.execute("""
        SELECT er.nombre as cliente, 
               COUNT(*) as num_facturas,
               SUM(f.total) as total
        FROM facturas_b2b f
        JOIN empresas er ON er.id = f.empresa_receptora_id
        WHERE f.empresa_emisora_id = %s
          AND f.fecha_emision BETWEEN %s AND %s
          AND f.estado != 'cancelada'
        GROUP BY er.id, er.nombre
        ORDER BY total DESC
    """, (eid, fecha_inicio, fecha_fin))
    por_cliente = cursor.fetchall()
    
    # Lista de clientes para filtro
    cursor.execute("""
        SELECT DISTINCT e.id, e.nombre
        FROM relaciones_b2b r
        JOIN empresas e ON e.id = r.empresa_cliente_id
        WHERE r.empresa_proveedor_id = %s AND r.activa = 1
    """, (eid,))
    clientes = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reporte_ventas.html',
        facturas=facturas,
        totales=totales,
        por_cliente=por_cliente,
        clientes=clientes,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cliente_id=cliente_id
    )


@app.route('/b2b/reporte/cartera')
@require_login
def reporte_cartera_b2b():
    """Reporte de cartera (CxC) con antigüedad"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Cartera por cliente con antigüedad
    cursor.execute("""
        SELECT 
            e.nombre as cliente,
            COUNT(*) as num_cuentas,
            SUM(c.saldo) as saldo_total,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) <= 0 THEN c.saldo ELSE 0 END) as vigente,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) BETWEEN 1 AND 30 THEN c.saldo ELSE 0 END) as vencido_1_30,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) BETWEEN 31 AND 60 THEN c.saldo ELSE 0 END) as vencido_31_60,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) BETWEEN 61 AND 90 THEN c.saldo ELSE 0 END) as vencido_61_90,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) > 90 THEN c.saldo ELSE 0 END) as vencido_90_mas
        FROM cuentas_por_cobrar c
        JOIN empresas e ON e.id = c.empresa_cliente_id
        WHERE c.empresa_id = %s AND c.estado NOT IN ('pagada', 'cancelada')
        GROUP BY e.id, e.nombre
        ORDER BY saldo_total DESC
    """, (eid,))
    cartera = cursor.fetchall()
    
    # Totales
    cursor.execute("""
        SELECT 
            SUM(saldo) as total,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) <= 0 THEN saldo ELSE 0 END) as vigente,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) BETWEEN 1 AND 30 THEN saldo ELSE 0 END) as vencido_1_30,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) BETWEEN 31 AND 60 THEN saldo ELSE 0 END) as vencido_31_60,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) BETWEEN 61 AND 90 THEN saldo ELSE 0 END) as vencido_61_90,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) > 90 THEN saldo ELSE 0 END) as vencido_90_mas
        FROM cuentas_por_cobrar
        WHERE empresa_id = %s AND estado NOT IN ('pagada', 'cancelada')
    """, (eid,))
    totales = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reporte_cartera.html',
        cartera=cartera,
        totales=totales
    )


@app.route('/b2b/reporte/deudas')
@require_login
def reporte_deudas_b2b():
    """Reporte de deudas (CxP) con antigüedad"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Deudas por proveedor con antigüedad
    cursor.execute("""
        SELECT 
            e.nombre as proveedor,
            COUNT(*) as num_cuentas,
            SUM(c.saldo) as saldo_total,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) <= 0 THEN c.saldo ELSE 0 END) as vigente,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) BETWEEN 1 AND 30 THEN c.saldo ELSE 0 END) as vencido_1_30,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) BETWEEN 31 AND 60 THEN c.saldo ELSE 0 END) as vencido_31_60,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) BETWEEN 61 AND 90 THEN c.saldo ELSE 0 END) as vencido_61_90,
            SUM(CASE WHEN DATEDIFF(CURDATE(), c.fecha_vencimiento) > 90 THEN c.saldo ELSE 0 END) as vencido_90_mas
        FROM cuentas_por_pagar c
        JOIN empresas e ON e.id = c.empresa_proveedor_id
        WHERE c.empresa_id = %s AND c.estado NOT IN ('pagada', 'cancelada')
        GROUP BY e.id, e.nombre
        ORDER BY saldo_total DESC
    """, (eid,))
    deudas = cursor.fetchall()
    
    # Totales
    cursor.execute("""
        SELECT 
            SUM(saldo) as total,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) <= 0 THEN saldo ELSE 0 END) as vigente,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) BETWEEN 1 AND 30 THEN saldo ELSE 0 END) as vencido_1_30,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) BETWEEN 31 AND 60 THEN saldo ELSE 0 END) as vencido_31_60,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) BETWEEN 61 AND 90 THEN saldo ELSE 0 END) as vencido_61_90,
            SUM(CASE WHEN DATEDIFF(CURDATE(), fecha_vencimiento) > 90 THEN saldo ELSE 0 END) as vencido_90_mas
        FROM cuentas_por_pagar
        WHERE empresa_id = %s AND estado NOT IN ('pagada', 'cancelada')
    """, (eid,))
    totales = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reporte_deudas.html',
        deudas=deudas,
        totales=totales
    )


@app.route('/b2b/reporte/flujo_efectivo')
@require_login
def reporte_flujo_efectivo_b2b():
    """Reporte de flujo de efectivo B2B"""
    eid = g.empresa_id
    
    # Filtros
    fecha_inicio = request.args.get('fecha_inicio', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Pagos realizados (egresos)
    cursor.execute("""
        SELECT p.*, e.nombre as proveedor_nombre
        FROM pagos_b2b p
        LEFT JOIN cuentas_por_pagar c ON c.id = p.cuenta_por_pagar_id
        LEFT JOIN empresas e ON e.id = c.empresa_proveedor_id
        WHERE p.empresa_id = %s AND p.tipo = 'pago'
          AND p.fecha BETWEEN %s AND %s
        ORDER BY p.fecha DESC
    """, (eid, fecha_inicio, fecha_fin))
    pagos = cursor.fetchall()
    
    # Cobros recibidos (ingresos)
    cursor.execute("""
        SELECT p.*, e.nombre as cliente_nombre
        FROM pagos_b2b p
        LEFT JOIN cuentas_por_cobrar c ON c.id = p.cuenta_por_cobrar_id
        LEFT JOIN empresas e ON e.id = c.empresa_cliente_id
        WHERE p.empresa_id = %s AND p.tipo = 'cobro'
          AND p.fecha BETWEEN %s AND %s
        ORDER BY p.fecha DESC
    """, (eid, fecha_inicio, fecha_fin))
    cobros = cursor.fetchall()
    
    # Totales por día
    cursor.execute("""
        SELECT 
            DATE(fecha) as dia,
            SUM(CASE WHEN tipo = 'cobro' THEN monto ELSE 0 END) as ingresos,
            SUM(CASE WHEN tipo = 'pago' THEN monto ELSE 0 END) as egresos
        FROM pagos_b2b
        WHERE empresa_id = %s AND fecha BETWEEN %s AND %s
        GROUP BY DATE(fecha)
        ORDER BY dia
    """, (eid, fecha_inicio, fecha_fin))
    por_dia = cursor.fetchall()
    
    # Totales generales
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN tipo = 'cobro' THEN monto ELSE 0 END) as total_cobros,
            SUM(CASE WHEN tipo = 'pago' THEN monto ELSE 0 END) as total_pagos
        FROM pagos_b2b
        WHERE empresa_id = %s AND fecha BETWEEN %s AND %s
    """, (eid, fecha_inicio, fecha_fin))
    totales = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/reporte_flujo.html',
        pagos=pagos,
        cobros=cobros,
        por_dia=por_dia,
        totales=totales,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

# =============================================
# INTEGRACIÓN CIERRE DE TURNO CON B2B
# =============================================
# 
# Este código debe integrarse en tu función de cierre de turno existente.
# Busca la función que cierra el turno y agrega la llamada a generar_orden_compra_desde_turno()
#
# OPCIÓN 1: Si tienes una ruta /cerrar_turno o similar, agrega este código al final
# OPCIÓN 2: Si el cierre es más complejo, crea una función auxiliar
#
# =============================================

# PASO 1: Agrega esta función auxiliar (si no la tienes ya)
def obtener_productos_faltantes_turno(turno_id, empresa_id):
    """
    Analiza el turno y determina qué productos necesitan reabastecimiento.
    Retorna lista de productos a pedir.
    """
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    productos_faltantes = []
    
    # Opción A: Basado en inventario mínimo vs actual
    cursor.execute("""
        SELECT m.id as mercancia_id, m.nombre, m.stock_minimo, m.stock_actual,
               (m.stock_minimo - m.stock_actual) as cantidad_faltante
        FROM mercancia m
        WHERE m.empresa_id = %s 
          AND m.activo = 1
          AND m.stock_actual < m.stock_minimo
          AND m.stock_minimo > 0
    """, (empresa_id,))
    
    for row in cursor.fetchall():
        if row['cantidad_faltante'] > 0:
            productos_faltantes.append({
                'mercancia_id': row['mercancia_id'],
                'nombre': row['nombre'],
                'cantidad': float(row['cantidad_faltante'])
            })
    
    cursor.close()
    db.close()
    
    return productos_faltantes


def obtener_productos_vendidos_turno(turno_id, empresa_id):
    """
    Alternativa: Obtiene productos vendidos durante el turno para reposición.
    Útil si quieres reponer exactamente lo que se vendió.
    """
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    productos = []
    
    # Obtener ventas del turno
    cursor.execute("""
        SELECT vd.mercancia_id, m.nombre, SUM(vd.cantidad) as cantidad_vendida
        FROM ventas_detalle vd
        JOIN ventas v ON v.id = vd.venta_id
        JOIN mercancia m ON m.id = vd.mercancia_id
        WHERE v.turno_id = %s AND v.empresa_id = %s
        GROUP BY vd.mercancia_id, m.nombre
        HAVING cantidad_vendida > 0
    """, (turno_id, empresa_id))
    
    for row in cursor.fetchall():
        productos.append({
            'mercancia_id': row['mercancia_id'],
            'nombre': row['nombre'],
            'cantidad': float(row['cantidad_vendida'])
        })
    
    cursor.close()
    db.close()
    
    return productos


# =============================================
# PASO 2: MODIFICAR TU FUNCIÓN DE CIERRE DE TURNO
# =============================================
# Busca tu función de cierre de turno y agrega el siguiente bloque
# justo ANTES de hacer el commit final o después de guardar el turno.
#
# Ejemplo de cómo quedaría:

"""
@app.route('/cerrar_turno', methods=['POST'])
@require_login
def cerrar_turno():
    eid = g.empresa_id
    uid = g.usuario_id
    turno_id = session.get('turno_id')
    
    # ... tu código existente de cierre de turno ...
    # ... calcular ventas, gastos, mermas, etc ...
    
    # ========== AGREGAR ESTE BLOQUE ==========
    
    # Verificar si hay proveedor B2B configurado
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT COUNT(*) as tiene_proveedor 
        FROM relaciones_b2b 
        WHERE empresa_cliente_id = %s AND activa = 1
    ''', (eid,))
    tiene_proveedor = cursor.fetchone()['tiene_proveedor'] > 0
    cursor.close()
    db.close()
    
    if tiene_proveedor:
        # Obtener productos faltantes (elige una opción)
        # Opción A: Por stock mínimo
        productos_faltantes = obtener_productos_faltantes_turno(turno_id, eid)
        
        # Opción B: Por lo vendido en el turno (comentar/descomentar según necesites)
        # productos_faltantes = obtener_productos_vendidos_turno(turno_id, eid)
        
        if productos_faltantes:
            orden_id = generar_orden_compra_desde_turno(
                turno_id=turno_id,
                empresa_cliente_id=eid,
                usuario_id=uid,
                productos_faltantes=productos_faltantes
            )
            
            if orden_id:
                flash('📦 Orden de compra B2B generada automáticamente', 'info')
    
    # ========== FIN DEL BLOQUE ==========
    
    # ... resto de tu código de cierre ...
    
    flash('✅ Turno cerrado correctamente', 'success')
    return redirect(url_for('dashboard'))
"""


# =============================================
# PASO 3: RUTA ALTERNATIVA - GENERAR OC MANUAL DESDE TURNO
# =============================================
# Si prefieres que el usuario decida cuándo generar la OC:

@app.route('/turno/<int:turno_id>/generar_oc', methods=['POST'])
@require_login
def generar_oc_desde_turno_manual(turno_id):
    """Genera OC manualmente desde un turno cerrado"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Verificar turno
    cursor.execute("""
        SELECT * FROM turnos WHERE id = %s AND empresa_id = %s
    """, (turno_id, eid))
    turno = cursor.fetchone()
    
    if not turno:
        flash('Turno no encontrado', 'danger')
        return redirect(url_for('turnos'))
    
    # Verificar que no exista ya una OC para este turno
    cursor.execute("""
        SELECT id, folio FROM ordenes_compra_b2b 
        WHERE turno_id = %s AND estado != 'cancelada'
    """, (turno_id,))
    oc_existente = cursor.fetchone()
    
    if oc_existente:
        flash(f'Ya existe la orden {oc_existente["folio"]} para este turno', 'warning')
        return redirect(url_for('ver_orden_compra_b2b', orden_id=oc_existente['id']))
    
    cursor.close()
    db.close()
    
    # Obtener productos faltantes
    productos = obtener_productos_faltantes_turno(turno_id, eid)
    
    if not productos:
        flash('No hay productos que requieran reabastecimiento', 'info')
        return redirect(url_for('turnos'))
    
    # Generar OC
    orden_id = generar_orden_compra_desde_turno(turno_id, eid, uid, productos)
    
    if orden_id:
        flash('✅ Orden de compra generada', 'success')
        return redirect(url_for('ver_orden_compra_b2b', orden_id=orden_id))
    else:
        flash('No se pudo generar la orden. Verifica que haya un proveedor configurado.', 'warning')
        return redirect(url_for('turnos'))


# =============================================
# PAGOS B2B
# Agregar a app.py
# =============================================

@app.route('/b2b/registrar_pago/<int:cuenta_id>', methods=['GET', 'POST'])
@require_login
def registrar_pago_cxp(cuenta_id):
    """Registrar pago a una cuenta por pagar"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener cuenta
    cursor.execute("""
        SELECT c.*, e.nombre as proveedor_nombre
        FROM cuentas_por_pagar c
        JOIN empresas e ON e.id = c.empresa_proveedor_id
        WHERE c.id = %s AND c.empresa_id = %s AND c.estado != 'pagada'
    """, (cuenta_id, eid))
    cuenta = cursor.fetchone()
    
    if not cuenta:
        flash('Cuenta no encontrada o ya pagada', 'danger')
        return redirect(url_for('cuentas_por_pagar_b2b'))
    
    if request.method == 'POST':
        monto = float(request.form.get('monto', 0))
        metodo = request.form.get('metodo_pago', 'transferencia')
        referencia = request.form.get('referencia', '')
        notas = request.form.get('notas', '')
        
        if monto <= 0:
            flash('El monto debe ser mayor a 0', 'warning')
            return redirect(url_for('registrar_pago_cxp', cuenta_id=cuenta_id))
        
        if monto > float(cuenta['saldo']):
            flash('El monto no puede ser mayor al saldo pendiente', 'warning')
            return redirect(url_for('registrar_pago_cxp', cuenta_id=cuenta_id))
        
        # Registrar pago
        cursor.execute("""
            INSERT INTO pagos_b2b 
            (empresa_id, tipo, cuenta_por_pagar_id, factura_b2b_id, monto, metodo_pago,
             referencia, notas, registrado_por_usuario_id)
            VALUES (%s, 'pago', %s, %s, %s, %s, %s, %s, %s)
        """, (eid, cuenta_id, cuenta['factura_b2b_id'], monto, metodo, referencia, notas, uid))
        
        pago_id = cursor.lastrowid
        
        # Actualizar cuenta por pagar
        nuevo_pagado = float(cuenta['monto_pagado'] or 0) + monto
        nuevo_saldo = float(cuenta['monto_original']) - nuevo_pagado
        nuevo_estado = 'pagada' if nuevo_saldo <= 0 else 'parcial'
        
        cursor.execute("""
            UPDATE cuentas_por_pagar 
            SET monto_pagado = %s, saldo = %s, estado = %s
            WHERE id = %s
        """, (nuevo_pagado, nuevo_saldo, nuevo_estado, cuenta_id))
        
        # Buscar y actualizar la cuenta por cobrar del proveedor
        if cuenta['factura_b2b_id']:
            cursor.execute("""
                UPDATE cuentas_por_cobrar 
                SET monto_pagado = monto_pagado + %s,
                    saldo = monto_original - (monto_pagado + %s),
                    estado = CASE 
                        WHEN monto_original - (monto_pagado + %s) <= 0 THEN 'pagada'
                        ELSE 'parcial'
                    END
                WHERE factura_b2b_id = %s AND empresa_id = %s
            """, (monto, monto, monto, cuenta['factura_b2b_id'], cuenta['empresa_proveedor_id']))
            
            # Registrar el cobro del lado del proveedor
            cursor.execute("""
                INSERT INTO pagos_b2b 
                (empresa_id, tipo, cuenta_por_cobrar_id, factura_b2b_id, monto, metodo_pago,
                 referencia, notas, registrado_por_usuario_id)
                SELECT %s, 'cobro', cxc.id, %s, %s, %s, %s, %s, %s
                FROM cuentas_por_cobrar cxc
                WHERE cxc.factura_b2b_id = %s AND cxc.empresa_id = %s
            """, (cuenta['empresa_proveedor_id'], cuenta['factura_b2b_id'], monto, metodo, 
                  referencia, f'Pago recibido de cliente', uid,
                  cuenta['factura_b2b_id'], cuenta['empresa_proveedor_id']))
        
        # Notificar al proveedor
        crear_alerta_b2b(
            empresa_id=cuenta['empresa_proveedor_id'],
            rol_destino='cxc',
            tipo='pago',
            titulo='Pago Recibido',
            mensaje=f'Cobro de ${monto:.2f} - {metodo}',
            referencia_tipo='pago_b2b',
            referencia_id=pago_id
        )
        
        db.commit()
        
        if nuevo_estado == 'pagada':
            flash('✅ Cuenta liquidada completamente', 'success')
        else:
            flash(f'✅ Pago de ${monto:.2f} registrado. Saldo: ${nuevo_saldo:.2f}', 'success')
        
        return redirect(url_for('cuentas_por_pagar_b2b'))
    
    cursor.close()
    db.close()
    
    return render_template('b2b/registrar_pago.html', cuenta=cuenta, tipo='pago')


@app.route('/b2b/registrar_cobro/<int:cuenta_id>', methods=['GET', 'POST'])
@require_login
def registrar_cobro_cxc(cuenta_id):
    """Registrar cobro a una cuenta por cobrar"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener cuenta
    cursor.execute("""
        SELECT c.*, e.nombre as cliente_nombre
        FROM cuentas_por_cobrar c
        JOIN empresas e ON e.id = c.empresa_cliente_id
        WHERE c.id = %s AND c.empresa_id = %s AND c.estado != 'pagada'
    """, (cuenta_id, eid))
    cuenta = cursor.fetchone()
    
    if not cuenta:
        flash('Cuenta no encontrada o ya cobrada', 'danger')
        return redirect(url_for('cuentas_por_cobrar_b2b'))
    
    if request.method == 'POST':
        monto = float(request.form.get('monto', 0))
        metodo = request.form.get('metodo_pago', 'transferencia')
        referencia = request.form.get('referencia', '')
        notas = request.form.get('notas', '')
        
        if monto <= 0:
            flash('El monto debe ser mayor a 0', 'warning')
            return redirect(url_for('registrar_cobro_cxc', cuenta_id=cuenta_id))
        
        if monto > float(cuenta['saldo']):
            flash('El monto no puede ser mayor al saldo pendiente', 'warning')
            return redirect(url_for('registrar_cobro_cxc', cuenta_id=cuenta_id))
        
        # Registrar cobro
        cursor.execute("""
            INSERT INTO pagos_b2b 
            (empresa_id, tipo, cuenta_por_cobrar_id, factura_b2b_id, monto, metodo_pago,
             referencia, notas, registrado_por_usuario_id)
            VALUES (%s, 'cobro', %s, %s, %s, %s, %s, %s, %s)
        """, (eid, cuenta_id, cuenta['factura_b2b_id'], monto, metodo, referencia, notas, uid))
        
        # Actualizar cuenta por cobrar
        nuevo_pagado = float(cuenta['monto_pagado'] or 0) + monto
        nuevo_saldo = float(cuenta['monto_original']) - nuevo_pagado
        nuevo_estado = 'pagada' if nuevo_saldo <= 0 else 'parcial'
        
        cursor.execute("""
            UPDATE cuentas_por_cobrar 
            SET monto_pagado = %s, saldo = %s, estado = %s
            WHERE id = %s
        """, (nuevo_pagado, nuevo_saldo, nuevo_estado, cuenta_id))
        
        db.commit()
        
        if nuevo_estado == 'pagada':
            flash('✅ Cuenta cobrada completamente', 'success')
        else:
            flash(f'✅ Cobro de ${monto:.2f} registrado. Saldo: ${nuevo_saldo:.2f}', 'success')
        
        return redirect(url_for('cuentas_por_cobrar_b2b'))
    
    cursor.close()
    db.close()
    
    return render_template('b2b/registrar_pago.html', cuenta=cuenta, tipo='cobro')


@app.route('/b2b/historial_pagos')
@require_login
def historial_pagos_b2b():
    """Historial de pagos y cobros B2B"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, 
               u.nombre as registrado_por_nombre,
               CASE 
                   WHEN p.tipo = 'pago' THEN ep.nombre
                   ELSE ec.nombre
               END as contraparte_nombre
        FROM pagos_b2b p
        LEFT JOIN usuarios u ON u.id = p.registrado_por_usuario_id
        LEFT JOIN cuentas_por_pagar cxp ON cxp.id = p.cuenta_por_pagar_id
        LEFT JOIN cuentas_por_cobrar cxc ON cxc.id = p.cuenta_por_cobrar_id
        LEFT JOIN empresas ep ON ep.id = cxp.empresa_proveedor_id
        LEFT JOIN empresas ec ON ec.id = cxc.empresa_cliente_id
        WHERE p.empresa_id = %s
        ORDER BY p.fecha DESC
        LIMIT 100
    """, (eid,))
    pagos = cursor.fetchall()
    
    # Totales del mes
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN tipo = 'pago' THEN monto ELSE 0 END) as total_pagos,
            SUM(CASE WHEN tipo = 'cobro' THEN monto ELSE 0 END) as total_cobros
        FROM pagos_b2b
        WHERE empresa_id = %s 
          AND MONTH(fecha) = MONTH(CURDATE())
          AND YEAR(fecha) = YEAR(CURDATE())
    """, (eid,))
    totales = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/historial_pagos.html',
        pagos=pagos,
        totales=totales
    )

# =============================================
# DASHBOARD B2B
# Agregar a app.py
# =============================================

@app.route('/b2b/dashboard')
@require_login
def dashboard_b2b():
    """Dashboard resumen del módulo B2B"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # ========== COMO CLIENTE (Compramos) ==========
    
    # Órdenes de compra por estado
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'borrador' THEN 1 ELSE 0 END) as borradores,
            SUM(CASE WHEN estado = 'enviada' THEN 1 ELSE 0 END) as enviadas,
            SUM(CASE WHEN estado = 'facturada' THEN 1 ELSE 0 END) as facturadas,
            SUM(total) as monto_total
        FROM ordenes_compra_b2b
        WHERE empresa_cliente_id = %s AND estado != 'cancelada'
          AND MONTH(fecha_solicitud) = MONTH(CURDATE())
          AND YEAR(fecha_solicitud) = YEAR(CURDATE())
    """, (eid,))
    oc_stats = cursor.fetchone()
    
    # Facturas recibidas pendientes
    cursor.execute("""
        SELECT COUNT(*) as pendientes, SUM(total) as monto
        FROM facturas_b2b
        WHERE empresa_receptora_id = %s AND estado NOT IN ('recibida', 'cancelada')
    """, (eid,))
    facturas_pendientes_recibir = cursor.fetchone()
    
    # Cuentas por pagar
    cursor.execute("""
        SELECT 
            SUM(saldo) as total_deuda,
            SUM(CASE WHEN fecha_vencimiento < CURDATE() THEN saldo ELSE 0 END) as vencido,
            COUNT(*) as num_cuentas
        FROM cuentas_por_pagar
        WHERE empresa_id = %s AND estado NOT IN ('pagada', 'cancelada')
    """, (eid,))
    cxp_stats = cursor.fetchone()
    
    # ========== COMO PROVEEDOR (Vendemos) ==========
    
    # Pedidos recibidos
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'enviada' THEN 1 ELSE 0 END) as nuevos,
            SUM(CASE WHEN estado = 'recibida' THEN 1 ELSE 0 END) as por_facturar,
            SUM(total) as monto_total
        FROM ordenes_compra_b2b
        WHERE empresa_proveedor_id = %s AND estado NOT IN ('borrador', 'cancelada')
          AND MONTH(fecha_solicitud) = MONTH(CURDATE())
          AND YEAR(fecha_solicitud) = YEAR(CURDATE())
    """, (eid,))
    pedidos_stats = cursor.fetchone()
    
    # Facturas emitidas en proceso
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN estado_almacen IN ('pendiente', 'preparando') THEN 1 ELSE 0 END) as en_almacen,
            SUM(CASE WHEN estado_reparto = 'en_camino' THEN 1 ELSE 0 END) as en_reparto,
            SUM(CASE WHEN estado = 'recibida' THEN 1 ELSE 0 END) as entregadas
        FROM facturas_b2b
        WHERE empresa_emisora_id = %s AND estado != 'cancelada'
          AND MONTH(fecha_emision) = MONTH(CURDATE())
          AND YEAR(fecha_emision) = YEAR(CURDATE())
    """, (eid,))
    facturas_emitidas_stats = cursor.fetchone()
    
    # Cuentas por cobrar
    cursor.execute("""
        SELECT 
            SUM(saldo) as total_cartera,
            SUM(CASE WHEN fecha_vencimiento < CURDATE() THEN saldo ELSE 0 END) as vencido,
            COUNT(*) as num_cuentas
        FROM cuentas_por_cobrar
        WHERE empresa_id = %s AND estado NOT IN ('pagada', 'cancelada')
    """, (eid,))
    cxc_stats = cursor.fetchone()
    
    # ========== ALERTAS ACTIVAS ==========
    
    cursor.execute("""
        SELECT tipo, COUNT(*) as cantidad
        FROM alertas_b2b
        WHERE empresa_id = %s AND activa = 1 AND leida = 0
        GROUP BY tipo
    """, (eid,))
    alertas_por_tipo = {row['tipo']: row['cantidad'] for row in cursor.fetchall()}
    
    # ========== ACTIVIDAD RECIENTE ==========
    
    cursor.execute("""
        (SELECT 'oc' as tipo, folio as referencia, fecha_solicitud as fecha, 
                estado, total as monto, 'cliente' as rol
         FROM ordenes_compra_b2b 
         WHERE empresa_cliente_id = %s AND estado != 'cancelada'
         ORDER BY fecha_solicitud DESC LIMIT 3)
        UNION ALL
        (SELECT 'factura' as tipo, folio as referencia, fecha_emision as fecha,
                estado, total as monto, 'proveedor' as rol
         FROM facturas_b2b
         WHERE empresa_emisora_id = %s AND estado != 'cancelada'
         ORDER BY fecha_emision DESC LIMIT 3)
        ORDER BY fecha DESC
        LIMIT 5
    """, (eid, eid))
    actividad_reciente = cursor.fetchall()
    
    # ========== PAGOS DEL MES ==========
    
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN tipo = 'pago' THEN monto ELSE 0 END) as pagos,
            SUM(CASE WHEN tipo = 'cobro' THEN monto ELSE 0 END) as cobros
        FROM pagos_b2b
        WHERE empresa_id = %s
          AND MONTH(fecha) = MONTH(CURDATE())
          AND YEAR(fecha) = YEAR(CURDATE())
    """, (eid,))
    pagos_mes = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'b2b/dashboard.html',
        oc_stats=oc_stats,
        facturas_pendientes_recibir=facturas_pendientes_recibir,
        cxp_stats=cxp_stats,
        pedidos_stats=pedidos_stats,
        facturas_emitidas_stats=facturas_emitidas_stats,
        cxc_stats=cxc_stats,
        alertas_por_tipo=alertas_por_tipo,
        actividad_reciente=actividad_reciente,
        pagos_mes=pagos_mes
    )



# =============================================
# PASO 4: WIDGET PARA MOSTRAR EN DASHBOARD O TURNO
# =============================================
# Agrega este context processor para mostrar OC pendientes

@app.context_processor
def inject_oc_pendientes():
    """Inyecta cantidad de OC pendientes de aprobar"""
    if hasattr(g, 'empresa_id') and g.empresa_id:
        try:
            db = conexion_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*) as pendientes
                FROM ordenes_compra_b2b
                WHERE empresa_cliente_id = %s AND estado = 'borrador'
            """, (g.empresa_id,))
            result = cursor.fetchone()
            cursor.close()
            db.close()
            return {'oc_pendientes': result['pendientes'] if result else 0}
        except:
            pass
    return {'oc_pendientes': 0}

# ===== REGISTRO DE BLUEPRINTS =====
from inventarios.WIP import bp as wip_bp

app.register_blueprint(wip_bp, url_prefix="/inventarios")
# ==================================

@app.route("/api_test_login")
def api_test_login():
    # Página sencilla para probar /api/login desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Login ERP</title>
    </head>
    <body>
      <h2>Prueba /api/login (ERP)</h2>

      <label>
        Usuario:
        <input type="text" id="usuario" value="admin">
      </label>
      <br><br>
      <label>
        Password:
        <input type="password" id="password" value="1234">
      </label>
      <br><br>
      <button id="btnProbar">Probar login API</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta" style="background:#f4f4f4;padding:10px;border:1px solid #ccc;max-width:700px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const usuario  = document.getElementById('usuario').value.trim();
          const password = document.getElementById('password').value.trim();
          const salida   = document.getElementById('respuesta');
          salida.textContent = 'Enviando petición...';

          try {
            const resp = await fetch('/api/login', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ usuario, password })
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

@app.get("/api/ping_secure")
@require_token
def api_ping_secure():
    """
    Endpoint de prueba protegido por token.
    Solo responde si el cliente envía un Bearer token válido.
    """
    # request.api_user viene del payload del JWT (id, correo, rol, etc.)
    return jsonify({
        "ok": True,
        "msg": "Acceso autorizado con token",
        "user": request.api_user
    })

@app.route("/api_test_ping_secure")
def api_test_ping_secure():
    # Página sencilla para probar /api/ping_secure desde el mismo servidor
    return """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Prueba API Ping Secure</title>
    </head>
    <body>
      <h2>Prueba /api/ping_secure (con TOKEN)</h2>

      <p>Pega aquí el token JWT que te devolvió /api/login:</p>
      <textarea id="token" rows="4" cols="80"
        style="width:100%;max-width:800px;"></textarea>

      <br><br>
      <button id="btnProbar">Probar /api/ping_secure</button>

      <h3>Respuesta de la API:</h3>
      <pre id="respuesta"
           style="background:#f4f4f4;padding:10px;border:1px solid #ccc;
                  max-width:800px;white-space:pre-wrap;"></pre>

      <script>
        document.getElementById('btnProbar').addEventListener('click', async () => {
          const token  = document.getElementById('token').value.trim();
          const salida = document.getElementById('respuesta');
          salida.textContent = 'Llamando a /api/ping_secure...';

          if (!token) {
            salida.textContent = 'Falta pegar el token';
            return;
          }

          try {
            const resp = await fetch('/api/ping_secure', {
              method: 'GET',
              headers: {
                'Authorization': 'Bearer ' + token
              }
            });

            const text = await resp.text();
            try {
              const json = JSON.parse(text);
              salida.textContent = JSON.stringify(json, null, 2);
            } catch (e) {
              salida.textContent = 'Respuesta no JSON:\\n\\n' + text;
            }
          } catch (err) {
            salida.textContent = 'Error llamando a la API:\\n\\n' + err;
          }
        });
      </script>
    </body>
    </html>
    """

# ============================================================
# ÓRDENES DE COMPRA AUTOMÁTICAS
# ============================================================

@app.route('/admin/ordenes_auto')
@require_login
def ordenes_auto_lista():
    """Lista de órdenes de compra automáticas"""
    eid = g.empresa_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Obtener órdenes
        cursor.execute("""
            SELECT 
                o.id,
                o.folio,
                o.fecha_generacion,
                o.tipo_orden,
                o.estado,
                o.subtotal,
                o.iva,
                o.total,
                o.solicitado_por,
                r.nombre as revisado_por,
                o.fecha_revision,
                a.nombre as aprobado_por,
                o.fecha_aprobacion,
                COUNT(d.id) as total_items,
                SUM(CASE WHEN d.estado = 'completado' THEN 1 ELSE 0 END) as items_completados
            FROM ordenes_compra_automaticas o
            LEFT JOIN usuarios r ON r.id = o.revisado_por_usuario_id
            LEFT JOIN usuarios a ON a.id = o.aprobado_por_usuario_id
            LEFT JOIN ordenes_compra_automaticas_detalle d ON d.orden_id = o.id
            WHERE o.empresa_id = %s
            GROUP BY o.id
            ORDER BY o.fecha_generacion DESC
            LIMIT 50
        """, (eid,))
        
        ordenes = cursor.fetchall()
        
    finally:
        cursor.close()
        db.close()
    
    return render_template('ordenes_auto/lista.html', ordenes=ordenes)


@app.route('/admin/ordenes_auto/<int:orden_id>')
@require_login
def ordenes_auto_detalle(orden_id):
    """Ver detalle de una orden automática"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Obtener orden
        cursor.execute("""
            SELECT o.*,
                   r.nombre as revisado_por_nombre,
                   a.nombre as aprobado_por_nombre
            FROM ordenes_compra_automaticas o
            LEFT JOIN usuarios r ON r.id = o.revisado_por_usuario_id
            LEFT JOIN usuarios a ON a.id = o.aprobado_por_usuario_id
            WHERE o.id = %s AND o.empresa_id = %s
        """, (orden_id, eid))
        
        orden = cursor.fetchone()
        
        if not orden:
            flash('Orden no encontrada', 'danger')
            return redirect(url_for('ordenes_auto_lista'))
        
        # Obtener items
        cursor.execute("""
            SELECT 
                d.*,
                m.nombre as mercancia_nombre,
                pb.nombre as producto_base_nombre
            FROM ordenes_compra_automaticas_detalle d
            LEFT JOIN mercancia m ON m.id = d.mercancia_id
            LEFT JOIN producto_base pb ON pb.id = d.producto_base_id
            WHERE d.orden_id = %s
            ORDER BY d.dias_pendiente DESC, d.criterio
        """, (orden_id,))
        
        items = cursor.fetchall()
        
    finally:
        cursor.close()
        db.close()
    
    return render_template('ordenes_auto/detalle.html', orden=orden, items=items)


@app.route('/admin/ordenes_auto/<int:orden_id>/revisar', methods=['POST'])
@require_login
def ordenes_auto_revisar(orden_id):
    """Jefe de compras revisa la orden"""
    eid = g.empresa_id
    uid = g.usuario_id
    
    accion = request.form.get('accion')  # 'aprobar' o 'rechazar'
    notas = request.form.get('notas', '')
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar que la orden existe y está pendiente
        cursor.execute("""
            SELECT id, estado
            FROM ordenes_compra_automaticas
            WHERE id = %s AND empresa_id = %s AND estado = 'pendiente_revision'
        """, (orden_id, eid))
        
        orden = cursor.fetchone()
        
        if not orden:
            flash('Orden no encontrada o ya fue procesada', 'warning')
            return redirect(url_for('ordenes_auto_lista'))
        
        if accion == 'aprobar':
            cursor.execute("""
                UPDATE ordenes_compra_automaticas
                SET estado = 'aprobada_jefe',
                    aprobado_por_usuario_id = %s,
                    fecha_aprobacion = NOW(),
                    notas_revision = %s
                WHERE id = %s
            """, (uid, notas, orden_id))
            
            # Actualizar items a estado aprobado
            cursor.execute("""
                UPDATE ordenes_compra_automaticas_detalle
                SET estado = 'aprobado',
                    cantidad_aprobada = cantidad_solicitada
                WHERE orden_id = %s
            """, (orden_id,))
            
            flash('✅ Orden aprobada correctamente', 'success')
            
        elif accion == 'rechazar':
            cursor.execute("""
                UPDATE ordenes_compra_automaticas
                SET estado = 'rechazada',
                    revisado_por_usuario_id = %s,
                    fecha_revision = NOW(),
                    notas_rechazo = %s
                WHERE id = %s
            """, (uid, notas, orden_id))
            
            flash('Orden rechazada', 'info')
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ordenes_auto_detalle', orden_id=orden_id))


@app.route('/admin/ordenes_auto/generar_manual', methods=['POST'])
@require_login
def ordenes_auto_generar_manual():
    """Generar orden automática manualmente (no esperar al CRON)"""
    from orden_compra_auto import crear_orden_compra_automatica
    
    eid = g.empresa_id
    
    try:
        orden_id = crear_orden_compra_automatica(eid)
        
        if orden_id:
            flash(f'✅ Orden automática generada con éxito', 'success')
            return redirect(url_for('ordenes_auto_detalle', orden_id=orden_id))
        else:
            flash('No hay necesidades de compra en este momento', 'info')
            return redirect(url_for('ordenes_auto_lista'))
            
    except Exception as e:
        flash(f'Error al generar orden: {e}', 'danger')
        return redirect(url_for('ordenes_auto_lista'))


# ===== INICIAR SERVIDOR =====
if __name__ == '__main__':
    print("\n" + "="*60)
    print("RUTAS REGISTRADAS EN FLASK:")
    print("="*60)
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30s} {rule.rule}")
    print("="*60 + "\n")
        
    app.run(debug=True, host='0.0.0.0', port=5000)
