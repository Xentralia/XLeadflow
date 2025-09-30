# # # # # # # # # # # # # # # # # # # # # # # # # #
#              Generador de leads                 #
# V.4.0.0 //28 08 2025// Integracion de Apollo    #
#                                                 #
# Desplegado con streamlit y render               #
# Agente impulsado con OpenAI y Apollo API        #
# Desarrollador: Sergio Emiliano López Bautista   #
# # # # # # # # # # # # # # # # # # # # # # # # # #


# ------------------------- Requerimentos y librerías -------------------------------
import io
import os
import csv
import time
import codecs
import requests
import streamlit as st
from openai import OpenAI
import pandas as pd
import json
from dotenv import load_dotenv, find_dotenv
from utils.prompts import construir_prompt #Esto toma el archivo de prompts.py
# --------------------------- Seteadores ----------------------------------------------
st.set_page_config(page_title = "X Leadflow V.4.0.2",
                   page_icon = "📝",
                   layout="wide")

dotenv_path = find_dotenv()
load_dotenv(dotenv_path, override=True)
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
apollo_key = os.getenv("APOLLO_API_KEY")

st.title("Generador de leads 📝")

# ------------------------------ Estructuras -----------------------------------------
class Cliente:
    def __init__(self, industria, postores, producto, zona, tamanio):
        self.industria = industria        
        self.postores = postores
        self.producto = producto
        self.zona = zona
        self.tamanio = tamanio

# --------------------------- Funciones -----------------------------------------------
def instrucciones():
    with codecs.open("data/instrucciones.txt", "r", encoding="utf-8") as f:
        fi = f.read()
    file = fi.split('\n')
    for linea in file:
        st.markdown(linea)

def listas(archivo: str):
    if not os.path.exists(archivo):
        raise FileNotFoundError(f"El archivo {archivo} no existe.")
    with open(archivo, 'r', encoding='utf-8') as f:
        return f.read()
    
def lista2(ruta: str):
    texto = ''.join(listas(ruta))
    opciones = [item.strip().strip('"') for item in texto.split(",") if item.strip()]
    return opciones

def agente_seeker(cliente):
    datos = vars(cliente)
    try:
        seeker = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", 
                       "content": construir_prompt("data/prompt2.txt", datos)}],
            temperature=0
        )
        respuesta = seeker.choices[0].message.content.strip()
        return respuesta
    except Exception as e:
        st.error(f"Algo alió mal. {str(e)}")
        return None
    
def agente_payload(cliente):
    datos = vars(cliente)
    try:
        respuesta = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": construir_prompt("data/prompt3.txt", datos)}],
            temperature=0
        ).choices[0].message.content.strip()

        payload = json.loads(respuesta)
        return payload

    except Exception as e:
        st.error(f"Error generando payload: {e}")
        return {}

def agente_geolocalizador(cliente):
    datos = vars(cliente)
    try:
        geolocalizador = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", 
                       "content": construir_prompt("data/prompt4.txt", datos)}],
            temperature=0
        )
        respuesta = geolocalizador.choices[0].message.content.strip()
        return respuesta
    except Exception as e:
        st.error(f"Algo alió mal. {str(e)}")
        return None

def denue(entidad):
    token = os.getenv("DENUE_TOKEN")
    url = f"https://www.inegi.org.mx/app/api/denue/v1/consulta/BuscarEntidad/todos/{entidad}/1/100000000/{token}"

    response = requests.get(url)
    return response.json()

def apollo_personas(payload_nuevo):
    url = "https://api.apollo.io/api/v1/mixed_people/search"

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": apollo_key
    }

    payload = payload_nuevo

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def apollo_contact(payload_nuevo):
    url = "https://api.apollo.io/api/v1/contacts/search?sort_ascending=false"

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": apollo_key
    }

    payload_nuevo.pop("sort_by_field", None)
    payload_nuevo.pop("sort_ascending", None)
    response = requests.post(url, headers=headers, json=payload_nuevo)
    if response.status_code==200:
        return response.json()
    else:
        st.error(f"Ocurrió un inconveniente con la busqueda:{response.text}")
        return {}

# -------------------------------- Interfaz (MAIN)-----------------------------------------
st.markdown("## ¡Bienvenido!")
instrucciones()

st.sidebar.markdown("# Encontremos a tus clientes ideales")
st.sidebar.header("Completa estos datos clave:")

industria = st.sidebar.selectbox("Industria principal:", 
                                lista2("data/lista_ind.txt"), 
                                index=None, 
                                placeholder="¿En qué sector operas?")

if industria == "Otra":
    industria = st.sidebar.text_input("Especifica:")

postores = st.sidebar.text_input("Clientes ideales:", 
                                 placeholder="¿Qué empresas o perfiles buscas?")
producto = st.sidebar.text_input("Tu producto/servicio", 
                                 placeholder="¿Qué ofreces específicamente?")
zona = st.sidebar.text_input("Zona de cobertura", 
                             placeholder="Estados, regiones, ciudades")

tamanio = st.sidebar.pills("Tamaño del cliente", ["Pequeño", "Mediano", "Grande"], selection_mode="multi")

acuerdo = st.sidebar.checkbox(listas("data/acuerdo.txt"))

if acuerdo:
    if st.sidebar.button("🔍 Buscar Prospectos"):
        if all([industria, postores, producto, zona, tamanio]):

            with st.spinner("Recopilando información..."):
                cliente = Cliente(industria, postores, producto, zona, tamanio)
                #Buscamos la explicación
                p3 = agente_seeker(cliente)

                #Normalizamos los datos
                p4 = agente_payload(cliente)
                print(p4)
                # Rescatamos la normalización y hacemos la consulta
                json_path = apollo_contact(p4)

                # Cargar JSON directamente en un DataFrame
                if "contacts" in json_path:
                    df = pd.json_normalize(json_path["contacts"])
                else:
                    df = pd.DataFrame()  # Vacío si no hay contactos

                with open("data/estados.json", "r", encoding="utf-8") as f:
                    estados_dict = json.load(f)
                
                #entidad = estados_dict["Zacatecas"]
                #denue_data = denue(entidad)
                #print(denue_data)

                df_filtrado = df[
                    (df["name"].notna()) & #
                    (df["title"].notna()) & #
                    (df["organization_name"].notna()) & #
                    (df["linkedin_url"].notna()) & #
                    (df["city"].notna()) & #
                    (df["state"].notna()) & #
                    (df["country"].notna()) & #
                    (df["email"].notna()) & #
                    (df["organization.linkedin_url"].notna()) #
                ]
                df = df_filtrado[lista2("data/columnas_finales.txt")]

                # Guardar a CSV
                csv_completo = df.to_csv(index=False)
       
                st.success("Clientes encontrados")
                st.markdown(p3)
                st.dataframe(df)

                iz, der = st.columns([1,1], gap="small")
                with iz:
                    st.download_button(
                        label = "Sólo explicación",
                        data = p3,
                        file_name = f"explicacion_{cliente.industria}.txt",
                        mime = "text/plain"
                    )
                with der:
                    st.download_button(
                        label="Sólo leads",
                        data= csv_completo,
                        file_name=f"leads_{cliente.industria}.csv",
                        mime="text/csv"
                    )

        else:
            st.sidebar.warning("Por favor completa todos los campos.")