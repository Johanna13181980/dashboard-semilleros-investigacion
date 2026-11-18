import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import unicodedata

st.set_page_config(page_title="Semilleros | Analítica de investigación",page_icon="📊",layout="wide")
C={"azul":"#17365D","celeste":"#2878B5","verde":"#22A06B","naranja":"#F39C35","morado":"#8056B3","rojo":"#D9534F"}
PALETA=[C["celeste"],C["verde"],C["naranja"],C["morado"],C["rojo"],"#20A7B5","#D69E36"]
st.markdown("""<style>
.block-container{padding-top:1.5rem;max-width:1500px}
h1,h2,h3{color:#17365D}
[data-testid="stMetric"]{background:#EDF4FA;padding:14px;border-radius:12px;border-left:5px solid #2878B5}
</style>""",unsafe_allow_html=True)
def clean(s):
    return " ".join(str(s).strip().split()) if pd.notna(s) else ""
def norm(s):
    s=clean(s)
    return "".join(c for c in unicodedata.normalize("NFKD",s) if not unicodedata.combining(c)).casefold()
@st.cache_data(show_spinner=False)
def load(file_bytes):
    from io import BytesIO
    df=pd.read_excel(BytesIO(file_bytes))
    df.columns=[clean(c) for c in df.columns]
    names={"Ciudad de residencia":"Ciudad","Latitud":"Latitud","Longitud":"Longitud",
    "Seleccione la linea de investigación a la que pertenece su proyecto":"Línea",
    "En cuales de los siguientes productos participo durante el periodo":"Productos",
    "Participo como asistente de investigacion en un proyecto de investigacion vigente":"Asistente",
    "A cuantos eventos academicos o cientificos asistió durante el periodo":"Eventos",
    "En que modalidad participo":"Modalidad",
    "Cual fue el alcance de los eventos en los que participo":"Alcance",
    "Obtuvo algun reconocimiento, premio o distincion durante el periodo":"Reconocimiento",
    "Como calificaria su nivel de participacion en el semillero durante el periodo":"Nivel",
    "Tiene previsto continuar vinculado al semillero durante el proximo periodo":"Continuidad",
    "Considera que el semillero ha contribuido a su formacion academica o profesional":"Contribución"}
    df=df.rename(columns=names)
    required=list(names.values())
    missing=[c for c in required if c not in df.columns]
    if missing:
        raise ValueError("El Excel no contiene estas columnas requeridas: " + ", ".join(missing))
    df["Ciudad"]=df["Ciudad"].map(clean)
    df["Ciudad"]=df["Ciudad"].replace({"Bogota":"Bogotá","Bogotá D.C.":"Bogotá"})
    df["Línea"]=df["Línea"].map(clean).replace({"Analitica de datos":"Analítica de datos"})
    for c in ["Productos","Modalidad","Alcance","Asistente","Reconocimiento","Nivel","Continuidad","Contribución"]:
        df[c]=df[c].map(clean)
    df["Eventos"]=pd.to_numeric(df["Eventos"],errors="coerce")
    for c in ["Latitud","Longitud"]:df[c]=pd.to_numeric(df[c],errors="coerce")
    return df
st.title("Seguimiento de semilleros de investigación")
st.caption("Dashboard interactivo | Cargue el formulario Excel para calcular los indicadores")
archivo=st.file_uploader("Seleccione el archivo Excel de respuestas",type=["xlsx"],help="El archivo se utiliza para generar el tablero; no lo suba a GitHub")
if archivo is None:
    st.info("Cargue el archivo Excel para visualizar el mapa y las 12 figuras.")
    st.stop()
try:
    df=load(archivo.getvalue())
except Exception as exc:
    st.error(f"No fue posible leer el archivo: {exc}")
    st.stop()
with st.sidebar:
    st.header("Filtros")
    lineas=st.multiselect("Línea de investigación",sorted(df["Línea"].dropna().unique()),default=sorted(df["Línea"].dropna().unique()))
    ciudades=st.multiselect("Ciudad de residencia",sorted(df["Ciudad"].dropna().unique()),default=sorted(df["Ciudad"].dropna().unique()))
    nivel=st.multiselect("Nivel de participación",sorted(df["Nivel"].dropna().unique()),default=sorted(df["Nivel"].dropna().unique()))
    st.caption("Los filtros se aplican simultáneamente a todas las páginas.")
