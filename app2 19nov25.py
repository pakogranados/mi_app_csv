"""
    app.py - Aplicación Flask para un sistema ERP básico.
    Incluye autenticación de usuarios, control de inventario y registro de compras.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, Blueprint, g
from flask_cors import CORS
from db import conexion_db
from auth_utils import require_role
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timedelta
import re
import bcrypt
from flask_mail import Mail, Message
import secrets
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import csv
from functools import wraps

# ===== CREAR LA APP DE FLASK AQUÍ =====
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')




# Configuración de Mail (si usas email)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Ajusta según tu servidor
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'pakogranados1@gmail.com'
mail = Mail(app)
# =========================================

# ===== CORS =====
CORS(app, resources={r"/api/*": {"origins": "*"}})

# (Opcional) API blueprint
api = Blueprint("api", __name__, url_prefix="/api/v1")

# ===== FUNCIONES HELPER =====
def conexion_db():
    """Configuración de conexión con pool y reconexión automática"""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='miapp',
        autocommit=False,
        pool_name='mypool',
        pool_size=5,
        pool_reset_session=True,
        connect_timeout=10
    )

def require_login(f):
    @wraps(f)
    def _w(*a, **kw):
        if not session.get("usuario_id") or not session.get("empresa_id"):
            abort(401)
        g.empresa_id = int(session["empresa_id"])
        g.usuario_id = int(session["usuario_id"])
        return f(*a, **kw)
    return _w

@app.before_request
def cargar_contexto_empresa_usuario():
    """
    Carga en g.* la empresa y el usuario de la sesión,
    para que cualquier def pueda usar g.empresa_id y g.usuario_id.
    """
    g.usuario_id = session.get("usuario_id")
    g.empresa_id = session.get("empresa_id", 1)   # por defecto 1 si no hay sesión


# ========== TEMPORAL: Forzar sesión para pruebas ==========
@app.before_request
def forzar_sesion():
    """TEMPORAL: Forzar sesión para pruebas"""
    if 'usuario_id' not in session:
        session['usuario_id'] = 1
        session['empresa_id'] = 1
        session['username'] = 'Admin'
        session['rol'] = 'admin'  # ✅ AGREGADO
        print("🔧 Sesión forzada: usuario_id=1, empresa_id=1, rol=admin, username=Admin")
# ==========================================================

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
def caja_historial():
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT id, fecha, total
        FROM caja_ventas
        ORDER BY id DESC
        LIMIT 100
        """
    )
    ventas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("cobranza/caja_historial.html", ventas=ventas)

