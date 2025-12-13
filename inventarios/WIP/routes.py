# Inventarios/WIP/routes.py
from flask import jsonify
import sys
sys.path.append('..')  # Para importar ai_helper desde raíz
from ai_helper import extraer_materiales_con_ia, validar_materiales
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from . import bp
from db import conexion_db  # <- NO desde app
from flask import g
from auth_utils import require_login


@bp.get("/procesos")
@require_login
def procesos_list():
    """Listar procesos de la empresa activa"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            p.id,
            p.nombre,
            p.descripcion,
            p.activo,
            m.nombre AS pt_nombre
        FROM procesos p
        LEFT JOIN mercancia m
               ON m.id = p.pt_id
              AND m.empresa_id = %s
        WHERE p.empresa_id = %s
        ORDER BY p.nombre
    """, (eid, eid))
    items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('inventarios/WIP/procesos_list.html', procesos=items)

@bp.route("/procesos/nuevo", methods=["GET","POST"])
@require_login
def procesos_nuevo():
    """Crear nuevo proceso (aislado por empresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    if request.method == "POST":
        nombre   = (request.form.get("nombre") or "").strip()
        desc     = (request.form.get("descripcion") or "").strip()
        pt_id_s  = request.form.get("pt_id")
        pt_id    = int(pt_id_s) if pt_id_s and pt_id_s.isdigit() else None

        # Nuevos campos
        areas_involucradas = (request.form.get("areas_involucradas") or "").strip()
        responsables       = (request.form.get("responsables") or "").strip()
        materiales         = (request.form.get("materiales") or "").strip()
        costo_s            = request.form.get("costo_estimado")
        try:
            costo_estimado = float(costo_s) if costo_s not in (None, "") else 0.00
        except ValueError:
            costo_estimado = 0.00

        conn = conexion_db()
        cur  = conn.cursor(dictionary=True)
        try:
            # Validar PT pertenece a la empresa
            if pt_id is not None:
                cur.execute("""
                    SELECT id FROM mercancia
                    WHERE id=%s AND empresa_id=%s AND tipo='PT'
                    """, (pt_id, eid))
                if not cur.fetchone():
                    flash("El PT seleccionado no pertenece a esta empresa.", "warning")
                    return redirect(url_for("wip.procesos_nuevo"))

            # (Opcional) Evitar duplicados por nombre en la empresa
            if nombre:
                cur.execute("""
                    SELECT 1 FROM procesos
                    WHERE empresa_id=%s AND UPPER(TRIM(nombre))=UPPER(TRIM(%s))
                    LIMIT 1
                """, (eid, nombre))
                if cur.fetchone():
                    flash("Ya existe un proceso con ese nombre en esta empresa.", "warning")
                    return redirect(url_for("wip.procesos_nuevo"))

            # Insert con empresa_id
            cur.execute("""
                INSERT INTO procesos
                    (empresa_id, pt_id, nombre, descripcion,
                     areas_involucradas, responsables, materiales,
                     costo_estimado, activo)
                VALUES
                    (%s, %s, %s, %s,
                     %s, %s, %s,
                     %s, 1)
            """, (eid, pt_id, nombre, desc,
                  areas_involucradas, responsables, materiales,
                  costo_estimado))
            conn.commit()
            flash("✅ Proceso creado correctamente", "success")
            return redirect(url_for("wip.procesos_list"))

        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("wip.procesos_nuevo"))
        finally:
            try: cur.close()
            except: pass
            try: conn.close()
            except: pass

    # GET: cargar PTs de la empresa
    conn = conexion_db()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, nombre
        FROM mercancia
        WHERE empresa_id=%s AND tipo='PT'
        ORDER BY nombre
    """, (eid,))
    pts = cur.fetchall()
    cur.close(); conn.close()
    return render_template('inventarios/WIP/procesos_form.html', item=None, pts=pts)

