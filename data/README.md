# Catálogo de Dados - Segurança Pública

## Resumo do Contexto Analítico e Priorização (Sprint 1)
A modelagem preditiva de criminalidade veicular requer a separação entre crimes de roubo (violência/ameaça) e furto (ausência da vítima). A extração e o processamento de microdados exigem contratos de dados estritos para mitigar o viés temporal (diferença entre a data da ocorrência e a data do registro do boletim) e o viés espacial (geocodificação imprecisa nas coordenadas das delegacias).

**Decisão Arquitetural da Fonte:**
A **Secretaria de Segurança Pública do Estado de São Paulo (SSP-SP)** foi definida como a **fonte oficial e exclusiva** de dados para o treinamento do modelo *baseline*. 

**Justificativa:** A SSP-SP disponibiliza publicamente microdados estruturados em nível de Boletim de Ocorrência (BO) contendo coordenadas geográficas precisas (Latitude e Longitude), o que é estritamente obrigatório para mitigar o viés espacial (Modifiable Areal Unit Problem - MAUP) em análises de padrões de pontos (*Hotspots*).

**Processo de Ingestão:**
* **Método:** Automação programática via **Web Crawler em Selenium** (`src/scraper_ssp_sp.py`). O robô resolve a barreira de extração imposta pelas tecnologias obsoletas (PostBacks ASP.NET) e faz o download contínuo da série.
* **Link Oficial para Download:** [Portal Transparência SSP - Dados Criminais (Veículos)](http://www.ssp.sp.gov.br/transparenciassp/Consulta.aspx)
* **Janela Histórica Adotada:** 5 Anos (2019 a 2023) para balancear captura de sazonalidades (incluindo pandemia) sem sobrecarregar a infraestrutura local. Os arquivos brutos (formato `.xls`/`.csv`) são processados e baixados diretamente no diretório `data/SP/raw/`.

## 1. Fonte Primária

### Portal da Transparência SSP-SP
* **URL de Acesso:** http://www.ssp.sp.gov.br/transparenciassp/Consulta.aspx
* **Órgão Mantenedor:** Secretaria de Segurança Pública do Estado de São Paulo
* **Formatos Disponíveis:** CSV, XLS
* **Granularidade Espacial:** Coordenadas GPS (Lat/Long), Logradouro, Bairro, CEP, Delegacia
* **Granularidade Temporal:** Data exata, Hora exata, Período do dia

## 2. Dicionário de Variáveis Alvo (Features)

**Variáveis Espaciais (Spatial Features)**
* `LATITUDE` e `LONGITUDE`: Coordenadas geográficas exatas da ocorrência, sujeitas a filtros de *bounding box* e restrição de *snapping* em distritos policiais.
* `BAIRRO` ou `DISTRITO_POLICIAL`: Delimitação territorial, mandatória para junção com bases cartográficas (Shapefiles).
* `TIPO_LOCAL`: Classificação do ambiente (via pública, comércio, residência) para diferenciação de oportunidades delitivas.

**Variáveis Temporais (Temporal Features)**
* `DATA_OCORRENCIA`: Data real da infração, isolada da data do registro administrativo.
* `HORA_OCORRENCIA`: Horário da ocorrência, convertido em janelas temporais quando impreciso.
* `DIA_SEMANA`: Variável categórica para mensuração de sazonalidade entre dias úteis e fins de semana.