def precio_pt(mercancia_id: int) -> Decimal:
    """Mismo criterio que catálogo: modo, precio_manual, fallback y AUTO por costo."""
    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    # Trae modo, markup y manual
    cur.execute("""
        SELECT 
          COALESCE(p.modo, 'auto')        AS modo,
          COALESCE(p.markup_pct, 0.30)    AS markup_pct,
          p.precio_manual
        FROM mercancia m
        LEFT JOIN pt_precios p ON p.mercancia_id = m.id
        WHERE m.id = %s
    """, (mercancia_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return Decimal("0.00")

    modo         = row["modo"]
    markup_pct   = Decimal(str(row["markup_pct"]))
    precio_manual = row["precio_manual"]
    costo        = costo_pt(mercancia_id)  # debe devolver Decimal

    if modo == "manual":
        if precio_manual is not None:
            return Decimal(str(precio_manual)).quantize(Decimal("0.01"))
        # fallback a markup si manual está vacío
        return (costo * (Decimal("1") + markup_pct)).quantize(Decimal("0.01"))

    # AUTO por costo y curva
    pct_auto = markup_auto_para_costo(costo)  # devuelve Decimal
    return (costo * (Decimal("1") + pct_auto)).quantize(Decimal("0.01"))

@app.route('/test123')
def test123():
    return "<h1>FUNCIONA</h1><p>Session: " + str(session.get('username', 'No hay usuario')) + "</p>"



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
    from flask import g
    eid = g.empresa_id

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            m.id,
            m.nombre,
            COALESCE(p.modo, 'auto')     AS modo,
            COALESCE(p.markup_pct, 0.30) AS markup_pct,
            p.alias,
            p.precio_manual
        FROM mercancia m
        LEFT JOIN pt_precios p
               ON p.mercancia_id = m.id
              AND p.empresa_id   = %s
        WHERE m.tipo_inventario_id = 3
          AND m.empresa_id         = %s
        ORDER BY m.nombre
    """, (eid, eid))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    items = []
    for r in rows:
        mid           = r["id"]
        nombre        = r["nombre"]
        modo          = r["modo"]
        alias         = r.get("alias")
        markup_pct    = d(r.get("markup_pct") or 0)
        precio_manual = r.get("precio_manual")

        costo = costo_pt(mid)
        label = alias or nombre

        if modo == "manual" and precio_manual is not None:
            precio    = d(precio_manual)
            pct_usado = (precio / costo - d(1)) if costo > 0 else d(0)
        else:
            if modo == "manual":
                pct = markup_pct
            else:
                pct = markup_auto_para_costo(costo)
            precio    = (costo * (d(1) + pct)).quantize(Decimal("0.01"))
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
def apertura_turno():
    """Apertura de turno con fondo de caja, inventario y tipo de cambio"""
    
    print("=" * 50)
    print("DEBUG: Entrando a apertura_turno")
    print(f"DEBUG: Método = {request.method}")
    print(f"DEBUG: user_id en session = {session.get('user_id')}")
    print("=" * 50)
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar si ya hay un turno abierto
        cursor.execute(
            "SELECT * FROM turnos WHERE usuario_id = %s AND estado = 'abierto' ORDER BY fecha_apertura DESC LIMIT 1",
            (session.get('user_id', 12),)
        )
        turno_abierto = cursor.fetchone()
        print(f"DEBUG: Turno abierto encontrado = {turno_abierto}")
        
        if request.method == 'GET':
            print("DEBUG: Es GET, obteniendo productos...")
            # Obtener productos para el conteo
            cursor.execute("""
                SELECT m.id, m.nombre, m.precio
                FROM mercancia m
                WHERE m.tipo = 'PT' AND m.activo = 1
                ORDER BY m.nombre
            """)
            productos = cursor.fetchall()
            print(f"DEBUG: Productos obtenidos = {len(productos)}")
            
            # Sugerencias
            fondo_sugerido = 500.00
            tipo_cambio_sugerido = 20.00
            
            # Obtener último tipo de cambio usado
            cursor.execute(
                "SELECT tipo_cambio FROM turnos ORDER BY fecha_apertura DESC LIMIT 1"
            )
            ultimo_tc = cursor.fetchone()
            if ultimo_tc:
                tipo_cambio_sugerido = ultimo_tc['tipo_cambio']
            
            cursor.close()
            db.close()
            
            print("DEBUG: Renderizando template...")
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
        print("DEBUG: Es POST")
        if turno_abierto:
            cursor.close()
            db.close()
            flash('Ya tienes un turno abierto', 'warning')
            print("DEBUG: Redirigiendo a caja (turno ya abierto)")
            return redirect(url_for('caja'))
        
        fondo_inicial = float(request.form.get('fondo_inicial', 0))
        tipo_cambio = float(request.form.get('tipo_cambio', 20.0))
        notas = request.form.get('notas', '')
        
        # Validaciones
        if fondo_inicial < 0 or tipo_cambio < 0:
            cursor.close()
            db.close()
            flash('Los valores no pueden ser negativos', 'danger')
            print("DEBUG: Valores negativos, redirigiendo...")
            return redirect(url_for('apertura_turno'))
        
        # Insertar turno
        cursor.execute(
            """INSERT INTO turnos 
               (usuario_id, usuario_nombre, fecha_apertura, fondo_inicial, tipo_cambio, estado, notas)
               VALUES (%s, %s, %s, %s, %s, 'abierto', %s)""",
            (
                session.get('user_id', 12),
                session.get('username', 'Admin'),
                datetime.now(),
                fondo_inicial,
                tipo_cambio,
                notas
            )
        )
        turno_id = cursor.lastrowid
        print(f"DEBUG: Turno creado con ID = {turno_id}")
        
        # Guardar inventario inicial
        producto_ids = request.form.getlist('producto_id[]')
        producto_nombres = request.form.getlist('producto_nombre[]')
        cantidades = request.form.getlist('cantidad[]')
        
        for pid, pnombre, cant in zip(producto_ids, producto_nombres, cantidades):
            if cant and cant.strip():
                cursor.execute(
                    """INSERT INTO turno_inventario 
                       (turno_id, producto_id, producto_nombre, cantidad_inicial)
                       VALUES (%s, %s, %s, %s)""",
                    (turno_id, int(pid), pnombre, float(cant))
                )
        
        db.commit()
        cursor.close()
        db.close()
        
        session['turno_actual'] = turno_id
        
        flash(f'✅ Turno #{turno_id} abierto exitosamente', 'success')
        print("DEBUG: Turno abierto exitosamente, redirigiendo a caja")
        return redirect(url_for('caja'))
        
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        print(f"DEBUG ERROR TYPE: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Intentar rollback de forma segura
        try:
            if db and db.is_connected():
                db.rollback()
        except:
            pass
        
        # Cerrar conexiones de forma segura
        try:
            if cursor:
                cursor.close()
        except:
            pass
        
        try:
            if db and db.is_connected():
                db.close()
        except:
            pass
        
        flash(f'Error al abrir turno: {str(e)}', 'danger')
        print("DEBUG: Exception capturada, redirigiendo a apertura_turno")
        return redirect(url_for('apertura_turno'))

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
def agregar_consumo():
    """Agregar un consumo propio"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Verificar turno abierto
        cursor.execute(
            "SELECT id FROM turnos WHERE usuario_id = %s AND estado = 'abierto' LIMIT 1",
            (session.get('user_id', 12),)
        )
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        # Obtener datos del formulario
        producto_id = int(request.form.get('producto_id'))
        cantidad = float(request.form.get('cantidad', 1))
        notas = request.form.get('notas', '')
        
        # Obtener info del producto
        cursor.execute(
            "SELECT nombre, precio FROM mercancia WHERE id = %s",
            (producto_id,)
        )
        producto = cursor.fetchone()

        if not producto:
            cursor.close()
            db.close()
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('consumos_propios'))

        precio_unitario = float(producto['precio'])
        subtotal = cantidad * precio_unitario
        
        # Registrar consumo
        cursor.execute("""
            INSERT INTO consumos_propios 
            (turno_id, fecha, producto_id, producto_nombre, cantidad, 
             precio_unitario, subtotal, usuario_id, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            turno['id'],
            datetime.now(),
            producto_id,
            producto['nombre'],
            cantidad,
            precio_unitario,
            subtotal,
            session.get('user_id', 12),
            notas
        ))
        
        # ===== DESCONTAR DEL INVENTARIO =====
        cursor.execute("""
            UPDATE stock 
            SET unidades = unidades - %s 
            WHERE mercancia_id = %s AND fase = 'PT'
        """, (cantidad, producto_id))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ Consumo registrado: {producto["nombre"]} x {cantidad}', 'success')
        return redirect(url_for('consumos_propios'))
        
    except Exception as e:
        try:
            if db and db.is_connected():
                db.rollback()
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
        except:
            pass
        flash(f'Error al registrar consumo: {str(e)}', 'danger')
        return redirect(url_for('consumos_propios'))

@app.route('/agregar_merma', methods=['POST'])
def agregar_merma():
    """Agregar merma al turno actual"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id FROM turnos WHERE usuario_id = %s AND estado = 'abierto' LIMIT 1",
            (session.get('user_id', 12),)
        )
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        producto_id = int(request.form.get('producto_id'))
        cantidad = float(request.form.get('cantidad', 0))
        motivo = request.form.get('motivo', '')
        
        cursor.execute("SELECT nombre FROM mercancia WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        
        cursor.execute("""
            INSERT INTO turno_mermas 
            (turno_id, producto_id, producto_nombre, cantidad, motivo, fecha, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (turno['id'], producto_id, producto['nombre'], cantidad, motivo, 
              datetime.now(), session.get('user_id', 12)))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ Merma registrada: {cantidad} unidades', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            if db and db.is_connected():
                db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

@app.route('/eliminar_merma/<int:merma_id>', methods=['POST'])
def eliminar_merma(merma_id):
    """Eliminar una merma del turno"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("DELETE FROM turno_mermas WHERE id = %s", (merma_id,))
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Merma eliminada', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

# ==================== HISTORIAL DE TICKETS ====================

@app.route('/historial_tickets')
def historial_tickets():
    """Lista de todos los tickets/ventas"""
    
    # Obtener filtros
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    turno_id = request.args.get('turno_id', '')
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Query base
    query = """
        SELECT 
            v.id,
            v.fecha,
            v.total,
            v.usuario_id,
            u.nombre as cajero,
            t.id as turno_id
        FROM caja_ventas v
        LEFT JOIN usuarios u ON v.usuario_id = u.id
        LEFT JOIN turnos t ON DATE(v.fecha) = DATE(t.fecha_apertura) 
            AND t.usuario_id = v.usuario_id 
            AND t.estado = 'abierto'
        WHERE 1=1
    """
    params = []
    
    # Filtrar por rango de fechas
    if fecha_inicio:
        query += " AND DATE(v.fecha) >= %s"
        params.append(fecha_inicio)
    
    if fecha_fin:
        query += " AND DATE(v.fecha) <= %s"
        params.append(fecha_fin)
    
    # Filtrar por turno
    if turno_id:
        query += " AND t.id = %s"
        params.append(turno_id)
    
    query += " ORDER BY v.fecha DESC LIMIT 500"
    
    cursor.execute(query, params)
    ventas = cursor.fetchall()
    
    # Obtener turnos para el filtro
    cursor.execute("""
        SELECT id, usuario_nombre, fecha_apertura, fecha_cierre 
        FROM turnos 
        ORDER BY fecha_apertura DESC 
        LIMIT 50
    """)
    turnos = cursor.fetchall()
    
    # Calcular totales
    total_ventas = sum(v['total'] for v in ventas)
    cantidad_tickets = len(ventas)
    
    cursor.close()
    db.close()
    
    return render_template(
        'cobranza/historial_tickets.html',
        ventas=ventas,
        turnos=turnos,
        total_ventas=total_ventas,
        cantidad_tickets=cantidad_tickets,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        turno_id=turno_id
    )

@app.route('/ticket/<int:ticket_id>')
def ver_ticket(ticket_id):
    """Ver detalle de un ticket específico"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener venta
    cursor.execute("""
        SELECT 
            v.*,
            u.nombre as cajero
        FROM caja_ventas v
        LEFT JOIN usuarios u ON v.usuario_id = u.id
        WHERE v.id = %s
    """, (ticket_id,))
    venta = cursor.fetchone()
    
    if not venta:
        cursor.close()
        db.close()
        flash('Ticket no encontrado', 'danger')
        return redirect(url_for('historial_tickets'))
    
    # Obtener detalle
    cursor.execute("""
        SELECT 
            d.*,
            m.nombre as producto
        FROM caja_ventas_detalle d
        LEFT JOIN mercancia m ON d.mercancia_id = m.id
        WHERE d.venta_id = %s
    """, (ticket_id,))
    detalle = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'cobranza/ver_ticket.html',
        venta=venta,
        detalle=detalle
    )

# ==================== RETIRO PARCIAL DE EFECTIVO ====================

@app.route('/registrar_retiro', methods=['POST'])
def registrar_retiro():
    """Registrar retiro parcial de efectivo durante el turno"""
    
    # Verificar que haya un turno abierto
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT id FROM turnos WHERE usuario_id = %s AND estado = 'abierto' LIMIT 1",
        (session.get('user_id', 12),)
    )
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
        
        # Calcular efectivo antes y después (opcional, si llevas control)
        # Aquí podrías calcular basado en ventas y retiros anteriores
        
        # Registrar retiro
        cursor.execute("""
            INSERT INTO retiros_efectivo 
            (turno_id, fecha, monto, motivo, notas, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            turno['id'],
            datetime.now(),
            monto,
            motivo,
            notas,
            session.get('user_id', 12)
        ))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ Retiro de ${monto:.2f} registrado exitosamente', 'success')
        return redirect(url_for('caja'))
        
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        print(f"DEBUG ERROR TYPE: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Intentar rollback de forma segura
        try:
            if db and db.is_connected():
                db.rollback()
        except:
            pass
        
        # Cerrar conexiones de forma segura
        try:
            if cursor:
                cursor.close()
        except:
            pass
        
        try:
            if db and db.is_connected():
                db.close()
        except:
            pass
        
        flash(f'Error al abrir turno: {str(e)}', 'danger')
        print("DEBUG: Exception capturada, redirigiendo a apertura_turno")
        return redirect(url_for('apertura_turno'))

@app.route('/historial_retiros')
def historial_retiros():
    """Ver historial de retiros del turno actual o filtrado"""
    
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
        WHERE 1=1
    """
    params = []
    
    if turno_id:
        query += " AND r.turno_id = %s"
        params.append(turno_id)
    
    query += " ORDER BY r.fecha DESC LIMIT 100"
    
    cursor.execute(query, params)
    retiros = cursor.fetchall()
    
    # Obtener turnos para filtro
    cursor.execute("""
        SELECT id, usuario_nombre, fecha_apertura 
        FROM turnos 
        ORDER BY fecha_apertura DESC 
        LIMIT 50
    """)
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
def agregar_gasto():
    """Agregar gasto o compra al turno actual"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id FROM turnos WHERE usuario_id = %s AND estado = 'abierto' LIMIT 1",
            (session.get('user_id', 12),)
        )
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
            (turno_id, fecha, concepto, monto, tipo, notas, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (turno['id'], datetime.now(), concepto, monto, tipo, notas, session.get('user_id', 12)))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash(f'✅ {tipo.capitalize()} registrado: ${monto:.2f}', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            if db and db.is_connected():
                db.rollback()
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))


@app.route('/eliminar_gasto/<int:gasto_id>', methods=['POST'])
def eliminar_gasto(gasto_id):
    """Eliminar un gasto del turno"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("DELETE FROM turno_gastos WHERE id = %s", (gasto_id,))
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Gasto eliminado', 'success')
        return redirect(url_for('cerrar_turno'))
        
    except Exception as e:
        try:
            if db and db.is_connected():
                db.rollback()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('cerrar_turno'))

@app.route('/cerrar_turno', methods=['GET', 'POST'])
def cerrar_turno():
    """Cierre de turno - Primer intento: validar, Segundo: cerrar"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT * FROM turnos WHERE usuario_id = %s AND estado = 'abierto' LIMIT 1",
            (session.get('user_id', 12),)
        )
        turno = cursor.fetchone()
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        if request.method == 'GET':
            # Obtener productos para conteo final (SOLO para anotar)
            cursor.execute("""
                SELECT m.id, m.nombre, m.precio
                FROM mercancia m
                WHERE m.tipo = 'PT' AND m.activo = 1
                ORDER BY m.nombre
            """)
            productos = cursor.fetchall()
            
            # Obtener retiros
            cursor.execute("""
                SELECT COALESCE(SUM(monto), 0) as total_retiros
                FROM retiros_efectivo WHERE turno_id = %s
            """, (turno['id'],))
            retiros = cursor.fetchone()
            
            # Obtener gastos
            cursor.execute("""
                SELECT * FROM turno_gastos WHERE turno_id = %s ORDER BY fecha DESC
            """, (turno['id'],))
            gastos = cursor.fetchall()
            total_gastos = sum(g['monto'] for g in gastos)
            
            # Obtener mermas
            cursor.execute("""
                SELECT * FROM turno_mermas WHERE turno_id = %s ORDER BY fecha DESC
            """, (turno['id'],))
            mermas = cursor.fetchall()
            
            # Verificar si ya hubo un intento previo
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
            # PRIMER INTENTO - Solo validar
            print("🔍 Primer intento de cierre - Validando...")
            
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
                
                # Obtener cantidad inicial
                cursor.execute("""
                    SELECT cantidad_inicial FROM turno_inventario
                    WHERE turno_id = %s AND producto_id = %s
                """, (turno['id'], pid))
                inicial = cursor.fetchone()
                cant_inicial = float(inicial['cantidad_inicial']) if inicial else 0
                
                # Obtener consumos propios
                cursor.execute("""
                    SELECT COALESCE(SUM(cantidad), 0) as total_consumos
                    FROM consumos_propios
                    WHERE turno_id = %s AND producto_id = %s
                """, (turno['id'], pid))
                consumos = cursor.fetchone()
                cant_consumos = float(consumos['total_consumos'])
                
                # Obtener mermas
                cursor.execute("""
                    SELECT COALESCE(SUM(cantidad), 0) as total_mermas
                    FROM turno_mermas
                    WHERE turno_id = %s AND producto_id = %s
                """, (turno['id'], pid))
                mermas_prod = cursor.fetchone()
                cant_mermas = float(mermas_prod['total_mermas'])
                
                # Calcular ventas teóricas
                ventas_teoricas = cant_inicial - cant_consumos - cant_mermas - cant_final
                valor_diferencia = abs(ventas_teoricas) * pprecio
                
                if valor_diferencia > 70:
                    diferencias_inventario.append({
                        'producto': pnombre,
                        'diferencia': ventas_teoricas,
                        'valor': valor_diferencia
                    })
            
            if diferencias_inventario:
                # Hay diferencias significativas
                session[f'turno_{turno["id"]}_validado'] = True
                flash('⚠️ ATENCIÓN: Favor de verificar el conteo de mercancía, mermas y consumos ya que existe una diferencia significativa.', 'warning')
                
                for dif in diferencias_inventario:
                    flash(f"• {dif['producto']}: Diferencia de {dif['diferencia']:.2f} unidades (${dif['valor']:.2f})", 'warning')
                
                flash('Si los datos son correctos, presiona "Cerrar Turno" nuevamente para confirmar.', 'info')
                
                cursor.close()
                db.close()
                return redirect(url_for('cerrar_turno'))
            else:
                # No hay diferencias, proceder directamente
                session[f'turno_{turno["id"]}_validado'] = True
        
        # SEGUNDO INTENTO o sin diferencias - CERRAR DEFINITIVAMENTE
        print("✅ Cerrando turno definitivamente...")
        
        # Guardar inventario final y calcular ventas
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
            
            # Guardar inventario final
            cursor.execute("""
                INSERT INTO turno_inventario_final 
                (turno_id, producto_id, producto_nombre, cantidad_final)
                VALUES (%s, %s, %s, %s)
            """, (turno['id'], pid, pnombre, cant_final))
            
            # Obtener inicial
            cursor.execute("""
                SELECT cantidad_inicial FROM turno_inventario
                WHERE turno_id = %s AND producto_id = %s
            """, (turno['id'], pid))
            inicial = cursor.fetchone()
            cant_inicial = float(inicial['cantidad_inicial']) if inicial else 0
            
            # Consumos
            cursor.execute("""
                SELECT COALESCE(SUM(cantidad), 0) as total
                FROM consumos_propios
                WHERE turno_id = %s AND producto_id = %s
            """, (turno['id'], pid))
            consumos = cursor.fetchone()
            cant_consumos = float(consumos['total'])
            
            # Mermas
            cursor.execute("""
                SELECT COALESCE(SUM(cantidad), 0) as total
                FROM turno_mermas
                WHERE turno_id = %s AND producto_id = %s
            """, (turno['id'], pid))
            mermas = cursor.fetchone()
            cant_mermas = float(mermas['total'])
            
            # Calcular ventas
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
        
        # Guardar arqueo de dinero
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
            (turno_id, billetes_20, billetes_50, billetes_100, billetes_200, 
             billetes_500, dolares, monedas, total_efectivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (turno['id'], billetes_20, billetes_50, billetes_100, billetes_200,
              billetes_500, dolares, monedas, conteo_final))
        
        # Obtener totales
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total FROM retiros_efectivo
            WHERE turno_id = %s
        """, (turno['id'],))
        total_retiros = float(cursor.fetchone()['total'])
        
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total FROM turno_gastos
            WHERE turno_id = %s
        """, (turno['id'],))
        total_gastos = float(cursor.fetchone()['total'])
        
        # Calcular resultado
        total_corte = total_ventas_calculado
        efectivo_deberia_haber = total_ventas_calculado - total_retiros - total_gastos
        diferencia_efectivo = conteo_final - efectivo_deberia_haber
        
        # Actualizar turno
        notas_cierre = request.form.get('notas_cierre', '')
        
        cursor.execute("""
            UPDATE turnos 
            SET estado = 'cerrado',
                fecha_cierre = %s,
                fondo_final = %s,
                total_ventas = %s,
                diferencia = %s,
                notas = CONCAT(COALESCE(notas, ''), '\nCierre: ', %s)
            WHERE id = %s
        """, (datetime.now(), conteo_final + float(turno['fondo_inicial']),
              total_ventas_calculado, diferencia_efectivo, notas_cierre, turno['id']))
        
        db.commit()
        cursor.close()
        db.close()
        
        # Limpiar session
        session.pop(f'turno_{turno["id"]}_validado', None)
        session.pop('turno_actual', None)
        
        # Mostrar resumen
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
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            if db and db.is_connected():
                db.rollback()
        except:
            pass
        
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('apertura_turno'))

# ==================== CONSUMOS PROPIOS ====================

@app.route('/consumos_propios')
def consumos_propios():
    """Interfaz para registrar consumos propios antes del cierre"""
    
    try:
        print("=" * 50)
        print("DEBUG CONSUMOS: Entrando a consumos_propios")
        print(f"DEBUG: user_id = {session.get('user_id')}")
        
        db = conexion_db()
        cursor = db.cursor(dictionary=True)
        
        # Verificar turno abierto
        cursor.execute(
            "SELECT * FROM turnos WHERE usuario_id = %s AND estado = 'abierto' LIMIT 1",
            (session.get('user_id', 12),)
        )
        turno = cursor.fetchone()
        
        print(f"DEBUG: Turno encontrado = {turno}")
        print("=" * 50)
        
        if not turno:
            cursor.close()
            db.close()
            flash('No tienes un turno abierto', 'warning')
            return redirect(url_for('apertura_turno'))
        
        # Obtener productos disponibles
        cursor.execute("""
            SELECT 
                m.id, 
                m.nombre, 
                m.precio,
                0 as existencias
            FROM mercancia m
            WHERE m.tipo = 'PT' AND m.activo = 1
            ORDER BY m.nombre
        """)
        productos = cursor.fetchall()
        
        print(f"DEBUG: Productos obtenidos = {len(productos)}")
        
        # Obtener consumos del turno
        cursor.execute("""
            SELECT 
                c.*,
                u.nombre as usuario
            FROM consumos_propios c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.turno_id = %s
            ORDER BY c.fecha DESC
        """, (turno['id'],))
        consumos = cursor.fetchall()
        
        print(f"DEBUG: Consumos obtenidos = {len(consumos)}")
        
        # Total de consumos
        total_consumos = sum(c['subtotal'] for c in consumos)
        
        cursor.close()
        db.close()
        
        print("DEBUG: Renderizando template consumos_propios.html")
        
        return render_template(
            'cobranza/consumos_propios.html',
            turno=turno,
            productos=productos,
            consumos=consumos,
            total_consumos=total_consumos
        )
    
    except Exception as e:
        print("=" * 50)
        print(f"❌ ERROR EN CONSUMOS_PROPIOS: {str(e)}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals() and db.is_connected():
                db.close()
        except:
            pass
        
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('apertura_turno'))
        
