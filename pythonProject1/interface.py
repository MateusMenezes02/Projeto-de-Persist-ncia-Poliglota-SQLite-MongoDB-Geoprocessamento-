import streamlit as st
import pandas as pd
from geoprocessing_service import calcular_distancia, buscar_locais_em_raio, cruzar_dados_local_cidade
from pymongo import MongoClient
import sqlite3
import database_setup

# --- Constantes de Conexão ---
MONGO_URI = database_setup.MONGO_URI
DB_NAME = database_setup.DB_NAME
COLLECTION_NAME = database_setup.COLLECTION_NAME
SQLITE_DB = database_setup.SQLITE_DB

# Cliente MongoDB é inicializado fora das funções para reutilização
try:
    MONGO_CLIENT = MongoClient(MONGO_URI)
except Exception as e:
    st.error(f"Erro ao inicializar o cliente MongoDB: {e}")
    st.stop()



def get_all_cities_from_sqlite() -> list[str]:
    """
    Retorna todas as cidades (nome, estado) do SQLite no formato 'Cidade (Estado)'.

    Returns:
        list[str]: Lista de cidades formatadas.
    """
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome, estado FROM CIDADES ORDER BY nome")
        cidades = cursor.fetchall()
        return [f"{cidade[0]} ({cidade[1]})" for cidade in cidades]
    finally:
        conn.close()


def get_locals_by_city(city_name: str) -> list[dict]:
    """
    Busca locais no MongoDB filtrando pelo nome da cidade.

    Args:
        city_name (str): Nome completo da cidade (ex: 'João Pessoa (PB)').

    Returns:
        list[dict]: Lista de documentos de locais.
    """
    collection = MONGO_CLIENT[DB_NAME][COLLECTION_NAME]
    # Limpa o nome da cidade removendo o sufixo do estado (ex: "João Pessoa (PB)" -> "João Pessoa")
    city_name_clean = city_name.split(' (')[0]

    locais = list(collection.find({"cidade": city_name_clean}, {'_id': 0}))
    return locais


def insert_new_local_mongodb(nome: str, cidade: str, lat: float, lon: float, descricao: str) -> tuple[bool, str]:
    """
    Insere um novo local (Ponto de Interesse) no MongoDB com coordenadas GeoJSON.

    Args:
        nome (str): Nome do local.
        cidade (str): Nome da cidade.
        lat (float): Latitude.
        lon (float): Longitude.
        descricao (str): Descrição do local.

    Returns:
        tuple[bool, str]: Status (sucesso/falha) e mensagem.
    """
    collection = MONGO_CLIENT[DB_NAME][COLLECTION_NAME]

    if not (nome and cidade and lat and lon):
        return False, "Erro: Todos os campos obrigatórios (Nome, Cidade, Lat, Lon) devem ser preenchidos."

    try:
        documento = {
            "nome_local": nome,
            "cidade": cidade,
            "coordenadas": {
                "latitude": lat,
                "longitude": lon,
                # Padrão GeoJSON: [longitude, latitude]
                "ponto": {"type": "Point", "coordinates": [lon, lat]}
            },
            "descricao": descricao
        }
        collection.insert_one(documento)
        return True, f"Local '{nome}' inserido com sucesso no MongoDB."
    except Exception as e:
        return False, f"Erro ao inserir no MongoDB: {e}"


def insert_new_city_sqlite(nome: str, estado: str, populacao: int) -> tuple[bool, str]:
    """
    Insere uma nova cidade no SQLite.

    Args:
        nome (str): Nome da cidade.
        estado (str): Sigla do estado (UF).
        populacao (int): População estimada.

    Returns:
        tuple[bool, str]: Status (sucesso/falha) e mensagem.
    """
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    if not (nome and estado and populacao):
        conn.close()
        return False, "Erro: Todos os campos obrigatórios (Nome, Estado, População) devem ser preenchidos."

    try:
        cursor.execute("INSERT INTO CIDADES (nome, estado, populacao) VALUES (?, ?, ?)",
                       (nome, estado.upper(), populacao))
        conn.commit()
        return True, f"Cidade '{nome} ({estado.upper()})' inserida com sucesso no SQLite."
    except sqlite3.IntegrityError:
        return False, f"Erro: A cidade '{nome}' já existe no banco de dados SQLite."
    except Exception as e:
        return False, f"Erro ao inserir no SQLite: {e}"
    finally:
        conn.close()



