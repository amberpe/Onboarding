import boto3
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import numpy as np

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)
DATABASE_URL = "postgresql://postgres:postgres72861001@sandbox-ia.ccnrq57mco3x.us-east-1.rds.amazonaws.com:5432/clau"
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 1200})
Session = sessionmaker(bind=engine)
session = boto3.Session()
AWS_REGION = session.region_name
MODEL_NAME = "anthropic.claude-3-5-sonnet-20240620-v1:0"
#us.anthropic.claude-3-5-haiku-20241022-v1:0

def determinar_funcion(pregunta):
    system_prompt = """
    Eres un asistente inteligente que determina cuál función debe ejecutarse en base a la consulta del usuario. Las funciones disponibles son:

    1. procesar_tipo2(query: str, diff_file: str, json_file1: str, json_file2: str): Diferencias en una sección específica: Preguntas que mencionan una sección, parte o capítulo del documento (ejemplo: sección 4, 5.3, capítulo específico).
    2. procesar_tipo3(query: str, json_file1: str, json_file2: str): Diferencias en certificaciones técnicas, unidades lógicas o detalles específicos: Preguntas relacionadas con requisitos técnicos, certificaciones (como ISO), arquitectura, especificaciones técnicas o detalles específicos como anexos, formas de pago, características del servicio, plazos, condiciones o cualquier aspecto particular del documento.
    3. process_1(query: str, diff_file: str, json_file1: str, json_file2: str):  Diferencias en todo el documento: Preguntas generales que piden comparar todo el documento sin referirse a partes específicas.
    4. conversacional(query: str): Cuando no se trate de una pregunta o informacion sobre los documentos sino de una conversacion.


    Devuelve el nombre de la función y sus parámetros en formato JSON. Por ejemplo:
    {
        "function": "procesar_tipo2",
        "parameters": {
            "query": "Diferencias en la sección 4",
            "diff_file": "json/diff.json",
            "json_file1": "json/tdr_v4.json",
            "json_file2": "json/tdr_v6.json"
        }
    }

    Solo responde con el JSON correspondiente. NO AÑADAS TEXTO EXTRA.
    """

    user_prompt = f"Selecciona la función correcta para esta pregunta: {pregunta}"
    response = get_answer(user_prompt, system=system_prompt)
    return json.loads(response.strip())

def conversacional(query):
    system_prompt = """
    Eres un bot de chat de atención al cliente para ayudar a los usuarios a gestionar documentos de Términos de Referencia (TDRs) para licitaciones estatales.

    Tu trabajo es ayudar a los usuarios a comparar versiones de dos licitaciones y dar informacion sobre estos contratos.
    Especificamente son de la version 4 y la version 6 de un TDR, la informacion ya la tienes entonces el usuario no debe subir nada solo deberia hacer preguntas sobre estos documentos.
    las funcionalidades que ofreces son:
    1. Diferencias en todo el documento: Preguntas generales que piden comparar todo el documento sin referirse a partes específicas.

    2. Diferencias en una sección específica: Preguntas que mencionan una sección, parte o capítulo del documento (ejemplo: sección 4, 5.3, capítulo específico).

    3. Diferencias en certificaciones técnicas, unidades lógicas o detalles específicos: Preguntas relacionadas con requisitos técnicos, certificaciones (como ISO), arquitectura, especificaciones técnicas o detalles específicos como anexos, formas de pago, características del servicio, plazos, condiciones o cualquier aspecto particular del documento.

    
    Sé útil y breve en tus respuestas.
    Tienes acceso a un conjunto de herramientas, pero solo las usas cuando es necesario.
    Si no tienes suficiente información para usar una herramienta correctamente, hazle preguntas de seguimiento a un usuario para obtener los datos necesarios.
    
    ### Reglas:
    1. Si el mensaje del usuario es un saludo, agradecimiento o conversación general, responde de manera educada y amistosa.
    2. Si necesitas más información del usuario para usar una herramienta, pide los detalles faltantes.


    En cada turno de conversación, comenzarás pensando en tu respuesta.
    Una vez que hayas terminado, escribirás una respuesta para el usuario.
    """
    user_prompt = f""" <usuario>{query}</usuario> """
    response = get_answer(user_prompt, system=system_prompt)
    return response.strip()




