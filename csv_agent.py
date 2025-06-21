import os
import zipfile
import pandas as pd
import streamlit as st
from pathlib import Path
from langchain.llms import Ollama
import tempfile
import shutil
import traceback
import locale
import re
import ast
import textwrap


def main():
    st.set_page_config(
        page_title="Agente de Análise CSV",
        page_icon="📊",
        layout="wide"
    )
    

class CSVAnalysisAgent:
    def __init__(self):
        """Inicializa o agente com LLM local gratuita (Ollama)"""
        try:
            # Usando Ollama com modelo gratuito
            self.llm = Ollama(model="llama3.2:3b", temperature=0)
            self.dataframes = {}
            self.current_df = None
        except Exception as e:
            st.error(f"Erro ao inicializar LLM: {e}")
            st.info("Certifique-se de ter o Ollama instalado e rodando")
    
    def extract_zip_files(self, zip_path, extract_to):
        """Descompacta arquivos zip"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        except Exception as e:
            st.error(f"Erro ao descompactar: {e}")
            return False
    
    def load_csv_files(self, directory):
        """Carrega todos os arquivos CSV de um diretório"""
        csv_files = {}
        
        for file_path in Path(directory).rglob("*.csv"):
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                # Limpa nomes das colunas
                df.columns = df.columns.str.strip()
                csv_files[file_path.name] = df
                st.success(f"Carregado: {file_path.name} ({len(df)} linhas)")
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                    df.columns = df.columns.str.strip()
                    csv_files[file_path.name] = df
                    st.success(f"Carregado: {file_path.name} ({len(df)} linhas)")
                except Exception as e:
                    st.error(f"Erro ao carregar {file_path.name}: {e}")
            except Exception as e:
                st.error(f"Erro ao carregar {file_path.name}: {e}")
        
        return csv_files
    
    def select_dataframe(self, df_name):
        """Seleciona um DataFrame específico para análise"""
        if df_name in self.dataframes:
            self.current_df = self.dataframes[df_name]
            return True
        return False

    # SUBSTITUA TODA A SUA FUNÇÃO step0_select_file PELA VERSÃO ABAIXO

    def step0_select_file(self, question):
        """ETAPA 0: Seleciona o(s) arquivo(s) usando LÓGICA DE CÓDIGO, sem LLM, e retorna os papéis identificados."""
        
        file_list = list(self.dataframes.keys())
        question_lower = question.lower()

        # Se tiver só 1 arquivo, a escolha é óbvia.
        if len(file_list) == 1:
            # Retorna a informação completa, mesmo para um arquivo
            return {'sucesso': True, 'arquivos_escolhidos': file_list, 'header_file': None, 'items_file': file_list[0]}
        
        # Se tiver 2 arquivos, a heurística é aplicada.
        elif len(file_list) == 2:
            df1_name, df2_name = file_list[0], file_list[1]
            df1, df2 = self.dataframes[df1_name], self.dataframes[df2_name]
            
            # Heurística para identificar papéis
            if len(df1) > len(df2):
                items_file_name, header_file_name = df1_name, df2_name
            else:
                items_file_name, header_file_name = df2_name, df1_name
            
            # Lógica de roteamento baseada em palavras-chave
            header_keywords = ['fornecedor', 'fornecedores', 'nota fiscal', 'notas', 'montante recebido']
            items_keywords = ['item', 'itens', 'produto', 'produtos', 'quantidade', 'valor unitário', 'valor total']

            needs_header = any(keyword in question_lower for keyword in header_keywords)
            needs_items = any(keyword in question_lower for keyword in items_keywords)

            if needs_header and needs_items:
                chosen_files = [items_file_name, header_file_name]
            elif needs_header:
                chosen_files = [header_file_name]
            elif needs_items:
                chosen_files = [items_file_name]
            else:
                # Caso padrão
                chosen_files = [items_file_name]
                
            # Retorna o dicionário completo com os papéis identificados
            return {
                'sucesso': True,
                'arquivos_escolhidos': chosen_files,
                'header_file': header_file_name,
                'items_file': items_file_name
            }

        else:
            # Se tiver mais de 2 arquivos ou nenhum, a lógica atual não suporta.
            return {'sucesso': False, 'erro': 'Esta lógica de roteamento funciona apenas com 1 ou 2 arquivos carregados.'}

    def step1_interpret_question(self, question, selected_files, header_file, items_file):
        """ETAPA 1: LLM interpreta a pergunta e gera código Python usando um prompt mestre com exemplos."""
        
        # Esta função agora retorna apenas a string de código.
        # A lógica de retornar um dicionário foi removida.
        
        # Lógica para lidar com um único arquivo
        if len(selected_files) == 1:
            df_name = selected_files[0]
            self.select_dataframe(df_name)

            dataset_info = f"""
