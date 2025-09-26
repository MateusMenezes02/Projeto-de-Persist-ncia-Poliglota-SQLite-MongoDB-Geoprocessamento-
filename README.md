🌍 Projeto de Persistência Poliglota (SQLite + MongoDB + Geoprocessamento)

Este projeto demonstra *persistência poliglota* integrando dois bancos de dados:
- *SQLite* → para dados tabulares estruturados (ex: cidades e populações)
- *MongoDB* → para documentos geoespaciais (ex: pontos turísticos, locais)

Além disso, utiliza a biblioteca *geopy* para cálculos de distância e integra informações entre os bancos de dados.

---

## 🚀 Funcionalidades

- Criação e popularização de um banco *SQLite* com informações de cidades.
- Criação e popularização de uma coleção *MongoDB* com locais e coordenadas geoespaciais.
- Criação de *índice 2dsphere* no MongoDB para consultas geoespaciais.
- Cálculo de *distância em km* entre dois pontos (geopy).
- Busca de locais dentro de um *raio de distância* em torno de um ponto central (MongoDB).
- *Cruzamento de dados*: relaciona informações do MongoDB (locais) com o SQLite (cidades).
