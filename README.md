# Previsão e mapeamento de furtos e roubos de veículos

## Sobre o projeto
Pipeline automatizado de engenharia de dados criminais e modelo de Machine Learning para previsão de manchas criminais de furtos e roubos de veículos. Sistema desenvolvido para otimização da alocação de patrulhas ostensivas, antecipação de zonas de risco e redução de tempo de resposta policial. Projeto estruturado para a disciplina de Planejamento e Gestão de Projetos da Universidade Federal da Fronteira Sul (UFFS).

## Autores
- Jeferson Solforoso Pompermaier
- Alexsandro Lazzaretti

## Estrutura do repositório
- `/article/`: Construção incremental do artigo científico (Introdução, Metodologia, Resultados).
- `/data/`: Armazenamento de arquivos de dados brutos e pré-processados (fonte: SSP-SP).
- `/notebooks/`: Experimentação, Análise Exploratória de Dados (EDA) e prototipação de modelos via Google Colab.
- `/models/`: Modelos preditivos treinados e exportados (formatos .joblib ou .pkl).
- `/src/`: Módulos e scripts base em Python para processamento de dados e rotinas de ML.
- `/app/`: Código-fonte da aplicação interativa para publicação no Streamlit Community Cloud.
- `/tests/`: Arquivos de testes unitários, de integração e de aceite.
- `/.github/`: Automações, templates de issues e metadados de configuração do quadro Kanban.
- `/docs/`: Documentação técnica auxiliar.

## Sprint 0 - Planejamento
**Objetivo:** Estruturação inicial do projeto, configuração do repositório e definição dos artefatos de gestão.

**Entregáveis:**
- Configuração do repositório GitHub com a estrutura de diretórios obrigatória.
- Business Model Canvas estruturado com foco em Segurança Pública: [business_model_canvas.pdf](docs/business_model_canvas.pdf).
- Product Backlog inicial elaborado e priorizado: [Acessar Backlog](https://github.com/users/JefersonPompermaier/projects/1/views/1).
- Quadro Kanban configurado com definição de limites de Work In Progress (WIP): [Acessar Kanban](https://github.com/users/JefersonPompermaier/projects/1/views/1).
- Controle de escopo e entregas via Milestone: [Sprint 0](https://github.com/JefersonPompermaier/predicao-furtos-veiculos-ml/milestone/1).
- Artigo Científico (Introdução, Problema, Objetivos e Justificativa): [Artigo](https://drive.google.com/file/d/1-dWAhvRrFdxWnRe-51XXfa38HreCRPIJ/view?usp=drive_link).

## Sprint 1 - Levantamento e Preparação de Dados
**Objetivo:** Identificar, avaliar e extrair a base de dados ideal para o treinamento do modelo preditivo, atualizar o backlog e avançar na escrita acadêmica.

**Entregáveis:**
- Levantamento e Avaliação de Dataset: Mapeamento técnico da base criminal (SSP-SP) concluído.
- Avaliação da Fonte: Validação da viabilidade técnica (Granularidade Espacial e Temporal) da SSP-SP devido aos microdados georreferenciados (BOs).
- Ingestão de Dados Automatizada: Automação via **Web Crawler (Selenium)** do download da série histórica (2019-2023) hospedado em `/src/scraper_ssp_sp.py`, superando a barreira do ASP.NET. Os dados mensais são salvos em `/data/SP/raw/`.
- Análise Exploratória (EDA): Prototipação iniciada (ver notebooks) para validação de completude dos dados espaciais (análise de valores ausentes em lat/long).
- Backlog Priorizado: Atualização das próximas sprints focando na limpeza profunda, remoção de duplicatas (BO_PRINCIPAL) e criação da malha espacial H3.
- Requisitos:
  - Funcional: Pipeline deve ingerir dados brutos da SSP-SP em Python e gerar arquivo consolidado unificado.
  - Não Funcional: Processamento deve suportar mais de 1 milhão de registros (volumetria estimada de 5 anos).
- Artigo Científico: Revisão de literatura, formulação do problema e definição da Metodologia de coleta de dados incluídas. (Pronto para revisão do orientador).
