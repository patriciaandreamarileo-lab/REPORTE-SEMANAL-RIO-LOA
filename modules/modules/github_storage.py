
import streamlit as st
import requests
import base64
from pathlib import PurePosixPath


# =====================================================
# CONFIGURACIÓN DE GITHUB
# =====================================================

def obtener_configuracion():

    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    return token, repo


def obtener_headers():

    token, _ = obtener_configuracion()

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


# =====================================================
# CONSTRUIR DIRECCIÓN DEL ARCHIVO
# =====================================================

def obtener_url(ruta):

    _, repo = obtener_configuracion()

    ruta = str(PurePosixPath(ruta))

    return f"https://api.github.com/repos/{repo}/contents/{ruta}"


# =====================================================
# CONSULTAR ARCHIVO EXISTENTE
# =====================================================

def obtener_sha(ruta):

    respuesta = requests.get(
        obtener_url(ruta),
        headers=obtener_headers(),
        timeout=30
    )

    if respuesta.status_code == 200:
        return respuesta.json()["sha"]

    if respuesta.status_code == 404:
        return None

    raise Exception(
        f"Error consultando GitHub: {respuesta.status_code} "
        f"- {respuesta.text}"
    )


# =====================================================
# SUBIR O REEMPLAZAR ARCHIVO
# =====================================================

def subir_archivo_github(archivo, ruta):

    contenido = archivo.getvalue()

    contenido_base64 = base64.b64encode(
        contenido
    ).decode("utf-8")

    sha = obtener_sha(ruta)

    datos = {
        "message": f"Actualización de archivo: {ruta}",
        "content": contenido_base64
    }

    # Si el archivo ya existe, se reemplaza
    if sha:
        datos["sha"] = sha

    respuesta = requests.put(
        obtener_url(ruta),
        headers=obtener_headers(),
        json=datos,
        timeout=120
    )

    if respuesta.status_code not in (200, 201):

        raise Exception(
            f"Error al guardar archivo: "
            f"{respuesta.status_code} - {respuesta.text}"
        )

    return respuesta.json()


# =====================================================
# DESCARGAR ARCHIVO DESDE GITHUB
# =====================================================

def descargar_archivo_github(ruta):

    respuesta = requests.get(
        obtener_url(ruta),
        headers=obtener_headers(),
        params={"ref": "main"},
        timeout=60
    )

    if respuesta.status_code == 404:
        return None

    if respuesta.status_code != 200:

        raise Exception(
            f"Error descargando archivo: "
            f"{respuesta.status_code} - {respuesta.text}"
        )

    contenido = respuesta.json()["content"]

    return base64.b64decode(contenido)


# =====================================================
# COMPROBAR CONEXIÓN
# =====================================================

def comprobar_conexion():

    _, repo = obtener_configuracion()

    respuesta = requests.get(
        f"https://api.github.com/repos/{repo}",
        headers=obtener_headers(),
        timeout=30
    )

    return respuesta.status_code == 200
