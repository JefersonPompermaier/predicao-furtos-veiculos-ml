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

## Sprint 2 - MVP Analítico
**Objetivo:** Estabelecer a infraestrutura central de modelagem, criando o Baseline Preditivo para estimar manchas criminais a partir dos dados limpos da malha H3.

**Entregáveis:**
- **Pré-processamento e engenharia de atributos:** Desenvolvido notebook de limpeza de coordenadas e agrupamento de crimes em hexágonos do Uber H3 por semana: [02_pre_processamento.ipynb](notebooks/02_pre_processamento.ipynb).
- **Notebook com treinamento e comparação de modelos (baseline):** Desenvolvido pipeline de Machine Learning (Baseline RandomForestClassifier), comparando precisão, revocação e métrica ROC-AUC devido ao desbalanceamento: [03_modelagem_baseline.ipynb](notebooks/03_modelagem_baseline.ipynb).
- **Kanban do projeto atualizado:** Tarefas correspondentes movidas para a aba "Done" no framework ágil (ver Kanban do repositório).
- **Modelo treinado exportado:** Modelo Baseline congelado em formato binário usando Joblib e versionado em [models/baseline.joblib](models/baseline.joblib).
- **Artigo Científico:** Detalhamento formal na Metodologia sobre como a rotina da DSRM iterou sobre as fases do CRISP-DM para treinar o classificador Random Forest. [Artigo (LaTeX)](article/artigo.tex).

## Sprint 3 - MVP do Produto
**Objetivo:** Desenvolver e disponibilizar a aplicação web MVP em Streamlit consumindo o modelo preditivo baseline treinado na Sprint 2, com interface de mapas térmicos em grade Uber H3 cobrindo o Estado de São Paulo, módulo de modulação horária, consulta pontual e infraestrutura configurada para publicação no Streamlit Community Cloud.

**Entregáveis:**
- **Aplicação MVP em Streamlit:** Interface web contendo abas para visualização geoespacial (Mapa de risco), consulta interativa por coordenadas (Consulta por local) e documentação técnica das métricas e atributos: [app/main.py](app/main.py).
- **Mapeamento Térmico Quente e Frio (Uber H3):** Camadas Pydeck (H3HexagonLayer e HeatmapLayer) com escala térmica (azul a vermelho) parametrizável para densidade de pontos no Estado de São Paulo (até 30.977 hexágonos).
- **Módulo de Análise e Modulação Horária:** Decomposição e ponderação temporal baseada na distribuição empírica de 269.403 ocorrências da SSP-SP em 2023 ([data/SP/processed/perfil_horario.csv](data/SP/processed/perfil_horario.csv)), permitindo avaliar a variação do risco ao longo das 24 horas do dia.
- **Exportação de Relatórios Operacionais:** Funcionalidade de download em CSV com os escores de risco, percentis e contagens de ocorrências por hexágono para planejamento de patrulhamento ostensivo.
- **Configuração e Repositório Pronto para Deploy:** Dependências consolidadas em [requirements.txt](requirements.txt) e definições de inicialização em [.streamlit/config.toml](.streamlit/config.toml) para implantação no Streamlit Community Cloud.
- **Artigo Científico:** Inclusão do capítulo "Adequação ao Ciclo de Vida CRISP-ML(Q)" logo após a Metodologia, correlacionando todas as fases do ciclo de vida às Sprints 0 a 3 com fundamentação teórica: [Artigo (LaTeX)](article/artigo.tex).

### Instruções de Execução Local
1. Obtenha o código e acesse o diretório do projeto:
   ```bash
   git clone https://github.com/JefersonPompermaier/predicao-furtos-veiculos-ml.git
   cd predicao-furtos-veiculos-ml
   ```
2. Crie e ative um ambiente virtual Python:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicie o servidor da aplicação:
   ```bash
   streamlit run app/main.py
   ```
5. Acesse o painel pelo navegador em `http://localhost:8501`.

### Instruções para Deploy no Streamlit Community Cloud
1. Envie as alterações para o repositório remoto na branch `main`:
   ```bash
   git push origin main
   ```
