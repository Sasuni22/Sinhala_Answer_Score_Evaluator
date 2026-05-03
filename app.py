"""
SinhalaScore AI — Streamlit Application
Offline Intelligent Sinhala Open-Ended Answer Scorer
Ancient Sri Lanka (Anuradhapura Period)
"""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Prevent chromadb from touching Streamlit session state at import time
import chromadb.config
chromadb.config.Settings(anonymized_telemetry=False)
import sys
import os
import logging
import warnings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
logging.getLogger("chromadb").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit.components.v1 as components
import time
import json
import plotly.graph_objects as go

from data.questions import QUESTIONS
from utils.helpers import (
    get_score_grade,
    get_criteria_color,
    format_score_percentage,
    check_ollama_available,
    get_available_ollama_models,
)

st.set_page_config(
    page_title="සිංහල පිළිතුරු ඇගයුම් පද්ධතිය",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# GLOBAL CSS + ANIMATIONS  —  Welcome-page palette carried through
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@300;400;600;700&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+Sinhala:wght@300;400;600&display=swap');

/* ── Root Variables  (welcome-page palette) ── */
:root {
    --bg-primary:      #050709;
    --bg-secondary:    #0c1018;
    --bg-card:         #0f1520;
    --bg-card-hover:   #141c2a;
    --border:          #1e2535;
    --border-active:   #c9a96e;

    --text-primary:    #e8d4a0;
    --text-secondary:  #8b8070;
    --text-muted:      #3d3830;

    /* Gold accent family (from welcome page) */
    --accent-gold:     #c9a96e;
    --accent-gold-lt:  #e8d4a0;
    --accent-gold-dim: rgba(201,169,110,0.55);

    /* Blue kept only for subtle data/tech accents */
    --accent-blue:     #3d8ef8;
    --accent-cyan:     #4fc3f7;
    --accent-green:    #3fb950;
    --accent-yellow:   #d29922;
    --accent-red:      #f85149;
    --accent-purple:   #bc8cff;

    --shadow:          0 8px 32px rgba(0,0,0,0.6);
    --shadow-card:     0 2px 12px rgba(0,0,0,0.5);

    /* Glassmorphism uses gold tint instead of blue */
    --glass-bg:        rgba(15, 21, 32, 0.82);
    --glass-border:    rgba(201,169,110,0.12);
    --glass-blur:      16px;
}

/* ══ Anuradhapura Background ══ */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -2;
    background-image: url('https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Jetavanaramaya_stupa.jpg/1280px-Jetavanaramaya_stupa.jpg');
    background-size: cover;
    background-position: center center;
    background-repeat: no-repeat;
    opacity: 0.10;
    filter: sepia(0.7) brightness(0.6);
}

body::after {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -2;
    background:
        radial-gradient(ellipse at 20% 50%, rgba(201,169,110,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(201,169,110,0.02) 0%, transparent 50%),
        linear-gradient(160deg, rgba(5,7,9,0.88) 0%, rgba(5,7,9,0.75) 50%, rgba(5,7,9,0.90) 100%);
}

#particle-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: -1;
    pointer-events: none;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: #050709 !important;
    color: var(--text-primary) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: rgba(201,169,110,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(201,169,110,0.5); }

.main .block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 100% !important;
    background: transparent !important;
}

/* ══ Glassmorphism Cards  (gold border tint) ══ */
.sl-card {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border) !important;
    border-radius: 2px;          /* cinematic sharp corners */
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(201,169,110,0.06);
    transition: transform 0.22s cubic-bezier(.34,1.56,.64,1),
                border-color 0.22s ease,
                box-shadow 0.22s ease;
    position: relative;
    overflow: hidden;
}

/* Top shimmer line — gold version */
.sl-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,169,110,0.5), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.sl-card:hover {
    transform: translateY(-2px);
    border-color: rgba(201,169,110,0.3) !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6),
                0 0 0 1px rgba(201,169,110,0.08),
                0 0 20px rgba(201,169,110,0.05),
                inset 0 1px 0 rgba(201,169,110,0.08);
}
.sl-card:hover::before { opacity: 1; }

/* ══ Sidebar ══ */
section[data-testid="stSidebar"] {
    background: rgba(5, 7, 9, 0.97) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(201,169,110,0.10) !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* ── Score Ring ── */
.score-ring-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: var(--glass-bg) !important;
    backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: 2px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.score-ring-number {
    font-size: 4rem;
    font-weight: 700;
    color: var(--accent-gold);
    line-height: 1;
    font-family: 'JetBrains Mono', monospace;
}
.score-ring-max {
    font-size: 1.2rem;
    color: var(--text-secondary);
    font-family: 'JetBrains Mono', monospace;
}
.score-ring-grade {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.3em;
    margin-top: 0.5rem;
    font-family: 'Cinzel', serif;
    text-transform: uppercase;
}

/* ── Status Pills ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 0;              /* cinematic, no rounded */
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    font-family: 'Cinzel', serif;
    text-transform: uppercase;
}
.status-online  {
    background: rgba(201,169,110,0.08);
    color: var(--accent-gold);
    border: 1px solid rgba(201,169,110,0.25);
}
.status-pending {
    background: rgba(61,142,248,0.08);
    color: var(--accent-blue);
    border: 1px solid rgba(61,142,248,0.2);
}
.status-complete {
    background: rgba(63,185,80,0.08);
    color: var(--accent-green);
    border: 1px solid rgba(63,185,80,0.2);
}

@keyframes statusPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(201,169,110,0.5); }
    50%      { box-shadow: 0 0 0 5px rgba(201,169,110,0); }
}
.status-online::before {
    content: '';
    display: inline-block;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--accent-gold);
    animation: statusPulse 2.5s infinite;
    margin-right: 2px;
}

/* ── Metric Cards ── */
.metric-row { display: flex; gap: 1rem; margin-top: 1rem; }
.metric-card {
    flex: 1;
    background: rgba(15, 21, 32, 0.85) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(201,169,110,0.10);
    border-radius: 2px;
    padding: 1rem 1.2rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(201,169,110,0.28);
}
.metric-label {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.25em;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-family: 'Cinzel', serif;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent-gold-lt);
    font-family: 'JetBrains Mono', monospace;
}

/* ── Criteria Bars ── */
.criteria-item {
    background: rgba(15, 21, 32, 0.80) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(201,169,110,0.08);
    border-radius: 2px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s ease;
}
.criteria-item:hover { border-color: rgba(201,169,110,0.25); }
.criteria-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
.criteria-name { font-size: 0.85rem; color: var(--text-primary); font-weight: 500; }
.criteria-score { font-size: 0.85rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: var(--accent-gold); }
.criteria-bar-bg { height: 3px; background: rgba(30,37,53,0.9); border-radius: 0; }

.criteria-bar-fill {
    height: 3px;
    border-radius: 0;
    animation: barGrow 0.8s cubic-bezier(.34,1.56,.64,1) forwards;
    transform-origin: left;
}
@keyframes barGrow {
    from { transform: scaleX(0); opacity: 0.5; }
    to   { transform: scaleX(1); opacity: 1; }
}
.criteria-note { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.5rem; font-style: italic; font-family: 'Cormorant Garamond', serif; }

/* ── Section Headers ── */
.section-title {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.35em;
    color: var(--accent-gold-dim);
    text-transform: uppercase;
    font-family: 'Cinzel', serif;
    margin-bottom: 0.8rem;
}

/* ── Improvement Points ── */
.improvement-item {
    background: rgba(15, 21, 32, 0.82) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(201,169,110,0.08);
    border-radius: 2px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.6rem;
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.improvement-item:hover { transform: translateX(3px); border-color: rgba(201,169,110,0.22); }
.improvement-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
.improvement-title { font-size: 0.85rem; font-weight: 600; color: var(--accent-gold-lt); margin-bottom: 0.25rem; }
.improvement-desc  { font-size: 0.78rem; color: var(--text-secondary); }
.improvement-warning { background: rgba(248,81,73,0.06) !important; border-color: rgba(248,81,73,0.22) !important; }

/* ── Ontology Tags ── */
.ontology-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(201,169,110,0.07);
    border: 1px solid rgba(201,169,110,0.20);
    color: var(--accent-gold);
    padding: 3px 10px;
    border-radius: 0;
    font-size: 0.75rem;
    margin: 3px 3px 3px 0;
    font-family: 'Noto Sans Sinhala', sans-serif;
    transition: background 0.2s ease, border-color 0.2s ease;
    letter-spacing: 0.05em;
}
.ontology-tag:hover { background: rgba(201,169,110,0.14); border-color: rgba(201,169,110,0.4); }