@bp.route("/procesos/<int:id>/editar", methods=["GET","POST"])
@require_login
def procesos_editar(id):
    """Editar proceso existente (aislado por empresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        if request.method == "POST":
            nombre   = (request.form.get("nombre") or "").strip()
            desc     = (request.form.get("descripcion") or "").strip()
            activo   = 1 if request.form.get("activo") == "1" else 0
            pt_id_s  = request.form.get("pt_id")
            pt_id    = int(pt_id_s) if pt_id_s and pt_id_s.isdigit() else None

            # Campos nuevos
            areas_involucradas = (request.form.get("areas_involucradas") or "").strip()
            responsables       = (request.form.get("responsables") or "").strip()
            materiales         = (request.form.get("materiales") or "").strip()
            costo_s            = request.form.get("costo_estimado")
            try:
                costo_estimado = float(costo_s) if costo_s not in (None, "") else 0.00
            except ValueError:
                costo_estimado = 0.00

            # Validar que el proceso pertenezca a la empresa
            cur.execute("SELECT id FROM procesos WHERE id=%s AND empresa_id=%s", (id, eid))
            if not cur.fetchone():
                flash("Proceso no encontrado en esta empresa.", "warning")
                return redirect(url_for("wip.procesos_list"))

            # Validar PT del mismo tenant (si viene)
            if pt_id is not None:
                cur.execute("""
                    SELECT id FROM mercancia
                    WHERE id=%s AND empresa_id=%s AND tipo='PT'
                """, (pt_id, eid))
                if not cur.fetchone():
                    flash("El PT seleccionado no pertenece a esta empresa.", "warning")
                    return redirect(url_for("wip.procesos_editar", id=id))

            # Actualizar
            cur.execute("""
                UPDATE procesos
                   SET pt_id=%s,
                       nombre=%s,
                       descripcion=%s,
                       areas_involucradas=%s,
                       responsables=%s,
                       materiales=%s,
                       costo_estimado=%s,
                       activo=%s
                 WHERE id=%s
                   AND empresa_id=%s
            """, (pt_id, nombre, desc, areas_involucradas, responsables,
                  materiales, costo_estimado, activo, id, eid))
            conn.commit()
            flash("✅ Proceso actualizado", "success")
            return redirect(url_for("wip.procesos_list"))

        # GET: cargar proceso + catálogo de PTs del tenant
        cur.execute("SELECT * FROM procesos WHERE id=%s AND empresa_id=%s", (id, eid))
        item = cur.fetchone()
        if not item:
            flash("Proceso no encontrado", "warning")
            return redirect(url_for("wip.procesos_list"))

        cur.execute("""
            SELECT id, nombre
            FROM mercancia
            WHERE empresa_id=%s AND tipo='PT'
            ORDER BY nombre
        """, (eid,))
        pts = cur.fetchall()

        return render_template("inventarios/WIP/procesos_form.html", item=item, pts=pts)

    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass


# ==================== PASOS DEL PROCESO ====================
@bp.post("/procesos/<int:proceso_id>/analizar_descripcion")
def analizar_descripcion(proceso_id):
    """Analiza descripción con IA y extrae materiales"""
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    descripcion = request.json.get('descripcion', '').strip()
    
    if not descripcion or len(descripcion) < 10:
        return jsonify({'error': 'Descripción muy corta'}), 400
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    # Obtener lista de mercancías MP
    cur.execute("SELECT id, nombre FROM mercancia WHERE tipo='MP' ORDER BY nombre")
    mercancia_disponible = cur.fetchall()
    
    cur.close()
    conn.close()
    
    try:
        # Llamar a la IA
        materiales_detectados = extraer_materiales_con_ia(descripcion, mercancia_disponible)
        
        # Validar resultados
        materiales_validados = validar_materiales(materiales_detectados, mercancia_disponible)
        
        return jsonify({
            'success': True,
            'materiales': materiales_validados
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.get("/areas/<int:area_id>/responsable")
def obtener_responsable_area(area_id):
    """Obtiene el usuario responsable de un área"""
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("""
        SELECT u.id, u.nombre, u.puesto, u.correo
        FROM usuarios u
        JOIN usuario_areas ua ON ua.usuario_id = u.id
        WHERE ua.area_id = %s AND ua.es_responsable = 1
        LIMIT 1
    """, (area_id,))
    
    responsable = cur.fetchone()
    cur.close()
    conn.close()
    
    if responsable:
        return jsonify({
            'success': True,
            'responsable': {
                'id': responsable['id'],
                'nombre': responsable['nombre'],
                'puesto': responsable['puesto'] or 'Sin puesto',
                'correo': responsable['correo']
            }
        })
    else:
        return jsonify({
            'success': False,
            'mensaje': 'No hay responsable asignado a esta área'
        })

@bp.route("/procesos/<int:proceso_id>/pasos", methods=["GET","POST"])
def pasos(proceso_id):
    """Gestionar pasos de un proceso"""
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    # POST: Agregar nuevo paso CON materiales detectados por IA
    if request.method == "POST":
        accion = request.form.get("accion", "agregar")
        
        if accion == "agregar":
            nombre = (request.form.get("nombre") or "").strip()
            descripcion = (request.form.get("descripcion") or "").strip()
            area_id_s = request.form.get("area_id")
            area_id = int(area_id_s) if area_id_s and area_id_s.isdigit() else None
            responsable = (request.form.get("responsable") or "").strip()
            requiere = 1 if request.form.get("requiere_validez") == "1" else 0
            minutos_s = request.form.get("minutos_estimados")
            minutos = int(minutos_s) if minutos_s and minutos_s.isdigit() else None
            
            # Obtener siguiente orden
            cur.execute(
                "SELECT COALESCE(MAX(orden), 0) + 1 AS siguiente FROM proceso_pasos WHERE proceso_id=%s",
                (proceso_id,)
            )
            siguiente = cur.fetchone()["siguiente"]
            
            # Insertar paso (bloqueado por defecto al guardar con materiales)
            cur.execute("""
                INSERT INTO proceso_pasos 
                (proceso_id, orden, nombre, descripcion, area_id, responsable, requiere_validez, 
                 minutos_estimados, costo_estimado, estado, bloqueado, fecha_guardado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, 'guardado', 1, NOW())
            """, (proceso_id, siguiente, nombre, descripcion, area_id, responsable, requiere, minutos))
            
            paso_id = cur.lastrowid
            
            # ✅ NUEVO: Vincular usuarios responsables del área con el paso
            if area_id:
                try:
                    cur.execute("""
                        INSERT INTO paso_responsables (paso_id, usuario_id)
                        SELECT %s, usuario_id
                        FROM usuario_areas
                        WHERE area_id = %s AND es_responsable = 1
                    """, (paso_id, area_id))
                except Exception as e:
                    # Si la tabla no existe o hay error, continuar sin fallar
                    print(f"Advertencia: No se pudieron vincular responsables: {e}")
            
            # Procesar materiales detectados por IA (vienen como JSON)
            materiales_json = request.form.get("materiales_json", "[]")
            try:
                import json
                materiales = json.loads(materiales_json)
                
                for mat in materiales:
                    if mat.get('mercancia_id') and mat.get('cantidad', 0) > 0:
                        cur.execute("""
                            INSERT INTO paso_insumos (paso_id, mp_id, cantidad_por_lote, unidad_id)
                            VALUES (%s, %s, %s, NULL)
                        """, (paso_id, mat['mercancia_id'], mat['cantidad']))
                
            except json.JSONDecodeError:
                pass
            
            conn.commit()
            flash("✅ Paso guardado y bloqueado correctamente", "success")
            return redirect(url_for("wip.pasos", proceso_id=proceso_id))
        
        elif accion == "desbloquear":
            paso_id = int(request.form.get("paso_id"))
            cur.execute("UPDATE proceso_pasos SET bloqueado=0, estado='borrador' WHERE id=%s", (paso_id,))
            conn.commit()
            flash("🔓 Paso desbloqueado para edición", "info")
            return redirect(url_for("wip.pasos", proceso_id=proceso_id))
    
    # GET: Mostrar pasos
    cur.execute("SELECT id, nombre, descripcion FROM procesos WHERE id=%s", (proceso_id,))
    proceso = cur.fetchone()
    
    if not proceso:
        cur.close()
        conn.close()
        flash("Proceso no encontrado", "warning")
        return redirect(url_for("wip.procesos_list"))
    
    # Pasos con cálculo de costo
    cur.execute("""
        SELECT pp.*, a.nombre as area_nombre
        FROM proceso_pasos pp
        LEFT JOIN areas_produccion a ON a.id = pp.area_id
        WHERE pp.proceso_id = %s
        ORDER BY pp.orden, pp.id
    """, (proceso_id,))
    pasos = cur.fetchall()
    
    # Insumos por paso CON PRECIOS
    cur.execute("""
        SELECT 
            pi.id, 
            pi.paso_id, 
            pi.cantidad_por_lote,
            m.nombre as mp_nombre, 
            m.id as mp_id,
            m.cont_neto,
            u.nombre as unidad,
            COALESCE(
                (
                    -- Calcular costo promedio ponderado del inventario actual
                    SELECT 
                        CASE 
                            WHEN SUM(
                                CASE 
                                    WHEN UPPER(im.tipo_movimiento) IN ('ENTRADA', 'COMPRA') 
                                    THEN im.unidades 
                                    ELSE -im.unidades 
                                END
                            ) > 0
                            THEN SUM(
                                CASE 
                                    WHEN UPPER(im.tipo_movimiento) IN ('ENTRADA', 'COMPRA') 
                                    THEN im.unidades * im.precio_unitario 
                                    ELSE -im.unidades * im.precio_unitario 
                                END
                            ) / SUM(
                                CASE 
                                    WHEN UPPER(im.tipo_movimiento) IN ('ENTRADA', 'COMPRA') 
                                    THEN im.unidades 
                                    ELSE -im.unidades 
                                END
                            ) / m.cont_neto
                            ELSE 0 
                        END as costo_promedio_por_unidad_base
                    FROM inventario_movimientos im
                    WHERE im.mercancia_id = m.id
                ), 
                0
            ) as precio_unitario
        FROM paso_insumos pi
        JOIN mercancia m ON m.id = pi.mp_id
        LEFT JOIN unidades_medida u ON u.id = m.unidad_id
        WHERE pi.paso_id IN (SELECT id FROM proceso_pasos WHERE proceso_id = %s)
        ORDER BY pi.paso_id, m.nombre
    """, (proceso_id,))
 
    insumos = cur.fetchall()
    
    # Mapear insumos por paso_id y calcular costo real
    insumos_map = {}
    costo_pasos = {}
    for ins in insumos:
        if ins['paso_id'] not in insumos_map:
            insumos_map[ins['paso_id']] = []
            costo_pasos[ins['paso_id']] = 0.00
        
        # Calcular costo del insumo
        costo_insumo = float(ins['cantidad_por_lote']) * float(ins['precio_unitario'])
        ins['costo_total'] = costo_insumo
        costo_pasos[ins['paso_id']] += costo_insumo
        
        insumos_map[ins['paso_id']].append(ins)
    
    # Costo total del proceso
    costo_total_proceso = sum(costo_pasos.values())
    
    # Áreas y MP para los selects
    cur.execute("SELECT id, nombre FROM areas_produccion WHERE activo=1 ORDER BY nombre")
    areas = cur.fetchall()
    
    # MPs con inventario disponible
    cur.execute("""
        SELECT 
            m.id, 
            m.nombre,
            m.cont_neto,
            u.nombre as unidad_base,
            COALESCE(i.entradas - i.salidas, 0) as disponible
        FROM mercancia m
        LEFT JOIN inventario i ON i.mercancia_id = m.id
        LEFT JOIN unidades_medida u ON u.id = m.unidad_id
        WHERE m.tipo = 'MP' AND m.activo = 1
        ORDER BY m.nombre
    """)
    mps = cur.fetchall()
    
    # Calcular resumen de materiales
    resumen_materiales = {}
    for paso_id, materiales in insumos_map.items():
        for mat in materiales:
            mp_id = mat['mp_id']
            if mp_id not in resumen_materiales:
                resumen_materiales[mp_id] = {
                    'nombre': mat['mp_nombre'],
                    'cantidad_total': 0,
                    'unidad': mat['unidad'] or 'unidades'
                }
            resumen_materiales[mp_id]['cantidad_total'] += float(mat['cantidad_por_lote'])
    
    # Convertir a lista ordenada
    resumen_materiales = sorted(resumen_materiales.values(), key=lambda x: x['nombre'])
    total_materiales_unicos = len(resumen_materiales)
    
    # Obtener info del producto terminado si está configurado
    cur.execute("""
        SELECT 
            p.cantidad_producida,
            m.nombre as producto_terminado_nombre,
            u.nombre as unidad_produccion
        FROM procesos p
        LEFT JOIN mercancia m ON m.id = p.producto_terminado_id
        LEFT JOIN unidades_medida u ON u.id = p.unidad_produccion_id
        WHERE p.id = %s
    """, (proceso_id,))
    info_produccion = cur.fetchone()
    
    if info_produccion:
        proceso['cantidad_producida'] = info_produccion['cantidad_producida']
        proceso['producto_terminado_nombre'] = info_produccion['producto_terminado_nombre']
        proceso['unidad_produccion'] = info_produccion['unidad_produccion']
    
    cur.close()
    conn.close()
    
    return render_template(
        "inventarios/WIP/pasos_form.html",
        proceso=proceso,
        pasos=pasos,
        insumos_map=insumos_map,
        costo_pasos=costo_pasos,
        costo_total_proceso=costo_total_proceso,
        areas=areas,
        mps=mps,
        resumen_materiales=resumen_materiales,
        total_materiales_unicos=total_materiales_unicos
    )

@bp.route("/areas/<int:area_id>/responsables")
def area_responsables(area_id):
    """Obtener responsables de un área"""
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("""
        SELECT 
            u.id,
            u.nombre,
            u.correo as email,
            ua.es_responsable
        FROM usuario_areas ua
        JOIN usuarios u ON u.id = ua.usuario_id
        WHERE ua.area_id = %s
        ORDER BY ua.es_responsable DESC, u.nombre
    """, (area_id,))
    
    responsables = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'responsables': responsables
    })

@bp.route("/procesos/<int:proceso_id>/pasos/<int:paso_id>/editar", methods=["GET", "POST"])
def paso_editar(proceso_id, paso_id):
    """Editar un paso desbloqueado"""
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    # Verificar que el paso existe y está desbloqueado
    cur.execute("""
        SELECT pp.*, a.nombre as area_nombre
        FROM proceso_pasos pp
        LEFT JOIN areas_produccion a ON a.id = pp.area_id
        WHERE pp.id = %s AND pp.proceso_id = %s
    """, (paso_id, proceso_id))
    paso = cur.fetchone()
    
    if not paso:
        flash("Paso no encontrado", "danger")
        cur.close()
        conn.close()
        return redirect(url_for('wip.pasos', proceso_id=proceso_id))
    
    if paso['bloqueado']:
        flash("❌ Este paso está bloqueado. Desbloquealo primero.", "warning")
        cur.close()
        conn.close()
        return redirect(url_for('wip.pasos', proceso_id=proceso_id))
    
    # POST: Actualizar paso
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        area_id_s = request.form.get("area_id")
        area_id = int(area_id_s) if area_id_s and area_id_s.isdigit() else None
        responsable = (request.form.get("responsable") or "").strip()
        requiere = 1 if request.form.get("requiere_validez") == "1" else 0
        minutos_s = request.form.get("minutos_estimados")
        minutos = int(minutos_s) if minutos_s and minutos_s.isdigit() else None
        
        # Actualizar paso
        cur.execute("""
            UPDATE proceso_pasos 
            SET nombre=%s, descripcion=%s, area_id=%s, responsable=%s, 
                requiere_validez=%s, minutos_estimados=%s
            WHERE id=%s
        """, (nombre, descripcion, area_id, responsable, requiere, minutos, paso_id))
        
        # Eliminar materiales anteriores
        cur.execute("DELETE FROM paso_insumos WHERE paso_id=%s", (paso_id,))
        
        # Agregar nuevos materiales
        materiales_json = request.form.get("materiales_json", "[]")
        try:
            import json
            materiales = json.loads(materiales_json)
            
            for mat in materiales:
                if mat.get('mercancia_id') and mat.get('cantidad', 0) > 0:
                    cur.execute("""
                        INSERT INTO paso_insumos (paso_id, mp_id, cantidad_por_lote, unidad_id)
                        VALUES (%s, %s, %s, NULL)
                    """, (paso_id, mat['mercancia_id'], mat['cantidad']))
        except json.JSONDecodeError:
            pass
        
        conn.commit()
        flash("✅ Paso actualizado correctamente", "success")
        cur.close()
        conn.close()
        return redirect(url_for("wip.pasos", proceso_id=proceso_id))
    
    # GET: Cargar datos para edición
    cur.execute("SELECT id, nombre FROM procesos WHERE id=%s", (proceso_id,))
    proceso = cur.fetchone()
    
    # Áreas disponibles
    cur.execute("SELECT id, nombre FROM areas_produccion WHERE activo=1 ORDER BY nombre")
    areas = cur.fetchall()
    
    # MPs disponibles
    cur.execute("SELECT id, nombre FROM mercancia WHERE tipo='MP' ORDER BY nombre")
    mps = cur.fetchall()
    
    # Materiales actuales del paso
    cur.execute("""
        SELECT pi.id, pi.cantidad_por_lote, m.id as mercancia_id, m.nombre as mp_nombre
        FROM paso_insumos pi
        JOIN mercancia m ON m.id = pi.mp_id
        WHERE pi.paso_id = %s
        ORDER BY m.nombre
    """, (paso_id,))
    materiales_actuales = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template(
        "inventarios/WIP/paso_editar.html",
        proceso=proceso,
        paso=paso,
        areas=areas,
        mps=mps,
        materiales_actuales=materiales_actuales
    )    

@bp.post("/procesos/<int:proceso_id>/pasos/<int:paso_id>/insumos/agregar")
def paso_insumo_agregar(proceso_id, paso_id):
    """Agregar insumo a un paso"""
    if 'rol' not in session or session['rol'] != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')
    
    mp_id_s = request.form.get("mp_id")
    cantidad_s = request.form.get("cantidad_por_lote")
    unidad_id_s = request.form.get("unidad_id")
    
    if not (mp_id_s and cantidad_s):
        flash("Faltan datos", "warning")
        return redirect(url_for("wip.pasos", proceso_id=proceso_id))
    
    mp_id = int(mp_id_s)
    cantidad = float(cantidad_s)
    unidad_id = int(unidad_id_s) if unidad_id_s and unidad_id_s.isdigit() else None
    
    conn = conexion_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO paso_insumos (paso_id, mp_id, cantidad_por_lote, unidad_id)
        VALUES (%s, %s, %s, %s)
    """, (paso_id, mp_id, cantidad, unidad_id))
    conn.commit()
    cur.close()
    conn.close()
    
    flash("✅ Insumo agregado", "success")
    return redirect(url_for("wip.pasos", proceso_id=proceso_id))

