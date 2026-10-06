import os
import re
import json
import time
from typing import Tuple

import streamlit as st
import pymupdf
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ==============================================================================
# 1. ENTERPRISE CONFIGURATION
# ==============================================================================
AGENT_NAME = "CVision"
MODEL_NAME = "gemini-3.6-flash"

st.set_page_config(
    page_title=f"{AGENT_NAME} | Autonomous Talent Intelligence Agent",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Safe API Key Resolution from .streamlit/secrets.toml or Environment
API_KEY = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not API_KEY:
    API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ==============================================================================
# 2. DESIGN SYSTEM & MODERN UI PALETTE
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stMarkdown {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #F8FAFC;
    }

    /* Ambient Cyber-Slate Background */
    .stApp {
        background: radial-gradient(ellipse 90% 60% at 50% -10%, #171E38 0%, #080B12 100%);
        background-attachment: fixed;
        overflow-x: hidden;
    }

    /* Floating Background Resumes */
    .bg-resume-1 {
        position: fixed;
        top: 10%;
        left: -35px;
        width: 190px;
        height: 270px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        transform: rotate(-14deg);
        z-index: 0;
        pointer-events: none;
        animation: floatA 15s ease-in-out infinite;
        padding: 18px;
    }
    .bg-resume-2 {
        position: fixed;
        top: 48%;
        right: -45px;
        width: 220px;
        height: 310px;
        background: rgba(255, 255, 255, 0.018);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        transform: rotate(13deg);
        z-index: 0;
        pointer-events: none;
        animation: floatB 18s ease-in-out infinite;
        padding: 20px;
    }
    .doc-skeleton {
        height: 6px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .doc-skeleton-title {
        height: 12px;
        width: 55%;
        background: rgba(56, 189, 248, 0.2);
        border-radius: 4px;
        margin-bottom: 18px;
    }

    @keyframes floatA {
        0%, 100% { transform: translateY(0px) rotate(-14deg); }
        50% { transform: translateY(-24px) rotate(-11deg); }
    }
    @keyframes floatB {
        0%, 100% { transform: translateY(0px) rotate(13deg); }
        50% { transform: translateY(-28px) rotate(16deg); }
    }

    /* Top Centered Header */
    .top-header-center {
        text-align: center;
        margin-bottom: 24px;
        position: relative;
        z-index: 1;
    }
    .top-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 16px;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7DD3FC;
        margin-bottom: 10px;
    }
    .agent-main-title {
        font-size: 3.4rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #FFFFFF 0%, #38BDF8 45%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .agent-subtitle {
        font-size: 1.02rem;
        color: #94A3B8;
        font-weight: 400;
    }

    /* Multi-Agent Swarm Status Ribbon */
    .agent-swarm-ribbon {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 26px;
        position: relative;
        z-index: 1;
    }
    .swarm-bot-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.25s ease;
    }
    .swarm-bot-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.15);
    }
    .bot-avatar-box {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .bot-name {
        font-size: 0.88rem;
        font-weight: 700;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .bot-duty {
        font-size: 0.74rem;
        color: #94A3B8;
        margin-top: 2px;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }

    /* Professional Job Requisition Section */
    .requisition-panel {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
        position: relative;
        z-index: 1;
    }
    .req-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .req-tag-level { background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .req-tag-dept { background: rgba(168, 85, 247, 0.15); color: #D8B4FE; border: 1px solid rgba(168, 85, 247, 0.3); }

    /* Streamlit Input Styling */
    .stTextArea textarea {
        background: rgba(10, 15, 26, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #F1F5F9 !important;
        font-size: 0.88rem !important;
        line-height: 1.6 !important;
        padding: 14px !important;
    }
    .stTextArea textarea:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }

    [data-testid="stFileUploader"] section {
        background: rgba(10, 15, 26, 0.6) !important;
        border: 2px dashed rgba(56, 189, 248, 0.35) !important;
        border-radius: 14px !important;
        padding: 24px !important;
    }

    /* Primary CTA */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0284C7 0%, #6366F1 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 30px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 28px -4px rgba(2, 132, 199, 0.6) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 14px 34px -4px rgba(2, 132, 199, 0.8) !important;
    }

    /* Score Gauge */
    .gauge-wrapper {
        position: relative;
        width: 150px;
        height: 150px;
        margin: 0 auto 10px auto;
    }
    .gauge-svg {
        transform: rotate(-90deg);
        width: 150px;
        height: 150px;
    }
    .gauge-bg {
        fill: none;
        stroke: rgba(255, 255, 255, 0.07);
        stroke-width: 10;
    }
    .gauge-fill {
        fill: none;
        stroke-width: 10;
        stroke-linecap: round;
        transition: stroke-dashoffset 1s ease;
    }
    .gauge-center-box {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
    }
    .gauge-score-val {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.03em;
    }

    .clean-card {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        position: relative;
        z-index: 1;
    }
    .quote-box {
        margin-top: 8px;
        background: rgba(7, 11, 20, 0.7);
        border-left: 2px solid #38BDF8;
        padding: 10px 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.83rem;
        color: #CBD5E1;
        border-radius: 0 8px 8px 0;
    }
</style>

<!-- Floating Ambient Background Resumes -->
<div class="bg-resume-1">
    <div class="doc-skeleton-title"></div>
    <div class="doc-skeleton" style="width: 85%;"></div>
    <div class="doc-skeleton" style="width: 95%;"></div>
    <div class="doc-skeleton" style="width: 70%;"></div>
    <div class="doc-skeleton" style="width: 90%;"></div>
</div>
<div class="bg-resume-2">
    <div class="doc-skeleton-title" style="width: 60%; background: rgba(56, 189, 248, 0.2);"></div>
    <div class="doc-skeleton" style="width: 92%;"></div>
    <div class="doc-skeleton" style="width: 78%;"></div>
    <div class="doc-skeleton" style="width: 88%;"></div>
    <div class="doc-skeleton" style="width: 65%;"></div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. TOP CENTERED TITLE & MULTI-AGENT SWARM
# ==============================================================================
st.markdown(f"""
<div class="top-header-center">
    <div class="top-eyebrow">
        <span>👁️</span> Autonomous Talent Intelligence Engine • SRICL Grounded
    </div>
    <div class="agent-main-title">{AGENT_NAME}</div>
    <div class="agent-subtitle">Next-Gen Resume Analysis, De-Biased Skill Extraction & Candidate Alignment</div>
</div>

<!-- Dynamic Agent Swarm Banner -->
<div class="agent-swarm-ribbon">
    <div class="swarm-bot-card">
        <div class="bot-avatar-box" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3);">
            <svg width="24" height="24" viewBox="0 0 64 64" fill="none">
                <rect x="16" y="18" width="32" height="28" rx="8" fill="#0369A1" stroke="#38BDF8" stroke-width="3"/>
                <circle cx="26" cy="30" r="3.5" fill="#38BDF8"/>
                <circle cx="38" cy="30" r="3.5" fill="#38BDF8"/>
                <line x1="32" y1="8" x2="32" y2="18" stroke="#38BDF8" stroke-width="3"/>
                <circle cx="32" cy="7" r="3" fill="#38BDF8"/>
            </svg>
        </div>
        <div class="bot-details">
            <div class="bot-name">IngestBot <span style="font-size:0.65rem; color:#38BDF8;">● ONLINE</span></div>
            <div class="bot-duty">PDF Document & OCR Stream</div>
        </div>
    </div>
    <div class="swarm-bot-card">
        <div class="bot-avatar-box" style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3);">
            <svg width="24" height="24" viewBox="0 0 64 64" fill="none">
                <rect x="16" y="18" width="32" height="28" rx="8" fill="#B45309" stroke="#F59E0B" stroke-width="3"/>
                <circle cx="26" cy="30" r="3.5" fill="#FBBF24"/>
                <circle cx="38" cy="30" r="3.5" fill="#FBBF24"/>
                <line x1="32" y1="8" x2="32" y2="18" stroke="#F59E0B" stroke-width="3"/>
                <circle cx="32" cy="7" r="3" fill="#FBBF24"/>
            </svg>
        </div>
        <div class="bot-details">
            <div class="bot-name">GuardianBot <span style="font-size:0.65rem; color:#F59E0B;">● ACTIVE</span></div>
            <div class="bot-duty">Anti-Bias PII Redaction Gate</div>
        </div>
    </div>
    <div class="swarm-bot-card">
        <div class="bot-avatar-box" style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3);">
            <svg width="24" height="24" viewBox="0 0 64 64" fill="none">
                <rect x="16" y="18" width="32" height="28" rx="8" fill="#7E22CE" stroke="#A855F7" stroke-width="3"/>
                <circle cx="26" cy="30" r="3.5" fill="#D8B4FE"/>
                <circle cx="38" cy="30" r="3.5" fill="#D8B4FE"/>
                <line x1="32" y1="8" x2="32" y2="18" stroke="#A855F7" stroke-width="3"/>
                <circle cx="32" cy="7" r="3" fill="#D8B4FE"/>
            </svg>
        </div>
        <div class="bot-details">
            <div class="bot-name">VerifierBot <span style="font-size:0.65rem; color:#A855F7;">● LOCKED</span></div>
            <div class="bot-duty">SRICL Anti-Hallucination Sentinel</div>
        </div>
    </div>
    <div class="swarm-bot-card">
        <div class="bot-avatar-box" style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);">
            <svg width="24" height="24" viewBox="0 0 64 64" fill="none">
                <rect x="16" y="18" width="32" height="28" rx="8" fill="#047857" stroke="#10B981" stroke-width="3"/>
                <circle cx="26" cy="30" r="3.5" fill="#34D399"/>
                <circle cx="38" cy="30" r="3.5" fill="#34D399"/>
                <line x1="32" y1="8" x2="32" y2="18" stroke="#10B981" stroke-width="3"/>
                <circle cx="32" cy="7" r="3" fill="#34D399"/>
            </svg>
        </div>
        <div class="bot-details">
            <div class="bot-name">MatchBot <span style="font-size:0.65rem; color:#10B981;">● READY</span></div>
            <div class="bot-duty">Semantic Equivalence & Scoring</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. 10 COMPREHENSIVE REQUISITION BENCHMARKS
# ==============================================================================
role_catalog = {
    "AI / Machine Learning Research Intern [Internship]": {
        "level": "Internship", "domain": "Artificial Intelligence", "req_id": "REQ-AI-01",
        "jd": """Job Title: AI / Machine Learning Research Intern
Level: Internship | Domain: AI & Data Science
Role Overview:
We are seeking an enthusiastic AI/ML Research Intern to contribute to our core machine learning pipelines, experimentation workflows, and neural model evaluations.

Must-Have Technical Qualifications:
- Solid foundation in Python programming and numerical packages (NumPy, SciPy)
- Academic or project exposure to Machine Learning fundamentals and Deep Learning (PyTorch or TensorFlow)
- Basic understanding of Relational Databases and SQL data retrieval
- Git version control and collaborative GitHub workflow

Preferred Qualifications:
- Familiarity with Hugging Face transformers or Large Language Model prompting
- Experience running experiments in Jupyter Notebooks or Google Colab
- Strong analytical curiosity and foundational mathematics / linear algebra"""
    },
    "Junior Software Development Engineer [Entry Level]": {
        "level": "Entry Level", "domain": "Software Engineering", "req_id": "REQ-SWE-02",
        "jd": """Job Title: Junior Software Development Engineer (SDE I)
Level: Entry Level | Domain: Software Engineering
Role Overview:
Looking for a Junior SDE to build, test, and maintain client-facing web applications and scalable backend APIs within an agile sprint structure.

Must-Have Technical Qualifications:
- Proficiency in Python, JavaScript, or TypeScript
- Experience building web interfaces with React, Next.js, or Vue
- Understanding of RESTful API development using FastAPI, Flask, or Node.js
- Fundamental relational database knowledge with PostgreSQL or MySQL
- Git version control and PR review discipline

Preferred Qualifications:
- Basic containerization exposure using Docker
- Familiarity with unit testing frameworks (pytest, jest)
- Passion for clean code, responsive design, and rapid iteration"""
    },
    "Data Analyst & BI Associate [Junior / Associate]": {
        "level": "Associate", "domain": "Analytics & BI", "req_id": "REQ-DA-03",
        "jd": """Job Title: Data Analyst & Business Intelligence Associate
Level: Junior / Associate | Domain: Data & Analytics
Role Overview:
Seeking a Data Analyst to clean, aggregate, and visualize high-volume operational metrics into automated executive BI dashboards.

Must-Have Technical Qualifications:
- Advanced SQL querying skills (window functions, subqueries, complex joins, CTEs)
- Data manipulation and exploratory data analysis using Python (Pandas, NumPy)
- Production dashboard creation using PowerBI or Tableau
- Clear communication and ability to articulate data trends to business stakeholders

Preferred Qualifications:
- Familiarity with Cloud Data Warehouses such as Google BigQuery or Snowflake
- Foundational statistical hypothesis testing and A/B test analysis
- Experience with ETL scheduling tools or workflow automation"""
    },
    "Associate Cloud & DevOps Engineer [Junior / Mid]": {
        "level": "Mid Level", "domain": "Cloud & Infrastructure", "req_id": "REQ-OPS-04",
        "jd": """Job Title: Associate Cloud & DevOps Engineer
Level: Mid Level | Domain: Cloud Infrastructure & DevOps
Role Overview:
Seeking an engineer to support cloud automation, continuous deployment pipelines, and microservice infrastructure observability.

Must-Have Technical Qualifications:
- Hands-on Linux / Unix systems administration and Shell/Bash scripting
- Containerization with Docker and basic cluster orchestration with Kubernetes
- CI/CD pipeline building using GitHub Actions, GitLab CI, or Jenkins
- Basic cloud infrastructure knowledge on AWS (EC2, S3, IAM) or GCP

Preferred Qualifications:
- Infrastructure as Code basics using Terraform
- Monitoring and telemetry exposure with Prometheus and Grafana
- Python or Go scripting for operations automation"""
    },
    "Cybersecurity & SOC Defense Analyst [Mid Level]": {
        "level": "Mid Level", "domain": "Information Security", "req_id": "REQ-SEC-05",
        "jd": """Job Title: Cybersecurity & SOC Defense Analyst
Level: Mid Level | Domain: Information Security & Defense
Role Overview:
Responsible for real-time security event triage, vulnerability assessments, intrusion detection, and incident response execution.

Must-Have Technical Qualifications:
- Hands-on experience with SIEM platforms (Splunk, Microsoft Sentinel, or QRadar)
- Solid comprehension of Network Protocols (TCP/IP, DNS, SSL/TLS) and Firewall controls
- Vulnerability scanning and triage using tools like Nessus or Qualys
- Incident triage and security incident lifecycle management

Preferred Qualifications:
- Industry certifications: CompTIA Security+, CEH, or CySA+
- Scripting capability in Python or PowerShell for security log parsing
- Exposure to SOC-2, ISO 27001, or NIST compliance frameworks"""
    },
    "Backend Systems Engineer [Mid Level]": {
        "level": "Mid Level", "domain": "Distributed Systems & APIs", "req_id": "REQ-BE-06",
        "jd": """Job Title: Backend Systems Engineer
Level: Mid Level | Domain: Distributed Systems & APIs
Role Overview:
Engineer high-throughput, low-latency microservices, async task pipelines, and resilient database architectures.

Must-Have Technical Qualifications:
- Strong production experience in Python (FastAPI/Django) or Go
- Microservices architecture, RESTful API design, and asynchronous task queues (Celery)
- Deep relational schema design, indexing, and query optimization in PostgreSQL
- Distributed caching strategies using Redis or Memcached

Preferred Qualifications:
- Experience with event-driven streaming architectures using Apache Kafka or RabbitMQ
- Containerized deployments on Docker and Kubernetes
- Rigorous automated unit, integration, and load testing practices"""
    },
    "Mobile Application Developer [Mid Level]": {
        "level": "Mid Level", "domain": "Mobile Development", "req_id": "REQ-MOB-07",
        "jd": """Job Title: Mobile Application Developer (React Native / Flutter)
Level: Mid Level | Domain: Mobile Engineering
Role Overview:
Build engaging, cross-platform iOS and Android applications with intuitive UX and rock-solid offline state synchronization.

Must-Have Technical Qualifications:
- Production app development using React Native or Flutter
- State management mastery (Redux, MobX, or Riverpod / Bloc)
- Integration with RESTful / GraphQL backend microservices
- App publishing lifecycle on Apple App Store and Google Play Console

Preferred Qualifications:
- Native iOS (Swift) or Android (Kotlin) bridge development
- Push notifications, in-app purchases, and offline caching patterns
- Mobile performance profiling and memory leak remediation"""
    },
    "Senior Machine Learning & MLOps Engineer [Senior]": {
        "level": "Senior", "domain": "AI / Deep Learning", "req_id": "REQ-MLE-08",
        "jd": """Job Title: Senior Machine Learning & MLOps Engineer
Level: Senior | Domain: Machine Learning & MLOps
Role Overview:
Lead the technical architecture and scaling of generative AI pipelines, recommendation systems, and automated training/inference clusters.

Must-Have Technical Qualifications:
- 4+ years of production Python engineering and Deep Learning architectures (PyTorch)
- Model serving at scale, latency optimization, and GPU cluster deployment
- Container Orchestration using Kubernetes (k8s) and Docker
- Relational and vector database integration (PostgreSQL with pgvector, Pinecone, or Milvus)

Preferred Qualifications:
- Production MLOps tooling (Kubeflow, MLflow, or Weights & Biases)
- Cloud AI infrastructure on AWS (SageMaker, EKS) or GCP (Vertex AI)
- Experience with Large Language Model fine-tuning, quantization, and RAG pipelines
- Cross-functional team mentorship and technical design review leadership"""
    },
    "Lead Cloud Infrastructure Architect [Staff / Lead]": {
        "level": "Staff / Lead", "domain": "Enterprise Cloud", "req_id": "REQ-ARC-09",
        "jd": """Job Title: Lead Cloud Infrastructure Architect
Level: Staff / Lead | Domain: Cloud Architecture
Role Overview:
Define enterprise-wide multi-cloud infrastructure strategy, disaster recovery architectures, and zero-trust security postures.

Must-Have Technical Qualifications:
- 6+ years designing mission-critical multi-region infrastructure on AWS or GCP
- Production mastery of Infrastructure as Code using Terraform or OpenTofu
- Enterprise Kubernetes architecture, service mesh (Istio), and ingress routing
- Cost governance, FinOps practices, and high-availability SLA enforcement

Preferred Qualifications:
- AWS Certified Solutions Architect Professional or equivalent
- Zero-trust network security, automated secrets rotation (HashiCorp Vault)
- Experience presenting cloud roadmaps to C-level engineering leadership"""
    },
    "Engineering Manager / Technical Product Lead [Leadership]": {
        "level": "Executive / Lead", "domain": "Engineering Management", "req_id": "REQ-MGR-10",
        "jd": """Job Title: Engineering Manager / Technical Product Lead
Level: Leadership | Domain: Technical Management
Role Overview:
Lead a multidisciplinary software team of engineers, bridging technical delivery with product milestones and talent mentorship.

Must-Have Technical Qualifications:
- Proven track record managing 6+ software/cloud engineers through agile sprint cycles
- Deep technical background in software engineering (architecture reviews, system design)
- Excellent cross-functional coordination with Product, Design, and Executive leadership
- Hiring, performance coaching, and engineering career development experience

Preferred Qualifications:
- Experience managing distributed / remote-first engineering teams
- OKR definition, budget forecasting, and product roadmap prioritization
- Metric-driven sprint retrospectives and team velocity optimization"""
    }
}

# ==============================================================================
# 5. ENTERPRISE REQUISITION & RESUME INPUT SECTION
# ==============================================================================
col_jd, col_resume = st.columns([1.1, 0.9], gap="large")

with col_jd:
    st.markdown("### 📋 Target Job Requisition")
    
    selected_role = st.selectbox(
        "Select Enterprise Position Profile (Intern to Lead):",
        list(role_catalog.keys()) + ["Custom Enterprise Job Description"]
    )
    
    if selected_role != "Custom Enterprise Job Description":
        role_info = role_catalog[selected_role]
        default_jd_text = role_info["jd"]
        level_tag = role_info["level"]
        dept_tag = role_info["domain"]
        req_id = role_info["req_id"]
    else:
        default_jd_text = ""
        level_tag = "Custom"
        dept_tag = "General"
        req_id = "REQ-CUSTOM"

    st.markdown(f"""
    <div style="display: flex; gap: 8px; margin-bottom: 8px;">
        <span class="req-tag req-tag-level">⚡ Level: {level_tag}</span>
        <span class="req-tag req-tag-dept">🏛️ Domain: {dept_tag}</span>
        <span class="req-tag" style="background: rgba(255,255,255,0.06); color: #94A3B8; border: 1px solid rgba(255,255,255,0.1);">🆔 {req_id}</span>
    </div>
    """, unsafe_allow_html=True)
    
    jd_input = st.text_area(
        "Job Requisition Description & Requirements:",
        value=default_jd_text,
        height=210,
        placeholder="Paste role requirements, responsibilities, and qualifications here...",
        label_visibility="collapsed"
    )

with col_resume:
    st.markdown("### 📄 Candidate Resume Dossier")
    st.markdown("<div style='font-size:0.8rem; color:#94A3B8; margin-bottom: 12px;'>Upload native or scanned candidate resume in PDF format.</div>", unsafe_allow_html=True)
    
    uploaded_pdf = st.file_uploader(
        "Upload Resume:",
        type=["pdf"],
        label_visibility="collapsed"
    )
    if uploaded_pdf is not None:
        st.success(f"✓ Dossier Loaded: **{uploaded_pdf.name}** ({round(uploaded_pdf.size/1024, 1)} KB)")
    else:
        st.info("💡 Drag and drop your candidate resume PDF above to begin.")

# ==============================================================================
# 6. CORE ENGINES (PII DE-BIAS & SRICL GROUNDING)
# ==============================================================================
class PIIScrubber:
    def __init__(self):
        self.email_pat = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+', re.IGNORECASE)
        self.phone_pat = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.url_pat = re.compile(r'https?://[^\s]+|www\.[^\s]+|linkedin\.com/in/[^\s]+', re.IGNORECASE)

    def scrub(self, text: str) -> str:
        text = self.email_pat.sub('[EMAIL]', text)
        text = self.phone_pat.sub('[PHONE]', text)
        text = self.url_pat.sub('[LINK]', text)
        text = re.sub(r'\b(he|she)\b', 'they', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(him|her)\b', 'them', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(his|hers)\b', 'their', text, flags=re.IGNORECASE)
        return text

class SRICLVerifier:
    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold

    def verify(self, evidence: str, full_resume: str) -> Tuple[bool, float, str]:
        if not evidence or len(evidence.strip()) < 5:
            return False, 0.0, "No evidence quote provided"
        clean_res = re.sub(r'[^\w\s]', ' ', full_resume.lower())
        clean_ev = re.sub(r'[^\w\s]', ' ', evidence.lower()).strip()
        
        if clean_ev in clean_res:
            return True, 1.0, "Exact verbatim span corroborated"
            
        ev_tokens = set(clean_ev.split())
        res_tokens = set(clean_res.split())
        if not ev_tokens:
            return False, 0.0, "Empty token set"
            
        overlap = len(ev_tokens.intersection(res_tokens)) / len(ev_tokens)
        if overlap >= self.threshold:
            return True, round(overlap, 2), f"Token match ({int(overlap * 100)}%)"
        return False, round(overlap, 2), f"Grounding failure ({int(overlap * 100)}% < {int(self.threshold * 100)}%)"

def call_genai_with_retry(client, model_name: str, prompt: str, max_retries: int = 3, initial_delay: int = 5):
    """Executes model generation using modern google-genai client with exponential backoff."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text
        except APIError as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay)
            delay *= 2

# ==============================================================================
# 7. EXECUTION PIPELINE
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
run_btn = st.button("🚀 Execute CVision Candidate Assessment", type="primary", use_container_width=True)

if run_btn:
    if not API_KEY:
        st.error("⚠️ Gemini API key not found. Ensure `GEMINI_API_KEY` is configured in `.streamlit/secrets.toml`.")
    elif not uploaded_pdf:
        st.error("⚠️ Please upload a candidate resume PDF file.")
    elif not jd_input.strip():
        st.error("⚠️ Please specify target job requirements.")
    else:
        with st.status("🤖 CVision Swarm in Autonomous Execution...", expanded=True) as swarm_status:
            try:
                # 1. IngestBot
                st.write("🤖 **IngestBot**: Ingesting PDF streams & extracting text...")
                doc = pymupdf.open(stream=uploaded_pdf.read(), filetype="pdf")
                raw_resume = "\n".join([page.get_text() for page in doc]).strip()
                doc.close()

                if len(raw_resume) < 30:
                    st.error("PDF has insufficient extractable text.")
                    st.stop()

                # 2. GuardianBot
                st.write("🛡️ **GuardianBot**: Scrubbing contact info & demographic markers...")
                scrubber = PIIScrubber()
                scrubbed_resume = scrubber.scrub(raw_resume)

                # 3. MatchBot
                st.write(f"🧠 **MatchBot**: Reasoning through competencies with {MODEL_NAME}...")
                client = genai.Client(api_key=API_KEY)

                eval_prompt = f"""
                You are the CVision MatchBot evaluation engine.
                Compare candidate against job requirements.

                Job Description:
                \"\"\"{jd_input}\"\"\"

                Resume Text:
                \"\"\"{scrubbed_resume}\"\"\"

                Instructions:
                1. Classify requirements into Must-Have vs Preferred.
                2. Extract matching skills. For every single match, copy the EXACT verbatim sentence from the resume as 'evidence_quote'. Do not rephrase.
                3. Semantically match skills (e.g. Kubernetes satisfies Container Orchestration; PostgreSQL satisfies Relational Database).
                4. Classify missing requirements into 'Critical' (if Must-Have) or 'Minor' (if Preferred).
                5. Compute a realistic weighted Fit Score (0-100).
                6. Generate a 2-sentence executive summary and 3 high-impact improvement tips.

                Return ONLY valid raw JSON:
                {{
                  "fit_score": 86.0,
                  "verdict": "STRONG MATCH | MODERATE MATCH | LOW FIT",
                  "summary": "Executive recruiter synthesis.",
                  "matched_skills": [
                    {{
                      "required_skill": "Skill Name",
                      "candidate_skill": "Candidate Skill",
                      "importance": "Must-Have | Preferred",
                      "match_type": "Exact Match | Semantic Equivalent",
                      "evidence_quote": "Exact verbatim sentence from resume"
                    }}
                  ],
                  "missing_skills": [
                    {{
                      "required_skill": "Missing Skill",
                      "importance": "Must-Have | Preferred",
                      "gap_severity": "Critical | Minor",
                      "impact_reason": "Why missing affects role readiness"
                    }}
                  ],
                  "suggestions": [
                    {{
                      "area": "Focus Area",
                      "advice": "Actionable advice",
                      "star_bullet": "Quantified STAR-methodology bullet"
                    }}
                  ]
                }}
                """

                raw_json = call_genai_with_retry(client, MODEL_NAME, eval_prompt, max_retries=3, initial_delay=5)
                clean_json = raw_json.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)

                # 4. VerifierBot
                st.write("🔬 **VerifierBot**: Enforcing SRICL deterministic token grounding...")
                verifier = SRICLVerifier(threshold=0.65)
                verified_matches = []
                pruned_hallucinations = []

                for item in data.get("matched_skills", []):
                    ev = item.get("evidence_quote", "")
                    grounded, score, reason = verifier.verify(ev, raw_resume)
                    if grounded:
                        verified_matches.append(item)
                    else:
                        pruned_hallucinations.append({"skill": item.get("candidate_skill"), "reason": reason})

                swarm_status.update(label="✅ CVision Assessment Complete & Grounded!", state="complete", expanded=False)

            except APIError as e:
                swarm_status.update(label="⚠️ API Error Encountered", state="error")
                st.error(f"Gemini API Error: {str(e)}")
                st.stop()
            except json.JSONDecodeError:
                swarm_status.update(label="❌ Invalid JSON Output", state="error")
                st.error("Failed to parse JSON response from the model. Please rerun the assessment.")
                st.stop()
            except Exception as e:
                swarm_status.update(label="❌ Assessment Pipeline Failed", state="error")
                st.error(f"Error: {str(e)}")
                st.stop()

        # ==============================================================================
        # 8. RESULTS DASHBOARD
        # ==============================================================================
        st.markdown("<br>", unsafe_allow_html=True)
        fit_score = float(data.get("fit_score", 0.0))
        verdict = data.get("verdict", "EVALUATED")

        # Color Calculation for Radial Gauge
        stroke_color = "#10B981" if fit_score >= 75 else ("#F59E0B" if fit_score >= 50 else "#F43F5E")
        circ = 376.99
        offset = circ - (circ * (fit_score / 100.0))

        # Hero Score Banner
        col_g, col_s = st.columns(2, gap="large")

        with col_g:
            st.markdown(f"""
            <div class="clean-card" style="text-align: center;">
                <div class="gauge-wrapper">
                    <svg class="gauge-svg" viewBox="0 0 140 140">
                        <circle class="gauge-bg" cx="70" cy="70" r="60"></circle>
                        <circle class="gauge-fill" cx="70" cy="70" r="60" 
                                stroke="{stroke_color}" stroke-dasharray="{circ}" stroke-dashoffset="{offset}"></circle>
                    </svg>
                    <div class="gauge-center-box">
                        <div class="gauge-score-val" style="color: {stroke_color};">{int(fit_score)}%</div>
                        <div style="font-size:0.7rem; color:#94A3B8; font-weight:700;">FIT INDEX</div>
                    </div>
                </div>
                <div style="font-size: 1.1rem; font-weight: 800; color: {stroke_color};">{verdict}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_s:
            st.markdown(f"""
            <div class="clean-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size:0.78rem; font-weight:700; color:#94A3B8; text-transform:uppercase;">CVision Recruiter Synthesis</div>
                <div style="font-size:1.02rem; line-height:1.6; color:#F1F5F9; margin-top:8px;">
                    {data.get('summary', 'Evaluation completed.')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Swarm KPI Tiles
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""
            <div class="clean-card" style="padding: 14px 18px; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-size:1.6rem; font-weight:800; color:#34D399;">{len(verified_matches)}</div><div style="font-size:0.75rem; color:#94A3B8; font-weight:600; text-transform:uppercase;">Verified Skills</div></div>
                <div style="font-size: 1.4rem;">✓</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="clean-card" style="padding: 14px 18px; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-size:1.6rem; font-weight:800; color:#FB7185;">{len(data.get('missing_skills', []))}</div><div style="font-size:0.75rem; color:#94A3B8; font-weight:600; text-transform:uppercase;">Identified Gaps</div></div>
                <div style="font-size: 1.4rem;">✗</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="clean-card" style="padding: 14px 18px; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-size:1.6rem; font-weight:800; color:#38BDF8;">{len(pruned_hallucinations)}</div><div style="font-size:0.75rem; color:#94A3B8; font-weight:600; text-transform:uppercase;">Pruned Claims</div></div>
                <div style="font-size: 1.4rem;">🛡️</div>
            </div>
            """, unsafe_allow_html=True)

        # Tabs
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs([
            f"✅ Authenticated Matches ({len(verified_matches)})",
            f"❌ Skill Gaps ({len(data.get('missing_skills', []))})",
            "💡 Optimization Suggestions"
        ])

        with t1:
            for item in verified_matches:
                imp = item.get("importance", "Must-Have")
                badge_style = "background:rgba(244,63,94,0.15); color:#FDA4AF; border:1px solid rgba(244,63,94,0.3);" if imp == "Must-Have" else "background:rgba(56,189,248,0.15); color:#7DD3FC; border:1px solid rgba(56,189,248,0.3);"
                st.markdown(f"""
                <div class="clean-card" style="border-left: 3px solid #10B981; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="display:inline-block; padding:2px 8px; border-radius:6px; font-size:0.7rem; font-weight:700; text-transform:uppercase; {badge_style}">{imp}</span>
                            <strong style="margin-left: 8px; font-size:1.02rem; color:#F8FAFC;">{item.get('required_skill')}</strong>
                        </div>
                        <span style="font-size:0.85rem; color:#94A3B8;">Candidate: <code style="color:#38BDF8;">{item.get('candidate_skill')}</code></span>
                    </div>
                    <div class="quote-box">“{item.get('evidence_quote')}”</div>
                </div>
                """, unsafe_allow_html=True)

        with t2:
            for g in data.get("missing_skills", []):
                imp = g.get("importance", "Must-Have")
                badge_style = "background:rgba(244,63,94,0.15); color:#FDA4AF; border:1px solid rgba(244,63,94,0.3);" if imp == "Must-Have" else "background:rgba(56,189,248,0.15); color:#7DD3FC; border:1px solid rgba(56,189,248,0.3);"
                st.markdown(f"""
                <div class="clean-card" style="border-left: 3px solid #F43F5E; margin-bottom: 10px;">
                    <span style="display:inline-block; padding:2px 8px; border-radius:6px; font-size:0.7rem; font-weight:700; text-transform:uppercase; {badge_style}">{imp}</span>
                    <strong style="margin-left: 8px; font-size:1.02rem; color:#F8FAFC;">{g.get('required_skill')}</strong>
                    <div style="font-size:0.86rem; color:#94A3B8; margin-top:6px;">Impact: {g.get('impact_reason')}</div>
                </div>
                """, unsafe_allow_html=True)

        with t3:
            for s in data.get("suggestions", []):
                st.markdown(f"""
                <div class="clean-card" style="border-left: 3px solid #6366F1; margin-bottom: 12px;">
                    <div style="font-weight:700; color:#818CF8; margin-bottom:4px;">🎯 {s.get('area')}</div>
                    <div style="font-size:0.9rem; color:#CBD5E1; margin-bottom:8px;">{s.get('advice')}</div>
                    <div class="quote-box" style="border-left: 2px solid #818CF8;">
                        <span style="font-size:0.7rem; color:#818CF8; font-weight:700; text-transform:uppercase;">STAR Bullet:</span><br>
                        "{s.get('star_bullet')}"
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Export Candidate Evaluation Report (JSON)",
            data=json.dumps(data, indent=2),
            file_name=f"{AGENT_NAME}_Report.json",
            mime="application/json",
            use_container_width=True
        )