"""
app.py - Aplicación Flask para un sistema ERP básico.
Incluye autenticación de usuarios, control de inventario y registro de compras.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
from flask import Blueprint
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'mi_clave_super_secreta'
CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Blueprint("api", __name__, url_prefix="/api/v1")



def conexion_db():
    """
    Establece y retorna una conexión a la base de datos MySQL.
    Asegúrate de cerrar la conexión después de usarla.
    """
    return mysql.connector.connect(
        host="localhost",
        user="fcogranados",
        password="interely8711",
        database="miapp"
    )

# -------------------- Helpers de catálogo contable --------------------


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
    cursor.execute("SELECT id nombre FROM cuentas_contables WHERE codigo=%s", (code,))
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
from decimal import Decimal, InvalidOperation

def registrar_movimiento(tipo_inventario_id:int, mercancia_id:int,
                         tipo_movimiento:str, unidades, precio_unitario,
                         referencia:str=None, usuario_id:int=None) -> int:
    """
    Inserta un movimiento IN/OUT/ADJ para MP/WIP/PT en inventario_movimientos.
    Retorna el id insertado.
    """
    tipo_movimiento = tipo_movimiento.lower()  # 'entrada' | 'salida' | 'ajuste'
    if tipo_movimiento not in ('entrada','salida','ajuste'):
        raise ValueError("tipo_movimiento inválido")

    try:
        unidades = Decimal(str(unidades))
        precio_unitario = Decimal(str(precio_unitario))
    except InvalidOperation:
        raise ValueError("unidades/precio_unitario inválidos")

    conn = conexion_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO inventario_movimientos
              (tipo_inventario_id, mercancia_id, fecha, tipo_movimiento,
               unidades, precio_unitario, referencia)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """, (tipo_inventario_id, mercancia_id, tipo_movimiento,
              float(unidades), float(precio_unitario), referencia))
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()


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
                "UPDATE inventario_movimientos SET unidades = unidades - %s WHERE id = %s",
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
    db_name = None
    count = 0
    sample = None
    try:
        c = conn.cursor()
        c.execute("SELECT DATABASE()")
        row = c.fetchone()
        db_name = row[0] if row else None
        c.close()

        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM listado_compras")
        count = c.fetchone()[0]
        c.close()

        try:
            cur = conn.cursor(dictionary=True)
        except TypeError:
            import pymysql
            cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute("""
            SELECT id,
                   DATE_FORMAT(fecha, '%%d/%%m/%%Y') AS fecha,
                   proveedor,
                   numero_factura,
                   total_general AS total
            FROM listado_compras
            ORDER BY id DESC
            LIMIT 1
        """)
        sample = cur.fetchone()
        cur.close()
    finally:
        try: conn.close()
        except: pass

    return jsonify({"db": db_name, "count": count, "sample": sample})