st.set_page_config(layout="wide", page_title="Persistência Poliglota GeoSpatial")

# --- Cabeçalho e Configuração ---
st.title("🗺️ Persistência Poliglota (SQLite + MongoDB Geo)")
st.markdown(
    "Demonstração de integração entre **SQLite (dados estruturados)** e **MongoDB (dados Geoespaciais)**, utilizando as funções de geoprocessamento.")

# Garante que os bancos de dados estão configurados antes da execução da interface
try:
    database_setup.setup_sqlite()
    database_setup.setup_mongodb()
except Exception as e:
    st.error(f"Erro de Conexão/Setup do Banco de Dados. Verifique se o MongoDB está rodando. Detalhes: {e}")
    st.stop()

st.sidebar.title("Opções")
page = st.sidebar.radio("Navegar",
                        ["Visão Geral e Mapa", "Busca Geoespacial", "Inserção de Dados", "Cruzamento de Dados"])


if page == "Inserção de Dados":

    st.header("➕ Inserção de Novos Dados")
    st.markdown(
        "Use esta seção para adicionar novas **cidades** ao **SQLite** e novos **pontos de interesse** ao **MongoDB**.")

    # --- Seção: Inserir Nova Cidade (SQLite) ---
    st.subheader("Inserir Nova Cidade (SQLite)")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_city_name = st.text_input("Nome da Cidade (ex: Salvador)", key="city_name_sql")
    with col2:
        new_city_state = st.text_input("Estado (UF, ex: BA)", max_chars=2, key="city_state_sql")
    with col3:
        new_city_pop = st.number_input("População Estimada", min_value=100, step=10000, format="%d", key="city_pop_sql")

    if st.button("Inserir Cidade no SQLite"):
        success, message = insert_new_city_sqlite(new_city_name, new_city_state, new_city_pop)
        if success:
            st.success(message)
        else:
            st.error(message)

    # --- Seção: Inserir Novo Local (MongoDB) ---
    st.subheader("Inserir Novo Local (MongoDB)")
    # Obtém apenas o nome das cidades para o selectbox
    cidades_sqlite = [c.split(' (')[0] for c in get_all_cities_from_sqlite()]

    col_a, col_b = st.columns(2)
    with col_a:
        new_local_name = st.text_input("Nome do Local", key="local_name_mongo")
        new_local_city = st.selectbox("Cidade", cidades_sqlite, key="local_city_mongo")
    with col_b:
        new_local_lat = st.number_input("Latitude", format="%.5f", value=-7.11, key="local_lat_mongo")
        new_local_lon = st.number_input("Longitude", format="%.5f", value=-34.8, key="local_lon_mongo")

    new_local_desc = st.text_area("Descrição", key="local_desc_mongo")

    if st.button("Inserir Local no MongoDB"):
        success, message = insert_new_local_mongodb(new_local_name, new_local_city,
                                                    new_local_lat, new_local_lon, new_local_desc)
        if success:
            st.success(message)
        else:
            st.error(message)


elif page == "Visão Geral e Mapa":
    st.header("🌍 Locais Cadastrados por Cidade")
    st.markdown("Selecione uma **cidade** do **SQLite** para visualizar os **locais** associados no **MongoDB**.")

    cities_options = get_all_cities_from_sqlite()
    selected_city = st.selectbox("Selecione a Cidade:", cities_options)

    if selected_city:
        locais = get_locals_by_city(selected_city)

        st.subheader(f"Locais em {selected_city} (Total: {len(locais)})")

        if locais:
            # Prepara os dados para o st.dataframe e st.map
            data = [
                {
                    "Local": local.get("nome_local"),
                    "Descrição": local.get("descricao"),
                    "lat": local.get("coordenadas", {}).get("latitude"),
                    "lon": local.get("coordenadas", {}).get("longitude")
                } for local in locais
            ]

            df_locais = pd.DataFrame(data)

            # Mostra o mapa e o Dataframe
            st.map(df_locais[['lat', 'lon']].dropna(), zoom=12)
            st.dataframe(df_locais.drop(columns=['lat', 'lon']), use_container_width=True)

        else:
            st.info(f"Nenhum local encontrado no MongoDB para a cidade de {selected_city.split(' (')[0]}.")


