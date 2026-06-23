import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import altair as alt
import admin

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA (¡Siempre debe ser el primer comando!)
# ==============================================================================
st.set_page_config(page_title="Bodega Fuxion PRO MAX", layout="wide")

# ==============================================================================
# 2. CONEXIÓN A LA BASE DE DATOS (Híbrida: Nube + Local)
# ==============================================================================
try:
    # Intenta leer desde la Nube (Streamlit Cloud Secrets)
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # Si da error (porque estás en tu PC local), lee el archivo .env
    load_dotenv()
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# 3. SISTEMA DE SUSCRIPCIONES Y LOGIN
# ==============================================================================
# Inicializar memoria temporal
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "plan_actual" not in st.session_state:
    st.session_state["plan_actual"] = ""
if "dias_restantes" not in st.session_state:
    st.session_state["dias_restantes"] = 0
if "empresa_id" not in st.session_state:
    st.session_state["empresa_id"] = ""


def mostrar_login():
    st.markdown(
        "<h1 style='text-align: center;'>🔒 Acceso Bodega Fuxion PRO MAX</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("formulario_login"):
            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "Ingresar al Sistema", use_container_width=True
            )

            if submit:
                try:
                    respuesta = (
                        supabase.table("clientes_suscripciones")
                        .select("*")
                        .eq("usuario", usuario_input)
                        .eq("password", password_input)
                        .execute()
                    )

                    if len(respuesta.data) > 0:
                        datos_cliente = respuesta.data[0]
                        fecha_vencimiento = datetime.strptime(
                            datos_cliente["fecha_vencimiento"], "%Y-%m-%d"
                        ).date()
                        fecha_hoy = datetime.now().date()

                        if fecha_hoy <= fecha_vencimiento:
                            dias_calculados = (fecha_vencimiento - fecha_hoy).days

                            st.session_state["logeado"] = True
                            st.session_state["usuario_actual"] = usuario_input
                            st.session_state["empresa_id"] = datos_cliente["empresa_id"]
                            st.session_state["plan_actual"] = datos_cliente["plan"]
                            st.session_state["dias_restantes"] = dias_calculados

                            st.success("¡Acceso concedido! Preparando el Dashboard...")
                            st.rerun()
                        else:
                            st.error(
                                f"❌ Tu plan {datos_cliente['plan']} venció el {fecha_vencimiento.strftime('%d/%m/%Y')}."
                            )
                            st.warning(
                                "📲 Contáctanos por WhatsApp al +57 300 000 0000 para renovar tu suscripción."
                            )
                    else:
                        st.error("⚠️ Usuario o contraseña incorrectos.")
                except Exception as e:
                    st.error(
                        f"Error de conexión: {e}. Verifica que la tabla 'clientes_suscripciones' exista en Supabase."
                    )


# ==============================================================================
# 4. EL GUARDIA DE SEGURIDAD (Peaje)
# ==============================================================================
if not st.session_state["logeado"]:
    mostrar_login()
    st.stop()

# ==============================================================================
# 5. MENÚ DEL USUARIO (Si ya pasó el peaje)
# ==============================================================================
st.sidebar.markdown(f"👤 **Bienvenido:** {st.session_state['usuario_actual']}")
st.sidebar.markdown(f"⭐ **Plan Activo:** {st.session_state['plan_actual']}")

dias = st.session_state["dias_restantes"]

if dias > 10:
    st.sidebar.success(f"⏳ **Tiempo restante:** {dias} días")
elif dias > 0:
    st.sidebar.warning(f"⚠️ **Tiempo restante:** {dias} días")
    if dias in [10, 5, 1]:
        st.toast(
            f"¡Atención! A tu suscripción le quedan {dias} días. Contáctanos para renovar.",
            icon="🚨",
        )
else:
    st.sidebar.error("⏳ **Tiempo restante:** ¡Vence HOY!")
    st.toast("¡Atención! Tu plan vence el día de hoy.", icon="🚨")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["logeado"] = False
    st.rerun()

st.sidebar.markdown("---")

