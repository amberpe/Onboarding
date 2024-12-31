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
MODEL_NAME = "anthropic.claude-3-haiku-20240307-v1:0"

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
def clasificar_pregunta(pregunta):
    system_prompt = """

    Eres un clasificador inteligente que determina la categoría de una pregunta basada en su contenido. Clasifica la pregunta en una de las siguientes categorías:

    1. Diferencias en todo el documento: Preguntas generales que piden comparar todo el documento sin referirse a partes específicas.

    2. Diferencias en una sección específica: Preguntas que mencionan una sección, parte o capítulo del documento (ejemplo: sección 4, 5.3, capítulo específico).

    3. Diferencias en certificaciones técnicas o unidades lógicas: Preguntas relacionadas con requisitos técnicos, certificaciones (como ISO), arquitectura o especificaciones técnicas.

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

    response = get_completion(user_prompt, system=system_prompt)
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

