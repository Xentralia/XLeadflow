#Este archivo ayuda al archivo proncipal a tomar prompts externos con datos que se completan
#usando dicionarios que pueden ser proporcionados por el usuario o que pueden generarse en la
#ejecución de las funciones principales

import os

# Carga el contenido de un archivo de texto con la plantilla del prompt.
def cargar_prompt(ruta_archivo: str) -> str:
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"El archivo {ruta_archivo} no existe.")
    
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        return f.read()


# Rellena los campos del prompt con los datos proporcionados.
def rellenar_prompt(plantilla: str, datos: dict) -> str:
    try:
        return plantilla.format(**datos)
    except KeyError as e:
        raise ValueError(f"Falta el dato requerido en el prompt: {e}")


# Carga una plantilla desde archivo y la rellena con los datos.
def construir_prompt(ruta_archivo: str, datos: dict) -> str:
    plantilla = cargar_prompt(ruta_archivo)
    prompt_final = rellenar_prompt(plantilla, datos)
    return prompt_final
    #Esta función es la que hace magia en el archivo principal
