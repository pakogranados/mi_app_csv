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
