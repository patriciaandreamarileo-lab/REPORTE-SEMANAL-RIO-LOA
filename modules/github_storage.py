
import base64
import requests
import streamlit as st


# =========================================================
# 1. CONFIGURACIÓN
# =========================================================

def obtener_configuracion():

    try:
        token = st.secrets["GITHUB_TOKEN"]
        repositorio = st.secrets["GITHUB_REPO"]
        rama = st.secrets.get("GITHUB_BRANCH", "main")

        return token, repositorio, rama

    except Exception as error:

        raise ValueError(
            "Faltan configuraciones de GitHub en Streamlit Secrets. "
            "Verifica GITHUB_TOKEN y GITHUB_REPO."
        ) from error


def obtener_headers():

    token, _, _ = obtener_configuracion()

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def construir_url(ruta):

    _, repositorio, _ = obtener_configuracion()

    return (
        f"https://api.github.com/repos/"
        f"{repositorio}/contents/{ruta}"
    )


# =========================================================
# 2. DESCARGAR ARCHIVOS DESDE GITHUB
# =========================================================

def descargar_archivo_github(ruta):
    """
    Descarga archivos desde GitHub.

    Para archivos pequeños utiliza el contenido Base64
    de la API.

    Para archivos grandes utiliza download_url,
    evitando recibir contenido incompleto.
    """

    _, _, rama = obtener_configuracion()

    url = construir_url(ruta)

    respuesta = requests.get(
        url,
        headers=obtener_headers(),
        params={"ref": rama},
        timeout=60
    )

    if respuesta.status_code == 404:
        return None

    if respuesta.status_code != 200:

        raise Exception(
            f"Error al consultar {ruta}: "
            f"{respuesta.status_code} - {respuesta.text}"
        )

    datos = respuesta.json()

    # Caso 1: GitHub entrega el archivo en Base64
    if (
        datos.get("encoding") == "base64"
        and datos.get("content")
    ):

        contenido = datos["content"].replace("\n", "")

        archivo_bytes = base64.b64decode(contenido)

        if archivo_bytes:
            return archivo_bytes

    # Caso 2: archivo grande o contenido no disponible
    download_url = datos.get("download_url")

    if not download_url:

        raise Exception(
            f"GitHub no proporcionó una URL de descarga "
            f"para el archivo {ruta}."
        )

    respuesta_archivo = requests.get(
        download_url,
        headers={
            "Authorization": obtener_headers()["Authorization"],
            "Accept": "application/octet-stream"
        },
        timeout=120
    )

    if respuesta_archivo.status_code != 200:

        raise Exception(
            f"No fue posible descargar el archivo original: "
            f"{respuesta_archivo.status_code}"
        )

    contenido = respuesta_archivo.content

    if not contenido:

        raise Exception(
            f"El archivo descargado está vacío: {ruta}"
        )

    return contenido


# =========================================================
# 3. SUBIR O ACTUALIZAR ARCHIVOS EN GITHUB
# =========================================================

def subir_archivo_github(
    ruta,
    contenido,
    mensaje="Actualización desde dashboard"
):
    """
    Sube un archivo nuevo o reemplaza uno existente.

    Parámetros:
    ruta: ubicación del archivo en GitHub.
    contenido: contenido binario del archivo.
    mensaje: mensaje del commit.
    """

    _, _, rama = obtener_configuracion()

    url = construir_url(ruta)

    headers = obtener_headers()

    # Comprobar que el contenido sea binario
    if isinstance(contenido, str):

        raise TypeError(
            "El contenido debe ser bytes, no texto."
        )

    if not isinstance(contenido, bytes):

        raise TypeError(
            "El archivo debe enviarse en formato bytes."
        )

    if not contenido:

        raise ValueError(
            "El archivo seleccionado está vacío."
        )

    # Consultar si el archivo ya existe
    respuesta_actual = requests.get(
        url,
        headers=headers,
        params={"ref": rama},
        timeout=60
    )

    sha = None

    if respuesta_actual.status_code == 200:

        sha = respuesta_actual.json().get("sha")

    elif respuesta_actual.status_code != 404:

        raise Exception(
            "No se pudo verificar el archivo en GitHub: "
            f"{respuesta_actual.status_code} - "
            f"{respuesta_actual.text}"
        )

    # Convertir contenido a Base64
    contenido_base64 = base64.b64encode(
        contenido
    ).decode("utf-8")

    datos = {
        "message": mensaje,
        "content": contenido_base64,
        "branch": rama
    }

    # Si existe, actualizar utilizando su SHA
    if sha:
        datos["sha"] = sha

    respuesta = requests.put(
        url,
        headers=headers,
        json=datos,
        timeout=180
    )

    if respuesta.status_code not in (200, 201):

        raise Exception(
            f"Error al guardar {ruta}: "
            f"{respuesta.status_code} - "
            f"{respuesta.text}"
        )

    return True


# =========================================================
# 4. VERIFICAR CONEXIÓN CON GITHUB
# =========================================================

def verificar_conexion_github():

    try:

        _, repositorio, _ = obtener_configuracion()

        url = (
            f"https://api.github.com/repos/{repositorio}"
        )

        respuesta = requests.get(
            url,
            headers=obtener_headers(),
            timeout=30
        )

        if respuesta.status_code == 200:

            return True, "Conexión con GitHub exitosa."

        return False, (
            f"No se pudo conectar con GitHub. "
            f"Código: {respuesta.status_code}. "
            f"Detalle: {respuesta.text}"
        )

    except Exception as error:

        return False, str(error)


# =========================================================
# 5. RUTAS DE ARCHIVOS DE RÍO LOA
# =========================================================

RUTA_MRP = "data/MRP/Planificacion_MRP.xlsm"

RUTA_CONSUMO = (
    "data/CONSUMO/consumo_rio_loa.xlsx"
)

RUTA_PRECIOS = (
    "data/PRECIOS/precios_rio_loa.xlsx"
)