@app.route('/eliminar_consumo/<int:consumo_id>', methods=['POST'])
def eliminar_consumo(consumo_id):
    """Eliminar un consumo propio"""
    
    db = conexion_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("DELETE FROM consumos_propios WHERE id = %s", (consumo_id,))
        db.commit()
        cursor.close()
        db.close()
        
        flash('✅ Consumo eliminado', 'success')
        return redirect(url_for('consumos_propios'))
        
    except Exception as e:
        try:
            if db and db.is_connected():
                db.rollback()
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
        except:
            pass
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('consumos_propios'))



# --- Vistas ---

@app.get("/pt/catalogo")
@require_login
def pt_catalogo():
    if session.get("rol") != "admin":
        flash("Acceso no autorizado.", "danger")
        return redirect("/login")

    items = _pt_items_all()  # ya debe estar filtrando por empresa_id
    return render_template("inventarios/PT/pt_catalogo.html", items=items)


@app.post("/pt/catalogo_guardar")
@require_login
def pt_catalogo_guardar():
    if session.get("rol") != "admin":
        flash("Acceso no autorizado.", "danger")
        return redirect("/login")

    from flask import g
    eid = g.empresa_id  # empresa actual

    ids            = request.form.getlist("id[]")
    modos          = request.form.getlist("modo[]")
    markups        = request.form.getlist("manual_pct[]")
    precios_manual = request.form.getlist("precio_manual[]")
    aliases        = request.form.getlist("alias[]")

    conn = conexion_db()
    cur  = conn.cursor()

    for i, mid in enumerate(ids):
        mid = int(mid)

        modo = (modos[i] if i < len(modos) else "auto") or "auto"
        alias = (aliases[i].strip() or None) if i < len(aliases) else None

        # % manual (texto a decimal fraccional; si vacío => 0)
        mk_raw = markups[i].strip() if i < len(markups) else ""
        mk_val = d(mk_raw) / d(100) if mk_raw not in ("", None) else d("0")

        # precio manual (solo aplica en MANUAL; si vacío => None)
        pm_raw = precios_manual[i].strip() if i < len(precios_manual) else ""
        pm_val = d(pm_raw) if pm_raw not in ("", None) else None

        if modo == "auto":
            precio_manual = None
            markup_pct    = mk_val
        else:
            precio_manual = pm_val
            markup_pct    = mk_val

        if markup_pct is None:
            markup_pct = d("0")

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
    cur.close()
    conn.close()

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

@api.get("/inventario/<int:mercancia_id>/movimientos")
def api_movimientos(mercancia_id: int):
        
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
    """
    Registra un movimiento de inventario en inventario_movimientos
    ya con soporte multiempresa.
    """
    from flask import g, session
    from datetime import date as _date

    # 1) Obtener empresa_id de la sesión / g
    eid = getattr(g, "empresa_id", None) or session.get("empresa_id") or 1

    if fecha is None:
        fecha = _date.today()

    conn = conexion_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventario_movimientos
            (empresa_id, tipo_inventario_id, mercancia_id,
             fecha, tipo_movimiento, unidades, precio_unitario, referencia)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        eid,
        tipo_inventario_id,
        mercancia_id,
        fecha,
        tipo_movimiento,
        unidades,
        precio_unitario,
        referencia
    ))

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

from dotenv import load_dotenv
import os

load_dotenv()

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
        FROM production
        WHERE empresa_id = %s
          AND UPPER(status) IN ('OPEN','IN_PROGRESS')
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

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """
    Maneja el registro de nuevos usuarios.
    - Verifica si el correo ya existe.
    - Hashea la contraseña antes de guardar.
    - Asigna rol por defecto 'editor'.
    """
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena'].encode('utf-8')

        contrasena_hash = bcrypt.hashpw(contrasena, bcrypt.gensalt())

        try:
            conn = conexion_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM usuarios WHERE correo = %s", (correo,))
            existe = cursor.fetchone()

            if existe:
                flash('El correo ya está registrado. Usa otro.', 'danger')
                return redirect('/registro')

            cursor.execute(
                "INSERT INTO usuarios (nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s)",
                (nombre, correo, contrasena_hash.decode('utf-8'), 'editor'))

            conn.commit()
            cursor.close()
            conn.close()
            flash('Usuario registrado con éxito', 'success')
            return redirect('/login')

        except (mysql.connector.Error, ValueError) as e:
            flash(f'Error controlado: {e}', 'danger')
            return redirect('/registro')

    return render_template('registro.html')

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
    """
    Procesa el inicio de sesión del usuario.
    """
    mensaje = ''
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena'].encode('utf-8')

        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario and bcrypt.checkpw(contrasena, usuario['contrasena'].encode('utf-8')):
            # Guardar datos de sesión
            session['usuario_id'] = usuario['id']
            session['rol'] = usuario.get('rol', 'admin')

            # Muy importante: empresa_id del usuario
            session['empresa_id'] = usuario.get('empresa_id', 1)

            return redirect('/panel')
        else:
            mensaje = 'Usuario o contraseña incorrectos'

    return render_template('login.html', mensaje=mensaje)


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
    """
    Cierra sesión del usuario.
    """
    session.clear()
    return redirect('/login')


@app.route('/dashboard')
def dashboard():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 🔹 Inventario total
    cursor.execute("""
        SELECT COUNT(*) AS total_items, SUM(entradas - salidas) AS total_stock
        FROM inventario
    """)
    inventario = cursor.fetchone()

    # 🔹 Producciones activas
    cursor.execute("SELECT COUNT(*) AS en_proceso FROM production WHERE status = 'IN_PROGRESS'")
    produccion = cursor.fetchone()

    # 🔹 Productos terminados disponibles
    cursor.execute("""
        SELECT SUM(unidades) AS terminados
        FROM inventario_movimientos
        WHERE tipo_inventario_id = 3 AND tipo_movimiento = 'ENTRADA'
    """)
    terminados = cursor.fetchone()

    cursor.close(); conn.close()

    return render_template(
        'dashboard.html',
        inventario=inventario,
        produccion=produccion,
        terminados=terminados
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


@app.route('/admin/areas_produccion')
@require_role('admin')
def listar_areas():
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM areas_produccion ORDER BY nombre;")
    areas = cur.fetchall()
    cur.close(); conn.close()
    return render_template('inventarios/WIP/areas_list.html', areas=areas)


@app.route('/admin/areas_produccion/nueva', methods=['GET', 'POST'])
@require_role('admin')
def nueva_area():
    if request.method == 'POST':
        nombre = request.form['nombre']
        conn = conexion_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO areas_produccion (nombre, activo) VALUES (%s, TRUE)", (nombre,))
        conn.commit()
        cur.close(); conn.close()
        flash('Área registrada correctamente.', 'success')
        return redirect(url_for('listar_areas'))
    return render_template('inventarios/WIP/areas_form.html')


@app.route('/admin/areas_produccion/editar/<int:id>', methods=['GET', 'POST'])
@require_role('admin')
def editar_area(id):
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nombre = request.form['nombre']
        activo = 'activo' in request.form
        cur.execute("UPDATE areas_produccion SET nombre=%s, activo=%s WHERE id=%s", (nombre, activo, id))
        conn.commit()
        cur.close(); conn.close()
        flash('Área actualizada correctamente.', 'success')
        return redirect(url_for('listar_areas'))
    cur.execute("SELECT * FROM areas_produccion WHERE id=%s", (id,))
    area = cur.fetchone()
    cur.close(); conn.close()
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
    return render_template("listado_compras.html", compras=compras)
    



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
def catalogo_cuentas():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    q = (request.args.get('q') or '').strip()

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
          id, codigo, nombre, tipo, naturaleza, nivel,
          permite_subcuentas, padre_id, padre_codigo, padre_nombre, hijos
        FROM vw_cuentas_contables
    """
    params = []
    if q:
        sql += " WHERE codigo LIKE %s OR nombre LIKE %s OR padre_codigo LIKE %s OR padre_nombre LIKE %s"
        like = f"%{q}%"
        params = [like, like, like, like]
    sql += " ORDER BY codigo"

    cursor.execute(sql, params)
    cuentas = cursor.fetchall()
    cursor.close()
    conn.close()

    # --- helper local (borra si ya tienes nivel_from_code global) ---
    def _nivel_from_codigo(code: str | None):
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
    # ---------------------------------------------------------------

    # Mapeo a columnas estilo Excel:
    # - Nivel 1  -> CUENTA
    # - Nivel 2  -> si padre es nivel 1 => CUENTA MAYOR; si padre es nivel 2 => SUBCUENTA
    # - Nivel 3  -> SUB-SUBCUENTA
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
            'id': r['id'],  # <-- añade esto
            'codigo': r['codigo'],
            'cuenta': col_cuenta,
            'cuenta_mayor': col_mayor,
            'subcuenta': col_sub,
            'subsubcuenta': col_subsub
        })

    # Enviamos 'filas' para que el template pinte cada nombre en su columna
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
def unidades_medida():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        if not nombre:
            flash('Nombre requerido.', 'warning')
            return redirect(url_for('unidades_medida'))

        conn = conexion_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM unidades_medida WHERE UPPER(nombre)=UPPER(%s)", (nombre,))
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
            cursor.close(); conn.close()

    # GET
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM unidades_medida ORDER BY nombre")
    unidades = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('unidades_medida.html', unidades=unidades)

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
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT
                pb.id                                  AS id,
                pb.nombre                              AS producto,
                COALESCE(SUM(i.inventario_inicial),0)  AS inventario_inicial,
                COALESCE(SUM(i.entradas),0)            AS entradas,
                COALESCE(SUM(i.salidas),0)             AS salidas,
                COALESCE(SUM(i.inventario_inicial+i.entradas-i.salidas),0) AS disponible,
                NULL                                   AS valor_inventario,
                MAX(i.aprobado)                        AS aprobado,
                MIN(m.id)                              AS mercancia_id
            FROM producto_base pb
            JOIN mercancia m       ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id     = m.id
            WHERE pb.activo = 1
              AND m.tipo_inventario_id = %s          -- filtro MP=1, PT=3
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre ASC
        """, (tipo_inventario_id,))
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

