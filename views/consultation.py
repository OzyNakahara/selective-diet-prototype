import streamlit as st
from openai import OpenAI
import json
import datetime
import re

st.title("AI Consultation")
st.write("Type your health details and dietary goals. Our AI will configure your profile.")

user_text = st.text_area(
    "Example: I am a 30 year old male, 180cm, 80kg. I want to build muscle and I eat Halal.",
    height=150
)

VALID_DIETS = [
    "Weight Loss",
    "Gain Muscle",
    "Halal",
    "Gluten Free",
    "Vegan",
    "Vegetarian",
    "Keto",
    "Paleo",
    "Dairy Free",
    "Low Sodium",
    "Diabetic",
    "Nut Free"
]


def clear_previous_ai_outputs():
    """
    Clears previous AI outputs and final resolved profile values.
    Keeps form_* values from registration.py so personalization.py can compare:
    form_* vs ai_*.
    """
    keys_to_clear = [
        # Previous AI-source values
        "ai_age",
        "ai_dob",
        "ai_gender",
        "ai_height",
        "ai_weight",
        "ai_diets",

        # Previous final resolved values
        "user_dob",
        "user_gender",
        "user_height",
        "user_weight",

        # Diet/macro state
        "selected_diets",
        "diet_profile",
        "target_calories",
        "target_macros",

        # AI commentary cache from personalization.py
        "ai_commentary",
        "commentary_signature",
    ]

    for key in keys_to_clear:
        st.session_state.pop(key, None)

    # Clear conflict radio choices from personalization.py
    for key in list(st.session_state.keys()):
        if key.startswith("choice_"):
            st.session_state.pop(key, None)


def extract_json_from_text(text):
    """
    Attempts to parse JSON from the model output.
    Handles plain JSON and markdown fenced JSON.
    """
    cleaned = text.strip()

    # Remove markdown fences if present
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # First try direct JSON parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first JSON object from text
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Could not parse JSON from AI response.")


def normalize_ai_data(data):
    """
    Validates and normalizes AI output.
    Returns a clean dictionary with allowed values only.
    """
    clean = {
        "age": None,
        "gender": None,
        "height": None,
        "weight": None,
        "diets": []
    }

    # Age
    age = data.get("age")
    try:
        if age is not None:
            age = int(age)
            if 1 <= age <= 120:
                clean["age"] = age
    except (TypeError, ValueError):
        pass

    # Gender
    gender = data.get("gender")
    if gender in ["Male", "Female"]:
        clean["gender"] = gender

    # Height
    height = data.get("height")
    try:
        if height is not None:
            height = float(height)
            if 50.0 <= height <= 300.0:
                clean["height"] = height
    except (TypeError, ValueError):
        pass

    # Weight
    weight = data.get("weight")
    try:
        if weight is not None:
            weight = float(weight)
            if 20.0 <= weight <= 300.0:
                clean["weight"] = weight
    except (TypeError, ValueError):
        pass

    # Diets
    diets = data.get("diets", [])
    if isinstance(diets, list):
        clean["diets"] = [d for d in diets if d in VALID_DIETS]

    return clean


if st.button("Analyze and Update", use_container_width=True):
    if not user_text.strip():
        st.error("Please enter your details.")
    else:
        with st.spinner("Consulting AI..."):
            try:
                api_key = st.secrets["FUGU_API_KEY"]
                client = OpenAI(
                    base_url="https://api.sakana.ai/v1",
                    api_key=api_key
                )

                system_prompt = """
                Extract health profile data from the user's text.

                Return ONLY raw JSON. Do not include markdown, commentary, explanation, or extra text.

                JSON schema:
                {
                    "age": int or null,
                    "gender": "Male", "Female", or "Select",
                    "height": float or null,
                    "weight": float or null,
                    "diets": list of strings
                }

                Allowed diet strings:
                "Weight Loss", "Gain Muscle", "Halal", "Gluten Free", "Vegan",
                "Vegetarian", "Keto", "Paleo", "Dairy Free", "Low Sodium",
                "Diabetic", "Nut Free"

                Rules:
                - Use centimeters for height.
                - Use kilograms for weight.
                - If a value is not clearly provided, return null.
                - Do not guess missing age, height, weight, or gender.
                - Only use diet strings from the allowed list.
                - If no diets are mentioned, return an empty list.
                """

                response = client.chat.completions.create(
                    model="fugu",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0
                )

                raw_output = response.choices[0].message.content.strip()
                parsed_data = extract_json_from_text(raw_output)
                data = normalize_ai_data(parsed_data)

                # Clear previous AI/resolved outputs, but keep form_* data
                clear_previous_ai_outputs()

                # Store AI-source values only.
                # personalization.py will compare these with form_* values.
                if data["age"] is not None:
                    st.session_state.ai_age = data["age"]

                    # Approximate DOB from age.
                    # This is intentionally approximate because AI text usually gives age,
                    # not exact date of birth.
                    calc_year = datetime.date.today().year - data["age"]
                    st.session_state.ai_dob = datetime.date(calc_year, 1, 1)

                if data["gender"] is not None:
                    st.session_state.ai_gender = data["gender"]

                if data["height"] is not None:
                    st.session_state.ai_height = data["height"]

                if data["weight"] is not None:
                    st.session_state.ai_weight = data["weight"]

                if data["diets"]:
                    st.session_state.ai_diets = data["diets"]

                st.switch_page("views/personalization.py")

            except Exception as e:
                st.error(f"API Error: {e}")