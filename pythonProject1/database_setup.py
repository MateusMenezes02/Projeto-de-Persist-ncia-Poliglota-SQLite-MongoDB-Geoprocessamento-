import sqlite3
from pymongo import MongoClient

# --- Configurações de Conexão ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "poliglota_geoproj"
COLLECTION_NAME = "locais_geo"
SQLITE_DB = 'dados_estruturados.db'


# ----------------------------------------------------------------------
# 1. Configuração SQLite (Dados Tabulares Estruturados)
# ----------------------------------------------------------------------
def setup_sqlite():
    """Conecta ao SQLite e cria a tabela 'CIDADES'."""
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    print("Configurando SQLite...")

    # Cria a tabela de Cidades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CIDADES (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            estado TEXT NOT NULL,
            populacao INTEGER
        )
    ''')

    # Exemplo de inserção de dados
    cidades = [
        ('João Pessoa', 'PB', 817512),
        ('Recife', 'PE', 1653461),
        ('Natal', 'RN', 890480),
        ('Campina Grande', 'PB', 411807)
    ]

    # Inserimos apenas se o nome for novo (UNIQUE)
    cursor.executemany("INSERT OR IGNORE INTO CIDADES (nome, estado, populacao) VALUES (?, ?, ?)", cidades)

    conn.commit()
    conn.close()
    print("SQLite configurado e populado com sucesso.")


# ----------------------------------------------------------------------
# 2. Configuração MongoDB (Documentos Geoespaciais)
# ----------------------------------------------------------------------
def setup_mongodb():
    """Conecta ao MongoDB, cria a collection e o índice geoespacial."""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        print("Configurando MongoDB...")

        # --- CRIAÇÃO DO ÍNDICE GEOESPACIAL 2dSPHERE ---
        # ESSENCIAL para realizar buscas eficientes por raio ($nearSphere).
        collection.create_index([("coordenadas.ponto", "2dsphere")])
        print("Índice '2dsphere' criado/verificado.")

        # Exemplo de documentos (usando GeoJSON [longitude, latitude] para 'ponto')
        locais = [
            {
                "nome_local": "Praça da Independência",
                "cidade": "João Pessoa",
                "coordenadas": {
                    "latitude": -7.11532,
                    "longitude": -34.861,
                    # GeoJSON: [longitude, latitude]
                    "ponto": {"type": "Point", "coordinates": [-34.861, -7.11532]}
                },
                "descricao": "Ponto turístico central da cidade."
            },
            {
                "nome_local": "Estação Ciência",
                "cidade": "João Pessoa",
                "coordenadas": {
                    "latitude": -7.1189,
                    "longitude": -34.851,
                    "ponto": {"type": "Point", "coordinates": [-34.851, -7.1189]}
                },
                "descricao": "Espaço cultural e científico."
            },
            {
                "nome_local": "Praça do Marco Zero",
                "cidade": "Recife",
                "coordenadas": {
                    "latitude": -8.0614,
                    "longitude": -34.8715,
                    "ponto": {"type": "Point", "coordinates": [-34.8715, -8.0614]}
                },
                "descricao": "Marco inicial da cidade."
            },
            {
                "nome_local": "Museu da Cidade",
                "cidade": "Campina Grande",
                "coordenadas": {
                    "latitude": -7.2285,
                    "longitude": -35.8817,
                    "ponto": {"type": "Point", "coordinates": [-35.8817, -7.2285]}
                },
                "descricao": "Um dos principais museus de Campina Grande."
            }
        ]

        # Inserir dados se a collection estiver vazia
        if collection.count_documents({}) == 0:
            collection.insert_many(locais)
            print(f"MongoDB populado com {len(locais)} locais.")
        else:
            print("MongoDB já contém dados. Pulando inserção.")

    except Exception as e:
        print(f"Erro ao conectar ou configurar MongoDB. Certifique-se de que o servidor está rodando. Erro: {e}")


if __name__ == '__main__':
    setup_sqlite()
    setup_mongodb()