@app.route('/inventario')
def mostrar_inventario():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)     
    try:
        cur.execute("""
            SELECT
                pb.id AS id,
                pb.nombre AS producto,
                COALESCE(SUM(i.inventario_inicial), 0) AS inventario_inicial,
                COALESCE(SUM(i.entradas), 0)          AS entradas,
                COALESCE(SUM(i.salidas), 0)           AS salidas,
                COALESCE(SUM(i.inventario_inicial + i.entradas - i.salidas), 0) AS disponible,
                NULL AS valor_inventario,
                MAX(i.aprobado) AS aprobado,
                MIN(m.id) AS mercancia_id
            FROM producto_base pb
            JOIN mercancia m       ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id    = m.id
            WHERE pb.activo = 1
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre ASC
        """)
        inventario = cur.fetchall()
    finally:
        cur.close(); conn.close()


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
def inventario_movimientos_producto_base(producto_base_id):
    """Movimientos agrupados por producto base (ej: todos los aceites)"""
    if 'rol' not in session:
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 1) Obtener nombre del producto base y mercancías asociadas
    cursor.execute("""
        SELECT pb.nombre as producto_base_nombre,
               GROUP_CONCAT(m.id) as mercancia_ids,
               GROUP_CONCAT(m.nombre SEPARATOR ', ') as mercancias_nombres
        FROM producto_base pb
        LEFT JOIN mercancia m ON m.producto_base_id = pb.id
        WHERE pb.id = %s
        GROUP BY pb.id, pb.nombre
    """, (producto_base_id,))
    
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

    # 2) Query MODIFICADA: WHERE mercancia_id IN (...)
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
            UNION ALL
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                im.referencia AS documento, '' AS fuente, im.unidades,
                NULL AS contenido_neto_total, im.precio_unitario,
                (im.unidades*im.precio_unitario) AS importe,
                NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders})
            AND im.tipo_inventario_id = 1
            AND UPPER(im.tipo_movimiento) <> 'COMPRA'
            AND im.unidades > 0
            AND im.tipo_movimiento IS NOT NULL
            AND im.tipo_movimiento <> ''
        ) t
        ORDER BY t.fecha_raw ASC, t.documento ASC
        """
        cursor.execute(sql, mercancia_ids + mercancia_ids)
        movimientos = cursor.fetchall()

    elif almacen_id in (2, 3):
        placeholders = ','.join(['%s'] * len(mercancia_ids))
        cursor.execute(f"""
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                   im.referencia AS documento, '' AS fuente, im.unidades,
                   NULL AS contenido_neto_total, im.precio_unitario,
                   (im.unidades*im.precio_unitario) AS importe, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders}) AND im.tipo_inventario_id = %s
            ORDER BY im.fecha ASC, im.id ASC  # Ascendente (más antiguo primero)
        """, mercancia_ids + [almacen_id])
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
            UNION ALL
            SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                   im.referencia AS documento, '' AS fuente, im.unidades,
                   NULL AS contenido_neto_total, im.precio_unitario,
                   (im.unidades*im.precio_unitario) AS importe,
                   NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders})
              AND UPPER(im.tipo_movimiento) <> 'COMPRA'
        ) t
        ORDER BY t.fecha_raw DESC, t.documento DESC
        """
        cursor.execute(sql, mercancia_ids + mercancia_ids)
        movimientos = cursor.fetchall()

    # 3) Construir tablas (igual que antes)
    rows = []
    pu = 0.0  # Precio unitario promedio
    saldo_u = 0.0
    saldo_mx = 0.0
    for m in movimientos:
        tipo = (m.get('tipo_movimiento') or '').strip().lower()
        es_entrada = tipo in ('entrada','compra')
        contenido = m.get('contenido_neto_total')
        
        # ENTRADAS
        if es_entrada:
            entrada_u = float(contenido) if (contenido and float(contenido) > 0) else float(m.get('unidades') or 0.0)
            pu_entrada = float(m.get('precio_unitario') or 0.0)  # Precio de compra
            entrada_mx = entrada_u * pu_entrada
            
            saldo_u += entrada_u
            saldo_mx += entrada_mx
            
            # ✅ RECALCULAR COSTO PROMEDIO PONDERADO
            pu = saldo_mx / saldo_u if saldo_u > 0 else 0.0
            
            salida_u = 0.0
            salida_mx = 0.0
        
        # SALIDAS
        elif tipo == 'salida':
            salida_u = float(m.get('unidades') or 0.0)
            salida_mx = salida_u * pu  # ✅ USA EL COSTO PROMEDIO, NO el precio_unitario del movimiento
            
            saldo_u -= salida_u
            saldo_mx -= salida_mx
            
            entrada_u = 0.0
            entrada_mx = 0.0
            
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
    
    # Saldo final (último valor)
    saldo_final_u = rows[-1]["saldo_u"] if rows else 0.0
    saldo_final_mx = rows[-1]["saldo_mx"] if rows else 0.0
    pu_final = rows[-1]["pu"] if rows else 0.0

    cursor.close()
    conn.close()
    
    return render_template('inventarios/inventario_movimientos.html',
                           producto=producto,
                           tabla_unidades=tabla_unidades,
                           tabla_pesos=tabla_pesos,
                           # ✅ PASAR TOTALES
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
def mostrar_inventario_mp():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # ✅ OBTENER TODOS LOS PRODUCTOS BASE
        cur.execute("""
            SELECT
                pb.id AS producto_base_id,
                pb.id AS id,  -- ✅ Para la primera columna del template
                pb.nombre AS producto,
                MIN(m.id) AS mercancia_id,  -- ✅ Para los enlaces (singular)
                GROUP_CONCAT(m.id) AS mercancia_ids,
                COALESCE(MAX(i.inventario_inicial), 0) AS inventario_inicial,
                MAX(i.aprobado) AS aprobado
            FROM producto_base pb
            JOIN mercancia m ON m.producto_base_id = pb.id
            LEFT JOIN inventario i ON i.mercancia_id = m.id
            WHERE pb.activo = 1 AND m.tipo = 'MP'
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre
        """)
        inventario = cur.fetchall()
        
        # ✅ CALCULAR SALDO FINAL CON LA MISMA LÓGICA DE inventario_movimientos_producto_base
        for item in inventario:
            mercancia_ids = [int(x) for x in item['mercancia_ids'].split(',')]
            placeholders = ','.join(['%s'] * len(mercancia_ids))
            
            # Query idéntica a la que funciona en movimientos-producto-base (almacen=1)
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
                UNION ALL
                SELECT im.fecha AS fecha_raw, DATE_FORMAT(im.fecha,'%d/%b/%Y') AS fecha_fmt,
                    im.referencia AS documento, '' AS fuente, im.unidades,
                    NULL AS contenido_neto_total, im.precio_unitario,
                    (im.unidades*im.precio_unitario) AS importe,
                    NULL AS detalle, NULL AS compra_id, im.tipo_movimiento
                FROM inventario_movimientos im
                WHERE im.mercancia_id IN ({placeholders})
                AND im.tipo_inventario_id = 1
                AND UPPER(im.tipo_movimiento) <> 'COMPRA'
                AND im.unidades > 0
                AND im.tipo_movimiento IS NOT NULL
                AND im.tipo_movimiento <> ''
            ) t
            ORDER BY t.fecha_raw ASC, t.documento ASC
            """
            cur.execute(sql, mercancia_ids + mercancia_ids)
            movimientos = cur.fetchall()
            
            # ✅ APLICAR COSTEO PROMEDIO PONDERADO (lógica idéntica)
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
                    
                    # Recalcular precio promedio ponderado
                    pu = saldo_mx / saldo_u if saldo_u > 0 else 0.0
                    
                elif tipo == 'salida':
                    salida_u = float(m.get('unidades') or 0.0)
                    salida_mx = salida_u * pu  # ✅ USA EL COSTO PROMEDIO
                    
                    saldo_u -= salida_u
                    saldo_mx -= salida_mx
                    salidas_total += salida_u
            
            # ✅ ASIGNAR VALORES FINALES (igual que en movimientos-producto-base)
            item['entradas'] = entradas_total
            item['salidas'] = salidas_total
            item['disponible'] = saldo_u  # ✅ ÚLTIMO SALDO DE UNIDADES
            item['valor_inventario'] = saldo_mx  # ✅ ÚLTIMO SALDO EN PESOS
            
        # 🐛 DEBUG
        print(f"\n{'='*60}")
        print(f"DEBUG Inventario MP: {len(inventario)} productos base")
        print(f"{'='*60}")
        for item in inventario:
            print(f"📦 {item['producto']}")
            print(f"   Inicial: {item['inventario_inicial']}")
            print(f"   Entradas: {item['entradas']}")
            print(f"   Salidas: {item['salidas']}")
            print(f"   Disponible: {item['disponible']}")
            print(f"   Valor: ${item['valor_inventario']:.2f}")
            print(f"   {'-'*50}")
            
    finally:
        cur.close()
        conn.close()

    return render_template('inventarios/mp/inventario.html', inventario=inventario)

    
@app.route('/inventarios/produccion/listar')
def listar_produccion():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, p.fecha, pt.nombre AS producto, p.cantidad_producida, p.estado
        FROM produccion p
        JOIN productos_terminados pt ON pt.id = p.producto_terminado_id
        ORDER BY p.fecha ASC
    """)
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
def mostrar_inventario_wip():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # ✅ OBTENER TODOS LOS PRODUCTOS WIP
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
            LEFT JOIN inventario i ON i.mercancia_id = m.id
            WHERE pb.activo = 1 AND m.tipo = 'WIP'
            GROUP BY pb.id, pb.nombre
            ORDER BY pb.nombre
        """)
        inventario = cur.fetchall()
        
        # ✅ CALCULAR SALDO FINAL CON COSTEO PROMEDIO PONDERADO
        for item in inventario:
            mercancia_ids = [int(x) for x in item['mercancia_ids'].split(',')]
            placeholders = ','.join(['%s'] * len(mercancia_ids))
            
            # Query para movimientos de WIP (tipo_inventario_id = 2)
            sql = f"""
            SELECT im.fecha AS fecha_raw,
                   im.tipo_movimiento,
                   im.unidades,
                   im.precio_unitario
            FROM inventario_movimientos im
            WHERE im.mercancia_id IN ({placeholders})
            AND im.tipo_inventario_id = 2
            AND im.unidades > 0
            AND im.tipo_movimiento IS NOT NULL
            AND im.tipo_movimiento <> ''
            ORDER BY im.fecha ASC, im.id ASC
            """
            cur.execute(sql, mercancia_ids)
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
            
        # 🐛 DEBUG
        print(f"\n{'='*60}")
        print(f"DEBUG Inventario WIP: {len(inventario)} productos")
        print(f"{'='*60}")
        for item in inventario:
            print(f"📦 {item['producto']}")
            print(f"   Inicial: {item['inventario_inicial']}")
            print(f"   Entradas: {item['entradas']}")
            print(f"   Salidas: {item['salidas']}")
            print(f"   Disponible: {item['disponible']}")
            print(f"   Valor: ${item['valor_inventario']:.2f}")
            print(f"   {'-'*50}")
            
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
def orden_detalle(orden_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        # 🔹 1. Datos principales de la orden
        cur.execute("""
            SELECT op.id, op.fecha_creacion, op.cantidad_programada, op.estado,
                   op.observaciones, m.nombre AS producto
            FROM orden_produccion op
            JOIN mercancia m ON op.producto_id = m.id
            WHERE op.id = %s
        """, (orden_id,))
        orden = cur.fetchone()

        if not orden:
            flash('Orden de producción no encontrada.', 'warning')
            return redirect(url_for('list_production'))

        # 🔹 2. Fases asociadas al proceso
        cur.execute("""
            SELECT a.nombre AS area, f.descripcion, f.duracion, f.estado
            FROM orden_fase f
            JOIN areas a ON f.area_id = a.id
            WHERE f.orden_id = %s
            ORDER BY f.id ASC
        """, (orden_id,))
        fases = cur.fetchall()

        # 🔹 3. Materias primas asociadas a la orden
        cur.execute("""
            SELECT mp.nombre, om.cantidad_usada, om.costo_unitario
            FROM orden_material om
            JOIN mercancia mp ON om.mp_id = mp.id
            WHERE om.orden_id = %s
            ORDER BY mp.nombre
        """, (orden_id,))
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
def new_production():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Captura datos del formulario
        producto_id = (request.form.get('pt_id') or request.form.get('finished_product_id') or '').strip()
        cantidad_planificada = (request.form.get('planned_quantity') or '').strip()
        fecha = (request.form.get('date') or '').strip()

        # Validaciones
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
            # 1️⃣ Verifica que el producto exista y sea tipo PT
            cur.execute("SELECT 1 FROM mercancia WHERE id=%s AND tipo='PT' LIMIT 1", (producto_id,))
            if not cur.fetchone():
                flash('El producto seleccionado no existe o no es de tipo PT.', 'danger')
                return redirect(url_for('new_production'))

            # 2️⃣ Exige proceso definido y activo
            cur.execute("SELECT 1 FROM procesos WHERE pt_id=%s AND activo=1 LIMIT 1", (producto_id,))
            if not cur.fetchone():
                flash('Define el proceso de producción antes de crear la orden.', 'warning')
                return redirect(url_for('recetas_proceso', pt_id=producto_id))

            # 3️⃣ Crea la nueva orden en tabla orden_produccion
            cur.execute("""
                INSERT INTO orden_produccion (producto_id, cantidad_programada, fecha_creacion, estado)
                VALUES (%s, %s, %s, 'pendiente')
            """, (producto_id, cantidad, fecha))
            conn.commit()

            flash('Orden de producción creada correctamente.', 'success')
            return redirect(url_for('list_production'))

        except Exception as e:
            conn.rollback()
            flash(f'Error al crear la orden: {e}', 'danger')
            return redirect(url_for('new_production'))
        finally:
            try: cur.close()
            except: pass
            try: conn.close()
            except: pass

    # GET → muestra formulario con PT disponibles
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, nombre
        FROM mercancia
        WHERE tipo='PT'
        ORDER BY nombre
    """)
    productos = cur.fetchall()
    cur.close(); conn.close()

    return render_template('inventarios/WIP/orden_nueva.html', productos=productos)


