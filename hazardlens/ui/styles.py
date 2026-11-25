"""Design system: dark industrial theme with layered depth and subtle 3D motion."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{--bg:#090c11;--s1:#10141b;--s2:#151a23;--bd:#232a36;--tx:#e6e9ef;--mu:#8a93a5;--ac:#f2a33a;
--low:#34a37a;--med:#d6a73a;--high:#e5792e;--crit:#d94a4a;--r:16px;}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--tx);font-family:'Inter',system-ui,sans-serif;}
[data-testid="stAppViewContainer"]::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
background-image:linear-gradient(rgba(255,255,255,.028) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.028) 1px,transparent 1px);
background-size:46px 46px;-webkit-mask-image:radial-gradient(ellipse 75% 55% at 55% 0%,#000 25%,transparent 78%);mask-image:radial-gradient(ellipse 75% 55% at 55% 0%,#000 25%,transparent 78%);}
[data-testid="stAppViewContainer"]::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
background:radial-gradient(600px 300px at 12% -5%,rgba(242,163,58,.10),transparent 70%),radial-gradient(500px 360px at 95% 100%,rgba(217,74,74,.06),transparent 70%);}
[data-testid="stMain"],[data-testid="stSidebar"]{position:relative;z-index:1;}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,.stDeployButton{display:none!important;}
.block-container{padding:2.2rem 2.6rem 3rem!important;max-width:1320px!important;}
h1,h2,h3,h4{font-family:'Inter',sans-serif;letter-spacing:-.02em;}
label[data-testid="stWidgetLabel"] p{color:var(--mu)!important;font-size:12px!important;font-weight:500;}

/* sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d1118,#0a0d12)!important;border-right:1px solid var(--bd);}
[data-testid="stSidebarHeader"]::before{content:"HAZARDLENS";font-weight:800;font-size:15px;letter-spacing:.22em;color:#fff;padding-left:6px;
background:linear-gradient(90deg,#fff,var(--ac));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
[data-testid="stSidebarHeader"]{display:flex;align-items:center;justify-content:space-between;padding-top:18px;}
[data-testid="stSidebar"] hr{border-color:var(--bd);}
.side-note{font-size:11px;color:var(--mu);line-height:1.6;border:1px solid var(--bd);border-radius:12px;padding:10px 12px;background:rgba(255,255,255,.02);}
.side-note b{color:var(--tx);}

/* page header */
.hl-head{display:flex;justify-content:space-between;align-items:center;gap:24px;margin-bottom:26px;padding-bottom:22px;border-bottom:1px solid var(--bd);}
.hl-crumb{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mu);margin-bottom:10px;}
.hl-crumb i{color:var(--ac);font-style:normal;margin:0 4px;}
.hl-title{font-size:clamp(28px,3.4vw,42px);font-weight:800;color:#fff;margin:0 0 8px;padding:0;line-height:1.08;}
.hl-sub{color:var(--mu);font-size:15px;margin:0 0 14px;max-width:620px;line-height:1.55;}
.hl-chips{display:flex;gap:8px;flex-wrap:wrap;}
.hl-chip{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:600;letter-spacing:.04em;padding:4px 11px;border-radius:99px;border:1px solid;white-space:nowrap;}
.hl-label{font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:var(--mu);margin:4px 0 10px;display:flex;align-items:center;gap:10px;}
.hl-label::after{content:"";flex:1;height:1px;background:var(--bd);}

/* 3D scanner art */
.scan{width:210px;height:150px;perspective:640px;flex:none;}
.scan-plane{position:relative;width:176px;height:176px;margin:-6px auto 0;transform:rotateX(63deg) rotateZ(-18deg);transform-style:preserve-3d;}
.scan .ring{position:absolute;border-radius:50%;border:1px solid rgba(242,163,58,.38);}
.scan .r1{inset:0}.scan .r2{inset:24px}.scan .r3{inset:48px}.scan .r4{inset:70px;background:rgba(242,163,58,.22);border-color:rgba(242,163,58,.7);}
.scan .sweep{position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 0deg,rgba(242,163,58,.5),transparent 30%);animation:spin 5s linear infinite;}
.scan .pin{position:absolute;width:9px;height:9px;border-radius:50%;background:var(--crit);box-shadow:0 0 14px var(--crit);transform:translateZ(16px);animation:blip 2.6s ease-in-out infinite;}
.scan .p1{top:34px;left:112px}.scan .p2{top:112px;left:46px;animation-delay:.9s;background:var(--high);box-shadow:0 0 14px var(--high);}
.scan .p3{top:90px;left:130px;animation-delay:1.7s;background:var(--med);box-shadow:0 0 14px var(--med);}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes blip{0%,100%{opacity:.25;transform:translateZ(16px) scale(.8)}50%{opacity:1;transform:translateZ(22px) scale(1.15)}}

/* cards with layered depth */
.hl-card,.hl-kpi,.hl-hz,.hl-panel{background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.012));border:1px solid var(--bd);border-radius:var(--r);
box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 2px 3px rgba(0,0,0,.35),0 22px 44px -16px rgba(0,0,0,.65);
transition:transform .4s cubic-bezier(.2,.8,.2,1),box-shadow .4s,border-color .4s;transform:perspective(1100px) rotateX(0deg);}
.hl-card:hover,.hl-kpi:hover,.hl-hz:hover,.hl-panel:hover{transform:perspective(1100px) rotateX(1.6deg) translateY(-3px);border-color:rgba(242,163,58,.32);
box-shadow:0 1px 0 rgba(255,255,255,.08) inset,0 4px 8px rgba(0,0,0,.4),0 34px 60px -18px rgba(0,0,0,.8);}
.hl-panel{padding:20px 22px;margin-bottom:14px;}
.hl-panel h4{font-size:13px;font-weight:700;color:#fff;margin:0 0 10px;letter-spacing:.01em;}
.hl-panel p,.hl-panel li{color:#c3c9d6;font-size:14px;line-height:1.7;margin:0 0 6px;}
.hl-panel ul{margin:0;padding-left:18px;}
.hl-kpi{padding:18px 20px;position:relative;overflow:hidden;height:100%;}
.hl-kpi::before{content:"";position:absolute;left:0;top:0;right:0;height:2px;background:var(--k,var(--ac));opacity:.9;}
.hl-kpi .k-l{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--mu);}
.hl-kpi .k-v{font-size:34px;font-weight:800;color:var(--k,#fff);line-height:1.1;margin-top:8px;letter-spacing:-.03em;}
.hl-kpi .k-s{font-size:12px;color:var(--mu);margin-top:4px;}
.hl-card{padding:22px 24px;}

/* hazard card */
.hl-hz{padding:16px 18px;margin-bottom:12px;border-left:3px solid var(--c);}
.hz-top{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;}
.hz-ref{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:var(--mu);}
.hz-name{font-weight:700;color:#fff;font-size:16px;}
.hz-sc{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--mu);}
.hz-sc b{color:var(--c);font-size:15px;}
.hz-desc{color:#c3c9d6;font-size:14px;line-height:1.65;margin-bottom:10px;}
.hz-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.hz-grid div{font-size:12.5px;color:var(--mu);line-height:1.55;border-top:1px solid var(--bd);padding-top:8px;}
.hz-grid b{display:block;color:var(--tx);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:3px;font-weight:600;}

/* gauge */
.hl-gauge{position:relative;width:100%;max-width:230px;margin:0 auto;}
.hl-gauge svg{width:100%;display:block;}
.hl-gauge .g-val{position:absolute;left:0;right:0;bottom:6px;text-align:center;font-size:40px;font-weight:800;letter-spacing:-.03em;line-height:1;}
.hl-gauge .g-cap{position:absolute;left:0;right:0;bottom:-18px;text-align:center;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;color:var(--mu);text-transform:uppercase;}

/* matrix */
.mx{display:grid;grid-template-columns:96px repeat(5,1fr);gap:4px;}
.mx-c{position:relative;aspect-ratio:1.5/1;border-radius:8px;border:1px solid;display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap;padding:4px;}
.mx-c em{position:absolute;top:4px;left:7px;font-style:normal;font-size:10px;font-family:'JetBrains Mono',monospace;color:rgba(255,255,255,.55);}
.mx-dot{background:#fff;color:#111;font-weight:800;font-size:11px;border-radius:99px;padding:2px 7px;box-shadow:0 3px 8px rgba(0,0,0,.5);}
.mx-n{font-size:20px;font-weight:800;color:#fff;}
.mx-ax{font-size:10.5px;color:var(--mu);display:flex;flex-direction:column;justify-content:center;line-height:1.3;}
.mx-ax b{color:var(--tx);font-size:12px;}
.mx-ax.x{align-items:center;text-align:center;padding-top:4px;}
.mx-cap{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--mu);text-align:center;margin-top:8px;}

/* bars + table */
.bars .b{display:grid;grid-template-columns:110px 1fr 34px;align-items:center;gap:12px;margin-bottom:11px;font-size:13px;color:#c3c9d6;}
.bars .t{height:8px;border-radius:99px;background:rgba(255,255,255,.06);overflow:hidden;}
.bars .f{height:100%;border-radius:99px;background:var(--c);box-shadow:0 0 12px -2px var(--c);}
.bars .n{font-family:'JetBrains Mono',monospace;color:var(--mu);text-align:right;}
.hl-table{width:100%;border-collapse:collapse;font-size:13px;}
.hl-table th{text-align:left;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--mu);font-weight:500;padding:8px 10px;border-bottom:1px solid var(--bd);}
.hl-table td{padding:11px 10px;border-bottom:1px solid rgba(255,255,255,.04);color:#cdd3df;vertical-align:top;line-height:1.5;}
.hl-table tr:hover td{background:rgba(255,255,255,.02);}
.mono{font-family:'JetBrains Mono',monospace;font-size:12px;}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;font-size:12px;color:var(--mu);}
.legend span::before{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--c);margin-right:6px;}
.sos{display:flex;justify-content:space-between;align-items:center;padding:11px 14px;border-radius:12px;background:rgba(217,74,74,.07);border:1px solid rgba(217,74,74,.22);margin-bottom:8px;}
.sos b{font-family:'JetBrains Mono',monospace;font-size:18px;color:#ff8d8d;}
.sos span{color:#cdd3df;font-size:13.5px;}
.step{display:flex;gap:14px;margin-bottom:14px;}
.step .n{flex:none;width:30px;height:30px;border-radius:9px;background:rgba(242,163,58,.12);border:1px solid rgba(242,163,58,.35);color:var(--ac);font-weight:700;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:13px;}
.step p{margin:0;}.step b{color:#fff;}

/* streamlit widgets */
.st-key-formcard{background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.012));border:1px solid var(--bd);border-radius:20px;padding:26px 28px;margin-bottom:22px;
box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 30px 70px -20px rgba(0,0,0,.8);}
[data-baseweb="select"]>div,.stTextInput input,.stTextArea textarea{background:rgba(255,255,255,.03)!important;border:1px solid var(--bd)!important;border-radius:10px!important;color:var(--tx)!important;}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:rgba(242,163,58,.6)!important;box-shadow:0 0 0 3px rgba(242,163,58,.12)!important;}
[data-testid="stFileUploader"] section{background:rgba(255,255,255,.02)!important;border:1.5px dashed rgba(255,255,255,.14)!important;border-radius:14px!important;}
[data-testid="stFileUploader"] section:hover{border-color:rgba(242,163,58,.55)!important;}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{background:linear-gradient(180deg,#f6b04c,#e08f1c)!important;color:#1b1204!important;border:0!important;border-radius:11px!important;
font-weight:700!important;padding:.62rem 1.2rem!important;width:100%;box-shadow:0 1px 0 rgba(255,255,255,.35) inset,0 8px 20px -6px rgba(242,163,58,.55)!important;transition:all .2s!important;}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stFormSubmitButton"]>button:hover{transform:translateY(-2px);filter:brightness(1.07);box-shadow:0 1px 0 rgba(255,255,255,.4) inset,0 14px 28px -8px rgba(242,163,58,.7)!important;}
.stDownloadButton>button{background:rgba(255,255,255,.04)!important;color:var(--tx)!important;border:1px solid var(--bd)!important;box-shadow:none!important;}
.stDownloadButton>button:hover{border-color:rgba(242,163,58,.6)!important;}
[data-testid="stImage"] img{border-radius:14px!important;border:1px solid var(--bd)!important;box-shadow:0 24px 50px -16px rgba(0,0,0,.85)!important;}
button[data-baseweb="tab"]{font-weight:600!important;color:var(--mu)!important;}
button[data-baseweb="tab"][aria-selected="true"]{color:#fff!important;}
[data-baseweb="tab-highlight"]{background:var(--ac)!important;}
[data-baseweb="tab-border"]{background:var(--bd)!important;}
[data-testid="stStatusWidget"],[data-testid="stExpander"],details{border-color:var(--bd)!important;border-radius:12px!important;}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border:1px solid var(--bd);border-radius:12px;overflow:hidden;}
@media (prefers-reduced-motion:reduce){.scan .sweep,.scan .pin{animation:none}.hl-card,.hl-kpi,.hl-hz,.hl-panel{transition:none}}
@media (max-width:900px){.block-container{padding:1.2rem 1rem 2rem!important}.scan{display:none}.hz-grid{grid-template-columns:1fr}.mx{grid-template-columns:70px repeat(5,1fr)}}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
