import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from ner_extractor import BirthCertificateExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_extraction():
    sample_text = """
    ESTADOS UNIDOS MEXICANOS
    ACTA DE NACIMIENTO
    
    CRIP: 1234567890
    CURP: MAHI751031HMCRRS07
    
    DATOS DE LA PERSONA REGISTRADA
    NOMBRE: ISRAEL
    PRIMER APELLIDO: MARTINEZ
    SEGUNDO APELLIDO: HERNANDEZ
    FECHA DE NACIMIENTO: 31 DE OCTUBRE DE 1975
    LUGAR DE NACIMIENTO: MEXICO, DISTRITO FEDERAL
    SEXO: HOMBRE
    
    DATOS DE FILIACION
    NOMBRE DEL PADRE: JUAN MARTINEZ PEREZ
    NACIONALIDAD: MEXICANA
    NOMBRE DE LA MADRE: MARIA HERNANDEZ LOPEZ
    NACIONALIDAD: MEXICANA
    
    FECHA DE REGISTRO: 05 DE NOVIEMBRE DE 1975
    NUMERO DE ACTA: 12345
    OFICIALIA: 01
    MUNICIPIO DE REGISTRO: CUAUHTEMOC
    ENTIDAD FEDERATIVA: DISTRITO FEDERAL
    """
    
    print("Iniciando prueba de extracción NER con LLM...")
    extractor = BirthCertificateExtractor()
    data = extractor.extract_entities(sample_text)
    
    print("\n--- DATOS EXTRAÍDOS ---")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_extraction()
