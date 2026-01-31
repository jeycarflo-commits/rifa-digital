import streamlit as st
import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO


# ---------------- CONFIG ----------------
ARCHIVO = "rifa_data.xlsx"
TOTAL = 500
PRECIO = 5

# ---------------- GOOGLE SHEETS (PERSISTENCIA) ----------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SHEET_ID"]).sheet1

def sheet_to_df():
    sheet = get_sheet()
    values = sheet.get_all_values()

    if not values or len(values) < 2:
        return pd.DataFrame(
            columns=["Numero","Estado","Vendedor","Comprador","DNI","Telefono"]
        )

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

    df["Numero"] = df["Numero"].astype(str).str.zfill(3)
    df["Vendedor"] = df["Vendedor"].fillna("").str.upper().str.strip()
    df["Estado"] = df["Estado"].fillna("")
    df["Comprador"] = df["Comprador"].fillna("")
    df["DNI"] = df["DNI"].fillna("")
    df["Telefono"] = df["Telefono"].fillna("")

    return df

def reset_sheet():
    sheet = get_sheet()
    sheet.clear()
    sheet.append_row(
        ["Numero","Estado","Vendedor","Comprador","DNI","Telefono"]
    )

st.set_page_config(page_title="Rifa Digital PRO SALUD", page_icon="🎟️")

# ---------------- USUARIOS ----------------
import streamlit as st

# ---------------- USUARIOS ----------------
try:
    USUARIOS = st.secrets["USUARIOS"]
except:
    USUARIOS = {
        "JEYNYCARMEN": "123@",
        "JAIMEYARLEQUE": "123@",
        "YESENIACARMEN": "123@",
        "AARONCARMEN": "123@",
        "VIAINEYCARMEN": "123@",
        "INAGALLARDO": "123@",
        "KARINARIVAS": "123@",
        "ADMIN": "admin123"
    }

# Diccionario de nombres completos
NOMBRES_COMPLETOS = {
    "JEYNYCARMEN": "Jeyny Carmen",
    "JAIMEYARLEQUE": "Jaime Yarleque",
    "YESENIACARMEN": "Yesenia Carmen",
    "AARONCARMEN": "Aaron Carmen",
    "VIAINEYCARMEN": "Viainey Carmen",
    "INAGALLARDO": "Ina Gallardo",
    "KARINARIVAS": "Karina Rivas",
    "ADMIN": "Administrador"
}



# ---------------- PREMIOS ----------------
PREMIOS = [
    "1er premio: Televisor 50''",
    "2do premio: Smartphone",
    "3er premio: Bicicleta"
]

