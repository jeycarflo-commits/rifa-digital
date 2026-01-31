import streamlit as st
import pandas as pd
import os
from io import BytesIO
from urllib.parse import quote

import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIG ----------------
TOTAL = 500
PRECIO = 5

st.set_page_config(page_title="Rifa Digital PRO SALUD", page_icon="🎟️")

# ---------------- USUARIOS ----------------
# En Streamlit Cloud -> Settings -> Secrets puedes tener:
# [USUARIOS]
# JEYNYCARMEN="123@"
# ...
try:
    USUARIOS = dict(st.secrets["USUARIOS"])
except Exception:
    USUARIOS = {
        "JEYNYCARMEN": "123@",
        "JAIMEYARLEQUE": "123@",
        "YESENIACARMEN": "123@",
        "AARONCARMEN": "123@",
        "VIAINEYCARMEN": "123@",
        "INAGALLARDO": "123@",
        "KARINARIVAS": "123@",
        "ADMIN": "admin123",
    }

NOMBRES_COMPLETOS = {
    "JEYNYCARMEN": "Jeyny Carmen",
    "JAIMEYARLEQUE": "Jaime Yarleque",
    "YESENIACARMEN": "Yesenia Carmen",
    "AARONCARMEN": "Aaron Carmen",
    "VIAINEYCARMEN": "Viainey Carmen",
    "INAGALLARDO": "Ina Gallardo",
    "KARINARIVAS": "Karina Rivas",
    "ADMIN": "Administrador",
}

# ---------------- PREMIOS ----------------
PREMIOS = [
    "1er premio: Televisor 50''",
    "2do premio: Smartphone",
    "3er premio: Bicicleta",
]

# ---------------- GOOGLE SHEETS ----------------
# Secrets requeridos:
# SHEET_ID="...."
# [gcp_service_account] ... (service account)
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    # Escribe en la primera hoja (sheet1). Si quieres otra pestaña,
    # cámbialo por: .worksheet("Ventas")
    sheet_id = st.secrets.get("SHEET_ID", "1Sb8CQwE3zo8adi0hcpYlMLiIvrPFGEkyykdpLCAahmQ")
sh = client.open_by_key(sheet_id)

@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        client = gspread.authorize(creds)

        sheet_id = st.secrets.get("SHEET_ID", "1Sb8CQwE3zo8adi0hcpYlMLiIvrPFGEkyykdpLCAahmQ")
        if not sheet_id:
            raise ValueError("SHEET_ID está vacío")

        sh = client.open_by_key(sheet_id)
        return sh.sheet1

    except Exception as e:
        # Esto hará que veas el error real en pantalla
        st.error(f"❌ Error en get_sheet(): {type(e).__name__}: {e}")
        raise




def ensure_sheet_headers():
    """Asegura cabecera correcta en la primera fila."""
    ws = get_sheet()
    values = ws.get_all_values()
    headers = ["Numero", "Estado", "Vendedor", "Comprador", "DNI", "Telefono"]
    if not values:
        ws.append_row(headers)
        return
    if values[0] != headers:
        # Si la cabecera no coincide, NO la reemplazamos a la fuerza (para no destruir datos).
        # Solo avisamos para que el usuario la corrija.
        st.warning(
            "⚠️ Tu Google Sheet debe tener estas columnas en la fila 1: "
            "Numero | Estado | Vendedor | Comprador | DNI | Telefono"
        )


def sheet_to_df() -> pd.DataFrame:
    ensure_sheet_headers()
    ws = get_sheet()
    values = ws.get_all_values()
    if not values or len(values) < 2:
        return pd.DataFrame(columns=["Numero", "Estado", "Vendedor", "Comprador", "DNI", "Telefono"])

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

    # Normalizar columnas esperadas
    for col in ["Numero", "Estado", "Vendedor", "Comprador", "DNI", "Telefono"]:
        if col not in df.columns:
            df[col] = ""

    df["Numero"] = df["Numero"].astype(str).str.strip().str.zfill(3)
    df["Estado"] = df["Estado"].astype(str).str.strip()
    df["Vendedor"] = df["Vendedor"].astype(str).str.strip().str.upper()
    df["Comprador"] = df["Comprador"].astype(str).str.strip()
    df["DNI"] = df["DNI"].astype(str).str.strip()
    df["Telefono"] = df["Telefono"].astype(str).str.strip()

    # Mantener solo filas válidas (número)
    df = df[df["Numero"].str.match(r"^\d{3}$", na=False)]
    return df


def reset_sheet():
    """Reinicia ventas: deja solo cabecera."""
    ws = get_sheet()
    ws.clear()
    ws.append_row(["Numero", "Estado", "Vendedor", "Comprador", "DNI", "Telefono"])