d=df[df["Línea"].isin(lineas)&df["Ciudad"].isin(ciudades)&df["Nivel"].isin(nivel)].copy()
def yes(c):return d[c].map(norm).eq("si").sum()
def chart(fig,title):
    fig.update_layout(title=dict(text=title,font=dict(size=16,color=C["azul"])),font=dict(family="Arial",size=12),
      colorway=PALETA,margin=dict(l=15,r=15,t=65,b=20),height=355,legend_title_text="")
    st.plotly_chart(fig,use_container_width=True)
def counts(c):
    return d[c].replace("", "Sin respuesta").value_counts().rename_axis("Categoría").reset_index(name="Estudiantes")
def bar(c,title,order=None):
    t=counts(c)
    if order:t["Categoría"]=pd.Categorical(t["Categoría"],categories=order,ordered=True);t=t.sort_values("Categoría")
    else:t=t.sort_values("Estudiantes",ascending=True)
    f=px.bar(t,x="Estudiantes",y="Categoría",orientation="h",color="Categoría",color_discrete_sequence=PALETA,text="Estudiantes")
    f.update_layout(showlegend=False,yaxis_title="",xaxis_title="Número de estudiantes")
    chart(f,title)
def donut(c,title):
    t=counts(c)
    f=px.pie(t,values="Estudiantes",names="Categoría",hole=.57,color_discrete_sequence=PALETA)
    f.update_traces(textinfo="percent+value")
    chart(f,title)
def multi(c):
    vals=[]
    for v in d[c]:
        if v:
            vals.extend([clean(x) for x in v.split(",") if clean(x)])
    return pd.Series(vals,dtype=str).value_counts().rename_axis("Categoría").reset_index(name="Participaciones")
def multi_bar(c,title):
    t=multi(c)
    if t.empty:st.info("No hay respuestas para este gráfico.");return
    f=px.bar(t,x="Participaciones",y="Categoría",orientation="h",color="Categoría",color_discrete_sequence=PALETA,text="Participaciones")
    f.update_layout(showlegend=False,yaxis_title="")
    chart(f,title)
if d.empty:
    st.warning("No hay registros para los filtros seleccionados.");st.stop()
a,b,c,e,f=st.columns(5)
a.metric("Estudiantes",len(d))
b.metric("Ciudades",d["Ciudad"].nunique())
c.metric("Líneas",d["Línea"].nunique())
e.metric("Asistentes de investigación",int(yes("Asistente")))
f.metric("Asistencias a eventos",int(d["Eventos"].sum()))
a,b,c,e=st.columns(4)
a.metric("Participaron en eventos",int((d["Eventos"]>0).sum()))
b.metric("Con reconocimientos",int(yes("Reconocimiento")))
c.metric("Participación alta/muy alta",int(d["Nivel"].map(norm).isin(["alto","muy alto"]).sum()))
e.metric("Continuarán",int(yes("Continuidad")))
tab1,tab2,tab3,tab4=st.tabs(["01 · Caracterización","02 · Producción científica","03 · Participación y reconocimientos","04 · Continuidad e impacto"])
with tab1:
    x,y=st.columns([1.45,1])
    with x:
        st.subheader("Figura 1. Distribución geográfica de estudiantes en Colombia")
        geo=d.dropna(subset=["Latitud","Longitud"]).groupby("Ciudad",as_index=False).agg(Latitud=("Latitud","mean"),Longitud=("Longitud","mean"),Estudiantes=("Ciudad","size"))
        if not geo.empty:
            geo["radio"]=geo["Estudiantes"].map(lambda v: 6000+v*2100)
            geo["color"]=geo["Estudiantes"].map(lambda v:[34,160,107,190] if v==1 else ([243,156,53,210] if v<10 else [40,120,181,220]))
            st.pydeck_chart(pdk.Deck(map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=pdk.ViewState(latitude=4.6,longitude=-73.9,zoom=4.5,pitch=30),
                layers=[pdk.Layer("ScatterplotLayer",geo,get_position="[Longitud, Latitud]",get_radius="radio",get_fill_color="color",pickable=True),
                pdk.Layer("TextLayer",geo,get_position="[Longitud, Latitud]",get_text="Estudiantes",get_size=16,get_color=[20,40,70],get_alignment_baseline="'center'")],
                tooltip={"html":"<b>{Ciudad}</b><br/>Estudiantes: {Estudiantes}"}),height=460)
            st.caption("Cada burbuja representa una ciudad; el número corresponde a estudiantes registrados. Los colores diferencian concentraciones.")
            st.dataframe(geo[["Ciudad","Estudiantes"]].sort_values("Estudiantes",ascending=False),hide_index=True,use_container_width=True)
    with y:bar("Línea","Figura 2. Estudiantes por línea de investigación")
