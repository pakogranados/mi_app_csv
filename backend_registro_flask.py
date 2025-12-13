@app.route('/registrar_proveedor', methods=['GET', 'POST'])
def registrar_proveedor():
    """
    Formulario para registrar un nuevo proveedor.
    """
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        ciudad = request.form['ciudad']
        telefono = request.form['telefono']

        try:
            conn = conexion_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO proveedores (nombre, direccion, ciudad, telefono)
                VALUES (%s, %s, %s, %s)
            """, (nombre, direccion, ciudad, telefono))

            conn.commit()
            cursor.close()
            conn.close()
            flash('Proveedor registrado correctamente', 'success')
            return redirect('/registrar_proveedor')

        except mysql.connector.Error as e:
            flash(f'Error al registrar proveedor: {e}', 'danger')
            return redirect('/registrar_proveedor')

    return render_template('registrar_proveedor.html')


@app.route('/registrar_producto', methods=['GET', 'POST'])
def registrar_producto():
    """
    Formulario para registrar un nuevo producto con relaciones a otras tablas.
    """
    conn = conexion_db()
    cursor = conn.cursor(dictionary=True)

    # Obtener listas para los selects
    cursor.execute("SELECT id, nombre FROM unidades_medida")
    unidades = cursor.fetchall()
    cursor.execute("SELECT id, nombre FROM cuentas_contables")
    cuentas = cursor.fetchall()
    cursor.execute("SELECT id, nombre FROM subcuentas_contables")
    subcuentas = cursor.fetchall()

    if request.method == 'POST':
        nombre = request.form['nombre']
        unidad_id = request.form['unidad_id']
        cuenta_id = request.form['cuenta_id']
        subcuenta_id = request.form['subcuenta_id']

        try:
            cursor.execute("""
                INSERT INTO productos (nombre, unidad_id, cuenta_id, subcuenta_id)
                VALUES (%s, %s, %s, %s)
            """, (nombre, unidad_id, cuenta_id, subcuenta_id))
            conn.commit()
            flash('Producto registrado correctamente', 'success')
            return redirect('/registrar_producto')

        except mysql.connector.Error as e:
            flash(f'Error al registrar producto: {e}', 'danger')
            return redirect('/registrar_producto')

    cursor.close()
    conn.close()
    return render_template('registrar_producto.html',
                           unidades=unidades, cuentas=cuentas, subcuentas=subcuentas)