# ---------------- SESSION STATE ----------------
for key, val in {
    "login": False,
    "vendedor": None,
    "numero": None,
    "comprador": "",
    "dni": "",
    "telefono": "",
    "archivo_boleto": None,
    "link_whatsapp": None,
    "mostrar_boleto": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------- DATA ----------------
if "df" not in st.session_state:
    try:
        st.session_state.df = sheet_to_df()
    except Exception as e:
        st.error(f"Error conectando a Google Sheets: {e}")
        st.stop()



# ---------------- BOLETO ----------------
def crear_volante(numero, comprador, premios, archivo):
    img = Image.new("RGB", (700, 400), (255, 245, 230))
    d = ImageDraw.Draw(img)

    try:
        ft = ImageFont.truetype("arialbd.ttf", 45)
        fn = ImageFont.truetype("arialbd.ttf", 50)
        fs = ImageFont.truetype("arial.ttf", 22)
    except:
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

# ---------------- LOGIN ----------------
def login_page():
    st.title("🔐 INGRESA EL PASSWORD DEL VENDEDORES")
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
    st.success("## 💙 “Hoy no solo compras un número, hoy ayudas a cuidar una vida.")

    st.title("🎟️ Registro de ventas")
    vendedor = st.session_state.vendedor.strip().upper()
    df = st.session_state.df

    # Números libres
    libres = df.query("Estado=='Libre'")["Numero"].tolist()
    if not libres:
        st.warning("No quedan números disponibles")
        return

    # Inicializar número si no existe
    if "numero" not in st.session_state or st.session_state.numero not in libres:
        st.session_state.numero = libres[0]

    # Función para reiniciar campos al crear nueva venta
    def reset_venta():
        st.session_state.comprador = ""
        st.session_state.dni = ""
        st.session_state.telefono = ""
        st.session_state.mostrar_boleto = False
        if libres:
            st.session_state.numero = libres[0]

    # Selección de número y campos de comprador
    st.markdown("### 💳 Número de Rifa")
    numero = st.selectbox("", libres, key="numero")

    st.markdown("### 👨‍💼 👩‍💼 Nombre Completo del Comprador")
    comprador = st.text_input("", key="comprador")

    st.markdown("### 🪪 DNI del Comprador")
    dni = st.text_input("", key="dni")

    st.markdown("### 📱 Número de WhatsApp")
    telefono = st.text_input("", key="telefono")



    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        registrar = st.button("✅ Registrar venta")
    with col2:
        nueva = st.button("➕ Nueva venta", on_click=reset_venta)

    # Registrar venta
    if registrar:
        if not comprador or not dni or not telefono:
            st.error("Complete todos los campos")
        else:
            numero_fmt = str(numero).zfill(3)

            sheet = get_sheet()
sheet.append_row([
    numero_fmt,
    "Vendido",
    vendedor,
    comprador,
    dni,
    telefono
])

st.session_state.df = sheet_to_df()


            archivo = crear_volante(
                numero_fmt,
                comprador,
                PREMIOS,
                f"boleto_{numero_fmt}.png"
            )

            msg = f"Hola {comprador}, compraste el número {numero_fmt} de la rifa 🎟️. Aquí está tu boleto digital."
            link = f"https://wa.me/{telefono}?text={msg.replace(' ', '%20')}"

            st.session_state.archivo_boleto = archivo
            st.session_state.link_whatsapp = link
            st.session_state.mostrar_boleto = True

            st.success("Venta registrada correctamente")

    # Mostrar boleto si corresponde
    if st.session_state.mostrar_boleto:
        st.image(st.session_state.archivo_boleto, width=700)
        st.markdown(f"[📲 Enviar WhatsApp]({st.session_state.link_whatsapp})")



# ---------------- MIS VENTAS ----------------
def mis_ventas_page():
    ##################################################
    st.write("✅ Probando conexión con Google Sheets...")
try:
    sheet = get_sheet()
    st.write("Conectado a:", sheet.spreadsheet.title)
    st.write("Hoja:", sheet.title)
    st.write("Filas actuales:", sheet.row_count)
except Exception as e:
    st.error(f"❌ No conecta a Google Sheets: {e}")
    st.stop()
##############################################
    
    st.header("📊 Mis ventas")
    df = st.session_state.df
    usuario = st.session_state.vendedor.strip().upper()
    vendidos = df.query("Estado=='Vendido'")

    if vendidos.empty:
        st.info("No hay ventas registradas")
        return

    if usuario == "ADMIN":
        for v in vendidos["Vendedor"].unique():
            st.subheader(f"👤 {v}")
            df_v = vendidos[vendidos["Vendedor"] == v]
            st.write(f"Cantidad: {len(df_v)}")
            st.write(f"Total S/: {len(df_v) * PRECIO}")
            st.dataframe(df_v)
    else:
        df_v = vendidos[vendidos["Vendedor"] == usuario]
        st.write(f"Cantidad: {len(df_v)}")
        st.write(f"Total S/: {len(df_v) * PRECIO}")
        st.dataframe(df_v)

# ---------------- ADMIN ----------------
def admin_page():
    st.header("📊 Panel Admin")

    df = st.session_state.df
    vendidos = df[df["Estado"] == "Vendido"].copy()

    # ====== RESUMEN ARRIBA ======
    st.subheader("📊 Resumen por vendedor")

    if vendidos.empty:
        st.info("Aún no hay ventas registradas")
    else:
        resumen = (
            vendidos
            .groupby("Vendedor")
            .size()
            .reset_index(name="Numero")
        )

        resumen["Dinero"] = resumen["Numero"].astype(int) * PRECIO
        resumen = resumen.sort_values(by="Numero", ascending=False)

        st.dataframe(resumen, use_container_width=True)

    st.divider()

    # ====== MÉTRICAS ======
    st.subheader("📈 Totales generales")
    st.metric("Vendidos", len(vendidos))
    st.metric("Total S/", len(vendidos) * PRECIO)

    # ====== TABLA COMPLETA ======
    st.subheader("📋 Detalle de ventas")
    st.dataframe(vendidos, use_container_width=True)

  

    # ====== BOTONES (NO SE TOCAN) ======


# ---------------- NAVEGACIÓN ----------------
if st.session_state.login:
    opciones = ["Ventas", "Mis ventas"]
    if st.session_state.vendedor == "ADMIN":
        opciones.append("Admin")

    page = st.sidebar.radio("Menú", opciones)
    st.sidebar.divider()

    # ===== BOTONES ADMIN =====
    if st.session_state.vendedor == "ADMIN":

        if st.sidebar.button("🔁 Actualizar ventas"):
            df = pd.read_excel(ARCHIVO, dtype=str)

            df["Numero"] = df["Numero"].astype(str).str.zfill(3)
            df["Vendedor"] = (
                df["Vendedor"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            st.session_state.df = df
            st.success("Ventas actualizadas")
            st.rerun()

        if st.sidebar.button("🔄 Reiniciar rifa"):
            numeros = [str(i).zfill(3) for i in range(1, TOTAL + 1)]
            df_reset = pd.DataFrame({
                "Numero": numeros,
                "Estado": "Libre",
                "Vendedor": "",
                "Comprador": "",
                "DNI": "",
                "Telefono": ""
            })
            reset_sheet()
st.session_state.df = sheet_to_df()
st.success("Rifa reiniciada correctamente (Google Sheets)")
st.rerun()

            st.success("Rifa reiniciada correctamente")
            st.rerun()

        df_export = sheet_to_df()
buffer = BytesIO()
df_export.to_excel(buffer, index=False)
buffer.seek(0)

st.sidebar.download_button(
    "📤 Exportar Excel",
    buffer,
    file_name="rifa_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
    elif page == "Admin":
        admin_page()
else:
    login_page()
