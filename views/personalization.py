import streamlit as st
import datetime
import re

st.title("Your Health Profile")


# ============================================================
# Constants
# ============================================================

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
    "Nut Free",
]

DIET_OPTIONS = [
    {"label": "Weight Loss", "icon": "monitor_weight"},
    {"label": "Gain Muscle", "icon": "fitness_center"},
    {"label": "Halal", "icon": "restaurant"},
    {"label": "Gluten Free", "icon": "bakery_dining"},
    {"label": "Vegan", "icon": "eco"},
    {"label": "Vegetarian", "icon": "local_florist"},
    {"label": "Keto", "icon": "set_meal"},
    {"label": "Paleo", "icon": "kebab_dining"},
    {"label": "Dairy Free", "icon": "opacity"},
    {"label": "Low Sodium", "icon": "grain"},
    {"label": "Diabetic", "icon": "healing"},
    {"label": "Nut Free", "icon": "block"},
]


# ============================================================
# Helper Functions
# ============================================================

def age_from_dob(dob):
    if not isinstance(dob, datetime.date):
        return None

    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def values_equal(field, a, b):
    """
    Compare form value vs AI value.
    Float fields allow tiny differences.
    """
    if a is None or b is None:
        return False

    if field in ["height", "weight"]:
        try:
            return abs(float(a) - float(b)) <= 0.1
        except (TypeError, ValueError):
            return False

    return a == b


def format_conflict_option(field, source, value):
    """
    Display text for conflict resolver radio buttons.
    """
    source_label = "You entered" if source == "form" else "AI suggested"

    if field == "dob":
        if source == "ai":
            ai_age = st.session_state.get("ai_age")
            if ai_age is not None:
                return f"Age {ai_age} → approx. DOB {value}  ({source_label})"
        return f"{value}  ({source_label})"

    if field == "height":
        return f"{value} cm  ({source_label})"

    if field == "weight":
        return f"{value} kg  ({source_label})"

    return f"{value}  ({source_label})"


def make_format_func(field):
    # Binds field correctly for each radio button.
    return lambda option: format_conflict_option(field, option[0], option[1])


def clear_commentary_cache():
    st.session_state.pop("ai_commentary", None)
    st.session_state.pop("commentary_signature", None)


def reconcile_profile_sources():
    """
    Reconciles profile data from three possible sources:

    1. user_* = final resolved value
    2. form_* = signup form value
    3. ai_*   = AI consultation value

    Rules:
    - If user_* already exists, keep it.
    - If only form_* exists, use form_*.
    - If only ai_* exists, use ai_*.
    - If both exist and match, use the form value.
    - If both exist and disagree, ask the user to choose.
    """

    conflicts = []

    # -----------------------------
    # Date of Birth / Age
    # -----------------------------
    if "user_dob" not in st.session_state:
        form_dob = st.session_state.get("form_dob")
        ai_dob = st.session_state.get("ai_dob")
        ai_age = st.session_state.get("ai_age")

        if form_dob is not None and ai_dob is None:
            st.session_state.user_dob = form_dob

        elif ai_dob is not None and form_dob is None:
            st.session_state.user_dob = ai_dob

        elif form_dob is not None and ai_dob is not None:
            if form_dob == ai_dob:
                st.session_state.user_dob = form_dob
            else:
                # AI usually gives age, not exact DOB.
                # ai_dob is approximate, usually Jan 1 of calculated year.
                # If the form DOB produces roughly the same age, trust form DOB.
                form_age = age_from_dob(form_dob)

                if (
                    ai_age is not None
                    and form_age is not None
                    and abs(form_age - int(ai_age)) <= 1
                ):
                    st.session_state.user_dob = form_dob
                else:
                    conflicts.append("dob")

    # -----------------------------
    # Gender, Height, Weight
    # -----------------------------
    for field in ["gender", "height", "weight"]:
        user_key = f"user_{field}"

        if user_key in st.session_state:
            continue

        form_val = st.session_state.get(f"form_{field}")
        ai_val = st.session_state.get(f"ai_{field}")

        if form_val is not None and ai_val is None:
            st.session_state[user_key] = form_val

        elif ai_val is not None and form_val is None:
            st.session_state[user_key] = ai_val

        elif form_val is not None and ai_val is not None:
            if values_equal(field, form_val, ai_val):
                st.session_state[user_key] = form_val
            else:
                conflicts.append(field)

    return conflicts


