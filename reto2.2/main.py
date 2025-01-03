from tipos import procesar_tipo2,procesar_tipo3, process_1, procesar_tipov2
from ia import clasificar_pregunta, get_completion


def main():
    doc1 = "tdr_v4"
    doc2 = "tdr_v6"

    #texto1 = pymupdf4llm.to_markdown(f"{doc1}.pdf")
    #texto2 = pymupdf4llm.to_markdown(f"{doc2}.pdf")
    #procesar_documento_y_almacenar(texto1, "doc1", DATABASE_URL)
    #procesar_documento_y_almacenar(texto2, "doc2", DATABASE_URL)
    #save_diff(json1, json2, "json/diff.json")


    #:)
    QUESTION = """ ¿Cuales son las diferencias en todo el documento? """
    #QUESTION = """ ¿Cuales son las diferencias en las certificaciones? """
    #QUESTION = """Cuales son las formas de pago?"""
    #QUESTION = "El servicio de gestion de dns debe tener minimo de disponibilidad del 70.9%?"
    #QUESTION = "Es cierto que el postor debe acreditar 30000 soles como el monto facturado acumulado?"
    #QUESTION = "Dentro de las caracteristicas de la nube, es obligatoria la certificacion ISO 27020?"
    #QUESTION = "Dame información sobre los servicios de gestion de identidad y acceso"
    #QUESTION = "Que diferencias se encuentran dentro las consideraciones para la ejecucion de prestacion"
    #QUESTION = "Que es lo mas relevante en tomar en cuenta en las otras consideraciones para la ejecucion de la prestacion?"
    #QUESTION = """ De la seccion 5 del documento, qué información diferencia ambos documentos? """
    #QUESTION = """ De la seccion 7.1.1. del documento, qué información diferencia ambos documentos? """
    #QUESTION = "Cuáles son las diferencias entre las características y condiciones del servicio a contratar para los 2 documentos?"
    #QUESTION = "De la seccion 2, 3 y 6 del documento, qué información diferencia ambos documentos?"
    #QUESTION = "Nosotros como desarrolladores, cuáles son los principales cambios en todo el documento que debemos tener en cuenta en el segundo documento?"
    #QUESTION = """ Hablame sobre los plazos """



    first_answer = clasificar_pregunta(QUESTION)
    print(first_answer)


    json1 = f"json/{doc1}.json"
    json2 = f"json/{doc2}.json"

    result = ""
    if first_answer == '2':
        result = procesar_tipov2(QUESTION, "json/diff.json", json1, json2)
    elif first_answer == '3':
        result = procesar_tipo3(QUESTION, json1, json2)
    else:
        result = process_1(QUESTION, "json/diff.json", json1, json2)

    print(result)








if __name__ == '__main__':
    main()