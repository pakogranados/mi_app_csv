# api/caja_api.py

from flask import request, jsonify, g, current_app
from . import api
import jwt

# Proxy a la conexión de app.py (evita import circular directo)
def conexion_db():
    from db import conexion_db as _conexion_db   # O desde donde realmente la tienes
    return _conexion_db()


# Decorador para validar tokens
def require_token(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401

        token = auth.split(" ", 1)[1]
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],  # usa current_app, NO importes app
                algorithms=["HS256"]
            )
        except Exception:
            return jsonify({"error": "Token inválido o vencido"}), 401

        g.usuario_id = data["uid"]
        g.empresa_id = data["eid"]
        return f(*args, **kwargs)

    return wrapper


@api.get("/caja/config")
@require_token
def api_caja_config():
    eid = g.empresa_id
    caja_id = request.args.get("caja_id", type=int)

    if not caja_id:
        return jsonify({"error": "caja_id requerido"}), 400

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    # Validar la caja
    cur.execute("""
        SELECT id, nombre
        FROM cajas
        WHERE id=%s AND empresa_id=%s AND activo=1
    """, (caja_id, eid))
    caja = cur.fetchone()
    if not caja:
        cur.close()
        conn.close()
        return jsonify({"error": "Caja no encontrada"}), 404

    # Botones
    cur.execute("""
        SELECT id, fila, columna, etiqueta, color, tipo, producto_id
        FROM caja_botones
        WHERE caja_id = %s
        ORDER BY fila, columna
    """, (caja_id,))
    botones = cur.fetchall()

    # Cargar productos a los que apuntan los botones
    producto_ids = [b["producto_id"] for b in botones if b["producto_id"]]
    productos_map = {}

    if producto_ids:
        placeholders = ",".join(["%s"] * len(producto_ids))
        cur.execute(f"""
            SELECT 
                id, 
                nombre, 
                precio AS precio_venta   -- usamos 'precio' y lo renombramos
            FROM mercancia
            WHERE id IN ({placeholders})
        """, producto_ids)
        for row in cur.fetchall():
            productos_map[row["id"]] = row


    cur.close()
    conn.close()

    resp_botones = []
    for b in botones:
        info = dict(b)
        if b["producto_id"]:
            p = productos_map.get(b["producto_id"])
            if p:
                info["producto"] = {
                    "nombre": p["nombre"],
                    "precio_venta": float(p.get("precio_venta") or 0),
                }
        resp_botones.append(info)

    return jsonify({
        "caja": caja,
        "botones": resp_botones
    })


@api.get("/pt")
@require_token
def api_pt_list():
    """
    Catálogo de Productos Terminados (PT) para la app móvil.
    Reutiliza el mismo catálogo PT que usas en el módulo web.
    """
    eid = g.empresa_id

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT 
                m.id,
                m.nombre,
                COALESCE(m.precio, 0) AS precio_venta,
                COALESCE(inv.inventario_inicial, 0)
              + COALESCE(inv.entradas, 0)
              - COALESCE(inv.salidas, 0) AS stock
            FROM mercancia m
            LEFT JOIN inventario inv 
                   ON inv.mercancia_id = m.id
            WHERE m.tipo_inventario_id = 3     -- PT
              AND m.empresa_id = %s
              AND m.activo = 1
            ORDER BY m.nombre
        """, (eid,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "nombre": r["nombre"],
            "precio_venta": float(r["precio_venta"] or 0),
            "stock": float(r["stock"] or 0),
        })

    return jsonify({"items": items})
