# api/pt_api.py

from flask import jsonify, g, current_app, request
from . import api
from .caja_api import require_token  # reutilizamos el decorador de token
import mysql.connector
import jwt

# Proxy a la conexión definida en app.py (sin bucle circular)
def conexion_db():
    from app import conexion_db as _conexion_db
    return _conexion_db()

# Si YA tienes require_token en otro archivo y lo quieres compartir,
# puedes eliminar este y reutilizar el otro.
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
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except Exception:
            return jsonify({"error": "Token inválido o vencido"}), 401

        g.usuario_id = data["uid"]
        g.empresa_id = data["eid"]
        return f(*args, **kwargs)

    return wrapper


@api.get("/pt")
@require_token
def api_pt_list():
    """
    Catálogo de Productos Terminados (PT) para la app móvil.
    """
    eid = g.empresa_id

    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT 
                m.id,
                m.nombre,
                COALESCE(m.precio, 0)            AS precio_venta,
                COALESCE(inv.disponible_base, 0) AS stock_disponible
            FROM mercancia m
            LEFT JOIN inventario inv
              ON inv.mercancia_id = m.id
             AND inv.empresa_id   = %s
            WHERE m.tipo = 'PT'
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
            "stock": float(r["stock_disponible"] or 0),
        })

    return jsonify({"items": items})

