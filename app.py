import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
ARCHIVO = "rifa_data.xlsx"
TOTAL = 500
PRECIO = 5

st.set_page_config(page_title="Rifa Digital", page_icon="🎟️")

# ---------------- USUARIOS ----------------
load_dotenv()

USUARIOS = {
    key: os.getenv(key)
    for key in ["JEYNY", "JAIME", "YESSENIA", "VIAINEY", "INA", "AARON", "ADMIN"]
    if os.getenv(key)
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
    "telefono": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------- DATA ----------------
if "df" not in st.session_state:
    if os.path.exists(ARCHIVO):
        st.session_state.df = pd.read_excel(ARCHIVO, dtype=str)
    else:
        numeros = [str(i).zfill(3) for i in range(1, TOTAL + 1)]
        st.session_state.df = pd.DataFrame({
            "Numero": numeros,
            "Estado": "Libre",
            "Vendedor": "",
            "Comprador": "",
            "DNI": "",
            "Telefono": ""
        })
        st.session_state.df.to_excel(ARCHIVO, index=False)

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
    st.title("🔐 INGRESO VENDEDORES")
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        u = user.strip().upper()
        if u in USUARIOS and USUARIOS[u] == pwd.strip():
            st.session_state.login = True
            st.session_state.vendedor = u
            st.success(f"Bienvenido {u}")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# ---------------- VENTAS ----------------
def ventas_page():
    st.title("🎟️ Registro de ventas")

    vendedor = st.session_state.vendedor
    df = st.session_state.df

    libres = df.query("Estado=='Libre'")["Numero"].tolist()
    if not libres:
        st.warning("No quedan números disponibles")
        return

    if st.session_state.numero not in libres:
        st.session_state.numero = libres[0]

    numero = st.selectbox("Número", libres)
    comprador = st.text_input("Comprador")
    dni = st.text_input("DNI")
    telefono = st.text_input("WhatsApp")

    if st.button("Registrar venta"):
        if not comprador or not dni or not telefono:
            st.error("Complete todos los campos")
            return

        df.loc[df["Numero"] == numero,
               ["Estado", "Vendedor", "Comprador", "DNI", "Telefono"]] = \
               ["Vendido", vendedor, comprador, dni, telefono]

        df.to_excel(ARCHIVO, index=False)

        archivo = crear_volante(
            numero,
            comprador,
            PREMIOS,
            f"boleto_{numero}.png"
        )

        st.image(archivo, width=700)

        msg = f"Hola {comprador}, compraste el número {numero} de la rifa 🎟️"
        link = f"https://wa.me/{telefono}?text={msg.replace(' ', '%20')}"
        st.markdown(f"[📲 Enviar WhatsApp]({link})")

        st.success("Venta registrada correctamente")
        st.experimental_rerun()

# ---------------- MIS VENTAS ----------------
def mis_ventas_page():
    st.header("📊 Mis ventas")

    df = st.session_state.df
    usuario = st.session_state.vendedor
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
    vendidos = df.query("Estado=='Vendido'")
    st.metric("Vendidos", len(vendidos))
    st.metric("Total S/", len(vendidos) * PRECIO)
    st.dataframe(vendidos)

# ---------------- NAVEGACIÓN ----------------
if st.session_state.login:
    opciones = ["Ventas", "Mis ventas"]

    if st.session_state.vendedor == "ADMIN":
        opciones.append("Admin")

    page = st.sidebar.radio("Menú", opciones)

    if st.button("🔒 Cerrar sesión"):
        st.session_state.login = False
        st.session_state.vendedor = None
        st.experimental_rerun()

    if page == "Ventas":
        ventas_page()
    elif page == "Mis ventas":
        mis_ventas_page()
    elif page == "Admin":
        admin_page()
else:
    login_page()