elif page == "Busca Geoespacial":
    st.header("🔍 Busca de Locais em Raio (MongoDB GeoSpatial)")
    st.markdown("Utiliza a função geoespacial `$nearSphere` do MongoDB, que requer o índice **`2dsphere`**.")

    st.subheader("Configurações da Busca")
    col1, col2, col3 = st.columns(3)

    with col1:
        center_lat = st.number_input("Latitude Central", format="%.5f", value=-7.11532, key="center_lat")
    with col2:
        center_lon = st.number_input("Longitude Central", format="%.5f", value=-34.861, key="center_lon")
    with col3:
        radius_km = st.slider("Raio de Busca (km)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key="radius_km")

    if st.button("Buscar Locais no Raio"):

        with st.spinner(f"Buscando locais em até **{radius_km} km** do ponto central ({center_lat}, {center_lon})..."):
            locais_proximos = buscar_locais_em_raio(center_lat, center_lon, radius_km)

        st.subheader(f"Resultados Encontrados: {len(locais_proximos)}")

        if locais_proximos:
            data = []
            for local in locais_proximos:
                local_lat = local['coordenadas']['latitude']
                local_lon = local['coordenadas']['longitude']
                # Recalcula a distância exata com geopy para exibição detalhada
                dist_exata = calcular_distancia(center_lat, center_lon, local_lat, local_lon)

                data.append({
                    "Local": local['nome_local'],
                    "Cidade": local['cidade'],
                    "Distância (km)": f"{dist_exata:.3f}",
                    "lat": local_lat,
                    "lon": local_lon
                })

            df_proximos = pd.DataFrame(data)

            # Mostra o mapa e o Dataframe
            st.map(df_proximos[['lat', 'lon']].dropna(), zoom=12)
            st.dataframe(df_proximos.drop(columns=['lat', 'lon']), use_container_width=True)
        else:
            st.warning("Nenhum local encontrado no raio especificado.")


elif page == "Cruzamento de Dados":
    st.header("🔗 Cruzamento de Dados (MongoDB + SQLite)")
    st.markdown(
        "Busca um **local** no **MongoDB** e cruza com os dados estruturados (População, Estado) da sua **cidade** no **SQLite**.")

    # Busca todos os locais no MongoDB para o Selectbox
    try:
        collection = MONGO_CLIENT[DB_NAME][COLLECTION_NAME]
        all_locals = list(collection.find({}, {'nome_local': 1, '_id': 0}))
        local_names = [l['nome_local'] for l in all_locals]
    except Exception as e:
        local_names = []
        st.error(f"Erro ao buscar locais no MongoDB. Verifique a conexão: {e}")

    selected_local_cross = st.selectbox("Selecione o Local:", local_names)

    if st.button("Cruzar Informações"):
        if selected_local_cross:
            with st.spinner(f"Cruzando dados para '{selected_local_cross}'..."):
                dados_cruzados = cruzar_dados_local_cidade(selected_local_cross)

            if 'erro' not in dados_cruzados:
                st.subheader(f"Resultado do Cruzamento para **{selected_local_cross}**")

                # --- Dados do Local (MongoDB) ---
                st.markdown("### 🔹 Informações do Local (Fonte: MongoDB)")
                local_info = dados_cruzados.get('local_mongo_info', {})

                st.json(local_info)

                # --- Dados da Cidade (SQLite) ---
                st.markdown("### 🔹 Informações Estruturadas da Cidade (Fonte: SQLite)")
                cidade_info = dados_cruzados.get('cidade_sqlite_info')

                if cidade_info:
                    col_sql1, col_sql2 = st.columns(2)
                    with col_sql1:
                        st.metric("Cidade/Estado", f"{cidade_info['nome']} / {cidade_info['estado']}")
                    with col_sql2:
                        # Formata a população para melhor leitura
                        pop_formatada = f"{cidade_info['populacao']:,}".replace(',', '.')
                        st.metric("População Estimada", pop_formatada)

                    st.markdown(
                        f"*(A busca no SQLite foi feita usando a chave 'cidade': **{local_info.get('cidade')}**)*")

                else:
                    st.warning(
                        f"Não foi possível encontrar a cidade '{local_info.get('cidade')}' no banco de dados SQLite para cruzamento.")
            else:
                st.error(dados_cruzados['erro'])
        else:
            st.warning("Selecione um local para cruzar os dados.")