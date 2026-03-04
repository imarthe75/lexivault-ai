# ner_extractor.py

import logging
import json
import os
from llm_client import get_ollama_generation

class BirthCertificateExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_name = os.getenv("OLLAMA_GENERATION_MODEL", "mistral")

    def extract_entities(self, text: str) -> dict:
        """
        Extrae entidades de un acta de nacimiento mexicana usando un LLM (Ollama/Mistral).
        Solicita una respuesta en formato JSON estricto.
        """
        prompt = f"""
        Actúa como un experto en extracción de datos de documentos oficiales mexicanos (Actas de Nacimiento).
        Analiza el siguiente texto extraído (OCR) de un Acta de Nacimiento.
        
        ADVERTENCIA: El texto proviene de un OCR de baja calidad. Puede estar fragmentado, desordenado y contener caracteres basura.
        Tu objetivo es reconstruir la información lógica buscando patrones y palabras clave.

        TEXTO DEL ACTA:
        \"\"\"
        {text}
        \"\"\"
        
        ESTRATEGIAS DE EXTRACCIÓN:
        1. **Nombres**: Busca cerca de la etiqueta "Nombre(s):" o "Registrado". Si ves "VIOLETA" cerca de "Nombre(s):", ese es el nombre.
        2. **Apellidos**: Busca "Primer Apellido:" y "Segundo Apellido:". Si no están claros, busca palabras en mayúsculas cerca del nombre que parezcan apellidos (ej. "MARTINEZ", "DE LA ROSA").
        3. **Padres**: La sección de padres suele estar bajo "Datos de Filiación". Busca nombres completos asociados a "PADRE" o "MADRE". Si ves "ISRAEL MARTINEZ" y "MARIA INES", son probables padres.
        4. **Ignorar**: NO confundas al "Director General" o "Oficial" (ej. Cesar Enrique Sanchez) con el padre.
        5. **Fechas**: Busca patrones de fecha (DD/MM/AAAA).
        6. **Nacionalidad**: Si ves "MEXICANA" cerca de un nombre de padre/madre, asígnalo.

        EJEMPLO "ONE-SHOT" (APRENDE DE ESTO):
        Si el texto OCR es:
        "VIOLETA.
        Nombre(s):
        MUJER
        ...
        ISRAEL MARTINEZ
        Primer Apellido:
        DE LA ROSA
        Segundo Apellido:
        ...
        Datos de Filiación
        ISRAEL MARTINEZ
        PADRE
        MARIA INES
        MADRE"

        TU SALIDA JSON DEBE SER:
        {{
            "nombres": "VIOLETA",
            "primer_apellido": "MARTINEZ",
            "segundo_apellido": "DE LA ROSA",
            "sexo": "MUJER",
            "padres": [
                {{"nombre_completo": "ISRAEL MARTINEZ", "nacionalidad": null, "parentesco": "PADRE"}},
                {{"nombre_completo": "MARIA INES", "nacionalidad": null, "parentesco": "MADRE"}}
            ]
        }}
        
        CAMPOS REQUERIDOS (JSON):
        - nombres: (String) Solo el nombre de pila (ej. "VIOLETA"). NO incluyas apellidos ni nombres de padres.
        - primer_apellido: (String)
        - segundo_apellido: (String)
        - fecha_nacimiento: (String, YYYY-MM-DD)
        - lugar_nacimiento: (String)
        - sexo: (String, HOMBRE/MUJER)
        - curp: (String, 18 chars)
        - crip: (String)
        - padres: (Lista de objetos: {{"nombre_completo": "...", "nacionalidad": "...", "parentesco": "PADRE/MADRE"}})
        - fecha_registro: (String, YYYY-MM-DD)
        - numero_acta: (String)
        - municipio_registro: (String)
        - entidad_registro: (String)

        RESPUESTA JSON:
        """

        try:
            self.logger.info(f"Enviando solicitud a Ollama ({self.model_name}) para extracción NER...")
            response_json_str = get_ollama_generation(prompt, self.model_name, json_mode=True)
            
            # Limpiar posibles bloques de código markdown ```json ... ```
            if "```json" in response_json_str:
                response_json_str = response_json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in response_json_str:
                response_json_str = response_json_str.split("```")[1].split("```")[0].strip()

            extracted_data = json.loads(response_json_str)
            self.logger.info("Extracción NER con LLM completada exitosamente.")

            # Post-procesamiento heurístico para corregir nombres/apellidos cuando el LLM
            # incluye apellidos en el campo `nombres` debido a OCR o ambigüedad.
            def _norm(s):
                return s.strip() if isinstance(s, str) else ''

            nombres = _norm(extracted_data.get('nombres', ''))
            primer_ap = _norm(extracted_data.get('primer_apellido', ''))
            segundo_ap = _norm(extracted_data.get('segundo_apellido', ''))

            # Si `nombres` contiene varias palabras y `primer_apellido` está vacío
            # o parece contener parte del nombre, intentar re-segmentar.
            if nombres:
                tokens = [t for t in nombres.split() if t]
                if len(tokens) >= 2 and (not primer_ap or primer_ap.lower() in [t.lower() for t in tokens]):
                    # Heurística simple: asumir primer token(s) como nombre(s),
                    # segundo token como primer apellido, resto como segundo apellido.
                    # Manejar partículas de apellido comunes (DE, DEL, DE LA, VAN, VON).
                    particles = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'DELA', 'DE', 'VON', 'VAN', 'MC', 'MAC'}

                    # Busca si hay una secuencia de partículas que formen un apellido compuesto
                    # Recorremos tokens y asignamos: nombres = first token, primer_ap = second, segundo_ap = rest
                    new_nombres = tokens[0]
                    new_primer = tokens[1]
                    rest = tokens[2:]

                    # Si el rest empieza con partícula como DE + LA etc, mantenla junto al segundo apellido
                    if rest:
                        # unir restos respetando partículas (ej. DE LA ROSA)
                        new_segundo = []
                        i = 0
                        while i < len(rest):
                            tok = rest[i]
                            # if token is a particle and there's a following token, join with following
                            if tok.upper() in particles and i + 1 < len(rest):
                                # include particle and next token
                                new_segundo.append(tok)
                                i += 1
                                new_segundo.append(rest[i])
                            else:
                                new_segundo.append(tok)
                            i += 1
                        new_segundo = ' '.join(new_segundo)
                    else:
                        new_segundo = segundo_ap

                    # Update extracted_data only if it looks reasonable (avoid clobbering good results)
                    # Condición: primer_ap estaba vacío o igual al segundo token
                    extracted_data['nombres'] = new_nombres
                    extracted_data['primer_apellido'] = new_primer
                    if new_segundo:
                        extracted_data['segundo_apellido'] = new_segundo

                    self.logger.debug(f"Re-parsed name: nombres={new_nombres}, primer_apellido={new_primer}, segundo_apellido={new_segundo}")

            # Devolver JSON post-procesado
            return extracted_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Error al decodificar JSON de la respuesta del LLM: {e}. Respuesta: {response_json_str}")
            return {}
        except Exception as e:
            self.logger.error(f"Error durante la extracción con LLM: {e}")
            return {}