# ---------------- SESSION STATE ----------------
defaults = {
    "login": False,
    "vendedor": None,
    "numero": None,
    "comprador": "",
    "dni": "",
    "telefono": "",
    "archivo_boleto": None,
    "link_whatsapp": None,
    "mostrar_boleto": False,
    "df": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def refresh_df():
    st.session_state.df = sheet_to_df()


# Cargar DF al inicio
if st.session_state.df is None:
    try:
        refresh_df()
    except Exception as e:
        st.error(f"❌ Error conectando a Google Sheets: {e}")
        st.stop()


# ---------------- BOLETO ----------------
def crear_volante(numero: str, comprador: str, premios: list[str], archivo: str) -> str:
    img = Image.new("RGB", (700, 400), (255, 245, 230))
    d = ImageDraw.Draw(img)

    try:
        ft = ImageFont.truetype("arialbd.ttf", 45)
        fn = ImageFont.truetype("arialbd.ttf", 50)
        fs = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        ft = fn = fs = ImageFont.load_default()

    d.rectangle([10, 10, 690, 390], outline="orange", width=5)
    d.text((350, 30), "🎟️ BOLETO DE RIFA 🎟️", fill="darkblue", font=ft, anchor="ms")
    d.text((350, 100), f"Número: {numero}", fill="red", font=fn, anchor="ms")
    d.text((50, 180), f"Comprador: {comprador}", fill="black", font=fs)
    d.text((50, 220), "Premios:", fill="green", font=fs)

    y = 250
    for p in premios:
        d.text((70, y), f"- {p}", fill="darkgreen", font=fs)
        y += 30

    img.save(archivo)
    return archivo


def format_phone_for_wa(raw: str) -> str:
    """Normaliza teléfono para wa.me. Acepta 9 dígitos (Perú) o 51+9."""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 9:
        return "51" + digits
    return digits


# ---------------- LOGIN ----------------
def login_page():
    st.title("🔐 Ingreso vendedores")
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        u = user.strip().upper()
        if u in USUARIOS and USUARIOS[u] == pwd.strip():
            st.session_state.login = True
            st.session_state.vendedor = u
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")


# ---------------- VENTAS ----------------
def ventas_page():
    st.markdown("## 💙 Rifa Pro Salud")
    st.markdown("#### Hoy no solo compras un número, hoy ayudas a cuidar una vida.")
    st.title("🎟️ Registro de ventas")

    vendedor = (st.session_state.vendedor or "").strip().upper()
    nombre_vendedor = NOMBRES_COMPLETOS.get(vendedor, vendedor)
    st.caption(f"Conectado como: **{nombre_vendedor}**")

    # Refrescar ventas del sheet
    df = sheet_to_df()
    st.session_state.df = df

    vendidos = set(df[df["Estado"].str.upper() == "VENDIDO"]["Numero"].tolist())
    todos = [str(i).zfill(3) for i in range(1, TOTAL + 1)]
    libres = [n for n in todos if n not in vendidos]

    if not libres:
        st.warning("No quedan números disponibles")
        return

    def reset_venta():
        st.session_state.comprador = ""
        st.session_state.dni = ""
        st.session_state.telefono = ""
        st.session_state.mostrar_boleto = False
        st.session_state.archivo_boleto = None
        st.session_state.link_whatsapp = None
        st.session_state.numero = libres[0] if libres else None

    # Si el número actual no está disponible, asigna el primero libre
    if st.session_state.numero not in libres:
        st.session_state.numero = libres[0]

    st.markdown("#### 🎟️ Número de rifa")
    numero = st.selectbox("", libres, key="numero")

    st.markdown("#### 👤 Nombre completo del comprador")
    comprador = st.text_input("", key="comprador")

    st.markdown("#### 🆔 DNI del comprador")
    dni = st.text_input("", key="dni")

    st.markdown("#### 📱 Número de WhatsApp")
    telefono = st.text_input("", key="telefono", help="Ejemplo: 999888777 o 51999888777")

    col1, col2 = st.columns(2)
    with col1:
        registrar = st.button("✅ Registrar venta")
    with col2:
        st.button("➕ Nueva venta", on_click=reset_venta)

    if registrar:
        comprador = (comprador or "").strip()
        dni = (dni or "").strip()
        telefono = (telefono or "").strip()

        if not comprador or not dni or not telefono:
            st.error("Complete todos los campos.")
        else:
            numero_fmt = str(numero).zfill(3)
            telefono_wa = format_phone_for_wa(telefono)

            # Validación mínima
            if len(telefono_wa) < 9:
                st.error("Ingrese un número de teléfono válido (solo dígitos).")
                return

            try:
                ws = get_sheet()
                ws.append_row([numero_fmt, "Vendido", vendedor, comprador, dni, telefono])
            except Exception as e:
                st.error(f"❌ No se pudo guardar en Google Sheets: {e}")
                st.stop()

            # Refrescar DF para que el número desaparezca de libres
            refresh_df()

            # Generar boleto (en cloud es temporal, pero sirve para ver/descargar)
            archivo = crear_volante(numero_fmt, comprador, PREMIOS, f"boleto_{numero_fmt}.png")

            msg = f"Hola {comprador}, compraste el número {numero_fmt} de la rifa 🎟️. Aquí está tu boleto digital."
            link = f"https://wa.me/{telefono_wa}?text={quote(msg)}"

            st.session_state.archivo_boleto = archivo
            st.session_state.link_whatsapp = link
            st.session_state.mostrar_boleto = True

            st.success("✅ Venta registrada correctamente (guardada en Google Sheets).")
            # Limpieza de campos para siguiente venta
            st.session_state.comprador = ""
            st.session_state.dni = ""
            st.session_state.telefono = ""

            st.rerun()

    if st.session_state.mostrar_boleto and st.session_state.archivo_boleto:
        st.image(st.session_state.archivo_boleto, width=700)
        if st.session_state.link_whatsapp:
            st.markdown(f"[📲 Enviar WhatsApp]({st.session_state.link_whatsapp})")

        # Botón para descargar el boleto
        try:
            with open(st.session_state.archivo_boleto, "rb") as f:
                st.download_button(
                    "⬇️ Descargar boleto PNG",
                    data=f,
                    file_name=os.path.basename(st.session_state.archivo_boleto),
                    mime="image/png",
                )
        except Exception:
            pass


# ---------------- MIS VENTAS ----------------
def mis_ventas_page():
    st.header("📊 Mis ventas")

    df = sheet_to_df()
    st.session_state.df = df

    vendidos = df[df["Estado"].str.upper() == "VENDIDO"].copy()
    if vendidos.empty:
        st.info("No hay ventas registradas.")
        return

    usuario = (st.session_state.vendedor or "").strip().upper()

    if usuario == "ADMIN":
        for v in sorted(vendidos["Vendedor"].unique()):
            st.subheader(f"👤 {NOMBRES_COMPLETOS.get(v, v)}")
            df_v = vendidos[vendidos["Vendedor"] == v]
            st.write(f"Cantidad: **{len(df_v)}**")
            st.write(f"Total S/: **{len(df_v) * PRECIO}**")
            st.dataframe(df_v, use_container_width=True)
    else:
        df_v = vendidos[vendidos["Vendedor"] == usuario]
        st.write(f"Cantidad: **{len(df_v)}**")
        st.write(f"Total S/: **{len(df_v) * PRECIO}**")
        st.dataframe(df_v, use_container_width=True)


# ---------------- ADMIN ----------------
def admin_page():
    st.header("📊 Panel Admin")

    df = sheet_to_df()
    st.session_state.df = df

    vendidos = df[df["Estado"].str.upper() == "VENDIDO"].copy()

    st.subheader("📊 Resumen por vendedor")
    if vendidos.empty:
        st.info("Aún no hay ventas registradas.")
    else:
        resumen = vendidos.groupby("Vendedor").size().reset_index(name="Cantidad")
        resumen["Dinero"] = resumen["Cantidad"].astype(int) * PRECIO
        resumen = resumen.sort_values(by="Cantidad", ascending=False)
        resumen["Vendedor"] = resumen["Vendedor"].apply(lambda x: NOMBRES_COMPLETOS.get(x, x))
        st.dataframe(resumen, use_container_width=True)

    st.divider()

    st.subheader("📈 Totales generales")
    st.metric("Vendidos", len(vendidos))
    st.metric("Total S/", len(vendidos) * PRECIO)

    st.subheader("📋 Detalle de ventas")
    st.dataframe(vendidos, use_container_width=True)


# ---------------- NAVEGACIÓN ----------------
if st.session_state.login:
    opciones = ["Ventas", "Mis ventas"]
    if (st.session_state.vendedor or "").upper() == "ADMIN":
        opciones.append("Admin")

    page = st.sidebar.radio("Menú", opciones)
    st.sidebar.divider()

    if (st.session_state.vendedor or "").upper() == "ADMIN":
        if st.sidebar.button("🔁 Actualizar ventas"):
            refresh_df()
            st.success("✅ Ventas actualizadas desde Google Sheets")
            st.rerun()

        if st.sidebar.button("🔄 Reiniciar rifa"):
            reset_sheet()
            refresh_df()
            st.success("✅ Rifa reiniciada correctamente (Google Sheets)")
            st.rerun()

        # Exportar Excel desde Google Sheets
        df_export = sheet_to_df()
        buffer = BytesIO()
        df_export.to_excel(buffer, index=False)
        buffer.seek(0)
        st.sidebar.download_button(
            "📤 Exportar Excel",
            buffer,
            file_name="rifa_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.sidebar.divider()
    if st.sidebar.button("🔒 Cerrar sesión"):
        st.session_state.login = False
        st.session_state.vendedor = None
        st.session_state.mostrar_boleto = False
        st.rerun()

    if page == "Ventas":
        ventas_page()
    elif page == "Mis ventas":
        mis_ventas_page()
    else:
        admin_page()
else:
    login_page()
