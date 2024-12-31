from sqlalchemy import create_engine, Column, Integer, Text, inspect
from pgvector.sqlalchemy import Vector
import re
from langchain.chains import LLMChain
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, Text
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from typing import Dict, List
from ia import embed_call
import unicodedata
from difflib import SequenceMatcher, unified_diff


def detectar_y_dividir_secciones(texto: str) -> List[Dict[str, str]]:
    patron_principal = r'(?m)^\*\*(\d+(\.\d+)*\.)\s*(.+)$'
    matches = list(re.finditer(patron_principal, texto))

    secciones = []
    for i, match in enumerate(matches):
        numero = match.group(1).strip()
        titulo = f"El título de esta sección es: {match.group(3).strip()}"

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        contenido = limpiar_texto(texto[start:end])
        contenido_limpio = re.sub(patron_principal, '', contenido).strip()

        secciones.append({
            "numero": numero,
            "titulo": titulo,
            "contenido": contenido_limpio
        })
    return secciones
def exportar_a_json(secciones: List[Dict[str, str]], output_file: str) -> None:
    estructura = {
        "secciones": secciones
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(estructura, f, indent=4, ensure_ascii=False)
    print(f"El archivo JSON se ha guardado en '{output_file}'.")
def dividir_en_fragmentos(secciones: List[Dict[str, str]], max_chars: int = 100) -> List[Dict[str, str]]:
    fragmentos = []
    for seccion in secciones:
        numero = seccion["numero"]
        titulo = seccion["titulo"]
        contenido = seccion["contenido"]

        while contenido:
            if len(contenido) <= max_chars:
                fragmento = contenido
                contenido = ""
            else:
                corte = contenido[:max_chars].rfind(' ')
                if corte == -1:
                    corte = max_chars
                fragmento = contenido[:corte]
                contenido = contenido[corte:].strip()

            fragmentos.append({
                "numero": numero,
                "titulo": titulo,
                "fragmento": limpiar_texto(fragmento)
            })
    return fragmentos
def limpiar_texto(texto: str) -> str:
    return re.sub(r'\s+', ' ', texto).strip()
def almacenar_fragmentos(fragmentos: List[Dict[str, str]], tabla: str, database_url: str):
    engine = create_engine(database_url)
    metadata = MetaData()
    inspector = inspect(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    if not inspector.has_table(tabla):
        Table(
            tabla,
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('numero', String, nullable=False),
            Column('titulo', Text, nullable=False),
            Column('fragmento', Text, nullable=False),
            Column('embedding', Vector(1024), nullable=False)
        )
        metadata.create_all(engine)

    insert_query = text(f"""
        INSERT INTO {tabla} (numero, titulo, fragmento, embedding) 
        VALUES (:numero, :titulo, :fragmento, :embedding)
    """)
    for fragmento in fragmentos:
        embedding = embed_call(fragmento["fragmento"])['embedding']
        session.execute(
            insert_query,
            {
                "numero": fragmento["numero"],
                "titulo": fragmento["titulo"],
                "fragmento": fragmento["fragmento"],
                "embedding": embedding
            }
        )
    session.commit()
    session.close()
    print(f"Fragmentos almacenados exitosamente en la tabla '{tabla}'.")

def procesar_documento_y_almacenar(texto: str, tabla: str, database_url: str, max_chars: int = 100):
    output_file = f"{tabla}.json"
    secciones = detectar_y_dividir_secciones(texto)
    exportar_a_json(secciones, output_file)
    fragmentos = dividir_en_fragmentos(secciones, max_chars=max_chars)
    almacenar_fragmentos(fragmentos, tabla, database_url)


def procesar(parrafo1: str, parrafo2: str):
    from tipos import cargar_json
    def normalizar_texto(texto):
        texto = " ".join(texto.split())
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
        return texto.strip().lower()

    texto1_normalizado = normalizar_texto(parrafo1)
    texto2_normalizado = normalizar_texto(parrafo2)


    if texto1_normalizado == texto2_normalizado:
        return "ambos documentos presentan la misma información"

    diff_ratio = SequenceMatcher(None, parrafo1.strip(), parrafo2.strip()).ratio()
    if diff_ratio < 1:
        parrafo1 = parrafo1.replace("\\n", "\n")
        parrafo2 = parrafo2.replace("\\n", "\n")
        parrafo1 = "\n".join(line.strip() for line in parrafo1.splitlines())
        parrafo2 = "\n".join(line.strip() for line in parrafo2.splitlines())
        diff = list(unified_diff(parrafo1.splitlines(), parrafo2.splitlines(), lineterm=""))

        diff = [line for line in diff if not line.startswith(("-", "+")) or len(line.strip()) > 2]

        if not diff:
            return "ambos documentos presentan la misma información"

        return "\n".join(diff)

    return "ambos documentos presentan la misma información"

def save_diff(json_file1: str, json_file2: str, output_file: str):
    data_v4 = cargar_json(json_file1)
    data_v6 = cargar_json(json_file2)

    dicc_dif = {}
    secciones_v4 = {seccion["numero"]: seccion["contenido"] for seccion in data_v4.get("secciones", [])}
    secciones_v6 = {seccion["numero"]: seccion["contenido"] for seccion in data_v6.get("secciones", [])}

    secc = sorted(set(secciones_v4.keys()).union(secciones_v6.keys()))

    for numero_seccion in secc:
        contenido_v4 = secciones_v4.get(numero_seccion, "No se encontró esta sección en el Documento 1.")
        contenido_v6 = secciones_v6.get(numero_seccion, "No se encontró esta sección en el Documento 2.")
        diferencias = procesar(contenido_v4, contenido_v6) if contenido_v4 != contenido_v6 else "ambos documentos presentan la misma información"
        dicc_dif[numero_seccion] = diferencias

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dicc_dif, f, indent=4, ensure_ascii=False)

