# api/auth_api.py

from flask import request, jsonify, g, current_app
from . import api
import datetime
import jwt
import bcrypt

# Usar la misma conexión que app.py, pero SIN importar app (evita circular)
def conexion_db():
    from db import conexion_db as _conexion_db
    return _conexion_db()


# Generar token JWT
def crear_token(usuario_id, empresa_id):
    payload = {
        "uid": usuario_id,
        "eid": empresa_id,
        # 8 horas de vigencia
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


@api.post("/login")
def api_login():
    """
    Login para la app móvil / pruebas.
    Acepta:
      - JSON: { "correo": "...", "password": "..." }
      - JSON: { "usuario": "...", "password": "..." }
      - FORM: campos 'correo' o 'usuario', y 'password' o 'contrasena'
    """

    # Intentar leer JSON de forma segura
    data_json = request.get_json(silent=True) or {}

    # Normalizar correo / usuario
    correo = (
        data_json.get("correo")
        or data_json.get("usuario")
        or request.form.get("correo")
        or request.form.get("usuario")
    )

    # Normalizar contraseña
    password = (
        data_json.get("password")
        or data_json.get("contrasena")
        or request.form.get("password")
        or request.form.get("contrasena")
    )

    if not correo or not password:
        return jsonify({"error": "Correo y contraseña son obligatorios"}), 400

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        # Tu tabla 'usuarios' (según DESCRIBE) tiene:
        # correo, contrasena (hash), empresa_id, activo, etc.
        cur.execute(
            """
            SELECT id, empresa_id, contrasena, activo
            FROM usuarios
            WHERE correo = %s
            """,
            (correo,),
        )
        row = cur.fetchone()

    finally:
        cur.close()
        conn.close()

    # Usuario no encontrado
    if not row:
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Usuario inactivo
    if row.get("activo") == 0:
        return jsonify({"error": "Usuario inactivo"}), 403

    # Validar contraseña con bcrypt
    try:
        hash_guardado = row["contrasena"] or ""
        ok = bcrypt.checkpw(
            password.encode("utf-8"),
            hash_guardado.encode("utf-8"),
        )
    except Exception:
        ok = False

    if not ok:
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Si todo bien, generar token
    token = crear_token(row["id"], row["empresa_id"])

    return jsonify(
        {
            "token": token,
            "usuario_id": row["id"],
            "empresa_id": row["empresa_id"],
        }
    )