@app.route('/production')
def list_production():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

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
            ORDER BY op.fecha_creacion DESC, op.id DESC
        """)
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
def cerrar_orden_produccion(orden_id):
    """Cierra una orden de producción: descarga el WIP, genera el producto terminado y cambia el estado a 'cerrada'."""
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        # 🔹 Verificar que la orden existe y no esté cerrada
        cur.execute("""
            SELECT op.id, op.estado, op.cantidad_programada, m.id AS producto_id, m.nombre AS producto
            FROM orden_produccion op
            JOIN mercancia m ON op.producto_id = m.id
            WHERE op.id = %s
        """, (orden_id,))
        orden = cur.fetchone()

        if not orden:
            flash('Orden no encontrada.', 'warning')
            return redirect(url_for('list_production'))

        if orden['estado'] == 'cerrada':
            flash('Esta orden ya está cerrada.', 'info')
            return redirect(url_for('list_production'))

        # 🔹 Calcular el costo promedio total del WIP asociado
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN tipo_movimiento='ENTRADA' THEN unidades * precio_unitario END),0)
                - COALESCE(SUM(CASE WHEN tipo_movimiento='SALIDA' THEN unidades * precio_unitario END),0) AS costo_total
            FROM inventario_movimientos
            WHERE tipo_inventario_id = 2
              AND referencia LIKE %s
        """, (f"OP{orden_id}%",))
        costo_wip = float(cur.fetchone()['costo_total'] or 0)

        cantidad_final = float(orden['cantidad_programada'])
        pu_pt = (costo_wip / cantidad_final) if cantidad_final > 0 else 0

        # 🔹 Registrar salida de WIP
        cur.execute("""
            INSERT INTO inventario_movimientos
            (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
            VALUES (2, %s, 'SALIDA', %s, %s, %s, NOW())
        """, (orden['producto_id'], cantidad_final, pu_pt, f"OP{orden_id}-CIERRE"))

        # 🔹 Registrar entrada a inventario de Producto Terminado
        cur.execute("""
            INSERT INTO inventario_movimientos
            (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
            VALUES (3, %s, 'ENTRADA', %s, %s, %s, NOW())
        """, (orden['producto_id'], cantidad_final, pu_pt, f"OP{orden_id}-CIERRE"))

        # 🔹 Cambiar estado de la orden a 'cerrada'
        cur.execute("UPDATE orden_produccion SET estado='cerrada' WHERE id=%s", (orden_id,))
        conn.commit()

        flash(f"Orden de producción #{orden_id} cerrada correctamente. Costo total: ${costo_wip:,.2f}", 'success')
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
def admin_proceso_detalle(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True, buffered=True)  # <-- buffered
    try:
        # --- POST ---
        if request.method == 'POST':
            a = request.form.get('accion')

            if a == 'add_insumo':
                cur.execute("""
                    INSERT INTO procesos_insumos
                       (proceso_id, mercancia_id, unidad, cantidad, merma_pct)
                    VALUES (%s,%s,%s,%s,%s)
                """, (id,
                      request.form['mercancia_id'],
                      request.form.get('unidad', ''),
                      str(cantidad),            # 2 decimales
                      str(merma)))              # 2 decimales
                conn.commit()
                flash('Insumo agregado', 'success')

            elif a == 'del_insumo':
                cur.execute("DELETE FROM procesos_insumos WHERE id=%s AND proceso_id=%s",
                            (request.form['item_id'], id))
                conn.commit()
                flash('Insumo eliminado', 'info')

            elif a == 'add_operacion':
                orden   = int(request.form.get('orden', 1) or 1)
                dur_min = int(request.form.get('duracion_minutos', 0) or 0)
                depende_de = request.form.get('depende_de') or None
                cur.execute("""
                    INSERT INTO procesos_etapas
                       (proceso_id, orden, area_id, nombre, descripcion, duracion_minutos, depende_de, instrucciones)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (id, orden,
                      request.form['area_id'],
                      request.form.get('nombre', ''),
                      request.form.get('descripcion', ''),
                      dur_min, depende_de,
                      request.form.get('instrucciones', '')))
                conn.commit()
                flash('Operación agregada', 'success')

            elif a == 'del_operacion':
                cur.execute("DELETE FROM procesos_etapas WHERE id=%s AND proceso_id=%s",
                            (request.form['etapa_id'], id))
                conn.commit()
                flash('Operación eliminada', 'info')

            elif a == 'add_check':
                cur.execute("""
                    INSERT INTO procesos_etapas_checklist(etapa_id, texto, orden)
                    VALUES (
                      %s,
                      %s,
                      COALESCE((SELECT MAX(orden)+1
                                  FROM procesos_etapas_checklist
                                 WHERE etapa_id=%s), 0)
                    )
                """, (request.form['etapa_id'],
                      request.form['texto'],
                      request.form['etapa_id']))
                conn.commit()
                flash('Checklist agregado', 'success')

        # --- almacén MP ---
        try:
            mp_id = get_mp_id()
        except NameError:
            cur.execute("""
                SELECT id FROM tipos_inventario WHERE clave='MP' LIMIT 1
            """)
            r = cur.fetchone()
            mp_id = r['id'] if r else None

        # ---- cabecera ----
        cur.execute("SELECT id, nombre, descripcion FROM procesos WHERE id=%s", (id,))
        proceso = cur.fetchone()
        if not proceso:
            abort(404)

        # áreas del proceso
        cur.execute("""
            SELECT a.id, a.nombre
              FROM procesos_areas pa
              JOIN areas_produccion a ON a.id = pa.area_id
             WHERE pa.proceso_id = %s
             ORDER BY a.nombre
        """, (id,))
        areas_proc = cur.fetchall()

        # catálogos
        cur.execute("SELECT id, nombre FROM areas_produccion ORDER BY nombre")
        areas = cur.fetchall()

        # ¿mercancia tiene columna tipo_inventario_id?
        cur.execute("""
            SELECT COUNT(*) AS has_col
              FROM INFORMATION_SCHEMA.COLUMNS
             WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'mercancia'
               AND COLUMN_NAME = 'tipo_inventario_id'
        """)
        has_col = cur.fetchone()['has_col'] == 1

        # catálogo de mercancias para combo de insumos
        if has_col and mp_id:
            cur.execute("""
                SELECT id, nombre
                  FROM mercancia
                 WHERE tipo_inventario_id = %s
                 ORDER BY nombre
            """, (mp_id,))
        else:
            cur.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
        mercancias = cur.fetchall()

        # componentes del proceso con costo de referencia
        # Nota: NO usar mi.tipo_inventario_id. Esa columna no existe en movimientos_inventario.
        cur.execute("""
            SELECT
                pi.id,
                pi.unidad,
                ROUND(pi.cantidad, 2)  AS cantidad,
                ROUND(pi.merma_pct, 2) AS merma_pct,
                m.id AS mercancia_id,
                m.nombre AS mercancia,
                (
                    SELECT ROUND(mov.costo_unitario, 2)
                    FROM movimientos_inventario mov
                    WHERE mov.producto_id = pi.mercancia_id
                    ORDER BY mov.fecha DESC, mov.id DESC
                    LIMIT 1
                ) AS costo_ref
                FROM procesos_insumos pi
                JOIN mercancia m ON m.id = pi.mercancia_id
                WHERE pi.proceso_id = %s
                ORDER BY pi.id
        """, (id,))
        componentes = cur.fetchall()

        # operaciones y checklist
        cur.execute("""
            SELECT pe.id, pe.orden, pe.nombre, pe.descripcion, pe.duracion_minutos,
                   pe.depende_de, dep.nombre AS depende_de_nombre,
                   a.nombre AS area, pe.instrucciones
              FROM procesos_etapas pe
              JOIN areas_produccion a ON a.id = pe.area_id
              LEFT JOIN procesos_etapas dep ON dep.id = pe.depende_de
             WHERE pe.proceso_id = %s
             ORDER BY pe.orden, pe.id
        """, (id,))
        operaciones = cur.fetchall()

        cur.execute("""
            SELECT c.id, c.etapa_id, c.texto, c.done, c.orden
              FROM procesos_etapas_checklist c
             WHERE c.etapa_id IN (SELECT id FROM procesos_etapas WHERE proceso_id = %s)
             ORDER BY c.etapa_id, c.orden, c.id
        """, (id,))
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
def admin_procesos():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        # --- POST ---
        if request.method == 'POST':
            accion = request.form.get('accion')

            if accion == 'add_proceso':
                nombre = request.form['nombre'].strip()
                descripcion = request.form.get('descripcion','').strip()
                pt_id_raw = request.form.get('pt_id')
                pt_id = int(pt_id_raw) if pt_id_raw and pt_id_raw.isdigit() else None

                if pt_id is not None:
                    cur.execute("SELECT id FROM mercancia WHERE id=%s", (pt_id,))
                    if not cur.fetchone():
                        flash('Producto terminado no válido', 'danger')
                        return redirect(url_for('admin_procesos'))

                cur.execute("""
                    INSERT INTO procesos (pt_id, nombre, descripcion)
                    VALUES (%s, %s, %s)
                """, (pt_id, nombre, descripcion))
                conn.commit()
                proc_id = cur.lastrowid

                for a in request.form.getlist('areas[]'):
                    if a:
                        cur.execute(
                            "INSERT IGNORE INTO procesos_areas(proceso_id, area_id) VALUES(%s,%s)",
                            (proc_id, a)
                        )

                ims_id  = request.form.getlist('insumo_mercancia_id[]')
                ims_udm = request.form.getlist('insumo_unidad[]')
                ims_qty = request.form.getlist('insumo_cantidad[]')
                ims_mer = request.form.getlist('insumo_merma[]')
                for mid, udm, qty, mer in zip(ims_id, ims_udm, ims_qty, ims_mer):
                    if mid and qty:
                        cur.execute("""
                            INSERT INTO procesos_insumos(proceso_id, mercancia_id, unidad, cantidad, merma_pct)
                            VALUES(%s,%s,%s,%s,%s)
                        """, (proc_id, mid, (udm or ''), qty, (mer or 0)))
                conn.commit()
                return redirect(url_for('admin_proceso_detalle', id=proc_id))

            elif accion == 'add_insumo':
                cantidad = r2(request.form['cantidad'])
                merma    = r2(request.form.get('merma_pct') or 0)
                cur.execute("""
                    INSERT INTO procesos_insumos
                    (proceso_id, mercancia_id, unidad, cantidad, merma_pct)
                    VALUES (%s,%s,%s,%s,%s)
                """, (request.form['proceso_id'],
                    request.form['mercancia_id'],
                    request.form.get('unidad', ''),
                    str(cantidad),
                    str(merma)))
                conn.commit()
                flash('Insumo agregado', 'success')

            elif accion == 'del_insumo':
                cur.execute(
                    "DELETE FROM procesos_insumos WHERE id=%s AND proceso_id=%s",
                    (request.form['item_id'], request.form['proceso_id'])
                )
                conn.commit()
                flash('Insumo eliminado', 'info')

        # --- MP id (si no hay, no filtrar) ---
        try:
            mp_id = get_mp_id()
        except NameError:
            cur.execute("SELECT id FROM tipos_inventario WHERE clave='MP'")
            row = cur.fetchone()
            mp_id = row['id'] if row else None
        mp_filter = bool(mp_id)

        # Catálogos: áreas
        cur.execute("SELECT id, nombre FROM areas_produccion ORDER BY nombre")
        areas = cur.fetchall()

        # Catálogo: materias primas
        if mp_filter:
            cur.execute("""
                SELECT id, nombre
                FROM mercancia
                WHERE tipo_inventario_id = %s
                ORDER BY nombre
            """, (mp_id,))
        else:
            cur.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
        mercancias = cur.fetchall()

        # Catálogo: productos terminados (soporta esquema con tipo_inventario_id o con tipo='PT')
        cur.execute("""
            SELECT id, nombre
            FROM mercancia
            WHERE (
                CASE
                  WHEN EXISTS(
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME='mercancia'
                      AND COLUMN_NAME='tipo_inventario_id'
                  )
                  THEN tipo_inventario_id = (SELECT id FROM tipos_inventario WHERE clave='PT' LIMIT 1)
                  ELSE tipo = 'PT'
                END
            )
            ORDER BY nombre
        """)
        pts = cur.fetchall()

        # Procesos + áreas
        cur.execute("""
            SELECT p.id, p.nombre, p.descripcion,
                   COALESCE(GROUP_CONCAT(a.nombre ORDER BY a.nombre SEPARATOR ' + '), '—') AS areas_txt
            FROM procesos p
            LEFT JOIN procesos_areas pa ON pa.proceso_id = p.id
            LEFT JOIN areas_produccion a ON a.id = pa.area_id
            GROUP BY p.id, p.nombre, p.descripcion
            ORDER BY areas_txt, p.nombre
        """)
        procesos = cur.fetchall()

        # Insumos con costo ref
        if mp_filter:
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
                 WHERE m.tipo_inventario_id = %s
                 ORDER BY m.nombre
            """, (mp_id,))
        else:
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
                 ORDER BY m.nombre
            """)
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

@app.get('/pt/recetas')
def recetas_list():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT 
                m.id   AS pt_id,
                m.nombre AS pt_nombre,
                COUNT(p.id) AS procesos_totales,
                SUM(CASE WHEN p.activo = 1 THEN 1 ELSE 0 END) AS procesos_activos
            FROM mercancia m
            LEFT JOIN procesos p ON p.pt_id = m.id
            WHERE m.tipo = 'PT'
            GROUP BY m.id, m.nombre
            ORDER BY m.nombre
        """)
        pts = cur.fetchall()
    finally:
        cur.close(); conn.close()

    # OJO: plantilla en templates/inventarios/PT/recetas_list.html
    return render_template('inventarios/PT/recetas_list.html', pts=pts)


# Alias para compatibilidad con la URL anterior
@app.route('/recetas')
def recetas_legacy_redirect():
    return redirect(url_for('recetas_list'), code=301)



