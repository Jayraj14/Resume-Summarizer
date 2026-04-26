import streamlit as st
import pdfplumber
import ollama

st.set_page_config(page_title="Resume Chatbot", page_icon="📄")
st.title("📄 Resume Analyzer (Chat with your Resume)")


# ----------- PDF TEXT EXTRACTION ----------- #
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


# ----------- SESSION STATE ----------- #
if "messages" not in st.session_state:
    st.session_state.messages = []

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""


# ----------- FILE UPLOAD ----------- #
uploaded_file = st.file_uploader("Upload your Resume", type=["pdf", "txt"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = uploaded_file.read().decode("utf-8")

    if resume_text.strip():
        st.session_state.resume_text = resume_text
        st.success("✅ Resume uploaded successfully!")

        with st.expander("📄 Preview Resume"):
            st.write(resume_text[:1000])
    else:
        st.error("❌ Could not extract text.")


# ----------- INITIAL ANALYSIS (Score + Summary) ----------- #
if st.session_state.resume_text:

    if st.button("📊 Generate Resume Analysis"):

        with st.spinner("Analyzing resume..."):

            analysis_prompt = f"""
            You are a professional resume evaluator.

            Important rule:
            - Do NOT mention any name from the resume.
            - Always refer to the candidate as "the person".

            Analyze the resume and provide:

            1. Resume Score (out of 10)
            2. Strengths
            3. Weaknesses
            4. Suggested Roles
            5. Improvements

            Give structured output with clear headings.

            Resume:
            {st.session_state.resume_text}
            """

            try:
                response = ollama.chat(
                    model="phi", messages=[{"role": "user", "content": analysis_prompt}]
                )

                result = response["message"]["content"]

                st.subheader("📊 Resume Analysis")
                st.markdown(result)

            except Exception as e:
                st.error("❌ Error analyzing resume")
                st.write(e)


# ----------- CHAT SECTION ----------- #
if st.session_state.resume_text:

    st.subheader("💬 Chat with your Resume")

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask something about your resume...")

    if user_input:

        # 🔒 Keyword filter
        blocked_keywords = ["movie", "song", "weather", "news", "cricket", "match"]

        if any(word in user_input.lower() for word in blocked_keywords):
            reply = "⚠️ I can only answer questions related to your resume."
            st.warning(reply)

            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": reply})

        else:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(user_input)

            chat_prompt = f"""
            You are a strict resume assistant.

            Rules:
            - ONLY answer resume-related questions
            - If unrelated, say: "I can only answer questions related to your resume."
            - Do NOT mention any name from the resume
            - Refer to the candidate as "the person"
            - Be concise and professional

            Resume:
            {st.session_state.resume_text}

            Question:
            {user_input}
            """

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = ollama.chat(
                            model="phi",
                            messages=[{"role": "user", "content": chat_prompt}],
                        )

                        reply = response["message"]["content"]
                        st.markdown(reply)

                    except Exception as e:
                        reply = "❌ Error connecting to local model."
                        st.error(reply)
                        st.write(e)

            st.session_state.messages.append({"role": "assistant", "content": reply})