@bp.get("/mercancia/<int:mercancia_id>/info")
def obtener_info_mercancia(mercancia_id):
    """Obtiene información de una mercancía para agregar a un paso"""
    if 'rol' not in session or session['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener mercancía CON INVENTARIO
        cur.execute("""
            SELECT 
                m.id,
                m.nombre,
                m.tipo,
                m.cont_neto,
                u.nombre as unidad_base,
                u.id as unidad_id,
                pb.nombre as producto_base_nombre,
                COALESCE(i.entradas - i.salidas, 0) as disponible
            FROM mercancia m
            LEFT JOIN unidades_medida u ON u.id = m.unidad_id
            LEFT JOIN producto_base pb ON pb.id = m.producto_base_id
            LEFT JOIN inventario i ON i.mercancia_id = m.id
            WHERE m.id = %s AND m.tipo = 'MP'
        """, (mercancia_id,))
        
        mercancia = cur.fetchone()
        
        if not mercancia:
            return jsonify({'success': False, 'error': 'Mercancía no encontrada'}), 404
        
        # Calcular precio promedio ponderado del inventario
        cur.execute("""
            SELECT 
                COALESCE(
                    SUM(CASE 
                        WHEN UPPER(tipo_movimiento) IN ('ENTRADA', 'COMPRA') 
                        THEN unidades 
                        ELSE -unidades 
                    END), 0
                ) as saldo_unidades,
                COALESCE(
                    SUM(CASE 
                        WHEN UPPER(tipo_movimiento) IN ('ENTRADA', 'COMPRA') 
                        THEN unidades * precio_unitario 
                        ELSE -unidades * precio_unitario 
                    END), 0
                ) as saldo_pesos
            FROM inventario_movimientos
            WHERE mercancia_id = %s
        """, (mercancia_id,))

        saldos = cur.fetchone()
        precio_unitario_paquete = (
            saldos['saldo_pesos'] / saldos['saldo_unidades'] 
            if saldos['saldo_unidades'] > 0 
            else 0
        )

        # Calcular precio por unidad base
        cont_neto = float(mercancia['cont_neto']) if mercancia['cont_neto'] else 1
        precio_por_unidad_base = precio_unitario_paquete / cont_neto if cont_neto > 0 else 0
        
        # Calcular disponible en unidad base
        disponible_unidades = float(mercancia['disponible']) if mercancia['disponible'] else 0
        disponible_unidad_base = disponible_unidades * cont_neto
        
        return jsonify({
            'success': True,
            'mercancia': {
                'id': mercancia['id'],
                'nombre': mercancia['nombre'],
                'unidad_base': mercancia['unidad_base'] or 'unidades',
                'unidad_id': mercancia['unidad_id'],
                'contenido_neto': cont_neto,
                'disponible_paquetes': disponible_unidades,
                'disponible_unidad_base': disponible_unidad_base,
                'precio_unitario_paquete': float(precio_unitario_paquete),
                'precio_por_unidad_base': round(precio_por_unidad_base, 6),
                'producto_base': mercancia['producto_base_nombre'],
                'ejemplo_calculo': f"Si usas 100 {mercancia['unidad_base'] or 'unidades'}, el costo será: ${round(precio_por_unidad_base * 100, 2)}"
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@bp.post("/procesos/<int:proceso_id>/pasos/<int:paso_id>/insumos/<int:insumo_id>/eliminar")
@require_login
def paso_insumo_eliminar(proceso_id, paso_id, insumo_id):
    """Eliminar insumo de un paso (aislado por empresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        # Validar que el paso pertenece al proceso y a la empresa
        cur.execute("""
            SELECT 1
            FROM proceso_pasos
            WHERE id=%s AND proceso_id=%s AND empresa_id=%s
            """, (paso_id, proceso_id, eid))
        if not cur.fetchone():
            flash("Paso no encontrado para esta empresa.", "warning")
            return redirect(url_for("wip.pasos", proceso_id=proceso_id))

        # Borrar insumo del paso dentro del tenant
        cur.execute("""
            DELETE FROM paso_insumos
            WHERE id=%s AND paso_id=%s AND empresa_id=%s
        """, (insumo_id, paso_id, eid))
        conn.commit()
        flash("Insumo eliminado", "info")
        return redirect(url_for("wip.pasos", proceso_id=proceso_id))
    except Exception as e:
        conn.rollback()
        flash(f"Error: {e}", "danger")
        return redirect(url_for("wip.pasos", proceso_id=proceso_id))
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

@bp.get("/ordenes")
@require_login
def ordenes_list():
    """Listar órdenes de producción (aislado por empresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT  op.id,
                    op.fecha,
                    op.cantidad,
                    op.estado,
                    op.referencia,
                    m.nombre AS producto
            FROM    orden_produccion op
            JOIN    mercancia m
                      ON m.id = op.pt_mercancia_id
                     AND m.empresa_id = %s
            WHERE   op.empresa_id = %s
            ORDER BY op.fecha DESC, op.id DESC
        """, (eid, eid))
        ordenes = cur.fetchall()
        return render_template('inventarios/WIP/orden_list.html', ordenes=ordenes)
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

@bp.route("/ordenes/nueva", methods=["GET","POST"])
@require_login
def orden_nueva():
    """Crear nueva orden de producción (aislado por empresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    if request.method == "POST":
        pt_id      = int(request.form["pt_id"])
        cantidad   = float(request.form["cantidad"])
        fecha      = request.form["fecha"]
        referencia = (request.form.get("referencia") or "").strip()

        conn = conexion_db(); cur = conn.cursor(dictionary=True)
        try:
            # Verificar que el PT exista en esta empresa
            cur.execute("""
                SELECT id FROM mercancia
                WHERE id=%s AND empresa_id=%s AND tipo='PT'
            """, (pt_id, eid))
            if not cur.fetchone():
                flash("El producto no pertenece a esta empresa.", "warning")
                return redirect(url_for("wip.orden_nueva"))

            # Verificar proceso activo del mismo tenant
            cur.execute("""
                SELECT id FROM procesos
                WHERE pt_id=%s AND empresa_id=%s AND activo=1
                LIMIT 1
            """, (pt_id, eid))
            proceso = cur.fetchone()
            if not proceso:
                flash("⚠️ Este producto no tiene proceso de producción configurado.", "warning")
                return redirect(url_for("wip.procesos_list"))

            # Crear orden
            cur.execute("""
                INSERT INTO orden_produccion
                    (empresa_id, fecha, pt_mercancia_id, cantidad, estado, referencia)
                VALUES
                    (%s, %s, %s, %s, 'abierta', %s)
            """, (eid, fecha, pt_id, cantidad, referencia))
            orden_id = cur.lastrowid
            conn.commit()

            flash(f"✅ Orden #{orden_id} creada correctamente", "success")
            return redirect(url_for("wip.orden_detalle", orden_id=orden_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("wip.orden_nueva"))
        finally:
            try: cur.close()
            except: pass
            try: conn.close()
            except: pass

    # GET: catálogo de PT del tenant y flag de proceso
    conn = conexion_db(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT  m.id,
                    m.nombre,
                    (
                      SELECT COUNT(*)
                      FROM procesos p
                      WHERE p.pt_id = m.id
                        AND p.empresa_id = %s
                        AND p.activo = 1
                    ) AS tiene_proceso
            FROM mercancia m
            WHERE m.empresa_id = %s
              AND m.tipo = 'PT'
            ORDER BY m.nombre
        """, (eid, eid))
        productos = cur.fetchall()
        return render_template('inventarios/WIP/orden_nueva.html', productos=productos)
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

@bp.get("/ordenes/<int:orden_id>")
@require_login
def orden_detalle(orden_id):
    """Ver detalle de una orden (aislado por empresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    eid = g.empresa_id

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    # 1) Encabezado de la orden (valida pertenencia a la empresa)
    cur.execute("""
        SELECT  op.*,
                m.nombre AS producto
        FROM    orden_produccion op
        JOIN    mercancia m
                  ON m.id = op.pt_mercancia_id
                 AND m.empresa_id = %s
        WHERE   op.id = %s
          AND   op.empresa_id = %s
        """, (eid, orden_id, eid))
    orden = cur.fetchone()
    if not orden:
        cur.close(); conn.close()
        flash("Orden no encontrada", "warning")
        return redirect(url_for("wip.ordenes_list"))

    # 2) Proceso asociado (del mismo PT y empresa)
    cur.execute("""
        SELECT  p.*,
                COUNT(pp.id) AS total_pasos
        FROM    procesos p
        LEFT JOIN proceso_pasos pp
               ON pp.proceso_id = p.id
              AND pp.empresa_id = %s
        WHERE   p.pt_id = %s
          AND   p.empresa_id = %s
          AND   p.activo = 1
        GROUP BY p.id
        LIMIT 1
        """, (eid, orden['pt_mercancia_id'], eid))
    proceso = cur.fetchone()

    # 3) Pasos del proceso (solo si hay proceso y dentro del tenant)
    pasos = []
    if proceso:
        cur.execute("""
            SELECT  pp.*,
                    a.nombre AS area_nombre
            FROM    proceso_pasos pp
            LEFT JOIN areas_produccion a
                   ON a.id = pp.area_id
                  AND a.empresa_id = %s
            WHERE   pp.proceso_id = %s
              AND   pp.empresa_id = %s
            ORDER BY pp.orden
            """, (eid, proceso['id'], eid))
        pasos = cur.fetchall()

    # 4) Movimientos de inventario relacionados a la OP (mismo tenant)
    cur.execute("""
        SELECT  im.*,
                m.nombre AS producto_nombre
        FROM    inventario_movimientos im
        JOIN    mercancia m
                  ON m.id = im.mercancia_id
                 AND m.empresa_id = %s
        WHERE   im.empresa_id = %s
          AND   im.referencia = %s
        ORDER BY im.fecha DESC, im.id DESC
        """, (eid, eid, f"OP{orden_id}"))
    movimientos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'inventarios/WIP/orden_detalle.html',
        orden=orden,
        proceso=proceso,
        pasos=pasos,
        movimientos=movimientos
    )

@bp.route('/ordenes/<int:orden_id>/iniciar', methods=['POST'])
@require_login
def orden_iniciar(orden_id):
    """Iniciar orden de producción (multiempresa)"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    from datetime import date
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    eid = g.empresa_id

    try:
        # 1. Obtener datos de la orden
        cur.execute("""
            SELECT op.*, m.nombre AS producto_nombre, p.id AS proceso_id
            FROM orden_produccion op
            JOIN mercancia m 
                 ON m.id = op.pt_mercancia_id
                AND m.empresa_id = %s
            LEFT JOIN procesos p 
                 ON p.pt_id = op.pt_mercancia_id
                AND p.empresa_id = %s
            WHERE op.id = %s
              AND op.empresa_id = %s
        """, (eid, eid, orden_id, eid))
        orden = cur.fetchone()

        if not orden:
            flash("Orden no encontrada o no pertenece a tu empresa.", "warning")
            return redirect(url_for("wip.ordenes_list"))

        if orden['estado'] == 'cerrada':
            flash("Esta orden ya está cerrada", "info")
            return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

        if not orden['proceso_id']:
            flash("⚠️ Esta orden no tiene proceso asociado.", "warning")
            return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

        # 2. Obtener insumos del proceso (solo de la empresa)
        cur.execute("""
            SELECT 
                pi.mp_id,
                pi.cantidad_por_lote,
                m.nombre AS mp_nombre,
                m.tipo_inventario_id
            FROM proceso_pasos pp
            JOIN paso_insumos pi 
                 ON pi.paso_id = pp.id
            JOIN mercancia m 
                 ON m.id = pi.mp_id
                AND m.empresa_id = %s
            WHERE pp.proceso_id = %s
              AND pp.empresa_id = %s
              AND pi.cantidad_por_lote > 0
        """, (eid, orden['proceso_id'], eid))
        insumos = cur.fetchall()

        if not insumos:
            flash("⚠️ El proceso no tiene insumos definidos.", "warning")
            return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

        # 3. Calcular cantidades
        cantidad_producida = float(orden['cantidad'])
        lote_base = 12.0
        factor = cantidad_producida / lote_base

        errores = []
        movimientos_realizados = 0
        costo_total_produccion = 0

        # 4. Consumir materias primas
        from app import calcular_precio_promedio_periodo

        for insumo in insumos:
            cantidad_a_consumir = float(insumo['cantidad_por_lote']) * factor

            # Calcular stock actual (solo del tenant)
            cur.execute("""
                SELECT 
                    COALESCE(SUM(CASE 
                        WHEN tipo_movimiento IN ('compra','entrada') THEN unidades 
                        ELSE -unidades 
                    END), 0) AS stock_actual
                FROM inventario_movimientos
                WHERE mercancia_id = %s
                  AND empresa_id = %s
            """, (insumo['mp_id'], eid))
            result = cur.fetchone()
            stock_actual = float(result['stock_actual']) if result else 0

            # Calcular precio promedio
            precio_unitario = calcular_precio_promedio_periodo(insumo['mp_id'])

            print(f"\n{'='*60}")
            print(f"🔍 DEBUG COSTEO - MP: {insumo['mp_nombre']} (ID: {insumo['mp_id']})")
            print(f"{'='*60}")
            print(f"Precio: ${precio_unitario:.2f} | Stock: {stock_actual:.2f} | "
                  f"Consumo: {cantidad_a_consumir:.2f} | Total: ${cantidad_a_consumir * precio_unitario:.2f}")
            print("="*60)

            if stock_actual < cantidad_a_consumir:
                errores.append(f"Stock insuficiente de {insumo['mp_nombre']} (necesitas {cantidad_a_consumir:.2f}, hay {stock_actual:.2f})")
                continue

            costo_consumo = cantidad_a_consumir * precio_unitario
            costo_total_produccion += costo_consumo

            # Registrar salida
            cur.execute("""
                INSERT INTO inventario_movimientos
                    (empresa_id, tipo_inventario_id, mercancia_id, fecha,
                     tipo_movimiento, unidades, precio_unitario, referencia)
                VALUES (%s, %s, %s, %s, 'salida', %s, %s, %s)
            """, (eid, insumo['tipo_inventario_id'] or 1, insumo['mp_id'], date.today(),
                  cantidad_a_consumir, precio_unitario, f"Orden #{orden_id} - Inicio producción"))

            # Actualizar inventario_mp (tenant aislado)
            cur.execute("""
                INSERT INTO inventario_mp
                    (empresa_id, mercancia_id, producto, inventario_inicial, entradas, salidas, aprobado)
                VALUES (%s, %s, %s, 0, 0, %s, 1)
                ON DUPLICATE KEY UPDATE salidas = salidas + VALUES(salidas)
            """, (eid, insumo['mp_id'], insumo['mp_nombre'], cantidad_a_consumir))

            movimientos_realizados += 1

        if errores:
            conn.rollback()
            for e in errores:
                flash(f"❌ {e}", "danger")
            return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

        conn.commit()
        flash(f"✅ Orden #{orden_id} iniciada. {movimientos_realizados} insumos consumidos. Costo total: ${costo_total_produccion:,.2f}", "success")
        return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al iniciar orden: {e}", "danger")
        return redirect(url_for("wip.orden_detalle", orden_id=orden_id))
    finally:
        cur.close(); conn.close()

@bp.post("/ordenes/<int:orden_id>/cerrar")
@require_login
def orden_cerrar(orden_id):
    """Cerrar orden de producción (genera PT) — aislado por empresa"""
    if session.get('rol') != 'admin':
        flash('Acceso no autorizado.', 'danger')
        return redirect('/login')

    from datetime import date
    eid = g.empresa_id

    conn = conexion_db()
    cur = conn.cursor(dictionary=True)

    try:
        # 1) Obtener orden y validar pertenencia
        cur.execute("""
            SELECT  op.*,
                    m.nombre AS producto_nombre,
                    m.tipo_inventario_id
            FROM    orden_produccion op
            JOIN    mercancia m
                      ON m.id = op.pt_mercancia_id
                     AND m.empresa_id = %s
            WHERE   op.id = %s
              AND   op.empresa_id = %s
        """, (eid, orden_id, eid))
        orden = cur.fetchone()

        if not orden:
            flash("Orden no encontrada o no pertenece a tu empresa.", "warning")
            return redirect(url_for("wip.ordenes_list"))

        if orden['estado'] == 'cerrada':
            flash("Esta orden ya está cerrada", "info")
            return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

        cantidad_producida = float(orden['cantidad'] or 0)

        # 2) Aumentar inventario de PT (tabla por empresa)
        cur.execute("""
            SELECT id, inventario_inicial, entradas, salidas
            FROM   inventario_pt
            WHERE  empresa_id = %s
              AND  producto_id = %s
        """, (eid, orden['pt_mercancia_id']))
        inv_pt = cur.fetchone()

        if inv_pt:
            cur.execute("""
                UPDATE inventario_pt
                   SET entradas = entradas + %s
                 WHERE id = %s
            """, (cantidad_producida, inv_pt['id']))
        else:
            cur.execute("""
                INSERT INTO inventario_pt
                    (empresa_id, producto_id, inventario_inicial, entradas, salidas, precio_unitario)
                VALUES
                    (%s, %s, 0, %s, 0, 0)
            """, (eid, orden['pt_mercancia_id'], cantidad_producida))

        # 3) Registrar movimiento de entrada al almacén de PT
        cur.execute("""
            INSERT INTO inventario_movimientos
                (empresa_id, tipo_inventario_id, mercancia_id, fecha,
                 tipo_movimiento, unidades, precio_unitario, referencia)
            VALUES
                (%s, %s, %s, %s,
                 'entrada', %s, %s, %s)
        """, (
            eid,
            orden['tipo_inventario_id'] or 3,
            orden['pt_mercancia_id'],
            date.today(),
            cantidad_producida,
            0,  # si tienes costo acumulado, aquí podrías registrar el costo unitario promedio del lote
            f"OP{orden_id} - Producción completada"
        ))

        # 4) Cerrar la orden (misma empresa)
        cur.execute("""
            UPDATE orden_produccion
               SET estado = 'cerrada'
             WHERE id = %s
               AND empresa_id = %s
        """, (orden_id, eid))

        conn.commit()

        flash(f"✅ Orden #{orden_id} cerrada correctamente", "success")
        flash(f"✨ Generadas {cantidad_producida:.0f} unidades de {orden['producto_nombre']}", "success")
        return redirect(url_for("wip.orden_detalle", orden_id=orden_id))

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al cerrar orden: {e}", "danger")
        return redirect(url_for("wip.orden_detalle", orden_id=orden_id))
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass


@bp.route('/centro-incidencias')
def centro_incidencias():
    """Centro de Gestión de Incidencias"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        areas_sistema = [
            {'codigo': 'compras', 'nombre': 'Compras', 'icono': '🛒'},
            {'codigo': 'recepcion', 'nombre': 'Recepción de Mercancía', 'icono': '📦'},
            {'codigo': 'produccion', 'nombre': 'Producción (WIP)', 'icono': '🏭'},
            {'codigo': 'almacen', 'nombre': 'Prod. Terminados', 'icono': '📦'},
            {'codigo': 'reparto', 'nombre': 'Reparto', 'icono': '🚚'},
            {'codigo': 'cobranza', 'nombre': 'Cobranza', 'icono': '💰'},
            {'codigo': 'cuentas_pagar', 'nombre': 'Cuentas por Pagar', 'icono': '💸'},
            {'codigo': 'ventas', 'nombre': 'Ventas y Cortes', 'icono': '🛍️'},
            {'codigo': 'contabilidad', 'nombre': 'Contabilidad', 'icono': '📊'},
            {'codigo': 'mantenimiento', 'nombre': 'Mantenimiento', 'icono': '🔧'}
        ]
        
        dashboard_data = []
        
        for area in areas_sistema:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE 
                        WHEN tiempo_estimado IS NULL OR fecha_inicio IS NULL THEN 1
                        WHEN TIMESTAMPDIFF(MINUTE, fecha_inicio, NOW()) <= tiempo_estimado THEN 1
                        ELSE 0
                    END) as verde,
                    SUM(CASE 
                        WHEN tiempo_estimado IS NOT NULL 
                        AND fecha_inicio IS NOT NULL
                        AND TIMESTAMPDIFF(MINUTE, fecha_inicio, NOW()) > tiempo_estimado
                        AND TIMESTAMPDIFF(MINUTE, fecha_inicio, NOW()) <= (tiempo_estimado * 2) THEN 1
                        ELSE 0
                    END) as amarillo,
                    SUM(CASE 
                        WHEN tiempo_estimado IS NOT NULL 
                        AND fecha_inicio IS NOT NULL
                        AND TIMESTAMPDIFF(MINUTE, fecha_inicio, NOW()) > (tiempo_estimado * 2) THEN 1
                        ELSE 0
                    END) as rojo
                FROM incidencias
                WHERE tipo_tarea = %s
                AND estado IN ('nueva', 'asignada', 'en_analisis', 'en_proceso', 'en_revision')
            """, (area['codigo'],))
            
            resumen = cur.fetchone()
            
            cur.execute("""
                SELECT 
                    t.id,
                    t.codigo,
                    t.titulo,
                    t.estado,
                    t.prioridad,
                    t.severidad,
                    t.fecha_inicio,
                    t.tiempo_estimado,
                    t.fecha_cumplimiento,
                    u.nombre as responsable_nombre,
                    TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) as tiempo_transcurrido,
                    CASE 
                        WHEN t.tiempo_estimado IS NULL OR t.fecha_inicio IS NULL THEN 'gris'
                        WHEN TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) <= t.tiempo_estimado THEN 'verde'
                        WHEN TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) <= (t.tiempo_estimado * 2) THEN 'amarillo'
                        ELSE 'rojo'
                    END as semaforo
                FROM incidencias t
                LEFT JOIN usuarios u ON u.id = t.responsable_id
                WHERE t.tipo_tarea = %s
                AND t.estado IN ('nueva', 'asignada', 'en_analisis', 'en_proceso', 'en_revision')
                ORDER BY 
                    FIELD(t.severidad, 'critica', 'alta', 'media', 'baja'),
                    FIELD(t.prioridad, 'urgente', 'alta', 'normal', 'baja'),
                    t.fecha_cumplimiento ASC
            """, (area['codigo'],))
            
            incidencias = cur.fetchall()
            
            dashboard_data.append({
                'codigo': area['codigo'],
                'nombre': area['nombre'],
                'icono': area['icono'],
                'total': resumen['total'] or 0,
                'verde': resumen['verde'] or 0,
                'amarillo': resumen['amarillo'] or 0,
                'rojo': resumen['rojo'] or 0,
                'incidencias': incidencias
            })
        
        return render_template(
            'supervisor/centro_incidencias.html',
            dashboard_data=dashboard_data
        )
    
    finally:
        cur.close()
        conn.close()


@bp.route('/incidencia/<int:incidencia_id>/detalle')
def incidencia_detalle(incidencia_id):
    """Vista detallada de una incidencia específica"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT 
                t.*,
                u.nombre as responsable_nombre,
                u.correo as responsable_email,
                asignador.nombre as asignador_nombre,
                revisor.nombre as revisor_nombre,
                aprobador.nombre as aprobador_nombre,
                TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) as tiempo_transcurrido,
                CASE 
                    WHEN t.tiempo_estimado IS NULL OR t.fecha_inicio IS NULL THEN 0
                    ELSE (TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) / t.tiempo_estimado) * 100
                END as porcentaje_tiempo
            FROM incidencias t
            LEFT JOIN usuarios u ON u.id = t.responsable_id
            LEFT JOIN usuarios asignador ON asignador.id = t.created_by
            LEFT JOIN usuarios revisor ON revisor.id = t.revisor_id
            LEFT JOIN usuarios aprobador ON aprobador.id = t.aprobador_id
            WHERE t.id = %s
        """, (incidencia_id,))
        
        incidencia = cur.fetchone()
        
        if not incidencia:
            flash('Incidencia no encontrada', 'warning')
            return redirect(url_for('wip.centro_incidencias'))
        
        if incidencia['tiempo_estimado'] and incidencia['tiempo_transcurrido']:
            if incidencia['tiempo_transcurrido'] <= incidencia['tiempo_estimado']:
                semaforo = {'color': 'verde', 'clase': 'success', 'texto': 'EN TIEMPO'}
            elif incidencia['tiempo_transcurrido'] <= (incidencia['tiempo_estimado'] * 2):
                semaforo = {'color': 'amarillo', 'clase': 'warning', 'texto': 'FUERA DE OBJETIVO'}
            else:
                semaforo = {'color': 'rojo', 'clase': 'danger', 'texto': 'CRÍTICO'}
        else:
            semaforo = {'color': 'gris', 'clase': 'secondary', 'texto': 'SIN INICIAR'}
        
        cur.execute("""
            SELECT 
                b.*,
                u.nombre as usuario_nombre
            FROM incidencias_bitacora b
            JOIN usuarios u ON u.id = b.usuario_id
            WHERE b.tarea_id = %s
            ORDER BY b.fecha_accion DESC
        """, (incidencia_id,))
        
        bitacora = cur.fetchall()
        
        return render_template(
            'supervisor/incidencia_detalle.html',
            incidencia=incidencia,
            semaforo=semaforo,
            bitacora=bitacora,
            now=datetime.now()
        )
    
    finally:
        cur.close()
        conn.close()


@bp.route('/notificaciones/pendientes')
def notificaciones_pendientes():
    """Obtiene incidencias pendientes del usuario actual"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 403
    
    usuario_id = session['usuario_id']
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT 
                t.id,
                t.codigo,
                t.titulo,
                t.area_nombre,
                t.prioridad,
                t.severidad,
                t.fecha_cumplimiento,
                t.fecha_inicio,
                t.tiempo_estimado,
                u.nombre as responsable_nombre,
                CASE 
                    WHEN t.tiempo_estimado IS NULL OR t.fecha_inicio IS NULL THEN 'gris'
                    WHEN TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) <= t.tiempo_estimado THEN 'verde'
                    WHEN TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) <= (t.tiempo_estimado * 2) THEN 'amarillo'
                    ELSE 'rojo'
                END as semaforo,
                CASE 
                    WHEN t.fecha_cumplimiento < CURDATE() THEN 1
                    ELSE 0
                END as vencida
            FROM incidencias t
            LEFT JOIN usuarios u ON u.id = t.responsable_id
            WHERE t.responsable_id = %s
            AND t.estado IN ('nueva', 'asignada', 'en_analisis', 'en_proceso', 'en_revision')
            ORDER BY 
                FIELD(t.severidad, 'critica', 'alta', 'media', 'baja'),
                FIELD(t.prioridad, 'urgente', 'alta', 'normal', 'baja'),
                t.fecha_cumplimiento ASC
            LIMIT 10
        """, (usuario_id,))
        
        incidencias = cur.fetchall()
        
        # Formatear fechas
        for inc in incidencias:
            if inc['fecha_cumplimiento']:
                inc['fecha_cumplimiento'] = inc['fecha_cumplimiento'].strftime('%d/%m/%Y')
        
        return jsonify({'incidencias': incidencias})
    
    finally:
        cur.close()
        conn.close()

@bp.route('/centro-alertas')
def centro_alertas():
    """Centro de Alertas del Sistema"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Obtener alertas agrupadas por área
        areas_alertas = [
            {'codigo': 'recepcion_mp', 'nombre': 'Recepción Materia Prima', 'icono': '📦', 'tipos': ['recepcion_mp']},
            {'codigo': 'productos_terminados', 'nombre': 'Productos Terminados', 'icono': '📦', 'tipos': ['entrega_producto', 'recepcion_pt']},
            {'codigo': 'compras', 'nombre': 'Compras', 'icono': '🛒', 'tipos': ['cotizacion_compra', 'aprobacion_compra']},
            {'codigo': 'cuentas_pagar', 'nombre': 'Cuentas por Pagar', 'icono': '💸', 'tipos': ['pago_proveedor']},
            {'codigo': 'cobranza', 'nombre': 'Cobranza', 'icono': '💰', 'tipos': ['cobro_cliente']},
        ]
        
        dashboard_data = []
        
        for area in areas_alertas:
            # Convertir lista de tipos a string para SQL
            tipos_str = "','".join(area['tipos'])
            
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN prioridad = 'urgente' THEN 1 ELSE 0 END) as urgentes,
                    SUM(CASE WHEN prioridad = 'alta' THEN 1 ELSE 0 END) as altas,
                    SUM(CASE WHEN fecha_limite < NOW() THEN 1 ELSE 0 END) as vencidas
                FROM alertas_sistema
                WHERE area_destino = %s
                AND estado IN ('pendiente', 'en_proceso')
            """, (area['codigo'],))
            
            resumen = cur.fetchone()
            
            cur.execute(f"""
                SELECT 
                    a.id,
                    a.codigo,
                    a.tipo_alerta,
                    a.titulo,
                    a.descripcion,
                    a.estado,
                    a.prioridad,
                    a.fecha_creacion,
                    a.fecha_limite,
                    a.referencia_codigo,
                    u.nombre as responsable_nombre,
                    CASE 
                        WHEN a.fecha_limite < NOW() THEN 'vencida'
                        WHEN a.fecha_limite < DATE_ADD(NOW(), INTERVAL 2 HOUR) THEN 'urgente'
                        ELSE 'normal'
                    END as estado_tiempo
                FROM alertas_sistema a
                LEFT JOIN usuarios u ON u.id = a.responsable_id
                WHERE a.area_destino = %s
                AND a.estado IN ('pendiente', 'en_proceso')
                ORDER BY 
                    FIELD(a.prioridad, 'urgente', 'alta', 'normal', 'baja'),
                    a.fecha_limite ASC
            """, (area['codigo'],))
            
            alertas = cur.fetchall()
            
            dashboard_data.append({
                'codigo': area['codigo'],
                'nombre': area['nombre'],
                'icono': area['icono'],
                'total': resumen['total'] or 0,
                'urgentes': resumen['urgentes'] or 0,
                'altas': resumen['altas'] or 0,
                'vencidas': resumen['vencidas'] or 0,
                'alertas': alertas
            })
        
        return render_template(
            'supervisor/centro_alertas.html',
            dashboard_data=dashboard_data
        )
    
    finally:
        cur.close()
        conn.close()


@bp.route('/alerta/<int:alerta_id>/detalle')
def alerta_detalle(alerta_id):
    """Vista detallada de una alerta"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT 
                a.*,
                u.nombre as responsable_nombre,
                u.correo as responsable_email,
                procesador.nombre as procesador_nombre
            FROM alertas_sistema a
            LEFT JOIN usuarios u ON u.id = a.responsable_id
            LEFT JOIN usuarios procesador ON procesador.id = a.procesado_por
            WHERE a.id = %s
        """, (alerta_id,))
        
        alerta = cur.fetchone()
        
        if not alerta:
            flash('Alerta no encontrada', 'warning')
            return redirect(url_for('wip.centro_alertas'))
        
        # Determinar estado visual
        if alerta['fecha_limite'] and alerta['fecha_limite'] < datetime.now():
            estado_visual = {'color': 'rojo', 'clase': 'danger', 'texto': 'VENCIDA'}
        elif alerta['prioridad'] == 'urgente':
            estado_visual = {'color': 'rojo', 'clase': 'danger', 'texto': 'URGENTE'}
        elif alerta['prioridad'] == 'alta':
            estado_visual = {'color': 'amarillo', 'clase': 'warning', 'texto': 'IMPORTANTE'}
        else:
            estado_visual = {'color': 'azul', 'clase': 'info', 'texto': 'NORMAL'}
        
        # Obtener bitácora
        cur.execute("""
            SELECT 
                b.*,
                u.nombre as usuario_nombre
            FROM alertas_bitacora b
            JOIN usuarios u ON u.id = b.usuario_id
            WHERE b.alerta_id = %s
            ORDER BY b.fecha_accion DESC
        """, (alerta_id,))
        
        bitacora = cur.fetchall()
        
        return render_template(
            'supervisor/alerta_detalle.html',
            alerta=alerta,
            estado_visual=estado_visual,
            bitacora=bitacora,
            now=datetime.now()
        )
    
    finally:
        cur.close()
        conn.close()


@bp.route('/alerta/<int:alerta_id>/procesar', methods=['GET', 'POST'])
def procesar_alerta(alerta_id):
    """Procesar una alerta"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'GET':
            # Mostrar formulario de procesamiento
            cur.execute("SELECT * FROM alertas_sistema WHERE id = %s", (alerta_id,))
            alerta = cur.fetchone()
            
            if not alerta:
                flash('Alerta no encontrada', 'warning')
                return redirect(url_for('wip.centro_alertas'))
            
            return render_template('supervisor/procesar_alerta.html', alerta=alerta)
        
        else:  # POST
            accion = request.form.get('accion')
            notas = request.form.get('notas')
            
            if accion == 'completar':
                cur.execute("""
                    UPDATE alertas_sistema 
                    SET estado = 'completada',
                        fecha_completado = NOW(),
                        procesado_por = %s,
                        notas_proceso = %s
                    WHERE id = %s
                """, (session['usuario_id'], notas, alerta_id))
                
                # Registrar en bitácora
                cur.execute("""
                    INSERT INTO alertas_bitacora (alerta_id, usuario_id, accion, comentario)
                    VALUES (%s, %s, 'completada', %s)
                """, (alerta_id, session['usuario_id'], notas))
                
                flash('Alerta completada exitosamente', 'success')
                
            elif accion == 'cancelar':
                cur.execute("""
                    UPDATE alertas_sistema 
                    SET estado = 'cancelada',
                        procesado_por = %s,
                        notas_proceso = %s
                    WHERE id = %s
                """, (session['usuario_id'], notas, alerta_id))
                
                cur.execute("""
                    INSERT INTO alertas_bitacora (alerta_id, usuario_id, accion, comentario)
                    VALUES (%s, %s, 'cancelada', %s)
                """, (alerta_id, session['usuario_id'], notas))
                
                flash('Alerta cancelada', 'info')
            
            conn.commit()
            return redirect(url_for('wip.centro_alertas'))
    
    finally:
        cur.close()
        conn.close()



