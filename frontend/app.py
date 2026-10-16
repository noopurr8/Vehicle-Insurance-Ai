import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import uuid
from ai.chatbot.chatbot import chat_turn

API_URL = "http://127.0.0.1:8000/claims/process"


st.set_page_config(
    page_title="AI Vehicle Insurance",
    page_icon="🚗",
    layout="wide"
)


st.title("🚗 AI Vehicle Insurance Platform")
st.write("AI-powered vehicle insurance claim processing")
# ---------------- AI INSURANCE CHATBOT ----------------

st.subheader("💬 AI Insurance Assistant")

if "chat_thread_id" not in st.session_state:
    st.session_state.chat_thread_id = str(uuid.uuid4())

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_message = st.chat_input(
    "Ask about insurance, policies, applications, or claims..."
)

if user_message:
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_message
    })

    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply, widgets = chat_turn(
                st.session_state.chat_thread_id,
                user_message
            )

        st.write(reply)

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": reply
    })

st.divider()
# ---------------- AI ANALYSIS FOR EXISTING CLAIM ----------------

st.subheader("🔍 Analyze Existing Claim")

claim_number = st.text_input(
    "Claim Number",
    placeholder="Example: CLM-2026-00005"
)

ai_document = st.file_uploader(
    "Upload Insurance Document for AI Analysis",
    type=["png", "jpg", "jpeg"],
    key="ai_document"
)

ai_vehicle_image = st.file_uploader(
    "Upload Vehicle Damage Image for AI Analysis",
    type=["png", "jpg", "jpeg"],
    key="ai_vehicle_image"
)

if st.button("🔍 Run AI Analysis", type="primary"):

    if not claim_number:
        st.error("Please enter the claim number.")

    elif ai_document is None or ai_vehicle_image is None:
        st.error("Please upload both the insurance document and vehicle image.")

    else:
        with st.spinner(
            "Running OCR, damage detection, fraud screening and priority analysis..."
        ):

            try:
                claim_id = claim_number.replace("CLM-2026-", "")

                files = {
                    "document": (
                        ai_document.name,
                        ai_document.getvalue(),
                        ai_document.type
                    ),
                    "vehicle_image": (
                        ai_vehicle_image.name,
                        ai_vehicle_image.getvalue(),
                        ai_vehicle_image.type
                    )
                }

                response = requests.post(
                    f"http://127.0.0.1:8000/claims/{claim_id}/process-ai",
                    files=files
                )

                if response.status_code == 200:

                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])

                    else:
                        st.success(
                            f"AI analysis completed for {result['claim_number']}"
                        )

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Claim Number",
                                result["claim_number"]
                            )

                        with col2:
                            st.metric(
                                "Priority",
                                result["priority"]
                            )

                        with col3:
                            st.metric(
                                "Status",
                                result["status"]
                            )

                        st.divider()

                        st.write("### 📄 OCR Results")

                        extracted = result["ocr"]["extracted_fields"]

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write("**Vehicle Number**")
                            st.write(
                                extracted.get("vehicle_number")
                                or "Not detected"
                            )

                        with col2:
                            st.write("**Policy Number**")
                            st.write(
                                extracted.get("policy_number")
                                or "Not detected"
                            )

                        with col3:
                            st.write("**Expiry Date**")
                            st.write(
                                extracted.get("expiry_date")
                                or "Not detected"
                            )

                        st.divider()

                        st.write("### 🚗 Damage Detection")

                        damage = result["damage_detection"]

                        st.write(
                            f"**Total Damage Detected:** "
                            f"{damage['damage_count']}"
                        )

                        for item in damage["damages"]:
                            st.write(
                                f"• **{item['damage_type']}** "
                                f"({item['confidence'] * 100:.1f}% confidence)"
                            )

                        st.divider()

                        st.write("### 🛡️ Fraud Screening")

                        fraud = result["fraud_detection"]
                        fraud_probability = fraud["fraud_probability"]

                        st.progress(fraud_probability)

                        st.write(
                            f"**Fraud Probability:** "
                            f"{fraud_probability * 100:.1f}%"
                        )

                        if fraud["fraud_prediction"] == 1:
                            st.warning("Claim flagged for fraud review.")
                        else:
                            st.success("Claim not flagged for fraud.")

                        st.divider()

                        st.write("### ⚡ Claim Priority")

                        st.info(
                            f"Priority assigned: **{result['priority']}**"
                        )

                else:
                    st.error(
                        f"API Error: {response.status_code}"
                    )
                    st.code(response.text)

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure the backend server is running."
                )

            except Exception as e:
                st.error(f"Unexpected error: {e}")

