import streamlit as st
import base64
import os
from PIL import Image
from groq import Groq
import io

st.set_page_config(
    page_title="HazardLens — Multimodal AI Assistant",
    page_icon="⚡",
    layout="centered"
)

st.markdown("""
<style>
    body { background-color: #0f1117; }
    .main { background-color: #0f1117; }

    .title-block {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .title-block h1 {
        font-size: 2.6rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -1px;
        margin-bottom: 0.2rem;
    }
    .title-block p {
        color: #8b8fa8;
        font-size: 1rem;
        margin: 0;
    }

    .warning-box {
        background: linear-gradient(135deg, #2d1b1b, #1a0f0f);
        border: 1.5px solid #e74c3c;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-top: 1.2rem;
    }
    .warning-box .label {
        color: #e74c3c;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .warning-box .content {
        color: #f5f5f5;
        font-size: 1rem;
        line-height: 1.65;
    }

    .safe-box {
        background: linear-gradient(135deg, #1b2d1b, #0f1a0f);
        border: 1.5px solid #2ecc71;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-top: 1.2rem;
    }
    .safe-box .label {
        color: #2ecc71;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .safe-box .content {
        color: #f5f5f5;
        font-size: 1rem;
        line-height: 1.65;
    }

    .info-box {
        background: #1a1d2e;
        border: 1px solid #2a2d3e;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-top: 1rem;
        color: #8b8fa8;
        font-size: 0.88rem;
        line-height: 1.6;
    }

    .stButton > button {
        background: #e74c3c;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        width: 100%;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #c0392b;
        color: white;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1a1d2e;
        color: #f0f0f0;
        border: 1px solid #2a2d3e;
        border-radius: 8px;
    }

    [data-testid="stFileUploader"] {
        background: #1a1d2e;
        border: 1.5px dashed #2a2d3e;
        border-radius: 10px;
        padding: 0.5rem;
    }

    .divider {
        border: none;
        border-top: 1px solid #2a2d3e;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="title-block">
    <h1>⚡ HazardLens</h1>
    <p>Multimodal AI Assistant — Visual Danger Analysis</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input("Groq API Key", value=GROQ_API_KEY, type="password", placeholder="gsk_...")
    if api_key_input:
        GROQ_API_KEY = api_key_input
    st.markdown('<div class="info-box">Uses <b>LLaMA 3.2 Vision</b> via Groq for fast, free multimodal inference.</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown("""
    1. Upload any image
    2. Ask a question about it
    3. AI infers contextual danger
    """)


def encode_image(image_file) -> str:
    bytes_data = image_file.getvalue()
    return base64.standard_b64encode(bytes_data).decode("utf-8")


def analyze_image(image_b64: str, query: str, api_key: str) -> str:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a safety analysis expert. When given an image and a query, "
                    "you analyze the visual content deeply to identify specific, contextual dangers — "
                    "not just describe what you see. Focus on the real-world risk and consequences. "
                    "Be direct, precise, and actionable. Always explain WHY something is dangerous."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": query
                    }
                ]
            }
        ],
        max_tokens=400,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp"],
    help="Upload any image to analyze for potential hazards"
)

query = st.text_area(
    "Your question",
    value="What is the primary danger shown in this image?",
    height=80,
    placeholder="Ask anything about the image..."
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

st.markdown("")

if st.button("🔍 Analyze Image"):
    if not uploaded_file:
        st.error("Please upload an image first.")
    elif not query.strip():
        st.error("Please enter a question.")
    elif not GROQ_API_KEY:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        with st.spinner("Analyzing image for hazards..."):
            try:
                image_b64 = encode_image(uploaded_file)
                result = analyze_image(image_b64, query.strip(), GROQ_API_KEY)

                danger_keywords = [
                    "danger", "hazard", "risk", "warning", "electrocution",
                    "electric", "shock", "fatal", "injury", "fire", "unsafe",
                    "critical", "severe", "toxic", "explosive", "harmful"
                ]
                is_danger = any(kw in result.lower() for kw in danger_keywords)

                if is_danger:
                    st.markdown(f"""
                    <div class="warning-box">
                        <div class="label">⚠️ Hazard Detected</div>
                        <div class="content">{result}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="safe-box">
                        <div class="label">✅ Analysis Complete</div>
                        <div class="content">{result}</div>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
    <b>About this system</b><br>
    HazardLens uses LLaMA 3.2 Vision (11B) via Groq to perform contextual danger inference — 
    going beyond generic image captioning to identify real-world risks and their consequences.
    Built for the Edxso AI Engineer Intern Assignment 2.
</div>
""", unsafe_allow_html=True)
