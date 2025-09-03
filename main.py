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

st.title("📝 Herramienta especializada en prospección de ventas a empresas, no a consumidores.")

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

def agente(cliente):
    datos = vars(cliente)
    peticion = construir_prompt("data/prompt.txt", datos)
    try:
        traductor = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", 
                       "content": peticion}
                    ],
            temperature=0
        )
        respuesta = traductor.choices[0].message.content.strip()

        try:
            payload = json.loads(respuesta)
        except json.JSONDecodeError:
            raise ValueError(f"No se pudo convertir a JSON: {respuesta}")
        return payload

    except Exception as e:
        st.error(f"Algo alió mal. {str(e)}")
        return None
    
def apollo(payload_oai):
    url = "https://api.apollo.io/api/v1/mixed_people/search"

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": apollo_key
    }

    payload = payload_oai

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# -------------------------------- Interfaz (MAIN)-----------------------------------------
st.markdown("## ¡Bienvenido!")
instrucciones()

st.sidebar.markdown("# Encontremos a tus clientes ideales")
st.sidebar.header("Completa estos datos clave:")

industria = st.sidebar.selectbox("Industria principal:", 
                                ["Agroindustria", "Alimentos", "Arquitectura", "Artes/Cultural", "Automotriz",
                                 "Bebidas", "Bienes Raíces",
                                 "Ciberseguridad", "Construcción", "Consultoría", "Contabilidad",
                                 "Diseño", "Dispositivos Médicos",
                                 "e-commerce", "e-learning", "Educación", "Energía", "Entretenimiento",
                                 "Farmacéutica", "Finanzas", "Fintech", "Fitness/Wellness",
                                 "Gobierno",
                                 "Hardware Tecnológico", "Hospitales/Clínicas", "Hotelería",
                                 "Industrial", "Inteligencia Artificial",
                                 "Legal", "Logística",
                                 "Manufactura", "Medios", "Moda",
                                 "Nutrición",
                                 "ONGs/Social", "Organismos Gubernamentales",
                                 "Plásticos", "Publicidad/Marketing",
                                 "Química",
                                 "Recursos Humanos", "Retail/Comercio",
                                 "Salud", "Seguros", "Software", "Suplementos",
                                 "Tecnología", "Telecomunicaciones", "Textil", "Transporte", "Turismo",
                                 "Videojuegos", "Otra"],
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

acuerdo = st.sidebar.checkbox("Confirmo que comprendo y acepto que los prospectos son generados automáticamente " \
                      "por Inteligencia Artificial (IA) mediante análisis de fuentes públicas.  " \
                      "La información debe ser verificada antes de ser utilizada, XentraliA no garantiza precisión ni disponibilidad de datos. " \
                      "Me comprometo a cumplir con leyes aplicables de protección de datos.")


if acuerdo:
    if st.sidebar.button("🔍 Buscar Prospectos"):
        if all([industria, postores, producto, zona, tamanio]):

            with st.spinner("Recopilando información..."):
                cliente = Cliente(industria, postores, producto, zona, tamanio)
                #Normalizamos los datos
                p4 = agente(cliente)
                # Rescatamos la normalización y hacemos la consulta
                json_path = apollo(p4)

                print(f"Se cargaron {len(json_path)} leads desde {json_path}")

                # Cargar JSON directamente en un DataFrame
                df = pd.json_normalize(json_path)

                # Guardar a CSV
                csv_completo = df.to_csv(f"leads_{cliente.industria}.csv", index=False)
                print(f"Se guardaron {len(df)} leads filtrados en leads_filtrados3.csv")
                
       
                st.success("Clientes encontrados")
                st.markdown(df)

                iz, der = st.columns([1,1], gap="small")
                with iz:
                    st.download_button(
                        label = "Info completa",
                        data = str(json_path),
                        file_name = f"información_{cliente.industria}.txt",
                        mime = "text/plain"
                    )
                with der:
                    st.download_button(
                        label="Sólo leads en CSV",
                        data= csv_completo,
                        file_name="leads_CSV.csv",
                        mime="text/csv"
                    )
        else:
            st.sidebar.warning("Por favor completa todos los campos.")