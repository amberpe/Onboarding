from tipos import procesar_tipo2,procesar_tipo3, process_1
from ia import clasificar_pregunta, get_completion, optimizar_query


def main():
    doc1 = "tdr_v4"
    doc2 = "tdr_v6"

    #texto1 = pymupdf4llm.to_markdown(f"{doc1}.pdf")
    #texto2 = pymupdf4llm.to_markdown(f"{doc2}.pdf")
    #procesar_documento_y_almacenar(texto1, "doc1", DATABASE_URL)
    #procesar_documento_y_almacenar(texto2, "doc2", DATABASE_URL)
    #save_diff(json1, json2, "json/diff.json")

    #QUESTION = """ ¿Cuales son las diferencias de certificaciones entre ambos documentos ? """
    QUESTION = """ ¿Cuales son las diferencias en todo el documento? """
    #QUESTION = """ ¿Cuales son las diferencias en la seccion 5. ? """


    #QUESTION = optimizar_query(QUESTION)
    first_answer = clasificar_pregunta(QUESTION)
    print(first_answer)
    json1 = f"json/{doc1}.json"
    json2 = f"json/{doc2}.json"

    result = ""
    if first_answer == '2':
        result = procesar_tipo2(QUESTION, "json/diff.json", json1, json2)
    elif first_answer == '3':
        result = procesar_tipo3(QUESTION, json1, json2)
    else:
        result = process_1(QUESTION, "json/diff.json", json1, json2)


    print(result)






if __name__ == '__main__':
    main()