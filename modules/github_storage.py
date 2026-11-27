import streamlit as st
import requests
import base64
from pathlib import PurePosixPath


# =====================================================
# 1. CONFIGURACIÓN DE GITHUB
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
# 2. DIRECCIÓN DEL ARCHIVO
# =====================================================

def obtener_url(ruta):

    _, repo = obtener_configuracion()

    ruta = str(PurePosixPath(ruta))

    return f"https://api.github.com/repos/{repo}/contents/{ruta}"


# =====================================================
# 3. OBTENER IDENTIFICADOR DEL ARCHIVO
# =====================================================

def obtener_sha(ruta):

    respuesta = requests.get(
        obtener_url(ruta),
        headers=obtener_headers(),
        params={"ref": "main"},
        timeout=30
    )

    if respuesta.status_code == 200:
        return respuesta.json()["sha"]

    if respuesta.status_code == 404:
        return None

    raise Exception(
        f"Error consultando GitHub: "
        f"{respuesta.status_code} - {respuesta.text}"
    )


# =====================================================
# 4. SUBIR O REEMPLAZAR ARCHIVOS
# =====================================================

def subir_archivo_github(archivo, ruta):

    contenido = archivo.getvalue()

    contenido_base64 = base64.b64encode(
        contenido
    ).decode("utf-8")

    sha = obtener_sha(ruta)

    datos = {
        "message": f"Actualización de archivo: {ruta}",
        "content": contenido_base64,
        "branch": "main"
    }

    if sha:
        datos["sha"] = sha

    respuesta = requests.put(
        obtener_url(ruta),
        headers=obtener_headers(),
        json=datos,
        timeout=180
    )

    if respuesta.status_code not in (200, 201):

        raise Exception(
            f"Error al guardar archivo: "
            f"{respuesta.status_code} - {respuesta.text}"
        )

    return respuesta.json()


# =====================================================
# 5. DESCARGAR ARCHIVOS DESDE GITHUB
# =====================================================

def descargar_archivo_github(ruta):

    # Primero consultamos los metadatos del archivo
    respuesta = requests.get(
        obtener_url(ruta),
        headers=obtener_headers(),
        params={"ref": "main"},
        timeout=30
    )

    if respuesta.status_code == 404:
        return None

    if respuesta.status_code != 200:

        raise Exception(
            f"Error consultando archivo: "
            f"{respuesta.status_code} - {respuesta.text}"
        )

    informacion = respuesta.json()

    # Obtenemos la dirección del archivo original
    url_descarga = informacion.get("download_url")

    if not url_descarga:
        raise Exception(
            "GitHub no entregó la dirección de descarga del archivo."
        )

    # Descargamos los bytes originales, sin convertirlos a JSON
    headers_descarga = {
        "Authorization": f"Bearer {obtener_configuracion()[0]}",
        "Accept": "application/octet-stream"
    }

    descarga = requests.get(
        url_descarga,
        headers=headers_descarga,
        timeout=180
    )

    if descarga.status_code != 200:

        raise Exception(
            f"Error descargando archivo: "
            f"{descarga.status_code}"
        )

    contenido = descarga.content

    if not contenido:
        raise Exception("El archivo descargado está vacío.")

    return contenido


# =====================================================
# 6. COMPROBAR CONEXIÓN
# =====================================================

def comprobar_conexion():

    _, repo = obtener_configuracion()

    respuesta = requests.get(
        f"https://api.github.com/repos/{repo}",
        headers=obtener_headers(),
        timeout=30
    )

    return respuesta.status_code == 200