@app.route("/check_producto/<nombre>")
def check_producto(nombre):
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM mercancia WHERE nombre = %s", (nombre,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({"existe": row is not None})



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

    return redirect(url_for('cuentas_contables'))

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
                VALUES ( % s, % s, % s, % s, % s)
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
    """
    Permite al administrador registrar nuevas unidades de medida """

    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        conn = conexion_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM unidades_medida WHERE nombre=%s", (nombre,))
        existe = cursor.fetchone()
    if existe:
        cursor.close()
        conn.close()
        flash('La unidad ya existe.', 'warning')
        return redirect(url_for('unidades_medida'))

    cursor.execute(
        "INSERT INTO unidades_medida (nombre) VALUES (%s)", (nombre,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Unidad registrada con éxito', 'success')
    return redirect(url_for('unidades_medida'))

    # Mostrar existentes
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM unidades_medida")
    unidades = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('unidades_medida.html', unidades=unidades)

def registrar_asiento_compra(conn, compra_id, proveedor, total_general, metodo_pago):
    """
    Inserta el asiento contable de una compra.
    """
    cursor = conn.cursor(dictionary=True)

    # 1) Insertar cabecera del asiento
    cursor.execute("""
        INSERT INTO asientos_contables (fecha, concepto)
        VALUES (CURDATE(), %s)
    """, (f"Compra a {proveedor} - ID compra {compra_id}",))
    asiento_id = cursor.lastrowid

    # 2) Determinar cuenta del Haber según método de pago
    if metodo_pago.lower() == "efectivo":
        cuenta_haber = "111-001-000"   # Caja
    elif metodo_pago.lower() in ("transferencia", "deposito", "cheque"):
        cuenta_haber = "111-002-000"   # Bancos
    else:
        cuenta_haber = "211-001-000"   # Proveedores (si queda a crédito)

    # Buscar IDs de cuentas
    cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '112-001-000'")  # Inventarios
    cuenta_inventario_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '114-002-000'")  # IVA acreditable
    cuenta_iva_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = %s", (cuenta_haber,))
    cuenta_haber_id = cursor.fetchone()["id"]

    # 3) Insertar partidas
    # Inventario al DEBE
    cursor.execute("""
        INSERT INTO asientos_detalle (asiento_id, cuenta_id, debe, haber)
        VALUES (%s, %s, %s, 0)
    """, (asiento_id, cuenta_inventario_id, total_general))  # Aquí deberías usar subtotal sin IVA

    # IVA acreditable al DEBE
    cursor.execute("""
        INSERT INTO asientos_detalle (asiento_id, cuenta_id, debe, haber)
        VALUES (%s, %s, %s, 0)
    """, (asiento_id, cuenta_iva_id, total_general * 0.16))  # Asumiendo IVA 16%

    # Pago o Proveedores al HABER
    cursor.execute("""
        INSERT INTO asientos_detalle (asiento_id, cuenta_id, debe, haber)
        VALUES (%s, %s, 0, %s)
    """, (asiento_id, cuenta_haber_id, total_general * 1.16))  # Total con IVA

    conn.commit()
    cursor.close()



# INVENTARIOS #




@app.route('/inventario', methods=['GET', 'POST'])
def mostrar_inventario():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Traer inventario base
    cursor.execute("""
        SELECT 
            COALESCE(i.id, 0)               AS id,
            m.id                             AS mercancia_id,
            m.nombre                         AS producto,
            COALESCE(i.inventario_inicial,0) AS inventario_inicial,
            COALESCE(i.entradas,0)           AS entradas,
            COALESCE(i.salidas,0)            AS salidas,
            COALESCE(i.aprobado,0)           AS aprobado
        FROM mercancia m
        LEFT JOIN inventario i ON i.mercancia_id = m.id
        WHERE EXISTS (
            SELECT 1 FROM inventario_movimientos im WHERE im.mercancia_id = m.id
        ) OR i.id IS NOT NULL
        ORDER BY m.nombre ASC
    """)
    inventario_base = cursor.fetchall()

    inventario_final = []

    for prod in inventario_base:
        mercancia_id = prod['mercancia_id']

        # Ajustar entradas y salidas al contenido neto
        cursor.execute("SELECT cont_neto FROM mercancia WHERE id=%s", (mercancia_id,))
        row = cursor.fetchone()
        cont_neto = row['cont_neto'] if row and row['cont_neto'] else 1

        # 2️⃣ Total entradas (ajustadas a contenido neto)
        cursor.execute("""
            SELECT COALESCE(SUM(unidades),0) AS total_entradas
            FROM inventario_movimientos
            WHERE mercancia_id = %s AND UPPER(tipo_movimiento) IN ('COMPRA','ENTRADA')
        """, (mercancia_id,))
        total_entradas = cursor.fetchone()['total_entradas'] or 0

        # 3️⃣ Total salidas (ajustadas)
        cursor.execute("""
            SELECT COALESCE(SUM(unidades),0) AS total_salidas
            FROM inventario_movimientos
            WHERE mercancia_id = %s AND UPPER(tipo_movimiento) = 'SALIDA'
        """, (mercancia_id,))
        total_salidas = (cursor.fetchone()['total_salidas'] or 0)

        # 4️⃣ Disponible
        disponible = float(prod['inventario_inicial'] or 0) + float(total_entradas or 0) - float(total_salidas or 0)

        # 5️⃣ Valor inventario usando PEPS
        cursor.execute("""
            SELECT unidades, precio_unitario
            FROM inventario_movimientos
            WHERE mercancia_id = %s AND tipo_movimiento = 'COMPRA'
            ORDER BY fecha ASC, id ASC
        """, (mercancia_id,))
        entradas_fifo = cursor.fetchall()

        unidades_pendientes = disponible
        valor_inventario = 0
        for entrada in entradas_fifo:
            if unidades_pendientes <= 0:
                break
            if entrada['unidades'] <= unidades_pendientes:
                valor_inventario += entrada['unidades'] * entrada['precio_unitario']
                unidades_pendientes -= entrada['unidades']
            else:
                valor_inventario += unidades_pendientes * entrada['precio_unitario']
                unidades_pendientes = 0

        inventario_final.append({
            'id': prod['id'],
            'mercancia_id': prod['mercancia_id'],      # 👈 necesitas esto para los links
            'producto': prod['producto'],
            'inventario_inicial': prod['inventario_inicial'],
            'entradas': total_entradas,
            'salidas': total_salidas,
            'disponible': disponible,
            'valor_inventario': valor_inventario,
            'aprobado': prod['aprobado']
        })

    cursor.close()
    conn.close()

    return render_template('inventario.html', inventario=inventario_final)


@app.route('/inventarios/movimientos/<int:mercancia_id>')
def inventario_movimientos(mercancia_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Obtener nombre de la mercancía
    cursor.execute("SELECT nombre FROM mercancia WHERE id = %s", (mercancia_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close(); conn.close()
        flash('Mercancía no encontrada.', 'warning')
        return redirect(url_for('mostrar_inventario'))

    producto = row['nombre']

    # 2️⃣ Traer movimientos desde detalle_compra + listado_compras
    sql = """
    SELECT * FROM (
        SELECT 
            lc.fecha AS fecha_raw,
            DATE_FORMAT(lc.fecha, '%d/%b/%y') AS fecha_fmt,
            lc.numero_factura AS documento,
            lc.proveedor AS fuente,
            dc.unidades,
            dc.contenido_neto_total,
            -- precio unitario por contenido neto: total / contenido
            CASE 
            WHEN dc.contenido_neto_total > 0 THEN dc.precio_total / dc.contenido_neto_total
            ELSE NULL
            END AS precio_unitario,
            dc.precio_total AS importe,
            dc.producto AS detalle,
            dc.compra_id,
            'compra' AS tipo_movimiento
        FROM detalle_compra dc
        JOIN listado_compras lc ON dc.compra_id = lc.id
        WHERE dc.mercancia_id = %s

        UNION ALL

        SELECT 
            im.fecha AS fecha_raw,
            DATE_FORMAT(im.fecha, '%d/%b/%y') AS fecha_fmt,
            im.referencia AS documento,
            '---' AS fuente,
            im.unidades,
            NULL AS contenido_neto_total,
            im.precio_unitario,
            (im.unidades * im.precio_unitario) AS importe,
            NULL AS detalle,
            NULL AS compra_id,
            im.tipo_movimiento
        FROM inventario_movimientos im
        WHERE im.mercancia_id = %s
        AND UPPER(im.tipo_movimiento) <> 'COMPRA'  -- 👈 evita duplicar compras
    ) t
    ORDER BY t.fecha_raw DESC, t.documento DESC
    """
    cursor.execute(sql, (mercancia_id, mercancia_id))
    movimientos = cursor.fetchall()


  
    # 3) Construir filas acumuladas para las dos tablas
    rows = []
    saldo_u = 0.0
    saldo_mx = 0.0

    for m in movimientos:
        tipo = (m.get('tipo_movimiento') or '').strip().lower()
        es_entrada = tipo in ('entrada', 'compra')

        # Unidades
        contenido = m.get('contenido_neto_total')
        if es_entrada:
            if contenido and contenido > 0:
                entrada_u = float(contenido)
            else:
                entrada_u = float(m.get('unidades') or 0)
        else:
            entrada_u = 0.0
        salida_u = float(m.get('unidades') or 0.0) if tipo == 'salida' else 0.0

        # Pesos
        entrada_mx = float(m.get('importe') or 0.0) if es_entrada else 0.0
        salida_mx  = float(m.get('importe') or 0.0) if tipo == 'salida' else 0.0

        # Saldos
        saldo_u += entrada_u - salida_u
        saldo_mx += entrada_mx - salida_mx

        # Precio unitario (por contenido neto)
        if es_entrada and entrada_u > 0:
            pu = entrada_mx / entrada_u
        elif tipo == 'salida':
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

    # 4) Mapear a las dos tablas que usa tu HTML
    tabla_unidades = [
        {
            "fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
            "entrada": r["entrada_u"], "salida": r["salida_u"], "saldo": r["saldo_u"]
        } for r in rows
    ]
    tabla_pesos = [
        {
            "fecha": r["fecha"], "documento": r["documento"], "fuente": r["fuente"],
            "entrada": r["entrada_mx"], "salida": r["salida_mx"], "saldo": r["saldo_mx"], "pu": r["pu"]
        } for r in rows
    ]

    cursor.close(); conn.close()

    # 5) Render
    return render_template(
        'inventario_movimientos.html',
        producto=producto,
        tabla_unidades=tabla_unidades,
        tabla_pesos=tabla_pesos
    )

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

                # Actualizar inventario MP (restar)
                cursor.execute("""
                    UPDATE inventario_mp
                    SET salidas = salidas + %s
                    WHERE mercancia_id = %s
                """, (float(qty), mp_id))

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

@app.route('/inventarios/materias_primas', methods=['GET', 'POST'])
def mostrar_inventario_mp():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            i.id,
            COALESCE(m.nombre, i.producto) AS producto,
            i.inventario_inicial,
            COALESCE(e.total_entradas, 0) AS entradas_calc,
            COALESCE(s.total_salidas, 0) AS salidas_calc,
            (i.inventario_inicial + COALESCE(e.total_entradas, 0) - COALESCE(s.total_salidas, 0)) AS disponible_calc,
            i.aprobado
        FROM inventario i
        LEFT JOIN mercancia m ON m.id = i.mercancia_id
        LEFT JOIN (
            SELECT mercancia_id, SUM(unidades) AS total_entradas
            FROM detalle_compra
            GROUP BY mercancia_id
        ) e ON e.mercancia_id = i.mercancia_id
        LEFT JOIN (
            SELECT mercancia_id, SUM(unidades) AS total_salidas
            FROM detalle_venta
            GROUP BY mercancia_id
        ) s ON s.mercancia_id = i.mercancia_id
        ORDER BY producto ASC
    """)
    inventario = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('inventarios/materias_primas.html', inventario=inventario)

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
        ORDER BY p.fecha DESC
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



#     WIP    INVENTORY



@app.route('/production/new', methods=['GET', 'POST'])
def new_production():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        date = request.form['date']
        finished_product_id = request.form['finished_product_id']
        planned_quantity = request.form['planned_quantity']

        cursor.execute("""
            INSERT INTO production (date, finished_product_id, planned_quantity, status)
            VALUES (%s, %s, %s, 'IN_PROGRESS')
        """, (date, finished_product_id, planned_quantity))
        conn.commit()

        flash('Orden de producción creada con éxito', 'success')
        cursor.close(); conn.close()
        return redirect(url_for('list_production'))

    # 🔹 Mostrar lista de productos terminados
    cursor.execute("SELECT id, nombre FROM mercancia")   # o finished_products si la tienes
    products = cursor.fetchall()

    cursor.close(); conn.close()
    # 👇 ahora apunta a templates/inventarios/WIP/production_new.html
    return render_template('inventarios/WIP/production_new.html', products=products)


@app.route('/production')
def list_production():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id, p.date, m.nombre AS product, p.planned_quantity, p.status
        FROM production p
        JOIN mercancia m ON p.finished_product_id = m.id
        ORDER BY p.date DESC
    """)
    productions = cursor.fetchall()

    cursor.close(); conn.close()
    # 👇 ahora apunta a templates/inventarios/WIP/production_list.html
    return render_template('inventarios/WIP/production_list.html', productions=productions)


@app.route('/production/<int:production_id>/materials', methods=['GET', 'POST'])
def production_materials(production_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 🔹 Verificar que la orden existe
    cursor.execute("SELECT p.id, p.date, m.nombre AS product FROM production p JOIN mercancia m ON p.finished_product_id = m.id WHERE p.id = %s", (production_id,))
    production = cursor.fetchone()
    if not production:
        cursor.close(); conn.close()
        flash('Orden de producción no encontrada.', 'warning')
        return redirect(url_for('list_production'))

    if request.method == 'POST':
        raw_material_id = request.form['raw_material_id']
        quantity_used = request.form['quantity_used']

        # Guardar detalle en production_raw_materials
        cursor.execute("""
            INSERT INTO production_raw_materials (production_id, raw_material_id, quantity_used)
            VALUES (%s, %s, %s)
        """, (production_id, raw_material_id, quantity_used))

        # También generar salida en inventario_movimientos
        cursor.execute("""
            INSERT INTO inventario_movimientos
            (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
            VALUES (1, %s, 'SALIDA', %s, 0, %s, NOW())
        """, (raw_material_id, quantity_used, f'Producción {production_id}'))

        conn.commit()
        flash('Materia prima registrada en la producción.', 'success')
        cursor.close(); conn.close()
        return redirect(url_for('production_materials', production_id=production_id))

    # 🔹 Si es GET → mostrar formulario con lista de materias primas
    cursor.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
    materials = cursor.fetchall()

    cursor.execute("SELECT prm.id, m.nombre, prm.quantity_used FROM production_raw_materials prm JOIN mercancia m ON prm.raw_material_id = m.id WHERE prm.production_id = %s", (production_id,))
    used_materials = cursor.fetchall()

    cursor.close(); conn.close()
    return render_template('inventarios/WIP/production_materials.html',
                           production=production,
                           materials=materials,
                           used_materials=used_materials)


@app.route('/production/<int:production_id>/wip', methods=['GET', 'POST'])
def production_wip(production_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 🔹 Verificar que la orden existe
    cursor.execute("""
        SELECT p.id, p.date, m.nombre AS product, p.planned_quantity
        FROM production p
        JOIN mercancia m ON p.finished_product_id = m.id
        WHERE p.id = %s
    """, (production_id,))
    production = cursor.fetchone()
    if not production:
        cursor.close(); conn.close()
        flash('Orden de producción no encontrada.', 'warning')
        return redirect(url_for('list_production'))

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        unit_cost = request.form['unit_cost']

        # Guardar entrada a WIP
        cursor.execute("""
            INSERT INTO production_wip (production_id, product_id, quantity, unit_cost)
            VALUES (%s, %s, %s, %s)
        """, (production_id, product_id, quantity, unit_cost))

        # También generar entrada en inventario_movimientos
        cursor.execute("""
            INSERT INTO inventario_movimientos
            (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
            VALUES (2, %s, 'ENTRADA', %s, %s, %s, NOW())
        """, (product_id, quantity, unit_cost, f'Producción {production_id} - WIP'))

        conn.commit()
        flash('Producto en proceso registrado en WIP.', 'success')
        cursor.close(); conn.close()
        return redirect(url_for('production_wip', production_id=production_id))

    # 🔹 Si es GET → mostrar formulario
    cursor.execute("SELECT id, nombre FROM mercancia ORDER BY nombre")
    products = cursor.fetchall()

    cursor.execute("""
        SELECT pw.id, m.nombre, pw.quantity, pw.unit_cost
        FROM production_wip pw
        JOIN mercancia m ON pw.product_id = m.id
        WHERE pw.production_id = %s
    """, (production_id,))
    wip_items = cursor.fetchall()

    cursor.close(); conn.close()
    return render_template('inventarios/WIP/production_wip.html',
                           production=production,
                           products=products,
                           wip_items=wip_items)




#   PT    INVENTORY 


@app.route('/production/<int:production_id>/close', methods=['POST'])
def close_production(production_id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # 🔹 Obtener la orden
    cursor.execute("""
        SELECT p.id, p.finished_product_id, p.planned_quantity, p.status
        FROM production p
        WHERE p.id = %s
    """, (production_id,))
    production = cursor.fetchone()

    if not production:
        cursor.close(); conn.close()
        flash('Orden de producción no encontrada.', 'warning')
        return redirect(url_for('list_production'))

    if production['status'] == 'CLOSED':
        cursor.close(); conn.close()
        flash('La orden ya está cerrada.', 'info')
        return redirect(url_for('list_production'))

    # 🔹 Calcular total producido en WIP
    cursor.execute("""
        SELECT SUM(quantity) AS total_qty, AVG(unit_cost) AS avg_cost
        FROM production_wip
        WHERE production_id = %s
    """, (production_id,))
    wip_data = cursor.fetchone()
    total_qty = wip_data['total_qty'] or 0
    avg_cost = wip_data['avg_cost'] or 0

    if total_qty <= 0:
        cursor.close(); conn.close()
        flash('No hay producto en proceso registrado para cerrar.', 'danger')
        return redirect(url_for('production_wip', production_id=production_id))

    # 🔹 Salida de WIP
    cursor.execute("""
        INSERT INTO inventario_movimientos
        (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
        VALUES (2, %s, 'SALIDA', %s, %s, %s, NOW())
    """, (production['finished_product_id'], total_qty, avg_cost, f'Producción {production_id} Cerrada'))

    # 🔹 Entrada a Productos Terminados
    cursor.execute("""
        INSERT INTO inventario_movimientos
        (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
        VALUES (3, %s, 'ENTRADA', %s, %s, %s, NOW())
    """, (production['finished_product_id'], total_qty, avg_cost, f'Producción {production_id} Cerrada'))

    # 🔹 Actualizar estado de la orden
    cursor.execute("UPDATE production SET status = 'CLOSED' WHERE id = %s", (production_id,))
    conn.commit()

    cursor.close(); conn.close()
    flash(f'Producción #{production_id} cerrada con éxito.', 'success')
    return redirect(url_for('list_production'))





#    HOME  PANEL DE CONTROL    LOGIN    SIDEBAR    #



@app.route('/')
def home():
    """
    Muestra la página de inicio con accesos a los módulos principales del ERP.
    """
    return render_template('home.html')

@app.route('/panel_de_control')
def panel_de_control():
    """
    Muestra el panel exclusivo del administrador con accesos rápidos.
    """
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    return render_template('panel_admin.html')

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
            session['usuario_id'] = usuario['id']
            session['rol'] = usuario['rol']
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



@app.route('/nueva_compra', methods=['GET', 'POST'])
def nueva_compra():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado. Solo el administrador puede registrar compras.', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        proveedor = request.form['proveedor']
        fecha = request.form['fecha']
        numero_factura = request.form['numero_factura']
        metodo_pago = request.form['metodo_pago']

        productos = request.form.getlist('producto[]')
        unidades = request.form.getlist('unidades[]')
        precios = request.form.getlist('precio_unitario[]')
        totales = request.form.getlist('precio_total[]')

        # 🚨 Debug
        print("📦 DEBUG nueva_compra:")
        print("  productos:", productos)
        print("  unidades:", unidades)
        print("  precios:", precios)
        print("  totales:", totales)

        try:
            total_general = sum(
                Decimal(t.replace(',', '.'))
                for t in totales if t and t.strip()
            )
        except (InvalidOperation, TypeError):
            flash("Error en los valores numéricos del formulario.", "danger")
            return redirect(url_for('nueva_compra'))

        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)

        # Validar que todos los productos existan
        for prod in productos:
            cursor.execute("SELECT id FROM mercancia WHERE nombre = %s", (prod.strip(),))
            if not cursor.fetchone():
                cursor.close(); conn.close()
                flash(f"El producto '{prod.strip()}' no está registrado en el catálogo.", "danger")
                return redirect(url_for("mercancia"))

        try:
            # Insertar encabezado en listado_compras
            cursor.execute("""
                INSERT INTO listado_compras (proveedor, fecha, numero_factura, total)
                VALUES (%s, %s, %s, %s)
            """, (proveedor, fecha, numero_factura, float(total_general)))
            compra_id = cursor.lastrowid

            # Movimientos contables básicos
            cuenta_pago = 30 if metodo_pago == "efectivo" else 40 if metodo_pago == "banco" else 30
            movimientos = [
                {"cuenta_id": 10, "debe": float(total_general), "haber": 0},   # Inventarios
                {"cuenta_id": cuenta_pago, "debe": 0, "haber": float(total_general)}  # Pago
            ]
            registrar_asiento_compra(cursor, conn, f"Compra {numero_factura}", movimientos)

            # Insertar detalle de cada producto
            for prod, und, pu, pt in zip(productos, unidades, precios, totales):
                if not prod.strip():
                    continue

                cursor.execute("SELECT id, cont_neto FROM mercancia WHERE nombre = %s", (prod.strip(),))
                row = cursor.fetchone()
                if not row:
                    continue

                mercancia_id = row["id"]
                try:
                    cont_neto = float(row["cont_neto"])
                    if cont_neto <= 0:
                        cont_neto = 1
                except (TypeError, ValueError):
                    cont_neto = 1

                unidades_base = float(und or 0)
                contenido_neto_total = unidades_base * cont_neto   # 👈 nunca será 0 si hay unidades

                # Guardar en detalle_compra
                cursor.execute("""
                    INSERT INTO detalle_compra
                    (compra_id, mercancia_id, producto, unidades, contenido_neto_total, precio_unitario, precio_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    compra_id,
                    mercancia_id,
                    prod.strip(),
                    unidades_base,
                    contenido_neto_total,
                    float(pu or 0),
                    float(pt or 0)
                ))

                # Actualizar inventario
                cursor.execute("SELECT id FROM inventario WHERE mercancia_id = %s", (mercancia_id,))
                inv = cursor.fetchone()
                if inv:
                    cursor.execute("""
                        UPDATE inventario SET entradas = entradas + %s WHERE mercancia_id = %s
                    """, (unidades_base, mercancia_id))
                else:
                    cursor.execute("""
                        INSERT INTO inventario (producto, inventario_inicial, entradas, salidas, aprobado, mercancia_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (prod.strip(), 0, unidades_base, 0, 0, mercancia_id))

                cursor.execute("""
                    INSERT INTO inventario_movimientos
                    (tipo_inventario_id, mercancia_id, tipo_movimiento, unidades, precio_unitario, referencia, fecha)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    1,
                    mercancia_id,
                    'COMPRA',
                    contenido_neto_total,
                    float(pu or 0),
                    numero_factura,   # Documento como referencia
                    fecha             # 👈 aquí usas la fecha real de la compra (viene del formulario)
                ))
                
            conn.commit()
            flash("Compra registrada exitosamente y stock actualizado", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al registrar la compra o actualizar inventario: {e}", "danger")
        finally:
            cursor.close(); conn.close()

        return redirect(url_for('detalle_compra', id=compra_id))

    # GET → cargar formulario
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre FROM proveedores")
    proveedores = cursor.fetchall()
    cursor.execute("SELECT nombre FROM mercancia")
    productos = [row['nombre'] for row in cursor.fetchall()]
    cursor.close(); conn.close()
    return render_template('nueva_compra.html', proveedores=proveedores, productos=productos)


def registrar_asiento_compra(cursor, conn, concepto, movimientos):
    """
    movimientos = [
        {"cuenta_id": 10, "debe": 500, "haber": 0},   # Inventarios
        {"cuenta_id": 20, "debe": 80, "haber": 0},    # IVA acreditable
        {"cuenta_id": 30, "debe": 0, "haber": 580},   # Caja
    ]
    """
    # 1) Insertar cabecera
    cursor.execute("""
        INSERT INTO asientos_contables (fecha, concepto)
        VALUES (NOW(), %s)
    """, (concepto,))
    asiento_id = cursor.lastrowid

    # 2) Insertar detalles
    for mov in movimientos:
        cursor.execute("""
            INSERT INTO asientos_detalle (asiento_id, cuenta_id, debe, haber)
            VALUES (%s, %s, %s, %s)
        """, (asiento_id, mov["cuenta_id"], mov["debe"], mov["haber"]))

    conn.commit()
    return asiento_id

@app.route('/detalle_compra/<int:id>')
def detalle_compra(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # Encabezado
    cursor.execute("""
        SELECT id, proveedor, DATE_FORMAT(fecha, '%d %b %Y') AS fecha, numero_factura, total
        FROM listado_compras
        WHERE id = %s
    """, (id,))
    compra = cursor.fetchone()

    if not compra:
        cursor.close()
        conn.close()
        flash('La compra no existe.', 'warning')
        return redirect(url_for('listado_compras'))

    # 👇 YA fuera del if
    cursor.execute("""
        SELECT
            d.id,
            COALESCE(m.nombre, d.producto) AS producto,
            d.unidades,
            d.contenido_neto_total,
            d.precio_unitario,
            d.precio_total
        FROM detalle_compra d
        LEFT JOIN mercancia m ON m.id = d.mercancia_id
        WHERE d.compra_id = %s
        ORDER BY d.id
    """, (id,))
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
                DATE_FORMAT(fecha, '%d %b %Y') AS fecha,  -- fecha como texto
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


@app.route('/eliminar_compra/<int:id>')
def eliminar_compra(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor()
    try:
        # Elimina los detalles relacionados
        cursor.execute(
            "DELETE FROM detalle_compra WHERE compra_id = %s", (id,))

        # Luego elimina la compra principal
        cursor.execute("DELETE FROM listado_compras WHERE id = %s", (id,))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Compra eliminada correctamente.', 'success')
    except mysql.connector.Error as e:
        flash(f'Error al eliminar: {e}', 'danger')

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




#   COMPRAS - MERCANCIA  #



@app.route('/mercancia', methods=['GET', 'POST'])
def mercancia():
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        cont_neto = request.form['cont_neto'].strip()
        unidad_id = int(request.form['unidad_id'])
        iva = 1 if request.form.get('iva') else 0
        ieps = 1 if request.form.get('ieps') else 0

        conn = conexion_db()
        cursor = conn.cursor(dictionary=True)   # <-- importante
        
        try:
            # 1) Padre por defecto para productos: 112-001-000 (o el primero 112-xxx-000 con permite_subcuentas=1)
            cuenta_padre_id = get_default_inventory_parent(cursor, conn)

            # 2) Crear / reutilizar subcuenta nivel 3 para este producto (112-001-001, 112-001-002, ...)
            subcuenta_id, subcuenta_codigo = create_lvl3_account_for_product(
                cursor, conn,
                nombre_producto=nombre,
                parent_id=cuenta_padre_id
            )

            # 3) Guardar el producto con sus llaves contables
            cursor.execute("""
                INSERT INTO mercancia (nombre, unidad_id, cont_neto, iva, ieps, cuenta_id, subcuenta_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre, unidad_id, cont_neto, iva, ieps, cuenta_padre_id, subcuenta_id))
            
            conn.commit()
            flash(
                f'Producto registrado. Subcuenta asignada automáticamente: {subcuenta_codigo}', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'No se pudo registrar el producto: {e}', 'danger')

        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('mercancia'))

    # --- GET: cargar selects y listado ---
    cursor.execute("SELECT id, nombre FROM unidades_medida ORDER BY nombre")
    unidades = cursor.fetchall()

    cursor.execute("""
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
        ORDER BY p.nombre ASC
    """)
    productos = cursor.fetchall()

    # 🔹 Cargar catálogo de cuentas de nivel 3 (para elegir en el select)
    cursor.execute("""
        SELECT id, CONCAT(codigo, ' - ', nombre) AS etiqueta
        FROM cuentas_contables
        WHERE nivel = 3
        ORDER BY codigo
    """)
    cuentas_catalogo = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('mercancia.html',
                           unidades=unidades,
                           productos=productos,
                        cuentas_catalogo=cuentas_catalogo  # <-- ahora sí se pasa al template
    )


@app.route('/actualizar_mercancia/<int:id>', methods=['POST'])
def actualizar_mercancia(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

     # 🔹 Recuperar datos del formulario
    nombre = request.form['nombre'].strip()
    cont_neto = request.form['cont_neto'].strip()
    unidad_id = int(request.form['unidad_id'])

    # 🔹 IVA e IEPS: aseguramos que siempre tengan un valor entero
    iva = int(request.form.get('iva', 0))   # si no viene => 0
    ieps = int(request.form.get('ieps', 0)) # si no viene => 0

    # 🔹 Cuentas contables (si las editas desde el formulario)
    cuenta_id = int(request.form.get('cuenta_id')) if request.form.get('cuenta_id') else None
    subcuenta_id = int(request.form.get('subcuenta_id')) if request.form.get('subcuenta_id') else None

    # 🔹 Ejecutar update en BD
    conn = conexion_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE mercancia
            SET nombre=%s,
                cont_neto=%s,
                unidad_id=%s,
                iva=%s,
                ieps=%s,
                cuenta_id=%s,
                subcuenta_id=%s
            WHERE id=%s
        """, (nombre, cont_neto, unidad_id, iva, ieps, cuenta_id, subcuenta_id, id))

        conn.commit()
        flash('Mercancía actualizada correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('mercancia'))


@app.route('/eliminar_mercancia/<int:id>', methods=['POST'])
def eliminar_mercancia(id):
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('login'))

    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1) Verificar existencia (y obtener nombre para el mensaje)
        cursor.execute("SELECT id, nombre FROM mercancia WHERE id=%s", (id,))
        row = cursor.fetchone()
        if not row:
            flash('El producto no existe o ya fue eliminado.', 'warning')
            return redirect(url_for('mercancia'))

        # 2) Intentar eliminar
        try:
            cursor.execute("DELETE FROM mercancia WHERE id=%s", (id,))
            conn.commit()
            flash(
                f'Producto “{row["nombre"]}” eliminado correctamente.', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            # 1451 = restricción FK (referenciado en otras tablas)
            if getattr(e, 'errno', None) == 1451:
                flash(
                    'No se puede eliminar: el producto está referenciado en compras, inventario u otros movimientos.', 'warning')
            else:
                flash(f'Error al eliminar el producto: {e.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()

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


@api.get("/inventario")
def api_inventario():
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
          m.id   AS mercancia_id,
          m.nombre,
          COALESCE(SUM(CASE WHEN e.tipo_inventario_id=1 THEN e.unidades_disponibles END),0) AS mp,
          COALESCE(SUM(CASE WHEN e.tipo_inventario_id=2 THEN e.unidades_disponibles END),0) AS wip,
          COALESCE(SUM(CASE WHEN e.tipo_inventario_id=3 THEN e.unidades_disponibles END),0) AS pt
        FROM mercancia m
        LEFT JOIN v_existencias e ON e.mercancia_id = m.id
        GROUP BY m.id, m.nombre
        ORDER BY m.nombre
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    # suma total por SKU
    for r in rows:
        r["disponible_total"] = float(r.get("mp",0) or 0) + float(r.get("wip",0) or 0) + float(r.get("pt",0) or 0)
    return jsonify(rows)

@api.get("/inventario/<int:mercancia_id>/movimientos")
def api_movimientos(mercancia_id: int):
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, fecha, tipo_inventario_id, tipo_movimiento, unidades, precio_unitario, referencia
        FROM inventario_movimientos
        WHERE mercancia_id = %s
        ORDER BY fecha DESC, id DESC
    """, (mercancia_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

app.register_blueprint(api)


# ✅ SOLO este bloque debe estar al final
if __name__ == '__main__':
    app.run(debug=True)