📖 Project Overview
MediGuide AI is an intelligent Streamlit application where a user enters basic information and symptoms, and a LangChain-powered LLM generates structured, safety-focused preliminary guidance.

The app collects patient demographics, symptoms (via text, multiselect, and voice), duration, severity, and medical history, then uses a safety-engineered ChatPromptTemplate to return valid JSON with summary, possible conditions (educational), urgency triage, next steps, doctor questions, and warning signs.

Real-world framing: Think of it as a patient intake assistant that helps a user organize information to discuss with a doctor, NOT a diagnostic tool.