/* ── Analysis Text ── */
.analysis-box {
    background: rgba(15, 21, 32, 0.82) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(201,169,110,0.08);
    border-radius: 2px;
    padding: 1.2rem 1.4rem;
    font-size: 0.88rem;
    line-height: 1.80;
    color: var(--text-primary);
    font-family: 'Cormorant Garamond', serif;
}
.key-strength {
    background: rgba(63,185,80,0.06);
    border-left: 2px solid var(--accent-green);
    padding: 0.6rem 0.8rem;
    border-radius: 0;
    margin-top: 1rem;
    font-size: 0.82rem;
    color: var(--accent-green);
}

/* ── Sinhala / Question box ── */
.sinhala-text { font-family: 'Noto Sans Sinhala', sans-serif !important; line-height: 1.9 !important; }
.question-box {
    background: rgba(15, 21, 32, 0.82) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(201,169,110,0.10);
    border-radius: 2px;
    padding: 1rem 1.2rem;
    font-family: 'Noto Sans Sinhala', sans-serif;
    font-size: 0.95rem;
    line-height: 1.9;
    color: var(--text-primary);
    margin-bottom: 0.8rem;
}

/* ── Sidebar ── */
.sidebar-logo {
    padding: 1.4rem 1.4rem 1rem;
    border-bottom: 1px solid rgba(201,169,110,0.10);
    margin-bottom: 0.5rem;
}
.logo-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--accent-gold);
    letter-spacing: 0.04em;
    font-family: 'Cinzel', serif;
    line-height: 1.5;
}
.logo-sub {
    font-size: 0.58rem;
    letter-spacing: 0.35em;
    color: var(--accent-gold-dim);
    text-transform: uppercase;
    font-family: 'Cinzel', serif;
    margin-top: 0.3rem;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #c9a96e, #e8d4a0) !important;
    border-radius: 0 !important;
}

/* ── Text areas ── */
.stTextArea textarea {
    background: rgba(15, 21, 32, 0.92) !important;
    border: 1px solid rgba(201,169,110,0.15) !important;
    color: var(--text-primary) !important;
    border-radius: 2px !important;
    font-family: 'Noto Sans Sinhala', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.8 !important;
    backdrop-filter: blur(8px) !important;
}
.stTextArea textarea:focus {
    border-color: rgba(201,169,110,0.5) !important;
    box-shadow: 0 0 0 2px rgba(201,169,110,0.10) !important;
}
.stSelectbox > div > div {
    background: rgba(15, 21, 32, 0.92) !important;
    border: 1px solid rgba(201,169,110,0.15) !important;
    border-radius: 2px !important;
    color: var(--text-primary) !important;
    backdrop-filter: blur(8px) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 0 !important;
    font-weight: 600 !important;
    font-family: 'Cinzel', serif !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
}
.stButton > button[kind="primary"] {
    background: transparent !important;
    border: 1px solid rgba(201,169,110,0.55) !important;
    color: var(--accent-gold) !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(201,169,110,0.08) !important;
    border-color: rgba(201,169,110,0.9) !important;
    color: var(--accent-gold-lt) !important;
    box-shadow: 0 0 24px rgba(201,169,110,0.12) !important;
    transform: none !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(201,169,110,0.20) !important;
    color: var(--text-secondary) !important;
    backdrop-filter: blur(8px) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(201,169,110,0.45) !important;
    color: var(--accent-gold) !important;
    transform: none !important;
}

/* ── Dividers / Alerts / Spinner ── */
hr { border-color: rgba(201,169,110,0.12) !important; margin: 1rem 0 !important; }
.stAlert { border-radius: 2px !important; backdrop-filter: blur(8px) !important; }
.stSpinner > div { border-top-color: var(--accent-gold) !important; }

/* ── Top header ── */
.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 1.2rem 0;
    border-bottom: 1px solid rgba(201,169,110,0.12);
    margin-bottom: 1.5rem;
}
.top-header-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--accent-gold-lt);
    letter-spacing: 0.08em;
    font-family: 'Cinzel', serif;
}
.top-header-right { display: flex; align-items: center; gap: 0.8rem; }

/* ── Columns ── */
[data-testid="column"] { padding: 0 0.5rem !important; }
[data-testid="column"]:first-child { padding-left: 0 !important; }
[data-testid="column"]:last-child  { padding-right: 0 !important; }

/* ── Report badge / Protocol ── */
.report-badge {
    display: inline-block;
    background: rgba(201,169,110,0.08);
    border: 1px solid rgba(201,169,110,0.22);
    color: var(--accent-gold);
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.3em;
    padding: 3px 10px; border-radius: 0; margin-bottom: 0.8rem;
    font-family: 'Cinzel', serif;
    text-transform: uppercase;
}
.protocol-badge {
    background: rgba(15,21,32,0.82);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(201,169,110,0.10);
    border-radius: 0; padding: 0.7rem 1rem;
    font-size: 0.72rem; color: var(--text-secondary);
    display: flex; align-items: center; gap: 8px;
    font-family: 'Cinzel', serif;
    letter-spacing: 0.12em;
}

/* ══ Keyframe animations ══ */
@keyframes pulse {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.45; }
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes goldShimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
}
@keyframes spinGlow {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes dotBounce {
    0%,80%,100% { transform: scale(0.6); opacity: 0.4; }
    40%          { transform: scale(1.0); opacity: 1.0; }
}

.pulse { animation: pulse 2s infinite; }
.fade-in { animation: fadeSlideIn 0.4s ease forwards; }

/* ══ AI Thinking loader ══ */
.ai-loader {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 1rem;
    gap: 1.2rem;
}
.ai-loader-ring {
    width: 52px; height: 52px;
    border: 2px solid rgba(201,169,110,0.12);
    border-top-color: #c9a96e;
    border-right-color: #e8d4a0;
    border-radius: 50%;
    animation: spinGlow 1.2s linear infinite;
}
.ai-loader-dots {
    display: flex;
    gap: 6px;
    align-items: center;
}
.ai-loader-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent-gold);
    animation: dotBounce 1.4s infinite ease-in-out;
}
.ai-loader-dots span:nth-child(2) { animation-delay: 0.16s; background: var(--accent-gold-lt); }
.ai-loader-dots span:nth-child(3) { animation-delay: 0.32s; background: var(--accent-gold-dim); }
.ai-loader-text {
    font-size: 0.82rem;
    color: var(--accent-gold);
    font-weight: 500;
    letter-spacing: 0.15em;
    text-align: center;
    min-height: 1.4em;
    font-family: 'Cinzel', serif;
    text-transform: uppercase;
}
.ai-loader-subtext {
    font-size: 0.70rem;
    color: var(--text-muted);
    text-align: center;
    letter-spacing: 0.1em;
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
}

/* ══ Shimmer skeleton loader ══ */
.shimmer {
    background: linear-gradient(90deg,
        rgba(15,21,32,0.6) 25%,
        rgba(201,169,110,0.06) 50%,
        rgba(15,21,32,0.6) 75%);
    background-size: 200% auto;
    animation: goldShimmer 2s linear infinite;
    border-radius: 0;
    height: 10px;
    margin-bottom: 8px;
}

/* ══ Score ring entrance animation ══ */
@keyframes ringDraw {
    from { stroke-dasharray: 0 264; }
}
.score-svg-ring { animation: ringDraw 1s cubic-bezier(.34,1.56,.64,1) forwards; }

/* ══ Sidebar nav buttons — gold accent on active ══ */
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    border-color: transparent !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding-left: 1.4rem !important;
    border-radius: 0 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    border-left: 2px solid var(--accent-gold) !important;
    padding-left: calc(1.4rem - 2px) !important;
    color: var(--accent-gold) !important;
    background: rgba(201,169,110,0.05) !important;
}

