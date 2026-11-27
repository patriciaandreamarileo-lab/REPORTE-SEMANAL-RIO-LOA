
import streamlit as st
import requests
import base64
import zipfile
import io

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
        "X-GitHub-Api-Version": "2022-11-28",
        "Cache-Control": "no-cache"
    }


# =====================================================
# 2. DIRECCIÓN DEL ARCHIVO
# =====================================================

def obtener_url(ruta):

    _, repo = obtener_configuracion()

    ruta = str(PurePosixPath(ruta))

    return (
        f"https://api.github.com/repos/"
        f"{repo}/contents/{ruta}"
    )


# =====================================================
# 3. CONSULTAR INFORMACIÓN DEL ARCHIVO
# =====================================================

def obtener_info_archivo(ruta):

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
            f"Error consultando GitHub: "
            f"{respuesta.status_code} - {respuesta.text}"
        )

    return respuesta.json()


def obtener_sha(ruta):

    informacion = obtener_info_archivo(ruta)

    if informacion is None:
        return None

    return informacion.get("sha")


# =====================================================
# 4. SUBIR O REEMPLAZAR ARCHIVOS
# =====================================================

def subir_archivo_github(archivo, ruta):

    # Obtener contenido original

    if hasattr(archivo, "getvalue"):
        contenido = archivo.getvalue()
    else:
        contenido = bytes(archivo)

    if not contenido:
        raise Exception("El archivo seleccionado está vacío.")

    # Validar que sea un Excel válido

    if not zipfile.is_zipfile(io.BytesIO(contenido)):
        raise Exception(
            "El archivo no tiene una estructura Excel válida. "
            "Verifica que sea un archivo XLSM."
        )

    contenido_base64 = base64.b64encode(
        contenido
    ).decode("utf-8")

    # Consultar SHA actual y reemplazar

    for intento in range(2):

        sha_anterior = obtener_sha(ruta)

        datos = {
            "message": f"Actualización de archivo: {ruta}",
            "content": contenido_base64,
            "branch": "main"
        }

        if sha_anterior:
            datos["sha"] = sha_anterior

        respuesta = requests.put(
            obtener_url(ruta),
            headers=obtener_headers(),
            json=datos,
            timeout=180
        )

        # Si hubo conflicto, volver a consultar el SHA

        if respuesta.status_code in (409, 422):

            if intento == 0:
                continue

        if respuesta.status_code not in (200, 201):

            raise Exception(
                f"Error al guardar archivo en GitHub: "
                f"{respuesta.status_code} - {respuesta.text}"
            )

        resultado = respuesta.json()

        # Verificar que GitHub guardó la nueva versión

        informacion_actual = obtener_info_archivo(ruta)

        if informacion_actual is None:
            raise Exception(
                "GitHub respondió a la subida, "
                "pero no se encontró el archivo posteriormente."
            )

        sha_guardado = resultado.get(
            "content", {}
        ).get("sha")

        sha_actual = informacion_actual.get("sha")

        if sha_guardado and sha_actual != sha_guardado:

            raise Exception(
                "La verificación del archivo no coincide "
                "con la versión que se intentó guardar."
            )

        return {
            "ruta": ruta,
            "sha_archivo": sha_actual,
            "sha_commit": resultado.get(
                "commit", {}
            ).get("sha"),
            "mensaje_commit": resultado.get(
                "commit", {}
            ).get("message"),
            "tamano": informacion_actual.get("size"),
            "actualizado": True
        }

    raise Exception(
        "No fue posible actualizar el archivo después "
        "de reintentar la operación."
    )


# =====================================================
# 5. DESCARGAR ARCHIVOS DESDE GITHUB
# =====================================================

def descargar_archivo_github(ruta):

    informacion = obtener_info_archivo(ruta)

    if informacion is None:
        return None

    url_descarga = informacion.get("download_url")

    if not url_descarga:

        raise Exception(
            "GitHub no entregó la dirección de descarga."
        )

    # Incorporar SHA a la URL para evitar una versión antigua
    # almacenada en caché.

    url_descarga = (
        f"{url_descarga}?version={informacion.get('sha')}"
    )

    descarga = requests.get(
        url_descarga,
        headers={
            "Authorization": (
                f"Bearer {obtener_configuracion()[0]}"
            ),
            "Accept": "application/octet-stream",
            "Cache-Control": "no-cache"
        },
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