@bp.route('/tarea/<int:tarea_id>/detalle')
def tarea_detalle(tarea_id):
    """Vista detallada de una tarea específica"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT 
                t.*,
                u.nombre as responsable_nombre,
                u.correo as responsable_email,
                asignador.nombre as asignador_nombre,
                revisor.nombre as revisor_nombre,
                aprobador.nombre as aprobador_nombre,
                TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) as tiempo_transcurrido,
                CASE 
                    WHEN t.tiempo_estimado IS NULL OR t.fecha_inicio IS NULL THEN 0
                    ELSE (TIMESTAMPDIFF(MINUTE, t.fecha_inicio, NOW()) / t.tiempo_estimado) * 100
                END as porcentaje_tiempo
            FROM tareas_sistema t
            LEFT JOIN usuarios u ON u.id = t.responsable_id
            LEFT JOIN usuarios asignador ON asignador.id = t.created_by
            LEFT JOIN usuarios revisor ON revisor.id = t.revisor_id
            LEFT JOIN usuarios aprobador ON aprobador.id = t.aprobador_id
            WHERE t.id = %s
        """, (tarea_id,))
        
        tarea = cur.fetchone()
        
        if not tarea:
            flash('Tarea no encontrada', 'warning')
            return redirect(url_for('wip.dashboard_control_tower'))
        
        if tarea['tiempo_estimado'] and tarea['tiempo_transcurrido']:
            if tarea['tiempo_transcurrido'] <= tarea['tiempo_estimado']:
                semaforo = {'color': 'verde', 'clase': 'success', 'texto': 'EN TIEMPO'}
            elif tarea['tiempo_transcurrido'] <= (tarea['tiempo_estimado'] * 2):
                semaforo = {'color': 'amarillo', 'clase': 'warning', 'texto': 'FUERA DE OBJETIVO'}
            else:
                semaforo = {'color': 'rojo', 'clase': 'danger', 'texto': 'CRÍTICO'}
        else:
            semaforo = {'color': 'gris', 'clase': 'secondary', 'texto': 'SIN INICIAR'}
        
        cur.execute("""
            SELECT 
                b.*,
                u.nombre as usuario_nombre
            FROM tareas_bitacora b
            JOIN usuarios u ON u.id = b.usuario_id
            WHERE b.tarea_id = %s
            ORDER BY b.fecha_accion DESC
        """, (tarea_id,))
        
        bitacora = cur.fetchall()
        
        return render_template(
            'supervisor/tarea_detalle.html',
            tarea=tarea,
            semaforo=semaforo,
            bitacora=bitacora,
            now=datetime.now()
        )
    
    finally:
        cur.close()
        conn.close()


