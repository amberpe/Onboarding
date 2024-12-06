import boto3
import pandas as pd
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from langchain_aws import BedrockLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

DATABASE_URL = "postgresql://postgres:postgres72861001@sandbox-ia.ccnrq57mco3x.us-east-1.rds.amazonaws.com:5432/clau"
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 1200})
Session = sessionmaker(bind=engine)

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


def search_similar_fragments(query_text, top_k=10):
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
    filtered_df = df[df["similarity"] >= 0.55]
    return filtered_df


llm = BedrockLLM(model_id="amazon.titan-tg1-large")
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""Eres un bot experto en servicios de infraestructura en la nube. Responde de forma amigable y clara.
    Usa los fragmentos proporcionados como contexto para responder la pregunta. Elimina redundancias y organiza la información para que sea clara y completa.

    Formato:
    1. Respuesta directa: Un resumen conciso y claro.
    2. Explicación detallada: Una descripción elaborada basada en el contexto.
    3. Conclusión: Una síntesis final relevante.

    Contexto:
    {context}

    Pregunta:
    {question}

    Respuesta:
    """
)


def eliminar_overlap(fragmentos, overlap=20):
    resultado = []
    for fragmento in fragmentos:
        if resultado and fragmento.startswith(resultado[-1][-overlap:]):
            fragmento = fragmento[len(resultado[-1][-overlap:]):]
        resultado.append(fragmento.strip())
    return resultado

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
    return df

chain = LLMChain(llm=llm, prompt=prompt_template)


def realizar_consulta(query, top_k=10):
    resultados = search_similar_fragments(query, top_k)
    resultados = resultados.drop_duplicates(subset="fragmento", keep="first")
    indices_relevantes = resultados["numero_seccion"].unique().tolist()
    contenido_completo = obtener_contenido_completo(indices_relevantes)
    fragmentos_sin_overlap = eliminar_overlap(contenido_completo["contenido"].tolist())
    context = " ".join(fragmentos_sin_overlap)
    response = chain.run(context=context, question=query)
    print("Respuesta generada:\n\n", response)


if __name__ == "__main__":
    query = "¿Que certificaciones necesitan los desarrolladores?"
    realizar_consulta(query, top_k=10)