INFORMAÇÕES DO DATASET:
- Nome do DataFrame: df
- Colunas disponíveis: {list(self.current_df.columns)}
"""
            prompt = f"""
Você é um especialista em Python/Pandas que gera pequenos trechos de código para responder a uma pergunta.

{dataset_info}

REGRAS CRÍTICAS E OBRIGATÓRIAS:
1.  O DataFrame `df` já existe. Opere diretamente nele.
2.  O resultado final DEVE ser armazenado em uma variável string chamada `resultado`.
3.  Gere APENAS o código Python. NÃO inclua `import`, `print`, comentários ou qualquer texto de explicação.

---
EXEMPLOS DE GABARITO (Use como guia para responder à pergunta do usuário):

# GABARITO 1: Pergunta sobre CONTAGEM
PERGUNTA: "Quantos itens existem?" ou "Quantas linhas tem o dataset?"
CÓDIGO GERADO:
contagem = len(df)
resultado = f"A contagem de linhas é {{contagem}}."

# GABARITO 2: Pergunta sobre VALOR MÁXIMO
PERGUNTA: "Qual o produto mais caro?"
CÓDIGO GERADO:
linha_maior_valor = df.loc[df['VALOR UNITÁRIO'].idxmax()]
produto = linha_maior_valor['DESCRIÇÃO DO PRODUTO/SERVIÇO']
valor = linha_maior_valor['VALOR UNITÁRIO']
resultado = f"O produto com maior valor unitário é '{{produto}}' com valor de R$ {{valor:.2f}}."

# GABARITO 3: Pergunta sobre TOP N
PERGUNTA: "Mostre o top 5 produtos por quantidade"
CÓDIGO GERADO:
top_5 = df.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum().nlargest(5).reset_index()
resultado = f"O top 5 produtos por quantidade são:\\n{{top_5.to_string(index=False)}}"

# GABARITO 4: Pergunta sobre SOMA TOTAL
PERGUNTA: "Qual a soma dos valores?"
CÓDIGO GERADO:
soma_total = df['VALOR TOTAL'].sum()
resultado = f"A soma total dos valores é {{soma_total}}."

# Trecho a ser ADICIONADO no prompt da step1_interpret_question

# GABARITO 5: Pergunta sobre CONTAGEM DE NOTAS
PERGUNTA: "Quantas notas fiscais foram emitidas?"
CÓDIGO GERADO:
contagem_notas = len(df)
resultado = f"Foram emitidas {{contagem_notas}} notas fiscais."

---
PERGUNTA REAL DO USUÁRIO: "{question}"

CÓDIGO PYTHON (Siga o gabarito mais parecido com a pergunta real):
"""

        # Lógica para lidar com múltiplos arquivos
        else:
            df_cabecalho = self.dataframes[header_file]
            df_itens = self.dataframes[items_file]
            dataset_info = f"""
INFORMAÇÕES DOS DATASETS:
1. DataFrame `df_cabecalho` (do arquivo '{header_file}'):
   - Colunas: {list(df_cabecalho.columns)}
2. DataFrame `df_itens` (do arquivo '{items_file}'):
   - Colunas: {list(df_itens.columns)}
