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


def search_similar_fragments(query_text, top_k=8):
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
    return pd.DataFrame(results, columns=["id", "numero_seccion", "fragmento", "similarity"])


llm = BedrockLLM(model_id="amazon.titan-tg1-large")
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""Eres un bot de ayuda asi que saludame y respondeme amigablemente 
    Usando el siguiente contexto como referencia, responde a la pregunta de manera detallada, explicativa y bien elaborada. Si es necesario, organiza la información para que sea fácil de entender.

    1. Respuesta directa:
    2. Explicación detallada:
    3. Conclusión:

    Contexto:
    {context}

    Pregunta:
    {question}

    Respuesta:
    """
)
chain = LLMChain(llm=llm, prompt=prompt_template)


def realizar_consulta(query, top_k=5):
    resultados = search_similar_fragments(query, top_k)
    ojito = [f"Fragmento {idx + 1}: {resul['numero_seccion']} - {resul['fragmento']}" for idx, resul in resultados.iterrows()]
    context = "\n".join(ojito)
    response = chain.run(context=context, question=query)
    print("Respuesta generada:", response)


if __name__ == "__main__":
    query = input()
    realizar_consulta(query, top_k=5)
