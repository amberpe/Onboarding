from tool import function_calling


def main():
    print("Chatbot de comparacion de TDRS")

    QUESTION = """ ¿Cuales son las diferencias en todo el documento? """
    # QUESTION = """ ¿Cuales son las diferencias en las certificaciones? """
    # QUESTION = """Cuales son las formas de pago?"""
    # QUESTION = "El servicio de gestion de dns debe tener minimo de disponibilidad del 70.9%?"
    # QUESTION = "Es cierto que el postor debe acreditar 30000 soles como el monto facturado acumulado?"
    # QUESTION = "Dentro de las caracteristicas de la nube, es obligatoria la certificacion ISO 27020?"
    # QUESTION = "Dame información sobre los servicios de gestion de identidad y acceso"
    # QUESTION = "Que diferencias se encuentran dentro las consideraciones para la ejecucion de prestacion"
    # QUESTION = "Que es lo mas relevante en tomar en cuenta en las otras consideraciones para la ejecucion de la prestacion?"
    # QUESTION = """ De la seccion 5 del documento, qué información diferencia ambos documentos? """
    # QUESTION = """ De la seccion 7.1.1. y 5.1. del documento, qué información diferencia ambos documentos? """
    # QUESTION = "comparacion de la seccion ocho"
    # QUESTION = "Cuáles son las diferencias entre las características y condiciones del servicio a contratar para los 2 documentos?"
    #QUESTION = "De los apartados 2, 3 y 6 del documento, qué información diferencia ambos documentos?"
    # QUESTION = "Nosotros como desarrolladores, cuáles son los principales cambios en todo el documento que debemos tener en cuenta en el segundo documento?"
    #QUESTION = """ Hablame sobre los plazos """
    # QUESTION = "Cuales son las diferencias en la seccion 5.4 de los 2 documentos?"

    function_calling(QUESTION)






if __name__ == '__main__':



    main()