st.divider()

st.divider()

st.subheader("Submit Insurance Claim")

document = st.file_uploader(
    "Upload Insurance Document",
    type=["png", "jpg", "jpeg"]
)

vehicle_image = st.file_uploader(
    "Upload Vehicle Damage Image",
    type=["png", "jpg", "jpeg"]
)

claim_description = st.text_area(
    "Claim Description",
    placeholder="Describe the accident or vehicle damage..."
)


if st.button("🔍 Process Claim", type="primary"):

    if document is None or vehicle_image is None:
        st.error("Please upload both the insurance document and vehicle image.")

    else:
        with st.spinner("Processing claim using AI..."):

            try:
                files = {
                    "document": (
                        document.name,
                        document.getvalue(),
                        document.type
                    ),
                    "vehicle_image": (
                        vehicle_image.name,
                        vehicle_image.getvalue(),
                        vehicle_image.type
                    )
                }

                data = {
                    "claim_description": claim_description
                }

                response = requests.post(
                    API_URL,
                    files=files,
                    data=data
                )

                if response.status_code == 200:

                    result = response.json()

                    st.success("Claim processed successfully!")

                    st.divider()

                    # Claim summary
                    st.subheader("📋 Claim Summary")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Claim ID",
                            result["claim_id"]
                        )

                    with col2:
                        st.metric(
                            "Priority",
                            result["priority"]
                        )

                    with col3:
                        st.metric(
                            "Status",
                            result["status"]
                        )

                    st.divider()

                    # OCR
                    st.subheader("📄 Extracted Information")

                    extracted = result["ocr"]["extracted_fields"]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**Vehicle Number**")
                        st.write(
                            extracted.get("vehicle_number")
                            or "Not detected"
                        )

                    with col2:
                        st.write("**Policy Number**")
                        st.write(
                            extracted.get("policy_number")
                            or "Not detected"
                        )

                    with col3:
                        st.write("**Expiry Date**")
                        st.write(
                            extracted.get("expiry_date")
                            or "Not detected"
                        )

                    st.divider()

                    # Damage detection
                    st.subheader("🚗 Damage Detection")

                    damage = result["damage_detection"]

                    st.write(
                        f"**Total Damage Detected:** "
                        f"{damage['damage_count']}"
                    )

                    for item in damage["damages"]:
                        st.write(
                            f"• **{item['damage_type']}** "
                            f"({item['confidence'] * 100:.1f}% confidence)"
                        )

                    st.divider()

                    # Fraud detection
                    st.subheader("🕵️ Fraud Detection")

                    fraud = result["fraud_detection"]

                    fraud_probability = fraud["fraud_probability"]

                    st.progress(fraud_probability)

                    st.write(
                        f"**Fraud Probability:** "
                        f"{fraud_probability * 100:.1f}%"
                    )

                    if fraud["fraud_prediction"] == 1:
                        st.warning("Claim flagged for fraud review.")
                    else:
                        st.success("Claim not flagged for fraud.")

                    st.divider()

                    # Final decision
                    st.subheader("⚡ Claim Priority")

                    st.info(
                        f"Priority assigned: **{result['priority']}**"
                    )

                else:
                    st.error(
                        f"API Error: {response.status_code}"
                    )
                    st.code(response.text)

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure the backend server is running."
                )

            except Exception as e:
                st.error(f"Unexpected error: {e}")