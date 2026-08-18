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
- Artigo Científico (Introdução, Problema, Objetivos e Justificativa): [Artigo](https://www.overleaf.com/6548316254mfvbtfvtnrmr#7125df).

## Sprint 1 - Conhecendo os Dados
**Objetivo:** Identificar, avaliar e extrair a base de dados ideal para o treinamento do modelo preditivo, atualizar o backlog e avançar na escrita acadêmica.

**Entregáveis:**
- **Levantamento de datasets públicos (com justificativa da escolha):** Mapeamento técnico concluído e validado no diretório de dados [data/README.md](data/README.md). A base da SSP-SP foi eleita devido aos microdados georreferenciados. A coleta automatizada é feita via Web Crawler (`src/scraper_ssp_sp.py`).
- **Notebook de Análise Exploratória de Dados (EDA):** Prototipação concluída para validação de completude dos dados espaciais e temporais: [01_exploracao_dados.ipynb](notebooks/01_exploracao_dados.ipynb).
- **Backlog de requisitos priorizado:** Refinamento do backlog com novas histórias de usuário e requisitos funcionais/não-funcionais mapeados (ver Kanban do repositório).
- **Artigo Científico:** Inclusão das seções de Fundamentação Teórica, Trabalhos Relacionados e Metodologia (DSRM): [Artigo (LaTeX)](article/artigo.tex).
