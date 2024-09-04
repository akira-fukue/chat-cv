from openai import OpenAI
import streamlit as st
import fitz  # PyMuPDF para manipulação de PDFs

# Função para extrair texto do PDF
def extract_text_from_pdf(pdf_file):
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
        return text

# Função para detectar o nome do candidato via IA
def detect_candidate_name(pdf_text, client):
    prompt = f"O seguinte texto é o conteúdo de um currículo:\n\n{pdf_text}\n\nPor favor, extraia o nome do candidato:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # Corrigido o acesso à mensagem da resposta
    return response.choices[0].message.content.strip()

# Configuração da sidebar para chave da OpenAI e upload de PDF
st.sidebar.title("Configurações")
uploaded_file = st.sidebar.file_uploader("Envie seu Currículo (PDF)", type="pdf")
openai_api_key = st.sidebar.text_input("Insira sua chave OpenAI", type="password", key="api_key_input")

# Verifica se o PDF foi carregado
if not uploaded_file:
    st.sidebar.warning("Por favor, carregue o currículo para continuar.")
    st.stop()

# Verifica se a chave da API foi fornecida
if not openai_api_key:
    st.sidebar.warning("Por favor, insira sua chave OpenAI para continuar.")
    st.stop()

# Inicializa o cliente da OpenAI
client = OpenAI(api_key=openai_api_key)

# Carregar o conteúdo do PDF
pdf_text = extract_text_from_pdf(uploaded_file)

# Detecta o nome do candidato usando IA
candidate_name = detect_candidate_name(pdf_text, client)

# Atualiza o título com o nome do candidato, se detectado
if candidate_name:
    st.title(f"🥸 Entreviste o Bot do {candidate_name}")
else:
    st.title("🥸 Entreviste o Bot do candidato")

# Notifica que o currículo foi carregado com sucesso
st.sidebar.success("Currículo carregado com sucesso!")

# Inicializa a sessão de mensagens
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens antigas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Função de chat com PDF
if prompt := st.chat_input("Faça uma pergunta sobre o currículo ou outra coisa:"):
    # Adiciona a pergunta do usuário à lista de mensagens
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Envia a pergunta e o conteúdo do PDF para o ChatGPT
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ] + [{"role": "system", "content": f"Este é o conteúdo do currículo: {pdf_text}"}],
            stream=True,
        )
        response = st.write_stream(stream)

    # Adiciona a resposta do assistente à lista de mensagens
    st.session_state.messages.append({"role": "assistant", "content": response})
