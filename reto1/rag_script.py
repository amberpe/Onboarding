import boto3
import pandas as pd
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text


DATABASE_URL = "postgresql://postgres:postgres72861001@sandbox-ia.ccnrq57mco3x.us-east-1.rds.amazonaws.com:5432/clau"
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 1200})
Session = sessionmaker(bind=engine)

session = boto3.Session()
AWS_REGION = session.region_name
MODEL_NAME = "anthropic.claude-3-haiku-20240307-v1:0"



def get_completion(prompt, system=''):
    bedrock = boto3.client(service_name='bedrock-runtime', region_name=AWS_REGION)

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0
    }

    if system:
        request_body["system"] = system

    response = bedrock.invoke_model(modelId=MODEL_NAME, body=json.dumps(request_body))
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)
def embed_call(chunk_message):
    body = json.dumps({'inputText': chunk_message})
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId="amazon.titan-embed-text-v2:0",
        contentType='application/json',
        accept='application/json'
    )
    return json.loads(response['body'].read().decode('utf-8'))
def search_similar_fragments(query_text, top_k):
    session = Session()
    query_embedding = embed_call(query_text)['embedding']
    embedding_str = "ARRAY[" + ", ".join(map(str, query_embedding)) + "]::vector"

    query = text(f"""
        SELECT 
            id, 
            numero_seccion, 
            fragmento, 
            cosine_similarity(embedding, {embedding_str}) AS similarity
        FROM secciones
        ORDER BY similarity DESC
        LIMIT :top_k
    """)

    results = session.execute(query, {"top_k": top_k}).fetchall()
    session.close()
    df = pd.DataFrame(results, columns=["id", "numero_seccion", "fragmento", "similarity"])
    return df
def obtener_contenido_completo(indices):
    session = Session()
    query = text("""
        SELECT numero_seccion, fragmento
        FROM secciones
        WHERE numero_seccion = ANY(:indices)
        ORDER BY numero_seccion ASC
    """)
    results = session.execute(query, {"indices": indices}).fetchall()
    session.close()

    df = pd.DataFrame(results, columns=["numero_seccion", "contenido"])

    contenido_agrupado = (
        df.groupby("numero_seccion")["contenido"]
        .apply(lambda fragments: " ".join(fragments))
        .tolist()
    )
    return contenido_agrupado



def realizar_consulta(query, top_k):
    resultados = search_similar_fragments(query, top_k)
    resultados = resultados.drop_duplicates(subset="fragmento", keep="first")
    indices_relevantes = resultados["numero_seccion"].unique().tolist()
    contenido_completo = obtener_contenido_completo(indices_relevantes)
    return contenido_completo

def generate_research(search_results):
    research = '<search_results>\n'
    for i, result in enumerate(search_results, start=1):
        research += f'    <search_result id={i}>\n'
        research += f'    {result}\n'
        research += f'    </search_result>\n'
    research += '</search_results>'
    return research


if __name__ == "__main__":
    QUESTION = "¿Qué motores de base de datos debe permitir el servicio?"

    research = realizar_consulta(QUESTION, top_k=3)
    NEW_RESEARCH = generate_research(research)

    SYSTEM_PROMPT = "Eres un asistente inteligente especializado en ayudar a los usuarios a gestionar documentos de Términos de Referencia (TDRs) para licitaciones estatales. Tu objetivo es facilitar la búsqueda y comparación de información clave dentro de los TDRs"
    TONE_CONTEXT = "Debes mantener un tono amigable de servicio al cliente.."
    INPUT_DATA = f"""A continuación se muestra una investigación que se ha recopilado. Úsela para responder una pregunta del usuario..
    <investigación>
    {NEW_RESEARCH}
    </investigación>"""

    EXAMPLES = """Al citar la investigación en su respuesta, utilice corchetes que contengan el ID del índice de búsqueda, seguido de un punto. Colóquelos al final de la oración que está citando. Ejemplos de formato de citación adecuado:
    <examples>
    <example>
    El plazo de prescripción caduca después de 10 años para delitos como este. [3].
    </example>
    <example>
    Sin embargo, la protección no se aplica cuando ambas partes han renunciado específicamente a ella. [5].
    </example>
    </examples>"""

    TASK_DESCRIPTION = f"""Escriba una respuesta clara y concisa a esta pregunta:
    <question>
    {QUESTION}
    </question>
    No debe tener más de un par de párrafos. Si es posible, debe concluir con una sola oración que responda directamente a la pregunta del usuario. Sin embargo, si no hay suficiente información en la investigación recopilada para producir dicha respuesta, puede dudar y escribir "Lo siento, no tengo suficiente información a mano para responder a esta pregunta"."""

    PRECOGNITION = "Antes de responder, extraiga las citas más relevantes de la investigación en base a la pregunta en las etiquetas <relevant_quotes>."
    OUTPUT_FORMATTING = "Coloque su respuesta de dos párrafos en las etiquetas <respuesta>."
    PREFILL = "<citas_relevantes>"

    PROMPT = ""


    if TONE_CONTEXT:
        PROMPT += f"""\n\n{TONE_CONTEXT}"""
    if INPUT_DATA:
        PROMPT += f"""\n\n{INPUT_DATA}"""
    if EXAMPLES:
        PROMPT += f"""\n\n{EXAMPLES}"""
    if TASK_DESCRIPTION:
        PROMPT += f"""\n\n{TASK_DESCRIPTION}"""
    if PRECOGNITION:
        PROMPT += f"""\n\n{PRECOGNITION}"""
    if OUTPUT_FORMATTING:
        PROMPT += f"""\n\n{OUTPUT_FORMATTING}"""


    print(get_completion(PROMPT, SYSTEM_PROMPT))



