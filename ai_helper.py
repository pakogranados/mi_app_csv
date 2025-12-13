# ai_helper.py
import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

def extraer_materiales_con_ia(descripcion, mercancia_disponible):
    """
    Usa Claude para extraer materiales y cantidades de una descripción de proceso.
    
    Args:
        descripcion: Texto descriptivo del paso
        mercancia_disponible: Lista de dict con mercancías disponibles [{id, nombre}, ...]
    
    Returns:
        Lista de dict con materiales detectados: [{mercancia_id, cantidad, unidad, confianza}, ...]
    """
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Preparar lista de mercancías para el contexto
    lista_mercancia = "\n".join([f"- ID {m['id']}: {m['nombre']}" for m in mercancia_disponible])
    
    prompt = f"""Eres un asistente experto en análisis de recetas de producción. 

Tu tarea es extraer los materiales e ingredientes mencionados en la siguiente descripción de proceso, junto con sus cantidades.

MERCANCÍAS DISPONIBLES EN INVENTARIO:
{lista_mercancia}

DESCRIPCIÓN DEL PROCESO:
{descripcion}

INSTRUCCIONES:
1. Identifica TODOS los materiales/ingredientes mencionados
2. Extrae la cantidad numérica de cada uno
3. Identifica la unidad de medida (gramos, kg, ml, litros, unidades, etc)
4. Haz "matching" con las mercancías disponibles (usa el ID más apropiado)
5. Si un material NO está en la lista, usa mercancia_id: null
6. Asigna nivel de confianza: "alta", "media", "baja"

FORMATO DE RESPUESTA (JSON estricto, sin markdown):
{{
  "materiales": [
    {{
      "mercancia_id": 45,
      "nombre_detectado": "azúcar",
      "cantidad": 500,
      "unidad": "gramos",
      "confianza": "alta"
    }}
  ]
}}

Responde SOLO con el JSON, sin explicaciones adicionales."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extraer el contenido de texto
        respuesta = message.content[0].text
        
        # Parsear JSON
        resultado = json.loads(respuesta)
        
        return resultado.get('materiales', [])
        
    except json.JSONDecodeError as e:
        print(f"Error al parsear JSON de Claude: {e}")
        print(f"Respuesta recibida: {respuesta}")
        return []
    except Exception as e:
        print(f"Error al consultar Claude API: {e}")
        return []


def validar_materiales(materiales_ia, mercancia_bd):
    """
    Valida y enriquece los materiales detectados por IA con info de BD.
    
    Args:
        materiales_ia: Lista de materiales detectados por IA
        mercancia_bd: Lista completa de mercancías de BD
    
    Returns:
        Lista validada con info adicional
    """
    resultado = []
    
    # Crear dict para lookup rápido
    mercancia_dict = {m['id']: m for m in mercancia_bd}
    
    for mat in materiales_ia:
        merc_id = mat.get('mercancia_id')
        
        if merc_id and merc_id in mercancia_dict:
            merc = mercancia_dict[merc_id]
            resultado.append({
                'mercancia_id': merc_id,
                'nombre': merc['nombre'],
                'nombre_detectado': mat.get('nombre_detectado', ''),
                'cantidad': mat.get('cantidad', 0),
                'unidad': mat.get('unidad', ''),
                'confianza': mat.get('confianza', 'baja'),
                'encontrado': True
            })
        else:
            # Material no encontrado en BD
            resultado.append({
                'mercancia_id': None,
                'nombre': mat.get('nombre_detectado', 'Desconocido'),
                'nombre_detectado': mat.get('nombre_detectado', ''),
                'cantidad': mat.get('cantidad', 0),
                'unidad': mat.get('unidad', ''),
                'confianza': mat.get('confianza', 'baja'),
                'encontrado': False
            })
    
    return resultado