import bcrypt

# Contraseña original (texto plano)
contrasena_original = "admin123"

# Generar hash
hash_generado = bcrypt.hashpw(contrasena_original.encode('utf-8'), bcrypt.gensalt())

print("Hash generado:", hash_generado.decode())

# Ahora probamos si una contraseña ingresada coincide con el hash:
contrasena_ingresada = "admin123"  # prueba con la correcta y luego con una incorrecta

if bcrypt.checkpw(contrasena_ingresada.encode('utf-8'), hash_generado):
    print("¡Contraseña correcta!")
else:
    print("Contraseña incorrecta.")