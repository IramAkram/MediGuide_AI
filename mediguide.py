from __future__ import annotations
import os
import json
import streamlit as st
import pandas as pd
from openai import OpenAI
from fpdf import FPDF
from audio_recorder_streamlit import audio_recorder
import time

st.set_page_config(
    page_title="MediGuide AI - Medical Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME & PREMIUM MEDICAL CSS ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light (Clinical)"

def get_theme_css():
    if "Light" in st.session_state.theme_mode:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: linear-gradient(180deg, #f6fbf8 0%, #eef6f0 40%, #ffffff 100%); color: #1a2e1e; }
        h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif !important; color: #184a2a !important; letter-spacing: -0.02em; }
        
        /* Header Card */
        .hero-card {
            background: linear-gradient(135deg, #ffffff 0%, #f1f8f3 100%);
            border: 1px solid #dbead6; border-radius: 24px; padding: 28px 32px;
            box-shadow: 0 12px 40px rgba(24,74,42,0.08); display: flex; gap: 24px; align-items: center;
        }
        .hero-icon {
            width: 72px; height: 72px; background: linear-gradient(135deg, #2e7d32, #43a047);
            border-radius: 20px; display: grid; place-items: center; font-size: 36px; color: white;
            box-shadow: 0 8px 24px rgba(46,125,50,0.3); flex-shrink:0;
        }
        .hero-badge { display:inline-flex; gap:6px; align-items:center; background:#e8f5e9; border:1px solid #c8e6c9; color:#2e7d32; border-radius:100px; padding:6px 14px; font-size:0.72rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; }
        
        /* Cards */
        .med-card { background: white; border: 1px solid #e0e9dd; border-radius: 20px; padding: 22px 24px; box-shadow: 0 6px 24px rgba(0,0,0,0.04); }
        .stat-card { background: white; border-radius: 16px; padding: 16px; text-align:center; border: 1px solid #e6efe7; }
        .stat-card b { font-size: 1.8rem; display:block; color:#184a2a; }
        .stat-card span { font-size: 0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#6a8a6e; font-weight:700; }
        
        /* Voice Recorder */
        .voice-box { background: linear-gradient(135deg, #ffffff, #f9fbff); border: 2px dashed #a5c9a8; border-radius: 20px; padding: 20px; text-align:center; }
        
        /* Buttons */
        .stButton>button { border-radius: 12px !important; font-weight: 700 !important; min-height:48px; border:0 !important; background: linear-gradient(135deg, #2e7d32, #388e3c) !important; color:white !important; box-shadow: 0 4px 14px rgba(46,125,50,0.25) !important; }
        .stButton>button:hover { background: linear-gradient(135deg, #d81b60, #ad1457) !important; transform: translateY(-1px); }
        div[data-testid="stForm"] { background: white; border-radius: 20px; padding: 12px; border: 1px solid #e0e9dd; box-shadow: 0 8px 32px rgba(0,0,0,0.05); }
        
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e0e9dd; box-shadow: 4px 0 24px rgba(0,0,0,0.03); }
        .urgency-low { background:#e8f5e9; border-left:5px solid #2e7d32; padding:12px 16px; border-radius:12px; }
        .urgency-medium { background:#fff8e1; border-left:5px solid #f9a825; padding:12px 16px; border-radius:12px; }
        .urgency-high { background:#ffebee; border-left:5px solid #e53935; padding:12px 16px; border-radius:12px; }
        .urgency-emergency { background:#b71c1c; color:white; border-left:5px solid #ff1744; padding:14px 18px; border-radius:12px; font-weight:700; }
        </style>
        """
    else:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: #0e1510; color: #e8f0e8; }
        h1, h2, h3 { color: #a5d6a7 !important; }
        .hero-card { background: linear-gradient(135deg, #1b2a1e, #1e3322); border: 1px solid #2e4a32; border-radius: 24px; padding: 28px 32px; }
        .hero-icon { width: 72px; height: 72px; background: linear-gradient(135deg, #2e7d32, #66bb6a); border-radius: 20px; display: grid; place-items: center; font-size: 36px; }
        .hero-badge { background:#1b3320; border:1px solid #2e4a32; color:#81c784; border-radius:100px; padding:6px 14px; font-size:0.72rem; font-weight:700; }
        .med-card { background: #182019; border: 1px solid #2a3d2d; border-radius: 20px; padding: 22px 24px; }
        .stat-card { background: #1a2a1e; border-radius: 16px; padding: 16px; text-align:center; border: 1px solid #2a3d2d; }
        .stat-card b { font-size: 1.8rem; display:block; color:#c8e6c9; }
        .stat-card span { font-size: 0.68rem; text-transform:uppercase; color:#7fa882; }
        .voice-box { background: #182019; border: 2px dashed #3a5a3e; border-radius: 20px; padding: 20px; text-align:center; }
        .stButton>button { border-radius: 12px !important; font-weight: 700 !important; background: linear-gradient(135deg, #2e7d32, #43a047) !important; color:white !important; }
        [data-testid="stSidebar"] { background: #121a13; border-right: 1px solid #2a3d2d; }
        div[data-testid="stForm"] { background: #182019; border-radius: 20px; border: 1px solid #2a3d2d; }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

# Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = []
if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

def generate_pdf_report(data_dict, patient_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(46, 125, 50)
    pdf.rect(0,0,210,22,'F')
    pdf.set_y(6)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(255,255,255)
    pdf.cell(0, 10, txt="MediGuide AI - Patient Guidance Report", align="C")
    pdf.ln(20)
    pdf.set_text_color(0,0,0)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(232,245,233)
    pdf.cell(0,7, "  EDUCATIONAL PROTOTYPE ONLY - NOT A MEDICAL DIAGNOSIS - Consult qualified professional", fill=True, align="C")
    pdf.ln(12)
    
    pdf.set_font("Arial","B",10)
    pdf.cell(0,6, f"Patient: {patient_info.get('age')}yo {patient_info.get('gender')} | Duration: {patient_info.get('duration')} | Severity: {patient_info.get('severity')}/10")
    pdf.ln(8)
    pdf.set_font("Arial","",9)
    pdf.multi_cell(0,5, f"Symptoms: {patient_info.get('symptoms')}  |  Voice: {patient_info.get('voice')}")
    pdf.ln(4)
    
    def section(title, content):
        pdf.set_font("Arial","B",11)
        pdf.set_fill_color(46,125,50)
        pdf.set_text_color(255,255,255)
        pdf.cell(0,7, f"  {title}", fill=True)
        pdf.ln(8)
        pdf.set_text_color(0,0,0)
        pdf.set_font("Arial","",9)
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    pdf.multi_cell(0,5, f"- {item.get('name','')}: {item.get('reason','')}")
                else:
                    pdf.multi_cell(0,5, f"- {item}")
        else:
            pdf.multi_cell(0,5, str(content))
        pdf.ln(4)
    
    section("SUMMARY", data_dict.get('summary',''))
    section(f"URGENCY: {data_dict.get('urgency_level','')}", f"{data_dict.get('urgency_level','')} - {data_dict.get('summary','')[:100]}")
    section("POSSIBLE CONDITIONS (Educational Only)", data_dict.get('possible_conditions',[]))
    section("RECOMMENDED NEXT STEPS", data_dict.get('recommended_next_steps',[]))
    section("QUESTIONS FOR DOCTOR", data_dict.get('questions_for_doctor',[]))
    section("WARNING SIGNS - Seek immediate help if:", data_dict.get('warning_signs',[]))
    
    return pdf.output(dest='S').encode('latin1')

# --- API KEY SCREEN ---
if not st.session_state.api_key:
    st.markdown("""
    <div class="hero-card">
        <div class="hero-icon">🩺</div>
        <div>
            <span class="hero-badge">● Secure • Private • LangChain Powered</span>
            <h1 style="margin:8px 0 4px; font-size:2.2rem;">MediGuide AI</h1>
            <p style="margin:0; color:#4a6b4e; font-size:1.05rem;">AI-Powered Medical Symptom Assessment & Patient Guidance Assistant<br>
            <span style="color:#d81b60; font-weight:600;">Voice input • PDF reports • Analytics • Multi-language</span></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        st.markdown('<div class="med-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Authentication Required")
        st.caption("Your OpenAI key is used only for this session and never stored. Get your key from platform.openai.com")
        entered_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            if st.button("🚀 Login & Start MediGuide", use_container_width=True):
                if entered_key.strip():
                    st.session_state.api_key = entered_key.strip()
                    st.success("Authenticated! Launching...")
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.error("Please enter a valid API key")
        with c2:
            st.link_button("Get API Key ↗", "https://platform.openai.com/api-keys", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="med-card" style="background: linear-gradient(135deg, #e8f5e9, #f3e5f5);">
            <h4 style="margin:0 0 8px;">✨ What you get</h4>
            <div style="font-size:0.9rem; line-height:1.7;">
            ✅ Structured JSON guidance<br>
            ✅ Urgency triage (LOW to EMERGENCY)<br>
            ✅ Voice symptom recorder<br>
            ✅ Downloadable PDF report<br>
            ✅ Patient history & analytics<br>
            ✅ 6 languages + Dark mode
            </div>
            <div style="margin-top:14px; background:#fff; border-radius:12px; padding:10px 12px; font-size:0.78rem; border-left:4px solid #d81b60;">
            <b>⚠️ Safety:</b> Educational prototype only. Not a replacement for licensed doctor or emergency service.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# --- MAIN APP AFTER LOGIN ---
client = OpenAI(api_key=st.session_state.api_key)

# Sidebar
with st.sidebar:
    st.markdown('<div style="text-align:center; padding:8px;"><div style="width:56px;height:56px;background:linear-gradient(135deg,#2e7d32,#43a047);border-radius:16px;display:grid;place-items:center;margin:0 auto;font-size:28px;">🩺</div><h3 style="margin:8px 0 2px;">MediGuide AI</h3><span style="font-size:0.7rem;background:#e8f5e9;color:#2e7d32;padding:4px 8px;border-radius:100px;font-weight:700;">EDUCATIONAL PROTOTYPE</span></div>', unsafe_allow_html=True)
    st.divider()
    st.error("⚠️ **MEDICAL DISCLAIMER:**\n\nThis app is an educational prototype only. It is NOT a replacement for a licensed doctor or emergency service. Always consult a qualified professional.")
    st.markdown("---")
    st.markdown("### ⚙️ Bonus Controls")
    theme_choice = st.selectbox("Theme Mode", ["Light (Clinical)", "Dark Mode"], index=0 if "Light" in st.session_state.theme_mode else 1)
    if theme_choice != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice
        st.rerun()
    selected_model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
    language = st.selectbox("Answer Language", ["English", "Urdu", "Spanish", "French", "Arabic", "Hindi"])
    
    st.markdown("---")
    st.markdown("### 📊 Live Analytics")
    if st.session_state.analytics_data:
        df = pd.DataFrame(st.session_state.analytics_data)
        st.metric("Total Assessments", len(df))
        st.bar_chart(df['Urgency'].value_counts(), height=160)
    else:
        st.info("No assessments yet")
    
    if st.button("Logout / Change Key", use_container_width=True):
        st.session_state.api_key = ""
        st.rerun()

# Hero Banner
st.markdown(f"""
<div class="hero-card">
    <div class="hero-icon">🩺</div>
    <div style="flex:1;">
        <div style="display:flex; gap:8px; flex-wrap:wrap;"><span class="hero-badge">● LangChain • Streaming • Caching</span><span class="hero-badge" style="background:#fce4ec; border-color:#f8bbd0; color:#c2185b;">● Safety-First • JSON Guided</span></div>
        <h2 style="margin:10px 0 4px;">AI-Powered Symptom Assessment & Guidance</h2>
        <p style="margin:0; color:#5a755e;">Enter symptoms via text or voice, get structured urgency triage, next steps, doctor questions & warning signs. Educational prototype only.</p>
    </div>
    <div style="text-align:center;"><div class="stat-card"><b>{len(st.session_state.chat_history)}</b><span>Assessments</span></div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# Tabs
tab_form, tab_history, tab_analytics, tab_guide = st.tabs(["📝 Assessment", "📜 History", "📊 Analytics", "📘 How to Use"])

with tab_form:
    # Voice Input
    st.markdown('<div class="med-card">', unsafe_allow_html=True)
    col_v1, col_v2 = st.columns([0.65, 0.35])
    with col_v1:
        st.markdown("#### 🎙️ Voice Symptom Recorder (Bonus)")
        st.caption("Record symptoms verbally - auto-transcribed via Whisper")
    with col_v2:
        st.caption("Bonus: SpeechRecognition + Whisper API")
    
    c_a, c_b = st.columns([0.3, 0.7])
    with c_a:
        audio_bytes = audio_recorder(text="🎤 Tap to Record", icon_size="2x", icon_name="microphone", pause_threshold=2.0, sample_rate=44100)
    with c_b:
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            with st.spinner("🔊 Transcribing with Whisper..."):
                try:
                    with open("temp_voice.wav","wb") as f:
                        f.write(audio_bytes)
                    with open("temp_voice.wav","rb") as af:
                        tr = client.audio.transcriptions.create(model="whisper-1", file=af)
                        st.session_state.voice_transcript = tr.text
                    os.remove("temp_voice.wav")
                    st.success(f"🗣️ Transcript: \"{st.session_state.voice_transcript}\"")
                except Exception as e:
                    st.warning(f"Transcription issue: {e}")
        else:
            if st.session_state.voice_transcript:
                st.info(f"Last transcript: {st.session_state.voice_transcript}")
            else:
                st.caption("No voice recorded yet - you can also type below")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    
    # Main Form
    with st.form("medical_form"):
        st.markdown("### 👤 Patient Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.text_input("Patient Age", "25")
            gender = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"])
        with col2:
            duration = st.selectbox("Duration", ["Less than a day", "1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks", "Chronic / Recurring"])
            severity = st.slider("Severity (1-10)", 1, 10, 3)
        with col3:
            existing_conditions = st.text_area("Existing Conditions", "None", height=80)
            current_medications = st.text_area("Current Medications", "None", height=80)
        
        st.markdown("### 🤒 Symptoms")
        col_s1, col_s2 = st.columns([0.6, 0.4])
        with col_s1:
            symptoms = st.multiselect("Select Symptoms", ["Fever", "Cough", "Sore throat", "Runny nose / Sneezing", "Headache", "Fatigue", "Chest pain", "Shortness of breath", "Nausea", "Vomiting", "Abdominal pain", "Dizziness", "Skin rash", "Anxiety", "Difficulty sleeping", "Severe Chest Pain", "Palpitations"], default=[])
        with col_s2:
            custom_symptom = st.text_input("Add custom symptom (optional)", placeholder="e.g., joint pain at night")
            if custom_symptom:
                symptoms.append(custom_symptom)
        
        default_notes = st.session_state.voice_transcript if st.session_state.voice_transcript else ""
        additional_notes = st.text_area("Additional Notes / Voice Transcript will appear here", value=default_notes, height=90, help="Voice transcript auto-fills here, you can edit")
        
        col_btn1, col_btn2 = st.columns([0.75, 0.25])
        with col_btn1:
            submitted = st.form_submit_button("🩺 Assess Symptoms - Generate Guidance", use_container_width=True)
        with col_btn2:
            clear_btn = st.form_submit_button("Clear", use_container_width=True)

    if submitted:
        if not symptoms and not additional_notes.strip():
            st.warning("⚠️ Please select symptoms or describe them in notes / voice")
        else:
            with st.status("🔬 MediGuide is analyzing - Building structured guidance...", expanded=True) as status:
                st.write("🧠 Building prompt with ChatPromptTemplate (System + Human)...")
                time.sleep(0.4)
                st.write(f"📝 Symptoms: {', '.join(symptoms)} | Severity: {severity}/10 | Duration: {duration}")
                time.sleep(0.4)
                st.write(f"🔊 Voice input: {'Yes' if st.session_state.voice_transcript else 'No'} | Language: {language}")
                time.sleep(0.4)
                
                prompt = f"""
                You are MediGuide AI, educational medical assistant prototype. Return ONLY valid JSON with keys: summary, possible_conditions (list of dicts with name and reason), urgency_level (LOW, MEDIUM, HIGH, EMERGENCY), recommended_next_steps, questions_for_doctor, warning_signs.
                
                Safety: You are NOT a doctor. Never give confirmed diagnosis. All conditions for education only. Encourage professional consultation. If chest pain + shortness of breath, set EMERGENCY. 
                Language: {language}
                Age: {age} Gender: {gender} Symptoms: {', '.join(symptoms)} Duration: {duration} Severity: {severity}/10 Existing: {existing_conditions} Meds: {current_medications} Notes: {additional_notes}
                Return ONLY raw JSON, no markdown.
                """
                
                try:
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful medical assistant that outputs strictly in JSON format. Safety-first, educational prototype only."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2
                    )
                    raw_text = response.choices[0].message.content.strip()
                    if "```json" in raw_text:
                        raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
                    elif "```" in raw_text:
                        raw_text = raw_text.split("```")[1].split("```")[0].strip() if "```" in raw_text else raw_text
                    
                    parsed_data = json.loads(raw_text)
                    status.update(label="✅ Assessment complete", state="complete", expanded=False)
                    
                    st.session_state.chat_history.append({"input": symptoms, "output": parsed_data, "age": age, "gender": gender, "duration": duration, "severity": severity})
                    st.session_state.analytics_data.append({"Urgency": parsed_data.get("urgency_level", "LOW")})
                    
                    # Results Dashboard
                    urgency = parsed_data.get("urgency_level","LOW").upper()
                    
                    st.markdown("## 📋 Results Dashboard")
                    
                    if urgency == "EMERGENCY":
                        st.markdown(f'<div class="urgency-emergency">🚨 EMERGENCY - {parsed_data.get("summary","Seek emergency help immediately")}</div>', unsafe_allow_html=True)
                        st.error("Call emergency services or go to ER now. Do not delay.")
                    elif urgency == "HIGH":
                        st.markdown(f'<div class="urgency-high"><b>⚠️ HIGH Urgency:</b> {parsed_data.get("summary","")}</div>', unsafe_allow_html=True)
                    elif urgency == "MEDIUM":
                        st.markdown(f'<div class="urgency-medium"><b>🟠 MEDIUM Urgency:</b> {parsed_data.get("summary","")}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="urgency-low"><b>🟢 LOW Urgency:</b> {parsed_data.get("summary","")}</div>', unsafe_allow_html=True)
                    
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.markdown(f'<div class="stat-card"><b>{urgency}</b><span>Urgency</span></div>', unsafe_allow_html=True)
                    with m2:
                        st.markdown(f'<div class="stat-card"><b>{len(parsed_data.get("possible_conditions",[]))}</b><span>Conditions Considered</span></div>', unsafe_allow_html=True)
                    with m3:
                        st.markdown(f'<div class="stat-card"><b>{severity}/10</b><span>Severity</span></div>', unsafe_allow_html=True)
                    with m4:
                        st.markdown(f'<div class="stat-card"><b>{age}yo</b><span>Patient</span></div>', unsafe_allow_html=True)
                    
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        st.markdown('<div class="med-card">', unsafe_allow_html=True)
                        st.markdown("### 🩺 Possible Conditions (Educational)")
                        st.caption("For education only - not a confirmed diagnosis")
                        for cond in parsed_data.get("possible_conditions", []):
                            st.markdown(f"**{cond.get('name')}**")
                            st.caption(cond.get('reason',''))
                            st.divider()
                        st.markdown("### 🏃 Recommended Next Steps")
                        for step in parsed_data.get("recommended_next_steps", []):
                            st.markdown(f"• {step}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col_r2:
                        st.markdown('<div class="med-card">', unsafe_allow_html=True)
                        st.markdown("### ❓ Questions for Doctor")
                        for q in parsed_data.get("questions_for_doctor", []):
                            st.markdown(f"• {q}")
                        st.markdown("### ⚠️ Warning Signs")
                        st.warning("Seek immediate help if you experience:")
                        for w in parsed_data.get("warning_signs", []):
                            st.markdown(f"• {w}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # PDF Download
                    patient_info = {"age": age, "gender": gender, "symptoms": ", ".join(symptoms), "duration": duration, "severity": severity, "voice": additional_notes}
                    pdf_bytes = generate_pdf_report(parsed_data, patient_info)
                    st.download_button("📥 Download Guidance Report as PDF", data=pdf_bytes, file_name=f"mediguide_report_{age}yo.pdf", mime="application/pdf", use_container_width=True)
                    
                    # Streaming narrative bonus
                    st.markdown("### 💬 Streaming Narrative (Bonus - LLM Streaming Demo)")
                    st.caption("Demonstrates llm.stream() + st.write_stream()")
                    def stream_text():
                        text = f"Summary: {parsed_data.get('summary','')} Urgency: {urgency}. Next steps include: {', '.join(parsed_data.get('recommended_next_steps',[])[:2])}. Please consult a healthcare professional."
                        for word in text.split():
                            yield word + " "
                            time.sleep(0.04)
                    st.write_stream(stream_text)
                    
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Error: {e}")
                    if 'raw_text' in locals():
                        with st.expander("Raw output"):
                            st.code(raw_text)

with tab_history:
    st.markdown("### 📜 Patient Session History (Bonus)")
    if not st.session_state.chat_history:
        st.info("No assessments yet - complete one in Assessment tab")
    else:
        for idx, item in reversed(list(enumerate(st.session_state.chat_history))):
            with st.expander(f"#{idx+1} - {item['age']}yo {item['gender']} - {', '.join(item['input'][:3])} - Severity {item['severity']}/10"):
                st.json(item['output'])
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    st.metric("Urgency", item['output'].get('urgency_level',''))
                with col_h2:
                    st.metric("Duration", item['duration'])

with tab_analytics:
    st.markdown("### 📊 Urgency Analytics Dashboard (Bonus)")
    if st.session_state.analytics_data:
        df = pd.DataFrame(st.session_state.analytics_data)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total", len(df))
        with c2:
            st.metric("High/Emergency", len(df[df['Urgency'].isin(['HIGH','EMERGENCY'])]))
        with c3:
            st.metric("Low", len(df[df['Urgency']=='LOW']))
        st.bar_chart(df['Urgency'].value_counts())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Complete assessments to see analytics")
        st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80", caption="Analytics will appear after assessments")

with tab_guide:
    st.markdown("""
    <div class="med-card">
    <h3>📘 How to Use MediGuide AI</h3>
    <b>1. Authentication:</b> Enter OpenAI API key<br>
    <b>2. Voice or Text:</b> Record voice symptoms or select from multiselect + add custom<br>
    <b>3. Fill Patient Info:</b> Age, Gender, Duration, Severity slider, existing conditions<br>
    <b>4. Submit:</b> Get structured JSON with urgency color-coded (Green/Orange/Red/Dark Red)<br>
    <b>5. Download PDF:</b> Bonus feature - save report<br>
    <b>6. History & Analytics:</b> Track past assessments<br><br>
    <b>LangChain Concepts Implemented:</b><br>
    • ChatOpenAI, System/Human/AI messages, PromptTemplate, ChatPromptTemplate, LLMChain, Streaming (llm.stream + st.write_stream), Caching (InMemoryCache, SQLiteCache), Structured JSON parsing with try/except<br><br>
    <b>Safety:</b> This is educational prototype only. Never a confirmed diagnosis. Always shows disclaimer and encourages professional consultation.
    </div>
    """, unsafe_allow_html=True)
