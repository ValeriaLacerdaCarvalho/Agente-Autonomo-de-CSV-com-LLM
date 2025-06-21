# 🤖 Agente Autônomo para Análise de Dados CSV

Um agente autônomo construído com Python, Streamlit e LangChain/Ollama, capaz de responder a perguntas em linguagem natural sobre dados contidos em arquivos CSV.

## 🚀 Funcionalidades Principais

- **Interface Web Interativa:** Criada com Streamlit para fácil utilização.
- **Roteamento Dinâmico de Arquivos:** O agente identifica automaticamente qual(is) arquivo(s) são necessários para responder a uma pergunta, mesmo com nomes de arquivo desconhecidos.
- **Análise de Múltiplos Arquivos:** Capaz de realizar a junção (`merge`) de dados de dois arquivos para responder a perguntas complexas.
- **Geração de Código Inteligente:** Utiliza um LLM para traduzir perguntas em linguagem natural para código Python/pandas executável.
- **Análises Avançadas:** Suporta contagens, somas, médias, buscas por valor máximo e criação de listas "Top N".
- **Execução Local e Segura:** Roda inteiramente na máquina local usando Ollama, garantindo a privacidade dos dados.

## 🛠️ Stack Tecnológico

- **Linguagem:** Python
- **Interface:** Streamlit
- **Orquestração de LLM:** LangChain
- **LLM Local:** Ollama (com o modelo `llama3.2:3b`)
- **Manipulação de Dados:** Pandas

## ⚙️ Instalação e Execução

**Pré-requisitos:**
- Python 3.9+
- Git
- [Ollama](https://ollama.ai/) instalado e em execução.
- O modelo de linguagem necessário baixado: `ollama run llama3.2:3b`

**Passos para Instalação:**

1. Clone o repositório:
   ```bash
   git clone [URL_DO_SEU_REPOSITORIO]
   cd [NOME_DA_PASTA_DO_PROJETO]
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No macOS/Linux:
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute a aplicação Streamlit:
   ```bash
   streamlit run seu_arquivo.py
   ```

A aplicação será aberta em uma nova aba do seu navegador.

## 📝 Como Usar

1. Na barra lateral, faça o upload de um arquivo `.zip` contendo um ou dois arquivos `.csv`.
2. Explore os dados carregados nas abas da coluna da esquerda.
3. Digite sua pergunta em linguagem natural na caixa de texto da direita ou clique em um dos exemplos.
4. Clique em "Analisar" e aguarde a resposta do agente, que aparecerá no histórico.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.