@bp.route('/api/alertas/resumen')
def api_alertas_resumen():
    """API: Obtener resumen de alertas para el badge"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 403
    
    from app import conexion_db
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT COUNT(*) as total
            FROM alertas_sistema
            WHERE estado IN ('pendiente', 'en_proceso')
        """)
        
        result = cur.fetchone()
        total_alertas = result['total'] if result else 0
        
        cur.execute("""
            SELECT 
                a.id,
                a.codigo,
                a.titulo,
                a.tipo_alerta,
                a.prioridad,
                a.fecha_limite,
                a.referencia_codigo,
                CASE 
                    WHEN a.fecha_limite < NOW() THEN 'vencida'
                    WHEN a.prioridad = 'urgente' THEN 'urgente'
                    ELSE 'normal'
                END as estado_visual
            FROM alertas_sistema a
            WHERE a.estado IN ('pendiente', 'en_proceso')
            ORDER BY 
                FIELD(a.prioridad, 'urgente', 'alta', 'normal', 'baja'),
                a.fecha_limite ASC
            LIMIT 5
        """)
        
        alertas = cur.fetchall()
        
        for alerta in alertas:
            if alerta['fecha_limite']:
                alerta['fecha_limite'] = alerta['fecha_limite'].strftime('%d/%m %H:%M')
        
        return jsonify({
            'total': total_alertas,
            'alertas': alertas
        })
    
    finally:
        cur.close()
        conn.close()


