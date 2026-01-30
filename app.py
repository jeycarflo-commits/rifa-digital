import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ---------------- CONFIG ----------------
ARCHIVO = "rifa_data.xlsx"
TOTAL = 500
PRECIO = 5

st.set_page_config(page_title="Rifa Digital", page_icon="🎟️")

# ---------------- USUARIOS ----------------
USUARIOS = {
    "JEYNY": "123@",
    "JAIME": "123@",
    "YESSENIA": "123@",
    "VIAINEY": "123@",
    "INA": "123@",
    "AARON": "123@",
    "ADMIN": "ADMIN123"
}

# ---------- Premios ----------
PREMIOS = [
    "1er premio: Televisor 50''",
    "2do premio: Smartphone",
    "3er premio: Bicicleta"
]

# ---------------- Inicializar session_state ----------------
for key, default in {
    "login": False,
    "vendedor": None,
    "page": "Login",
    "numero": None,
    "comprador": "",
    "dni": "",
    "telefono": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- Inicializar dataframe en session_state ----------------
if "df" not in st.session_state:
    if os.path.exists(ARCHIVO):
        st.session_state.df = pd.read_excel(ARCHIVO)
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

# ------------------ FUNCION BOLETO ------------------
def crear_volante_profesional(numero, comprador, premios, archivo="boleto.png", logo_path=None):
    ancho, alto = 700, 400
    imagen = Image.new("RGB", (ancho, alto), color=(255, 245, 230))
    dibujar = ImageDraw.Draw(imagen)
    try:
        fuente_titulo = ImageFont.truetype("arialbd.ttf", 45)
        fuente_texto = ImageFont.truetype("arial.ttf", 22)
        fuente_numero = ImageFont.truetype("arialbd.ttf", 50)
    except:
        fuente_titulo = ImageFont.load_default()
        fuente_texto = ImageFont.load_default()
        fuente_numero = ImageFont.load_default()

    margen = 10
    dibujar.rectangle([margen, margen, ancho - margen, alto - margen], outline="orange", width=5)

    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path)
        logo.thumbnail((80, 80))
        imagen.paste(logo, (ancho - 100, 20))

    dibujar.text((ancho//2, 30), "🎟️ BOLETO DE RIFA 🎟️", fill="darkblue", font=fuente_titulo, anchor="ms")
    dibujar.text((ancho//2, 100), f"Número: {numero}", fill="red", font=fuente_numero, anchor="ms")
    dibujar.text((50, 180), f"Comprador: {comprador}", fill="black", font=fuente_texto)
    dibujar.text((50, 220), "Premios a sortear:", fill="green", font=fuente_texto)
    y = 250
    for premio in premios:
        dibujar.text((70, y), f"- {premio}", fill="darkgreen", font=fuente_texto)
        y += 30
    dibujar.line((50, 210, ancho - 50, 210), fill="orange", width=3)
    imagen.save(archivo)
    return archivo

# ------------------ LOGIN ------------------
def login_page():
    st.title("🔐 INGRESO VENDEDORES")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        user_upper = user.strip().upper()
        password_stripped = password.strip()
        if user_upper in USUARIOS and USUARIOS[user_upper] == password_stripped:
            st.session_state.login = True
            st.session_state.vendedor = user_upper
            st.session_state.page = "Ventas"
            st.success(f"BIENVENIDO VENDEDOR {user_upper}")
        else:
            st.error("Usuario o contraseña incorrectos")

# ------------------ VENTAS ------------------
def ventas_page():
    vendedor = st.session_state.vendedor
    st.title("🎟️ Sistema de Rifa")

    if st.button("🔒 Cerrar sesión"):
        st.session_state.login = False
        st.session_state.vendedor = None
        st.session_state.page = "Login"

    st.success(f"Conectado como: {vendedor}")

    st.header("Registrar venta")

    # Mostrar números libres
    libres = st.session_state.df[st.session_state.df["Estado"] == "Libre"]["Numero"].tolist()
    
    if not libres:
        st.info("No quedan números libres")
        st.session_state.numero = None
    else:
        if st.session_state.numero not in libres:
            st.session_state.numero = libres[0]
        st.session_state.numero = st.selectbox("Número", libres, index=libres.index(st.session_state.numero))

    # Inputs
    st.session_state.comprador = st.text_input("Comprador", value=st.session_state.comprador)
    st.session_state.dni = st.text_input("DNI", value=st.session_state.dni)
    st.session_state.telefono = st.text_input("WhatsApp", value=st.session_state.telefono)

    # Registrar venta
    if st.button("Registrar venta") and st.session_state.numero:
        numero = st.session_state.numero
        comprador = st.session_state.comprador.strip()
        dni = st.session_state.dni.strip()
        telefono = st.session_state.telefono.strip()

        if comprador == "" or dni == "" or telefono == "":
            st.error("Debe ingresar Comprador, DNI y número de celular")
        else:
            # Guardar venta
            st.session_state.df.loc[
                st.session_state.df["Numero"] == numero,
                ["Estado", "Vendedor", "Comprador", "DNI", "Telefono"]
            ] = ["Vendido", vendedor, comprador, dni, telefono]

            st.session_state.df.to_excel(ARCHIVO, index=False)

            # Generar boleto
            archivo_boleto = crear_volante_profesional(
                numero, comprador, PREMIOS,
                archivo=f"boleto_{numero}.png",
                logo_path="logo.png"
            )
            st.image(archivo_boleto, caption="Tu boleto digital 🎟️", use_column_width=True)

            # Enviar WhatsApp
            mensaje = f"Hola {comprador}, compraste el número {numero} de la rifa 🎟️. Aquí está tu boleto digital."
            link = f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}"
            st.markdown(f"[📲 Enviar WhatsApp]({link})")

            st.success("Venta registrada y boleto generado")

            # Limpiar campos
            st.session_state.comprador = ""
            st.session_state.dni = ""
            st.session_state.telefono = ""

            # Actualizar número seleccionado automáticamente
            libres = st.session_state.df[st.session_state.df["Estado"] == "Libre"]["Numero"].tolist()
            if libres:
                st.session_state.numero = libres[0]
            else:
                st.session_state.numero = None

# ------------------ RESUMEN PERSONAL ------------------
def resumen_page():
    st.header("📊 Mis ventas")
    vendedor = st.session_state.vendedor
    mis = st.session_state.df[
        (st.session_state.df["Estado"] == "Vendido") & 
        (st.session_state.df["Vendedor"] == vendedor)
    ]
    st.write("Vendidos:", len(mis))
    st.write("Total S/:", len(mis) * PRECIO)
    st.dataframe(mis)

# ------------------ PANEL ADMIN ------------------
def admin_page():
    st.header("📈 Panel administrador")
    df = st.session_state.df
    vendidos = df[df["Estado"] == "Vendido"].shape[0]
    total = vendidos * PRECIO
    st.metric("Total vendidos", vendidos)
    st.metric("Total recaudado", f"S/ {total}")

    reporte = df[df["Estado"] == "Vendido"].groupby("Vendedor").size().reset_index(name="Cantidad")
    st.dataframe(reporte)

    # Exportar Excel
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="📥 Exportar Excel",
        data=buffer,
        file_name="reporte_rifa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Reiniciar ventas
    if st.button("🔄 Reiniciar todas las ventas"):
        st.session_state.df["Estado"] = "Libre"
        st.session_state.df["Vendedor"] = ""
        st.session_state.df["Comprador"] = ""
        st.session_state.df["DNI"] = ""
        st.session_state.df["Telefono"] = ""
        st.session_state.df.to_excel(ARCHIVO, index=False)
        st.success("¡Todas las ventas fueron reiniciadas!")

    # Sortear ganador
    vendidos_df = df[df["Estado"] == "Vendido"]
    if st.button("🎉 Sortear ganador"):
        if vendidos_df.shape[0] > 0:
            ganador = vendidos_df.sample(1)
            st.success(f"Ganador: {ganador.iloc[0]['Numero']} - {ganador.iloc[0]['Comprador']}")
        else:
            st.warning("No hay ventas registradas para sortear")

# ------------------ NAVEGACIÓN ------------------
if st.session_state.login:
    opciones = ["Ventas", "Mis ventas"]
    if st.session_state.vendedor.upper() == "ADMIN":
        opciones.append("Admin")
    pagina = st.sidebar.radio("Ir a:", opciones, index=0)

    if pagina == "Ventas":
        ventas_page()
    elif pagina == "Mis ventas":
        resumen_page()
    elif pagina == "Admin":
        admin_page()
else:
    login_page()