st.markdown(
    """
    <style>
    .stApp { background-color: #F4F6F9; }
    h1, h2, h3, h4 { color: #1E2B58 !important; font-family: 'Arial', sans-serif; }
    .btn-principal>button { background-color: #00ADEF; color: white; border-radius: 6px; font-weight: bold; border: none; width: 100%; height: 45px;}
    .btn-principal>button:hover { background-color: #1E2B58; color: white; }
    div[data-testid="metric-container"] { background-color: #ffffff; border-radius: 8px; padding: 15px; border: 2px solid #00ADEF; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);}
    .header-tabla { background-color: #1E2B58; color: white; padding: 8px; border-radius: 4px; font-weight: bold; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. INICIALIZAR MEMORIA ESTADO (SESSION STATE)
# ==============================================================================
if "carrito_ventas" not in st.session_state:
    st.session_state.carrito_ventas = []
if "carrito_entradas" not in st.session_state:
    st.session_state.carrito_entradas = []
if "limpiador" not in st.session_state:
    st.session_state.limpiador = 0
if "prod_limpiador" not in st.session_state:
    st.session_state.prod_limpiador = 0

lk = str(st.session_state.limpiador)
plk = str(st.session_state.prod_limpiador)

# ==============================================================================
# 3. DESCARGA DE DATOS (CEREBRO CENTRAL)
# ==============================================================================
id_seguro = st.session_state.get("empresa_id", "")

# PRODUCTOS AHORA SON GLOBALES (SIN FILTRO) PARA QUE TODOS LOS VEAN
try:
    t_prod = supabase.table("productos").select("*").execute().data or []
except:
    t_prod = []
lista_prod = [p["nombre"] for p in t_prod] if t_prod else ["Sin datos"]

# LAS DEMÁS TABLAS ESTÁN AISLADAS POR CLIENTE (CON FILTRO)
try:
    t_cli = (
        supabase.table("clientes")
        .select("*")
        .eq("empresa_id", id_seguro)
        .execute()
        .data
        or []
    )
except:
    t_cli = []
lista_cli = [c["nombre"] for c in t_cli] if t_cli else ["Sin datos"]

try:
    t_ase = (
        supabase.table("asesores")
        .select("*")
        .eq("empresa_id", id_seguro)
        .execute()
        .data
        or []
    )
except:
    t_ase = []
lista_ase = [a["nombre"] for a in t_ase] if t_ase else ["Sin datos"]

try:
    t_gastos = (
        supabase.table("gastos").select("*").eq("empresa_id", id_seguro).execute().data
        or []
    )
except:
    t_gastos = []

try:
    t_abonos = (
        supabase.table("abonos").select("*").eq("empresa_id", id_seguro).execute().data
        or []
    )
except:
    t_abonos = []

try:
    t_ventas = (
        supabase.table("ventas").select("*").eq("empresa_id", id_seguro).execute().data
        or []
    )
except:
    t_ventas = []

try:
    t_entradas = (
        supabase.table("entradas")
        .select("*")
        .eq("empresa_id", id_seguro)
        .execute()
        .data
        or []
    )
except:
    t_entradas = []

try:
    t_bonos = (
        supabase.table("bonos_extras")
        .select("*")
        .eq("empresa_id", id_seguro)
        .execute()
        .data
        or []
    )
except:
    t_bonos = []

try:
    t_inv = (
        supabase.table("inventario")
        .select("*")
        .eq("empresa_id", id_seguro)
        .execute()
        .data
        or []
    )
except:
    t_inv = []

# SEMANAS GLOBALES (SIN FILTRO)
try:
    res_sem = supabase.table("semanas").select("*").execute().data
    t_semanas = res_sem if res_sem else []
except:
    try:
        res_sem2 = supabase.table("semana").select("*").execute().data
        t_semanas = res_sem2 if res_sem2 else []
    except:
        t_semanas = []


# ==============================================================================
# 4. FUNCIONES MATEMÁTICAS Y DE NEGOCIO (PREVIAS A LAS INTERFACES)
# ==============================================================================
def extraer_numero_semana(nombre):
    try:
        return int("".join(filter(str.isdigit, str(nombre))))
    except:
        return 0


hoy = datetime.now().date()
periodo_actual_sistema = "Periodo 1"
semana_actual_sistema = "Semana 1"

if t_semanas:
    for s in t_semanas:
        try:
            f_ini_raw = (
                str(s.get("fecha_inicio") or s.get("fecha_ini") or "")
                .strip()
                .split("T")[0]
            )
            f_fin_raw = str(s.get("fecha_fin", "")).strip().split("T")[0]
            if not f_ini_raw or not f_fin_raw:
                continue

            def parsear_fecha(texto):
                if "-" in texto:
                    partes = texto.split("-")
                    if len(partes[0]) == 4:
                        return datetime.strptime(texto, "%Y-%m-%d").date()
                    else:
                        return datetime.strptime(texto, "%d-%m-%Y").date()
                elif "/" in texto:
                    partes = texto.split("/")
                    if len(partes[2]) == 4:
                        return datetime.strptime(texto, "%d/%m/%Y").date()
                return None

            d_ini = parsear_fecha(f_ini_raw)
            d_fin = parsear_fecha(f_fin_raw)

            if d_ini and d_fin:
                if d_ini <= hoy <= d_fin:
                    semana_actual_sistema = str(
                        s.get("nombre_semana") or s.get("semana", "Semana 1")
                    ).strip()
                    periodo_actual_sistema = str(s.get("periodo", "Periodo 1")).strip()
                    break
        except:
            continue


def buscar_x_pub(nombre_producto):
    coincidencias = [p for p in t_prod if p["nombre"] == nombre_producto]
    if not coincidencias:
        return 0.0
    return float(coincidencias[0].get("precio_pub", 0.0))


def obtener_stock_actual(nombre_p):
    try:
        in_ent = sum(
            float(item.get("cantidad") or 0)
            for item in t_entradas
            if item.get("producto") == nombre_p
        )
        out_ven = sum(
            float(item.get("cantidad") or 0)
            for item in t_ventas
            if item.get("producto") == nombre_p
        )
        in_inv = sum(
            float(item.get("cantidad") or 0)
            for item in t_inv
            if item.get("producto") == nombre_p
            and "SUMA" in item.get("tipo_movimiento", "")
        )
        out_inv = sum(
            float(item.get("cantidad") or 0)
            for item in t_inv
            if item.get("producto") == nombre_p
            and "RESTA" in item.get("tipo_movimiento", "")
        )
        return (in_ent + in_inv) - (out_ven + out_inv)
    except:
        return 0


def calcular_puntos_vendedora(nombre_asesor):
    try:
        if not nombre_asesor:
            return 0, 0, 0
        total_pv_ganados = sum(
            int(v.get("puntos_pv") or 0)
            for v in t_ventas
            if v.get("asesor") == nombre_asesor
        )
        regalos_entregados = [
            r
            for r in t_inv
            if r.get("asesor") == nombre_asesor and r.get("tipo_movimiento") == "RESTA"
        ]
        total_cajas_regalo = sum(
            int(r.get("cantidad") or 0) for r in regalos_entregados
        )
        pv_descontados_por_regalos = total_cajas_regalo * 80
        pv_disponibles_netos = total_pv_ganados - pv_descontados_por_regalos
        return total_pv_ganados, pv_descontados_por_regalos, pv_disponibles_netos
    except:
        return 0, 0, 0


def calcular_saldo_cliente(nombre_cliente):
    try:
        if not nombre_cliente or nombre_cliente == "Sin datos":
            return 0.0
        total_credito = sum(
            float(v.get("precio_venta") or 0)
            for v in t_ventas
            if v.get("cliente") == nombre_cliente
            and v.get("medio_pago") in ["Crédito", "Otros", "Addi", "Sistecrédito"]
        )
        total_abonos = sum(
            float(a.get("monto") or 0)
            for a in t_abonos
            if a.get("cliente") == nombre_cliente
        )
        return total_credito - total_abonos
    except:
        return 0.0


def generar_siguiente_factura():
    try:
        numeros = []
        for item in t_ventas:
            fact_id = item.get("id_factura_venta")
            if fact_id and fact_id.startswith("FACT-"):
                try:
                    numeros.append(int(fact_id.split("-")[1]))
                except:
                    continue
        if not numeros:
            return "FACT-001"
        return f"FACT-{(max(numeros) + 1):03d}"
    except:
        return "FACT-001"


def calcular_porcentaje_fuxion(total_pv):
    if total_pv >= 800:
        return "50%"
    elif total_pv >= 500:
        return "40%"
    elif total_pv >= 300:
        return "30%"
    elif total_pv >= 100:
        return "25%"
    elif total_pv >= 60:
        return "20%"
    else:
        return "0%"


def obtener_periodo_semana_de_fecha(fecha_str):
    try:
        if isinstance(fecha_str, pd.Timestamp):
            f_date = fecha_str.date()
        else:
            f_date = pd.to_datetime(fecha_str).date()
        for s in t_semanas:
            ini_raw = str(s.get("fecha_inicio") or s.get("fecha_ini") or "").split("T")[
                0
            ]
            fin_raw = str(s.get("fecha_fin", "")).split("T")[0]
            if ini_raw and fin_raw:
                ini = pd.to_datetime(ini_raw, dayfirst=False, errors="coerce")
                if pd.isna(ini):
                    ini = pd.to_datetime(ini_raw, dayfirst=True, errors="coerce")
                fin = pd.to_datetime(fin_raw, dayfirst=False, errors="coerce")
                if pd.isna(fin):
                    fin = pd.to_datetime(fin_raw, dayfirst=True, errors="coerce")
                if not pd.isna(ini) and not pd.isna(fin):
                    if ini.date() <= f_date <= fin.date():
                        return str(s.get("periodo", "N/A")).strip(), str(
                            s.get("nombre_semana") or s.get("semana", "N/A")
                        ).strip()
    except:
        pass
    return "N/A", "N/A"


def obtener_pv_unificado_semanas():
    pv_num = {}
    for ent in t_entradas:
        w = extraer_numero_semana(ent.get("semana", ""))
        if w > 0:
            pv_num[w] = pv_num.get(w, 0.0) + float(ent.get("puntos_pv") or 0.0)
    for v in t_ventas:
        if v.get("medio_pago") in [
            "Plataforma Fuxion",
            "Pago Directo a Fuxion (Plataforma)",
        ]:
            _, v_sem = obtener_periodo_semana_de_fecha(v.get("fecha"))
            w = extraer_numero_semana(v_sem)
            if w > 0:
                pv_num[w] = pv_num.get(w, 0.0) + float(v.get("puntos_pv") or 0.0)
    return pv_num


# ==============================================================================
# 5. RENDERIZACIÓN DEL DASHBOARD GENERAL (MÓDULO DE GRÁFICOS)
# ==============================================================================
def render_dashboard():
    st.title("📊 Panel de Control Gerencial (Inteligencia de Negocios)")
    v_df = pd.DataFrame(t_ventas)
    df_calendario = pd.DataFrame(t_semanas)
    anios_set, periodos_set, semanas_set = set(), set(), set()

    if not df_calendario.empty:
        col_fecha = (
            "fecha_inicio"
            if "fecha_inicio" in df_calendario.columns
            else ("fecha_ini" if "fecha_ini" in df_calendario.columns else None)
        )
        if col_fecha:
            fechas_validas = pd.to_datetime(
                df_calendario[col_fecha], errors="coerce"
            ).dropna()
            anios_set = set(fechas_validas.dt.year.astype(int).astype(str))
        if "periodo" in df_calendario.columns:
            periodos_set = set(
                df_calendario["periodo"].dropna().astype(str).str.strip()
            )
        col_sem = (
            "nombre_semana"
            if "nombre_semana" in df_calendario.columns
            else ("semana" if "semana" in df_calendario.columns else None)
        )
        if col_sem:
            semanas_set = set(df_calendario[col_sem].dropna().astype(str).str.strip())

    anios = ["TODOS"] + sorted(list(anios_set))
    periodos = ["TODOS"] + sorted(list(periodos_set))
    semanas = ["TODOS"] + sorted(list(semanas_set), key=extraer_numero_semana)

    st.markdown("### 🔍 Filtros de Análisis (Slicers)")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sel_anio = st.selectbox("📅 Seleccionar Año", anios)
    with col_f2:
        sel_periodo = st.selectbox("🗓️ Seleccionar Periodo", periodos)
    with col_f3:
        sel_semana = st.selectbox("📆 Seleccionar Semana", semanas)

    if v_df.empty:
        st.info("No hay ventas registradas para mostrar en el Dashboard.")
        return

    v_df["fecha"] = pd.to_datetime(v_df["fecha"], errors="coerce")
    v_df["Año"] = v_df["fecha"].dt.year.astype(str)

    def map_per_sem(f):
        p, s = obtener_periodo_semana_de_fecha(f)
        return pd.Series([p, s])

    v_df[["Periodo", "Semana"]] = v_df["fecha"].apply(map_per_sem)

    df_filtrado = v_df.copy()
    if sel_anio != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Año"] == sel_anio]
    if sel_periodo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Periodo"] == sel_periodo]
    if sel_semana != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Semana"] == sel_semana]

    if df_filtrado.empty:
        st.warning(f"⚠️ No hay ventas registradas bajo estos filtros.")
        return

    st.markdown("### 📈 Indicadores Clave (KPIs)")
    col1, col2, col3, col4 = st.columns(4)
    total_ventas = df_filtrado["precio_venta"].sum()
    total_cajas = df_filtrado["cantidad"].sum()
    ticket_promedio = total_ventas / len(df_filtrado) if len(df_filtrado) > 0 else 0

    cartera_data = []
    for c in t_cli:
        saldo = calcular_saldo_cliente(c["nombre"])
        if saldo > 0:
            cartera_data.append({"Cliente": c["nombre"], "Deuda": saldo})
    df_cartera = pd.DataFrame(cartera_data)
    total_cartera = df_cartera["Deuda"].sum() if not df_cartera.empty else 0

    col1.metric("💰 Venta Total (Filtrada)", f"${total_ventas:,.0f}")
    col2.metric("📦 Cajas Vendidas (Filtrada)", f"{total_cajas:,.0f}")
    col3.metric("🧾 Ticket Promedio", f"${ticket_promedio:,.0f}")
    col4.metric("🚨 Cartera Activa (Global)", f"${total_cartera:,.0f}")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 👩‍💼 Rendimiento de Vendedores / Asesores")
        df_asesores = (
            df_filtrado.groupby("asesor")["precio_venta"]
            .sum()
            .reset_index()
            .sort_values(by="precio_venta", ascending=False)
        )
        if not df_asesores.empty:
            bar_vend = (
                alt.Chart(df_asesores)
                .mark_bar(
                    color="#00ADEF", cornerRadiusTopLeft=5, cornerRadiusTopRight=5
                )
                .encode(
                    x=alt.X(
                        "asesor",
                        sort="-y",
                        title="Asesor Comercial",
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("precio_venta", title="Total Vendido ($)"),
                )
            )
            txt_vend = bar_vend.mark_text(
                align="center",
                baseline="bottom",
                dy=-5,
                fontWeight="bold",
                color="#1E2B58",
            ).encode(text=alt.Text("precio_venta:Q", format="$,.0f"))
            st.altair_chart(bar_vend + txt_vend, use_container_width=True)
        else:
            st.info("Sin datos de asesores.")

    with c2:
        st.markdown("#### 💳 Composición por Medio de Pago (Ingresos)")
        df_pagos = df_filtrado.groupby("medio_pago")["precio_venta"].sum().reset_index()
        if not df_pagos.empty:
            df_pagos["Porcentaje"] = (
                df_pagos["precio_venta"] / df_pagos["precio_venta"].sum()
            ) * 100
            pie_base = alt.Chart(df_pagos).encode(
                theta=alt.Theta(field="precio_venta", type="quantitative"),
                color=alt.Color(
                    field="medio_pago",
                    type="nominal",
                    legend=alt.Legend(title="Método", orient="right"),
                ),
                tooltip=[
                    alt.Tooltip("medio_pago", title="Medio"),
                    alt.Tooltip("precio_venta", title="Monto", format="$,.0f"),
                    alt.Tooltip("Porcentaje", title="Porcentaje", format=".1f"),
                ],
            )
            pie = pie_base.mark_arc(innerRadius=50, stroke="#fff")
            pie_txt = pie_base.mark_text(
                radiusOffset=25, fontSize=13, fontWeight="bold"
            ).encode(text=alt.Text("precio_venta:Q", format="$,.0f"))
            st.altair_chart(pie + pie_txt, use_container_width=True)
        else:
            st.info("Sin datos de medios de pago.")

    st.markdown("---")
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("#### 🚨 Top Clientes con Créditos / Deudas Activas")
        if not df_cartera.empty:
            df_cartera_top = df_cartera.sort_values(by="Deuda", ascending=False).head(
                10
            )
            bar_cart = (
                alt.Chart(df_cartera_top)
                .mark_bar(
                    color="#ff4d4d", cornerRadiusTopLeft=5, cornerRadiusTopRight=5
                )
                .encode(
                    x=alt.X(
                        "Cliente",
                        sort="-y",
                        title="Nombre del Cliente",
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("Deuda", title="Saldo Pendiente ($)"),
                )
            )
            txt_cart = bar_cart.mark_text(
                align="center",
                baseline="bottom",
                dy=-5,
                fontWeight="bold",
                color="#cc0000",
            ).encode(text=alt.Text("Deuda:Q", format="$,.0f"))
            st.altair_chart(bar_cart + txt_cart, use_container_width=True)
        else:
            st.success("¡Excelente! No tienes cartera pendiente con tus clientes.")

    with c4:
        st.markdown("#### 🏆 Top 5 Productos Estrella")
        if not df_filtrado.empty:
            top_prod = (
                df_filtrado.groupby("producto")["cantidad"]
                .sum()
                .reset_index()
                .sort_values(by="cantidad", ascending=False)
                .head(5)
            )
            bar_prod = (
                alt.Chart(top_prod)
                .mark_bar(
                    color="#28a745", cornerRadiusTopLeft=5, cornerRadiusTopRight=5
                )
                .encode(
                    x=alt.X(
                        "producto",
                        sort="-y",
                        title="Producto",
                        axis=alt.Axis(labelAngle=-45),
                    ),
                    y=alt.Y("cantidad", title="Cajas Vendidas"),
                )
            )
            txt_prod = bar_prod.mark_text(
                align="center", baseline="bottom", dy=-5, fontSize=13, fontWeight="bold"
            ).encode(text=alt.Text("cantidad:Q", format=",.0f"))
            st.altair_chart(bar_prod + txt_prod, use_container_width=True)
        else:
            st.info("Sin datos de productos vendidos.")


# ==============================================================================
# BLOQUE 6: MENÚ LATERAL Y NAVEGACIÓN
# ==============================================================================
st.sidebar.title("📦 Fuxion Cloud OS")
st.sidebar.write("`Versión Comercial`")
st.sidebar.write("---")

if st.sidebar.checkbox("Activar modo Admin"):
    admin.mostrar_panel_admin(supabase)

menu_seleccionado = st.sidebar.radio(
    "Módulos del Sistema:",
    [
        "📊 Dashboard General",
        "🏆 Calificación PRO-LEV X",
        "💰 Comisiones Fuxion (Auto)",
        "💰 Control de Abonos",
        "📦 Kardex / Inventario",
        "📝 Libro de Movimientos",
        "📥 Entradas (Compras)",
        "🛒 Salidas (Ventas)",
        "⚙️ Gestión de Productos",
        "👥 Base de Datos Clientes",
        "👩‍💼 Gestión de Asesores",
        "💸 Registro de Gastos",
    ],
)

# ==============================================================================
# BLOQUE 7: RUTEADOR DE INTERFACES RESTANTES
# ==============================================================================
if menu_seleccionado == "📊 Dashboard General":
    render_dashboard()

elif menu_seleccionado == "🏆 Calificación PRO-LEV X":
    st.title("🏆 Calificación Plan PRO-LEV X (Ventana Móvil PV4)")
    st.write(
        "Auditoría de Volumen Personal y Arrastre exacto de **Compras Propias y Plataforma a FuXion** en base a las últimas 4 semanas."
    )
    if t_semanas:
        df_sem_full = pd.DataFrame(t_semanas)
        col_nom = (
            "nombre_semana"
            if "nombre_semana" in df_sem_full.columns
            else ("semana" if "semana" in df_sem_full.columns else None)
        )
        if col_nom:
            df_sem_full["num_sem"] = df_sem_full[col_nom].apply(extraer_numero_semana)
            df_sem_full = df_sem_full.sort_values(by="num_sem").reset_index(drop=True)
            lista_semanas_ordenadas = [
                str(x).strip() for x in df_sem_full[col_nom].tolist()
            ]
            idx_semana_sel = 0
            for i, val in enumerate(lista_semanas_ordenadas):
                if val.upper() == semana_actual_sistema.upper():
                    idx_semana_sel = i
                    break
            semana_seleccionada = st.selectbox(
                "Seleccione la Semana de Evaluación",
                lista_semanas_ordenadas,
                index=idx_semana_sel,
            )
            sem_num_actual = extraer_numero_semana(semana_seleccionada)
            pv_compras_num = obtener_pv_unificado_semanas()
            filas_historicas = []
            rango_matematico = range(sem_num_actual - 3, sem_num_actual + 1)
            acumulado = 0.0
            for w in rango_matematico:
                if w <= 0:
                    continue
                pv_semana = pv_compras_num.get(w, 0.0)
                arrastre = acumulado
                total_pv = arrastre + pv_semana
                porcentaje = calcular_porcentaje_fuxion(total_pv)
                p_match = df_sem_full[df_sem_full["num_sem"] == w]
                per_nom = (
                    p_match["periodo"].iloc[0]
                    if not p_match.empty and "periodo" in p_match.columns
                    else "N/A"
                )
                filas_historicas.append(
                    {
                        "Periodo": per_nom,
                        "Semana": f"Semana {w}",
                        "PV": pv_semana,
                        "Arrastre": arrastre,
                        "Total PV": total_pv,
                        "%": porcentaje,
                    }
                )
                acumulado = total_pv

            df_mostrar = pd.DataFrame(filas_historicas)
            st.markdown(
                f"### 📊 Ventana Móvil de Calificación hasta **{semana_seleccionada}**"
            )
            st.dataframe(
                df_mostrar.style.format(
                    {"PV": "{:,.0f}", "Arrastre": "{:,.0f}", "Total PV": "{:,.0f}"}
                ),
                use_container_width=True,
            )

            if not df_mostrar.empty:
                pv_actual = df_mostrar.iloc[-1]["Total PV"]
                pct_actual = df_mostrar.iloc[-1]["%"]
                if pv_actual < 60:
                    faltante, prox = 60 - pv_actual, "20%"
                elif pv_actual < 100:
                    faltante, prox = 100 - pv_actual, "25%"
                elif pv_actual < 300:
                    faltante, prox = 300 - pv_actual, "30%"
                elif pv_actual < 500:
                    faltante, prox = 500 - pv_actual, "40%"
                elif pv_actual < 800:
                    faltante, prox = 800 - pv_actual, "50%"
                else:
                    faltante, prox = 0, "MAX"

                msj = (
                    "🌟 <b>¡Felicidades!</b> Has alcanzado el nivel MÁXIMO de descuento en Fuxion (50%)."
                    if prox == "MAX"
                    else f"🚀 Te hacen falta <b style='color: #cc0000; font-size: 18px;'>{faltante:,.0f} PV</b> para alcanzar el siguiente nivel del <b style='color: #cc0000; font-size: 18px;'>{prox}</b> de descuento."
                )

                st.markdown(
                    f"""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #00ADEF; border: 1px solid #e0e0e0; margin-top: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);">
                    <h4 style="color: #1E2B58; margin-top: 0; margin-bottom: 12px; font-size: 18px;">🎯 Rastreador de Metas ({semana_seleccionada})</h4>
                    <ul style="list-style-type: none; padding-left: 0; font-size: 16px; color: #333;">
                        <li style="margin-bottom: 8px;">🔹 <b>PV TOTAL ACUMULADO (PV4):</b> <span style="font-weight: bold; color: #1E2B58;">{pv_actual:,.0f} PV</span></li>
                        <li style="margin-bottom: 8px;">🔹 <b>NIVEL DE DESCUENTO ACTUAL:</b> <span style="color: #00ADEF; font-weight: bold; font-size: 18px;">{pct_actual}</span></li>
                        <li style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #ccc;">{msj}</li>
                    </ul>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("### 📝 Desglose Exacto de Puntos en esta Ventana")
            semanas_evaluadas = list(rango_matematico)
            desglose = []
            for ent in t_entradas:
                w = extraer_numero_semana(ent.get("semana", ""))
                if w in semanas_evaluadas:
                    desglose.append(
                        {
                            "Fecha": ent.get("fecha"),
                            "Semana": f"Sem {w}",
                            "Operación": "Compra Fábrica",
                            "Producto": ent.get("producto"),
                            "Cant.": ent.get("cantidad"),
                            "PV Aportado": float(ent.get("puntos_pv") or 0.0),
                        }
                    )
            for v in t_ventas:
                if v.get("medio_pago") in [
                    "Plataforma Fuxion",
                    "Pago Directo a Fuxion (Plataforma)",
                ]:
                    _, v_sem = obtener_periodo_semana_de_fecha(v.get("fecha"))
                    w = extraer_numero_semana(v_sem)
                    if w in semanas_evaluadas:
                        desglose.append(
                            {
                                "Fecha": v.get("fecha"),
                                "Semana": f"Sem {w}",
                                "Operación": "Venta Plataforma",
                                "Producto": v.get("producto"),
                                "Cant.": v.get("cantidad"),
                                "PV Aportado": float(v.get("puntos_pv") or 0.0),
                            }
                        )

            if desglose:
                df_desglose = pd.DataFrame(desglose).sort_values(by=["Semana", "Fecha"])
                st.dataframe(df_desglose, use_container_width=True)
            else:
                st.info(
                    "No hay compras ni ventas de plataforma registradas en estas 4 semanas."
                )
    else:
        st.info("Por favor carga el calendario oficial en la tabla de Supabase.")

elif menu_seleccionado == "💰 Comisiones Fuxion (Auto)":
    st.title("💰 Comisiones Fuxion (Motor Automático PRO-LEV X)")
    st.markdown(
        """
    <div style="background-color: #E0F7FA; padding: 15px; border-radius: 8px; border-left: 5px solid #00ADEF; margin-bottom: 20px;">
    El sistema suma el <b>Total del Precio Público vendido en la Semana</b> (Tus Compras a Fábrica + Ventas Plataforma), calcula la <b>Base sin IVA (/ 1.19)</b>, y le aplica tu Escala de Descuento (PV4) para obtener el <b>Bono V.D. Exacto</b>.<br>
    Luego aplica: <b>1. Retefuente (10%) | 2. ReteICA (0.69%) | 3. Comisión Bancaria ($1,563)</b>.
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 RECALCULAR COMISIONES AHORA", use_container_width=True):
        st.rerun()

    with st.expander(
        "➕ Añadir Bono Familia / Liderazgo a una Semana Específica", expanded=True
    ):
        col_b1, col_b2, col_b3, col_b4 = st.columns([2, 2, 2, 2])
        lista_periodos, lista_semanas = [], []
        if t_semanas:
            df_sem = pd.DataFrame(t_semanas)
            if "periodo" in df_sem.columns:
                lista_periodos = df_sem["periodo"].dropna().unique().tolist()
            col_nom = (
                "nombre_semana"
                if "nombre_semana" in df_sem.columns
                else ("semana" if "semana" in df_sem.columns else None)
            )
            if col_nom:
                lista_semanas = df_sem[col_nom].dropna().unique().tolist()
        with col_b1:
            b_per = st.selectbox(
                "Período", lista_periodos if lista_periodos else ["Periodo 1"]
            )
        with col_b2:
            b_sem = st.selectbox(
                "Semana", lista_semanas if lista_semanas else ["Semana 1"]
            )
        with col_b3:
            b_monto = st.number_input(
                "Valor Bono Familia ($)", min_value=0.0, step=10000.0
            )
        with col_b4:
            st.write("")
            st.write("")
            if st.button("💾 Guardar Bono y Recalcular"):
                try:
                    b_exist = (
                        supabase.table("bonos_extras")
                        .select("id")
                        .eq("periodo", b_per)
                        .eq("semana", b_sem)
                        .eq("empresa_id", id_seguro)
                        .execute()
                        .data
                    )
                    if b_exist:
                        supabase.table("bonos_extras").update(
                            {"bono_familia": b_monto}
                        ).eq("id", b_exist[0]["id"]).execute()
                    else:
                        supabase.table("bonos_extras").insert(
                            {
                                "periodo": b_per,
                                "semana": b_sem,
                                "bono_familia": b_monto,
                                "empresa_id": id_seguro,
                            }
                        ).execute()
                    st.success("Bono guardado exitosamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error en BD: {e}")

    st.markdown("### 📊 Historial Automatizado de Pagos Fuxion")
    reporte = []
    if t_semanas:
        pv_compras_num = obtener_pv_unificado_semanas()
        semanas_activas = set(pv_compras_num.keys())
        for b in t_bonos:
            w = extraer_numero_semana(b.get("semana", ""))
            if w > 0:
                semanas_activas.add(w)
        lista_semanas_evaluar = sorted(list(semanas_activas))
        df_sem_full = pd.DataFrame(t_semanas)
        col_nom = (
            "nombre_semana"
            if "nombre_semana" in df_sem_full.columns
            else ("semana" if "semana" in df_sem_full.columns else None)
        )
        if col_nom:
            df_sem_full["num_sem"] = df_sem_full[col_nom].apply(extraer_numero_semana)
            for sem_num in lista_semanas_evaluar:
                pv_semana = pv_compras_num.get(sem_num, 0.0)
                pv4 = sum(
                    pv_compras_num.get(w, 0.0) for w in range(sem_num - 3, sem_num + 1)
                )
                escala_str = calcular_porcentaje_fuxion(pv4)
                porcentaje_dcto = float(escala_str.replace("%", "")) / 100.0
                precio_semana = 0.0
                for ent in t_entradas:
                    if extraer_numero_semana(ent.get("semana", "")) == sem_num:
                        precio_semana += buscar_x_pub(ent.get("producto")) * float(
                            ent.get("cantidad") or 0.0
                        )
                for v in t_ventas:
                    if v.get("medio_pago") in [
                        "Plataforma Fuxion",
                        "Pago Directo a Fuxion (Plataforma)",
                    ]:
                        _, v_sem = obtener_periodo_semana_de_fecha(v.get("fecha"))
                        if extraer_numero_semana(v_sem) == sem_num:
                            precio_semana += buscar_x_pub(v.get("producto")) * float(
                                v.get("cantidad") or 0.0
                            )

                base_sin_iva = precio_semana / 1.19
                bono_vd = base_sin_iva * porcentaje_dcto
                bono_fam = sum(
                    float(b.get("bono_familia") or 0.0)
                    for b in t_bonos
                    if extraer_numero_semana(b.get("semana", "")) == sem_num
                )
                comision_bruta = bono_vd + bono_fam
                retefuente = comision_bruta * 0.10 if comision_bruta > 0 else 0
                reteica = comision_bruta * 0.0069 if comision_bruta > 0 else 0
                bancaria = 1563 if comision_bruta > 0 else 0
                neto = max(0, comision_bruta - retefuente - reteica - bancaria)

                per_nom = "N/A"
                p_match = df_sem_full[df_sem_full["num_sem"] == sem_num]
                if not p_match.empty and "periodo" in p_match.columns:
                    per_nom = p_match["periodo"].iloc[0]
                if bono_vd > 0 or bono_fam > 0 or pv_semana > 0:
                    reporte.append(
                        {
                            "Período": per_nom,
                            "Semana": f"Semana {sem_num}",
                            "PV Sem": int(pv_semana),
                            "Total PV4": int(pv4),
                            "% Escala": escala_str,
                            "Bono V.D.": bono_vd,
                            "Bono Fam.": bono_fam,
                            "Com. Bruta": comision_bruta,
                            "Retenciones": retefuente + reteica + bancaria,
                            "Neto a Cuenta": neto,
                        }
                    )
        reporte.reverse()

    if reporte:
        df_rep = pd.DataFrame(reporte)
        st.dataframe(
            df_rep.style.format(
                {
                    "Bono V.D.": "${:,.0f}",
                    "Bono Fam.": "${:,.0f}",
                    "Com. Bruta": "${:,.0f}",
                    "Retenciones": "${:,.0f}",
                    "Neto a Cuenta": "${:,.0f}",
                }
            ),
            use_container_width=True,
        )
    else:
        st.info(
            "No hay comisiones para mostrar. Registra compras para ganar PV y ventas en 'Plataforma Fuxion' para generar comisiones."
        )

elif menu_seleccionado == "💰 Control de Abonos":
    st.title("💰 Control de Cartera y Abonos de Clientes")
    if st.session_state.get("msg_abono"):
        st.success(st.session_state.msg_abono)
        st.session_state.msg_abono = None
    t_ab_lista, t_ab_crear = st.tabs(
        ["📋 Estado de Cuenta General", "➕ Registrar Abono / Pago"]
    )

    with t_ab_lista:
        if t_cli:
            cartera_data = []
            for cli in t_cli:
                nom_c = cli["nombre"]
                deuda_neta = calcular_saldo_cliente(nom_c)
                if deuda_neta > 0:
                    estado_cuenta = f"🔴 Debe ${deuda_neta:,.0f}"
                elif deuda_neta < 0:
                    estado_cuenta = f"🟢 Saldo a Favor: ${abs(deuda_neta):,.0f}"
                else:
                    estado_cuenta = "⚪ Al día"
                cartera_data.append(
                    {
                        "Cliente": nom_c,
                        "Celular": cli.get("celular", ""),
                        "Estado Financiero": estado_cuenta,
                    }
                )
            st.dataframe(pd.DataFrame(cartera_data), use_container_width=True)
        else:
            st.info("No hay clientes en el directorio.")

    with t_ab_crear:
        col_ab1, col_ab2 = st.columns(2)
        with col_ab1:
            cli_abono = st.selectbox(
                "Seleccione el Cliente", [""] + lista_cli, key=f"cb_ab_{lk}"
            )
            if cli_abono:
                saldo_en_vivo = calcular_saldo_cliente(cli_abono)
                if saldo_en_vivo > 0:
                    st.error(
                        f"💵 **Deuda actual de este cliente:** ${saldo_en_vivo:,.0f}"
                    )
                elif saldo_en_vivo < 0:
                    st.success(
                        f"💰 **Saldo a favor actual:** ${abs(saldo_en_vivo):,.0f}"
                    )
                else:
                    st.info("ℹ️ Este cliente no tiene deudas pendientes.")
        with col_ab2:
            f_abono = st.date_input(
                "Fecha del Abono", datetime.today(), key=f"f_ab_{lk}"
            )

        col_ab3, col_ab4 = st.columns(2)
        with col_ab3:
            monto_abono = st.number_input(
                "Monto Recibido ($)", min_value=0.0, step=5000.0, key=f"m_ab_{lk}"
            )
        with col_ab4:
            medio_abono = st.selectbox(
                "Medio de Recaudo",
                [
                    "Efectivo",
                    "Llave",
                    "Crédito",
                    "Addi",
                    "Sistecrédito",
                    "Bolt",
                    "Plataforma Fuxion",
                    "Otros",
                ],
                key=f"med_ab_{lk}",
            )

        st.markdown('<br><div class="btn-principal">', unsafe_allow_html=True)
        if st.button("💾 Procesar y Registrar Abono"):
            if not cli_abono or monto_abono <= 0:
                st.error("Debe seleccionar un cliente y un monto válido.")
            else:
                try:
                    supabase.table("abonos").insert(
                        {
                            "fecha": str(f_abono),
                            "cliente": cli_abono,
                            "monto": monto_abono,
                            "medio_pago": medio_abono,
                            "empresa_id": id_seguro,
                        }
                    ).execute()
                    st.session_state.limpiador += 1
                    st.session_state.msg_abono = f"¡Abono de ${monto_abono:,.0f} registrado con éxito para {cli_abono}!"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al conectar con la base de datos: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu_seleccionado == "📦 Kardex / Inventario":
    st.title("📦 Kardex Matemático en Tiempo Real")
    with st.expander(
        "🤝 Registrar Movimiento de Inventario / Préstamos y Entrega de Regalos",
        expanded=False,
    ):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            tipo_mov = st.selectbox(
                "Tipo de Movimiento",
                [
                    "Préstamo: Me prestan a mí (Suma)",
                    "Préstamo: Yo presto a compañero (Resta)",
                    "Cambio: Recibo de compañero (Suma)",
                    "Cambio: Entrego a compañero (Resta)",
                    "Regalo: Entrega a Asesor (Resta)",
                    "Consumo Personal (Resta)",
                ],
            )
            asesor_mov = st.selectbox("Compañero Asesor / Vendedora", [""] + lista_ase)
            if asesor_mov:
                _, _, saldo_pv_neto = calcular_puntos_vendedora(asesor_mov)
                st.write(
                    f"🏅 **Saldo PV de {asesor_mov}:** `{saldo_pv_neto} PV` disponibles."
                )
        with col_m2:
            prod_mov = st.selectbox("Producto", lista_prod)
            stock_ajustes = obtener_stock_actual(prod_mov)
            st.write(f"📊 **Cantidad en Existencia:** `{stock_ajustes}` cajas")
            cant_mov = st.number_input("Cantidad Cajas", min_value=1, step=1, value=1)

        if st.button("🤝 Registrar Movimiento"):
            if not asesor_mov or not prod_mov:
                st.warning("Selecciona Asesor y Producto.")
            else:
                marca_matematica = "SUMA" if "(Suma)" in tipo_mov else "RESTA"
                if marca_matematica == "RESTA" and cant_mov > stock_ajustes:
                    st.error(
                        f"🚨 ¡Stock Insuficiente! En bodega solo quedan {stock_ajustes} cajas."
                    )
                    st.stop()
                if tipo_mov == "Regalo: Entrega a Asesor (Resta)":
                    costo_en_puntos = cant_mov * 80
                    if costo_en_puntos > saldo_pv_neto:
                        st.error(
                            f"🚨 **¡Puntos Insuficientes!** {asesor_mov} necesita `{costo_en_puntos} PV`."
                        )
                        st.stop()
                supabase.table("inventario").insert(
                    {
                        "fecha": datetime.now().strftime("%Y-%m-%d"),
                        "producto": prod_mov,
                        "tipo_movimiento": marca_matematica,
                        "cantidad": cant_mov,
                        "asesor": asesor_mov,
                        "observacion": f"{tipo_mov}: {asesor_mov} (-{cant_mov * 80} PV)",
                        "empresa_id": id_seguro,
                    }
                ).execute()
                st.success("Movimiento registrado con éxito.")
                st.rerun()

    st.markdown("---")
    try:
        df_ent = (
            pd.DataFrame(t_entradas)
            if t_entradas
            else pd.DataFrame(columns=["producto", "cantidad"])
        )
        df_ven = (
            pd.DataFrame(t_ventas)
            if t_ventas
            else pd.DataFrame(columns=["producto", "cantidad"])
        )
        df_inv = (
            pd.DataFrame(t_inv)
            if t_inv
            else pd.DataFrame(columns=["producto", "cantidad", "tipo_movimiento"])
        )

        kardex_data = []
        for p in t_prod:
            n = p["nombre"]
            in_q = (
                df_ent[df_ent["producto"] == n]["cantidad"].sum()
                if not df_ent.empty
                else 0
            )
            if not df_inv.empty and "SUMA" in df_inv["tipo_movimiento"].values:
                in_q += df_inv[
                    (df_inv["producto"] == n)
                    & (df_inv["tipo_movimiento"].str.contains("SUMA"))
                ]["cantidad"].sum()
            out_q = (
                df_ven[df_ven["producto"] == n]["cantidad"].sum()
                if not df_ven.empty
                else 0
            )
            if not df_inv.empty and "RESTA" in df_inv["tipo_movimiento"].values:
                out_q += df_inv[
                    (df_inv["producto"] == n)
                    & (df_inv["tipo_movimiento"].str.contains("RESTA"))
                ]["cantidad"].sum()
            kardex_data.append(
                {
                    "Producto": n,
                    "Totales (+)": int(in_q),
                    "Totales (-)": int(out_q),
                    "Stock Real": int(in_q - out_q),
                }
            )

        df_kardex = pd.DataFrame(kardex_data)
        total_cajas_bodega = df_kardex["Stock Real"].sum()

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            st.markdown(
                f"### 📦 **Total Cajas en Bodega:** `{int(total_cajas_bodega)}`"
            )
        with col_t2:
            ocultar_cero = st.checkbox("Ocultar productos sin stock", value=True)

        if ocultar_cero:
            df_kardex = df_kardex[df_kardex["Stock Real"] > 0]
        st.dataframe(
            df_kardex.style.apply(
                lambda r: (
                    (
                        ["background-color: #ff4d4d; color: white"]
                        if r["Stock Real"] <= 0
                        else [""]
                    )
                    * len(r)
                ),
                axis=1,
            ),
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Error: {e}")

elif menu_seleccionado == "📝 Libro de Movimientos":
    st.title("📝 Auditoría de Movimientos")
    tab_ven, tab_ent, tab_inv_tab, tab_gas, tab_ab = st.tabs(
        [
            "🛒 Ventas",
            "📥 Compras",
            "🤝 Préstamos/Ajustes",
            "💸 Gastos",
            "💰 Abonos Recibidos",
        ]
    )
    with tab_inv_tab:
        if t_inv:
            df_i = pd.DataFrame(t_inv)
            cols_to_show = [
                "fecha",
                "tipo_movimiento",
                "producto",
                "cantidad",
                "observacion",
                "asesor",
            ]
            df_i = df_i[[c for c in cols_to_show if c in df_i.columns]]
            df_i.columns = [
                "Fecha",
                "Tipo",
                "Producto",
                "Cantidad",
                "Observación",
                "Asesor / Vendedora",
            ]
            st.dataframe(df_i, use_container_width=True)
        else:
            st.info("No hay préstamos o ajustes registrados.")

    with tab_ven:
        if t_ventas:
            df_v = pd.DataFrame(t_ventas)
            cols_to_show = [
                "fecha",
                "cliente",
                "asesor",
                "producto",
                "cantidad",
                "precio_venta",
                "medio_pago",
                "id_factura_venta",
                "puntos_pv",
                "tipo_destinatario",
            ]
            df_v = df_v[[c for c in cols_to_show if c in df_v.columns]]
            df_v = df_v.rename(
                columns={
                    "fecha": "Fecha",
                    "cliente": "Cliente",
                    "asesor": "Asesor",
                    "producto": "Producto",
                    "cantidad": "Cant.",
                    "precio_venta": "Cobro ($)",
                    "medio_pago": "Medio Pago",
                    "id_factura_venta": "N° Factura",
                    "puntos_pv": "PV Ganados",
                    "tipo_destinatario": "Destinatario",
                }
            )
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("No hay facturas de venta registradas.")

    with tab_ent:
        if t_entradas:
            df_e = pd.DataFrame(t_entradas)
            cols_to_show = [
                "fecha",
                "numero_pedido",
                "semana",
                "producto",
                "cantidad",
                "precio_costo_total",
                "puntos_pv",
            ]
            df_e = df_e[[c for c in cols_to_show if c in df_e.columns]]
            df_e.columns = [
                "Fecha Compra",
                "N° Pedido",
                "Semana",
                "Producto",
                "Cant. Cajas",
                "Costo Invertido ($)",
                "PV Aportados",
            ]
            st.dataframe(df_e, use_container_width=True)
        else:
            st.info("No hay ingresos a bodega registrados.")

    with tab_gas:
        if t_gastos:
            df_g = pd.DataFrame(t_gastos)
            cols_to_show = [
                c for c in ["fecha", "concepto", "monto"] if c in df_g.columns
            ]
            if cols_to_show:
                df_g = df_g[cols_to_show]
                df_g.columns = ["Fecha", "Concepto", "Monto ($)"]
            st.dataframe(df_g, use_container_width=True)
        else:
            st.info("No hay gastos registrados.")

    with tab_ab:
        if t_abonos:
            df_ab_tab = pd.DataFrame(t_abonos)
            cols_to_show = [
                c
                for c in ["fecha", "cliente", "monto", "medio_pago"]
                if c in df_ab_tab.columns
            ]
            if cols_to_show:
                df_ab_tab = df_ab_tab[cols_to_show]
                df_ab_tab.columns = [
                    "Fecha Abono",
                    "Cliente",
                    "Monto Recibido ($)",
                    "Medio de Pago",
                ]
            st.dataframe(df_ab_tab, use_container_width=True)
        else:
            st.info("No se han registrado abonos en el sistema aún.")

elif menu_seleccionado == "📥 Entradas (Compras)":
    st.title("📥 Registro de Pedidos a Fábrica")
    if st.session_state.get("msg_entrada"):
        st.success(st.session_state.msg_entrada)
        st.session_state.msg_entrada = None

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        f_pedido = st.date_input("Fecha de Compra", datetime.today(), key=f"f_ped_{lk}")
        sem_list = []
        if t_semanas:
            col_nom = (
                "nombre_semana"
                if "nombre_semana" in t_semanas[0]
                else ("semana" if "semana" in t_semanas[0] else None)
            )
            if col_nom:
                sem_list = [str(s.get(col_nom, "")).strip() for s in t_semanas]
        if not sem_list:
            sem_list = ["Semana 1", "Semana 2", "Semana 3", "Semana 4"]
        idx_sem = 0
        for i, val in enumerate(sem_list):
            if val.upper() == semana_actual_sistema.upper():
                idx_sem = i
                break
        sem = st.selectbox(
            "Semana Fuxion (Autodetectada)", sem_list, index=idx_sem, key=f"sem_{lk}"
        )
    with col_in2:
        num_ped = st.text_input("N° de Orden / Pedido Fuxion", key=f"n_ped_{lk}")
        modalidad = st.selectbox("Modalidad", ["Normal", "Autoenvío"], key=f"mod_{lk}")

    col_a, col_c = st.columns(2)
    with col_a:
        asesor = st.selectbox("Asesor (Dueño PV)", [""] + lista_ase, key=f"ase_{lk}")
    with col_c:
        cliente = st.selectbox("Cliente Destino", [""] + lista_cli, key=f"cli_{lk}")

    st.markdown("---")
    col_l1, col_l2, col_l3 = st.columns([3, 1, 1])
    with col_l1:
        prod_ped = st.selectbox(
            "Seleccionar Producto", lista_prod, key=f"e_sel_prod_{lk}"
        )
        stock_compras = obtener_stock_actual(prod_ped)
        st.write(f"📊 **Stock Actual en Bodega:** `{stock_compras}` cajas")
    with col_l2:
        cant_ped = st.number_input(
            "Cantidad", min_value=1, step=1, value=1, key=f"e_sel_cant_{lk}"
        )
    with col_l3:
        es_regalo = st.checkbox("¿Es Regalo?", key=f"reg_{lk}")

    precio_u = 0 if es_regalo else buscar_x_pub(prod_ped)
    total_linea = precio_u * cant_ped
    prod_data = next((p for p in t_prod if p["nombre"] == prod_ped), {})
    pv_unit = 0 if es_regalo else int(prod_data.get("puntos_pv", 0))
    st.metric(f"Total línea (Precio Pub: ${precio_u:,.0f})", f"${total_linea:,.0f}")

    if st.button("➕ Añadir a Lista"):
        st.session_state.carrito_entradas.append(
            {
                "Producto": prod_ped,
                "Cantidad": cant_ped,
                "PV Unitario": pv_unit,
                "¿Es Regalo?": "SI" if es_regalo else "NO",
                "Total": total_linea,
            }
        )
        st.rerun()

    if st.session_state.carrito_entradas:
        st.markdown("### 📦 Resumen del Pedido")
        enc_c1, enc_c2, enc_c3, enc_c4, enc_c5, enc_c6 = st.columns([3, 1, 2, 2, 2, 1])
        with enc_c1:
            st.markdown(
                "<div class='header-tabla'>Producto</div>", unsafe_allow_html=True
            )
        with enc_c2:
            st.markdown("<div class='header-tabla'>Cant.</div>", unsafe_allow_html=True)
        with enc_c3:
            st.markdown(
                "<div class='header-tabla'>Puntos (PV)</div>", unsafe_allow_html=True
            )
        with enc_c4:
            st.markdown(
                "<div class='header-tabla'>¿Regalo?</div>", unsafe_allow_html=True
            )
        with enc_c5:
            st.markdown(
                "<div class='header-tabla'>Costo Línea</div>", unsafe_allow_html=True
            )
        with enc_c6:
            st.markdown(
                "<div class='header-tabla'>Acción</div>", unsafe_allow_html=True
            )

        for i, item in enumerate(st.session_state.carrito_entradas):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 1, 2, 2, 2, 1])
            with c1:
                st.write(f"📦 {item['Producto']}")
            with c2:
                st.write(f"{item['Cantidad']}")
            with c3:
                st.write(f"**{item['PV Unitario'] * item['Cantidad']} PV**")
            with c4:
                st.write(item["¿Es Regalo?"])
            with c5:
                st.write(f"${item['Total']:,.0f}")
            with c6:
                if st.button("❌", key=f"del_e_{i}_{lk}"):
                    st.session_state.carrito_entradas.pop(i)
                    st.rerun()
        st.markdown("---")
        subtotal_inversion = sum(
            item["Total"] for item in st.session_state.carrito_entradas
        )
        total_pv_compra = sum(
            item["PV Unitario"] * item["Cantidad"]
            for item in st.session_state.carrito_entradas
        )
        num_productos = len(st.session_state.carrito_entradas)
        valor_flete = 16600 if modalidad == "Autoenvío" else 0
        flete_por_producto = valor_flete / num_productos if num_productos > 0 else 0
        gran_total = subtotal_inversion + valor_flete

        st.info(
            f"**Subtotal:** ${subtotal_inversion:,.0f} | **Flete Total:** ${valor_flete:,.0f} | **PUNTOS A GANAR PRO-LEV X:** {total_pv_compra} PV"
        )
        st.subheader(f"💰 Inversión Total: ${gran_total:,.0f}")
        col_f1, col_f2 = st.columns([1, 4])
        with col_f1:
            if st.button("🗑️ Vaciar Lista", key=f"vac_e_{lk}"):
                st.session_state.carrito_entradas = []
                st.rerun()
        with col_f2:
            st.markdown('<div class="btn-principal">', unsafe_allow_html=True)
            if st.button("✅ Registrar Todo en Bodega"):
                try:
                    data_to_insert = [
                        {
                            "fecha": str(f_pedido),
                            "numero_pedido": num_ped,
                            "semana": sem,
                            "producto": i["Producto"],
                            "cantidad": i["Cantidad"],
                            "precio_costo_total": i["Total"]
                            + (flete_por_producto * i["Cantidad"]),
                            "puntos_pv": i["PV Unitario"] * i["Cantidad"],
                            "empresa_id": id_seguro,  # NUEVO - PARA ENLAZAR CON EL CLIENTE
                        }
                        for i in st.session_state.carrito_entradas
                    ]
                    supabase.table("entradas").insert(data_to_insert).execute()
                    st.session_state.carrito_entradas = []
                    st.success(
                        "¡Pedido registrado exitosamente con sus PV de calificación!"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

elif menu_seleccionado == "🛒 Salidas (Ventas)":
    st.title("🛒 Terminal de Ventas POS")
    n_factura = generar_siguiente_factura()

    if st.session_state.get("msg_ok"):
        st.success(st.session_state.msg_ok)
        st.balloons()
        if "ultima_factura" in st.session_state:
            uf = st.session_state.ultima_factura
            color_saldo = "#ff4d4d" if uf["saldo_pendiente"] > 0 else "#00cc00"
            texto_saldo = (
                f"ATENCIÓN: Saldo de Deuda Total Pendiente: ${uf['saldo_pendiente']:,.0f}"
                if uf["saldo_pendiente"] > 0
                else "Sin deudas pendientes (A Paz y Salvo)"
            )

            st.markdown(
                f"""
            <div style="background-color: #ffffff; padding: 25px; border-radius: 8px; border: 2px dashed #1E2B58; max-width: 550px; margin: 0 auto; font-family: 'Courier New', monospace; box-shadow: 2px 2px 15px rgba(0,0,0,0.08); color: #333333;">
                <div style="text-align: center; font-weight: bold; font-size: 22px; color: #1E2B58; letter-spacing: 1px;">📦 FUXION CLOUD OS</div>
                <div style="text-align: center; font-size: 13px; margin-bottom: 12px; color: #555555;">SISTEMA COMERCIAL DE DESPACHOS</div>
                <div style="border-top: 1px dashed #1E2B58; margin: 10px 0;"></div>
                <table style="width: 100%; font-size: 14px;">
                    <tr><td><b>N° COMPROBANTE:</b></td><td style="text-align: right;">{uf["n_factura"]}</td></tr>
                    <tr><td><b>FECHA VENTA:</b></td><td style="text-align: right;">{uf["fecha"]}</td></tr>
                    <tr><td><b>CLIENTE FINAL:</b></td><td style="text-align: right;">{uf["cliente"]}</td></tr>
                    <tr><td><b>DESTINATARIO:</b></td><td style="text-align: right;">{uf["tipo_destinatario"]}</td></tr>
                    <tr><td><b>ASESOR DUEÑO:</b></td><td style="text-align: right;">{uf["asesor"]}</td></tr>
                    <tr><td><b>MEDIO DE PAGO:</b></td><td style="text-align: right;">{uf["medio_pago"]}</td></tr>
                </table>
                <div style="border-top: 1px dashed #1E2B58; margin: 12px 0;"></div>
                <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
                    <tr style="border-bottom: 1px dashed #333;"><th style="text-align: left; padding-bottom: 5px;">CANT</th><th style="text-align: left; padding-bottom: 5px;">PRODUCTO (PLAN)</th><th style="text-align: right; padding-bottom: 5px;">TOTAL</th></tr>
            """,
                unsafe_allow_html=True,
            )

            for item in uf["items"]:
                st.markdown(
                    f"""<tr><td>{item["Cantidad"]}</td><td>{item["Producto"]}<br><small style="color:#666;">Desc: {item["Plan"]} | {item["PV Linea"]} PV</small></td><td style="text-align: right;">${item["Total Cobrado"]:,.0f}</td></tr>""",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                </table>
                <div style="border-top: 1px solid #1E2B58; margin: 12px 0;"></div>
                <div style="text-align: right; font-size: 14px;">
                    <p style="margin: 2px 0;"><b>SUBTOTAL BASE:</b> ${uf["subtotal"]:,.0f}</p>
                    <p style="margin: 2px 0; color: #cc0000;"><b>DESCUENTO APLICADO:</b> -${uf["descuento"]:,.0f}</p>
                    <p style="margin: 2px 0; color: #00ADEF;"><b>PUNTOS DE LA VENTA:</b> {uf["total_pv"]} PV</p>
                    <h3 style="margin: 5px 0; color: #1E2B58; font-size: 20px;">TOTAL PAGADO: ${uf["total"]:,.0f}</h3>
                </div>
                <div style="border-top: 1px dashed #1E2B58; margin: 12px 0;"></div>
                <div style="text-align: center; font-size: 14px; background-color: #f4f6f9; padding: 12px; border-radius: 6px; border: 1px solid #ddd;">
                    <b style="color: #333;">ESTADO DE CUENTA (HISTÓRICO)</b><br><span style="{color_saldo}">{texto_saldo}</span>
                </div>
                <div style="text-align: center; font-weight: bold; margin-top: 15px; color: #00ADEF; font-size: 14px;">🚀 ¡DESPACHO REGISTRADO EXITOSAMENTE! 🚀</div>
            </div><br>
            """,
                unsafe_allow_html=True,
            )
        st.session_state.msg_ok = None

    st.markdown("### 1. Datos de la Factura")
    col1_1, col1_2, col1_3 = st.columns(3)
    with col1_1:
        st.text_input(
            "N° Factura (Automático)",
            value=n_factura,
            disabled=True,
            key=f"v_fact_num_{lk}",
        )
        cliente = st.selectbox("Cliente Final", lista_cli, key=f"v_cli_{lk}")
    with col1_2:
        fecha_venta = st.date_input("Fecha", datetime.today(), key=f"v_fech_{lk}")
        tipo_destinatario = st.selectbox(
            "Tipo de Destinatario",
            ["Cliente real", "Vendedora", "Cliente Plataforma"],
            key=f"v_tipo_dest_{lk}",
        )
    with col1_3:
        asesor = st.selectbox("Vendedor / Asesor", lista_ase, key=f"v_ase_{lk}")
        medio_pago = st.selectbox(
            "Medio de Pago",
            [
                "Efectivo",
                "Llave",
                "Crédito",
                "Addi",
                "Sistecrédito",
                "Bolt",
                "Plataforma Fuxion",
                "Otros",
            ],
            key=f"v_pag_{lk}",
        )

    if asesor:
        ganados, quemados, netos = calcular_puntos_vendedora(asesor)
        st.info(
            f"🏅 **Auditoría PV de {asesor}:** Acumulados Históricos: `{ganados} PV` | Descontados por Regalos: `{quemados} PV` | **Saldo Neto Actual: `{netos} PV`**"
        )

    st.markdown("---")
    st.markdown("### 2. Agregar Productos")
    col_p1, col_p2, col_p3, col_p4, col_p5, col_p6 = st.columns([3, 1, 2, 1.5, 2, 1])
    with col_p1:
        producto = st.selectbox(
            "Seleccione Producto", lista_prod, key=f"v_sel_prod_{plk}"
        )
        stock_db = obtener_stock_actual(producto)
        en_carrito = sum(
            item["Cantidad"]
            for item in st.session_state.carrito_ventas
            if item["Producto"] == producto
        )
        stock_real_disponible = stock_db - en_carrito
        st.write(f"📊 **Stock Disponible:** `{stock_real_disponible}` cajas")
    with col_p2:
        cantidad = st.number_input(
            "Cant.", min_value=1, step=1, value=1, key=f"v_sel_cant_{plk}"
        )
    with col_p3:
        dcto_seleccionado = st.selectbox(
            "Plan de Descuento",
            ["0%", "20%", "25%", "30%", "40%", "50%", "Gana por Puntos (80 PV)"],
            key=f"v_sel_dcto_{plk}",
        )
    with col_p4:
        dcto_especial = st.number_input(
            "Dcto Extra p/Caja ($)",
            min_value=0.0,
            step=100.0,
            value=0.0,
            key=f"v_dcto_esp_{plk}",
        )
    with col_p5:
        precio_publico_u = buscar_x_pub(producto)
        prod_data = next((p for p in t_prod if p["nombre"] == producto), {})
        pv_caja_base = int(prod_data.get("puntos_pv" or 0) if prod_data else 0)

        if dcto_seleccionado == "Gana por Puntos (80 PV)":
            precio_con_descuento_u = precio_publico_u
        else:
            porcentaje_dcto = float(dcto_seleccionado.replace("%", "")) / 100.0
            base_sin_iva = precio_publico_u / 1.19
            monto_descuento_porcentual = base_sin_iva * porcentaje_dcto
            precio_con_descuento_u = precio_publico_u - monto_descuento_porcentual

        precio_final_u = max(0.0, precio_con_descuento_u - dcto_especial)
        precio_calculado_total = precio_final_u * cantidad
        total_pv_linea = pv_caja_base * cantidad
        st.metric(
            label=f"Costo Caja: ${precio_final_u:,.0f}",
            value=f"${precio_calculado_total:,.0f}",
        )
    with col_p6:
        st.write("")
        st.write("")
        if st.button("➕ Añadir"):
            if cantidad > stock_real_disponible:
                st.error(f"🚨 ¡Stock insuficiente!")
            else:
                st.session_state.carrito_ventas.append(
                    {
                        "Producto": producto,
                        "Cantidad": cantidad,
                        "Plan": dcto_seleccionado,
                        "Dcto Fijo": dcto_especial,
                        "Precio Publico Base": precio_publico_u,
                        "Total Cobrado": precio_calculado_total,
                        "PV Linea": total_pv_linea,
                    }
                )
                st.session_state.prod_limpiador += 1
                st.rerun()

    if st.session_state.carrito_ventas:
        st.markdown("### 3. Resumen de Venta Actual")
        enc_v1, enc_v2, enc_v3, enc_v4, enc_v5 = st.columns([4, 2, 2, 2, 1])
        with enc_v1:
            st.markdown(
                "<div class='header-tabla'>Producto (Plan)</div>",
                unsafe_allow_html=True,
            )
        with enc_v2:
            st.markdown(
                "<div class='header-tabla'>Cantidad</div>", unsafe_allow_html=True
            )
        with enc_v3:
            st.markdown(
                "<div class='header-tabla'>Puntos (PV)</div>", unsafe_allow_html=True
            )
        with enc_v4:
            st.markdown(
                "<div class='header-tabla'>Total Cobro</div>", unsafe_allow_html=True
            )
        with enc_v5:
            st.markdown(
                "<div class='header-tabla'>Acción</div>", unsafe_allow_html=True
            )

        for i, item in enumerate(st.session_state.carrito_ventas):
            c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 1])
            with c1:
                st.write(f"🛒 {item['Producto']} ({item['Plan']})")
            with c2:
                st.write(f"{item['Cantidad']} unidades")
            with c3:
                st.write(f"**{item['PV Linea']} PV**")
            with c4:
                st.write(f"${item['Total Cobrado']:,.0f}")
            with c5:
                if st.button("❌", key=f"del_v_{i}_{lk}"):
                    st.session_state.carrito_ventas.pop(i)
                    st.rerun()
        st.markdown("---")
        total_factura = sum(
            item["Total Cobrado"] for item in st.session_state.carrito_ventas
        )
        st.info(f"**Monto Total a Cobrar:** ${total_factura:,.2f}")
        col_f1, col_f2 = st.columns([1, 4])
        with col_f1:
            if st.button("🗑️ Vaciar Lista", key=f"vac_v_{lk}"):
                st.session_state.carrito_ventas = []
                st.rerun()
        with col_f2:
            st.markdown('<div class="btn-principal">', unsafe_allow_html=True)
            if st.button("✅ Confirmar y Registrar Factura"):
                try:
                    subtotal_venta = sum(
                        item["Precio Publico Base"] * item["Cantidad"]
                        for item in st.session_state.carrito_ventas
                    )
                    total_dcto = subtotal_venta - total_factura
                    total_pv_factura = sum(
                        item["PV Linea"] for item in st.session_state.carrito_ventas
                    )
                    deuda_historica = calcular_saldo_cliente(cliente)
                    deuda_actualizada = (
                        deuda_historica + total_factura
                        if medio_pago in ["Crédito", "Otros", "Addi", "Sistecrédito"]
                        else deuda_historica
                    )

                    st.session_state.ultima_factura = {
                        "n_factura": n_factura,
                        "fecha": str(fecha_venta),
                        "cliente": cliente,
                        "tipo_destinatario": tipo_destinatario,
                        "asesor": asesor,
                        "medio_pago": medio_pago,
                        "items": list(st.session_state.carrito_ventas),
                        "subtotal": subtotal_venta,
                        "descuento": total_dcto,
                        "total_pv": total_pv_factura,
                        "total": total_factura,
                        "saldo_pendiente": deuda_actualizada,
                    }

                    supabase.table("ventas").insert(
                        [
                            {
                                "fecha": str(fecha_venta),
                                "asesor": asesor,
                                "cliente": cliente,
                                "tipo_destinatario": tipo_destinatario,
                                "producto": i["Producto"],
                                "cantidad": i["Cantidad"],
                                "precio_venta": i["Total Cobrado"],
                                "medio_pago": medio_pago,
                                "id_factura_venta": n_factura,
                                "puntos_pv": i["PV Linea"],
                                "empresa_id": id_seguro,  # NUEVO - PARA ENLAZAR CON EL CLIENTE
                            }
                            for i in st.session_state.carrito_ventas
                        ]
                    ).execute()

                    st.session_state.carrito_ventas = []
                    st.session_state.limpiador += 1
                    st.session_state.prod_limpiador += 1
                    st.success("Factura registrada exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

elif menu_seleccionado == "⚙️ Gestión de Productos":
    st.title("⚙️ Catálogo Maestro de Productos")
    if st.session_state.get("msg_admin"):
        st.success(st.session_state.msg_admin)
        st.session_state.msg_admin = None
    t_crear, t_editar, t_lista = st.tabs(
        ["➕ Crear Producto", "✏️ Editar Producto", "📋 Ver Catálogo Completo"]
    )

    with t_crear:
        col1, col2 = st.columns(2)
        with col1:
            nom_p = st.text_input("Nombre del Producto", key=f"p_nom_{lk}")
            pres_p = st.selectbox(
                "Presentación",
                [
                    "Caja x 28 sticks",
                    "Caja x 14 sticks",
                    "Caja x 7 sticks",
                    "Frasco / Pote",
                    "Muestra Libre",
                ],
                key=f"p_pres_{lk}",
            )
            dia_p = st.number_input(
                "Días de Consumo Promedio",
                min_value=1,
                step=1,
                value=28,
                key=f"p_dia_{lk}",
            )
        with col2:
            pun_p = st.number_input(
                "Puntos de Volumen (PV)", min_value=0, step=1, key=f"p_pun_{lk}"
            )
            pre_p = st.number_input(
                "Precio Venta Público ($)",
                min_value=0.0,
                step=1000.0,
                key=f"p_pre_{lk}",
            )
        st.markdown('<br><div class="btn-principal">', unsafe_allow_html=True)
        if st.button("💾 Guardar Producto (Para Todos)"):
            if nom_p:
                supabase.table("productos").insert(
                    {
                        "nombre": nom_p,
                        "presentacion": pres_p,
                        "dias_consumo": dia_p,
                        "puntos_pv": pun_p,
                        "precio_pub": pre_p,
                    }
                ).execute()
                st.session_state.limpiador += 1
                st.session_state.msg_admin = (
                    f"¡Producto '{nom_p}' registrado con éxito!"
                )
                st.rerun()
            else:
                st.error("El nombre del producto es obligatorio.")
        st.markdown("</div>", unsafe_allow_html=True)

    with t_editar:
        if t_prod:
            p_edit = st.selectbox(
                "Seleccione el Producto", [p["nombre"] for p in t_prod]
            )
            dat_a = next((p for p in t_prod if p["nombre"] == p_edit), {})
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                n_pres = st.text_input(
                    "Presentación", value=dat_a.get("presentacion", "Caja x 28 sticks")
                )
                n_dia = st.number_input(
                    "Días de Cobertura",
                    value=int(dat_a.get("dias_consumo") or 28),
                    step=1,
                )
                n_pun = st.number_input(
                    "Puntos (PV)", value=int(dat_a.get("puntos_pv") or 0), step=1
                )
            with col_e2:
                n_pre = st.number_input(
                    "Precio Público ($)",
                    value=float(dat_a.get("precio_pub") or 0.0),
                    step=1000.0,
                )
            if st.button("💾 Aplicar Cambios"):
                supabase.table("productos").update(
                    {
                        "presentacion": n_pres,
                        "dias_consumo": n_dia,
                        "puntos_pv": n_pun,
                        "precio_pub": n_pre,
                    }
                ).eq("nombre", p_edit).execute()
                st.session_state.msg_admin = f"¡{p_edit} actualizado!"
                st.rerun()

    with t_lista:
        if t_prod:
            df_prod = pd.DataFrame(t_prod)[
                ["nombre", "presentacion", "puntos_pv", "precio_pub", "dias_consumo"]
            ]
            df_prod.columns = [
                "Nombre",
                "Presentación",
                "PV",
                "Venta ($)",
                "Días Consumo",
            ]
            st.dataframe(df_prod, use_container_width=True)

elif menu_seleccionado == "👥 Base de Datos Clientes":
    st.title("👥 Directorio de Clientes")
    if st.session_state.get("msg_cliente"):
        st.success(st.session_state.msg_cliente)
        st.session_state.msg_cliente = None
    t_cli_lista, t_cli_crear = st.tabs(
        ["📋 Lista de Clientes", "➕ Registrar Nuevo Cliente"]
    )

    with t_cli_lista:
        if t_cli:
            df_cli = pd.DataFrame(t_cli)[["nombre", "celular", "direccion"]]
            df_cli.columns = ["Nombre Completo", "Número Celular", "Zona / Dirección"]
            df_cli.fillna("", inplace=True)
            st.dataframe(df_cli, use_container_width=True)
        else:
            st.info("Aún no tienes clientes registrados.")

    with t_cli_crear:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            c_nombre = st.text_input("Nombre Completo del Cliente", key=f"c_nom_{lk}")
            c_celular = st.text_input("Número de Teléfono / Celular", key=f"c_cel_{lk}")
        with col_c2:
            c_direccion = st.text_input(
                "Dirección o Zona de Residencia", key=f"c_dir_{lk}"
            )
        st.markdown('<br><div class="btn-principal">', unsafe_allow_html=True)
        if st.button("💾 Guardar Cliente"):
            if c_nombre:
                nombre_formateado = c_nombre.strip().title()
                supabase.table("clientes").insert(
                    {
                        "nombre": nombre_formateado,
                        "celular": c_celular,
                        "direccion": c_direccion,
                        "empresa_id": id_seguro,  # NUEVO - PARA ENLAZAR CON EL CLIENTE
                    }
                ).execute()
                st.session_state.limpiador += 1
                st.session_state.msg_cliente = (
                    f"¡Cliente '{nombre_formateado}' guardado exitosamente!"
                )
                st.rerun()
            else:
                st.error("El nombre es obligatorio.")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu_seleccionado == "👩‍💼 Gestión de Asesores":
    st.title("👩‍💼 Directorio de Asesores / Vendedoras")
    if st.session_state.get("msg_ase"):
        st.success(st.session_state.msg_ase)
        st.session_state.msg_ase = None
    t_ase_lista, t_ase_crear = st.tabs(
        ["📋 Lista de Asesores y Puntos", "➕ Registrar Nuevo Asesor"]
    )

    with t_ase_lista:
        if t_ase:
            asesores_data = []
            for ase in t_ase:
                nombre = ase["nombre"]
                tel = ase.get("telefono", "")
                ganados, quemados, netos = calcular_puntos_vendedora(nombre)
                asesores_data.append(
                    {
                        "Asesora / Vendedora": nombre,
                        "Teléfono": tel,
                        "PV Ganados (Ventas)": ganados,
                        "PV Canjeados": quemados,
                        "Saldo PV Neto": netos,
                    }
                )
            df_ase = pd.DataFrame(asesores_data)

            def color_saldo(col):
                return [
                    "color: #00cc00; font-weight: bold;"
                    if v > 0
                    else (
                        "color: #ff4d4d; font-weight: bold;"
                        if v < 0
                        else "color: gray; font-weight: bold;"
                    )
                    for v in col
                ]

            st.dataframe(
                df_ase.style.apply(color_saldo, subset=["Saldo PV Neto"], axis=0),
                use_container_width=True,
            )
        else:
            st.info("Aún no tienes Asesores / Vendedoras registradas.")

    with t_ase_crear:
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            a_nombre = st.text_input("Nombre Completo de la Asesora", key=f"a_nom_{lk}")
        with col_a2:
            a_tel = st.text_input("Número de Teléfono / Celular", key=f"a_tel_{lk}")
        st.markdown('<br><div class="btn-principal">', unsafe_allow_html=True)
        if st.button("💾 Guardar Asesor"):
            if a_nombre:
                try:
                    nombre_asesor_formateado = a_nombre.strip().upper()
                    supabase.table("asesores").insert(
                        {
                            "nombre": nombre_asesor_formateado,
                            "telefono": a_tel,
                            "empresa_id": id_seguro,  # NUEVO - PARA ENLAZAR CON EL CLIENTE
                        }
                    ).execute()
                    st.session_state.limpiador += 1
                    st.session_state.msg_ase = (
                        f"¡Asesor '{nombre_asesor_formateado}' guardado exitosamente!"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.error("El nombre es obligatorio.")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu_seleccionado == "💸 Registro de Gastos":
    st.title("💸 Registro de Gastos Operativos")
    if st.session_state.get("msg_gasto"):
        st.success(st.session_state.msg_gasto)
        st.session_state.msg_gasto = None
    t_gasto_lista, t_gasto_crear = st.tabs(
        ["📋 Historial de Gastos", "➕ Registrar Nuevo Gasto"]
    )

    with t_gasto_lista:
        if t_gastos:
            df_g = pd.DataFrame(t_gastos)
            cols_to_show = [
                c for c in ["fecha", "concepto", "monto"] if c in df_g.columns
            ]
            if cols_to_show:
                df_g = df_g[cols_to_show]
                df_g.columns = ["Fecha", "Concepto del Gasto", "Monto Saliente ($)"]
            st.dataframe(df_g, use_container_width=True)
        else:
            st.info("No hay gastos registrados.")

    with t_gasto_crear:
        g_fecha = st.date_input("Fecha del Gasto", datetime.today(), key=f"g_fech_{lk}")
        g_concepto = st.text_input(
            "Concepto / Descripción del Gasto", key=f"g_conc_{lk}"
        )
        g_monto = st.number_input(
            "Monto ($)", min_value=0.0, step=1000.0, key=f"g_monto_{lk}"
        )
        st.markdown('<br><div class="btn-principal">', unsafe_allow_html=True)
        if st.button("💾 Guardar Gasto"):
            if g_concepto and g_monto > 0:
                try:
                    supabase.table("gastos").insert(
                        {
                            "fecha": str(g_fecha),
                            "concepto": g_concepto,
                            "monto": g_monto,
                            "empresa_id": id_seguro,  # NUEVO - PARA ENLAZAR CON EL CLIENTE
                        }
                    ).execute()
                    st.session_state.limpiador += 1
                    st.session_state.msg_gasto = "Gasto registrado exitosamente."
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.error("Debe ingresar un concepto válido y un monto mayor a cero.")
        st.markdown("</div>", unsafe_allow_html=True)
