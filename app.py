import streamlit as st
import base64
import os
from groq import Groq

st.set_page_config(
    page_title="HazardLens AI",
    page_icon="⚡",
    layout="wide"
)

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]  # Replace with your actual Groq key

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #020408 !important;
    font-family: 'Inter', sans-serif;
    color: #e8eaf0;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(220,38,38,0.15) 0%, transparent 70%),
        radial-gradient(ellipse 50% 40% at 90% 90%, rgba(239,68,68,0.08) 0%, transparent 60%),
        #020408 !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"],
section[data-testid="stSidebar"], footer { display: none !important; }

[data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

.hero {
    text-align: center;
    padding: 72px 24px 48px;
    position: relative;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(220,38,38,0.12);
    border: 1px solid rgba(220,38,38,0.3);
    border-radius: 100px;
    padding: 6px 16px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #f87171;
    margin-bottom: 28px;
}

.hero-badge .dot {
    width: 6px; height: 6px;
    background: #ef4444;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

.hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(48px, 7vw, 88px);
    font-weight: 700;
    line-height: 1.0;
    letter-spacing: -3px;
    color: #ffffff;
    margin-bottom: 20px;
}

.hero h1 span {
    background: linear-gradient(135deg, #ef4444 0%, #f97316 50%, #fbbf24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 18px;
    color: #64748b;
    font-weight: 400;
    max-width: 480px;
    margin: 0 auto 48px;
    line-height: 1.6;
}

.stats-row {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-bottom: 64px;
    flex-wrap: wrap;
}

.stat-item { text-align: center; }

.stat-num {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
}

.stat-label {
    font-size: 11px;
    color: #475569;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 4px;
}

.stat-divider {
    width: 1px;
    background: #1e2430;
    align-self: stretch;
}

.main-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 40px;
    margin: 0 40px 32px;
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.04),
        0 32px 64px rgba(0,0,0,0.6),
        0 0 80px rgba(220,38,38,0.06),
        inset 0 1px 0 rgba(255,255,255,0.08);
    position: relative;
    overflow: hidden;
}

.main-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(239,68,68,0.5), transparent);
}

.section-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 12px;
}

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1.5px dashed rgba(255,255,255,0.1) !important;
    border-radius: 16px !important;
    transition: all 0.2s !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(239,68,68,0.4) !important;
    background: rgba(239,68,68,0.03) !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #475569 !important;
}

.stTextArea textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    resize: none !important;
    transition: border-color 0.2s !important;
}

.stTextArea textarea:focus {
    border-color: rgba(239,68,68,0.5) !important;
    box-shadow: 0 0 0 3px rgba(239,68,68,0.08) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 16px 40px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    width: 100% !important;
    cursor: pointer !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 16px rgba(220,38,38,0.35), 0 1px 0 rgba(255,255,255,0.1) inset !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #ef4444, #dc2626) !important;
    box-shadow: 0 8px 24px rgba(220,38,38,0.5) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stImage"] img {
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5) !important;
}

.result-danger {
    background: linear-gradient(135deg, rgba(220,38,38,0.1), rgba(185,28,28,0.06));
    border: 1px solid rgba(220,38,38,0.35);
    border-radius: 18px;
    padding: 28px 32px;
    margin: 24px 40px;
    position: relative;
    box-shadow: 0 0 40px rgba(220,38,38,0.08), inset 0 1px 0 rgba(255,255,255,0.05);
}

.result-danger::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(239,68,68,0.6), transparent);
    border-radius: 18px 18px 0 0;
}

.result-safe {
    background: linear-gradient(135deg, rgba(34,197,94,0.08), rgba(21,128,61,0.05));
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 18px;
    padding: 28px 32px;
    margin: 24px 40px;
    position: relative;
    box-shadow: 0 0 40px rgba(34,197,94,0.06), inset 0 1px 0 rgba(255,255,255,0.05);
}

.result-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
    padding: 5px 12px;
    border-radius: 100px;
}

.tag-danger {
    background: rgba(220,38,38,0.2);
    color: #f87171;
    border: 1px solid rgba(220,38,38,0.3);
}

.tag-safe {
    background: rgba(34,197,94,0.15);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.3);
}

.result-text {
    font-size: 16px;
    line-height: 1.75;
    color: #e2e8f0;
    font-weight: 400;
}

.how-section {
    margin: 0 40px 64px;
    padding: 36px 40px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
}

.how-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 28px;
}

.steps-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
}

.step-item { text-align: center; }

.step-icon {
    width: 48px; height: 48px;
    background: rgba(220,38,38,0.1);
    border: 1px solid rgba(220,38,38,0.2);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    margin: 0 auto 12px;
}

.step-title {
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 6px;
}

.step-desc {
    font-size: 12px;
    color: #475569;
    line-height: 1.5;
}

.footer {
    text-align: center;
    padding: 32px 24px 48px;
    border-top: 1px solid rgba(255,255,255,0.05);
    color: #334155;
    font-size: 13px;
}

