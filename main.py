from fastapi import FastAPI, HTTPException #importamos la clase FastAPI del framework FastAPI y la clase HTTPException
from fastapi.responses import HTMLResponse, JSONResponse #importamos la clase JSONResponse de la librería responses de FastAPI para devolver respuestas en formato JSON
import pandas as pd #importamos la librería pandas para trabajar con dataframes
from nltk.tokenize import word_tokenize #importamos la función word_tokenize de la librería nltk para tokenizar palabras
    
import nltk
from nltk.corpus import wordnet

nltk.data.path.append(r"C:\Users\judac\AppData\Roaming\Python\Python312\site-packages\nltk")

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

#Ruta de inicio cuando alguien entra a la api, mensaje de bienvenida
@app.get('/', tags=["Inicio"])
def inicio():
    return HTMLResponse('<h1>¡Bienvenido al area de servicio tecnico!</h1>') #devolvemos un mensaje de bienvenida en formato HTML

#Obtener la información de todos los celulares
@app.get('/celulares', tags=["Celulares"])
def get_celulares():
    return celulares_list or HTTPException(status_code=500, detail="No se encontraron celulares") #devolvemos la lista de celulares o un mensaje de error si no se encontraron celulares

#Obtener la información de un celular en especifico
@app.get('/celulares/{orden}', tags=["Celulares"])
def get_celular(orden: int):
    #Buscar en la lista de celulares el celular con el número de orden especificado
    return next((m for m in celulares_list if m ["Orden"] == orden), {"detalle": "Celular no encontrado"}) #devolvemos el celular o un mensaje de error si no se encontro el celular

#Ruta del chatbot que responde con modelos segun comentario
@app.get('/chatbot', tags=["Chatbot"])
def chatbot(query: str):
    #Tokenizamos la consulta, osea dividimos la consulta en palabras
    query_words = word_tokenize(query.lower())
    
    #Buscamos sinónimos de las palabras clave
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)
    
    #filtramos la lista de celulares buscando coincidencias en los comentarios
    results = [m for m in celulares_list if any (s in m ['Comentarios'].lower() for s in synonyms)]
    
    #Si encontramos celulares enviamos la lista, si no se muestra un mensaje de que no se encontraron coincidencias
    return JSONResponse (content={"respuesta": "alguno de estos es tu celular?" if results else "No se encontraron celulares con ese daño", "celulares": results})

#Ruta para buscar celulares por marca
@app.get('/celulares/', tags=['Celulares'])
def get_celulares_por_marca(marca: str):
    #filtramos la lista de celulares buscando coincidencias en la marca
    results = [m for m in celulares_list if marca.lower() in m['Marca'].lower()]