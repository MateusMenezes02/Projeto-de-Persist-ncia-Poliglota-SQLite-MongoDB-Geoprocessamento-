from geopy.distance import great_circle
from pymongo import MongoClient
from pymongo.errors import OperationFailure
import sqlite3

# --- Constantes de Conexão (Devem ser as mesmas do setup) ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "poliglota_geoproj"
COLLECTION_NAME = "locais_geo"
SQLITE_DB = 'dados_estruturados.db'
MONGO_CLIENT = MongoClient(MONGO_URI)


# ----------------------------------------------------------------------
# 1. FUNÇÃO: Calcular Distância entre dois pontos (geopy)
# ----------------------------------------------------------------------
def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em quilômetros (km) entre dois pontos geográficos
    utilizando o método do Círculo Máximo (geopy.great_circle), que é
    mais preciso.
    """
    ponto_a = (lat1, lon1)
    ponto_b = (lat2, lon2)

    distancia_km = great_circle(ponto_a, ponto_b).km
    return distancia_km


# ----------------------------------------------------------------------
# 2. FUNÇÃO: Listar locais em um raio de distância (MongoDB GeoSpatial)
# ----------------------------------------------------------------------
def buscar_locais_em_raio(latitude_central, longitude_central, raio_km):
    """
    Lista os locais no MongoDB que estão dentro de um raio de distância
    em km, utilizando a consulta geoespacial $nearSphere.

    Args:
        latitude_central (float): Latitude do ponto de busca.
        longitude_central (float): Longitude do ponto de busca.
        raio_km (float): Raio de busca em quilômetros.

    Returns:
        list: Lista de documentos JSON (locais) encontrados.
    """
    collection = MONGO_CLIENT[DB_NAME][COLLECTION_NAME]

    # MongoDB utiliza metros para $maxDistance em consultas geoespaciais
    raio_metros = raio_km * 1000

    try:
        resultados = collection.find({
            "coordenadas.ponto": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude_central, latitude_central]  # [lon, lat] padrão GeoJSON
                    },
                    "$maxDistance": raio_metros  # Distância máxima em metros
                }
            }
        })

        # Converte o cursor do MongoDB para uma lista Python
        locais = list(resultados)
        return locais

    except OperationFailure as e:
        print(f"ERRO: Verifique se o índice '2dsphere' foi criado no MongoDB. Erro: {e}")
        return []


# ----------------------------------------------------------------------
# 3. FUNÇÃO: Consultar e Cruzar dados (MongoDB + SQLite)
# ----------------------------------------------------------------------
def cruzar_dados_local_cidade(nome_local):
    """
    Busca um local no MongoDB e cruza a informação da sua 'cidade'
    com dados adicionais da cidade no SQLite (População, Estado).

    Retorna um dicionário com os dados combinados.
    """
    # 1. Buscar o local no MongoDB
    collection = MONGO_CLIENT[DB_NAME][COLLECTION_NAME]
    # O .pop('_id') é para remover o ObjectId do MongoDB e facilitar a serialização/visualização
    local_mongo = collection.find_one({"nome_local": nome_local}, {'_id': False})

    if not local_mongo:
        return {"erro": f"Local '{nome_local}' não encontrado no MongoDB."}

    cidade_do_local = local_mongo.get("cidade")

    # 2. Buscar informações adicionais da cidade no SQLite
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    # Busca a linha da cidade
    cursor.execute("SELECT * FROM CIDADES WHERE nome = ?", (cidade_do_local,))
    cidade_sqlite = cursor.fetchone()
    conn.close()

    # 3. Combinar e formatar os resultados
    dados_cruzados = {
        "local_mongo_info": local_mongo,
        "cidade_sqlite_info": None
    }

    if cidade_sqlite:
        dados_cruzados["cidade_sqlite_info"] = {
            "id": cidade_sqlite[0],
            "nome": cidade_sqlite[1],
            "estado": cidade_sqlite[2],
            "populacao": f"{cidade_sqlite[3]:,}".replace(",", "."),  # Formatação de número
            "fonte_db": "SQLite"
        }

    return dados_cruzados