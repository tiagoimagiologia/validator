import streamlit as st
import easyocr
import fitz
import datetime
import re
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="Validador Completo", layout="centered")
st.title("🏥 Analisador de Prescrições Pro")

@st.cache_resource
def carregar_leitor():
    return easyocr.Reader(['pt'])

reader = carregar_leitor()
arquivo = st.file_uploader("Carregue o PDF", type="pdf")

if arquivo:
    with st.spinner('A analisar todos os campos...'):
        doc = fitz.open(stream=arquivo.read(), filetype="pdf")
        texto_extraido = ""
        for pagina in doc:
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2.5, 2.5)) 
            texto_extraido += " ".join(reader.readtext(pix.tobytes(), detail=0)) + " "

    st.subheader("📋 Relatório de Avaliação")
    texto_min = texto_extraido.lower()

    # --- EXTRAÇÃO DE DADOS ---
    
    # 1. Nome do Utente (Procura entre "Utente:" e "SNS:")
    nome_match = re.search(r'utente:\s*(.*?)\s*(?=sns:)', texto_min)
    nome_exibido = nome_match.group(1).upper() if nome_match else "Não detetado"

    # 2. SNS
    sns_match = re.search(r'\d{9}', texto_extraido)
    
    # 3. Informação Clínica / Motivo
    # Procura o que vem depois de "complementar do exame:" ou "clínica do utente:"
    motivo_match = re.search(r'(?:exame:|clínica:)\s*(.*?)\s*(?=comprovativo|consentimento|assinatura)', texto_min)
    motivo_exibido = motivo_match.group(1) if motivo_match else "Não detetado"

    # 4. Médico e Data
    tem_medico = any(t in texto_min for t in ["méd", "céd", "dr.", "dra.", "prescritor"])
    data_match = re.search(r'(\d{4}/\d{2}/\d{2})|(\d{2}/\d{2}/\d{4})', texto_extraido)

    # --- EXIBIÇÃO ---
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"👤 **Utente:** {nome_exibido}")
        st.write(f"{'✅' if sns_match else '❌'} **SNS:** {sns_match.group(0) if sns_match else '---'}")
        st.write(f"{'✅' if tem_medico else '❌'} **Identificação Médica**")

    with col2:
        st.write(f"📝 **Motivo/Clínica:** {motivo_exibido[:50]}...") # Mostra os primeiros 50 caracteres
        st.write(f"{'✅' if motivo_match else '❌'} **Informação Clínica**")
        if data_match:
            st.success(f"📅 Data: {data_match.group(0)}")
        else:
            st.error("❌ Data não detetada")

    if not motivo_match:
        st.info("💡 Dica: O motivo costuma estar após 'Informação complementar do exame'")

    with st.expander("🔍 Ver texto completo lido"):
        st.write(texto_extraido)
