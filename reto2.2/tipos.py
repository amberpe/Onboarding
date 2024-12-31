import re
import pandas as pd
import json
from sqlalchemy.sql import text
from ia import get_completion, embed_call, Session
from prepro import procesar

def search_similar_fragments(query_text, top_k, name_table):
    session = Session()
    query_embedding = embed_call(query_text)['embedding']
    embedding_str = "ARRAY[" + ", ".join(map(str, query_embedding)) + "]::vector"

    query = text(f"""
        SELECT 
            id, 
            numero, 
            fragmento, 
            cosine_similarity(embedding, {embedding_str}) AS similarity
        FROM {name_table}
        ORDER BY similarity DESC
        LIMIT :top_k
    """)

    results = session.execute(query, {"top_k": top_k}).fetchall()
    session.close()
    df = pd.DataFrame(results, columns=["id", "numero_seccion", "fragmento", "similarity"])
    return df
def cargar_json(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
def obtener_contenido_por_indices(json_data, indices_relevantes):
    contenidos = []
    for seccion in json_data.get("secciones", []):
        if seccion["numero"] in indices_relevantes:
            contenidos.append(seccion["contenido"])
    return contenidos
def realizar_consulta(query: str, top_k: int, name_table: str, json_file):
    resultados = search_similar_fragments(query, top_k, name_table)
    indices_relevantes = resultados["numero_seccion"].unique().tolist()
    indices_relevantes = [num if num.endswith('.') else num + '.' for num in indices_relevantes]
    print(indices_relevantes)
    json_data = cargar_json(json_file)
    contenido_completo = obtener_contenido_por_indices(json_data, indices_relevantes)
    #print(contenido_completo)
    return contenido_completo, indices_relevantes
def generate_research(search_results, indices_relevantes):
    research = '<search_results>\n'
    for idx, result in zip(indices_relevantes, search_results):
        research += f'    <search_result id="{idx}">\n'
        research += f'        {result}\n'
        research += f'    </search_result>\n'
    research += '</search_results>'
    return research
def procesar_tipo3(question: str, json_file1: str, json_file2: str):
    contenido_completo1, indices_relevantes1 = realizar_consulta(
        question, top_k=3, name_table="tdr_v4_2", json_file=json_file1
    )
    contenido_completo2, indices_relevantes2 = realizar_consulta(
        question, top_k=3, name_table="tdr_v6_2", json_file=json_file2
    )
    research1 = generate_research(contenido_completo1, indices_relevantes1)
    research2 = generate_research(contenido_completo2, indices_relevantes2)

    SYSTEM_PROMPT = """
    Eres un asistente inteligente especializado en ayudar a los usuarios a gestionar documentos de Términos de Referencia (TDRs) para licitaciones estatales. 
    Tu objetivo es facilitar la búsqueda, comparación y análisis de información clave dentro de los TDRs.
    """

    prompt = ""

    prompt += f"""
    Hola, necesito que me ayudes a responder una **pregunta específica** utilizando la información de las secciones que te proporcionaré. Estas secciones pertenecen a **dos versiones distintas** de un mismo documento.


    Por favor, realiza las siguientes tareas:
    1. **Analiza ambas versiones de texto** y extrae las citas más relevantes de la investigación en base a la pregunta.
    2. **Identifica cómo cambia la respuesta a la pregunta entre ambas versiones.**

    **Pregunta específica**: {question}

    **Versión antigua**:
    <bloque>{research1}</bloque>

    **Versión nueva**:
    <bloque>{research2}</bloque>


    Instrucciones:
    - Evita el uso de saltos de línea dobles. Usa un único salto de línea entre párrafos o elementos.
    - Mantén una respuesta clara, DIRECTA y organizada.
    """
    return get_completion(prompt, SYSTEM_PROMPT)

#________________________________________________________-

def reemplazar_numeros_escritos(texto: str) -> str:
    numeros_escritos = {
        "uno": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
        "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"
    }
    for palabra, numero in numeros_escritos.items():
        texto = re.sub(rf'\b{palabra}\b', numero, texto, flags=re.IGNORECASE)
    return texto
def extraer_numero_seccion(pregunta: str):
    texto_limpio = reemplazar_numeros_escritos(pregunta)
    match1 = re.search(r"secci[oó]n\s+(\d+(\.\d+)*)", texto_limpio, re.IGNORECASE)
    match2 = re.search(r"secci[oó]n\s+(\d+(\.\d+)*\.)", texto_limpio, re.IGNORECASE)
    if match1:
        return match1.group(1)
    if match2:
        return match2.group(1)
    return None


#---------------------------------
def extraer_seccion2(json_input, numero_seccion):
    if isinstance(json_input, str):
        with open(json_input, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(json_input, dict):
        data = json_input
    else:
        raise TypeError("El argumento 'json_input' debe ser una ruta de archivo o un diccionario.")

    for seccion in data.get("secciones", []):
        if seccion["numero"] == numero_seccion:
            return seccion["contenido"]

    return None
def procesar_tipo2(query: str, diff_file: str, json_file1: str, json_file2: str):
    num = extraer_numero_seccion(query)
    if not num:
        raise ValueError("No se pudo extraer el número de sección de la consulta proporcionada.")
    if not num.endswith("."):
        num += "."
    diff = obtener_seccion(diff_file,num)

    json_data1 = cargar_json(json_file1)
    json_data2 = cargar_json(json_file2)
    doc1 = extraer_seccion2(json_data1, num)
    doc2 = extraer_seccion2(json_data2, num)

    #print("--------------------------")
    fff = gencomp2(diff, num, doc1, doc2)
    return get_completion(fff)
def obtener_seccion(json_file, numero_seccion):
    data = cargar_json(json_file)
    return data.get(numero_seccion, "Sección no encontrada.")
def gencomp2(retrieved_info, section, doc1, doc2):
    return f"""

        Eres un asistente inteligente especializado en ayudar a los usuarios a gestionar documentos de Términos de Referencia (TDRs) para licitaciones estatales. 
        Tu objetivo es facilitar la búsqueda, comparación y análisis de información clave dentro de los TDRs.
            
        Por favor, realiza las siguientes tareas:
        1. **Analiza las diferencias encontradas en ambas versiones de texto** y extrae las citas más relevantes de la investigación.
        2. **Identifica eliminaciones o adiciones entre ambas versiones. usa la informacion de la tarea anterior y DEBES SER BREVE Y DIRECTO EN TU RESPUESTA**
        
        Tienes que tener encuenta que todo lo que está delante de un '-' representa lo que se ha modificado del primer documento, y todo lo que está delante de un '+' representa lo que se ha modificado del segundo documento.

        El formato del archivo markdown que vas a generar como respuesta que tienes que seguir es el siguiente:
        ### 1. <Análisis de las diferencias encontradas:>
            <Diferencias encontradas>
        ### 2. <Diferencias Principales:>
            <Respuesta en base a la tarea anterior>
        
        Te estoy dando como contexto el contenido de ambos documentos (Documento 1 y Documento 2) y la consulta con el fin de que me des una respuesta más precisa.

        NO TE EXPLAYES MÁS DE LO NECESARIO. 
        Previamente a responder, PIENSA DOS VECES si la respuesta que estás dando a la consulta es la correcta. 

        Instrucciones:
        - Evita el uso de saltos de línea dobles. Usa un único salto de línea entre párrafos o elementos.
        - Mantén una respuesta clara, DIRECTA y organizada.

        NO AÑADAS NINGÚN MENSAJE EXTRA COMO "DESPUES DE ANALIZAR" O "LUEGO DE REVISAR" O "DESPUES DE EXAMINAR" O SIMILARES.

        <Seccion>
        {section}
        </Seccion>

        <Diferencias>
        {retrieved_info}
        </Diferencias>
        
        <Documento 1>{doc1}</Documento 1>
        <Documento 2>{doc2}</Documento 2>
        """

#-------------------------------------
def generar_reporte_desde_diferencias(diferencias: dict) -> str:
    reporte = ""
    print(diferencias.keys())
    for numero_seccion in diferencias.keys():
        diferencia = diferencias[numero_seccion]
        if diferencia != "ambos documentos presentan la misma información":
            reporte += f"### {numero_seccion}\n{diferencia}\n\n"
    return reporte

def process_1(query: str, diff_file: str, json_file1: str, json_file2: str):
    try:
        with open(diff_file, "r", encoding="utf-8") as f:
            diferencias = json.load(f)

        reporte = ""
        for numero_seccion in diferencias.keys():
            diferencia = diferencias[numero_seccion]
            if diferencia != "ambos documentos presentan la misma información":
                reporte += f"\n\n # NUMERO DE SECCION: {numero_seccion} \n\n  "
                num = f" ¿Cuales son las diferencias en la seccion {numero_seccion} ? "
                reporte += procesar_tipo2(num, diff_file, json_file1,json_file2)

        print("------------------------")

        prompt = f"""
        En el Estado Peruano se realizan miles de licitaciones para proyectos y compras, cuyos contratos pasan por largos procesos de revisión y cambios. Tú eres una IA experta en analizar diferencias entre versiones de contratos.

        **Objetivo**:
        Proporciona una respuesta clara y concisa que detalle las diferencias relevantes para cada seccion entre las dos versiones de los documentos. 
        
        **Formato de respuesta**:
        - Genera una respuesta para cada sección en el siguiente formato:
          ```
          ### <número de la sección>
          <resumen de las diferencias o indicación de que son iguales>
          ```
          
        IMPORTANTE ANALIZAR CADA SECCION ṔORQUE TODAS TIENEN DIFERENCIAS
        AÑADIR VIÑETAS 

        **Reporte**:
        {reporte}
        """

        so = get_completion(prompt)
        return so

    except FileNotFoundError:
        return f"No se pudo abrir el archivo {diff_file}. Asegúrate de que exista y esté en la ubicación correcta."


