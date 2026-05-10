"""app.py — HireIQ Streamlit UI"""
from __future__ import annotations
import os,io,time,json
from datetime import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
st.set_page_config(page_title="HireIQ",page_icon="✦",layout="wide",initial_sidebar_state="expanded")
load_dotenv()

# ── CSS ──
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
*{font-family:'Inter',sans-serif!important}
.stApp{background:#080810!important}
header[data-testid="stHeader"],#MainMenu,footer,.stDeployButton,div[data-testid="stToolbar"]{display:none!important}
.block-container{padding-top:0!important;padding-bottom:2rem!important;max-width:1200px!important}
section[data-testid="stSidebar"]{background:#0c0c18!important;border-right:1px solid #1e1e2e}
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] li{color:#94a3b8!important;font-size:13px}
section[data-testid="stFileUploadDropzone"]{background:#0f0f1a!important;border:1px dashed #2a2a40!important;border-radius:12px!important}
section[data-testid="stFileUploadDropzone"]:hover{border-color:#7c3aed!important}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#7c3aed,#06b6d4)!important;border-radius:4px}
div[data-testid="stExpander"]{background:#0f0f1a!important;border:1px solid #1e1e2e!important;border-radius:10px!important}
input,textarea,select,.stTextInput input,.stNumberInput input{background:#0f0f1a!important;border:1px solid #2a2a40!important;color:#e2e8f0!important;border-radius:8px!important}
.stSelectbox>div>div{background:#0f0f1a!important;color:#e2e8f0!important}
button[kind="primary"]{background:linear-gradient(135deg,#7c3aed,#4f46e5)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-weight:600!important}
button[kind="primary"]:hover{filter:brightness(1.15)!important}
button[kind="secondary"]{background:#0f0f1a!important;color:#c4b5fd!important;border:1px solid #7c3aed!important;border-radius:10px!important;font-weight:600!important}
hr{border-color:#1e1e2e!important}
</style>""",unsafe_allow_html=True)

# ── HELPERS ──
def extract_jd_text(f)->str:
    n=f.name.lower()
    if n.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(f.read())) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif n.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(f.read())).paragraphs)
    else:
        return f.read().decode("utf-8")

def get_llm():
    k=os.getenv("GOOGLE_API_KEY")
    if not k:st.error("GOOGLE_API_KEY not set.");st.stop()
    from langchain_community.cache import SQLiteCache
    from langchain_core.globals import set_llm_cache
    set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model="gemini-1.5-pro",temperature=0.1,google_api_key=k)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown('<div style="padding:8px 0 12px"><span style="color:#c4b5fd;font-size:20px;font-weight:800">✦</span> <span style="font-size:17px;font-weight:700;color:#fff">HireIQ</span></div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Pipeline Flow**")
    st.markdown("1. Upload Job Description\n2. Upload Resumes\n3. Run Agent\n4. Review & Override\n5. Download Report")
    st.markdown("---")
    st.markdown("**Evaluation Metrics**")
    st.markdown('<span style="color:#7c3aed">●</span> Skills Match — 30%<br><span style="color:#06b6d4">●</span> Experience — 25%<br><span style="color:#3b82f6">●</span> Education — 15%<br><span style="color:#f59e0b">●</span> Portfolio — 20%<br><span style="color:#10b981">●</span> Communication — 10%',unsafe_allow_html=True)
    st.markdown("---")
    st.caption("v1.0.0 · Gemini 2.5 Flash")

# ── NAVBAR ──
st.markdown("""
<div style="background:#080810;border-bottom:1px solid #1e1e2e;padding:14px 0;display:flex;align-items:center;justify-content:space-between;margin-bottom:0">
  <div style="display:flex;align-items:center;gap:10px">
    <div style="width:32px;height:32px;background:linear-gradient(135deg,#7c3aed,#4f46e5);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:15px">H</div>
    <span style="font-size:18px;font-weight:700;color:#fff">HireIQ</span>
    <span style="background:#7c3aed;color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:5px;letter-spacing:.5px">BETA</span>
  </div>
  <div style="display:flex;align-items:center;gap:16px;font-size:12px;color:#475569">
    <span>Docs</span>
    <span>GitHub</span>
    <span style="background:#0f0f1a;border:1px solid #1e1e2e;padding:4px 12px;border-radius:6px;font-size:11px;color:#94a3b8">Gemini 2.5 Flash · LangChain</span>
  </div>
</div>
""",unsafe_allow_html=True)

# ── HERO ──
st.markdown("""
<div style="text-align:center;padding:48px 0 36px">
  <div style="display:inline-flex;align-items:center;gap:6px;font-size:11px;color:#10b981;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-bottom:20px">
    <span style="width:6px;height:6px;border-radius:50%;background:#10b981;display:inline-block"></span> SYSTEM OPERATIONAL
  </div>
  <h1 style="font-size:46px;font-weight:800;color:#fff;letter-spacing:-0.04em;line-height:1.15;margin:0 0 14px;text-align:center">
    AI-Powered<br>
    <span style="background:linear-gradient(135deg,#7c3aed,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent">Candidate Intelligence</span>
  </h1>
  <p style="color:#64748b;font-size:15px;max-width:520px;margin:0 auto 24px;line-height:1.6;text-align:center">
    Upload a job description and resumes. Our AI agent evaluates, scores, and ranks every candidate in seconds.
  </p>
  <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap">
    <span style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:8px;padding:7px 14px;font-size:12px;color:#94a3b8">5-Dimension Scoring</span>
    <span style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:8px;padding:7px 14px;font-size:12px;color:#94a3b8">Bias-Free Evaluation</span>
    <span style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:8px;padding:7px 14px;font-size:12px;color:#94a3b8">Instant Report Export</span>
    <span style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:8px;padding:7px 14px;font-size:12px;color:#94a3b8">Audit Trail Logged</span>
  </div>
</div>
""",unsafe_allow_html=True)

# ── UPLOAD SECTION ──
c1,c2=st.columns(2,gap="medium")
with c1:
    st.markdown("""<div style="background:#0c0c18;border:1px solid #1e1e2e;border-left:3px solid #7c3aed;border-radius:14px;padding:22px 24px;margin-bottom:8px">
      <div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:2px">Job Description</div>
      <div style="font-size:12px;color:#64748b">TXT, PDF, or DOCX</div>
    </div>""",unsafe_allow_html=True)
    jd_file=st.file_uploader("jd",type=["txt","pdf","docx"],key="jd",label_visibility="collapsed")
    if jd_file:
        st.markdown(f'<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:8px 14px;font-size:12px;color:#10b981;font-weight:600;margin-top:4px">✓ {jd_file.name} · {jd_file.size//1024}KB loaded</div>',unsafe_allow_html=True)

with c2:
    st.markdown("""<div style="background:#0c0c18;border:1px solid #1e1e2e;border-left:3px solid #06b6d4;border-radius:14px;padding:22px 24px;margin-bottom:8px">
      <div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:2px">Candidate Resumes</div>
      <div style="font-size:12px;color:#64748b">PDF or DOCX · Multiple allowed</div>
    </div>""",unsafe_allow_html=True)
    resume_files=st.file_uploader("r",type=["pdf","docx","txt","json"],accept_multiple_files=True,key="res",label_visibility="collapsed")
    if resume_files:
        st.markdown(f'<div style="background:rgba(6,182,212,.08);border:1px solid rgba(6,182,212,.2);border-radius:8px;padding:8px 14px;font-size:12px;color:#06b6d4;font-weight:600;margin-top:4px">{len(resume_files)} resume{"s" if len(resume_files)!=1 else ""} ready</div>',unsafe_allow_html=True)

# ── EXECUTE ──
st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
if not jd_file:
    st.markdown('<div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.12);border-radius:10px;padding:10px;text-align:center;font-size:13px;color:#fca5a5;margin-bottom:10px">Upload a Job Description to enable the pipeline</div>',unsafe_allow_html=True)
run=st.button("Execute Shortlisting Pipeline",type="primary",use_container_width=True,disabled=not jd_file)

# ── PIPELINE ──
if run:
    if not resume_files:st.warning("Upload at least one resume.");st.stop()
    llm=get_llm()
    from agents.jd_parser import parse_jd
    from agents.profile_parser import parse_profile_from_text
    from agents.scorer import score_candidate
    from agents.ranker import rank_candidates
    from report.generator import generate_html_report
    from tools.pdf_reader import extract_text_from_bytes
    steps=["Parsing JD","Parsing Resumes","Scoring Candidates","Ranking","Report Ready"]
    def mk_step(ai):
        h='<div style="display:flex;justify-content:center;gap:4px;padding:12px 0;flex-wrap:wrap">'
        for i,s in enumerate(steps):
            if i<ai:h+=f'<span style="color:#10b981;font-size:12px;font-weight:500;padding:6px 12px">✓ {s}</span>'
            elif i==ai:h+=f'<span style="color:#c4b5fd;font-size:12px;font-weight:600;padding:6px 12px;background:rgba(124,58,237,.08);border-radius:6px">● {s}</span>'
            else:h+=f'<span style="color:#334155;font-size:12px;padding:6px 12px">○ {s}</span>'
            if i<len(steps)-1:h+='<span style="color:#1e1e2e;font-size:12px;padding:0 2px">→</span>'
        return h+'</div>'
    stel=st.empty();pbar=st.progress(0);stxt=st.empty()
    stel.markdown(mk_step(0),unsafe_allow_html=True);pbar.progress(10);stxt.caption("_Extracting requirements from JD..._")
    jd_text=extract_jd_text(jd_file);jd_req=parse_jd(jd_text,llm);st.toast(f"JD: {jd_req.role_title}")
    stel.markdown(mk_step(1),unsafe_allow_html=True);stxt.caption("_Parsing candidate resumes..._")
    profiles=[]
    for i,rf in enumerate(resume_files):
        pbar.progress(10+int(30*(i+1)/len(resume_files)))
        try:
            if i>0:time.sleep(15)
            profiles.append(parse_profile_from_text(extract_text_from_bytes(rf.read(),rf.name),llm))
        except Exception as e:st.error(f"Failed: {rf.name}: {e}")
    if not profiles:st.error("No resumes parsed.");stel.empty();pbar.empty();stxt.empty();st.stop()
    stel.markdown(mk_step(2),unsafe_allow_html=True);stxt.caption("_Evaluating candidates against JD..._")
    scores=[]
    for i,p in enumerate(profiles):
        pbar.progress(40+int(40*(i+1)/len(profiles)))
        try:time.sleep(15);scores.append(score_candidate(jd_req,p,llm))
        except Exception as e:st.error(f"Failed: {p.name}: {e}")
    if not scores:st.error("No candidates scored.");stel.empty();pbar.empty();stxt.empty();st.stop()
    stel.markdown(mk_step(3),unsafe_allow_html=True);pbar.progress(90);stxt.caption("_Ranking..._")
    report=rank_candidates(scores,jd_req.role_title);os.makedirs("output",exist_ok=True)
    hp=generate_html_report(report,os.path.join("output","shortlist_report.html"))
    stel.markdown(mk_step(4),unsafe_allow_html=True);pbar.progress(100);stxt.caption("_Done._")
    time.sleep(.5);stel.empty();pbar.empty();stxt.empty()
    st.session_state["report"]=report;st.session_state["html_path"]=hp

# ── RESULTS ──
if "report" not in st.session_state:
    st.stop()

report=st.session_state["report"];hp=st.session_state["html_path"]
st.markdown("---")

# Metrics
hi=sum(1 for c in report.ranked_candidates if c.recommendation.value=="Hire")
ma=sum(1 for c in report.ranked_candidates if c.recommendation.value=="Maybe")
no=sum(1 for c in report.ranked_candidates if c.recommendation.value=="No Hire")

m1,m2,m3,m4=st.columns(4)
with m1:
    st.markdown(f'<div style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:12px;padding:20px;text-align:center"><div style="font-size:36px;font-weight:800;color:#06b6d4;font-family:JetBrains Mono,monospace">{report.total_candidates}</div><div style="font-size:11px;color:#64748b;margin-top:6px;text-transform:uppercase;letter-spacing:.5px;font-weight:600">Total Evaluated</div></div>',unsafe_allow_html=True)
with m2:
    st.markdown(f'<div style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:12px;padding:20px;text-align:center"><div style="font-size:36px;font-weight:800;color:#10b981;font-family:JetBrains Mono,monospace">{hi}</div><div style="font-size:11px;color:#64748b;margin-top:6px;text-transform:uppercase;letter-spacing:.5px;font-weight:600">Recommended Hire</div></div>',unsafe_allow_html=True)
with m3:
    st.markdown(f'<div style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:12px;padding:20px;text-align:center"><div style="font-size:36px;font-weight:800;color:#f59e0b;font-family:JetBrains Mono,monospace">{ma}</div><div style="font-size:11px;color:#64748b;margin-top:6px;text-transform:uppercase;letter-spacing:.5px;font-weight:600">Maybe</div></div>',unsafe_allow_html=True)
with m4:
    st.markdown(f'<div style="background:#0f0f1a;border:1px solid #1e1e2e;border-radius:12px;padding:20px;text-align:center"><div style="font-size:36px;font-weight:800;color:#ef4444;font-family:JetBrains Mono,monospace">{no}</div><div style="font-size:11px;color:#64748b;margin-top:6px;text-transform:uppercase;letter-spacing:.5px;font-weight:600">No Hire</div></div>',unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>",unsafe_allow_html=True)
st.markdown("<h3 style='font-size:18px;font-weight:700;color:#fff;margin-bottom:16px'>Ranked Candidates</h3>",unsafe_allow_html=True)

dlb=["Skills Match (30%)","Experience (25%)","Education (15%)","Portfolio (20%)","Communication (10%)"]
bcl=["#7c3aed","#06b6d4","#3b82f6","#f59e0b","#10b981"]

for idx,c in enumerate(report.ranked_candidates,1):
    rc="background:rgba(16,185,129,.1);color:#34d399;border:1px solid rgba(16,185,129,.2)" if c.recommendation.value=="Hire" else("background:rgba(245,158,11,.1);color:#fbbf24;border:1px solid rgba(245,158,11,.2)" if c.recommendation.value=="Maybe" else "background:rgba(239,68,68,.1);color:#fca5a5;border:1px solid rgba(239,68,68,.2)")
    ri="✦ Hire" if c.recommendation.value=="Hire" else("◐ Maybe" if c.recommendation.value=="Maybe" else "✗ No Hire")
    dims=c.dimension_list()

    # Score bars HTML
    bars=""
    for j,d in enumerate(dims):
        vc="#10b981" if d.score>=7 else("#f59e0b" if d.score>=4 else "#ef4444")
        w=int(d.score*10)
        bars+=f'''<div style="display:grid;grid-template-columns:160px 1fr 40px;align-items:center;gap:10px;padding:5px 0">
          <span style="font-size:12px;color:#94a3b8;font-weight:500">{dlb[j]}</span>
          <div style="height:7px;background:#151520;border-radius:4px;overflow:hidden"><div style="height:100%;width:{w}%;background:{bcl[j]};border-radius:4px"></div></div>
          <span style="font-family:JetBrains Mono,monospace;font-size:12px;font-weight:600;color:{vc};text-align:right">{d.score:.1f}</span>
        </div>
        <div style="font-size:11px;color:#475569;font-style:italic;padding:0 0 3px 0">{d.justification}</div>'''

    # Total score display
    ts_html=f'<span style="font-family:JetBrains Mono,monospace;font-size:22px;font-weight:700;color:#fff">{c.effective_score:.2f}<small style="color:#475569;font-size:13px;font-weight:400"> /10</small></span>'
    if c.override_adjusted_score is not None:
        ts_html=f'<span style="text-decoration:line-through;color:#ef4444;font-size:14px">{c.total_weighted_score:.2f}</span> <span style="color:#10b981;font-weight:700;font-size:18px">{c.override_adjusted_score:.2f}</span><small style="color:#475569"> /10</small>'
        bars+=f'<div style="margin-top:8px;padding:10px 14px;background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.12);border-radius:8px;font-size:12px;color:#f59e0b"><strong>Override:</strong> <em>{c.override}</em></div>'

    st.markdown(f'''<div style="background:#0c0c18;border:1px solid #1e1e2e;border-radius:14px;padding:24px 28px;margin-bottom:12px">
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;flex-wrap:wrap">
        <div style="width:38px;height:38px;border-radius:50%;background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.25);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:#c4b5fd;flex-shrink:0">#{idx}</div>
        <span style="font-size:18px;font-weight:700;color:#fff;flex:1">{c.candidate_name}</span>
        <span style="display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:16px;font-size:11px;font-weight:700;{rc}">{ri}</span>
        {ts_html}
      </div>
      {bars}
    </div>''',unsafe_allow_html=True)

# ── OVERRIDE + DOWNLOAD ──
st.markdown("---")
oc,dc=st.columns([2,1],gap="large")
with oc:
    st.markdown("<h4 style='color:#fff;font-size:16px;margin-bottom:2px'>HR Score Override</h4>",unsafe_allow_html=True)
    st.caption("Adjust a candidate score manually — logged for audit")
    a,b=st.columns(2)
    with a:
        sn=st.selectbox("Candidate",[c.candidate_name for c in report.ranked_candidates])
        ns=st.number_input("New Score",0.0,10.0,7.5,0.1)
    with b:
        rr=st.text_area("Reason",height=110,placeholder="e.g., Strong interview performance")
    if st.button("Apply Override",type="primary",use_container_width=True):
        if not rr.strip():st.warning("Provide a reason.")
        else:
            from agents.ranker import apply_override
            from report.generator import generate_html_report as gr
            u=apply_override(report,sn,ns,rr.strip())
            st.session_state["report"]=u;st.session_state["html_path"]=gr(u,os.path.join("output","shortlist_report.html"))
            st.toast("Override applied and logged ✓");st.rerun()

with dc:
    st.markdown("<h4 style='color:#fff;font-size:16px;margin-bottom:2px'>Export</h4>",unsafe_allow_html=True)
    st.caption("Share reports with stakeholders")
    with open(hp,"r",encoding="utf-8") as f:hd=f.read()
    jp=os.path.join("output","shortlist_report.json")
    with open(jp,"r",encoding="utf-8") as f:jdata=f.read()
    st.download_button("Download HTML Report",hd,f"shortlist_{datetime.now().strftime('%Y%m%d')}.html","text/html",use_container_width=True,type="primary")
    st.download_button("Download JSON Data",jdata,f"shortlist_{datetime.now().strftime('%Y%m%d')}.json","application/json",use_container_width=True)