def initialize_selected_diets():
    """
    Initializes selected_diets once from AI/form diet sources.
    After user starts clicking diet buttons, we do not overwrite their choices.
    """
    if "selected_diets" not in st.session_state:
        merged = set()

        ai_diets = st.session_state.get("ai_diets", [])
        form_diets = st.session_state.get("form_diets", [])

        if isinstance(ai_diets, list):
            merged.update(ai_diets)

        if isinstance(form_diets, list):
            merged.update(form_diets)

        st.session_state.selected_diets = [
            diet for diet in VALID_DIETS if diet in merged
        ]


def profile_missing_fields():
    """
    Returns a list of required missing/invalid profile fields.
    """
    missing = []

    dob = st.session_state.get("user_dob")
    gender = st.session_state.get("user_gender")
    height = st.session_state.get("user_height")
    weight = st.session_state.get("user_weight")

    if not isinstance(dob, datetime.date):
        missing.append("Date of Birth")

    if gender not in ["Male", "Female"]:
        missing.append("Biological Sex")

    try:
        height = float(height)
        if not (50.0 <= height <= 300.0):
            missing.append("Height")
    except (TypeError, ValueError):
        missing.append("Height")

    try:
        weight = float(weight)
        if not (20.0 <= weight <= 300.0):
            missing.append("Weight")
    except (TypeError, ValueError):
        missing.append("Weight")

    return missing


def show_missing_profile_form(missing):
    """
    Shows a form if required profile values are missing.
    Prevents KeyError crashes when AI consultation did not extract everything.
    """
    st.warning(
        "Some required profile details are missing or invalid. "
        "Please complete them before continuing."
    )

    if missing:
        st.caption("Missing or invalid: " + ", ".join(missing))

    with st.form("missing_profile_form"):
        current_dob = st.session_state.get("user_dob")
        if not isinstance(current_dob, datetime.date):
            current_dob = None

        current_gender = st.session_state.get("user_gender", "Select")
        gender_options = ["Select", "Male", "Female"]
        gender_index = (
            gender_options.index(current_gender)
            if current_gender in gender_options
            else 0
        )

        current_height = st.session_state.get("user_height")
        try:
            current_height = float(current_height)
            if not (50.0 <= current_height <= 300.0):
                current_height = None
        except (TypeError, ValueError):
            current_height = None

        current_weight = st.session_state.get("user_weight")
        try:
            current_weight = float(current_weight)
            if not (20.0 <= current_weight <= 300.0):
                current_weight = None
        except (TypeError, ValueError):
            current_weight = None

        dob_input = st.date_input(
            "Date of Birth",
            value=current_dob,
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            key="missing_dob_input",
        )

        gender_input = st.selectbox(
            "Biological Sex, for BMR",
            options=gender_options,
            index=gender_index,
            key="missing_gender_input",
        )

        height_input = st.number_input(
            "Height (cm)",
            value=current_height,
            min_value=50.0,
            max_value=300.0,
            step=1.0,
            key="missing_height_input",
        )

        weight_input = st.number_input(
            "Weight (kg)",
            value=current_weight,
            min_value=20.0,
            max_value=300.0,
            step=1.0,
            key="missing_weight_input",
        )

        submitted = st.form_submit_button("Save Details", use_container_width=True)

        if submitted:
            if not dob_input:
                st.error("Date of Birth is required.")
            elif gender_input == "Select":
                st.error("Please select Male or Female for BMR calculation.")
            elif not height_input:
                st.error("Height is required.")
            elif not weight_input:
                st.error("Weight is required.")
            else:
                st.session_state.user_dob = dob_input
                st.session_state.user_gender = gender_input
                st.session_state.user_height = float(height_input)
                st.session_state.user_weight = float(weight_input)

                clear_commentary_cache()
                st.rerun()


def show_conflict_resolver(conflicts):
    """
    Shows conflict UI when signup form and AI consultation disagree.
    """
    labels = {
        "dob": "Date of Birth / Age",
        "gender": "Biological Sex",
        "height": "Height",
        "weight": "Weight",
    }

    st.warning(
        "We found differences between the information you entered and the AI consultation. "
        "Please choose which value to use."
    )

    with st.form("conflict_resolver"):
        choices = {}

        for field in conflicts:
            form_val = st.session_state.get(f"form_{field}")
            ai_val = st.session_state.get(f"ai_{field}")

            choices[field] = st.radio(
                f"**{labels[field]}**",
                options=[
                    ("form", form_val),
                    ("ai", ai_val),
                ],
                format_func=make_format_func(field),
                key=f"choice_{field}",
            )

        submitted = st.form_submit_button("Confirm Selections", use_container_width=True)

        if submitted:
            for field, selected in choices.items():
                _, selected_value = selected
                st.session_state[f"user_{field}"] = selected_value

            clear_commentary_cache()
            st.rerun()

    st.stop()


