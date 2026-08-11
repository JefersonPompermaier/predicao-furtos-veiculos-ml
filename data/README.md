# Catálogo de Dados - Segurança Pública

## Resumo do Contexto Analítico
A modelagem preditiva de criminalidade veicular requer a separação entre crimes de roubo (violência/ameaça) e furto (ausência da vítima). A extração e o processamento de microdados exigem contratos de dados estritos para mitigar o viés temporal (diferença entre a data da ocorrência e a data do registro do boletim) e o viés espacial (geocodificação imprecisa nas coordenadas das delegacias).

## 1. Fontes Primárias Mapeadas

### Sistema Nacional de Informações de Segurança Pública (SINESP)
* **URL de Acesso:** https://dados.gov.br/dados/conjuntos-dados/sistema-nacional-de-estatisticas-de-seguranca-publica
* **Órgão Mantenedor:** Ministério da Justiça e Segurança Pública (MJSP)
* **Formatos Disponíveis:** CSV, XLSX
* **Granularidade Espacial:** Estado (UF) e Município
* **Granularidade Temporal:** Mês/Ano

### Portal da Transparência SSP-SP
* **URL de Acesso:** http://www.ssp.sp.gov.br/transparenciassp/Consulta.aspx
* **Órgão Mantenedor:** Secretaria de Segurança Pública do Estado de São Paulo
* **Formatos Disponíveis:** CSV, XLS
* **Granularidade Espacial:** Coordenadas GPS (Lat/Long), Logradouro, Bairro, CEP, Delegacia
* **Granularidade Temporal:** Data exata, Hora exata, Período do dia

### Portal de Dados Abertos SSP-RS
* **URL de Acesso:** https://dados.rs.gov.br/
* **Órgão Mantenedor:** Secretaria de Estado da Segurança Pública do Rio Grande do Sul
* **Formatos Disponíveis:** CSV
* **Granularidade Espacial:** Município, Bairro
* **Granularidade Temporal:** Data exata, Faixa de Horário

### Instituto de Segurança Pública do Rio de Janeiro (ISPDados)
* **URL de Acesso:** https://www.ispdados.rj.gov.br/
* **Órgão Mantenedor:** Instituto de Segurança Pública (ISP-RJ)
* **Formatos Disponíveis:** CSV, SHP (Shapefiles), KML
* **Granularidade Espacial:** CISP (Circunscrição), AISP, RISP, Município
* **Granularidade Temporal:** Mês/Ano

## 2. Dicionário de Variáveis Alvo (Features)

**Variáveis Espaciais (Spatial Features)**
* `LATITUDE` e `LONGITUDE`: Coordenadas geográficas exatas da ocorrência, sujeitas a filtros de *bounding box* e restrição de *snapping* em distritos policiais.
* `BAIRRO` ou `DISTRITO_POLICIAL`: Delimitação territorial, mandatória para junção com bases cartográficas (Shapefiles).
* `TIPO_LOCAL`: Classificação do ambiente (via pública, comércio, residência) para diferenciação de oportunidades delitivas.

**Variáveis Temporais (Temporal Features)**
* `DATA_OCORRENCIA`: Data real da infração, isolada da data do registro administrativo.
* `HORA_OCORRENCIA`: Horário da ocorrência, convertido em janelas temporais quando impreciso.
* `DIA_SEMANA`: Variável categórica para mensuração de sazonalidade entre dias úteis e fins de semana.