/* ══ Divider diamond ornament helper ══ */
.ornament-line {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0.6rem 0 1rem;
    opacity: 0.4;
}
.ornament-line hr {
    flex: 1;
    margin: 0 !important;
    border-color: rgba(201,169,110,0.4) !important;
}
.ornament-diamond {
    width: 5px; height: 5px;
    border: 1px solid rgba(201,169,110,0.7);
    transform: rotate(45deg);
    flex-shrink: 0;
}

/* ══ Welcome Page Styles ══ */
@keyframes welcomeFadeUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes welcomeGlow {
    0%, 100% { text-shadow: 0 0 30px rgba(201,169,110,0.2), 0 0 60px rgba(201,169,110,0.05); }
    50%       { text-shadow: 0 0 50px rgba(201,169,110,0.35), 0 0 100px rgba(201,169,110,0.10); }
}
@keyframes borderPulse {
    0%, 100% { border-color: rgba(201,169,110,0.25); box-shadow: 0 0 0 0 rgba(201,169,110,0.15); }
    50%       { border-color: rgba(201,169,110,0.55); box-shadow: 0 0 25px rgba(201,169,110,0.12); }
}
@keyframes runeFloat {
    0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.08; }
    33%       { transform: translateY(-12px) rotate(2deg); opacity: 0.14; }
    66%       { transform: translateY(6px) rotate(-1deg); opacity: 0.06; }
}
@keyframes lineExpand {
    from { width: 0; }
    to   { width: 100%; }
}
@keyframes featureFadeIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
}

.welcome-page {
    min-height: 88vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 2rem;
    position: relative;
    text-align: center;
}

.welcome-eyebrow {
    font-family: 'Cinzel', serif;
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.55em;
    color: rgba(201,169,110,0.5);
    text-transform: uppercase;
    margin-bottom: 2.2rem;
    animation: welcomeFadeUp 0.8s ease forwards;
    animation-delay: 0.1s;
    opacity: 0;
}

.welcome-title-wrap {
    animation: welcomeFadeUp 0.9s ease forwards;
    animation-delay: 0.25s;
    opacity: 0;
    margin-bottom: 0.6rem;
}

.welcome-title-sinhala {
    font-family: 'Noto Sans Sinhala', sans-serif;
    font-size: clamp(2rem, 5vw, 3.4rem);
    font-weight: 600;
    color: #e8d4a0;
    line-height: 1.25;
    animation: welcomeGlow 4s ease-in-out infinite;
    display: block;
    margin-bottom: 0.5rem;
}

.welcome-title-en {
    font-family: 'Cinzel', serif;
    font-size: clamp(0.75rem, 1.8vw, 1.05rem);
    font-weight: 400;
    letter-spacing: 0.28em;
    color: rgba(201,169,110,0.6);
    text-transform: uppercase;
    display: block;
}

.welcome-ornament {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin: 2rem auto;
    width: 360px;
    max-width: 90%;
    animation: welcomeFadeUp 0.9s ease forwards;
    animation-delay: 0.4s;
    opacity: 0;
}
.welcome-ornament-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,169,110,0.4));
}
.welcome-ornament-line.right {
    background: linear-gradient(90deg, rgba(201,169,110,0.4), transparent);
}
.welcome-ornament-diamond {
    width: 7px; height: 7px;
    border: 1px solid rgba(201,169,110,0.6);
    transform: rotate(45deg);
    flex-shrink: 0;
}
.welcome-ornament-dot {
    width: 3px; height: 3px;
    background: rgba(201,169,110,0.4);
    border-radius: 50%;
}

.welcome-desc {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(0.95rem, 2vw, 1.18rem);
    font-style: italic;
    line-height: 1.9;
    color: rgba(232,212,160,0.55);
    max-width: 560px;
    margin: 0 auto 2.8rem;
    animation: welcomeFadeUp 0.9s ease forwards;
    animation-delay: 0.55s;
    opacity: 0;
}

.welcome-features {
    display: flex;
    gap: 1.2rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 3rem;
    animation: welcomeFadeUp 0.9s ease forwards;
    animation-delay: 0.7s;
    opacity: 0;
}
.welcome-feature-chip {
    background: rgba(15, 21, 32, 0.75);
    border: 1px solid rgba(201,169,110,0.12);
    border-radius: 0;
    padding: 0.55rem 1.1rem;
    display: flex;
    align-items: center;
    gap: 8px;
    backdrop-filter: blur(8px);
    transition: border-color 0.25s ease, background 0.25s ease;
}
.welcome-feature-chip:hover {
    border-color: rgba(201,169,110,0.3);
    background: rgba(201,169,110,0.05);
}
.welcome-feature-icon {
    font-size: 0.85rem;
    color: var(--accent-gold);
}
.welcome-feature-text {
    font-family: 'Cinzel', serif;
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    color: rgba(232,212,160,0.6);
    text-transform: uppercase;
}

.welcome-cta-wrap {
    animation: welcomeFadeUp 0.9s ease forwards;
    animation-delay: 0.85s;
    opacity: 0;
}

/* Style the journey button via a wrapper class applied via st.markdown trick */
.welcome-btn-container .stButton > button[kind="primary"] {
    padding: 0.85rem 3rem !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.35em !important;
    border: 1px solid rgba(201,169,110,0.5) !important;
    animation: borderPulse 3s ease-in-out infinite !important;
    position: relative !important;
}
.welcome-btn-container .stButton > button[kind="primary"]::after {
    content: '' !important;
    position: absolute !important;
    bottom: -6px; left: 10%; right: 10% !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(201,169,110,0.4), transparent) !important;
}

.welcome-footer {
    animation: welcomeFadeUp 0.9s ease forwards;
    animation-delay: 1s;
    opacity: 0;
    margin-top: 3rem;
    font-family: 'Cinzel', serif;
    font-size: 0.55rem;
    letter-spacing: 0.3em;
    color: rgba(201,169,110,0.2);
    text-transform: uppercase;
}

/* Floating rune decorations */
.welcome-rune {
    position: absolute;
    font-family: 'Noto Sans Sinhala', sans-serif;
    font-size: 4rem;
    color: rgba(201,169,110,1);
    pointer-events: none;
    user-select: none;
    animation: runeFloat 8s ease-in-out infinite;
}
.welcome-rune.r1 { top: 8%;  left: 5%;  animation-delay: 0s;   font-size: 3rem; }
.welcome-rune.r2 { top: 15%; right: 6%; animation-delay: 2.5s; font-size: 2.5rem; }
.welcome-rune.r3 { bottom: 18%; left: 8%;  animation-delay: 1.2s; font-size: 2rem; }
.welcome-rune.r4 { bottom: 12%; right: 5%; animation-delay: 3.8s; font-size: 3.5rem; }

/* Hide sidebar on welcome page */
.welcome-hide-sidebar section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# Particle Network Background  (gold tinted)
# ══════════════════════════════════════════════════════════════
components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { width:100%; height:100%; overflow:hidden; background:transparent; }
  canvas { position:fixed; top:0; left:0; width:100%; height:100%; }