.footer span { color: #475569; }

#MainMenu { visibility: hidden; }
.stDeployButton { display: none; }
label[data-testid="stWidgetLabel"] { color: #64748b !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="hero">
    <div class="hero-badge">
        <div class="dot"></div>
        AI-Powered Safety Analysis
    </div>
    <h1>Detect Danger<br><span>Instantly.</span></h1>
    <p class="hero-sub"></p>
</div>

<div class="stats-row">
    <div class="stat-item">
        <div class="stat-num">17B</div>
        <div class="stat-label">Vision Parameters</div>
    </div>
    <div class="stat-divider"></div>
    <div class="stat-item">
        <div class="stat-num">&lt;2s</div>
        <div class="stat-label">Inference Time</div>
    </div>
    <div class="stat-divider"></div>
    <div class="stat-item">
        <div class="stat-num">100%</div>
        <div class="stat-label">Context-Aware</div>
    </div>
    <div class="stat-divider"></div>
    <div class="stat-item">
        <div class="stat-num">Free</div>
        <div class="stat-label">Groq Powered</div>
    </div>
</div>
""", unsafe_allow_html=True)


st.markdown('<div class="main-card">', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="section-label">Upload Image</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop image here or click to browse",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        col_l, col_c, col_r = st.columns([1, 4, 1])
        with col_c:
            st.image(uploaded_file, use_column_width=True)

with col2:
    st.markdown('<div class="section-label">Your Query</div>', unsafe_allow_html=True)
    query = st.text_area(
        "Query",
        value="What is the primary danger shown in this image?",
        height=130,
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Model</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
    border-radius:10px;padding:12px 16px;margin-bottom:20px;">
        <div style="font-size:13px;font-weight:600;color:#e2e8f0;">LLaMA 4 Scout · 17B</div>
        <div style="font-size:11px;color:#475569;margin-top:3px;">Groq · Fast inference · Free tier</div>
    </div>
    """, unsafe_allow_html=True)

    analyze = st.button("⚡ Analyze for Hazards")

st.markdown('</div>', unsafe_allow_html=True)


def encode_image(image_file) -> str:
    return base64.standard_b64encode(image_file.getvalue()).decode("utf-8")

def analyze_image(image_b64: str, query: str) -> str:
    import httpx
    client = Groq(api_key=GROQ_API_KEY, http_client=httpx.Client())
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert safety analyst. Analyze the image and respond in this exact format:\n\n"
                    "⚠ Primary Hazard\n"
                    "[One-line hazard title]\n\n"
                    "📝 Why It Is Dangerous\n"
                    "[2-3 sentences explaining the specific risk and what could go wrong]\n\n"
                    "⚡ Immediate Actions\n"
                    "[2-3 specific steps someone should take right now]\n\n"
                    "🛡 Prevention Measures\n"
                    "[2-3 ways to prevent this hazard in future]\n\n"
                    "Keep it direct and practical. No generic advice."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    {"type": "text", "text": query}
                ]
            }
        ],
        max_tokens=500,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

if analyze:
    if not uploaded_file:
        st.error("Please upload an image first.")
    elif not query.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("🔍 Analyzing image — please wait..."):
            try:
                image_b64 = encode_image(uploaded_file)
                result = analyze_image(image_b64, query.strip())

                danger_keywords = [
                    "danger", "hazard", "risk", "warning", "electrocution",
                    "electric", "shock", "fatal", "fire", "unsafe", "critical",
                    "severe", "toxic", "explosive", "harmful", "lethal", "death"
                ]
                is_danger = any(kw in result.lower() for kw in danger_keywords)

                st.success("✅ Analysis Completed Successfully")

                formatted = result.replace("\n", "<br>")

                if is_danger:
                    st.markdown(f"""
                    <div class="result-danger">
                        <div class="result-tag tag-danger">⚠ Hazard Detected</div>
                        <div class="result-text">{formatted}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="result-safe">
                        <div class="result-tag tag-safe">✓ Analysis Complete</div>
                        <div class="result-text">{formatted}</div>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")


st.markdown("""
<div class="how-section">
    <div class="how-title">How it works</div>
    <div class="steps-grid">
        <div class="step-item">
            <div class="step-icon">🖼️</div>
            <div class="step-title">Upload Image</div>
            <div class="step-desc">Any JPG, PNG or WEBP image up to 20MB</div>
        </div>
        <div class="step-item">
            <div class="step-icon">💬</div>
            <div class="step-title">Ask a Question</div>
            <div class="step-desc">Natural language query about the scene</div>
        </div>
        <div class="step-item">
            <div class="step-icon">🧠</div>
            <div class="step-title">AI Inference</div>
            <div class="step-desc">LLaMA 4 Scout reasons about the context</div>
        </div>
        <div class="step-item">
            <div class="step-icon">⚡</div>
            <div class="step-title">Hazard Report</div>
            <div class="step-desc">Specific danger identified with action steps</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
