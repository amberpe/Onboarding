from tipos import procesar_tipo3, process_1, procesar_tipov2
from ia import *


tols = [
{
    "name": "procesar_tipo1",
    "description": "Función que se encarga de comparar todo el documento sin referirse a partes específicas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta general sobre las diferencias en todo el documento."
            },
            "diff_file": {
                "name": "json/diff.json",
                "type": "string",
                "description": "Archivo JSON que contiene las diferencias entre los documentos."
            },
            "json_file1": {
                "name": "json/tdr_v4.json",
                "type": "string",
                "description": "Ruta del archivo JSON que representa el primer documento."
            },
            "json_file2": {
                "name": "json/tdr_v6.json",
                "type": "string",
                "description": "Ruta del archivo JSON que representa el segundo documento."
            }
        },
        "required": ["query", "diff_file", "json_file1", "json_file2"]
    }
}, {
    "name": "procesar_tipo2",
    "description": "Función que procesa diferencias en una sección, parte o capítulo del documento (ejemplo: sección 4, 5.3, capítulo específico).",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta específica sobre una sección del documento."
            },
            "diff_file": {
                "name": "json/diff.json",
                "type": "string",
                "description": "Archivo JSON que contiene las diferencias entre los documentos."
            },
            "json_file1": {
                "name": "json/tdr_v4.json",
                "type": "string",
                "description": "Ruta del archivo JSON que representa el primer documento."
            },
            "json_file2": {
                "name": "json/tdr_v6.json",
                "type": "string",
                "description": "Ruta del archivo JSON que representa el segundo documento."
            }
        },
        "required": ["query", "diff_file", "json_file1", "json_file2"]
    }
}, {
    "name": "procesar_tipo3",
    "description": "Función que procesa diferencias en certificaciones técnicas, unidades lógicas o detalles específicos: Preguntas relacionadas con requisitos técnicos, certificaciones (como ISO), arquitectura, especificaciones técnicas o detalles específicos como anexos, formas de pago, características del servicio, plazos, condiciones o cualquier aspecto particular del documento",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Consulta que compara múltiples secciones de los documentos."
            },
            "diff_file": {
                "name": "json/diff.json",
                "type": "string",
                "description": "Archivo JSON que contiene las diferencias entre los documentos."
            },
            "json_file1": {
                "name": "json/tdr_v4.json",
                "type": "string",
                "description": "Ruta del archivo JSON que representa el primer documento."
            },
            "json_file2": {
                "name": "json/tdr_v6.json",
                "type": "string",
                "description": "Ruta del archivo JSON que representa el segundo documento."
            }
        },
        "required": ["query", "json_file1", "json_file2"]
    }
}
]

def process_tool_call(tool_name, parametros):
    if tool_name == "procesar_tipo2":
        return procesar_tipov2(**parametros)
    elif tool_name == "procesar_tipo3":
        return procesar_tipo3(**parametros)
    elif tool_name == "procesar_tipo1":
        return process_1(**parametros)
    elif tool_name == "conversacional":
        return conversacional(**parametros)
    else:
        return f"Tool '{tool_name}' is not recognized."

def function_calling(prompt):
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "tools": tols
    }
    response = bedrock_runtime.invoke_model(
        modelId=MODEL_NAME,
        body=json.dumps(request_body),
        contentType="application/json"
    )
    response_body = json.loads(response['body'].read())
    response = response_body['content']
    if response[-1].get("type") == "tool_use":
        tool_use = response[-1]
        tool_name = tool_use["name"]
        tool_input = tool_use["input"]
        print(f"Claude wants to use the {tool_name} tool")
        tool_input["query"]=prompt
        tool_result = process_tool_call(tool_name, tool_input)
        print(tool_result)