</style>
</head>
<body>
<canvas id="pc"></canvas>
<script>
(function(){
  const c = document.getElementById('pc');
  const ctx = c.getContext('2d');
  function resize(){ c.width=window.innerWidth; c.height=window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);
  const N=45, D=130, pts=[];
  for(let i=0;i<N;i++) pts.push({
    x:Math.random()*c.width, y:Math.random()*c.height,
    vx:(Math.random()-.5)*.25, vy:(Math.random()-.5)*.25,
    r:Math.random()*1.4+.4, a:Math.random()*.3+.1
  });
  function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    for(const p of pts){
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>c.width) p.vx*=-1;
      if(p.y<0||p.y>c.height) p.vy*=-1;
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(201,169,110,${p.a*0.4})`;
      ctx.fill();
    }
    for(let i=0;i<pts.length;i++){
      for(let j=i+1;j<pts.length;j++){
        const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<D){
          ctx.beginPath();
          ctx.moveTo(pts[i].x,pts[i].y);
          ctx.lineTo(pts[j].x,pts[j].y);
          ctx.strokeStyle=`rgba(232,212,160,${(1-dist/D)*.12})`;
          ctx.lineWidth=.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
</body>
</html>
""", height=0, scrolling=False)

# ──────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "result" not in st.session_state:
    st.session_state.result = None
if "selected_q_idx" not in st.session_state:
    st.session_state.selected_q_idx = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "vector_store_built" not in st.session_state:
    st.session_state.vector_store_built = False
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemma3:1b"


# ──────────────────────────────────────────
# SIDEBAR  (hidden on welcome page)
# ──────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <div class="logo-title">සිංහල පිළිතුරු<br>ඇගයුම් පද්ධතිය</div>
            <div class="logo-sub">Precision Evaluation · v4.2</div>
        </div>
        """, unsafe_allow_html=True)

        pages = [
            ("dashboard",      "⬛", "Dashboard"),
            ("evaluation",     "⚡", "Evaluation"),
            ("marking_guides", "📋", "Marking Guides"),
            ("analytics",      "📊", "Analytics"),
            ("history",        "🕐", "History"),
            ("settings",       "⚙️", "Settings"),
        ]
        for page_id, icon, label in pages:
            if st.button(f"{icon}  {label}", key=f"nav_{page_id}",
                         use_container_width=True, type="secondary"):
                st.session_state.page = page_id
                st.rerun()

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        ollama_ok = check_ollama_available(st.session_state.selected_model)
        status_html = (
            '<span class="status-pill status-online">● System </span>'
            if ollama_ok else
            '<span class="status-pill status-pending">● Ollama Offline</span>'
        )
        st.markdown(f"<div style='padding:0 1.4rem;'>{status_html}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        if st.button("✦  New Evaluation", key="new_eval_btn",
                     use_container_width=True, type="primary"):
            st.session_state.page = "evaluation"
            st.session_state.result = None
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='padding:0.8rem 1.4rem; border-top:1px solid rgba(201,169,110,0.10);'>
            <div style='display:flex; align-items:center; gap:10px;'>
                <div style='width:34px;height:34px;border-radius:0;
                            border: 1px solid rgba(201,169,110,0.4);
                            display:flex;align-items:center;justify-content:center;
                            font-weight:600;font-size:0.85rem;color:#c9a96e;
                            font-family:"Cinzel",serif;
                            background:rgba(201,169,110,0.06);'>A</div>
                <div>
                    <div style='font-size:0.82rem;font-weight:600;color:#e8d4a0;font-family:"Cinzel",serif;'>Admin User</div>
                    <div style='font-size:0.58rem;color:rgba(201,169,110,0.5);letter-spacing:0.22em;font-family:"Cinzel",serif;text-transform:uppercase;'>Chief Examiner</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: WELCOME
# ──────────────────────────────────────────
def render_welcome():
    # Hide sidebar and strip all Streamlit chrome on welcome page
    # Also style the real Streamlit button to look like our CTA
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    .main .block-container { padding: 0 !important; max-width: 100% !important; }

    /* Make the real Streamlit CTA button look exactly like the design */
    div[data-testid="stMainBlockContainer"] .stButton > button {
        font-family: 'Cinzel', serif !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.38em !important;
        text-transform: uppercase !important;
        color: #c9a96e !important;
        background: transparent !important;
        border: 1px solid rgba(201,169,110,0.45) !important;
        border-radius: 0 !important;
        padding: 0.85rem 3rem !important;
        width: auto !important;
        display: block !important;
        margin: 0 auto !important;
        animation: btnPulseReal 3s ease-in-out infinite !important;
        transition: background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s !important;
        cursor: pointer !important;
    }
    div[data-testid="stMainBlockContainer"] .stButton > button:hover {
        background: rgba(201,169,110,0.09) !important;
        border-color: rgba(201,169,110,0.9) !important;
        color: #e8d4a0 !important;
        box-shadow: 0 0 30px rgba(201,169,110,0.16) !important;
    }
    @keyframes btnPulseReal {
        0%,100% { border-color: rgba(201,169,110,0.30); box-shadow: 0 0 0 0 rgba(201,169,110,0.10); }
        50%      { border-color: rgba(201,169,110,0.70); box-shadow: 0 0 25px rgba(201,169,110,0.15); }
    }
    /* Center the button column */
    div[data-testid="stMainBlockContainer"] [data-testid="column"]:nth-child(2) {
        display: flex !important;
        justify-content: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # The full welcome page (everything EXCEPT the button) rendered via components.html
    components.html("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@300;400;600;700&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=Noto+Sans+Sinhala:wght@300;400;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --gold:     #c9a96e;
    --gold-lt:  #e8d4a0;
    --gold-dim: rgba(201,169,110,0.55);
    --bg:       #050709;
    --text-sec: #8b8070;
    --glass:    rgba(15,21,32,0.75);
}

html, body {
    width: 100%; height: 100%;
    background: #050709;
    color: #e8d4a0;
    overflow: hidden;
}

/* ── Background stupa image ── */
body::before {
    content: '';
    position: fixed; inset: 0;
    background-image: url('https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Jetavanaramaya_stupa.jpg/1280px-Jetavanaramaya_stupa.jpg');
    background-size: cover;
    background-position: center;
    opacity: 0.10;
    filter: sepia(0.7) brightness(0.6);
    z-index: 0;
}
body::after {
    content: '';
    position: fixed; inset: 0;
    background:
        radial-gradient(ellipse at 20% 50%, rgba(201,169,110,0.04) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(201,169,110,0.03) 0%, transparent 50%),
        linear-gradient(160deg, rgba(5,7,9,0.92) 0%, rgba(5,7,9,0.78) 50%, rgba(5,7,9,0.93) 100%);
    z-index: 0;
}

canvas#pc { position: fixed; inset: 0; z-index: 1; pointer-events: none; }

/* ── Layout ── */
.page {
    position: relative;
    z-index: 2;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 2rem 2rem;
    text-align: center;
}

/* ── Floating runes ── */
.rune {
    position: fixed;
    font-family: 'Noto Sans Sinhala', sans-serif;
    color: var(--gold);
    pointer-events: none;
    user-select: none;
    animation: runeFloat 8s ease-in-out infinite;
    z-index: 2;
}
.r1 { top: 8%;  left: 5%;  font-size: 2.8rem; animation-delay: 0s;   opacity: 0.10; }
.r2 { top: 14%; right: 6%; font-size: 2.2rem; animation-delay: 2.5s; opacity: 0.08; }
.r3 { bottom: 18%; left: 7%;  font-size: 1.8rem; animation-delay: 1.2s; opacity: 0.07; }
.r4 { bottom: 12%; right: 5%; font-size: 3rem;   animation-delay: 3.8s; opacity: 0.09; }

@keyframes runeFloat {
    0%,100% { transform: translateY(0) rotate(0deg); }
    33%      { transform: translateY(-14px) rotate(2deg); }
    66%      { transform: translateY(7px) rotate(-1deg); }
}

/* ── Animations ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes goldGlow {
    0%,100% { text-shadow: 0 0 30px rgba(201,169,110,0.18), 0 0 60px rgba(201,169,110,0.06); }
    50%      { text-shadow: 0 0 55px rgba(201,169,110,0.38), 0 0 110px rgba(201,169,110,0.12); }
}
@keyframes btnPulse {
    0%,100% { border-color: rgba(201,169,110,0.28); box-shadow: 0 0 0 0 rgba(201,169,110,0.12); }
    50%      { border-color: rgba(201,169,110,0.65); box-shadow: 0 0 28px rgba(201,169,110,0.14); }
}
@keyframes shimmerLine {
    from { background-position: -200% center; }
    to   { background-position:  200% center; }
}

/* ── Eyebrow ── */
.eyebrow {
    font-family: 'Cinzel', serif;
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.55em;
    color: rgba(201,169,110,0.45);
    text-transform: uppercase;
    margin-bottom: 2rem;
    animation: fadeUp 0.8s ease forwards;
    animation-delay: 0.1s;
    opacity: 0;
}

/* ── Title ── */
.title-wrap {
    animation: fadeUp 0.9s ease forwards;
    animation-delay: 0.25s;
    opacity: 0;
    margin-bottom: 0.5rem;
}
.title-sinhala {
    font-family: 'Noto Sans Sinhala', sans-serif;
    font-size: clamp(1.9rem, 4.5vw, 3.2rem);
    font-weight: 600;
    color: #e8d4a0;
    line-height: 1.3;
    display: block;
    margin-bottom: 0.5rem;
    animation: goldGlow 4.5s ease-in-out infinite;
}
.title-en {
    font-family: 'Cinzel', serif;
    font-size: clamp(0.65rem, 1.5vw, 0.95rem);
    font-weight: 400;
    letter-spacing: 0.32em;
    color: rgba(201,169,110,0.5);
    text-transform: uppercase;
    display: block;
}

/* ── Ornament ── */
.ornament {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin: 2rem auto;
    width: 340px;
    max-width: 88%;
    animation: fadeUp 0.9s ease forwards;
    animation-delay: 0.4s;
    opacity: 0;
}
.orn-line { flex: 1; height: 1px; }
.orn-line.left  { background: linear-gradient(90deg, transparent, rgba(201,169,110,0.45)); }
.orn-line.right { background: linear-gradient(90deg, rgba(201,169,110,0.45), transparent); }
.orn-diamond {
    width: 7px; height: 7px;
    border: 1px solid rgba(201,169,110,0.65);
    transform: rotate(45deg);
    flex-shrink: 0;
}
.orn-dot { width: 3px; height: 3px; background: rgba(201,169,110,0.45); border-radius: 50%; }

/* ── Description ── */
.desc {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(0.92rem, 1.8vw, 1.12rem);
    font-style: italic;
    line-height: 1.95;
    color: rgba(232,212,160,0.5);
    max-width: 520px;
    margin: 0 auto 2.6rem;
    animation: fadeUp 0.9s ease forwards;
    animation-delay: 0.55s;
    opacity: 0;
}

/* ── Feature chips ── */
.features {
    display: flex;
    gap: 0.9rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 3rem;
    animation: fadeUp 0.9s ease forwards;
    animation-delay: 0.7s;
    opacity: 0;
}
.chip {
    background: rgba(15,21,32,0.78);
    border: 1px solid rgba(201,169,110,0.13);
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    gap: 7px;
    backdrop-filter: blur(10px);
    transition: border-color 0.25s, background 0.25s;
    cursor: default;
}
.chip:hover { border-color: rgba(201,169,110,0.35); background: rgba(201,169,110,0.06); }
.chip-icon { font-size: 0.85rem; color: var(--gold); }
.chip-text {
    font-family: 'Cinzel', serif;
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    color: rgba(232,212,160,0.58);
    text-transform: uppercase;
}

/* ── Footer ── */
.footer {
    animation: fadeUp 0.9s ease forwards;
    animation-delay: 1s;
    opacity: 0;
    margin-top: 2.8rem;
    font-family: 'Cinzel', serif;
    font-size: 0.52rem;
    letter-spacing: 0.28em;
    color: rgba(201,169,110,0.18);
    text-transform: uppercase;
}
</style>
</head>
<body>

<canvas id="pc"></canvas>

<div class="page">
    <!-- Floating runes -->
    <div class="rune r1">ශ්‍රී</div>
    <div class="rune r2">ල</div>
    <div class="rune r3">ක</div>
    <div class="rune r4">ධ</div>

    <div class="eyebrow">Anuradhapura Period &nbsp;·&nbsp; Ancient Sri Lanka &nbsp;·&nbsp; AI Evaluation</div>

    <div class="title-wrap">
        <span class="title-sinhala">සිංහල පිළිතුරු ඇගයුම් පද්ධතිය</span>
        <span class="title-en">Sinhala Answer Scoring System</span>
    </div>

    <div class="ornament">
        <div class="orn-line left"></div>
        <div class="orn-dot"></div>
        <div class="orn-diamond"></div>
        <div class="orn-dot"></div>
        <div class="orn-line right"></div>
    </div>

    <div class="desc">
        An intelligent offline scoring engine for Sinhala open-ended answers,
        grounded in the history and heritage of the Anuradhapura Kingdom.
        Precision evaluation powered by RAG, ontology reasoning, and local AI.
    </div>

    <div class="features">
        <div class="chip"><span class="chip-icon">◈</span><span class="chip-text">Ontology Reasoning</span></div>
        <div class="chip"><span class="chip-icon">⟡</span><span class="chip-text">RAG Knowledge Base</span></div>
        <div class="chip"><span class="chip-icon">✦</span><span class="chip-text">Offline AI Scoring</span></div>
        <div class="chip"><span class="chip-icon">◉</span><span class="chip-text">Multi-Criteria Analysis</span></div>
    </div>

    <div class="footer">© 2024 SinhalaScore Intelligent Systems &nbsp;·&nbsp; Secure Offline Scoring Environment &nbsp;·&nbsp; v4.2</div>
</div>

<script>
/* ── Particle network ── */
(function(){
    const c = document.getElementById('pc');
    const ctx = c.getContext('2d');
    function resize(){ c.width = window.innerWidth; c.height = window.innerHeight; }
    resize();
    window.addEventListener('resize', resize);
    const N = 48, D = 135, pts = [];
    for(let i = 0; i < N; i++) pts.push({
        x: Math.random()*c.width, y: Math.random()*c.height,
        vx: (Math.random()-.5)*.22, vy: (Math.random()-.5)*.22,
        r: Math.random()*1.5+.4
    });
    function draw(){
        ctx.clearRect(0, 0, c.width, c.height);
        for(const p of pts){
            p.x += p.vx; p.y += p.vy;
            if(p.x < 0 || p.x > c.width)  p.vx *= -1;
            if(p.y < 0 || p.y > c.height) p.vy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
            ctx.fillStyle = 'rgba(201,169,110,0.18)';
            ctx.fill();
        }
        for(let i = 0; i < pts.length; i++){
            for(let j = i+1; j < pts.length; j++){
                const dx = pts[i].x-pts[j].x, dy = pts[i].y-pts[j].y;
                const d = Math.sqrt(dx*dx+dy*dy);
                if(d < D){
                    ctx.beginPath();
                    ctx.moveTo(pts[i].x, pts[i].y);
                    ctx.lineTo(pts[j].x, pts[j].y);
                    ctx.strokeStyle = `rgba(232,212,160,${(1-d/D)*.13})`;
                    ctx.lineWidth = .5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
})();
</script>
</body>
</html>
""", height=560, scrolling=False)

    # Real Streamlit button — fully functional, styled via CSS above
    col_l, col_c, col_r = st.columns([2.5, 1, 2.5])
    with col_c:
        if st.button("✦  Begin Your Journey", key="welcome_cta", type="primary"):
            st.session_state.page = "dashboard"
            st.rerun()

    # Footer text below button
    st.markdown("""
    <div style="text-align:center;margin-top:1.5rem;font-family:'Cinzel',serif;
                font-size:0.52rem;letter-spacing:0.28em;color:rgba(201,169,110,0.18);
                text-transform:uppercase;">
        © 2024 SinhalaScore Intelligent Systems &nbsp;·&nbsp; Secure Offline Scoring &nbsp;·&nbsp; v4.2
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: DASHBOARD
# ──────────────────────────────────────────
def render_dashboard():
    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">ලකුණු වලට පමණක් නොව, අවබෝධයටද වටිනාකමක්</div>
        <div class="top-header-right">
            <span class="status-pill status-online">System</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_main, col_right = st.columns([3, 1.4])

    with col_main:
        st.markdown('<div class="sl-card">', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown('<h3 style="margin:0 0 1rem 0;font-size:1.05rem;font-weight:600;color:#e8d4a0;font-family:\'Cinzel\',serif;letter-spacing:0.06em;">Evaluate Student Answer</h3>', unsafe_allow_html=True)
        with c2:
            st.markdown('<span class="status-pill status-online" style="font-size:0.6rem;">✦ AI Active</span>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Select History Question</div>', unsafe_allow_html=True)
        q_options = [f"{q['id']}: {q['sinhala'][:60]}..." for q in QUESTIONS]
        sel = st.selectbox("Select Question", q_options, index=st.session_state.selected_q_idx,
                           label_visibility="collapsed", key="dash_q_sel")
        st.session_state.selected_q_idx = q_options.index(sel)

        st.markdown('<div class="section-title" style="margin-top:1rem;">Student Response (Sinhala Text)</div>', unsafe_allow_html=True)
        student_answer = st.text_area(
            "Student Answer",
            placeholder="සිසුන්ගේ පිළිතුර මෙහි ඇතුළත් කරන්න...",
            height=160, label_visibility="collapsed", key="dash_answer",
        )
        char_count = len(student_answer)
        st.markdown(f'<div style="text-align:right;font-size:0.72rem;color:var(--text-secondary);margin-top:-0.5rem;margin-bottom:0.8rem;font-family:\'JetBrains Mono\',monospace;">{char_count:,} / 5,000</div>', unsafe_allow_html=True)

        c_btn1, c_btn2 = st.columns([1, 2])
        with c_btn1:
            if st.button("Clear Draft", key="clear_btn", use_container_width=True):
                st.session_state.result = None
                st.rerun()
        with c_btn2:
            if st.button("✦  Begin Evaluation", key="begin_eval_btn",
                         use_container_width=True, type="primary"):
                if not student_answer.strip():
                    st.error("Please enter a student response first.")
                else:
                    st.session_state.eval_answer = student_answer
                    st.session_state.page = "evaluation"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        history = st.session_state.history
        avg_acc = round(sum(r["score"] for r in history) / len(history) * 5, 1) if history else 94.2
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-label">Average</div>
                <div class="metric-value" style="color:var(--accent-gold);">{avg_acc}%</div>
                <div style="height:3px;background:rgba(30,37,53,0.8);border-radius:0;margin-top:8px;">
                    <div style="width:{min(avg_acc,100)}%;height:3px;background:linear-gradient(90deg,#c9a96e,#e8d4a0);border-radius:0;"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Evaluation Speed</div>
                <div class="metric-value">1.2s <span style="font-size:0.85rem;color:var(--text-secondary);">/page</span></div>
                <div style="height:3px;background:rgba(30,37,53,0.8);border-radius:0;margin-top:8px;">
                    <div style="width:45%;height:3px;background:#c9a96e;border-radius:0;"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Vocabulary Depth</div>
                <div class="metric-value" style="font-size:1.1rem;color:var(--accent-gold-lt);">High</div>
                <div style="margin-top:6px;color:var(--accent-gold);font-size:0.9rem;">★★★★☆</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="sl-card" style="min-height:320px;">
            <div style="font-size:0.7rem;font-weight:600;margin-bottom:1.5rem;color:var(--accent-gold-dim);letter-spacing:0.3em;font-family:'Cinzel',serif;text-transform:uppercase;">Analysis Preview</div>
        """, unsafe_allow_html=True)

        if st.session_state.result:
            result = st.session_state.result
            grade, color = get_score_grade(result["score"])
            st.markdown(f"""
            <div style="text-align:center;padding:1rem 0;">
                <div style="font-size:3rem;font-weight:700;color:{color};font-family:'JetBrains Mono',monospace;line-height:1;">{result['score']}</div>
                <div style="font-size:1rem;color:var(--text-secondary);">/20</div>
                <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.25em;color:{color};margin-top:0.5rem;font-family:'Cinzel',serif;text-transform:uppercase;">{grade}</div>
            </div>
            <div style="height:3px;background:rgba(30,37,53,0.8);border-radius:0;margin:1rem 0;">
                <div style="width:{result['score']*5}%;height:3px;border-radius:0;background:{color};"></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:2rem 0;">
                <div style="font-size:2.5rem;opacity:0.18;margin-bottom:1rem;color:#c9a96e;">✦</div>
                <div style="font-size:0.82rem;font-weight:600;color:var(--text-primary);font-family:'Cinzel',serif;letter-spacing:0.08em;">Status: Pending</div>
                <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:0.6rem;line-height:1.7;font-family:'Cormorant Garamond',serif;font-style:italic;">
                    Enter a student response and<br>click 'Begin Evaluation' to initiate<br>the deep-scoring neural network.
                </div>
            </div>
            <div style="height:3px;background:linear-gradient(90deg,#c9a96e 0%,#c9a96e 60%,rgba(30,37,53,0.5) 60%);border-radius:0;margin:0.5rem 0;"></div>
            <div style="height:3px;background:linear-gradient(90deg,#c9a96e 0%,#c9a96e 45%,rgba(30,37,53,0.5) 45%);border-radius:0;margin:0.5rem 0;"></div>
            <div style="height:3px;background:linear-gradient(90deg,#e8d4a0 0%,#e8d4a0 70%,rgba(30,37,53,0.5) 70%);border-radius:0;margin:0.5rem 0;"></div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="protocol-badge" style="margin-top:1rem;">✦ Evaluation Protocol v4.2</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;color:var(--text-muted);font-size:0.68rem;margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(201,169,110,0.08);font-family:'Cinzel',serif;letter-spacing:0.1em;">
        © 2024 SinhalaScore Intelligent Systems · Secure Offline Scoring Environment
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: EVALUATION
# ──────────────────────────────────────────
def render_evaluation():
    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">Evaluation</div>
        <div class="top-header-right"><span class="status-pill status-online">AI Active</span></div>
    </div>
    """, unsafe_allow_html=True)

    ollama_ok = check_ollama_available(st.session_state.selected_model)
    if not ollama_ok:
        st.markdown("""
        <div class="sl-card" style="border-color:rgba(248,81,73,0.25) !important;background:rgba(248,81,73,0.04) !important;">
            <div style="font-size:0.82rem;color:#f85149;font-weight:600;font-family:'Cinzel',serif;letter-spacing:0.1em;">⚠ Ollama Not Available</div>
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.5rem;font-family:'Cormorant Garamond',serif;font-style:italic;">
                Ollama is not running. The system will use keyword-based fallback scoring.<br>
                Run: <code style="font-family:'JetBrains Mono';color:#e8d4a0;">ollama serve</code> and <code style="font-family:'JetBrains Mono';color:#e8d4a0;">ollama pull gemma3:1b</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="sl-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Select History Question</div>', unsafe_allow_html=True)

        q_options = [f"{q['id']}: {q['sinhala'][:60]}..." for q in QUESTIONS]
        sel = st.selectbox("Select Question", q_options, index=st.session_state.selected_q_idx,
                           label_visibility="collapsed", key="eval_q_sel")
        st.session_state.selected_q_idx = q_options.index(sel)
        selected_q = QUESTIONS[st.session_state.selected_q_idx]

        st.markdown(f"""
        <div class="question-box">
            <strong style="font-size:0.58rem;letter-spacing:0.28em;color:var(--accent-gold-dim);font-family:'Cinzel',serif;text-transform:uppercase;">Full Question</strong><br><br>
            {selected_q['sinhala']}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Student Response (Sinhala Text)</div>', unsafe_allow_html=True)
        default_answer = st.session_state.get("eval_answer", "")
        student_answer = st.text_area(
            "Student Answer", value=default_answer,
            placeholder="සිසුන්ගේ පිළිතුර මෙහි ඇතුළත් කරන්න...",
            height=200, label_visibility="collapsed", key="eval_answer_input",
        )
        char_count = len(student_answer)
        st.markdown(f'<div style="text-align:right;font-size:0.72rem;color:var(--text-secondary);margin-top:-0.5rem;margin-bottom:0.8rem;font-family:\'JetBrains Mono\',monospace;">{char_count:,} / 5,000</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("Clear Draft", key="eval_clear", use_container_width=True):
                st.session_state.result = None
                st.session_state.eval_answer = ""
                st.rerun()
        with c2:
            evaluate = st.button("✦  Begin Evaluation", key="eval_submit",
                                 use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if evaluate:
            if not student_answer.strip():
                st.error("Please enter a student response.")
            else:
                _run_evaluation(selected_q, student_answer)

    with col_right:
        _render_result_panel()


def _run_evaluation(question: dict, student_answer: str):
    from agents.pipeline import run_scoring_pipeline

    ai_messages = [
        ("✦", "Retrieving knowledge context..."),
        ("◈", "Extracting ontology concepts..."),
        ("◉", "Analysing answer coverage..."),
        ("⟡", "Scoring each criterion..."),
        ("✧", "Generating feedback..."),
        ("◎", "Validating final score..."),
        ("★", "Evaluation complete!"),
    ]

    progress_bar = st.progress(0)
    loader_slot = st.empty()
    steps_done = [0]
    total_steps = 7

    def progress_callback(step_msg: str):
        steps_done[0] += 1
        progress_val = min(steps_done[0] / total_steps, 1.0)
        progress_bar.progress(progress_val)

        icon, text = ai_messages[min(steps_done[0]-1, len(ai_messages)-1)]
        loader_slot.markdown(f"""
        <div class="sl-card" style="text-align:center; padding:2rem;">
            <div class="ai-loader">
                <div class="ai-loader-ring"></div>
                <div class="ai-loader-dots">
                    <span></span><span></span><span></span>
                </div>
                <div class="ai-loader-text">{icon} &nbsp; {text}</div>
                <div class="ai-loader-subtext">SinhalaScore AI · Deep Neural Scoring Engine</div>
            </div>
            <div style="margin-top:1.2rem;">
                <div class="shimmer" style="width:75%;margin:0 auto 8px;"></div>
                <div class="shimmer" style="width:55%;margin:0 auto 8px;"></div>
                <div class="shimmer" style="width:65%;margin:0 auto;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    try:
        result_msg = run_scoring_pipeline(
            question=question,
            student_answer=student_answer,
            model=st.session_state.selected_model,
            progress_callback=progress_callback,
        )
    except Exception as e:
        progress_bar.empty()
        loader_slot.empty()
        st.error(f"Error during evaluation: {str(e)}")
        return

    progress_bar.progress(1.0)
    time.sleep(0.4)
    progress_bar.empty()
    loader_slot.empty()

    result = {
        "question_id": question["id"],
        "question":    question["sinhala"],
        "answer":      student_answer,
        "score":       result_msg.final_score,
        "breakdown":   result_msg.score_breakdown,
        "explanation": result_msg.explanation,
        "ontology_concepts": result_msg.ontology_concepts,
        "coverage":    result_msg.coverage_report,
        "timestamp":   time.strftime("%Y-%m-%d %H:%M"),
    }
    st.session_state.result = result
    st.session_state.history.append(result)
    st.session_state.page = "report"
    st.rerun()


def _render_result_panel():
    result = st.session_state.result
    st.markdown('<div class="sl-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.68rem;font-weight:600;color:var(--accent-gold-dim);margin-bottom:1rem;letter-spacing:0.3em;font-family:\'Cinzel\',serif;text-transform:uppercase;">Analysis Preview</div>', unsafe_allow_html=True)

    if result:
        grade, color = get_score_grade(result["score"])
        pct = format_score_percentage(result["score"])
        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem 0;" class="fade-in">
            <div style="font-size:3.5rem;font-weight:700;font-family:'JetBrains Mono';color:{color};line-height:1;">{result['score']}</div>
            <div style="font-size:1rem;color:var(--text-secondary);">/20</div>
            <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.25em;color:{color};margin-top:0.4rem;font-family:'Cinzel',serif;text-transform:uppercase;">{grade}</div>
        </div>
        """, unsafe_allow_html=True)
        for b in result["breakdown"][:3]:
            pct_crit = int((b.get("awarded_marks",0) / max(b.get("max_marks",1),1)) * 100)
            c = get_criteria_color(b.get("awarded_marks",0), b.get("max_marks",1))
            st.markdown(f"""
            <div style="margin-bottom:0.6rem;">
                <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:3px;">
                    <span style="color:var(--text-secondary);">{b['criteria'][:35]}...</span>
                    <span style="color:{c};font-family:'JetBrains Mono';">{b.get('awarded_marks',0)}/{b.get('max_marks',0)}</span>
                </div>
                <div style="height:2px;background:rgba(30,37,53,0.8);border-radius:0;">
                    <div style="width:{pct_crit}%;height:2px;background:{c};border-radius:0;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("✦ View Full Report", key="view_report_btn", use_container_width=True, type="primary"):
            st.session_state.page = "report"
            st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
            <div style="font-size:2rem;margin-bottom:1rem;color:rgba(201,169,110,0.2);">✦</div>
            <div style="font-size:0.82rem;color:var(--text-secondary);font-family:'Cormorant Garamond',serif;font-style:italic;line-height:1.7;">
                Enter an answer and click<br><strong style="color:var(--accent-gold-lt);">Begin Evaluation</strong><br>to see results here.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: REPORT
# ──────────────────────────────────────────
def render_report():
    result = st.session_state.result
    if not result:
        st.session_state.page = "evaluation"
        st.rerun()
        return

    grade, grade_color = get_score_grade(result["score"])

    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">Evaluation Report <span style="color:var(--text-secondary);font-weight:400;font-size:0.85rem;">#E-98421</span></div>
    </div>
    """, unsafe_allow_html=True)

    col_main, col_score = st.columns([3.5, 1.5])

    with col_main:
        st.markdown(f"""
        <div class="report-badge">● Scoring Complete</div>
        <div style="font-size:1rem;font-weight:600;margin-bottom:0.6rem;color:var(--accent-gold-lt);font-family:'Cinzel',serif;letter-spacing:0.05em;">
            Analysis of Sinhala Historical Essay — {result['question_id']}
        </div>
        <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.75;margin-bottom:1.5rem;font-family:'Cormorant Garamond',serif;font-style:italic;">
            A sophisticated evaluation of language precision, thematic depth, and structural coherence
            within the submitted response. The automated system has verified the context against the 2024 marking rubric.
        </div>
        """, unsafe_allow_html=True)

        breakdown = result["breakdown"]
        if breakdown:
            cols = st.columns(min(3, len(breakdown)))
            for i, b in enumerate(breakdown[:3]):
                pct_crit = int((b.get("awarded_marks",0) / max(b.get("max_marks",1),1)) * 100)
                c = get_criteria_color(b.get("awarded_marks",0), b.get("max_marks",1))
                note = b.get("justification","")[:50]
                with cols[i]:
                    st.markdown(f"""
                    <div class="criteria-item fade-in">
                        <div class="criteria-header">
                            <span class="criteria-name">{b['criteria'][:30]}</span>
                            <span class="criteria-score" style="color:{c};">{pct_crit}%</span>
                        </div>
                        <div class="criteria-bar-bg">
                            <div class="criteria-bar-fill" style="width:{pct_crit}%;background:{c};"></div>
                        </div>
                        <div class="criteria-note">{note}...</div>
                    </div>
                    """, unsafe_allow_html=True)

    with col_score:
        st.markdown(f"""
        <div class="score-ring-container fade-in">
            <div style="position:relative;width:130px;height:130px;margin-bottom:0.8rem;">
                <svg viewBox="0 0 100 100" style="width:130px;height:130px;transform:rotate(-90deg);">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(30,37,53,0.8)" stroke-width="5"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="{grade_color}" stroke-width="5"
                        stroke-dasharray="{int(result['score']/20*264)} 264"
                        stroke-linecap="square"
                        style="filter:drop-shadow(0 0 5px {grade_color}55);"/>
                </svg>
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;">
                    <div class="score-ring-number">{result['score']}</div>
                    <div class="score-ring-max">/20</div>
                </div>
            </div>
            <div class="score-ring-grade" style="color:{grade_color};">{grade}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    col_analysis, col_improve = st.columns([1.3, 1])

    with col_analysis:
        st.markdown('<div class="section-title">📊 Comprehensive Analysis</div>', unsafe_allow_html=True)
        explanation = result.get("explanation","")
        st.markdown(f'<div class="analysis-box fade-in" style="max-height:320px;overflow-y:auto;">{explanation}</div>', unsafe_allow_html=True)

        if result.get("ontology_concepts"):
            st.markdown('<div class="section-title" style="margin-top:1rem;">◈ Ontology Concepts Detected</div>', unsafe_allow_html=True)
            tags = "".join([f'<span class="ontology-tag">◆ {c["keyword"]}</span>' for c in result["ontology_concepts"]])
            st.markdown(f'<div style="margin-bottom:0.8rem;">{tags}</div>', unsafe_allow_html=True)

        awarded   = sum(b.get("awarded_marks",0) for b in breakdown)
        max_marks = sum(b.get("max_marks",0) for b in breakdown)
        if awarded / max(max_marks,1) >= 0.7:
            st.markdown("""
            <div class="key-strength fade-in">
                <strong style="font-family:'Cinzel',serif;letter-spacing:0.05em;">Key Strength:</strong>
                <span style="font-family:'Cormorant Garamond',serif;font-style:italic;"> Response demonstrates above-average command of historical
                terminology and thematic structure for this grade level.</span>
            </div>
            """, unsafe_allow_html=True)

    with col_improve:
        st.markdown('<div class="section-title">✧ Improvement Points</div>', unsafe_allow_html=True)
        low_criteria = [b for b in breakdown if b.get("awarded_marks",0) / max(b.get("max_marks",1),1) < 0.7]
        improvement_icons = ["✏️","Aₐ","◈","⚠️"]

        if low_criteria:
            for i, b in enumerate(low_criteria[:3]):
                warn_class = "improvement-warning" if i == len(low_criteria)-1 else ""
                icon = improvement_icons[min(i, len(improvement_icons)-1)]
                st.markdown(f"""
                <div class="improvement-item {warn_class} fade-in">
                    <span class="improvement-icon">{icon}</span>
                    <div>
                        <div class="improvement-title">Enhance: {b['criteria'][:40]}</div>
                        <div class="improvement-desc">{b.get('justification','Add more detail.')[:80]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="improvement-item fade-in">
                <span class="improvement-icon">★</span>
                <div>
                    <div class="improvement-title">Excellent Performance</div>
                    <div class="improvement-desc">All criteria met at a high level. Keep up the great work!</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        missing = result.get("coverage",{}).get("missing_topics",[])
        if missing:
            st.markdown(f"""
            <div class="improvement-item improvement-warning fade-in">
                <span class="improvement-icon">⚠️</span>
                <div>
                    <div class="improvement-title">Missing Topics Detected</div>
                    <div class="improvement-desc">{', '.join(missing[:3])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("📄 Download PDF", key="dl_report", use_container_width=True):
            st.info("PDF export — generate via system tools.")
    with c2:
        if st.button("✦ Re-evaluate", key="re_eval", use_container_width=True, type="primary"):
            st.session_state.result = None
            st.session_state.page = "evaluation"
            st.rerun()


# ──────────────────────────────────────────
# PAGE: MARKING GUIDES
# ──────────────────────────────────────────
def render_marking_guides():
    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">Marking Guides</div>
    </div>
    """, unsafe_allow_html=True)

    for q in QUESTIONS:
        with st.expander(f"**{q['id']}** — {q['sinhala'][:70]}..."):
            st.markdown(f'<div class="question-box">{q["sinhala"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Marking Criteria</div>', unsafe_allow_html=True)
            total = 0
            for c in q["marking_guide"]:
                total += c["marks"]
                kws = ", ".join(c.get("keywords",[])[:5]) or "Language quality"
                st.markdown(f"""
                <div class="criteria-item">
                    <div class="criteria-header">
                        <span style="color:var(--text-primary);">{c['criteria']}</span>
                        <span style="font-family:'JetBrains Mono';color:var(--accent-gold);">{c['marks']} marks</span>
                    </div>
                    <div style="font-size:0.78rem;color:var(--text-secondary);font-family:'Cormorant Garamond',serif;font-style:italic;">Keywords: {kws}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.85rem;color:var(--accent-gold-lt);font-family:\'Cinzel\',serif;letter-spacing:0.08em;margin-top:0.5rem;">Total: {total}/20</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: ANALYTICS
# ──────────────────────────────────────────
def render_analytics():
    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    history = st.session_state.history
    if not history:
        st.markdown("""
        <div class="sl-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2rem;margin-bottom:1rem;color:rgba(201,169,110,0.2);">✦</div>
            <div style="color:var(--text-secondary);font-family:'Cormorant Garamond',serif;font-style:italic;">No evaluations completed yet.<br>Complete some evaluations to see analytics.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    scores = [r["score"] for r in history]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(1, len(scores)+1)), y=scores,
        marker_color=['#c9a96e' for _ in scores],
        marker_line_color='rgba(201,169,110,0.4)',
        marker_line_width=1,
        name="Score /20",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#8b8070", font_family="Cinzel",
        xaxis=dict(gridcolor="rgba(30,37,53,0.8)", title="Evaluation #", color="#8b8070"),
        yaxis=dict(gridcolor="rgba(30,37,53,0.8)", title="Score", range=[0,20], color="#8b8070"),
        showlegend=False, margin=dict(l=0,r=0,t=20,b=0), height=250,
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total Evaluations</div><div class="metric-value">{len(scores)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Average Score</div><div class="metric-value">{sum(scores)/len(scores):.1f}/20</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Highest Score</div><div class="metric-value">{max(scores)}/20</div></div>', unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: HISTORY
# ──────────────────────────────────────────
def render_history():
    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">Evaluation History</div>
    </div>
    """, unsafe_allow_html=True)

    history = st.session_state.history
    if not history:
        st.markdown("""
        <div class="sl-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2rem;margin-bottom:1rem;color:rgba(201,169,110,0.2);">✦</div>
            <div style="color:var(--text-secondary);font-family:'Cormorant Garamond',serif;font-style:italic;">No evaluation history yet.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for i, r in enumerate(reversed(history)):
        grade, color = get_score_grade(r["score"])
        st.markdown(f"""
        <div class="sl-card" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">
            <div>
                <div style="font-size:0.82rem;font-weight:600;color:var(--accent-gold-lt);font-family:'Cinzel',serif;letter-spacing:0.05em;">{r['question_id']} — {r['timestamp']}</div>
                <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:0.3rem;font-family:'Cormorant Garamond',serif;font-style:italic;">{r['question'][:60]}...</div>
            </div>
            <div style="text-align:right;flex-shrink:0;margin-left:1rem;">
                <div style="font-size:1.4rem;font-weight:700;color:{color};font-family:'JetBrains Mono';">{r['score']}/20</div>
                <div style="font-size:0.65rem;color:{color};font-family:'Cinzel',serif;letter-spacing:0.15em;">{grade}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# PAGE: SETTINGS
# ──────────────────────────────────────────
def render_settings():
    st.markdown("""
    <div class="top-header fade-in">
        <div class="top-header-title">Settings</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="sl-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🤖 Ollama Model</div>', unsafe_allow_html=True)
        available_models = get_available_ollama_models()
        if available_models:
            model_choice = st.selectbox("Select Model", available_models, index=0, key="model_select")
            st.session_state.selected_model = model_choice
        else:
            st.text_input("Model Name", value=st.session_state.selected_model, key="model_name_input")
            if st.session_state.get("model_name_input"):
                st.session_state.selected_model = st.session_state.model_name_input
        st.markdown(f'<div style="margin-top:0.8rem;font-size:0.78rem;color:var(--text-secondary);">Current model: <code style="font-family:\'JetBrains Mono\';color:var(--accent-gold);">{st.session_state.selected_model}</code></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sl-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📚 Vector Store</div>', unsafe_allow_html=True)
        if st.button("✦ Rebuild Knowledge Base Index", key="rebuild_vs", use_container_width=True, type="primary"):
            with st.spinner("Building vector store..."):
                try:
                    from rag.retriever import build_vector_store
                    build_vector_store(force_rebuild=True)
                    st.session_state.vector_store_built = True
                    st.success("✅ Vector store rebuilt successfully!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="sl-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">◈ Ontology</div>', unsafe_allow_html=True)
        if st.button("✦ Visualize Ontology", key="viz_onto", use_container_width=True, type="primary"):
            try:
                from ontology.anuradhapura_ontology import build_ontology
                g = build_ontology()
                st.success(f"Ontology loaded: {len(g)} triples")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sl-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🗑️ Data Management</div>', unsafe_allow_html=True)
        if st.button("Clear History", key="clear_hist", use_container_width=True):
            st.session_state.history = []
            st.session_state.result = None
            st.success("History cleared.")
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────
# ROUTER / MAIN
# ──────────────────────────────────────────
def main():
    page = st.session_state.page

    # Welcome page: render standalone, no sidebar
    if page == "welcome":
        render_welcome()
        return

    # All other pages: render sidebar first
    render_sidebar()

    if   page == "dashboard":      render_dashboard()
    elif page == "evaluation":     render_evaluation()
    elif page == "report":         render_report()
    elif page == "marking_guides": render_marking_guides()
    elif page == "analytics":      render_analytics()
    elif page == "history":        render_history()
    elif page == "settings":       render_settings()
    else:                          render_dashboard()


if __name__ == "__main__":
    main()