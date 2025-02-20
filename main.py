import csv #Importamos la librería csv

from fastapi import FastAPI, HTTPException #importamos la clase FastAPI del framework FastAPI y la clase HTTPException
from fastapi.responses import HTMLResponse, JSONResponse #importamos la clase JSONResponse de la librería responses de FastAPI para devolver respuestas en formato JSON
import pandas as pd #importamos la librería pandas para trabajar con dataframes
from nltk.tokenize import word_tokenize #importamos la función word_tokenize de la librería nltk para tokenizar palabras 
import nltk
from nltk.corpus import wordnet
import os
from nltk.tokenize import RegexpTokenizer #importamos la clase RegexpTokenizer de la librería nltk.tokenize para tokenizar palabras
nltk_path = os.path.join(os.getenv("APPDATA"), "nltk_data")
nltk.data.path.append(nltk_path)

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from pydantic import BaseModel



# Verificar si los datos de NLTK están disponibles, si no, descargarlos
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
#Funcion para cargar csv de los celulares
def load_celulares():
    #Leemos el archivo csv con la informacion de celulares
    df = pd.read_csv("datos_servicio_tecnico_final.csv", delimiter=";", quotechar='"', on_bad_lines="skip")[['Orden', 'Cliente', 'Celular', 'Marca', 'Modelo', 'Estado', 'Comentarios', 'Técnico']]
    
    #Llenamos los espacios vacios con texto vacio y convertimos los datos en una lista de diccionarios
    return df.fillna('').to_dict(orient="records")

#Cargamos la información al iniciar la api
celulares_list = load_celulares()


#Función para encontrar sinonimos de una palabra
def get_synonyms(word):
    return{lemma.name().lower() for syn in wordnet.synsets(word) for lemma in syn.lemmas()}

#Creamos la apliación FastAPI, que sera el motor de nuestra API
app = FastAPI(title="Información del estado de tu celular", version="1.0.0")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static") #montamos la carpeta static para poder acceder a los archivos estáticos


#Ruta de inicio cuando alguien entra a la api, mensaje de bienvenida
@app.get('/', tags=["Inicio"])
def inicio(request: Request):
    #return HTMLResponse('<h1>¡Bienvenido al area de servicio tecnico!</h1>') #devolvemos un mensaje de bienvenida en formato HTML
    return templates.TemplateResponse("index.html", {"request": request})

#Obtener la información de todos los celulares
@app.get('/celulares', tags=["Celulares"])
def get_celulares():
    return celulares_list or HTTPException(status_code=500, detail="No se encontraron celulares") #devolvemos la lista de celulares o un mensaje de error si no se encontraron celulares



#Obtener la información de un celular en especifico por orden de servicio
@app.get('/celulares/orden', tags=["Celulares"])
def get_celular(orden: int):
    # Buscar en la lista de celulares el celular con el número de orden especificado
    celular = next((m for m in celulares_list if int(m["Orden"]) == orden), None)

    # Si no se encontró, devolvemos un mensaje de error
    if not celular:
        return {"Error": "Celular no encontrado"}

    # Convertimos solo "Comentarios" a minúsculas
    celular_modificado = {**celular, "Comentarios": str(celular["Comentarios"]).lower()}

    return JSONResponse(content=celular_modificado)


#Ruta para buscar celulares por marca
@app.get('/celulares/marca', tags=['Celulares'])
def get_celulares_por_marca(marca: str):
    print(f"Marca recibida: {marca}")
    #filtramos la lista de celulares buscando coincidencias en la marca
    results = [m for m in celulares_list if marca.lower() in m['Marca'].lower()]
    
    # Convertimos los valores del resultado a minúsculas antes de enviarlos
    results_modificados = [
        {**m, "Comentarios": str(m["Comentarios"]).lower()} for m in results
    ]
    
    return JSONResponse(content={"celulares": results_modificados}) if results else {"mensaje": "No se encontraron celulares con esa marca"}  #devolvemos la lista de celulares o un mensaje de error si no se encontraron celulares




#Ruta del chatbot que responde con modelos segun comentario
@app.get('/chatbot', tags=["Chatbot"])
def chatbot(query: str):
    # Verifica que nltk tenga los datos necesarios
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')

    # Tokenizamos la consulta (verificando si nltk está correctamente instalado)
    try:
        tokenizer = RegexpTokenizer(r'\w+')  # Tokenizador que solo toma palabras
        query_words = tokenizer.tokenize(query.lower())
    except Exception as e:
        return JSONResponse(content={"error": f"Error al tokenizar la consulta: {str(e)}"}, status_code=500)

    # Obtenemos sinónimos de cada palabra
    synonyms = set(query_words)
    for q in query_words:
        synonyms.update(get_synonyms(q))

    # Filtramos los celulares con coincidencias en comentarios
    try:
        results = [m for m in celulares_list if any(s in str(m.get('Comentarios', '')).lower() for s in synonyms)]
        # Convertimos los valores del resultado a minúsculas antes de enviarlos
        results_modificados = [
        {**m, "Comentarios": str(m["Comentarios"]).lower()} for m in results
    ]
    
        
    except Exception as e:
        return JSONResponse(content={"error": f"Error al buscar coincidencias: {str(e)}"}, status_code=500)

    # Devolvemos la respuesta
    return JSONResponse(content={"respuesta": "¿Alguno de estos es tu celular?" if results_modificados else "No se encontraron celulares con ese daño", "celulares": results_modificados})



#Función para obtener la lista de técnicos
@app.get('/celulares/tecnicos', tags=["Celulares"])
def obtener_tecnicos():
    # Extraer la lista única de técnicos desde celulares_list
    tecnicos = sorted(set(m["Técnico"] for m in celulares_list if m["Técnico"].strip()))
    return JSONResponse(content={"tecnicos": tecnicos})


#Función para obtener el estado de un celular
@app.get('/estados', tags=["Celulares"])
def get_estados():
    # Verifica que celulares_list esté cargado
    if not celulares_list:
        return JSONResponse(content={"error": "No hay datos disponibles"}, status_code=500)

    # Extraer valores únicos de la columna "Estado"
    estados_unicos = list(set(m["Estado"] for m in celulares_list if m.get("Estado")))

    return JSONResponse(content={"estados": estados_unicos})





#Función para agregar un nuevo celular

# 📌 Definimos un modelo de datos con Pydantic
class Celular(BaseModel):
    cliente: str
    celular: str
    marca: str
    modelo: str
    estado: str
    comentarios: str
    tecnico: str

@app.post('/celulares/agregar', tags=["Celulares"])
def agregar_celular(data: Celular):  # Recibe el JSON en el cuerpo
    try:
        
        max_orden = max(int(m["Orden"]) for m in celulares_list) + 1 if celulares_list else 1

        nuevo_celular = {
            "Orden": max_orden,
            "Cliente": data.cliente,
            "Celular": data.celular,
            "Marca": data.marca,
            "Modelo": data.modelo,
            "Estado": data.estado,
            "Comentarios": data.comentarios,
            "Técnico": data.tecnico
        }

        # 📌 Agregar al archivo CSV
        with open("datos_servicio_tecnico_final.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=nuevo_celular.keys(), delimiter=";")
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(nuevo_celular)

        # 📌 Agregar a la lista en memoria
        celulares_list.append(nuevo_celular)

        return {"Mensaje": "Celular agregado correctamente", "Celular": nuevo_celular}

    except Exception as e:
        return {"Error": str(e)}