def is_commentary_safe(text):
    """
    Basic post-generation safety filter for AI commentary.
    The system prompt is the first guardrail; this is a backup.
    """
    banned_patterns = [
        r"\bfat\b",
        r"\bobese\b",
        r"\bobesity\b",
        r"\blazy\b",
        r"\bugly\b",
        r"\bgross\b",
        r"\bdisgusting\b",
        r"\bfailure\b",
        r"\bpathetic\b",
        r"\bshame\b",
        r"\bshaming\b",
    ]

    lowered = text.lower()

    for pattern in banned_patterns:
        if re.search(pattern, lowered):
            return False

    return True


def generate_ai_commentary(age, gender, bmi, bmr):
    """
    Generates supportive AI commentary.
    If API/secrets/OpenAI are unavailable, returns a safe fallback.
    Cached by metric signature so it does not call the API on every rerun.
    """
    fallback = (
        "These baseline metrics are a helpful starting point. "
        "Use the settings below to choose goals that feel realistic, sustainable, "
        "and supportive of your health."
    )

    metrics_signature = f"{age}-{gender}-{bmi:.1f}-{int(bmr)}"

    if st.session_state.get("commentary_signature") == metrics_signature:
        return st.session_state.get("ai_commentary", fallback)

    try:
        from openai import OpenAI

        api_key = st.secrets["FUGU_API_KEY"]

        client = OpenAI(
            base_url="https://api.sakana.ai/v1",
            api_key=api_key,
        )

        system_prompt = """
        You are a supportive health and nutrition assistant.

        Write a short 2-3 sentence commentary about the user's baseline metrics.

        Rules:
        - Be respectful, warm, practical, and non-judgmental.
        - Do not body-shame.
        - Do not use derogatory, insulting, mocking, shaming, or fear-based language.
        - Avoid words such as "fat", "obese", "lazy", "ugly", "gross", or similar terms.
        - Do not make medical diagnoses.
        - Do not prescribe medical treatment.
        - Focus on healthy, sustainable next steps.
        - Output only the commentary text.
        """

        user_prompt = f"""
        User baseline:
        Age: {age}
        Biological sex for BMR calculation: {gender}
        BMI: {bmi:.1f}
        Estimated BMR: {int(bmr)} kcal/day
        """

        response = client.chat.completions.create(
            model="fugu",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )

        commentary = response.choices[0].message.content.strip()

        if not commentary or not is_commentary_safe(commentary):
            commentary = fallback

        st.session_state.ai_commentary = commentary
        st.session_state.commentary_signature = metrics_signature

        return commentary

    except Exception:
        st.session_state.ai_commentary = fallback
        st.session_state.commentary_signature = metrics_signature
        return fallback


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def round_to_step(value, step):
    return int(round(value / step) * step)


# ============================================================
# Reconcile Data Sources
# ============================================================

conflicts = reconcile_profile_sources()
initialize_selected_diets()

if conflicts:
    show_conflict_resolver(conflicts)

missing = profile_missing_fields()

if missing:
    show_missing_profile_form(missing)
    st.stop()


# ============================================================
# Math Calculations
# ============================================================

dob = st.session_state.user_dob
age = age_from_dob(dob)

height = float(st.session_state.user_height)
weight = float(st.session_state.user_weight)
gender = st.session_state.user_gender

height_in_meters = height / 100
bmi = weight / (height_in_meters ** 2)

# Mifflin-St Jeor BMR
if gender == "Male":
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
else:
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

# Determine BMI Status
if bmi < 18.5:
    bmi_status, bmi_color = "Underweight", "#3498db"
elif 18.5 <= bmi < 25:
    bmi_status, bmi_color = "Normal Weight", "#2ecc71"
elif 25 <= bmi < 30:
    bmi_status, bmi_color = "Overweight", "#e67e22"
else:
    bmi_status, bmi_color = "Obese", "#e74c3c"


# ============================================================
# Baseline Metric Displays
# ============================================================

st.markdown("### Baseline Metrics")

m1, m2, m3 = st.columns(3)
m1.metric("Age", f"{age} yrs")
m2.metric("BMI", f"{bmi:.1f}")
m3.metric("Est. BMR", f"{int(bmr)} kcal")