@app.route('/recetas/<int:pt_id>', methods=['GET','POST'])
def recetas_proceso(pt_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger'); return redirect(url_for('login'))
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        # PT
        cur.execute("SELECT id, nombre FROM mercancia WHERE id=%s AND tipo='PT'", (pt_id,))
        pt = cur.fetchone()
        if not pt:
            flash("PT no encontrado.", "danger"); return redirect(url_for('recetas_list'))

        if request.method == 'POST':
            nombre = (request.form.get('nombre') or '').strip() or f"Proceso de {pt['nombre']}"
            descripcion = (request.form.get('descripcion') or '').strip()
            # upsert 1 proceso por PT
            cur.execute("SELECT id FROM procesos WHERE pt_id=%s", (pt_id,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE procesos SET nombre=%s, descripcion=%s, activo=1 WHERE id=%s",
                            (nombre, descripcion, row['id']))
                proceso_id = row['id']
            else:
                cur.execute("INSERT INTO procesos (pt_id, nombre, descripcion, activo) VALUES (%s,%s,%s,1)",
                            (pt_id, nombre, descripcion))
                proceso_id = cur.lastrowid
            conn.commit()
            flash("Proceso guardado.", "success")
            return redirect(url_for('recetas_proceso', pt_id=pt_id))

        # GET: cargar proceso + pasos + insumos
        cur.execute("SELECT * FROM procesos WHERE pt_id=%s", (pt_id,))
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

            # insumos por paso
            for p in pasos:
                cur.execute("""
                  SELECT pin.id, pin.cantidad_por_lote,
                         m.nombre AS mp_nombre, m.id AS mp_id,
                         u.nombre AS unidad
                  FROM paso_insumos pin
                  JOIN mercancia m ON m.id=pin.mp_id
                  LEFT JOIN unidades_medida u ON u.id=pin.unidad_id
                  WHERE pin.paso_id=%s
                """, (p['id'],))
                p['insumos'] = cur.fetchall()

        # catálogos
        cur.execute("SELECT id, nombre FROM areas_produccion ORDER BY nombre")
        areas = cur.fetchall()
        cur.execute("SELECT id, nombre FROM mercancia WHERE tipo='MP' ORDER BY nombre")
        mps = cur.fetchall()
        cur.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        ums = cur.fetchall()

        return render_template('inventarios/WIP/recetas_proceso.html',
                            pt=pt, proceso=proceso, pasos=pasos,
                            areas=areas, mps=mps, ums=ums)
    finally:
        cur.close(); conn.close()


@app.post('/recetas/<int:pt_id>/pasos/agregar')
def recetas_paso_agregar(pt_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.','danger'); return redirect(url_for('login'))
    nombre = (request.form.get('nombre') or '').strip() or 'Paso'
    area_id_s = (request.form.get('area_id') or '').strip()
    requiere = 1 if (request.form.get('requiere_validez') == '1') else 0
    minutos_s = (request.form.get('minutos_estimados') or '').strip()
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM procesos WHERE pt_id=%s", (pt_id,))
        proc = cur.fetchone()
        if not proc:
            flash("Primero guarda el encabezado del proceso.", "warning")
            return redirect(url_for('recetas_proceso', pt_id=pt_id))

        area_id = int(area_id_s) if area_id_s.isdigit() else None
        minutos = int(minutos_s) if minutos_s.isdigit() else None

        cur.execute("SELECT COALESCE(MAX(orden),0)+1 AS nexto FROM proceso_pasos WHERE proceso_id=%s", (proc['id'],))
        nexto = cur.fetchone()['nexto']
        cur.execute("""
            INSERT INTO proceso_pasos (proceso_id, orden, nombre, area_id, requiere_validez, minutos_estimados)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (proc['id'], nexto, nombre, area_id, requiere, minutos))
        conn.commit()
        flash("Paso agregado.", "success")
    finally:
        cur.close(); conn.close()
    return redirect(url_for('recetas_proceso', pt_id=pt_id))


@app.post('/recetas/pasos/<int:paso_id>/insumos/agregar')
def recetas_paso_insumo_agregar(paso_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.','danger'); return redirect(url_for('login'))
    mp_id_s = (request.form.get('mp_id') or '').strip()
    cant_s  = (request.form.get('cantidad_por_lote') or '').strip()
    um_s    = (request.form.get('unidad_id') or '').strip()
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        # paso→proceso→pt_id para redirect
        cur.execute("""
            SELECT pp.id, pr.pt_id
            FROM proceso_pasos pp
            JOIN procesos pr ON pr.id=pp.proceso_id
            WHERE pp.id=%s
        """, (paso_id,))
        row = cur.fetchone()
        if not row: 
            flash("Paso no encontrado.","danger"); return redirect(url_for('recetas_list'))

        if not (mp_id_s.isdigit() and cant_s):
            flash("Selecciona MP y cantidad.","danger")
            return redirect(url_for('recetas_proceso', pt_id=row['pt_id']))

        um_id = int(um_s) if um_s.isdigit() else None
        cur.execute("""
          INSERT INTO paso_insumos (paso_id, mp_id, cantidad_por_lote, unidad_id)
          VALUES (%s,%s,%s,%s)
        """, (paso_id, int(mp_id_s), float(cant_s), um_id))
        conn.commit()
        flash("Insumo agregado.", "success")
        return redirect(url_for('recetas_proceso', pt_id=row['pt_id']))
    finally:
        cur.close(); conn.close()


@app.post('/recetas/pasos/<int:paso_id>/eliminar')
def recetas_paso_eliminar(paso_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.','danger'); return redirect(url_for('login'))
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
          SELECT pr.pt_id
          FROM proceso_pasos pp
          JOIN procesos pr ON pr.id=pp.proceso_id
          WHERE pp.id=%s
        """, (paso_id,))
        row = cur.fetchone()
        cur.execute("DELETE FROM proceso_pasos WHERE id=%s", (paso_id,))
        conn.commit()
        flash("Paso eliminado.","success")
        return redirect(url_for('recetas_proceso', pt_id=(row['pt_id'] if row else 0)))
    finally:
        cur.close(); conn.close()


@app.route('/recetas/<int:id>/eliminar', methods=['POST'])
def eliminar_receta(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger'); return redirect('/login')

    conn = conexion_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM recipes WHERE id=%s", (id,))
        conn.commit()
        flash('Ingrediente eliminado de la receta.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'No se pudo eliminar: {e}', 'danger')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('recetas'))


@app.route('/recetas/<int:id>/editar', methods=['GET','POST'])
def editar_receta(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger'); return redirect('/login')

    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        product_id  = request.form['product_id']
        material_id = request.form['material_id']
        quantity    = request.form['quantity']
        unit        = request.form['unit']
        try:
            cur.execute("""
                UPDATE recipes
                   SET product_id=%s, material_id=%s, quantity=%s, unit=%s
                 WHERE id=%s
            """, (product_id, material_id, quantity, unit, id))
            conn.commit()
            flash('Receta actualizada.', 'success')
            return redirect(url_for('recetas'))
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar: {e}', 'danger')
        finally:
            cur.close(); conn.close()
            return redirect(url_for('editar_receta', id=id))

    # GET
    cur.execute("SELECT id, product_id, material_id, quantity, unit FROM recipes WHERE id=%s", (id,))
    receta = cur.fetchone()
    if not receta:
        cur.close(); conn.close()
        flash('Registro no encontrado.', 'warning')
        return redirect(url_for('recetas'))

    # catálogos
    cur.execute("SELECT id, nombre FROM mercancia WHERE tipo='PT' ORDER BY nombre")
    productos = cur.fetchall()
    cur.execute("SELECT id, nombre FROM mercancia WHERE tipo='MP' ORDER BY nombre")
    materiales = cur.fetchall()

    cur.close(); conn.close()
    return render_template('inventarios/PT/recetas_editar.html',
                           receta=receta, productos=productos, materiales=materiales)


@app.route("/productos_terminados", methods=["GET", "POST"])
def productos_terminados():
    """Agregar y listar Productos Terminados (PT)"""
    
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        
        if not nombre:
            flash("⚠️ El nombre no puede estar vacío", "warning")
            return redirect(url_for("productos_terminados"))

        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)

        try:
            # Verificar que no exista
            cursor.execute("""
                SELECT id, nombre FROM mercancia 
                WHERE UPPER(TRIM(nombre)) = UPPER(%s)
                LIMIT 1
            """, (nombre,))
            duplicado = cursor.fetchone()
            
            if duplicado:
                flash(f"⚠️ Ya existe '{duplicado['nombre']}' (ID: {duplicado['id']})", 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for("productos_terminados"))
            
            # Insertar PT completo
            cursor.execute("""
                INSERT INTO mercancia 
                (nombre, tipo, tipo_inventario_id, precio, unidad_id, cont_neto, iva, ieps, activo)
                VALUES (%s, 'PT', 3, 0.00, 1, 1, 0, 0, 1)
            """, (nombre,))
            
            mid = cursor.lastrowid
            
            # Inventario inicial
            cursor.execute("""
                INSERT IGNORE INTO inventario
                (mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base)
                VALUES (%s, 0, 0, 0, 0, 0)
            """, (mid,))
            
            # Configuración de precio inicial (modo auto, markup 30%)
            cursor.execute("""
                INSERT INTO pt_precios (mercancia_id, modo, markup_pct)
                VALUES (%s, 'auto', 0.30)
            """, (mid,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f"✅ Producto '{nombre}' agregado correctamente", "success")
            return redirect(url_for("productos_terminados"))
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            flash(f"❌ Error: {str(e)}", "danger")
            return redirect(url_for("productos_terminados"))

    # GET → Listar PT
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nombre, precio
        FROM mercancia 
        WHERE tipo_inventario_id = 3 
        ORDER BY nombre
    """)
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
def productos_venta():
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    # Asegúrate de que en tu tabla mercancia exista el campo 'precio'
    cursor.execute("SELECT id, nombre, precio FROM mercancia")
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
    # Solo admin
    if session.get('rol') != 'admin':
        flash('Acceso denegado. Solo el administrador puede registrar compras.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    if request.method == 'POST':
        proveedor      = (request.form.get('proveedor') or '').strip()
        fecha          = (request.form.get('fecha') or '').strip()
        numero_factura = (request.form.get('numero_factura') or '').strip()
        metodo_pago    = (request.form.get('metodo_pago') or '').strip()

        nombres  = request.form.getlist('mercancia_nombre[]')
        mids     = request.form.getlist('mercancia_id[]')
        unidades = request.form.getlist('unidades[]')
        precios  = request.form.getlist('precio_unitario[]')
        totales  = request.form.getlist('precio_total[]')

        # 🐛 DEBUG
        print("\n" + "="*60, flush=True)
        print("DEBUG: Datos recibidos del formulario", flush=True)
        print("="*60, flush=True)
        print(f"Nombres: {nombres}", flush=True)
        print(f"IDs:     {mids}", flush=True)
        print("="*60 + "\n", flush=True)

        conn = conexion_db()
        cur = conn.cursor(dictionary=True)
        try:
            items = []
            productos_fallidos = []

            for i in range(max(len(nombres), len(unidades), len(precios), len(totales))):
                nom  = (nombres[i]  if i < len(nombres)  else "").strip()
                midS = (mids[i]     if i < len(mids)     else "").strip()
                undS = (unidades[i] if i < len(unidades) else "").strip()
                puS  = (precios[i]  if i < len(precios)  else "").strip()
                ptS  = (totales[i]  if i < len(totales)  else "").strip()

                if not nom and not undS and not puS and not ptS:
                    continue

                # Resolver mercancia por empresa
                try:
                    # Si tu helper admite empresa: resolver_mercancia(cur, nom, midS, empresa_id=eid)
                    mercancia_id = resolver_mercancia(cur, nom, midS)
                    # Validar pertenencia a esta empresa
                    cur.execute("""
                        SELECT m.id, m.nombre, m.producto_base_id, pb.nombre AS pb_nombre
                        FROM mercancia m
                        LEFT JOIN producto_base pb ON pb.id = m.producto_base_id
                        WHERE m.id = %s AND m.empresa_id = %s
                        """, (mercancia_id, eid))
                    merc = cur.fetchone()
                    if not merc:
                        productos_fallidos.append(f"'{nom}': Mercancía no encontrada en esta empresa")
                        continue
                    if not merc['producto_base_id']:
                        productos_fallidos.append(f"'{nom}': No tiene producto base asignado. Configúralo en catálogo primero.")
                        continue
                except LookupError as e:
                    productos_fallidos.append(f"'{nom}': {str(e)}")
                    continue

                # cont_neto del producto (mismo tenant)
                cur.execute("SELECT cont_neto FROM mercancia WHERE id=%s AND empresa_id=%s",
                            (mercancia_id, eid))
                r = cur.fetchone()
                try:
                    cont_neto = float(r['cont_neto'] or 1) if r else 1
                    if cont_neto <= 0:
                        cont_neto = 1
                except Exception:
                    cont_neto = 1

                und = float(undS or 0)
                pu  = float(puS or 0)
                pt  = float(ptS or (und * pu))

                items.append({
                    "mercancia_id": mercancia_id,
                    "nombre": nom,
                    "unidades_base": und,
                    "contenido_neto_total": und * cont_neto,
                    "precio_unitario": pu,
                    "precio_total": pt
                })

            if productos_fallidos:
                flash(f"⚠️ Productos omitidos: {', '.join(productos_fallidos)}", "warning")

            if not items:
                conn.rollback()
                flash("No hay renglones válidos para registrar.", "danger")
                return redirect(url_for('nueva_compra'))

            total_general = sum(x["precio_total"] for x in items)

            # Encabezado (con empresa)
            cur.execute("""
                INSERT INTO listado_compras (empresa_id, proveedor, fecha, numero_factura, total)
                VALUES (%s, %s, %s, %s, %s)
            """, (eid, proveedor, fecha, numero_factura, float(total_general)))
            compra_id = cur.lastrowid

            # 🐛 DEBUG
            print("\n" + "="*60, flush=True)
            print(f"COMPRA #{compra_id} - Items validados: {len(items)}", flush=True)
            print("="*60, flush=True)
            for idx, item in enumerate(items):
                print(f"[{idx+1}] {item['nombre']} (mercancia_id={item['mercancia_id']})", flush=True)
            print("="*60 + "\n", flush=True)

            # Crédito (si aplica)
            if metodo_pago == 'credito':
                cur.execute("""
                    INSERT INTO compras_credito
                      (empresa_id, compra_id, fecha, numero_documento, proveedor, importe, iva, ieps, total)
                    VALUES
                      (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (eid, compra_id, fecha, numero_factura, proveedor,
                      float(total_general), 0.0, 0.0, float(total_general)))

            # Asiento contable (ajusta tu helper para empresa si aún no lo hace)
            cuenta_pago = 30 if metodo_pago == "efectivo" else 40 if metodo_pago == "banco" else 30
            movimientos = [
                {"cuenta_id": 10, "debe": float(total_general), "haber": 0},
                {"cuenta_id": cuenta_pago, "debe": 0, "haber": float(total_general)}
            ]
            # Si tu función acepta empresa: registrar_asiento_compra(cur, conn, f"...", movimientos, empresa_id=eid)
            registrar_asiento_compra(cur, conn, f"Compra {numero_factura}", movimientos)

            # Detalle + inventario (todo con empresa)
            for x in items:
                cur.execute("""
                    INSERT INTO detalle_compra
                      (empresa_id, compra_id, mercancia_id, producto, unidades, contenido_neto_total, precio_unitario, precio_total)
                    VALUES
                      (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (eid, compra_id, x["mercancia_id"], x["nombre"], x["unidades_base"],
                      x["contenido_neto_total"], x["precio_unitario"], x["precio_total"]))

                # Stock (clave compuesta por empresa + mercancia_id)
                cur.execute("""
                    INSERT INTO inventario
                      (empresa_id, mercancia_id, inventario_inicial, entradas, salidas, aprobado)
                    VALUES
                      (%s, %s, 0, %s, 0, 0)
                    ON DUPLICATE KEY UPDATE
                      entradas = entradas + VALUES(entradas)
                """, (eid, x["mercancia_id"], x["contenido_neto_total"]))

                # Movimiento de inventario (MP = tipo_inventario_id=1; ajusta si difiere)
                cur.execute("""
                    INSERT INTO inventario_movimientos
                      (empresa_id, tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
                    VALUES
                      (%s, 1, %s, 'COMPRA', %s, %s, %s, %s)
                """, (eid, x["mercancia_id"], x["contenido_neto_total"], x["precio_unitario"], numero_factura, fecha))

            conn.commit()
            flash("✅ Compra registrada y stock actualizado.", "success")
            return redirect(url_for('detalle_compra', id=compra_id))

        except Exception as e:
            conn.rollback()
            flash(f"❌ Error: {e}", "danger")
            return redirect(url_for('nueva_compra'))
        finally:
            try: cur.close()
            except: pass
            try: conn.close()
            except: pass

    # GET — catálogos filtrados por empresa
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT nombre FROM proveedores WHERE empresa_id=%s ORDER BY nombre", (eid,))
    proveedores = cur.fetchall()
    cur.execute("""
        SELECT m.id, m.nombre
        FROM mercancia m
        WHERE m.empresa_id = %s
          AND m.tipo = 'MP'
          AND m.producto_base_id IS NOT NULL
          AND m.activo = 1
        ORDER BY m.nombre
    """, (eid,))
    productos = cur.fetchall()
    cur.close(); conn.close()

    return render_template('nueva_compra.html', proveedores=proveedores, productos=productos)

@app.route('/detalle_compra/<int:id>')
@require_login
def detalle_compra(id):
    # Solo admin
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # Encabezado (asegura pertenencia a la empresa)
    cursor.execute("""
        SELECT id,
               proveedor,
               DATE_FORMAT(fecha, '%%d %%b %%Y') AS fecha,
               numero_factura,
               total
        FROM listado_compras
        WHERE id = %s
          AND empresa_id = %s
    """, (id, eid))
    compra = cursor.fetchone()

    if not compra:
        cursor.close(); conn.close()
        flash('La compra no existe.', 'warning')
        return redirect(url_for('listado_compras'))

    # Detalle (filtrado por empresa)
    cursor.execute("""
        SELECT
            d.id,
            COALESCE(m.nombre, d.producto) AS producto,
            d.unidades,
            d.contenido_neto_total,
            d.precio_unitario,
            d.precio_total
        FROM detalle_compra d
        LEFT JOIN mercancia m
               ON m.id = d.mercancia_id
              AND m.empresa_id = %s
        WHERE d.compra_id = %s
          AND d.empresa_id = %s
        ORDER BY d.id
    """, (eid, id, eid))
    detalles = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('detalle_compra_popup.html',
                           compra=compra,
                           detalles=detalles)

@app.route('/listado_compras', methods=['GET'])
def listado_compras():
    conn = conexion_db()
    compras = []
    try:
        # Cursor dict para mysql-connector o PyMySQL
        try:
            cur = conn.cursor(dictionary=True)
        except TypeError:
            import pymysql
            cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute("""
            SELECT
                id,
                DATE_FORMAT(fecha, '%d %b %Y') AS fecha_fmt,  -- fecha como texto
                proveedor,
                numero_factura,
                total AS total                      -- alias que usa tu HTML
            FROM listado_compras
            ORDER BY id DESC
        """)
        compras = cur.fetchall()
    except Exception as e:
        print("[ERROR] /listado_compras:", e)
        flash(f"Error consultando listado_compras: {e}", "danger")
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

    return render_template('listado_compras.html', compras=compras)

@app.route('/editar_compra/<int:id>', methods=['GET', 'POST'])
def editar_compra(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

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
            WHERE id=%s
        """, (proveedor, fecha, numero_factura, total, id))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Compra actualizada correctamente.', 'success')
        return redirect('/listado_compras')

    cursor.execute("SELECT * FROM listado_compras WHERE id = %s", (id,))
    compra = cursor.fetchone()
    cursor.close()
    conn.close()

    if not compra:
        flash('Compra no encontrada.', 'warning')
        return redirect('/listado_compras')

    return render_template('editar_compra.html', compra=compra)

@app.route('/eliminar_compra/<int:id>', methods=['POST'])
def eliminar_compra(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Obtener factura
        cursor.execute("SELECT numero_factura FROM listado_compras WHERE id = %s", (id,))
        compra = cursor.fetchone()
        
        if not compra:
            flash('Compra no encontrada.', 'warning')
            return redirect('/listado_compras')

        numero_factura = compra['numero_factura']

        # 2. Restar entradas del inventario
        cursor.execute("""
            UPDATE inventario i
            JOIN detalle_compra dc ON dc.mercancia_id = i.mercancia_id
            SET i.entradas = GREATEST(0, i.entradas - dc.contenido_neto_total)
            WHERE dc.compra_id = %s
        """, (id,))

        # 3. Eliminar movimientos
        cursor.execute("""
            DELETE FROM inventario_movimientos 
            WHERE tipo_movimiento = 'COMPRA' 
              AND referencia = %s
        """, (numero_factura,))

        # 4. Eliminar detalles
        cursor.execute("DELETE FROM detalle_compra WHERE compra_id = %s", (id,))

        # 5. Eliminar crédito
        cursor.execute("DELETE FROM compras_credito WHERE compra_id = %s", (id,))

        # 6. Eliminar encabezado
        cursor.execute("DELETE FROM listado_compras WHERE id = %s", (id,))

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
def mercancia():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # --- DEBUG ---
        print(">>> DEBUG mercancia form:", dict(request.form), flush=True)

        nombre     = (request.form.get('nombre') or '').strip()
        
        # ✅ VALIDAR QUE NO EXISTA DUPLICADO
        cursor.execute("""
            SELECT id, nombre 
            FROM mercancia 
            WHERE UPPER(TRIM(nombre)) = UPPER(%s) 
            LIMIT 1
        """, (nombre,))
        duplicado = cursor.fetchone()
        
        if duplicado:
            flash(f"⚠️ Ya existe una mercancía con el nombre '{duplicado['nombre']}' (ID: {duplicado['id']}). Usa otro nombre o edita la existente.", 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('mercancia'))
        
        # Continuar con el resto de campos
        cont_s     = (request.form.get('cont_neto') or '0').strip()
        unidad_id  = int(request.form['unidad_id'])
        iva        = int(request.form.get('iva')  or 0)
        ieps       = int(request.form.get('ieps') or 0)

        # Catálogo MP
        catalogo_id_s  = request.form.get('catalogo_id') or ''
        catalogo_nuevo = (request.form.get('catalogo_nuevo') or '').strip()

        # Producto base
        producto_base_id = (
            int(request.form['producto_base_id'])
            if request.form.get('producto_base_id') and request.form['producto_base_id'].isdigit()
            else None
        )
        producto_base_nuevo = (request.form.get('producto_base_nuevo') or '').strip()

        try:
            # validar contenido neto
            try:
                cont_neto = Decimal(cont_s)
                if cont_neto <= 0:
                    raise InvalidOperation
            except InvalidOperation:
                raise ValueError("Contenido Neto inválido")

            # validar unidad
            cursor.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
            if not cursor.fetchone():
                raise ValueError("Unidad de medida inválida")

            # resolver catálogo MP
            catalogo_id = int(catalogo_id_s) if catalogo_id_s.isdigit() else None
            if not catalogo_id and catalogo_nuevo:
                catalogo_id = get_or_create_catalogo(cursor, conn, catalogo_nuevo, tipo='MP')

            # resolver producto base
            if not producto_base_id and producto_base_nuevo:
                cursor.execute("""
                    INSERT INTO producto_base (nombre, unidad_id, activo)
                    VALUES (%s, %s, 1)
                """, (producto_base_nuevo, unidad_id))
                conn.commit()
                producto_base_id = cursor.lastrowid

            # crear cuentas padre/subcuenta
            cursor.execute("""
                SELECT id FROM cuentas_contables
                WHERE nivel=2
                ORDER BY codigo
                LIMIT 1
            """)
            row = cursor.fetchone()
            cuenta_padre_id = row["id"] if row else None
            subcuenta_id = None
            subcuenta_codigo = ""

            # insertar producto (mercancia)
            cursor.execute("""
                INSERT INTO mercancia
                    (nombre, tipo, unidad_id, cont_neto, iva, ieps,
                     cuenta_id, subcuenta_id, catalogo_id, producto_base_id)
                VALUES (%s, 'MP', %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nombre,
                unidad_id,
                str(cont_neto),
                iva,
                ieps,
                cuenta_padre_id,
                subcuenta_id,
                catalogo_id,
                producto_base_id
            ))
            mid = cursor.lastrowid

            # asegurar inventario
            cursor.execute("""
                INSERT IGNORE INTO inventario
                    (mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base)
                VALUES (%s,0,0,0,0,0)
            """, (mid,))

            # crear presentación inicial
            cursor.execute("SELECT nombre FROM unidades_medida WHERE id=%s", (unidad_id,))
            um = cursor.fetchone()
            unidad_nombre = (um['nombre'] if um else '').lower()
            desc = f"{nombre} {cont_neto} {unidad_nombre}" if unidad_nombre else f"{nombre} {cont_neto}"
            cursor.execute("""
                INSERT IGNORE INTO presentaciones
                    (mercancia_id, descripcion, contenido_neto, unidad, factor_conversion)
                VALUES (%s, %s, %s, %s, %s)
            """, (mid, desc, str(cont_neto), unidad_nombre, str(cont_neto)))

            conn.commit()
            flash(f'✅ Producto registrado correctamente.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'❌ No se pudo registrar el producto: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('mercancia'))

    # GET: listas
    try:
        cursor.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        unidades = cursor.fetchall()

        cursor.execute("""
            SELECT p.id, p.nombre, p.cont_neto,
                   u.nombre AS unidad, p.iva, p.ieps,
                   p.catalogo_id, p.producto_base_id,
                   sc.id AS subcuenta_id,
                   CONCAT(sc.codigo, ' - ', sc.nombre) AS cuenta_asignada
            FROM mercancia p
            LEFT JOIN unidades_medida u ON p.unidad_id = u.id
            LEFT JOIN cuentas_contables sc ON p.subcuenta_id = sc.id
            ORDER BY p.nombre ASC
        """)
        productos = cursor.fetchall()

        # catálogos MP activos
        cursor.execute("""
            SELECT id, nombre
              FROM catalogo_inventario
             WHERE activo=1 AND tipo='MP'
             ORDER BY nombre
        """)
        catalogos = cursor.fetchall()

        # productos base activos
        cursor.execute("""
            SELECT id, nombre
              FROM producto_base
             WHERE activo=1
             ORDER BY nombre
        """)
        productos_base = cursor.fetchall()

        cursor.execute("""
            SELECT id, CONCAT(codigo, ' - ', nombre) AS etiqueta
              FROM cuentas_contables
             WHERE nivel = 3
             ORDER BY codigo
        """)
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
def actualizar_mercancia(id):   
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        nombre    = request.form['nombre'].strip()
        unidad_id = int(request.form['unidad_id'])
        iva_s     = str(request.form.get('iva', '0')).strip()
        ieps_s    = str(request.form.get('ieps', '0')).strip()
        cont_s    = (request.form.get('cont_neto') or '0').strip()
        sub_s     = request.form.get('subcuenta_id') or ''

        cur.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
        if not cur.fetchone():
            raise ValueError("Unidad de medida inválida")

        try:
            cont_neto = Decimal(cont_s)
            if cont_neto <= 0:
                raise InvalidOperation
        except InvalidOperation:
            raise ValueError("Contenido Neto inválido")

        iva  = int(iva_s) if iva_s.isdigit() else 0
        ieps = int(ieps_s) if ieps_s.isdigit() else 0
        subcuenta_id = int(sub_s) if sub_s.isdigit() else None

        # si hay subcuenta, alinear padre
        cuenta_padre_id = None
        if subcuenta_id:
            cur.execute("SELECT padre_id FROM cuentas_contables WHERE id=%s", (subcuenta_id,))
            r = cur.fetchone()
            if r and r['padre_id']:
                cuenta_padre_id = r['padre_id']

        # Manejar catálogo
        catalogo_id_s = request.form.get('catalogo_id') or ''
        catalogo_nuevo = (request.form.get('catalogo_nuevo') or '').strip()
        catalogo_id = int(catalogo_id_s) if catalogo_id_s.isdigit() else None
        if not catalogo_id and catalogo_nuevo:
            catalogo_id = get_or_create_catalogo(cur, conn, catalogo_nuevo, tipo='MP')

        # ✅ MANEJAR PRODUCTO_BASE (NUEVA LÓGICA)
        producto_base_id = (
            int(request.form['producto_base_id'])
            if request.form.get('producto_base_id') and request.form['producto_base_id'].isdigit()
            else None
        )
        producto_base_nuevo = (request.form.get('producto_base_nuevo') or '').strip()
        
        # Si se escribió un producto_base nuevo, crearlo
        if not producto_base_id and producto_base_nuevo:
            cur.execute("""
                INSERT INTO producto_base (nombre, unidad_id, activo)
                VALUES (%s, %s, 1)
            """, (producto_base_nuevo, unidad_id))
            conn.commit()
            producto_base_id = cur.lastrowid

        # ✅ UPDATE COMPLETO CON PRODUCTO_BASE_ID
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
                producto_base_id=%s
            WHERE id=%s
        """, (nombre, str(cont_neto), unidad_id, iva, ieps, subcuenta_id, cuenta_padre_id, catalogo_id, producto_base_id, id))

        # asegurar inventario
        cur.execute("""
            INSERT IGNORE INTO inventario
                (mercancia_id, inventario_inicial, entradas, salidas, aprobado, disponible_base)
            VALUES (%s, 0, 0, 0, 0, 0)
        """, (id,))

        # presentación
        cur.execute("SELECT nombre FROM unidades_medida WHERE id=%s", (unidad_id,))
        um = cur.fetchone()
        unidad_nombre = (um['nombre'] if um else '').lower()
        desc = f"{nombre} {cont_neto} {unidad_nombre}" if unidad_nombre else f"{nombre} {cont_neto}"
        cur.execute("""
            INSERT IGNORE INTO presentaciones
                (mercancia_id, descripcion, contenido_neto, unidad, factor_conversion)
            VALUES (%s, %s, %s, %s, %s)
        """, (id, desc, str(cont_neto), unidad_nombre, str(cont_neto)))

        conn.commit()
        flash('✅ Mercancía actualizada correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'❌ No se pudo actualizar: {e}', 'danger')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('mercancia'))


@app.route('/mercancia/<int:id>/eliminar', methods=['POST'])
def eliminar_mercancia(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger'); return redirect('/login')

    conn = conexion_db(); cur = conn.cursor()
    try:
        # borra solo lo que sabemos que existe
        cur.execute("DELETE FROM inventario_movimientos WHERE mercancia_id=%s", (id,))
        cur.execute("DELETE FROM detalle_compra          WHERE mercancia_id=%s", (id,))
        cur.execute("DELETE FROM presentaciones          WHERE mercancia_id=%s", (id,))
        cur.execute("DELETE FROM inventario              WHERE mercancia_id=%s", (id,))
        cur.execute("DELETE FROM mercancia               WHERE id=%s", (id,))

        conn.commit()
        flash('Producto eliminado.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'No se pudo eliminar: {e}', 'danger')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('mercancia'))

@app.route('/registrar_proveedor', methods=['GET', 'POST'])
def registrar_proveedor():
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        ciudad = request.form['ciudad']
        telefono = request.form['telefono']

        cursor.execute(
            "INSERT INTO proveedores (nombre, direccion, ciudad, telefono) VALUES (%s, %s, %s, %s)",
            (nombre, direccion, ciudad, telefono)
        )
        conn.commit()
        flash('Proveedor registrado correctamente', 'success')
        return redirect('/registrar_proveedor')

    # Obtener todos los proveedores para mostrarlos en la tabla
    cursor.execute("SELECT * FROM proveedores ORDER BY id DESC")
    proveedores = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('registrar_proveedor.html', proveedores=proveedores)


@app.route('/catalogo_mp', methods=['GET'])
def catalogo_mp():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    q = request.args.get('q', '').strip()

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    try:
        sql = """
        SELECT pb.id, pb.nombre, pb.activo, COUNT(m.id) AS vinculados
        FROM producto_base pb
        LEFT JOIN mercancia m ON m.producto_base_id = pb.id
        {where}
        GROUP BY pb.id, pb.nombre, pb.activo
        ORDER BY pb.nombre ASC
        """
        if q:
            cur.execute(sql.format(where="WHERE pb.nombre LIKE %s"), (f"%{q}%",))
        else:
            cur.execute(sql.format(where=""))
        items = cur.fetchall()

        # Unidades para el modal "Nuevo"
        cur.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        unidades = cur.fetchall()
    finally:
        cur.close(); conn.close()

    return render_template("inventarios/MP/catalogo_mp.html", items=items, q=q, unidades=unidades)

@app.route('/catalogo_mp/toggle/<int:id>', methods=['POST'])
def catalogo_mp_toggle(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE producto_base SET activo = 1 - activo WHERE id=%s", (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"No se pudo cambiar el estado: {e}", "danger")
    finally:
        cur.close(); conn.close()

    return redirect(url_for('catalogo_mp'))

@app.route('/catalogo_mp/editar/<int:id>', methods=['GET', 'POST'])
def catalogo_mp_editar(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

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

            # unidad_id robusto
            if unidad_id_s.isdigit():
                unidad_id = int(unidad_id_s)
                cur.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
                if not cur.fetchone():
                    flash("Unidad de medida inválida.", "danger")
                    return redirect(url_for('catalogo_mp_editar', id=id))
            else:
                cur.execute("SELECT id FROM unidades_medida ORDER BY id LIMIT 1")
                r = cur.fetchone()
                if not r:
                    cur.execute("INSERT INTO unidades_medida (nombre) VALUES ('kg')")
                    unidad_id = cur.lastrowid
                else:
                    unidad_id = r['id']

            # nombre duplicado (case-insensitive) distinto ID
            cur.execute("""
                SELECT id FROM producto_base
                WHERE UPPER(nombre)=UPPER(%s) AND id<>%s
                LIMIT 1
            """, (nombre, id))
            if cur.fetchone():
                flash("Ya existe otro producto base con ese nombre.", "warning")
                return redirect(url_for('catalogo_mp_editar', id=id))

            cur.execute("""
                UPDATE producto_base
                   SET nombre=%s, unidad_id=%s, activo=%s
                 WHERE id=%s
            """, (nombre, unidad_id, activo, id))
            conn.commit()
            flash("Producto base actualizado", "success")
            return redirect(url_for('catalogo_mp'))

        # GET: cargar item + unidades
        cur.execute("SELECT * FROM producto_base WHERE id=%s", (id,))
        item = cur.fetchone()
        cur.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
        unidades = cur.fetchall()
    finally:
        cur.close(); conn.close()

    if not item:
        flash("Ítem no encontrado", "danger")
        return redirect(url_for('catalogo_mp'))

    # 👇 RUTA CORRECTA DEL TEMPLATE
    return render_template("inventarios/MP/catalogo_mp_editar.html", item=item, unidades=unidades)


@app.post('/catalogo_mp/<int:id>/eliminar')
def catalogo_mp_eliminar(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.','danger'); return redirect('/login')

    conn = conexion_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM mercancia WHERE producto_base_id=%s LIMIT 1", (id,))
        if cur.fetchone():
            flash('No se puede eliminar: hay mercancías ligadas. Desligue primero.','warning')
        else:
            cur.execute("DELETE FROM producto_base WHERE id=%s", (id,))
            conn.commit()
            flash('Eliminado.','success')
    except Exception as e:
        conn.rollback(); flash(f'Error: {e}','danger')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('catalogo_mp'))


@app.route('/catalogo_mp/nuevo', methods=['POST'])
def catalogo_mp_nuevo():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger'); return redirect('/login')

    print(">>> catalogo_mp_nuevo FORM:", dict(request.form), flush=True)
    nombre = (request.form.get('nombre') or '').strip()
    unidad_id_s = (request.form.get('unidad_id') or '').strip()
    if not nombre:
        flash("Nombre obligatorio.", "danger"); return redirect(url_for('catalogo_mp') + '#nuevo')

    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        if not unidad_id_s.isdigit():
            cur.execute("SELECT id FROM unidades_medida ORDER BY id LIMIT 1")
            r = cur.fetchone()
            if not r:
                cur.execute("INSERT INTO unidades_medida (nombre) VALUES ('kg')")
                unidad_id = cur.lastrowid
            else:
                unidad_id = r["id"]
        else:
            unidad_id = int(unidad_id_s)
            cur.execute("SELECT id FROM unidades_medida WHERE id=%s", (unidad_id,))
            if not cur.fetchone():
                flash("Unidad inválida.", "danger"); return redirect(url_for('catalogo_mp') + '#nuevo')

        cur.execute("SELECT id FROM producto_base WHERE UPPER(nombre)=UPPER(%s) LIMIT 1", (nombre,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE producto_base SET activo=1, unidad_id=%s WHERE id=%s", (unidad_id, row['id']))
            flash("Producto base reactivado.", "info")
        else:
            cur.execute("INSERT INTO producto_base (nombre, unidad_id, activo) VALUES (%s, %s, 1)", (nombre, unidad_id))
            flash("Producto base agregado.", "success")

        conn.commit()
    except Exception as e:
        conn.rollback(); flash(f"Error: {e}", "danger")
    finally:
        cur.close(); conn.close()

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

@app.route('/admin/usuario-areas')
def admin_usuario_areas():
    """Gestión de asignaciones usuario-área"""
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado. Solo administradores.', 'danger')
        return redirect('/login')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    # Asignaciones existentes
    cur.execute("""
        SELECT 
            ua.id,
            u.id as usuario_id,
            u.nombre as usuario,
            u.puesto,
            u.correo,
            a.id as area_id,
            a.nombre as area,
            ua.es_responsable,
            DATE_FORMAT(ua.fecha_asignacion, '%d/%m/%Y %H:%i') as fecha
        FROM usuario_areas ua
        JOIN usuarios u ON u.id = ua.usuario_id
        JOIN areas_produccion a ON a.id = ua.area_id
        ORDER BY u.nombre, a.nombre
    """)
    asignaciones = cur.fetchall()
    
    # Usuarios disponibles
    cur.execute("SELECT id, nombre, puesto, correo FROM usuarios ORDER BY nombre")
    usuarios = cur.fetchall()
    
    # Áreas disponibles
    cur.execute("SELECT id, nombre FROM areas_produccion WHERE activo=1 ORDER BY nombre")
    areas = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin/usuario_areas.html', 
                          asignaciones=asignaciones,
                          usuarios=usuarios,
                          areas=areas)


@app.post('/admin/usuario-areas/agregar')
def admin_usuario_areas_agregar():
    """Agregar nueva asignación usuario-área"""
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    usuario_id = int(request.form.get('usuario_id'))
    area_id = int(request.form.get('area_id'))
    es_responsable = 1 if request.form.get('es_responsable') == '1' else 0
    
    conn = conexion_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO usuario_areas (usuario_id, area_id, es_responsable)
            VALUES (%s, %s, %s)
        """, (usuario_id, area_id, es_responsable))
        conn.commit()
        flash('✅ Asignación agregada correctamente', 'success')
    except Exception as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            flash('⚠️ Esta asignación ya existe', 'warning')
        else:
            flash(f'❌ Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin_usuario_areas'))


@app.post('/admin/usuario-areas/eliminar/<int:id>')
def admin_usuario_areas_eliminar(id):
    """Eliminar asignación usuario-área"""
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = conexion_db()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM usuario_areas WHERE id = %s", (id,))
        conn.commit()
        flash('🗑️ Asignación eliminada', 'info')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error al eliminar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin_usuario_areas'))


@app.post('/admin/usuario-areas/toggle-responsable/<int:id>')
def admin_usuario_areas_toggle(id):
    """Cambiar estado de responsable"""
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = conexion_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE usuario_areas 
            SET es_responsable = NOT es_responsable 
            WHERE id = %s
        """, (id,))
        conn.commit()
        flash('✅ Estado actualizado', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Error: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin_usuario_areas'))


    @app.route('/test-email')
    def test_email():
        """Ruta temporal para probar envío de email"""
        if 'usuario_id' not in session or session.get('rol') != 'admin':
            return "Debes ser admin para probar esto"
        
        resultado = enviar_email_activacion(
            nombre='Usuario de Prueba',
            correo_destino='tu_correo@gmail.com',
            token='token-de-prueba-123'
        )
        
        if resultado:
            return "✅ Email enviado correctamente! Revisa tu bandeja de entrada"
        else:
            return "❌ Error al enviar email. Revisa la consola para ver el error"


# ===== REGISTRO DE BLUEPRINTS =====
from inventarios.WIP import bp as wip_bp
app.register_blueprint(api)
# ==================================

# ===== INICIAR SERVIDOR =====
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔍 RUTAS REGISTRADAS EN FLASK:")
    print("="*60)
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30s} {rule.rule}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)