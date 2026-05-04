import streamlit as st
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import Orchestrator

st.set_page_config(page_title="Competitor Intelligence", layout="wide")

st.title("📊 Competitor Intelligence System")

company = st.text_input("Enter Company Name", "Stripe")
industry = st.text_input("Enter Industry", "fintech")

if st.button("Run Analysis"):
    st.info("Running analysis...")

    orchestrator = Orchestrator()
    result = orchestrator.run(company=company, industry=industry)

    evaluation = result.get("evaluation", {})

    st.success("Analysis Complete!")

    st.subheader("📈 Score")
    st.write(evaluation.get("score"))

    st.subheader("✅ Passed")
    st.write(evaluation.get("passed"))

    st.subheader("⚠️ Gaps")
    for gap in evaluation.get("gaps", []):
        st.write(f"- {gap}")

    st.subheader("💡 Suggested Queries")
    for q in evaluation.get("suggested_queries", []):
        st.write(f"- {q}")