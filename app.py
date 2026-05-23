import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from pypdf import PdfReader

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    api_key = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=api_key)

LIBROS_DIR = "libros"

HISTORIAL_DIR = "historial"
HISTORIAL_FILE = os.path.join(HISTORIAL_DIR, "conversaciones.json")


def guardar_conversacion(usuario, respuesta, modelo, nivel, modo):
    os.makedirs(HISTORIAL_DIR, exist_ok=True)

    nueva_conversacion = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modelo": modelo,
        "nivel": nivel,
        "modo": modo,
        "usuario": usuario,
        "respuesta": respuesta
    }

    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as archivo:
            historial = json.load(archivo)
    else:
        historial = []

    historial.append(nueva_conversacion)

    with open(HISTORIAL_FILE, "w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, ensure_ascii=False, indent=4)


def leer_libros():
    textos = []

    if not os.path.exists(LIBROS_DIR):
        return ""

    for nombre_archivo in os.listdir(LIBROS_DIR):
        ruta_archivo = os.path.join(LIBROS_DIR, nombre_archivo)

        if nombre_archivo.lower().endswith(".txt"):
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                textos.append(archivo.read())

        elif nombre_archivo.lower().endswith(".pdf"):
            reader = PdfReader(ruta_archivo)
            texto_pdf = ""

            for pagina in reader.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_pdf += texto_pagina + "\n"

            textos.append(texto_pdf)

    return "\n\n".join(textos)


st.set_page_config(
    page_title="INOKI English Teacher - Groq",
    page_icon="🇬🇧",
    layout="centered"
)

st.markdown("""
<style>
.main {
    background-color: #f7f9fc;
}

.block-container {
    padding-top: 2rem;
    max-width: 850px;
}

h1 {
    text-align: center;
    color: #1f2937;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 18px;
    margin-bottom: 25px;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0px 4px 18px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.stChatMessage {
    border-radius: 14px;
    padding: 8px;
}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.title("⚙️ Configuración")

    nivel = st.selectbox(
        "Nivel de inglés",
        ["A1-Principiante","A2-Basico", "B1-Intermedio" , "B2-Intermedio"]
    )

    modo = st.selectbox(
        "Modo de práctica",
        [
            "Profesor paciente",
            "Corrección gramatical",
            "Conversación diaria",
            "Preparación para examen",
            "Traducción y explicación"
        ]
    )

    st.divider()

    if st.button("🗑️ Borrar conversación"):
        st.session_state.mensajes = []
        st.rerun()


st.title("Inoki English Tutor - Groq")

st.markdown(
    """
    <p class="subtitle">
    Practica inglés, corrige frases y mejora tu gramática con ayuda personalizada.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="card">
        <b>Modelo:</b> Groq Llama 3.1 8B Instant<br>
        <b>Modo actual:</b> {modo}<br>
        <b>Nivel:</b> {nivel}
    </div>
    """,
    unsafe_allow_html=True
)


if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "contenido_libros" not in st.session_state:
    st.session_state.contenido_libros = leer_libros()


for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["contenido"])


pregunta = st.chat_input("Escribe tu pregunta o frase en inglés...")


if pregunta:
    st.session_state.mensajes.append({
        "rol": "user",
        "contenido": pregunta
    })

    with st.chat_message("user"):
        st.write(pregunta)

    prompt_sistema = f"""
Eres un profesor de inglés para un estudiante de nivel {nivel}.
Tu modo actual es: {modo}.

Usa la siguiente información de referencia tomada de libros de inglés cuando sea útil:

{st.session_state.contenido_libros[:3000]}

Reglas:
- Explica de forma clara y sencilla.
- Antes de cada respuesta ten en cuenta el historial de cada conversacion
- Si el estudiante comete errores, corrígelos con amabilidad.
- Da ejemplos cortos.
- Si responde en español, puedes explicar en español e inglés.
- Si practica conversación, responde en inglés sencillo.
- Si la información de los libros no es suficiente, responde con tu conocimiento general.
"""

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    *[
                        {
                            "role": m["rol"],
                            "content": m["contenido"]
                        }
                        for m in st.session_state.mensajes[-6:]
                    ]
                ],
                max_tokens=700
            )

            texto_respuesta = respuesta.choices[0].message.content
            st.write(texto_respuesta)

            guardar_conversacion(
                usuario=pregunta,
                respuesta=texto_respuesta,
                modelo="Groq Llama 3.1 8B Instant",
                nivel=nivel,
                modo=modo
            )

    st.session_state.mensajes.append({
        "rol": "assistant",
        "contenido": texto_respuesta
    })