@bp.route('/api/incidencias/resumen')
def api_incidencias_resumen():
    """API: Obtener resumen de incidencias para el badge"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 403
    
    from app import conexion_db
    usuario_id = session['usuario_id']
    conn = conexion_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute("""
            SELECT COUNT(*) as total
            FROM incidencias
            WHERE responsable_id = %s
            AND estado IN ('nueva', 'asignada', 'en_analisis', 'en_proceso', 'en_revision')
        """, (usuario_id,))
        
        result = cur.fetchone()
        total_incidencias = result['total'] if result else 0
        
        cur.execute("""
            SELECT 
                t.id,
                t.codigo,
                t.titulo,
                t.prioridad,
                t.severidad,
                t.fecha_cumplimiento,
                CASE 
                    WHEN t.fecha_cumplimiento < CURDATE() THEN 'vencida'
                    WHEN t.severidad = 'critica' THEN 'critica'
                    WHEN t.prioridad = 'urgente' THEN 'urgente'
                    ELSE 'normal'
                END as estado_visual
            FROM incidencias t
            WHERE t.responsable_id = %s
            AND t.estado IN ('nueva', 'asignada', 'en_analisis', 'en_proceso', 'en_revision')
            ORDER BY 
                FIELD(t.severidad, 'critica', 'alta', 'media', 'baja'),
                FIELD(t.prioridad, 'urgente', 'alta', 'normal', 'baja'),
                t.fecha_cumplimiento ASC
            LIMIT 5
        """, (usuario_id,))
        
        incidencias = cur.fetchall()
        
        for inc in incidencias:
            if inc['fecha_cumplimiento']:
                inc['fecha_cumplimiento'] = inc['fecha_cumplimiento'].strftime('%d/%m/%Y')
        
        return jsonify({
            'total': total_incidencias,
            'incidencias': incidencias
        })
    
    finally:
        cur.close()
        conn.close()