def embed_body(chunk_message: str):
    return json.dumps({
        'inputText': chunk_message,
    })
def embed_call(chunk_message: str):
    model_id = "amazon.titan-embed-text-v2:0"
    body = embed_body(chunk_message)

    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=model_id,
        contentType='application/json',
        accept='application/json'
    )
    return json.loads(response['body'].read().decode('utf-8'))
def get_completion(prompt, system=''):
    bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    if system:
        request_body["system"] = system

    response = bedrock.invoke_model(modelId=MODEL_NAME, body=json.dumps(request_body))
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def get_answer(prompt, system=''):
    bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }

    if system:
        request_body["system"] = system

    response = bedrock.invoke_model(modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0", body=json.dumps(request_body))
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def clasificar_pregunta(pregunta):
    system_prompt = """

    Eres un clasificador inteligente que determina la categoría de una pregunta basada en su contenido. Clasifica la pregunta en una de las siguientes categorías:

    1. Diferencias en todo el documento: Preguntas generales que piden comparar todo el documento sin referirse a partes específicas.

    2. Diferencias en una sección específica: Preguntas que mencionan una sección, parte o capítulo del documento (ejemplo: sección 4, 5.3, capítulo específico).

    3. Diferencias en certificaciones técnicas, unidades lógicas o detalles específicos: Preguntas relacionadas con requisitos técnicos, certificaciones (como ISO), arquitectura, especificaciones técnicas o detalles específicos como anexos, formas de pago, características del servicio, plazos, condiciones o cualquier aspecto particular del documento.

    IMPORTANTE: Devuelve únicamente el número de la categoría.

    Ejemplos:
    Pregunta: "¿Cuáles son las diferencias entre las versiones del documento?"  
    Respuesta: 1

    Pregunta: "¿Qué cambios hay en la sección 4 sobre objetivos de contratación?"  
    Respuesta: 2

    Pregunta: "¿Cuáles son las diferencias en los requisitos de certificación de arquitectura?"  
    Respuesta: 3

    """

    user_prompt = f"""Clasifica la siguiente pregunta: <pregunta>{pregunta}</pregunta> """

    response = get_answer(user_prompt, system=system_prompt)
    return response.strip()

def obtener_seccion_ia(pregunta):
    system_prompt = """
    
    Eres un extractor inteligente que identifica números de secciones mencionados en una consulta. Extrae los números de las secciones o divisiones indicados en la consulta y devuélvelos en una lista de enteros.
    Instrucciones:
    
        Analiza el texto de la consulta.
        Busca números de secciones o divisiones mencionados explícitamente en el texto, separados por comas, espacios, o conectores como "y."
        Devuelve únicamente una lista de enteros con los números mencionados. Si no se hace referencia a secciones, devuelve una lista vacía: [].
    
    Ejemplos:
    
    Pregunta: "Diferencias entre la seccion ocho"
    Respuesta: [8]
    
    Pregunta: "Comparacion de la seccion 2.1. y 2.2."
    Respuesta: [2.1., 2.2.]
    
    Pregunta: "Comparacion de la seccion 6.3.1."
    Respuesta: [6.3.1.]
    
    Pregunta: "Dame las secciones 2,3,6"
    Respuesta: [2, 3, 6]
    
    Pregunta: "Analiza las partes 4, 7 y 10"
    Respuesta: [4, 7, 10]
    
    Pregunta: "De acuerdo a las divisiones 1,2,5 y 9"
    Respuesta: [1, 2, 5, 9]
    
    Pregunta: "No menciona ninguna sección específica"
    Respuesta: []
    
    Pregunta: "¿Qué hay en las partes 3 y 8?"
    Respuesta: [3, 8]
        
    IMPORTANTE: RESPETAR EL FORMATO DE RESPUESTA
    Formato de respuesta:
    [<numero extraido>]
    
    """
    user_prompt = f"""Devuelveme los numeros de las secciones de la siguiente pregunta: <pregunta>{pregunta}</pregunta> """

    response = get_answer(user_prompt, system=system_prompt)
    return response.strip()


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)