with tab2:
    x,y=st.columns(2)
    with x:multi_bar("Productos","Figura 3. Productos académicos reportados")
    with y:
        t=d["Eventos"].fillna(-1).astype(int).value_counts().sort_index().reset_index()
        t.columns=["Eventos","Estudiantes"];t["Eventos"]=t["Eventos"].replace(-1,"Sin respuesta").astype(str)
        fig=px.bar(t,x="Eventos",y="Estudiantes",color="Eventos",text="Estudiantes",color_discrete_sequence=PALETA)
        fig.update_layout(showlegend=False)
        chart(fig,"Figura 4. Número de eventos por estudiante")
    x,y=st.columns(2)
    with x:multi_bar("Modalidad","Figura 6. Modalidad de participación en eventos")
    with y:multi_bar("Alcance","Figura 7. Alcance de los eventos")
    st.caption("En preguntas de selección múltiple se contabiliza cada categoría seleccionada. Las participaciones pueden superar el número de estudiantes.")
with tab3:
    x,y=st.columns(2)
    with x:donut("Asistente","Figura 5. Asistencia en proyectos de investigación vigentes")
    with y:donut("Reconocimiento","Figura 8. Reconocimientos, premios o distinciones")
    bar("Nivel","Figura 9. Nivel de participación en el semillero",["Medio","Alto","Muy alto"])
with tab4:
    x,y=st.columns(2)
    with x:donut("Continuidad","Figura 10. Intención de continuidad en el semillero")
    with y:bar("Contribución","Figura 11. Contribución a la formación académica o profesional",["Moderadamente","Bastante","Mucho"])
    st.subheader("Figura 12. Comparación de indicadores por línea de investigación")
    rows=[]
    for lin,g in d.groupby("Línea"):
        n=len(g)
        for nombre,val in [("Eventos",int((g["Eventos"]>0).sum())),("Asistentes",int(g["Asistente"].map(norm).eq("si").sum())),
            ("Reconocimientos",int(g["Reconocimiento"].map(norm).eq("si").sum())),
            ("Continuidad",int(g["Continuidad"].map(norm).eq("si").sum())),
            ("Participación alta",int(g["Nivel"].map(norm).isin(["alto","muy alto"]).sum()))]:
            rows.append({"Línea":lin,"Indicador":nombre,"Porcentaje":round(100*val/n,1),"Estudiantes":val})
    t=pd.DataFrame(rows)
    fig=px.bar(t,x="Indicador",y="Porcentaje",color="Línea",barmode="group",hover_data=["Estudiantes"],color_discrete_sequence=PALETA)
    fig.update_layout(yaxis_title="% dentro de cada línea")
    chart(fig,"Figura 12. Comparación porcentual entre líneas de investigación")
st.divider()
st.caption("Privacidad: el panel no muestra nombres ni correos personales. No incluya el Excel original en el repositorio de GitHub.")
st.download_button("Descargar datos agregados por ciudad (CSV)",data=d.groupby("Ciudad").size().reset_index(name="Estudiantes").to_csv(index=False).encode("utf-8-sig"),file_name="semilleros_ciudades.csv",mime="text/csv")
