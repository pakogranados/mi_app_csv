import bcrypt

# Contraseñas en texto plano
admin_password = 'admin123'
editor_password = 'editor123'

# Generar los hashes
admin_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
editor_hash = bcrypt.hashpw(editor_password.encode('utf-8'), bcrypt.gensalt())

print(f"Hash para admin123: {admin_hash.decode()}")
print(f"Hash para editor123: {editor_hash.decode()}")