with st.expander("ℹ️ How to read your scores", expanded=False):
    st.markdown(
        f"""
        **Your BMI Status:** <span style='color:{bmi_color}; font-weight:bold;'>{bmi_status}</span>

        * **Body Mass Index (BMI):** Scales weight to height.
        * **Basal Metabolic Rate (BMR):** Your body burns **{int(bmr)} calories** daily at absolute rest.
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# AI Commentary Section
# ============================================================

st.markdown("---")
st.markdown("### AI Health Insight")

with st.spinner("Preparing insight..."):
    commentary = generate_ai_commentary(age, gender, bmi, bmr)

st.info(commentary)


# ============================================================
# Dietary Focus
# ============================================================

st.markdown("---")
st.markdown("### Dietary Focus")
st.caption("Tap multiple options to combine preferences and goals.")

for i in range(0, len(DIET_OPTIONS), 4):
    cols = st.columns(4)
    for j in range(4):
        if i + j < len(DIET_OPTIONS):
            opt = DIET_OPTIONS[i + j]
            label = opt["label"]
            is_selected = label in st.session_state.selected_diets
            
            # The correct syntax is :material/icon_name:
            icon_name = "check_circle" if is_selected else opt["icon"]
            display_icon = f":material/{icon_name}:"
            
            display_label = f"**{label}**" if is_selected else label

            with cols[j]:
                if st.button(
                    display_label, 
                    icon=display_icon, 
                    use_container_width=True, 
                    key=f"btn_{label}"
                ):
                    if label in st.session_state.selected_diets:
                        st.session_state.selected_diets.remove(label)
                    else:
                        st.session_state.selected_diets.append(label)

                    st.rerun()


# ============================================================
# Suggested Macro Targets
# ============================================================

st.markdown("---")
st.markdown("### Suggested Macro Targets")

# Basic TDEE baseline assumption
base_calories = int(bmr * 1.3)

# Default macro distribution
p_pct, c_pct, f_pct = 0.25, 0.45, 0.30

active_targets = st.session_state.selected_diets

if "Weight Loss" in active_targets:
    base_calories -= 400
    p_pct, c_pct, f_pct = 0.35, 0.35, 0.30

if "Gain Muscle" in active_targets:
    base_calories += 300
    p_pct, c_pct, f_pct = 0.30, 0.45, 0.25

if "Keto" in active_targets:
    p_pct, c_pct, f_pct = 0.20, 0.05, 0.75

# Keep calories inside slider range and aligned to step
base_calories = clamp(base_calories, 1000, 5000)
base_calories = round_to_step(base_calories, 50)
base_calories = clamp(base_calories, 1000, 5000)

# Convert percentages to grams
suggested_protein = int((base_calories * p_pct) / 4)
suggested_carbs = int((base_calories * c_pct) / 4)
suggested_fats = int((base_calories * f_pct) / 9)

# Keep slider defaults valid
suggested_protein = clamp(suggested_protein, 30, 300)
suggested_carbs = clamp(suggested_carbs, 0, 500)
suggested_fats = clamp(suggested_fats, 10, 200)

target_cal = st.slider(
    "Target Daily Calories (kcal)",
    min_value=1000,
    max_value=5000,
    value=base_calories,
    step=50,
)

col_p, col_c, col_f = st.columns(3)

with col_p:
    u_protein = st.slider(
        "Protein (g)",
        min_value=30,
        max_value=300,
        value=suggested_protein,
    )

with col_c:
    u_carbs = st.slider(
        "Carbs (g)",
        min_value=0,
        max_value=500,
        value=suggested_carbs,
    )

with col_f:
    u_fats = st.slider(
        "Fats (g)",
        min_value=10,
        max_value=200,
        value=suggested_fats,
    )

# Real-time total vs target tracker
current_total_kcal = int((u_protein * 4) + (u_carbs * 4) + (u_fats * 9))

st.caption(
    f"Sum of macros: **{current_total_kcal} kcal** / "
    f"Assigned target: **{target_cal} kcal**"
)


# ============================================================
# Save Profile
# ============================================================

st.markdown("---")

if st.button("Save Profile & Open Dashboard", use_container_width=True):
    st.session_state.diet_profile = (
        ", ".join(st.session_state.selected_diets)
        if st.session_state.selected_diets
        else "General"
    )

    st.session_state.target_calories = target_cal
    st.session_state.target_macros = {
        "protein": u_protein,
        "carbs": u_carbs,
        "fats": u_fats,
    }

    st.switch_page("views/main_menu.py")