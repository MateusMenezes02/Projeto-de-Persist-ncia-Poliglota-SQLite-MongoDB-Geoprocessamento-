import database_setup
from geoprocessing_service import calcular_distancia, buscar_locais_em_raio, cruzar_dados_local_cidade
from pprint import pprint

if __name__ == '__main__':

    print("=====================================================")
    print("    INÍCIO DO PROJETO DE PERSISTÊNCIA POLIGLOTA    ")
    print("=====================================================")

    # 1. Configuração e Popularização dos Bancos de Dados
    print("\n--- 1. Configurando Bancos de Dados (SQLite e MongoDB) ---")
    # Execute o setup para garantir que os dados e o índice 2dsphere existam
    database_setup.setup_sqlite()
    database_setup.setup_mongodb()

    # 2. Demonstração de Geoprocessamento: Cálculo de Distância
    print("\n--- 2. Teste de Cálculo de Distância (geopy) ---")

    # Ponto A: Praça da Independência (João Pessoa)
    lat_jp, lon_jp = -7.11532, -34.861
    # Ponto B: Museu da Cidade (Campina Grande)
    lat_cg, lon_cg = -7.2285, -35.8817

    distancia_jp_cg = calcular_distancia(lat_jp, lon_jp, lat_cg, lon_cg)
    print(f"-> Ponto A: Praça da Independência (JP)")
    print(f"-> Ponto B: Museu da Cidade (CG)")
    print(f"-> Distância calculada: {distancia_jp_cg:.2f} km")

    # 3. Demonstração de Geoprocessamento: Busca em Raio
    print("\n--- 3. Teste de Busca em Raio (MongoDB GeoSpatial) ---")

    # Buscando locais a 2 km ao redor da Praça da Independência (JP)
    latitude_busca = -7.11532
    longitude_busca = -34.861
    raio = 2  # km

    locais_proximos = buscar_locais_em_raio(latitude_busca, longitude_busca, raio)

    print(f"Busca Central: ({latitude_busca}, {longitude_busca}) | Raio: {raio} km")
    print(f"Total de locais encontrados: {len(locais_proximos)}")

    for local in locais_proximos:
        # Calcula a distância exata com geopy para exibir no resultado
        local_lat = local['coordenadas']['latitude']
        local_lon = local['coordenadas']['longitude']
        dist_exata = calcular_distancia(latitude_busca, longitude_busca, local_lat, local_lon)

        print(f"  - {local['nome_local']} ({local['cidade']}) | Distância: {dist_exata:.3f} km")

    # 4. Demonstração de Consulta Poliglota
    print("\n--- 4. Teste de Cruzamento de Dados (MongoDB + SQLite) ---")

    nome_local_busca = "Praça do Marco Zero"
    dados_cruzados = cruzar_dados_local_cidade(nome_local_busca)

    if 'erro' not in dados_cruzados:
        print(f"Dados cruzados para o local: '{nome_local_busca}'")

        # Informação do local (MongoDB)
        local_info = dados_cruzados['local_mongo_info']
        print(f"\n[Dados do Local - MongoDB]")
        pprint(local_info)

        # Informação da cidade (SQLite)
        cidade_info = dados_cruzados['cidade_sqlite_info']
        print(f"\n[Dados Estruturados da Cidade - SQLite]")
        print(f"  Cidade: {cidade_info['nome']}/{cidade_info['estado']}")
        print(f"  População Estimada: {cidade_info['populacao']}")
    else:
        print(f"Erro na busca: {dados_cruzados['erro']}")

    print("\n=====================================================")
    print("    FIM DA EXECUÇÃO DO PROJETO    ")
    print("=====================================================")