Coluna em comum para junção (merge): 'CHAVE DE ACESSO'
"""
            safety_rules = "REGRAS: Gere APENAS código Python. NÃO use `print`. Salve a resposta na variável `resultado`."
            
            prompt = f"""
            {dataset_info}
            {safety_rules}
            PERGUNTA DO USUÁRIO: "{question}"

            INSTRUÇÃO OBRIGATÓRIA: Primeiro, junte os dataframes com `df_merged = pd.merge(df_cabecalho, df_itens, on='CHAVE DE ACESSO')`. Depois, analise o `df_merged`.

            EXEMPLO DE CÓDIGO:
            df_merged = pd.merge(df_cabecalho, df_itens, on='CHAVE DE ACESSO')
            linha_maior_valor = df_merged.loc[df_merged['VALOR UNITÁRIO'].idxmax()]
            fornecedor = linha_maior_valor['RAZÃO SOCIAL EMITENTE_x']
            produto = linha_maior_valor['DESCRIÇÃO DO PRODUTO/SERVIÇO']
            resultado = f"O fornecedor do item mais caro é '{{fornecedor}}', e o item é '{{produto}}'."

            CÓDIGO PYTHON:
            """

        try:
            response = self.llm.invoke(prompt)
            # Lógica de limpeza robusta
            cleaned_code = response.strip()
            if cleaned_code.startswith('```python'):
                cleaned_code = cleaned_code[len('```python'):].strip()
            if cleaned_code.startswith('`'):
                cleaned_code = cleaned_code.strip('`').strip()
            if cleaned_code.endswith('```'):
                cleaned_code = cleaned_code[:-len('```')].strip()
            return cleaned_code
        except Exception as e:
            return f"Erro na interpretação: {str(e)}"
    def step2_execute_code(self, generated_code, selected_files):
        """ETAPA 2: Executa o código Python gerado pela LLM com validação."""
        
        # Cria um namespace seguro
        namespace = {
            'pd': pd,
            'resultado': None
        }

        # Adiciona os DataFrames necessários ao namespace
        if len(selected_files) == 1:
            namespace['df'] = self.dataframes[selected_files[0]]
        else:
            # Garante que os nomes das variáveis correspondam aos usados no prompt da Etapa 1
            namespace['df_cabecalho'] = self.dataframes['202401_NFs_Cabecalho.csv']
            namespace['df_itens'] = self.dataframes['202401_NFs_Itens.csv']

        try:
            exec(generated_code, namespace)
            resultado = namespace.get('resultado', 'Código executado mas variável resultado não encontrada')
            
            return {
                'sucesso': True,
                'resultado': resultado,
                'codigo_executado': generated_code
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'traceback': traceback.format_exc(),
                'codigo_executado': generated_code
            }    
        

    def step3_generate_response(self, user_question, execution_result):
        """ETAPA 3: Formata números seletivamente e gera resposta textual."""

        if execution_result['sucesso']:
            
            formatted_result = str(execution_result['resultado'])
            
            # --- INÍCIO DA NOVA LÓGICA DE FORMATAÇÃO INTELIGENTE ---
            
            # Por padrão, vamos formatar como moeda, a menos que a pergunta indique o contrário.
            should_format_currency = True
            question_lower = user_question.lower()
            
            # Palavras-chave que indicam que o resultado NÃO é moeda.
            non_currency_keywords = ['quantas', 'contagem', 'top', 'quantidade']
            
            if any(keyword in question_lower for keyword in non_currency_keywords):
                should_format_currency = False
                
            # A formatação de moeda só acontece se a condição for verdadeira
            if should_format_currency:
                try:
                    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
                except locale.Error:
                    try:
                        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252') # Padrão para Windows
                    except locale.Error:
                        pass

                # Procura pelo primeiro número no texto do resultado para formatar
                numbers_found = re.findall(r'(\d+\.?\d*)', formatted_result)
                if numbers_found:
                    number_to_format_str = numbers_found[0]
                    try:
                        number_to_format_float = float(number_to_format_str)
                        # Formata o número como moeda brasileira
                        formatted_currency = locale.currency(number_to_format_float, grouping=True, symbol='R$')
                        # Substitui o número original no texto pelo número formatado
                        formatted_result = formatted_result.replace(number_to_format_str, formatted_currency, 1)
                    except (ValueError, IndexError):
                        pass # Se não for um número válido, não faz nada
            
            # --- FIM DA NOVA LÓGICA DE FORMATAÇÃO INTELIGENTE ---

            prompt = f"""
            Sua tarefa é criar uma frase clara e amigável em português a partir dos dados fornecidos.

            PERGUNTA ORIGINAL DO USUÁRIO: {user_question}
            
            DADOS JÁ FORMATADOS: 
            {formatted_result}

            INSTRUÇÕES:
            - Use os "DADOS JÁ FORMATADOS" para construir sua resposta.
            - Apresente a resposta de forma direta e natural.
            - NÃO mencione aspectos técnicos. Apenas a resposta final.

            Exemplo 1 (Contagem):
            DADOS JÁ FORMATADOS: "A contagem de linhas é 565."
            RESPOSTA FINAL: "Existem 565 linhas de itens no total."

            Exemplo 2 (Moeda):
            DADOS JÁ FORMATADOS: "A soma total dos valores é R$ 3.371.754,84."
            RESPOSTA FINAL: "A soma total dos valores é de R$ 3.371.754,84."

            RESPOSTA FINAL EM PORTUGUÊS:
            """
        else:
            # A lógica de erro continua a mesma
            prompt = f"""       
                Houve um erro ao processar a pergunta: {user_question}
                ERRO: {execution_result['erro']}
                Explique de forma simples que houve um problema...
                RESPOSTA:
                """
        
        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            return f"Erro ao gerar resposta: {str(e)}"

    def query_data(self, question):
        """Método principal que executa o fluxo autônomo completo."""
        
        if not self.dataframes:
            return "Por favor, carregue primeiro os arquivos CSV."
        
        with st.expander("🔍 Debug - Processo Autônomo Completo"):
            
            st.write("**ETAPA 0: Agente selecionando o(s) arquivo(s)...**")
            selection_result = self.step0_select_file(question)
            
            if not selection_result['sucesso']:
                error_message = f"Não consegui determinar qual arquivo usar. Detalhe: {selection_result['erro']}"
                st.error(error_message)
                return error_message

            arquivos_escolhidos = selection_result['arquivos_escolhidos']
            header_file = selection_result.get('header_file')
            items_file = selection_result.get('items_file')
            st.success(f"✅ Arquivo(s) escolhido(s): {arquivos_escolhidos}")


            st.write("**ETAPA 1: Interpretando pergunta e gerando código...**")
            generated_code = self.step1_interpret_question(question, arquivos_escolhidos, header_file, items_file)
            st.code(generated_code, language='python')
            
            st.write("**ETAPA 2: Executando código...**")
            execution_result = self.step2_execute_code(generated_code, arquivos_escolhidos)
            
            if execution_result['sucesso']:
                st.success("✅ Código executado com sucesso!")
                st.write(f"**Resultado:** {execution_result['resultado']}")
            else:
                st.error("❌ Erro na execução do código gerado:")
                st.code(execution_result['erro'])
                if 'traceback' in execution_result:
                    st.code(execution_result['traceback'])
            
            st.write("**ETAPA 3: Gerando resposta final...**")
        
        final_response = self.step3_generate_response(question, execution_result)
        
        return final_response
    
    def get_dataframe_info(self, df_name):
        """Retorna informações sobre um DataFrame"""
        if df_name in self.dataframes:
            df = self.dataframes[df_name]
            info = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "sample": df.head(5).to_dict('records'),
                "total_rows": len(df),
                "memory_usage": df.memory_usage(deep=True).sum()
            }
            return info
        return None
    
    def get_quick_stats(self, df_name):
        """Retorna estatísticas rápidas sem usar o agente"""
        if df_name in self.dataframes:
            df = self.dataframes[df_name]
            stats = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "numeric_columns": len(df.select_dtypes(include=['number']).columns),
                "text_columns": len(df.select_dtypes(include=['object']).columns),
                "null_values": df.isnull().sum().sum(),
                "duplicated_rows": df.duplicated().sum()
            }
            return stats
        return None

    def get_column_analysis(self, df_name):
        """Retorna análise detalhada das colunas para ajudar na identificação"""
        if df_name in self.dataframes:
            df = self.dataframes[df_name]
            analysis = {}
            
            for col in df.columns:
                analysis[col] = {
                    "tipo": str(df[col].dtype),
                    "valores_unicos": df[col].nunique(),
                    "nulos": df[col].isnull().sum(),
                    "exemplo": str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "N/A"
                }
            
            return analysis
        return None


def main():   
    if 'history' not in st.session_state:
        st.session_state.history = []

    st.title("🤖 Agente Inteligente para Análise de CSV")
    st.markdown("### 🔄 Sistema em 3 Etapas: Pergunta → Código → Execução → Resposta")
    
    # Inicializa o agente
    if 'agent' not in st.session_state:
        st.session_state.agent = CSVAnalysisAgent()
    
    agent = st.session_state.agent
    
    # Sidebar para upload e configuração
    with st.sidebar:
        st.header("📁 Carregar Dados")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Faça upload de arquivo ZIP ou CSV",
            type=['zip', 'csv'],
            help="Aceita arquivos ZIP contendo CSVs ou arquivos CSV individuais"
        )
        
        if uploaded_file:
            # Cria diretório temporário
            temp_dir = tempfile.mkdtemp()
            
            try:
                if uploaded_file.name.endswith('.zip'):
                    # Salva arquivo ZIP
                    zip_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(zip_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Descompacta
                    extract_dir = os.path.join(temp_dir, 'extracted')
                    if agent.extract_zip_files(zip_path, extract_dir):
                        # Carrega CSVs
                        agent.dataframes = agent.load_csv_files(extract_dir)
                else:
                    # Arquivo CSV individual
                    csv_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(csv_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    agent.dataframes = agent.load_csv_files(temp_dir)
                
                st.success(f"Carregados {len(agent.dataframes)} arquivo(s) CSV")
                
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")
    
    # Interface principal
    if agent.dataframes:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.header("📋 Arquivos Disponíveis")
            
            # Seleção de arquivo
            selected_file = st.selectbox(
                "Escolha um arquivo para analisar:",
                list(agent.dataframes.keys())
            )
            
            if selected_file:
                agent.select_dataframe(selected_file)
                
            # CÓDIGO NOVO (com Abas)

            # ... seu código da col1 ...

            # 1. Criamos todas as abas em uma única linha
            tab_geral, tab_colunas, tab_dados = st.tabs(["Visão Geral", "Análise das Colunas", "Amostra dos Dados"])

            # 2. Abrimos um bloco 'with' para cada aba e movemos o conteúdo para dentro
            with tab_geral:
                # Mova para cá o código que estava no expander "Informações do Arquivo"
                st.subheader("Visão Geral do Arquivo") # Adiciona um título dentro da aba
                info = agent.get_dataframe_info(selected_file)
                stats = agent.get_quick_stats(selected_file)
                
                col_metrica1, col_metrica2 = st.columns(2)
                col_metrica1.metric("Total de Linhas", stats['total_rows'])
                col_metrica2.metric("Total de Colunas", stats['total_columns'])
                # ... continue com as outras informações ...

            with tab_colunas:
                # Mova para cá o código que estava no expander "Análise das Colunas"
                st.subheader("Análise Detalhada de Cada Coluna")
                col_analysis = agent.get_column_analysis(selected_file)
                if col_analysis:
                    for col, details in col_analysis.items():
                        st.write(f"**{col}** (`{details['tipo']}`)")
                        st.write(f"  - Valores únicos: {details['valores_unicos']} | Nulos: {details['nulos']}")
                        # ...

            with tab_dados:
                # Mova para cá o código que estava no expander "Preview dos Dados"
                st.subheader("Amostra dos Dados Brutos")
                st.dataframe(agent.current_df) # Mostrando o dataframe inteiro na aba
        
        # SUBSTITUA TODO O SEU BLOCO "with col2:" POR ESTE

        # SUBSTITUA TODO O SEU BLOCO "with col2:" POR ESTE

        # SUBSTITUA TODO O SEU BLOCO "with col2:" PELA VERSÃO ABAIXO

        with col2:
            st.header("💬 Faça sua Pergunta")
            
            # --- INÍCIO DA NOVA LÓGICA DE SINALIZADOR ---

            # Verifica se a bandeira para limpar o texto foi levantada na execução anterior
            if st.session_state.get("clear_text_box_flag", False):
                st.session_state.question_input = ""  # Limpa o estado da caixa de texto
                st.session_state.clear_text_box_flag = False # Abaixa a bandeira

            # --- FIM DA NOVA LÓGICA DE SINALIZADOR ---
            
            st.markdown("""
            **🔄 Como funciona:**
            1. **Análise de Dados:** Explore os detalhes do arquivo carregado na coluna à esquerda.
            2. **Pergunta:** Escreva sua pergunta em linguagem natural na caixa de texto.
            3. **Resposta:** O agente irá analisar e a resposta aparecerá no histórico abaixo.
            """)
            
            # Botões de exemplo voltam a ser simples
            with st.expander("Exemplos de Perguntas Sugeridas"):
                examples = [
                    "Quantas linhas de itens existem?",
                    "Qual produto tem o maior valor unitário?",
                    "Qual o fornecedor com maior montante recebido?",
                    "Mostre o top 5 produtos por quantidade",
                    "Qual o nome do fornecedor do item mais caro?"
                ]
                for example in examples:
                    if st.button(example, key=f"ex_{example}"):
                        st.session_state.question_input = example
                        st.rerun()

            # Input da pergunta controlado pela 'key'
            st.text_area(
                "Sua pergunta:",
                key="question_input",
                height=100,
                placeholder="Digite sua pergunta sobre os dados..."
            )
            
            # Botão Analisar agora simplesmente levanta a bandeira
            if st.button("🔍 Analisar", type="primary"):
                question = st.session_state.question_input
                if question:
                    with st.spinner("🤖 Agente pensando... (Etapas 0 a 3)"):
                        response = agent.query_data(question)
                        st.session_state.history.append({"pergunta": question, "resposta": response})
                        # Apenas levanta a bandeira para limpar na próxima execução
                        st.session_state.clear_text_box_flag = True
                        st.rerun()
                else:
                    st.warning("Por favor, digite uma pergunta.")

            # O código para exibir o histórico continua o mesmo
            st.markdown("---")
            st.subheader("Histórico da Análise")

            if st.session_state.history:
                for item in reversed(st.session_state.history):
                    with st.chat_message("user"):
                        st.markdown(item['pergunta'])
                    with st.chat_message("assistant", avatar="📊"):
                        st.markdown(item['resposta'])
            else:
                st.info("O histórico de suas análises aparecerá aqui.")    
    else:
        st.info("👆 Faça upload de um arquivo CSV ou ZIP contendo CSVs para começar")
        
        # Instruções
        with st.expander("📖 Como usar"):
            st.write("""
            **Sistema em 3 Etapas:**
            
            1. **📝 Pergunta:** Você faz uma pergunta em linguagem natural
            2. **🧠 Interpretação:** LLM analisa e gera código Python específico
            3. **⚡ Execução:** Código é executado no dataset real
            4. **💬 Resposta:** LLM transforma o resultado em resposta clara
            
            **Vantagens desta abordagem:**
            - ✅ Maior precisão nas respostas
            - ✅ Transparência total (você vê o código gerado)
            - ✅ Menos erros de parsing
            - ✅ Resultados baseados nos dados reais
            
            **Exemplos de perguntas suportadas:**
            - Quantas linhas tem o dataset?
            - Qual é o maior valor na coluna X?
            - Mostre estatísticas descritivas
            - Qual categoria tem mais itens?
            - Some os valores da coluna Y
            """)

# Configuração para executar
if __name__ == "__main__":
    # Instruções de instalação
    st.sidebar.markdown("""
    ### 🛠️ Pré-requisitos
    
    **Instalar dependências:**
    ```bash
    pip install streamlit langchain pandas ollama
    ```
    
    **Instalar Ollama (LLM gratuita):**
    ```bash
    # Linux/Mac
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Windows: baixar do site ollama.ai
    ```
    
    **Baixar modelo:**
    ```bash
    ollama run llama3.2:3b
    ```
    """)
    
    main()