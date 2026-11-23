import base64
import calendar
from datetime import date, datetime, time as dt_time, timedelta
import hashlib
import io
import math
import os
import random
import re
import sqlite3
import time
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

# -------------------- PAGE CONFIGURATION --------------------
st.set_page_config(
    page_title="KCC Smart AKTU Academic ERP",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "nav_tick" not in st.session_state:
    st.session_state.nav_tick = 0

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "kcc"

if "show_forgot_pw" not in st.session_state:
    st.session_state.show_forgot_pw = False

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "st_self_att_open" not in st.session_state:
    st.session_state.st_self_att_open = False

if "self_open_date_record" not in st.session_state:
    st.session_state.self_open_date_record = None

theme_mode = st.session_state.theme_mode
is_logged_in = (st.session_state.auth_user is not None)


def hash_password(plain_pw: str) -> str:
    return hashlib.sha256(plain_pw.strip().encode("utf-8")).hexdigest()


# -------------------- PERIOD & TIMETABLE DATA --------------------
PERIOD_SLOTS = [
    ("P1", "09:10", "10:10", "9:10–10:10"),
    ("P2", "10:10", "11:10", "10:10–11:10"),
    ("P3", "11:10", "12:10", "11:10–12:10"),
    ("P4", "12:10", "13:10", "12:10–1:10"),
    ("LUNCH", "13:10", "14:10", "1:10–2:10"),
    ("P5", "14:10", "15:10", "2:10–3:10"),
    ("P6", "15:10", "16:10", "3:10–4:10"),
    ("P7", "16:10", "17:00", "4:10–5:00"),
]

DAYS_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DAY_FULL_TO_SHORT = {
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Mon",
    "Sunday": "Mon",
}

SECTION_TIMETABLES = {
    "Section B-3": {
        "room": "Room no. 216",
        "Mon": [("COA", "Ms. Arya Devi"), ("DSTL", "Mr. Satyam"), ("Python", "Mr. Vishal"), ("DE", "Dr. Deepak Gupta"), ("LUNCH", "1:10–2:10"), ("COA", "Ms. Arya Devi"), ("DS", "Mr. Diwakar"), ("Free", "")],
        "Tue": [("Apt", "Mr. Sherpal"), ("Python", "Mr. Vishal"), ("DS", "Mr. Diwakar"), ("Free", ""), ("LUNCH", "1:10–2:10"), ("DSTL", "Mr. Satyam"), ("DE", "Dr. Deepak Gupta"), ("COA", "Ms. Arya Devi")],
        "Wed": [("DS", "Mr. Diwakar"), ("Apt", "Mr. Sherpal"), ("DSTL", "Mr. Satyam"), ("Free", ""), ("LUNCH", "1:10–2:10"), ("TC", "Ms. Reha"), ("Python", "Mr. Vishal"), ("DE", "Dr. Deepak Gupta")],
        "Thu": [("DE", "Dr. Deepak Gupta"), ("DSTL", "Mr. Satyam"), ("Python", "Mr. Vishal"), ("TC", "Ms. Reha"), ("LUNCH", "1:10–2:10"), ("COA", "Ms. Arya Devi"), ("DS", "Mr. Diwakar"), ("Free", "")],
        "Fri": [("COA", "Ms. Arya Devi"), ("DE", "Dr. Deepak Gupta"), ("DS", "Mr. Diwakar"), ("Free", ""), ("LUNCH", "1:10–2:10"), ("Python", "Mr. Vishal"), ("DSTL", "Mr. Satyam"), ("COA", "Ms. Arya Devi")],
    },
    "Section B-2": {
        "room": "Room no. 214",
        "Mon": [("DSTL", "Mr. Satyam"), ("Free", ""), ("COA", "Ms. Arya Devi"), ("Python", "Mr. Vishal"), ("LUNCH", "1:10–2:10"), ("DS", "Mr. Diwakar"), ("COA", "Ms. Arya Devi"), ("DE", "Dr. Deepak Gupta")],
        "Tue": [("Python", "Mr. Vishal"), ("DS", "Mr. Diwakar"), ("COA", "Ms. Arya Devi"), ("Apt", "Mr. Sherpal"), ("LUNCH", "1:10–2:10"), ("DSTL", "Mr. Satyam"), ("TC", "Ms. Reha"), ("Free", "")],
        "Wed": [("COA", "Ms. Arya Devi"), ("Python", "Mr. Vishal"), ("DS", "Mr. Diwakar"), ("Free", ""), ("LUNCH", "1:10–2:10"), ("DE", "Dr. Deepak Gupta"), ("DSTL", "Mr. Satyam"), ("COA", "Ms. Arya Devi")],
        "Thu": [("DS", "Mr. Diwakar"), ("DE", "Dr. Deepak Gupta"), ("DSTL", "Mr. Satyam"), ("Python", "Mr. Vishal"), ("LUNCH", "1:10–2:10"), ("Apt", "Mr. Sherpal"), ("TC", "Ms. Reha"), ("COA", "Ms. Arya Devi")],
        "Fri": [("DE", "Dr. Deepak Gupta"), ("DSTL", "Mr. Satyam"), ("Free", ""), ("COA", "Ms. Arya Devi"), ("LUNCH", "1:10–2:10"), ("DS", "Mr. Diwakar"), ("Python", "Mr. Vishal"), ("TC", "Ms. Reha")],
    },
    "Section B-4": {
        "room": "Room no. 218",
        "Mon": [("DE", "Dr. Deepak Gupta"), ("DS", "Mr. Diwakar"), ("COA", "Ms. Arya Devi"), ("Free", ""), ("LUNCH", "1:10–2:10"), ("TC", "Ms. Reha"), ("DSTL", "Mr. Satyam"), ("Python", "Mr. Vishal")],
        "Tue": [("DS", "Mr. Diwakar"), ("DSTL", "Mr. Satyam"), ("Apt", "Mr. Sherpal"), ("Python", "Mr. Vishal"), ("LUNCH", "1:10–2:10"), ("DE", "Dr. Deepak Gupta"), ("COA", "Ms. Arya Devi"), ("TC", "Ms. Reha")],
        "Wed": [("DSTL", "Mr. Satyam"), ("COA", "Ms. Arya Devi"), ("Python", "Mr. Vishal"), ("DS", "Mr. Diwakar"), ("LUNCH", "1:10–2:10"), ("COA", "Ms. Arya Devi"), ("DE", "Dr. Deepak Gupta"), ("Apt", "Mr. Sherpal")],
        "Thu": [("Python", "Mr. Vishal"), ("DS", "Mr. Diwakar"), ("TC", "Ms. Reha"), ("COA", "Ms. Arya Devi"), ("LUNCH", "1:10–2:10"), ("Python", "Mr. Vishal"), ("DSTL", "Mr. Satyam"), ("DE", "Dr. Deepak Gupta")],
        "Fri": [("DS", "Mr. Diwakar"), ("Apt", "Mr. Sherpal"), ("DSTL", "Mr. Satyam"), ("DE", "Dr. Deepak Gupta"), ("LUNCH", "1:10–2:10"), ("COA", "Ms. Arya Devi"), ("TC", "Ms. Reha"), ("Free", "")],
    },
    "Section B-6": {
        "room": "Room no. 220",
        "Mon": [("DS", "Mr. Diwakar"), ("Python", "Mr. Vishal"), ("DE", "Dr. Deepak Gupta"), ("Apt", "Mr. Sherpal"), ("LUNCH", "1:10–2:10"), ("DSTL", "Mr. Satyam"), ("TC", "Ms. Reha"), ("COA", "Ms. Arya Devi")],
        "Tue": [("DE", "Dr. Deepak Gupta"), ("DSTL", "Mr. Satyam"), ("DS", "Mr. Diwakar"), ("TC", "Ms. Reha"), ("LUNCH", "1:10–2:10"), ("Python", "Mr. Vishal"), ("COA", "Ms. Arya Devi"), ("Apt", "Mr. Sherpal")],
        "Wed": [("Python", "Mr. Vishal"), ("DE", "Dr. Deepak Gupta"), ("COA", "Ms. Arya Devi"), ("DSTL", "Mr. Satyam"), ("LUNCH", "1:10–2:10"), ("Python", "Mr. Vishal"), ("DS", "Mr. Diwakar"), ("Free", "")],
        "Thu": [("COA", "Ms. Arya Devi"), ("Apt", "Mr. Sherpal"), ("DS", "Mr. Diwakar"), ("DSTL", "Mr. Satyam"), ("LUNCH", "1:10–2:10"), ("DE", "Dr. Deepak Gupta"), ("Python", "Mr. Vishal"), ("TC", "Ms. Reha")],
        "Fri": [("COA", "Ms. Arya Devi"), ("DS", "Mr. Diwakar"), ("TC", "Ms. Reha"), ("Python", "Mr. Vishal"), ("LUNCH", "1:10–2:10"), ("DSTL", "Mr. Satyam"), ("DE", "Dr. Deepak Gupta"), ("Apt", "Mr. Sherpal")],
    },
}

FACULTY_TIMETABLES = {
    "FAC001": {
        "Mon": ["Free", "B6", "Free", "B2", "LUNCH", "Free", "B3", "B4"],
        "Tue": ["B3", "Free", "B6", "B4", "LUNCH", "Free", "Free", "Free"],
        "Wed": ["Free", "B2", "Free", "Free", "LUNCH", "B6", "B3", "Free"],
        "Thu": ["B6", "Free", "B2", "Free", "LUNCH", "B4", "Free", "Free"],
        "Fri": ["Free", "B4", "B3", "Free", "LUNCH", "B6", "B2", "Free"],
    },
    "FAC002": {
        "Mon": ["B6", "Free", "B4", "Free", "LUNCH", "B3", "B2", "Free"],
        "Tue": ["Free", "B4", "B2", "Free", "LUNCH", "Free", "B6", "B3"],
        "Wed": ["B2", "Free", "B6", "Free", "LUNCH", "B4", "Free", "B3"],
        "Thu": ["Free", "B3", "Free", "B4", "LUNCH", "B2", "B6", "Free"],
        "Fri": ["B6", "Free", "B2", "B3", "LUNCH", "B4", "Free", "Free"],
    },
    "FAC003": {
        "Mon": ["B2", "Free", "B3", "B6", "LUNCH", "Free", "B4", "Free"],
        "Tue": ["Free", "B6", "B4", "Free", "LUNCH", "B2", "Free", "Free"],
        "Wed": ["B4", "Free", "B3", "B6", "LUNCH", "B2", "Free", "Free"],
        "Thu": ["Free", "B2", "Free", "B3", "LUNCH", "B6", "B4", "Free"],
        "Fri": ["Free", "B4", "Free", "B2", "LUNCH", "Free", "B6", "B3"],
    },
}


def get_now_ist():
    try:
        return datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        return datetime.now()


def get_active_period_code(now_dt):
    curr_t = now_dt.time()
    for p_code, start_s, end_s, _ in PERIOD_SLOTS:
        sh, sm = map(int, start_s.split(":"))
        eh, em = map(int, end_s.split(":"))
        if dt_time(sh, sm) <= curr_t < dt_time(eh, em):
            return p_code
    return None


# -------------------- STUDENT RESULTS DATA --------------------
DEMO_RESULTS = {
    "2504920100346": {
        "name": "Manas Srivastav",
        "roll_no": "2504920100346",
        "branch": "CSE",
        "result": "PASS",
        "cgpa": 8.03,
        "semesters": {
            "Semester 1": {
                "sgpa": 8.11,
                "subjects": [
                    {"subject": "Engineering Physics", "credits": 4, "marks": 78, "grade": "A"},
                    {"subject": "Engineering Mathematics-I", "credits": 4, "marks": 71, "grade": "A"},
                    {"subject": "Fundamentals of Electrical Engg", "credits": 4, "marks": 66, "grade": "B+"},
                    {"subject": "Programming for Problem Solving", "credits": 4, "marks": 84, "grade": "A+"},
                    {"subject": "Professional Communication", "credits": 2, "marks": 88, "grade": "A+"},
                ],
            },
            "Semester 2": {
                "sgpa": 7.94,
                "subjects": [
                    {"subject": "Engineering Chemistry", "credits": 4, "marks": 69, "grade": "B+"},
                    {"subject": "Engineering Mathematics-II", "credits": 4, "marks": 62, "grade": "B+"},
                    {"subject": "Fundamentals of Electronics Engg", "credits": 4, "marks": 75, "grade": "A"},
                    {"subject": "Environment & Ecology", "credits": 2, "marks": 91, "grade": "O"},
                    {"subject": "Engineering Graphics", "credits": 3, "marks": 80, "grade": "A+"},
                ],
            },
        },
    },
    "2504920100201": {
        "name": "Ananya Singh",
        "roll_no": "2504920100201",
        "branch": "CSE",
        "result": "PASS",
        "cgpa": 9.20,
        "semesters": {
            "Semester 1": {
                "sgpa": 9.33,
                "subjects": [
                    {"subject": "Engineering Physics", "credits": 4, "marks": 92, "grade": "O"},
                    {"subject": "Engineering Mathematics-I", "credits": 4, "marks": 86, "grade": "A+"},
                    {"subject": "Fundamentals of Electrical Engg", "credits": 4, "marks": 81, "grade": "A+"},
                    {"subject": "Programming for Problem Solving", "credits": 4, "marks": 95, "grade": "O"},
                    {"subject": "Professional Communication", "credits": 2, "marks": 79, "grade": "A"},
                ],
            },
            "Semester 2": {
                "sgpa": 9.06,
                "subjects": [
                    {"subject": "Engineering Chemistry", "credits": 4, "marks": 88, "grade": "A+"},
                    {"subject": "Engineering Mathematics-II", "credits": 4, "marks": 90, "grade": "O"},
                    {"subject": "Fundamentals of Electronics Engg", "credits": 4, "marks": 83, "grade": "A+"},
                    {"subject": "Environment & Ecology", "credits": 2, "marks": 85, "grade": "A+"},
                    {"subject": "Engineering Graphics", "credits": 3, "marks": 72, "grade": "A"},
                ],
            },
        },
    },
}

LETTER_GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "P": 4,
    "F": 0,
}


# -------------------- THEME PALETTE --------------------
if theme_mode == "dark":
    if not is_logged_in:
        bg_css = """
            background-color: #07131D !important;
            background-image:
                radial-gradient(ellipse at 18% 22%, rgba(14, 165, 233, 0.36) 0%, transparent 52%),
                radial-gradient(ellipse at 82% 75%, rgba(20, 184, 166, 0.32) 0%, transparent 54%),
                radial-gradient(ellipse at 55% 45%, rgba(56, 189, 248, 0.18) 0%, transparent 60%),
                linear-gradient(135deg, #061019 0%, #0C2233 50%, #071622 100%) !important;
        """
    else:
        bg_css = """
            background-color: #050D14 !important;
            background-image:
                radial-gradient(ellipse at 18% 22%, rgba(14, 165, 233, 0.22) 0%, transparent 52%),
                radial-gradient(ellipse at 82% 75%, rgba(20, 184, 166, 0.18) 0%, transparent 54%),
                radial-gradient(ellipse at 55% 45%, rgba(56, 189, 248, 0.11) 0%, transparent 60%),
                linear-gradient(135deg, #040B11 0%, #081724 50%, #050F18 100%) !important;
        """
    sidebar_bg = "#071420"
    text_main = "#F1F5F9"
    text_muted = "#9FB3C8"
    card_bg = "rgba(11, 26, 40, 0.88)"
    safe_card_bg = "rgba(16, 185, 129, 0.15)"
    safe_card_border = "rgba(52, 211, 153, 0.55)"
    card_border = "rgba(56, 189, 248, 0.32)"
    btn_bg = "#0E2235"
    btn_text = "#F1F5F9"
    btn_hover_bg = "#163552"
    btn_hover_border = "#38BDF8"
    btn_hover_shadow = "rgba(14, 165, 233, 0.42)"
    active_pill_grad = "linear-gradient(135deg, #0284C7 0%, #0D9488 100%)"
    active_pill_border = "#7DD3FC"
    active_pill_shadow = "0 0 22px rgba(56, 189, 248, 0.65), 0 8px 24px rgba(13, 148, 136, 0.48)"
    accent_color = "#38BDF8"
    input_bg = "#0A1B2B"
    code_bg = "rgba(14, 165, 233, 0.20)"
    code_text = "#7DD3FC"
    drawer_bg = "#0A1B2B"
    cal_card_bg = "#0D2236"
    cal_neutral_bg = "rgba(148, 163, 184, 0.12)"
    cal_neutral_txt = "#94A3B8"
    bar_track = "rgba(255, 255, 255, 0.12)"
    delta_bg = "rgba(16, 185, 129, 0.18)"
    delta_txt = "#6EE7B7"
    table_bg = "#091826"
    table_alt_bg = "#0E2235"
    table_hdr_bg = "#0F2942"
    alert_bg = "#0B1E30"
    df_filter = "none"
    is_light_ui = False

elif theme_mode == "light":
    if not is_logged_in:
        bg_css = """
            background-color: #D2E0E8 !important;
            background-image:
                radial-gradient(ellipse at 18% 22%, rgba(14, 165, 233, 0.28) 0%, transparent 52%),
                radial-gradient(ellipse at 82% 75%, rgba(13, 148, 136, 0.25) 0%, transparent 54%),
                radial-gradient(ellipse at 50% 50%, rgba(226, 236, 242, 0.65) 0%, transparent 65%),
                linear-gradient(135deg, #CEDCE5 0%, #DAE6ED 50%, #C8D8E2 100%) !important;
        """
    else:
        bg_css = """
            background-color: #C0D0DA !important;
            background-image:
                radial-gradient(ellipse at 18% 22%, rgba(14, 165, 233, 0.20) 0%, transparent 52%),
                radial-gradient(ellipse at 82% 75%, rgba(13, 148, 136, 0.18) 0%, transparent 54%),
                radial-gradient(ellipse at 50% 50%, rgba(203, 217, 226, 0.55) 0%, transparent 65%),
                linear-gradient(135deg, #BCCCD6 0%, #C8D7E0 50%, #B6C7D2 100%) !important;
        """
    sidebar_bg = "rgba(210, 223, 232, 0.95)"
    text_main = "#0F172A"
    text_muted = "#334155"
    card_bg = "rgba(241, 246, 249, 0.90)"
    safe_card_bg = "rgba(220, 252, 231, 0.88)"
    safe_card_border = "rgba(22, 163, 74, 0.45)"
    card_border = "rgba(100, 116, 139, 0.38)"
    btn_bg = "#F4F8FB"
    btn_text = "#0F172A"
    btn_hover_bg = "#E0F2FE"
    btn_hover_border = "#0284C7"
    btn_hover_shadow = "rgba(14, 165, 233, 0.36)"
    active_pill_grad = "linear-gradient(135deg, #0284C7 0%, #0D9488 100%)"
    active_pill_border = "#38BDF8"
    active_pill_shadow = "0 0 20px rgba(2, 132, 199, 0.45), 0 8px 22px rgba(13, 148, 136, 0.32)"
    accent_color = "#0284C7"
    input_bg = "#F4F8FB"
    code_bg = "#CBD5E1"
    code_text = "#0F172A"
    drawer_bg = "#F4F8FB"
    cal_card_bg = "#F4F8FB"
    cal_neutral_bg = "rgba(203, 213, 225, 0.65)"
    cal_neutral_txt = "#475569"
    bar_track = "rgba(15, 23, 42, 0.14)"
    delta_bg = "rgba(22, 163, 74, 0.14)"
    delta_txt = "#15803D"
    table_bg = "#F8FAFC"
    table_alt_bg = "#EEF2F6"
    table_hdr_bg = "#E2E8F0"
    alert_bg = "#E0F2FE"
    df_filter = "none"
    is_light_ui = True

else:
    if not is_logged_in:
        bg_css = """
            background-color: #FAF6F6 !important;
            background-image:
                radial-gradient(ellipse at 16% 20%, rgba(166, 28, 32, 0.14) 0%, transparent 52%),
                radial-gradient(ellipse at 85% 78%, rgba(185, 28, 28, 0.11) 0%, transparent 54%),
                linear-gradient(135deg, #FFFFFF 0%, #FDF2F2 50%, #F9EBEB 100%) !important;
        """
    else:
        bg_css = """
            background-color: #EFE8E8 !important;
            background-image:
                radial-gradient(ellipse at 16% 20%, rgba(166, 28, 32, 0.10) 0%, transparent 52%),
                radial-gradient(ellipse at 85% 78%, rgba(153, 27, 27, 0.08) 0%, transparent 54%),
                linear-gradient(135deg, #F3ECEC 0%, #ECE2E2 50%, #E7DCDC 100%) !important;
        """
    sidebar_bg = "rgba(255, 250, 250, 0.96)"
    text_main = "#1F1919"
    text_muted = "#574949"
    card_bg = "rgba(255, 255, 255, 0.94)"
    safe_card_bg = "rgba(240, 253, 244, 0.94)"
    safe_card_border = "rgba(22, 163, 74, 0.42)"
    card_border = "rgba(166, 28, 32, 0.28)"
    btn_bg = "#FFFFFF"
    btn_text = "#8B171B"
    btn_hover_bg = "#FDE8E8"
    btn_hover_border = "#A61C20"
    btn_hover_shadow = "rgba(166, 28, 32, 0.34)"
    active_pill_grad = "linear-gradient(135deg, #B91C1C 0%, #7F1316 100%)"
    active_pill_border = "#F87171"
    active_pill_shadow = "0 0 20px rgba(185, 28, 28, 0.48), 0 8px 22px rgba(127, 19, 22, 0.36)"
    accent_color = "#A61C20"
    input_bg = "#FFFFFF"
    code_bg = "#FEE2E2"
    code_text = "#991B1B"
    drawer_bg = "#FFFFFF"
    cal_card_bg = "#FFFFFF"
    cal_neutral_bg = "rgba(229, 215, 215, 0.55)"
    cal_neutral_txt = "#6B5B5B"
    bar_track = "rgba(127, 29, 29, 0.12)"
    delta_bg = "rgba(22, 163, 74, 0.12)"
    delta_txt = "#15803D"
    table_bg = "#FFFFFF"
    table_alt_bg = "#FDF6F6"
    table_hdr_bg = "#F9EBEB"
    alert_bg = "#FEF2F2"
    df_filter = "none"
    is_light_ui = True

st.markdown(f"""
<style>
:root {{
    --btn-bg: {btn_bg};
    --btn-text: {btn_text};
    --btn-hover-bg: {btn_hover_bg};
    --accent-color: {accent_color};
    --drawer-bg: {drawer_bg};
    --text-main: {text_main};
    --input-bg: {input_bg};
    --card-border: {card_border};
}}

@keyframes oceanMistFlow {{
    0% {{ background-position: 0% 20%; }}
    50% {{ background-position: 100% 80%; }}
    100% {{ background-position: 0% 20%; }}
}}

@keyframes activeClassBlinkRed {{
    0%, 100% {{
        border-color: #FF1E27 !important;
        box-shadow: 0 0 18px rgba(255, 30, 39, 0.95), 0 0 8px rgba(239, 68, 68, 0.85) inset !important;
    }}
    50% {{
        border-color: rgba(255, 30, 39, 0.25) !important;
        box-shadow: 0 0 4px rgba(255, 30, 39, 0.22) !important;
    }}
}}

html body .stApp {{
    {bg_css}
    background-size: 240% 240% !important;
    animation: oceanMistFlow 16s ease-in-out infinite !important;
    color: {text_main} !important;
}}

[data-testid="stHeader"] {{
    background: transparent !important;
}}

[data-testid="stToolbar"] {{
    right: 1rem !important;
    top: 0.35rem !important;
    z-index: 999 !important;
}}

html body .stApp [data-testid="stAlert"],
html body .stApp [data-testid="stNotification"],
html body .stApp .stAlert > div {{
    background: {alert_bg} !important;
    background-color: {alert_bg} !important;
    color: {text_main} !important;
    border: 1px solid {card_border} !important;
    border-radius: 12px !important;
}}

html body .stApp [data-testid="stAlert"] *,
html body .stApp [data-testid="stNotification"] * {{
    color: {text_main} !important;
}}

[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarNavCollapseButton"] button,
[data-testid="collapsedControl"] button {{
    background: {btn_bg} !important;
    background-color: {btn_bg} !important;
    color: {text_main} !important;
    border: 1px solid {card_border} !important;
    border-radius: 999px !important;
}}

[data-testid="stSidebarCollapseButton"] button *,
[data-testid="stSidebarNavCollapseButton"] button *,
[data-testid="collapsedControl"] button * {{
    color: {text_main} !important;
    fill: {text_main} !important;
}}

[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    background-color: {sidebar_bg} !important;
    backdrop-filter: blur(16px) !important;
    border-right: 1px solid {card_border} !important;
}}

html body .stApp h1, html body .stApp h2, html body .stApp h3,
html body .stApp h4, html body .stApp h5, html body .stApp label,
html body .stApp p, html body .stApp li, html body .stApp span,
html body .stApp [data-testid="stMarkdownContainer"],
html body .stApp [data-testid="stMetricValue"],
html body .stApp [data-testid="stMetricLabel"],
html body .stApp [data-baseweb="radio"] label div,
html body .stApp [data-baseweb="checkbox"] label div {{
    color: {text_main} !important;
}}

html body .stApp [data-testid="stMetricDelta"],
html body .stApp [data-testid="stMetricDelta"] > div {{
    background: {delta_bg} !important;
    background-color: {delta_bg} !important;
    color: {delta_txt} !important;
    border-radius: 999px !important;
    padding: 2px 10px !important;
    font-weight: 700 !important;
}}

html body .stApp [data-testid="stMetricDelta"] *,
html body .stApp [data-testid="stMetricDelta"] svg {{
    color: {delta_txt} !important;
    fill: {delta_txt} !important;
}}

html body .stApp [data-testid="stCaptionContainer"],
html body .stApp [data-testid="stCaptionContainer"] p {{
    color: {text_muted} !important;
    opacity: 1 !important;
}}

html body .stApp code {{
    background: {code_bg} !important;
    color: {code_text} !important;
    padding: 2px 7px !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
}}

html body .stApp .block-container {{
    max-width: 98% !important;
    padding-top: 3.5rem !important;
    padding-left: 1.8rem !important;
    padding-right: 1.8rem !important;
    padding-bottom: 2rem !important;
}}

.stButton button, .stFormSubmitButton button,
.stDownloadButton button, [data-testid="stDownloadButton"] button {{
    border-radius: 999px !important;
    border: 1px solid {card_border} !important;
    padding: 0.52rem 1.3rem !important;
    font-weight: 600 !important;
    background: {btn_bg} !important;
    background-color: {btn_bg} !important;
    color: {btn_text} !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.14) !important;
    transition: background 0.16s ease, background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease !important;
}}

.stButton button p, .stFormSubmitButton button p,
.stDownloadButton button p, [data-testid="stDownloadButton"] button p,
.stDownloadButton button span, [data-testid="stDownloadButton"] button span {{
    color: {btn_text} !important;
}}

.stButton button:hover, .stFormSubmitButton button:hover,
.stDownloadButton button:hover, [data-testid="stDownloadButton"] button:hover {{
    background: {btn_hover_bg} !important;
    background-color: {btn_hover_bg} !important;
    border-color: {btn_hover_border} !important;
    box-shadow: 0 8px 20px {btn_hover_shadow} !important;
}}

html body [data-testid="stPopover"],
html body [data-baseweb="popover"],
html body [data-baseweb="popover"] > div {{
    width: 100% !important;
    display: block !important;
}}

html body [data-testid="stPopover"] button,
html body [data-baseweb="popover"] button,
html body button[kind="secondary"],
html body [data-testid="stBaseButton-secondary"] {{
    width: 100% !important;
    min-height: 44px !important;
    border-radius: 999px !important;
    border: 1.5px solid var(--accent-color, #A61C20) !important;
    padding: 0.48rem 1.15rem !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    outline: none !important;
    position: relative !important;
    z-index: 1 !important;
}}

html body [data-testid="stPopover"] button {{
    background: var(--btn-bg) !important;
    background-color: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.14) !important;
    transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
}}

html body [data-testid="stPopover"] button:hover,
html body [data-testid="stPopover"] button:focus,
html body [data-testid="stPopover"] button:focus-visible,
html body [data-testid="stPopover"] button:active,
html body [data-baseweb="popover"] button:hover,
html body [data-baseweb="popover"] button:focus,
html body [data-baseweb="popover"] button:active,
html body [data-baseweb="popover"] button[aria-expanded="true"],
html body button[kind="secondary"]:hover,
html body button[kind="secondary"]:focus,
html body button[kind="secondary"]:active,
html body [data-testid="stBaseButton-secondary"]:hover,
html body [data-testid="stBaseButton-secondary"]:focus,
html body [data-testid="stBaseButton-secondary"]:active {{
    background: var(--btn-hover-bg) !important;
    background-color: var(--btn-hover-bg) !important;
    border-color: var(--accent-color, #A61C20) !important;
    color: var(--btn-text) !important;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18) !important;
}}

html body [data-testid="stPopover"] button *,
html body [data-baseweb="popover"] button * {{
    background: transparent !important;
    background-color: transparent !important;
    color: var(--btn-text) !important;
    fill: var(--btn-text) !important;
    pointer-events: none !important;
}}

html body [data-testid="stPopoverBody"],
html body [data-testid="stPopoverBody"] > div,
html body [data-testid="stPopoverBody"] [data-testid="stVerticalBlock"],
html body [data-baseweb="popover"] [data-baseweb="menu"] {{
    background: var(--drawer-bg) !important;
    background-color: var(--drawer-bg) !important;
    color: var(--text-main) !important;
}}

html body [data-testid="stPopoverBody"] {{
    border: 1.5px solid var(--accent-color, #A61C20) !important;
    border-radius: 16px !important;
    padding: 12px !important;
    box-shadow: 0 14px 32px rgba(0, 0, 0, 0.28) !important;
}}

html body [data-testid="stPopoverBody"] button {{
    width: 100% !important;
    justify-content: flex-start !important;
    border-radius: 12px !important;
    margin-bottom: 4px !important;
    padding: 0.55rem 1rem !important;
    background: var(--drawer-bg) !important;
    background-color: var(--drawer-bg) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--card-border) !important;
    box-shadow: none !important;
    transform: none !important;
}}

html body [data-testid="stPopoverBody"] button * {{
    color: var(--text-main) !important;
}}

html body [data-testid="stPopoverBody"] button:hover {{
    background: var(--btn-hover-bg) !important;
    background-color: var(--btn-hover-bg) !important;
    border-color: var(--accent-color, #A61C20) !important;
}}

[data-testid="stElementContainer"]:has(.tag-present),
[data-testid="stElementContainer"]:has(.tag-absent),
[data-testid="stElementContainer"]:has(.tag-dates),
[data-testid="stElementContainer"]:has(.nav-pill-tag),
[data-testid="stElementContainer"]:has(.nav-active),
[data-testid="stElementContainer"]:has(.theme-btn-tag) {{
    display: none !important;
}}

[data-testid="stColumn"]:has(.nav-pill-tag) button {{
    min-height: 54px !important;
    padding: 14px 20px !important;
    margin-bottom: 10px !important;
    outline: none !important;
}}

[data-testid="stColumn"]:has(.nav-pill-tag) button p {{
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.2px !important;
}}

[data-testid="stColumn"]:has(.nav-pill-tag):not(:has(.nav-active)) button:focus:not(:hover),
[data-testid="stColumn"]:has(.nav-pill-tag):not(:has(.nav-active)) button:active:not(:hover) {{
    background: {btn_bg} !important;
    background-color: {btn_bg} !important;
    border-color: {card_border} !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.14) !important;
}}

[data-testid="stColumn"]:has(.nav-pill-tag):not(:has(.nav-active)) button:focus:not(:hover) p,
[data-testid="stColumn"]:has(.nav-pill-tag):not(:has(.nav-active)) button:active:not(:hover) p {{
    color: {btn_text} !important;
}}

[data-testid="stColumn"]:has(.nav-pill-tag):not(:has(.nav-active)) button:hover {{
    background: {btn_hover_bg} !important;
    background-color: {btn_hover_bg} !important;
    border-color: {btn_hover_border} !important;
    box-shadow: 0 0 16px {btn_hover_shadow} !important;
}}

[data-testid="stColumn"]:has(.nav-active) button,
[data-testid="stColumn"]:has(.nav-active) button:hover,
[data-testid="stColumn"]:has(.nav-active) button:focus,
[data-testid="stColumn"]:has(.nav-active) button:active {{
    background: {active_pill_grad} !important;
    border-color: {active_pill_border} !important;
    box-shadow: {active_pill_shadow} !important;
}}

[data-testid="stColumn"]:has(.nav-active) button p,
[data-testid="stColumn"]:has(.nav-active) button:hover p,
[data-testid="stColumn"]:has(.nav-active) button:focus p,
[data-testid="stColumn"]:has(.nav-active) button:active p {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}}

[data-testid="stColumn"]:has(.tag-present) button:hover {{
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.28) 0%, rgba(14, 165, 233, 0.18) 100%) !important;
    border-color: rgba(34, 197, 94, 0.65) !important;
    box-shadow: 0 10px 22px rgba(34, 197, 94, 0.42) !important;
}}

[data-testid="stColumn"]:has(.tag-absent) button:hover {{
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.28) 0%, rgba(166, 28, 32, 0.18) 100%) !important;
    border-color: rgba(239, 68, 68, 0.65) !important;
    box-shadow: 0 10px 22px rgba(239, 68, 68, 0.42) !important;
}}

[data-testid="stColumn"]:has(.tag-dates) button:hover {{
    background: {btn_hover_bg} !important;
    border-color: {btn_hover_border} !important;
    box-shadow: 0 10px 22px {btn_hover_shadow} !important;
}}

html body .stApp [data-baseweb="select"] > div,
html body .stApp [data-baseweb="input"] > div,
html body .stApp [data-baseweb="base-input"],
html body .stApp [data-testid="stTextInput"] > div > div,
html body .stApp [data-testid="stTextInputRootElement"] > div,
html body .stApp [data-testid="stDateInput"] > div > div,
html body .stApp [data-testid="stDateInput"] input,
html body .stApp [data-testid="stNumberInput"] > div > div,
html body .stApp [data-testid="stNumberInput"] input,
html body .stApp [data-testid="stNumberInput"] button,
html body .stApp [data-testid="stExpander"] details,
html body .stApp [data-testid="stExpander"] summary,
html body [data-testid="stPopoverBody"] [data-baseweb="input"] > div,
html body [data-testid="stPopoverBody"] [data-testid="stTextInputRootElement"] > div {{
    border-radius: 14px !important;
    border: 1px solid {card_border} !important;
    background: {input_bg} !important;
    background-color: {input_bg} !important;
    color: {text_main} !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.14) !important;
}}

html body .stApp [data-baseweb="select"] span,
html body .stApp [data-baseweb="select"] div,
html body .stApp [data-baseweb="input"] input,
html body .stApp [data-testid="stTextInput"] input,
html body .stApp [data-testid="stTextInputRootElement"] input,
html body .stApp [data-testid="stTextInputRootElement"] button,
html body .stApp [data-testid="stDateInput"] input,
html body .stApp [data-testid="stDateInput"] svg,
html body .stApp [data-testid="stNumberInput"] input,
html body .stApp [data-testid="stNumberInput"] button svg,
html body .stApp [data-testid="stExpander"] summary,
html body .stApp [data-testid="stExpander"] summary p,
html body .stApp [data-testid="stExpander"] summary svg,
html body [data-testid="stPopoverBody"] input {{
    background-color: transparent !important;
    color: {text_main} !important;
    -webkit-text-fill-color: {text_main} !important;
    fill: {text_main} !important;
}}

html body .stApp input::placeholder,
html body .stApp textarea::placeholder {{
    color: {text_muted} !important;
    -webkit-text-fill-color: {text_muted} !important;
    opacity: 0.85 !important;
}}

[data-baseweb="popover"] ul,
[role="listbox"] {{
    background: {drawer_bg} !important;
    background-color: {drawer_bg} !important;
    border: 1px solid {card_border} !important;
}}

[role="option"] {{
    background-color: {drawer_bg} !important;
    color: {text_main} !important;
}}

.erp-table-wrap {{
    width: 100%;
    overflow-x: auto;
    border-radius: 14px;
    border: 1px solid {card_border};
    background: {table_bg} !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.16);
    margin-top: 8px;
    margin-bottom: 12px;
}}

table.erp-styled-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
    color: {text_main} !important;
}}

table.erp-styled-table thead th {{
    background: {table_hdr_bg} !important;
    color: {text_main} !important;
    font-weight: 700;
    text-align: left;
    padding: 11px 14px;
    border-bottom: 1px solid {card_border};
}}

table.erp-styled-table tbody tr:nth-child(odd) {{
    background: {table_bg} !important;
}}

table.erp-styled-table tbody tr:nth-child(even) {{
    background: {table_alt_bg} !important;
}}

table.erp-styled-table tbody td {{
    padding: 10px 14px;
    border-bottom: 1px solid {card_border};
    color: {text_main} !important;
}}

[data-testid="stDataFrame"] {{
    filter: {df_filter};
    border-radius: 14px !important;
    overflow: hidden !important;
}}

.tt-grid-wrap {{
    width: 100%;
    overflow-x: auto;
    border-radius: 16px;
    border: 1.5px solid {card_border};
    background: {table_bg} !important;
    padding: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
}}

table.tt-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 6px;
    font-size: 0.88rem;
}}

table.tt-table th {{
    background: {table_hdr_bg} !important;
    color: {text_main} !important;
    padding: 10px 8px;
    border-radius: 10px;
    text-align: center;
    font-weight: 700;
    border: 1px solid {card_border};
}}

table.tt-table td.tt-day-cell {{
    background: {table_hdr_bg} !important;
    color: {accent_color} !important;
    font-weight: 800;
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid {card_border};
}}

table.tt-table td.tt-slot {{
    background: {table_alt_bg} !important;
    color: {text_main} !important;
    border-radius: 10px;
    padding: 9px 8px;
    text-align: center;
    vertical-align: middle;
    border: 1.5px solid {card_border};
    min-width: 105px;
}}

table.tt-table td.tt-slot-lunch {{
    background: rgba(245, 158, 11, 0.14) !important;
    border: 1.5px dashed rgba(245, 158, 11, 0.65) !important;
    border-radius: 10px;
    padding: 9px 6px;
    text-align: center;
    font-weight: 700;
}}

table.tt-table td.tt-slot-free {{
    opacity: 0.72;
}}

table.tt-table td.tt-live-blink {{
    background: rgba(239, 68, 68, 0.18) !important;
    border: 2.5px solid #FF1E27 !important;
    animation: activeClassBlinkRed 1.05s infinite !important;
}}

.att-card-green {{
    width: 100%;
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 6px;
    background: {safe_card_bg} !important;
    border: 1.5px solid {safe_card_border} !important;
    backdrop-filter: blur(12px);
    box-sizing: border-box;
    box-shadow: 0 6px 20px rgba(34, 197, 94, 0.14);
    transition: box-shadow 0.2s ease, background-color 0.2s ease, border-color 0.2s ease !important;
}}

.att-card-green:hover {{
    background: rgba(34, 197, 94, 0.24) !important;
    border-color: rgba(74, 222, 128, 0.85) !important;
    box-shadow: 0 12px 32px rgba(34, 197, 94, 0.55), 0 0 20px rgba(34, 197, 94, 0.35) !important;
}}

.att-card-red {{
    width: 100%;
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 6px;
    background: {card_bg} !important;
    border: 1.5px solid {card_border} !important;
    backdrop-filter: blur(12px);
    box-sizing: border-box;
    transition: box-shadow 0.2s ease, background-color 0.2s ease, border-color 0.2s ease !important;
}}

.att-card-red:hover {{
    background: rgba(239, 68, 68, 0.22) !important;
    border-color: rgba(239, 68, 68, 0.78) !important;
    box-shadow: 0 12px 32px rgba(239, 68, 68, 0.48), 0 0 18px rgba(239, 68, 68, 0.30) !important;
}}

.self-att-panel {{
    border-radius: 18px;
    padding: 18px 22px;
    margin: 14px 0 18px 0;
    background: {card_bg} !important;
    border: 1.5px solid {accent_color} !important;
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
}}

.bar-track-bg {{
    position: relative;
    width: 100%;
    height: 28px;
    background: {bar_track};
    border-radius: 999px;
    overflow: hidden;
}}

.login-hero {{
    background: {card_bg};
    border: 1.5px solid {card_border};
    backdrop-filter: blur(14px);
    border-radius: 20px;
    padding: 22px 26px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}}

.cal-drawer-wrapper {{
    border-radius: 18px;
    padding: 18px 20px;
    margin-top: 8px;
    margin-bottom: 14px;
    background: {drawer_bg} !important;
    border: 1.5px solid {card_border};
    backdrop-filter: blur(14px);
    box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
}}

.cal-months-flex {{
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    margin-top: 12px;
}}

.cal-month-card {{
    flex: 1 1 300px;
    max-width: 380px;
    background: {cal_card_bg} !important;
    border: 1px solid {card_border};
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
}}

.cal-month-title {{
    text-align: center;
    font-weight: 700;
    font-size: 1.02rem;
    color: {text_main} !important;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid {card_border};
}}

.cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    text-align: center;
}}

.cal-weekday {{
    font-size: 0.75rem;
    font-weight: 700;
    color: {text_muted} !important;
    padding-bottom: 4px;
}}

.cal-day-empty {{ height: 36px; }}

.cal-day-neutral {{
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 9px;
    font-size: 0.85rem;
    color: {cal_neutral_txt} !important;
    background: {cal_neutral_bg} !important;
}}

.cal-day-present {{
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 9px;
    font-size: 0.88rem;
    font-weight: 800;
    color: #FFFFFF !important;
    background: linear-gradient(135deg, #16A34A, #22C55E);
    box-shadow: 0 3px 10px rgba(34, 197, 94, 0.42);
}}

.cal-day-absent {{
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 9px;
    font-size: 0.88rem;
    font-weight: 800;
    color: #FFFFFF !important;
    background: linear-gradient(135deg, #DC2626, #EF4444);
    box-shadow: 0 3px 10px rgba(239, 68, 68, 0.42);
}}
</style>
""", unsafe_allow_html=True)

DB_NAME = "aktu_manager.db"

GRADE_POINTS = {
    "A+ (90-100)": 10,
    "A (80-89)": 9,
    "B+ (70-79)": 8,
    "B (60-69)": 7,
    "C (50-59)": 6,
    "D (45-49)": 5,
    "F (Below 45)": 0,
}

DOODLES = {
    "🐱 Cyber Cat (Cool Shades)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#FFE8A3"/><polygon points="26,48 34,18 52,38" fill="#FF9F43" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><polygon points="94,48 86,18 68,38" fill="#FF9F43" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><circle cx="60" cy="66" r="34" fill="#FFBE76" stroke="#2D3436" stroke-width="3"/><rect x="33" y="54" width="23" height="14" rx="4" fill="#1E272E"/><rect x="64" y="54" width="23" height="14" rx="4" fill="#1E272E"/><line x1="56" y1="60" x2="64" y2="60" stroke="#1E272E" stroke-width="3"/><line x1="37" y1="57" x2="43" y2="65" stroke="#00D2D3" stroke-width="2.5"/><line x1="68" y1="57" x2="74" y2="65" stroke="#00D2D3" stroke-width="2.5"/><polygon points="56,74 64,74 60,79" fill="#FF6B81"/><path d="M52,83 Q60,90 68,83" fill="none" stroke="#2D3436" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "🤖 Chill Robo (Coder Bot)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#DFF9FB"/><line x1="60" y1="16" x2="60" y2="30" stroke="#2D3436" stroke-width="3.5"/><circle cx="60" cy="14" r="5" fill="#FF4757"/><rect x="28" y="30" width="64" height="56" rx="14" fill="#70A1FF" stroke="#2D3436" stroke-width="3"/><rect x="36" y="42" width="48" height="24" rx="8" fill="#1E272E"/><circle cx="48" cy="54" r="5" fill="#2ED573"/><circle cx="72" cy="54" r="5" fill="#2ED573"/><rect x="46" y="73" width="28" height="6" rx="3" fill="#FFFFFF"/><rect x="19" y="48" width="9" height="20" rx="4" fill="#FFA502" stroke="#2D3436" stroke-width="2.5"/><rect x="92" y="48" width="9" height="20" rx="4" fill="#FFA502" stroke="#2D3436" stroke-width="2.5"/></svg>',
    "🐼 Study Panda (Geek Mode)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#E8F8F5"/><circle cx="32" cy="34" r="13" fill="#2D3436"/><circle cx="88" cy="34" r="13" fill="#2D3436"/><circle cx="60" cy="64" r="35" fill="#FFFFFF" stroke="#2D3436" stroke-width="3"/><ellipse cx="45" cy="60" rx="10" ry="8" fill="#2D3436"/><ellipse cx="75" cy="60" rx="10" ry="8" fill="#2D3436"/><circle cx="45" cy="60" r="12" fill="none" stroke="#0984E3" stroke-width="3"/><circle cx="75" cy="60" r="12" fill="none" stroke="#0984E3" stroke-width="3"/><line x1="57" y1="60" x2="63" y2="60" stroke="#0984E3" stroke-width="3"/><circle cx="46" cy="59" r="3" fill="#FFFFFF"/><circle cx="76" cy="59" r="3" fill="#FFFFFF"/><ellipse cx="60" cy="73" rx="5" ry="3.5" fill="#2D3436"/><path d="M53,81 Q60,87 67,81" fill="none" stroke="#2D3436" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "🦊 Hoodie Fox (Dev Vibes)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#FAD390"/><polygon points="25,52 30,18 52,38" fill="#E55039" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><polygon points="95,52 90,18 68,38" fill="#E55039" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><path d="M26,62 Q60,24 94,62 Q86,96 60,98 Q34,96 26,62 Z" fill="#EB2F06" stroke="#2D3436" stroke-width="3"/><path d="M28,66 Q45,68 60,86 Q75,68 92,66 Q82,95 60,97 Q38,95 28,66 Z" fill="#FFFFFF"/><circle cx="45" cy="60" r="4" fill="#2D3436"/><circle cx="75" cy="60" r="4" fill="#2D3436"/><circle cx="60" cy="78" r="4.5" fill="#2D3436"/><path d="M54,85 Q60,90 66,85" fill="none" stroke="#2D3436" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "🐸 Chill Frog (Headphones)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#D5F5E3"/><path d="M24,62 A36,36 0 0,1 96,62" fill="none" stroke="#2D3436" stroke-width="5"/><circle cx="42" cy="38" r="13" fill="#2ECC71" stroke="#2D3436" stroke-width="3"/><circle cx="78" cy="38" r="13" fill="#2ECC71" stroke="#2D3436" stroke-width="3"/><circle cx="42" cy="38" r="6" fill="#FFFFFF"/><circle cx="78" cy="38" r="6" fill="#FFFFFF"/><circle cx="43" cy="38" r="3" fill="#2D3436"/><circle cx="79" cy="38" r="3" fill="#2D3436"/><ellipse cx="60" cy="68" rx="36" ry="26" fill="#2ECC71" stroke="#2D3436" stroke-width="3"/><rect x="17" y="54" width="10" height="22" rx="5" fill="#FF4757" stroke="#2D3436" stroke-width="2.5"/><rect x="93" y="54" width="10" height="22" rx="5" fill="#FF4757" stroke="#2D3436" stroke-width="2.5"/><path d="M44,72 Q60,84 76,72" fill="none" stroke="#2D3436" stroke-width="3" stroke-linecap="round"/></svg>',
    "🚀 Astro Bear (Space Explorer)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#2C3A47"/><circle cx="24" cy="28" r="2" fill="#FFF"/><circle cx="94" cy="26" r="2.5" fill="#FFF"/><circle cx="96" cy="88" r="2" fill="#FFF"/><circle cx="60" cy="62" r="42" fill="#74B9FF" fill-opacity="0.35" stroke="#DFE6E9" stroke-width="3.5"/><circle cx="38" cy="38" r="10" fill="#A0522D" stroke="#2D3436" stroke-width="2.5"/><circle cx="82" cy="38" r="10" fill="#A0522D" stroke="#2D3436" stroke-width="2.5"/><circle cx="60" cy="64" r="27" fill="#CD853F" stroke="#2D3436" stroke-width="2.5"/><ellipse cx="60" cy="71" rx="11" ry="8" fill="#FFEAA7"/><circle cx="50" cy="58" r="3.5" fill="#2D3436"/><circle cx="70" cy="58" r="3.5" fill="#2D3436"/><circle cx="60" cy="68" r="3.5" fill="#2D3436"/><path d="M55,74 Q60,78 65,74" fill="none" stroke="#2D3436" stroke-width="2" stroke-linecap="round"/></svg>',
}


# -------------------- FAST CACHED HYBRID DATABASE LAYER --------------------
def get_cloud_db_url():
    try:
        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"]).strip()
    except Exception:
        pass
    return os.environ.get("DATABASE_URL", "").strip()


class HybridCursor:
    def __init__(self, raw_cur, is_pg):
        self._cur = raw_cur
        self._is_pg = is_pg
        self.lastrowid = None

    def _adapt_sql(self, sql):
        if not self._is_pg:
            return sql
        adapted = sql.replace("?", "%s")
        adapted = adapted.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        adapted = adapted.replace("BLOB", "BYTEA")
        if adapted.lstrip().upper().startswith("INSERT INTO") and "RETURNING" not in adapted.upper():
            adapted = adapted.rstrip().rstrip(";") + " RETURNING id"
        return adapted

    def execute(self, sql, params=None):
        adapted = self._adapt_sql(sql)
        if params is not None:
            self._cur.execute(adapted, params)
        else:
            self._cur.execute(adapted)
        if self._is_pg and adapted.lstrip().upper().startswith("INSERT INTO"):
            row = self._cur.fetchone()
            if row:
                self.lastrowid = row[0]
        elif not self._is_pg:
            self.lastrowid = self._cur.lastrowid
        return self

    def executemany(self, sql, seq_of_params):
        if not self._is_pg:
            self._cur.executemany(sql, seq_of_params)
        else:
            adapted = sql.replace("?", "%s")
            self._cur.executemany(adapted, seq_of_params)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()


class HybridConnection:
    def __init__(self, raw_conn, is_pg):
        self.raw_conn = raw_conn
        self.is_pg = is_pg

    def cursor(self):
        return HybridCursor(self.raw_conn.cursor(), self.is_pg)

    def execute(self, sql, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def commit(self):
        self.raw_conn.commit()

    def close(self):
        if not self.is_pg:
            self.raw_conn.close()


@st.cache_resource
def _get_pg_persistent_conn(db_url: str):
    import psycopg2
    clean_url = db_url.strip()
    for attempt in range(2):
        try:
            return psycopg2.connect(clean_url, connect_timeout=10)
        except psycopg2.OperationalError:
            if attempt == 0:
                time.sleep(1.0)
            else:
                raise


def get_connection():
    db_url = get_cloud_db_url()
    if db_url:
        import psycopg2
        raw = _get_pg_persistent_conn(db_url)
        if raw.closed:
            _get_pg_persistent_conn.clear()
            raw = _get_pg_persistent_conn(db_url)
        try:
            if raw.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                raw.rollback()
        except Exception:
            pass
        return HybridConnection(raw, is_pg=True)
    raw = sqlite3.connect(DB_NAME, check_same_thread=False)
    raw.execute("PRAGMA foreign_keys = ON")
    return HybridConnection(raw, is_pg=False)


def read_df(query, conn, params=None):
    sql = query.replace("?", "%s") if conn.is_pg else query
    return pd.read_sql_query(sql, conn.raw_conn, params=params)


def render_clean_table(df_in):
    if df_in.empty:
        return f"<div style='padding:12px; color:{text_muted};'>No records found.</div>"
    th_cells = "".join(f"<th>{col}</th>" for col in df_in.columns)
    body_rows = []
    for _, r in df_in.iterrows():
        tds = "".join(f"<td>{r[col]}</td>" for col in df_in.columns)
        body_rows.append(f"<tr>{tds}</tr>")
    return (
        f'<div class="erp-table-wrap">'
        f'<table class="erp-styled-table">'
        f'<thead><tr>{th_cells}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        f'</table></div>'
    )


def save_user_theme_preference(role, user_id, chosen_theme):
    conn = get_connection()
    cur = conn.cursor()
    if role == "Student":
        cur.execute("UPDATE students SET theme_pref = ? WHERE id = ?", (chosen_theme, user_id))
    elif role == "Faculty":
        cur.execute("UPDATE faculty SET theme_pref = ? WHERE id = ?", (chosen_theme, user_id))
    elif role == "Admin":
        cur.execute("UPDATE admin_settings SET theme_pref = ? WHERE id = 1", (chosen_theme,))
    conn.commit()
    conn.close()


def apply_selected_theme(chosen_code):
    st.session_state.theme_mode = chosen_code
    if st.session_state.auth_user is not None:
        u = st.session_state.auth_user
        save_user_theme_preference(u["role"], u["id"], chosen_code)
    st.rerun()


def render_phone_qr_popover():
    with st.popover("📱 Phone QR", width="stretch"):
        st.caption("Scan with a phone camera to open the ERP on mobile.")
        detected_url = ""
        try:
            if "APP_URL" in st.secrets and str(st.secrets["APP_URL"]).strip():
                detected_url = str(st.secrets["APP_URL"]).strip()
        except Exception:
            pass

        if not detected_url:
            try:
                ctx_url = getattr(st.context, "url", "") or ""
                if ctx_url.startswith("http"):
                    detected_url = ctx_url.split("?")[0].rstrip("/")
            except Exception:
                pass

        if not detected_url:
            detected_url = "https://kcc-attendance-erp-bvt8a4ffjzbfriatjoytm3.streamlit.app"

        target_url = st.text_input("Live Portal URL", value=detected_url, key="phone_qr_url_input").strip()
        if target_url:
            try:
                import qrcode
                qr = qrcode.QRCode(version=1, box_size=6, border=2)
                qr.add_data(target_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#8B171B", back_color="#FFFFFF")
                buf = io.BytesIO()
                qr_img.save(buf, format="PNG")
                st.image(buf.getvalue(), caption="Teacher / Student Mobile Access", width=180)
            except ImportError:
                st.info("Install `qrcode` and `pillow` (`pip install qrcode pillow`) to render the scannable QR image.")
        else:
            st.warning("Enter your live Streamlit URL to generate a QR code.")


def render_top_header_bar():
    col_logo, _, col_qr, col_theme = st.columns([2.2, 3.1, 1.15, 1.45])

    with col_logo:
        logo_file = next((f for f in ["kcc img.png", "kcc_logo.png", "kcc.png"] if os.path.exists(f)), None)
        if logo_file:
            st.image(logo_file, width=110)
        else:
            st.markdown(
                """
                <a href="https://www.kccitm.edu.in/" target="_blank" style="text-decoration:none; display:inline-block;">
                    <div style="background:#A61C20; color:#FFFFFF; width:138px; border-radius:6px;
                                box-shadow:0 4px 14px rgba(166,28,32,0.32); overflow:hidden;
                                font-family:'Times New Roman', Georgia, serif; text-align:center;">
                        <div style="padding:7px 8px 6px 8px;">
                            <div style="font-size:27px; font-weight:700; line-height:0.95; letter-spacing:1.5px;">KCC</div>
                            <div style="font-family:Arial, sans-serif; font-size:10.5px; letter-spacing:2.4px; margin-top:3px; font-weight:500;">INSTITUTE</div>
                            <div style="font-family:Arial, sans-serif; font-size:6.3px; letter-spacing:0.4px; line-height:1.25; margin-top:2px; opacity:0.95;">
                                OF TECHNOLOGY<br>AND MANAGEMENT
                            </div>
                        </div>
                        <div style="height:2.5px; background:#FFFFFF; width:100%;"></div>
                        <div style="font-family:Arial, sans-serif; font-size:6.8px; letter-spacing:1.5px; padding:3.5px 4px; font-weight:600;">
                            GREATER NOIDA
                        </div>
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )

    with col_qr:
        st.markdown('<span class="theme-btn-tag"></span>', unsafe_allow_html=True)
        render_phone_qr_popover()

    with col_theme:
        st.markdown('<span class="theme-btn-tag"></span>', unsafe_allow_html=True)
        with st.popover("🎨 Change Theme", width="stretch"):
            curr = st.session_state.theme_mode
            if st.button(f"{'✓ ' if curr == 'kcc' else ''}🏛️ KCC Theme", key="thm_opt_kcc", width="stretch"):
                apply_selected_theme("kcc")
            if st.button(f"{'✓ ' if curr == 'dark' else ''}🌙 Ocean Dark Mode", key="thm_opt_dark", width="stretch"):
                apply_selected_theme("dark")
            if st.button(f"{'✓ ' if curr == 'light' else ''}☀️ Soft Coastal Light", key="thm_opt_light", width="stretch"):
                apply_selected_theme("light")


def seed_logs_for_record(cur, record_id, attended, total):
    absent = max(total - attended, 0)
    statuses = (["Present"] * attended) + (["Absent"] * absent)
    day_cursor = datetime.now().date() - timedelta(days=1)
    generated = []
    idx = 0
    while idx < len(statuses):
        if day_cursor.weekday() < 5:
            if absent > 0 and idx % max(1, total // max(absent, 1)) == 2 and statuses.count("Absent") > 0:
                st_val = "Absent"
                statuses.remove("Absent")
            else:
                st_val = statuses.pop(0)
            generated.append((record_id, day_cursor.strftime("%Y-%m-%d"), st_val))
        day_cursor -= timedelta(days=1)
    cur.executemany(
        "INSERT INTO attendance_logs (record_id, log_date, status) VALUES (?, ?, ?)",
        generated
    )


def _marks_to_grade(marks):
    if marks >= 90:
        return "O"
    if marks >= 80:
        return "A+"
    if marks >= 70:
        return "A"
    if marks >= 60:
        return "B+"
    if marks >= 50:
        return "B"
    if marks >= 45:
        return "C"
    if marks >= 40:
        return "P"
    return "F"


def seed_semester_results(cur, conn):
    for old_roll in ("2500000001", "2500000002"):
        try:
            cur.execute("DELETE FROM semester_results WHERE roll_no = ?", (old_roll,))
            conn.commit()
        except Exception:
            if conn.is_pg:
                conn.raw_conn.rollback()

    for r_no, sdata in DEMO_RESULTS.items():
        for sem_label, sem_obj in sdata["semesters"].items():
            cur.execute(
                "SELECT COUNT(*) FROM semester_results WHERE roll_no = ? AND semester = ?",
                (r_no, sem_label)
            )
            if cur.fetchone()[0] == 0:
                for sub_item in sem_obj["subjects"]:
                    try:
                        cur.execute("""
                            INSERT INTO semester_results
                            (roll_no, student_name, branch, semester, subject_name, credits, marks_100, grade, sgpa, cgpa, result_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sdata["roll_no"],
                            sdata["name"],
                            sdata["branch"],
                            sem_label,
                            sub_item["subject"],
                            float(sub_item["credits"]),
                            int(sub_item["marks"]),
                            sub_item["grade"],
                            float(sem_obj["sgpa"]),
                            float(sdata["cgpa"]),
                            sdata["result"],
                        ))
                        conn.commit()
                    except Exception:
                        if conn.is_pg:
                            conn.raw_conn.rollback()

    cur.execute("SELECT roll_no, name, branch FROM students ORDER BY roll_no")
    all_st_rows = cur.fetchall()

    sem1_subjects = [
        ("Engineering Physics", 4.0),
        ("Engineering Mathematics-I", 4.0),
        ("Fundamentals of Electrical Engg", 4.0),
        ("Programming for Problem Solving", 4.0),
        ("Professional Communication", 2.0),
    ]
    sem2_subjects = [
        ("Engineering Chemistry", 4.0),
        ("Engineering Mathematics-II", 4.0),
        ("Fundamentals of Electronics Engg", 4.0),
        ("Environment & Ecology", 2.0),
        ("Engineering Graphics", 3.0),
    ]

    for idx_s, (r_no, s_name, s_branch) in enumerate(all_st_rows):
        if str(r_no) in DEMO_RESULTS:
            continue
        cur.execute("SELECT COUNT(*) FROM semester_results WHERE roll_no = ?", (r_no,))
        if cur.fetchone()[0] > 0:
            continue

        rng_r = random.Random(int(re.sub(r"\D", "", str(r_no)) or str(idx_s + 100)))
        tier = idx_s % 5

        sem_records = []
        sgpas = {}
        has_backlog = False

        for sem_label, sub_defs in [("Semester 1", sem1_subjects), ("Semester 2", sem2_subjects)]:
            built_subs = []
            tot_cr = 0.0
            tot_pts = 0.0
            for sub_i, (sub_title, cr_val) in enumerate(sub_defs):
                if tier in (0, 1):
                    marks = rng_r.randint(70, 89)
                elif tier in (2, 3):
                    marks = rng_r.randint(60, 79)
                else:
                    if sem_label == "Semester 2" and sub_i in (1, 2):
                        marks = rng_r.randint(24, 36)
                        has_backlog = True
                    else:
                        marks = rng_r.randint(52, 76)

                grd = _marks_to_grade(marks)
                pts = LETTER_GRADE_POINTS.get(grd, 0)
                tot_cr += cr_val
                tot_pts += cr_val * pts
                built_subs.append((sub_title, cr_val, marks, grd))

            sgpa_val = round(tot_pts / tot_cr, 2) if tot_cr > 0 else 0.0
            sgpas[sem_label] = sgpa_val
            sem_records.append((sem_label, sgpa_val, built_subs))

        cgpa_val = round((sgpas["Semester 1"] + sgpas["Semester 2"]) / 2.0, 2)
        status_str = "BACK" if has_backlog else "PASS"

        for sem_label, sgpa_val, built_subs in sem_records:
            for sub_title, cr_val, marks, grd in built_subs:
                try:
                    cur.execute("""
                        INSERT INTO semester_results
                        (roll_no, student_name, branch, semester, subject_name, credits, marks_100, grade, sgpa, cgpa, result_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(r_no), s_name, s_branch, sem_label, sub_title,
                        float(cr_val), int(marks), grd, float(sgpa_val), float(cgpa_val), status_str
                    ))
                    conn.commit()
                except Exception:
                    if conn.is_pg:
                        conn.raw_conn.rollback()


def ensure_timetable_tables(conn):
    cur = conn.cursor()
    for ddl in [
        """
        CREATE TABLE IF NOT EXISTS student_timetables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            day_code TEXT NOT NULL,
            period_code TEXT NOT NULL,
            subject_txt TEXT NOT NULL,
            faculty_txt TEXT NOT NULL DEFAULT '',
            UNIQUE(section, day_code, period_code)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS faculty_timetables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_code TEXT NOT NULL,
            day_code TEXT NOT NULL,
            period_code TEXT NOT NULL,
            slot_val TEXT NOT NULL,
            UNIQUE(faculty_code, day_code, period_code)
        )
        """,
    ]:
        try:
            cur.execute(ddl)
            conn.commit()
        except Exception:
            if conn.is_pg:
                conn.raw_conn.rollback()


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS admin_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL,
            full_name TEXT NOT NULL,
            password TEXT NOT NULL,
            recovery_pin TEXT NOT NULL,
            theme_pref TEXT NOT NULL DEFAULT 'kcc'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS subject_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            credits REAL NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            recovery_pin TEXT NOT NULL DEFAULT '1234',
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            section TEXT NOT NULL,
            semester TEXT NOT NULL,
            prev_credits REAL NOT NULL DEFAULT 40.0,
            prev_cgpa REAL NOT NULL DEFAULT 8.0,
            avatar_mode TEXT NOT NULL DEFAULT 'Pre-built Doodle',
            doodle_name TEXT NOT NULL DEFAULT '🐱 Cyber Cat (Cool Shades)',
            photo_blob BLOB,
            theme_pref TEXT NOT NULL DEFAULT 'kcc'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS student_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            attended INTEGER NOT NULL DEFAULT 0,
            total INTEGER NOT NULL DEFAULT 0,
            grade TEXT NOT NULL DEFAULT 'A (80-89)',
            UNIQUE(student_id, subject_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subject_catalog(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (record_id) REFERENCES student_subjects(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS self_attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (record_id) REFERENCES student_subjects(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_code TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            recovery_pin TEXT NOT NULL DEFAULT '1234',
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            theme_pref TEXT NOT NULL DEFAULT 'kcc',
            created_at TEXT NOT NULL DEFAULT '2026-08-01'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS faculty_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            appointed_at TEXT NOT NULL DEFAULT '2026-08-01',
            UNIQUE(faculty_id, section, subject_id),
            FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subject_catalog(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS semester_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            student_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            semester TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            credits REAL NOT NULL,
            marks_100 INTEGER NOT NULL,
            grade TEXT NOT NULL,
            sgpa REAL NOT NULL,
            cgpa REAL NOT NULL,
            result_status TEXT NOT NULL DEFAULT 'PASS'
        )
        """,
    ]

    for stmt in ddl_statements:
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            if conn.is_pg:
                conn.raw_conn.rollback()

    ensure_timetable_tables(conn)

    for tbl in ["admin_settings", "students", "faculty"]:
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN theme_pref TEXT NOT NULL DEFAULT 'kcc'")
            conn.commit()
        except Exception:
            if conn.is_pg:
                conn.raw_conn.rollback()

    try:
        cur.execute("ALTER TABLE faculty ADD COLUMN created_at TEXT NOT NULL DEFAULT '2026-08-01'")
        conn.commit()
    except Exception:
        if conn.is_pg:
            conn.raw_conn.rollback()

    try:
        cur.execute("ALTER TABLE faculty_assignments ADD COLUMN appointed_at TEXT NOT NULL DEFAULT '2026-08-01'")
        conn.commit()
    except Exception:
        if conn.is_pg:
            conn.raw_conn.rollback()

    cur.execute("SELECT COUNT(*) FROM admin_settings")
    if cur.fetchone()[0] == 0:
        try:
            cur.execute("""
                INSERT INTO admin_settings (id, username, full_name, password, recovery_pin, theme_pref)
                VALUES (1, 'admin', 'KCC ERP Administrator', ?, '9999', 'kcc')
            """, (hash_password("admin123"),))
            conn.commit()
        except Exception:
            if conn.is_pg:
                conn.raw_conn.rollback()

    cur.execute("SELECT COUNT(*) FROM subject_catalog")
    if cur.fetchone()[0] == 0:
        subjects_seed = [
            ("BCS301", "Data Structures", 4.0),
            ("BCS302", "Computer Organization & Architecture", 4.0),
            ("BCS303", "Discrete Structures & Theory of Logic", 4.0),
            ("BAS303", "Mathematics-IV", 4.0),
            ("BCC302", "Python Programming", 2.0),
            ("BCS351", "Data Structures Lab", 1.0),
            ("BCS352", "COA Lab", 1.0),
        ]
        for s_code, s_name, s_cred in subjects_seed:
            try:
                cur.execute("INSERT INTO subject_catalog (code, name, credits) VALUES (?, ?, ?)", (s_code, s_name, s_cred))
                conn.commit()
            except Exception:
                if conn.is_pg:
                    conn.raw_conn.rollback()

    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        doodle_list = list(DOODLES.keys())
        default_st_hash = hash_password("student123")
        sections_roster = {
            "Section B-2": [
                ("2504920100201", "Ananya Singh"),
                ("2504920100202", "Kabir Yadav"),
                ("2504920100203", "Ishita Tiwari"),
                ("2504920100204", "Devansh Mishra"),
                ("2504920100205", "Riya Agarwal"),
                ("2504920100206", "Harshit Dubey"),
                ("2504920100207", "Sneha Chauhan"),
                ("2504920100208", "Yashvardhan Pandey"),
                ("2504920100209", "Tanvi Saxena"),
                ("2504920100210", "Nikhil Srivastava"),
            ],
            "Section B-3": [
                ("2504920100346", "Manas Srivastav"),
                ("2504920100312", "Aarav Sharma"),
                ("2504920100315", "Priya Verma"),
                ("2504920100318", "Rohan Gupta"),
                ("2504920100321", "Aditi Joshi"),
                ("2504920100324", "Siddharth Nair"),
                ("2504920100327", "Kritika Bansal"),
                ("2504920100330", "Utkarsh Tripathi"),
                ("2504920100335", "Megha Kulkarni"),
                ("2504920100340", "Pranav Shukla"),
            ],
            "Section B-4": [
                ("2504920100401", "Vaibhav Rastogi"),
                ("2504920100402", "Nandini Bhatt"),
                ("2504920100403", "Ayushman Dixit"),
                ("2504920100404", "Shreya Malhotra"),
                ("2504920100405", "Kartikeya Pathak"),
                ("2504920100406", "Palak Jaiswal"),
                ("2504920100407", "Abhinav Chaturvedi"),
                ("2504920100408", "Divya Rajpoot"),
                ("2504920100409", "Tushar Chaudhary"),
                ("2504920100410", "Sakshi Rathore"),
            ],
            "Section B-6": [
                ("2504920100601", "Aditya Dwivedi"),
                ("2504920100602", "Muskan Thakur"),
                ("2504920100603", "Shaurya Pratap"),
                ("2504920100604", "Komal Kashyap"),
                ("2504920100605", "Rajat Maurya"),
                ("2504920100606", "Anushka Tomar"),
                ("2504920100607", "Mayank Solanki"),
                ("2504920100608", "Pooja Bisht"),
                ("2504920100609", "Himanshu Gautam"),
                ("2504920100610", "Lavanya Singhal"),
            ],
        }

        rng = random.Random(42)
        idx_counter = 0
        for sec_name, stu_list in sections_roster.items():
            for r_no, s_name in stu_list:
                prev_cg = 8.35 if r_no == "2504920100346" else round(rng.uniform(6.95, 9.15), 2)
                doodle = doodle_list[0] if r_no == "2504920100346" else doodle_list[idx_counter % len(doodle_list)]
                try:
                    cur.execute("""
                        INSERT INTO students (roll_no, password, recovery_pin, name, branch, section, semester, prev_credits, prev_cgpa, avatar_mode, doodle_name, photo_blob, theme_pref)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r_no, default_st_hash, "1234", s_name, "B.Tech CSE", sec_name,
                        "3rd Semester", 40.0, prev_cg, "Pre-built Doodle", doodle, None, "kcc"
                    ))
                    conn.commit()
                except Exception:
                    if conn.is_pg:
                        conn.raw_conn.rollback()
                idx_counter += 1

    cur.execute("SELECT COUNT(*) FROM student_subjects")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id, roll_no FROM students")
        all_students = cur.fetchall()
        cur.execute("SELECT id, code FROM subject_catalog ORDER BY code")
        all_subjects = cur.fetchall()

        manas_preset = [
            (26, 30, "A (80-89)"),
            (21, 30, "B+ (70-79)"),
            (24, 28, "A+ (90-100)"),
            (19, 28, "B (60-69)"),
            (18, 20, "A+ (90-100)"),
            (11, 12, "A (80-89)"),
            (9, 12, "B+ (70-79)"),
        ]
        grade_choices = ["A+ (90-100)", "A (80-89)", "B+ (70-79)", "B (60-69)", "C (50-59)"]
        rng_fix = random.Random(42)

        for st_id, r_no in all_students:
            for s_idx, (sub_id, code) in enumerate(all_subjects):
                if r_no == "2504920100346":
                    att, tot, grd = manas_preset[s_idx % len(manas_preset)]
                else:
                    tot = 12 if code in ("BCS351", "BCS352") else (20 if code == "BCC302" else 28)
                    att = rng_fix.randint(int(tot * 0.58), tot)
                    grd = rng_fix.choice(grade_choices)
                try:
                    cur.execute(
                        "INSERT INTO student_subjects (student_id, subject_id, attended, total, grade) VALUES (?, ?, ?, ?, ?)",
                        (st_id, sub_id, att, tot, grd)
                    )
                    new_rec_id = cur.lastrowid
                    if new_rec_id:
                        seed_logs_for_record(cur, new_rec_id, att, tot)
                    conn.commit()
                except Exception:
                    if conn.is_pg:
                        conn.raw_conn.rollback()

    cur.execute("SELECT COUNT(*) FROM faculty")
    if cur.fetchone()[0] == 0:
        default_fac_hash = hash_password("faculty123")
        for f_code, f_name, f_desig in [
            ("FAC001", "Mr. Vishal", "Assistant Professor (Python)"),
            ("FAC002", "Arya Devi", "Assistant Professor (COA)"),
            ("FAC003", "Mr. Satyam", "Assistant Professor (DSTL)"),
        ]:
            try:
                cur.execute(
                    "INSERT INTO faculty (faculty_code, password, recovery_pin, name, department, designation, theme_pref, created_at) VALUES (?, ?, ?, ?, 'Computer Science & Engineering', ?, 'kcc', '2026-08-01')",
                    (f_code, default_fac_hash, "1234", f_name, f_desig)
                )
                conn.commit()
            except Exception:
                if conn.is_pg:
                    conn.raw_conn.rollback()

    cur.execute("SELECT id, faculty_code FROM faculty")
    fac_map = {code: fid for fid, code in cur.fetchall()}
    cur.execute("SELECT id, code FROM subject_catalog")
    sub_map = {code: sid for sid, code in cur.fetchall()}

    all_secs = ["Section B-2", "Section B-3", "Section B-4", "Section B-6"]
    if all(k in fac_map for k in ("FAC001", "FAC002", "FAC003")) and all(k in sub_map for k in ("BCC302", "BCS302", "BCS303")):
        for sec in all_secs:
            for f_code, s_code in [("FAC001", "BCC302"), ("FAC002", "BCS302"), ("FAC003", "BCS303")]:
                fid = fac_map[f_code]
                sid = sub_map[s_code]
                cur.execute(
                    "SELECT id FROM faculty_assignments WHERE faculty_id = ? AND section = ? AND subject_id = ?",
                    (fid, sec, sid)
                )
                if not cur.fetchone():
                    try:
                        cur.execute(
                            "INSERT INTO faculty_assignments (faculty_id, section, subject_id, appointed_at) VALUES (?, ?, ?, '2026-08-01')",
                            (fid, sec, sid)
                        )
                        conn.commit()
                    except Exception:
                        if conn.is_pg:
                            conn.raw_conn.rollback()

    seed_semester_results(cur, conn)
    conn.close()


@st.cache_resource
def ensure_db_initialized(schema_v: int = 3):
    init_db()
    return True


# -------------------- PDF / DOCX FILE PARSERS --------------------
def extract_text_from_upload(uploaded_file):
    if uploaded_file is None:
        return ""
    fname = (uploaded_file.name or "").lower()
    raw_bytes = uploaded_file.getvalue()

    if fname.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(raw_bytes))
            lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for tbl in doc.tables:
                for row in tbl.rows:
                    cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                    lines.append(" | ".join(cells))
            return "\n".join(lines)
        except ImportError:
            import zipfile
            import xml.etree.ElementTree as ET
            try:
                with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                    xml_bytes = zf.read("word/document.xml")
                root = ET.fromstring(xml_bytes)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                lines = []
                for tr in root.findall(".//w:tr", ns):
                    row_cells = []
                    for tc in tr.findall(".//w:tc", ns):
                        cell_txt = "".join(t.text or "" for t in tc.findall(".//w:t", ns)).strip()
                        row_cells.append(cell_txt)
                    if any(row_cells):
                        lines.append(" | ".join(row_cells))
                if not lines:
                    for p in root.findall(".//w:p", ns):
                        p_txt = "".join(t.text or "" for t in p.findall(".//w:t", ns)).strip()
                        if p_txt:
                            lines.append(p_txt)
                return "\n".join(lines)
            except Exception as exc:
                st.error(f"Could not parse .docx archive: {exc}")
                return ""
        except Exception as exc:
            st.error(f"Could not read .docx file: {exc}")
            return ""

    if fname.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw_bytes))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            pass
        try:
            import pdfplumber
            pages_txt = []
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                for page in pdf.pages:
                    pages_txt.append(page.extract_text() or "")
            return "\n".join(pages_txt)
        except Exception as exc:
            st.error(f"Could not read .pdf file (install `pypdf` or `pdfplumber`): {exc}")
            return ""

    return raw_bytes.decode("utf-8", errors="ignore")


def apply_uploaded_results_to_db(text_content, conn):
    if not text_content.strip():
        return 0, "Uploaded file had no readable text."

    cur = conn.cursor()
    cur.execute("SELECT roll_no, name, branch FROM students")
    db_students = {str(r[0]).strip(): (str(r[1]).strip(), str(r[2]).strip()) for r in cur.fetchall()}

    updated_rows = 0
    lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]

    for ln in lines:
        parts = [p.strip() for p in re.split(r"\s*\|\s*|\s*,\s*", ln)]
        if len(parts) >= 7 and re.fullmatch(r"\d{6,15}", parts[0]):
            r_no = parts[0]
            r_name = parts[1]
            if r_no in db_students:
                db_name, db_branch = db_students[r_no]
                if db_name.lower() != r_name.lower():
                    continue
                sem_lbl = parts[2] if parts[2].lower().startswith("sem") else f"Semester {parts[2]}"
                subj_nm = parts[3]
                try:
                    cred_v = float(parts[4])
                    marks_v = int(float(parts[5]))
                    grd_v = parts[6].upper() if parts[6].upper() in LETTER_GRADE_POINTS else _marks_to_grade(marks_v)
                    sgpa_v = float(parts[7]) if len(parts) > 7 else float(LETTER_GRADE_POINTS.get(grd_v, 7))
                    cgpa_v = float(parts[8]) if len(parts) > 8 else sgpa_v
                    stat_v = parts[9].upper() if len(parts) > 9 else ("BACK" if grd_v == "F" else "PASS")
                except ValueError:
                    continue

                cur.execute(
                    "DELETE FROM semester_results WHERE roll_no = ? AND semester = ? AND LOWER(subject_name) = LOWER(?)",
                    (r_no, sem_lbl, subj_nm)
                )
                cur.execute("""
                    INSERT INTO semester_results
                    (roll_no, student_name, branch, semester, subject_name, credits, marks_100, grade, sgpa, cgpa, result_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (r_no, db_name, db_branch, sem_lbl, subj_nm, cred_v, marks_v, grd_v, sgpa_v, cgpa_v, stat_v))
                updated_rows += 1

    if updated_rows == 0:
        for ln in lines:
            roll_match = re.search(r"\b(\d{8,15})\b", ln)
            if not roll_match:
                continue
            r_no = roll_match.group(1)
            if r_no not in db_students:
                continue
            db_name, _ = db_students[r_no]
            if db_name.lower() not in ln.lower():
                continue

            sem_m = re.search(r"(Semester\s*\d+|Sem\s*\d+)", ln, re.IGNORECASE)
            sem_lbl = sem_m.group(1).title().replace("Sem ", "Semester ") if sem_m else "Semester 1"
            sgpa_m = re.search(r"SGPA\s*[:=]?\s*(\d+(?:\.\d+)?)", ln, re.IGNORECASE)
            cgpa_m = re.search(r"CGPA\s*[:=]?\s*(\d+(?:\.\d+)?)", ln, re.IGNORECASE)
            if sgpa_m:
                sgpa_v = float(sgpa_m.group(1))
                cgpa_v = float(cgpa_m.group(1)) if cgpa_m else sgpa_v
                stat_v = "BACK" if "BACK" in ln.upper() or "FAIL" in ln.upper() else "PASS"
                cur.execute(
                    "UPDATE semester_results SET sgpa = ?, cgpa = ?, result_status = ? WHERE roll_no = ? AND semester = ?",
                    (sgpa_v, cgpa_v, stat_v, r_no, sem_lbl)
                )
                updated_rows += 1

    conn.commit()
    return updated_rows, f"Matched and updated {updated_rows} result record(s) by Roll No & Name."


def apply_uploaded_timetable_to_db(text_content, target_type, target_key, conn):
    ensure_timetable_tables(conn)
    if not text_content.strip():
        return 0, "Uploaded file had no readable text."

    cur = conn.cursor()
    updated = 0
    lines = [ln.strip() for ln in text_content.splitlines() if ln.strip()]
    period_codes = [p[0] for p in PERIOD_SLOTS]

    for ln in lines:
        parts = [p.strip() for p in re.split(r"\s*\|\s*|\s*,\s*", ln)]
        if len(parts) < 3:
            continue
        day_token = parts[0][:3].title()
        if day_token not in DAYS_ORDER:
            continue

        slot_vals = parts[1:]
        for idx_s, p_code in enumerate(period_codes):
            if idx_s >= len(slot_vals):
                break
            val = slot_vals[idx_s]
            if not val:
                continue
            if target_type == "student":
                subj_part = val.split("(")[0].strip()
                fac_m = re.search(r"\(([^)]+)\)", val)
                fac_part = fac_m.group(1).strip() if fac_m else ""
                cur.execute(
                    "DELETE FROM student_timetables WHERE section = ? AND day_code = ? AND period_code = ?",
                    (target_key, day_token, p_code)
                )
                cur.execute("""
                    INSERT INTO student_timetables (section, day_code, period_code, subject_txt, faculty_txt)
                    VALUES (?, ?, ?, ?, ?)
                """, (target_key, day_token, p_code, subj_part, fac_part))
                updated += 1
            else:
                sec_clean = val.replace("Section", "").strip()
                cur.execute(
                    "DELETE FROM faculty_timetables WHERE UPPER(faculty_code) = ? AND day_code = ? AND period_code = ?",
                    (target_key.upper(), day_token, p_code)
                )
                cur.execute("""
                    INSERT INTO faculty_timetables (faculty_code, day_code, period_code, slot_val)
                    VALUES (?, ?, ?, ?)
                """, (target_key.upper(), day_token, p_code, sec_clean))
                updated += 1

    conn.commit()
    return updated, f"Updated {updated} timetable slot(s) for {target_key}."


def get_effective_section_timetable(section_name, conn):
    ensure_timetable_tables(conn)
    base = SECTION_TIMETABLES.get(section_name, SECTION_TIMETABLES["Section B-3"])
    out = {
        "room": base["room"],
        "Mon": list(base["Mon"]),
        "Tue": list(base["Tue"]),
        "Wed": list(base["Wed"]),
        "Thu": list(base["Thu"]),
        "Fri": list(base["Fri"]),
    }
    cur = conn.cursor()
    cur.execute("SELECT day_code, period_code, subject_txt, faculty_txt FROM student_timetables WHERE section = ?", (section_name,))
    p_index_map = {p[0]: i for i, p in enumerate(PERIOD_SLOTS)}
    for d_c, p_c, s_txt, f_txt in cur.fetchall():
        if d_c in out and p_c in p_index_map:
            out[d_c][p_index_map[p_c]] = (s_txt, f_txt)
    return out


def get_effective_faculty_timetable(fac_code, conn):
    ensure_timetable_tables(conn)
    fc = str(fac_code).upper()
    base = FACULTY_TIMETABLES.get(fc)
    out = {
        d: list(base[d]) if base and d in base else ["Free"] * len(PERIOD_SLOTS)
        for d in DAYS_ORDER
    }
    for d in DAYS_ORDER:
        for idx_p, p_info in enumerate(PERIOD_SLOTS):
            if p_info[0] == "LUNCH":
                out[d][idx_p] = "LUNCH"

    cur = conn.cursor()
    cur.execute("SELECT day_code, period_code, slot_val FROM faculty_timetables WHERE UPPER(faculty_code) = ?", (fc,))
    p_index_map = {p[0]: i for i, p in enumerate(PERIOD_SLOTS)}
    for d_c, p_c, s_val in cur.fetchall():
        if d_c in out and p_c in p_index_map:
            out[d_c][p_index_map[p_c]] = s_val
    return out


def authenticate_user(role, login_id, password):
    login_id = login_id.strip()
    pw_hash = hash_password(password)
    conn = get_connection()
    cur = conn.cursor()

    if role == "Admin":
        cur.execute("SELECT username, full_name, theme_pref FROM admin_settings WHERE LOWER(username) = LOWER(?) AND password = ?", (login_id, pw_hash))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"role": "Admin", "id": 1, "name": row[1], "username": row[0], "theme_pref": row[2] or "kcc"}
        return None

    elif role == "Student":
        cur.execute("SELECT id, name, roll_no, section, theme_pref FROM students WHERE roll_no = ? AND password = ?", (login_id, pw_hash))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"role": "Student", "id": row[0], "name": row[1], "roll_no": row[2], "section": row[3], "theme_pref": row[4] or "kcc"}

    elif role == "Faculty":
        cur.execute("SELECT id, name, faculty_code, theme_pref FROM faculty WHERE UPPER(faculty_code) = UPPER(?) AND password = ?", (login_id, pw_hash))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"role": "Faculty", "id": row[0], "name": row[1], "faculty_code": row[2], "theme_pref": row[3] or "kcc"}

    conn.close()
    return None


def quick_demo_login(role, login_id):
    conn = get_connection()
    cur = conn.cursor()
    if role == "Admin":
        cur.execute("SELECT username, full_name, theme_pref FROM admin_settings WHERE id = 1")
        row = cur.fetchone()
        conn.close()
        if row:
            return {"role": "Admin", "id": 1, "name": row[1], "username": row[0], "theme_pref": row[2] or "kcc"}
    elif role == "Student":
        cur.execute("SELECT id, name, roll_no, section, theme_pref FROM students WHERE roll_no = ?", (login_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"role": "Student", "id": row[0], "name": row[1], "roll_no": row[2], "section": row[3], "theme_pref": row[4] or "kcc"}
    elif role == "Faculty":
        cur.execute("SELECT id, name, faculty_code, theme_pref FROM faculty WHERE UPPER(faculty_code) = UPPER(?)", (login_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"role": "Faculty", "id": row[0], "name": row[1], "faculty_code": row[2], "theme_pref": row[3] or "kcc"}
    conn.close()
    return None


def complete_login(user_obj):
    st.session_state.auth_user = user_obj
    st.session_state.theme_mode = user_obj.get("theme_pref", "kcc")
    st.session_state.st_self_att_open = False
    st.session_state.self_open_date_record = None
    st.rerun()


def logout_user():
    st.session_state.auth_user = None
    st.session_state.theme_mode = "kcc"
    st.session_state.st_self_att_open = False
    st.session_state.self_open_date_record = None
    st.rerun()


def change_user_password(role, user_id, current_pw, new_pw, new_pin=None):
    if len(new_pw.strip()) < 4:
        return False, "New password must be at least 4 characters long."
    if new_pin and (not new_pin.isdigit() or len(new_pin) != 4):
        return False, "Recovery PIN must be a 4-digit number."

    cur_hash = hash_password(current_pw)
    new_hash = hash_password(new_pw)
    conn = get_connection()
    cur = conn.cursor()

    if role == "Student":
        cur.execute("SELECT password, recovery_pin FROM students WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row or row[0] != cur_hash:
            conn.close()
            return False, "Current password is incorrect."
        pin_to_save = new_pin if new_pin else row[1]
        cur.execute("UPDATE students SET password = ?, recovery_pin = ? WHERE id = ?", (new_hash, pin_to_save, user_id))

    elif role == "Faculty":
        cur.execute("SELECT password, recovery_pin FROM faculty WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row or row[0] != cur_hash:
            conn.close()
            return False, "Current password is incorrect."
        pin_to_save = new_pin if new_pin else row[1]
        cur.execute("UPDATE faculty SET password = ?, recovery_pin = ? WHERE id = ?", (new_hash, pin_to_save, user_id))

    elif role == "Admin":
        cur.execute("SELECT password, recovery_pin FROM admin_settings WHERE id = 1")
        row = cur.fetchone()
        if not row or row[0] != cur_hash:
            conn.close()
            return False, "Current Admin password is incorrect."
        pin_to_save = new_pin if new_pin else row[1]
        cur.execute("UPDATE admin_settings SET password = ?, recovery_pin = ? WHERE id = 1", (new_hash, pin_to_save))

    conn.commit()
    conn.close()
    return True, "Password & Recovery PIN updated successfully!"


def admin_reset_credentials(target_role, identifier, new_pw, new_pin):
    if len(new_pw.strip()) < 4:
        return False, "Password must be at least 4 characters long."
    if not new_pin.strip().isdigit() or len(new_pin.strip()) != 4:
        return False, "Recovery PIN must be exactly 4 digits."

    new_hash = hash_password(new_pw)
    conn = get_connection()
    cur = conn.cursor()
    if target_role == "Student":
        cur.execute(
            "UPDATE students SET password = ?, recovery_pin = ? WHERE roll_no = ?",
            (new_hash, new_pin.strip(), identifier.strip())
        )
    elif target_role == "Faculty":
        cur.execute(
            "UPDATE faculty SET password = ?, recovery_pin = ? WHERE UPPER(faculty_code) = UPPER(?)",
            (new_hash, new_pin.strip(), identifier.strip())
        )
    conn.commit()
    conn.close()
    return True, f"Credentials updated & hashed for {identifier.strip()} (New Password: '{new_pw.strip()}' | PIN: '{new_pin.strip()}')."


def verify_and_reset_password(role, login_id, full_name, recovery_pin, new_pw):
    login_id = login_id.strip()
    full_name = full_name.strip().lower()
    recovery_pin = recovery_pin.strip()

    if len(new_pw.strip()) < 4:
        return False, "New password must be at least 4 characters long."

    conn = get_connection()
    cur = conn.cursor()

    if role == "Student":
        cur.execute("SELECT id, name, recovery_pin FROM students WHERE roll_no = ?", (login_id,))
        row = cur.fetchone()
        if not row or row[1].strip().lower() != full_name:
            conn.close()
            return False, "Roll Number and Registered Name do not match."
        db_id, _, db_pin = row

    elif role == "Faculty":
        cur.execute("SELECT id, name, recovery_pin FROM faculty WHERE UPPER(faculty_code) = UPPER(?)", (login_id,))
        row = cur.fetchone()
        if not row or row[1].strip().lower() != full_name:
            conn.close()
            return False, "Faculty ID and Registered Name do not match."
        db_id, _, db_pin = row

    elif role == "Admin":
        cur.execute("SELECT username, full_name, recovery_pin FROM admin_settings WHERE id = 1")
        row = cur.fetchone()
        if not row or row[0].lower() != login_id.lower() or row[1].strip().lower() != full_name:
            conn.close()
            return False, "Admin Username and Registered Name do not match."
        db_id, _, db_pin = 1, row[1], row[2]

    if recovery_pin != db_pin:
        conn.close()
        return False, "Verification failed: Invalid 4-Digit Recovery PIN."

    new_hash = hash_password(new_pw)
    if role == "Student":
        cur.execute("UPDATE students SET password = ? WHERE id = ?", (new_hash, db_id))
    elif role == "Faculty":
        cur.execute("UPDATE faculty SET password = ? WHERE id = ?", (new_hash, db_id))
    elif role == "Admin":
        cur.execute("UPDATE admin_settings SET password = ? WHERE id = 1", (new_hash,))

    conn.commit()
    conn.close()
    return True, f"Identity verified! Password for {login_id} has been securely reset."


def render_sidebar_password_changer(role, user_id, current_pin):
    with st.expander("🔒 Change Password & PIN", expanded=False):
        with st.form(f"chg_pw_form_{role}_{user_id}", clear_on_submit=True):
            cur_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            conf_pw = st.text_input("Confirm New Password", type="password")
            new_pin = st.text_input("4-Digit Recovery PIN", value=str(current_pin), max_chars=4)
            if st.form_submit_button("🔑 Update Credentials", width="stretch"):
                if new_pw != conf_pw:
                    st.error("New password and confirmation do not match.")
                else:
                    ok, msg = change_user_password(role, user_id, cur_pw, new_pw, new_pin)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def fetch_student_by_id(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, roll_no, name, branch, section, semester, prev_credits, prev_cgpa, avatar_mode, doodle_name, photo_blob, recovery_pin
        FROM students WHERE id = ?
    """, (student_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0], "roll_no": r[1], "name": r[2], "branch": r[3],
        "section": r[4], "semester": r[5], "prev_credits": r[6], "prev_cgpa": r[7],
        "avatar_mode": r[8], "doodle_name": r[9], "photo_blob": r[10], "recovery_pin": r[11]
    }


def fetch_student_records(student_id):
    conn = get_connection()
    query = """
        SELECT ss.id AS record_id, sc.id AS subject_id, sc.code, sc.name, sc.credits,
               ss.attended, ss.total, ss.grade
        FROM student_subjects ss
        JOIN subject_catalog sc ON ss.subject_id = sc.id
        WHERE ss.student_id = ?
        ORDER BY sc.code
    """
    df = read_df(query, conn, params=(student_id,))
    conn.close()
    return df


def fetch_student_semester_results(roll_no):
    conn = get_connection()
    df = read_df("""
        SELECT semester, subject_name, credits, marks_100, grade, sgpa, cgpa, result_status, student_name, branch
        FROM semester_results
        WHERE roll_no = ?
        ORDER BY semester, id
    """, conn, params=(str(roll_no).strip(),))
    conn.close()
    return df


def fetch_faculty_roster_since_appointment(target_section, target_sub_id, appointed_at_str):
    conn = get_connection()
    cur = conn.cursor()
    appt_date = str(appointed_at_str or "2026-08-01")[:10]
    cur.execute("""
        SELECT ss.id AS record_id, s.roll_no, s.name AS student_name, s.section,
               COUNT(al.id) AS total_cnt,
               COALESCE(SUM(CASE WHEN al.status = 'Present' THEN 1 ELSE 0 END), 0) AS present_cnt
        FROM student_subjects ss
        JOIN students s ON ss.student_id = s.id
        LEFT JOIN attendance_logs al ON al.record_id = ss.id AND al.log_date >= ?
        WHERE s.section = ? AND ss.subject_id = ?
        GROUP BY ss.id, s.roll_no, s.name, s.section
        ORDER BY s.roll_no
    """, (appt_date, target_section, target_sub_id))
    rows = cur.fetchall()
    conn.close()
    rows_out = [
        {
            "record_id": int(r[0]),
            "roll_no": r[1],
            "student_name": r[2],
            "section": r[3],
            "attended": int(r[5] or 0),
            "total": int(r[4] or 0),
        }
        for r in rows
    ]
    return pd.DataFrame(rows_out)


def fetch_all_self_attendance_stats(record_ids):
    if not record_ids:
        return {}
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in record_ids)
    cur.execute(f"""
        SELECT record_id,
               COUNT(*) AS tot,
               COALESCE(SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END), 0) AS att
        FROM self_attendance_logs
        WHERE record_id IN ({placeholders})
        GROUP BY record_id
    """, tuple(record_ids))
    res = {int(r[0]): (int(r[2] or 0), int(r[1] or 0)) for r in cur.fetchall()}
    conn.close()
    return res


def fetch_self_record_logs(record_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT log_date, status FROM self_attendance_logs WHERE record_id = ? ORDER BY log_date ASC, id ASC", (record_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_self_attendance(record_id, status, log_dt):
    conn = get_connection()
    cur = conn.cursor()
    d_str = log_dt.strftime("%Y-%m-%d") if log_dt else datetime.now().strftime("%Y-%m-%d")
    cur.execute("INSERT INTO self_attendance_logs (record_id, log_date, status) VALUES (?, ?, ?)", (record_id, d_str, status))
    conn.commit()
    conn.close()


def fetch_record_logs_with_ids(record_id, min_date_str=None):
    conn = get_connection()
    cur = conn.cursor()
    if min_date_str:
        cur.execute(
            "SELECT id, log_date, status FROM attendance_logs WHERE record_id = ? AND log_date >= ? ORDER BY log_date DESC, id DESC",
            (record_id, str(min_date_str)[:10])
        )
    else:
        cur.execute("SELECT id, log_date, status FROM attendance_logs WHERE record_id = ? ORDER BY log_date DESC, id DESC", (record_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_record_logs(record_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT log_date, status FROM attendance_logs WHERE record_id = ? ORDER BY log_date ASC, id ASC", (record_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def sync_record_totals_from_logs(cur, record_id):
    cur.execute("SELECT COUNT(*) FROM attendance_logs WHERE record_id = ?", (record_id,))
    tot = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attendance_logs WHERE record_id = ? AND status = 'Present'", (record_id,))
    att = cur.fetchone()[0]
    cur.execute("UPDATE student_subjects SET attended = ?, total = ? WHERE id = ?", (att, tot, record_id))


def mark_attendance_record(record_id, status, log_dt=None):
    conn = get_connection()
    cur = conn.cursor()
    d_str = log_dt.strftime("%Y-%m-%d") if log_dt else datetime.now().strftime("%Y-%m-%d")
    cur.execute("INSERT INTO attendance_logs (record_id, log_date, status) VALUES (?, ?, ?)", (record_id, d_str, status))
    sync_record_totals_from_logs(cur, record_id)
    conn.commit()
    conn.close()


def edit_attendance_log_entry(log_id, record_id, new_status, new_date_str=None):
    conn = get_connection()
    cur = conn.cursor()
    if new_date_str:
        cur.execute("UPDATE attendance_logs SET status = ?, log_date = ? WHERE id = ?", (new_status, new_date_str, log_id))
    else:
        cur.execute("UPDATE attendance_logs SET status = ? WHERE id = ?", (new_status, log_id))
    sync_record_totals_from_logs(cur, record_id)
    conn.commit()
    conn.close()


def delete_attendance_log_entry(log_id, record_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM attendance_logs WHERE id = ?", (log_id,))
    sync_record_totals_from_logs(cur, record_id)
    conn.commit()
    conn.close()


def update_student_avatar_and_cgpa(student_id, prev_credits, prev_cgpa, avatar_mode, doodle_name, photo_blob):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE students
        SET prev_credits = ?, prev_cgpa = ?, avatar_mode = ?, doodle_name = ?, photo_blob = ?
        WHERE id = ?
    """, (prev_credits, prev_cgpa, avatar_mode, doodle_name, photo_blob, student_id))
    conn.commit()
    conn.close()


def analyze_attendance(attended, total, target=0.75):
    if total == 0:
        return 0.0, "No Classes", "No classes held yet (0/0)."
    pct = (attended / total) * 100
    if pct >= target * 100:
        can_bunk = math.floor((attended - target * total) / target)
        return pct, "Safe (>= 75%)", f"Can skip {can_bunk} class(es) and still stay above {int(target*100)}%"
    else:
        must_attend = math.ceil((target * total - attended) / (1 - target))
        return pct, "Shortage (< 75%)", f"Attend {must_attend} more class(es) to reach {int(target*100)}%"


def render_student_timetable_section(section_name):
    conn_tt = get_connection()
    tt_data = get_effective_section_timetable(section_name, conn_tt)
    conn_tt.close()

    now_ist = get_now_ist()
    default_day = DAY_FULL_TO_SHORT.get(now_ist.strftime("%A"), "Mon")
    default_period = get_active_period_code(now_ist)

    st.subheader(f"🗓️ Class Timetable — {section_name} ({tt_data['room']})")
    st.caption(f"Live IST Clock: {now_ist.strftime('%A, %d %b %Y • %I:%M %p')} • Active class blinks 🔴 red across its border.")

    tc1, tc2, tc3 = st.columns([1.2, 1.3, 1.8])
    with tc1:
        sim_enabled = st.checkbox("🧪 Preview / Test Time", value=False, key="tt_sim_toggle")
    with tc2:
        chosen_day = st.selectbox(
            "Day",
            DAYS_ORDER,
            index=DAYS_ORDER.index(default_day) if default_day in DAYS_ORDER else 0,
            disabled=not sim_enabled,
            key="tt_sim_day",
        )
    with tc3:
        period_options = ["None (Outside Class Hours)"] + [f"{p[0]} ({p[3]})" for p in PERIOD_SLOTS]
        default_p_idx = 0
        if default_period:
            for idx_p, slot_item in enumerate(PERIOD_SLOTS, start=1):
                if slot_item[0] == default_period:
                    default_p_idx = idx_p
                    break
        chosen_period_lbl = st.selectbox(
            "Active Period Slot",
            period_options,
            index=default_p_idx,
            disabled=not sim_enabled,
            key="tt_sim_period",
        )

    active_day = chosen_day if sim_enabled else default_day
    active_period = (
        None if (sim_enabled and chosen_period_lbl.startswith("None"))
        else (chosen_period_lbl.split(" ")[0] if sim_enabled else default_period)
    )

    if active_period:
        p_idx = next((i for i, s in enumerate(PERIOD_SLOTS) if s[0] == active_period), None)
        if p_idx is not None:
            subj_now, fac_now = tt_data.get(active_day, [])[p_idx]
            st.markdown(
                f"<div style='padding:10px 14px; border-radius:12px; border:2px solid #FF1E27; "
                f"background:rgba(239,68,68,0.14); margin-bottom:12px; font-weight:700;'>"
                f"🔴 LIVE NOW ({active_day} • {PERIOD_SLOTS[p_idx][0]} {PERIOD_SLOTS[p_idx][3]}): "
                f"{subj_now} {f'— {fac_now}' if fac_now else ''}"
                f"</div>",
                unsafe_allow_html=True,
            )

    hdr_html = "<th>Day</th>" + "".join(
        f"<th>{p_code}<br><span style='font-size:0.74rem; font-weight:500;'>{p_disp}</span></th>"
        for p_code, _, _, p_disp in PERIOD_SLOTS
    )

    rows_html = []
    for d_code in DAYS_ORDER:
        day_slots = tt_data.get(d_code, [])
        cells = [f"<td class='tt-day-cell'>{d_code}</td>"]
        for idx_s, (p_code, _, _, _) in enumerate(PERIOD_SLOTS):
            subj_txt, fac_txt = day_slots[idx_s] if idx_s < len(day_slots) else ("Free", "")
            is_live_cell = (d_code == active_day and active_period == p_code)
            blink_cls = " tt-live-blink" if is_live_cell else ""

            if p_code == "LUNCH":
                cells.append(f"<td class='tt-slot-lunch{blink_cls}'>🍽️ LUNCH</td>")
            elif subj_txt == "Free":
                cells.append(f"<td class='tt-slot tt-slot-free{blink_cls}'><span style='color:{text_muted};'>Free</span></td>")
            else:
                live_tag = "<div style='font-size:0.68rem; font-weight:800; color:#FF1E27;'>● LIVE</div>" if is_live_cell else ""
                fac_line = f"<div style='font-size:0.76rem; color:{text_muted};'>{fac_txt}</div>" if fac_txt else ""
                cells.append(
                    f"<td class='tt-slot{blink_cls}'>{live_tag}"
                    f"<div style='font-weight:700;'>{subj_txt}</div>{fac_line}</td>"
                )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    st.markdown(
        f"<div class='tt-grid-wrap'><table class='tt-table'><thead><tr>{hdr_html}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table></div>",
        unsafe_allow_html=True
    )


def _normalize_sec_code(val: str) -> str:
    return re.sub(r"(?i)\bsection\b", "", str(val or "")).replace("-", "").replace(" ", "").strip().upper()


def get_today_section_slots_from_grid(fac_tt, section_label, section_tt=None, fac_name="", subj_code=""):
    sec_target = _normalize_sec_code(section_label)
    now_ist = get_now_ist()
    today_code = DAY_FULL_TO_SHORT.get(now_ist.strftime("%A"), "Mon")
    day_row = fac_tt.get(today_code, []) if fac_tt else []
    slots_found = []

    for idx_p, sec_val in enumerate(day_row):
        if idx_p >= len(PERIOD_SLOTS):
            break
        p_code, _, _, p_disp = PERIOD_SLOTS[idx_p]
        if p_code == "LUNCH":
            continue
        if _normalize_sec_code(sec_val) == sec_target:
            slot_str = f"{p_code} ({p_disp})"
            if slot_str not in slots_found:
                slots_found.append(slot_str)

    if not slots_found and section_tt:
        sec_day_slots = section_tt.get(today_code, [])
        fac_last = str(fac_name or "").split()[-1].lower()
        sub_short = str(subj_code or "").strip().lower()
        for idx_p, item in enumerate(sec_day_slots):
            if idx_p >= len(PERIOD_SLOTS):
                break
            p_code, _, _, p_disp = PERIOD_SLOTS[idx_p]
            if p_code == "LUNCH":
                continue
            s_txt, f_txt = item if isinstance(item, (list, tuple)) and len(item) >= 2 else ("", "")
            fac_match = bool(fac_last and fac_last in str(f_txt).lower())
            sub_match = bool(sub_short and sub_short in str(s_txt).lower())
            if fac_match or sub_match:
                slot_str = f"{p_code} ({p_disp})"
                if slot_str not in slots_found:
                    slots_found.append(slot_str)

    return today_code, slots_found


def render_faculty_timetable_view(fac_code, fac_name, fac_tt):
    now_ist = get_now_ist()
    today_code = DAY_FULL_TO_SHORT.get(now_ist.strftime("%A"), "Mon")
    active_period = get_active_period_code(now_ist)

    st.subheader(f"🗓️ Faculty Lecture Timetable — {fac_name} ({fac_code})")
    st.caption(f"Today is {today_code} ({now_ist.strftime('%I:%M %p IST')}). Appointed section slots are shown below.")

    today_row = fac_tt.get(today_code, [])
    today_lectures = []
    for idx_p, sec_val in enumerate(today_row):
        if sec_val not in ("Free", "LUNCH") and idx_p < len(PERIOD_SLOTS):
            p_code, _, _, p_disp = PERIOD_SLOTS[idx_p]
            now_badge = " 🔴 **CURRENT CLASS**" if p_code == active_period else ""
            sec_clean = sec_val if sec_val.startswith("Section") else f"Section {sec_val}"
            today_lectures.append(f"- **{p_code} ({p_disp})** → **{sec_clean}**{now_badge}")

    if today_lectures:
        st.markdown(f"#### 📌 Today's ({today_code}) Classes")
        for item_txt in today_lectures:
            st.markdown(item_txt)
    else:
        st.info(f"No scheduled classes on {today_code}.")

    st.divider()
    st.markdown("#### Full Weekly Lecture Grid")
    hdr_html = "<th>Day</th>" + "".join(
        f"<th>{p_code}<br><span style='font-size:0.74rem; font-weight:500;'>{p_disp}</span></th>"
        for p_code, _, _, p_disp in PERIOD_SLOTS
    )
    rows_html = []
    for d_code in DAYS_ORDER:
        d_slots = fac_tt.get(d_code, [])
        cells = [f"<td class='tt-day-cell'>{d_code}</td>"]
        for idx_p, (p_code, _, _, _) in enumerate(PERIOD_SLOTS):
            val = d_slots[idx_p] if idx_p < len(d_slots) else "Free"
            is_now = (d_code == today_code and p_code == active_period and val not in ("Free", "LUNCH"))
            blink_cls = " tt-live-blink" if is_now else ""
            if val == "LUNCH":
                cells.append("<td class='tt-slot-lunch'>🍽️ LUNCH</td>")
            elif val == "Free":
                cells.append(f"<td class='tt-slot tt-slot-free'><span style='color:{text_muted};'>Free</span></td>")
            else:
                sec_disp = val if val.startswith("Section") else f"Section {val}"
                cells.append(
                    f"<td class='tt-slot{blink_cls}'><div style='font-weight:800; color:{accent_color};'>{sec_disp}</div></td>"
                )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    st.markdown(
        f"<div class='tt-grid-wrap'><table class='tt-table'><thead><tr>{hdr_html}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody></table></div>",
        unsafe_allow_html=True
    )


def render_avatar_html(profile, size=115):
    if profile["avatar_mode"] == "Upload My Photo" and profile["photo_blob"]:
        raw_blob = bytes(profile["photo_blob"])
        b64_img = base64.b64encode(raw_blob).decode("utf-8")
        img_src = f"data:image/png;base64,{b64_img}"
    else:
        svg_code = DOODLES.get(profile["doodle_name"], list(DOODLES.values())[0]).strip()
        b64_svg = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        img_src = f"data:image/svg+xml;base64,{b64_svg}"

    return f"""
    <div style="display:flex; justify-content:center; margin-bottom:10px;">
        <img src="{img_src}" style="width:{size}px; height:{size}px; border-radius:50%;
             object-fit:cover; border:3px solid {accent_color}; box-shadow:0 4px 10px rgba(0,0,0,0.15);" />
    </div>
    """


def build_monthly_calendar_html(logs, code, name, title_prefix="Official Attendance Calendar"):
    date_status_map = {}
    months_set = set()
    pres_count = 0
    abs_count = 0

    for d_str, status in logs:
        try:
            dt = datetime.strptime(d_str, "%Y-%m-%d").date()
            date_status_map[dt] = status
            months_set.add((dt.year, dt.month))
            if status == "Present":
                pres_count += 1
            elif status == "Absent":
                abs_count += 1
        except ValueError:
            continue

    if not months_set:
        today = date.today()
        months_set.add((today.year, today.month))

    sorted_months = sorted(months_set)
    weekday_headers = "".join(
        f'<div class="cal-weekday">{day}</div>'
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )

    month_cards = []
    for yr, mo in sorted_months:
        month_title = f"{calendar.month_name[mo]} {yr}"
        cal_matrix = calendar.monthcalendar(yr, mo)
        day_cells = []
        for week in cal_matrix:
            for day_num in week:
                if day_num == 0:
                    day_cells.append('<div class="cal-day-empty"></div>')
                else:
                    curr_dt = date(yr, mo, day_num)
                    st_val = date_status_map.get(curr_dt)
                    if st_val == "Present":
                        day_cells.append(f'<div class="cal-day-present" title="{curr_dt.strftime("%d %b %Y")} — Present">{day_num}</div>')
                    elif st_val == "Absent":
                        day_cells.append(f'<div class="cal-day-absent" title="{curr_dt.strftime("%d %b %Y")} — Absent">{day_num}</div>')
                    else:
                        day_cells.append(f'<div class="cal-day-neutral">{day_num}</div>')

        month_cards.append(
            f'<div class="cal-month-card">'
            f'<div class="cal-month-title">🗓️ {month_title}</div>'
            f'<div class="cal-grid">{weekday_headers}{"".join(day_cells)}</div>'
            f'</div>'
        )

    return (
        f'<div class="cal-drawer-wrapper">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">'
        f'<div style="font-size:1.05rem; font-weight:700; color:{accent_color};">'
        f'📅 {title_prefix} &mdash; {code} ({name})'
        f'</div>'
        f'<div style="font-size:0.88rem;">'
        f'<span style="display:inline-block; width:11px; height:11px; background:#22C55E; border-radius:3px; margin-right:5px;"></span>'
        f'<b style="color:#16A34A;">Present: {pres_count}</b>'
        f'&nbsp;&nbsp;&nbsp;'
        f'<span style="display:inline-block; width:11px; height:11px; background:#EF4444; border-radius:3px; margin-right:5px;"></span>'
        f'<b style="color:#DC2626;">Absent: {abs_count}</b>'
        f'</div>'
        f'</div>'
        f'<div class="cal-months-flex">{"".join(month_cards)}</div>'
        f'</div>'
    )


def render_student_self_attendance_manager(df):
    st.markdown(
        f'<div class="self-att-panel">'
        f'<div style="font-size:1.12rem; font-weight:700; color:{accent_color};">'
        f'📝 Student Self Attendance Mini-Manager'
        f'</div>'
        f'<div style="color:{text_muted}; font-size:0.9rem; margin-top:2px;">'
        f'Track your own attendance across your active semester subjects and inspect your personal calendar.'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    self_date = st.date_input("Select Class Date for Self Attendance", value=date.today(), key="st_self_att_date")
    rec_ids = [int(r) for r in df["record_id"].tolist()]
    stats_map = fetch_all_self_attendance_stats(rec_ids)

    for _, row in df.iterrows():
        rec_id = int(row["record_id"])
        code = row["code"]
        name = row["name"]
        s_att, s_tot = stats_map.get(rec_id, (0, 0))
        s_pct = (s_att / s_tot * 100) if s_tot > 0 else 0.0
        is_open = (st.session_state.self_open_date_record == rec_id)

        sc1, sc2, sc3, sc4, sc5 = st.columns([2.5, 1.3, 0.95, 0.95, 1.25])
        with sc1:
            st.markdown(
                f"<div style='padding-top:8px;'><b>{code}</b> &mdash; {name}</div>",
                unsafe_allow_html=True
            )
        with sc2:
            st.markdown(
                f"<div style='padding-top:8px; font-weight:700;'>{s_att}/{s_tot} ({s_pct:.1f}%)</div>",
                unsafe_allow_html=True
            )
        with sc3:
            st.markdown('<span class="tag-present"></span>', unsafe_allow_html=True)
            if st.button("✅ Present", key=f"self_pres_{rec_id}", width="stretch"):
                mark_self_attendance(rec_id, "Present", self_date)
                st.rerun()
        with sc4:
            st.markdown('<span class="tag-absent"></span>', unsafe_allow_html=True)
            if st.button("❌ Absent", key=f"self_abs_{rec_id}", width="stretch"):
                mark_self_attendance(rec_id, "Absent", self_date)
                st.rerun()
        with sc5:
            st.markdown('<span class="tag-dates"></span>', unsafe_allow_html=True)
            cal_lbl = "🔼 Hide Cal" if is_open else "📅 Calendar"
            if st.button(cal_lbl, key=f"self_cal_{rec_id}", width="stretch"):
                st.session_state.self_open_date_record = None if is_open else rec_id
                st.rerun()

        if is_open:
            s_logs = fetch_self_record_logs(rec_id)
            st.markdown(
                build_monthly_calendar_html(s_logs, code, name, title_prefix="Self Attendance Calendar"),
                unsafe_allow_html=True
            )


def render_student_attendance_chart(summary_df, target_pct=75):
    if "open_date_record" not in st.session_state:
        st.session_state.open_date_record = None

    legend_html = (
        f'<div style="display:flex; justify-content:space-between; align-items:center; '
        f'flex-wrap:wrap; gap:8px; margin-bottom:14px; font-size:0.9rem;">'
        f'<div>'
        f'<span style="display:inline-block; width:12px; height:12px; background:#22C55E; border-radius:50%; margin-right:6px; box-shadow:0 0 8px #22C55E;"></span>'
        f'<b>Safe (&ge; {target_pct}%)</b>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;'
        f'<span style="display:inline-block; width:12px; height:12px; background:#EF4444; border-radius:50%; margin-right:6px; box-shadow:0 0 8px #EF4444;"></span>'
        f'<b>Shortage (&lt; {target_pct}%)</b>'
        f'</div>'
        f'<div style="color:{text_muted};">Read-only official ERP records &bull; Click <b>📅 View Calendar</b> to inspect dates</div>'
        f'</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    for _, row in summary_df.iterrows():
        rec_id = int(row["record_id"])
        att_now = int(row["Attended"])
        tot_now = int(row["Total"])
        pct = float(row["Percentage (%)"])
        is_safe = pct >= target_pct
        is_open = (st.session_state.open_date_record == rec_id)

        card_class = "att-card-green" if is_safe else "att-card-red"
        bar_grad = "linear-gradient(90deg, #16A34A, #22C55E)" if is_safe else "linear-gradient(90deg, #DC2626, #EF4444)"
        bar_glow = "rgba(34, 197, 94, 0.55)" if is_safe else "rgba(239, 68, 68, 0.55)"
        text_color = "#15803D" if (is_safe and is_light_ui) else ("#4ADE80" if is_safe else ("#B91C1C" if is_light_ui else "#F87171"))
        bar_width = max(min(pct, 100.0), 10.0)
        icon = "✅" if is_safe else "⚠️"

        card_html = (
            f'<div class="{card_class}">'
            f'<div class="bar-track-bg">'
            f'<div style="width:{bar_width}%; height:100%; background:{bar_grad}; border-radius:999px; '
            f'box-shadow:0 0 16px {bar_glow}; display:flex; align-items:center; justify-content:flex-end; '
            f'padding-right:14px; color:#FFFFFF; font-weight:700; font-size:0.92rem; box-sizing:border-box;">'
            f'{pct:.2f}%'
            f'</div>'
            f'<div style="position:absolute; left:{target_pct}%; top:0; bottom:0; width:2px; '
            f'border-left:2px dashed rgba(148,163,184,0.75);"></div>'
            f'</div>'
            f'<div style="margin-top:8px; font-size:0.98rem; font-weight:700; color:{text_main};">'
            f'{row["Code"]} &mdash; {row["Subject Name"]} '
            f'<span style="font-weight:400; color:{text_muted}; font-size:0.86rem;">({att_now}/{tot_now} classes)</span>'
            f'</div>'
            f'<div style="margin-top:3px; font-size:0.9rem; font-weight:600; color:{text_color};">'
            f'{icon} {row["Smart Recommendation"]}'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        c_btn, _ = st.columns([1.45, 5.55])
        with c_btn:
            st.markdown('<span class="tag-dates"></span>', unsafe_allow_html=True)
            toggle_label = "🔼 Hide Calendar" if is_open else "📅 View Calendar"
            if st.button(toggle_label, key=f"st_cal_{rec_id}", width="stretch"):
                st.session_state.open_date_record = None if is_open else rec_id
                st.rerun()

        if is_open:
            logs = fetch_record_logs(rec_id)
            st.markdown(build_monthly_calendar_html(logs, row["Code"], row["Subject Name"]), unsafe_allow_html=True)

        st.markdown('<div style="margin-bottom:10px;"></div>', unsafe_allow_html=True)


@st.fragment(run_every=5)
def live_student_attendance_panel(student_id: int, section_name: str):
    df_live = fetch_student_records(student_id)
    if df_live.empty:
        st.info("No subjects assigned to your profile yet. Contact your Admin.")
        return

    total_att = df_live["attended"].sum()
    total_cls = df_live["total"].sum()
    overall_pct = (total_att / total_cls * 100) if total_cls > 0 else 0.0
    shortage_count = sum(1 for _, r in df_live.iterrows() if (r["total"] > 0 and (r["attended"] / r["total"]) < 0.75))

    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Attendance", f"{overall_pct:.2f}%", f"{total_att}/{total_cls} Classes")
    c2.metric("AKTU Minimum Requirement", "75.00%", "Mandatory for End-Sem")
    c3.metric("Subjects in Shortage", f"{shortage_count} Subject(s)", delta_color="inverse")

    st.divider()

    records = []
    for _, row in df_live.iterrows():
        pct, status, action = analyze_attendance(row["attended"], row["total"])
        records.append({
            "record_id": row["record_id"],
            "Code": row["code"],
            "Subject Name": row["name"],
            "Attended": row["attended"],
            "Total": row["total"],
            "Percentage (%)": round(pct, 2),
            "Status": status,
            "Smart Recommendation": action
        })
    summary_df = pd.DataFrame(records)

    hdr_col, self_btn_col = st.columns([4.8, 1.5])
    with hdr_col:
        st.markdown("#### Horizontal Attendance Bar Chart (75% Target Analysis)")
    with self_btn_col:
        self_lbl = "🔼 Close Self Attendance" if st.session_state.st_self_att_open else "📝 Self Attendance"
        if st.button(self_lbl, key="st_self_att_toggle", width="stretch"):
            st.session_state.st_self_att_open = not st.session_state.st_self_att_open
            st.rerun()

    if st.session_state.st_self_att_open:
        render_student_self_attendance_manager(df_live)

    render_student_attendance_chart(summary_df, target_pct=75)

    st.divider()
    st.markdown("#### Detailed Official Attendance Summary")
    st.markdown(render_clean_table(summary_df.drop(columns=["record_id"])), unsafe_allow_html=True)


# -------------------- ONE-TIME INITIALIZATION & TOP HEADER BAR --------------------
ensure_db_initialized(3)
render_top_header_bar()


# ==================== LOGIN & VERIFIED PASSWORD RESET PORTAL ====================
if st.session_state.auth_user is None:
    st.markdown(f"""
    <div class="login-hero">
        <h1 style="margin:0; color:{accent_color} !important;">🎓 KCC Institute of Technology and Management</h1>
        <p style="font-size:1.15rem; color:{text_muted}; margin:6px 0 0 0;">
            Smart AKTU Academic ERP Portal &bull; SHA-256 Secured Role-Based Attendance &amp; SGPA System
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_login, col_demo = st.columns([1.15, 1])

    with col_login:
        if not st.session_state.show_forgot_pw:
            st.subheader("🔐 ERP Portal Sign In")
            selected_role = st.radio(
                "Select Your Persona Role",
                ["Student", "Faculty", "Admin"],
                horizontal=True
            )

            placeholder_map = {
                "Student": "Enter AKTU Roll No (e.g., 2504920100346)",
                "Faculty": "Enter Faculty ID (FAC001, FAC002, FAC003)",
                "Admin": "Enter Admin Username (admin)"
            }

            with st.form("erp_login_form"):
                login_id = st.text_input("User ID / Roll Number", placeholder=placeholder_map[selected_role])
                login_pw = st.text_input("Password", type="password", placeholder="Enter password")
                submit_login = st.form_submit_button("🚀 Login to ERP Portal", width="stretch")

                if submit_login:
                    user_obj = authenticate_user(selected_role, login_id, login_pw)
                    if user_obj:
                        complete_login(user_obj)
                    else:
                        st.error("Invalid credentials for the selected role.")

            if st.button("🔑 Forgot Password? Verify & Reset", key="open_forgot_btn", width="stretch"):
                st.session_state.show_forgot_pw = True
                st.rerun()

        else:
            st.subheader("🔑 Verified Password Recovery")
            st.caption("Enter your User ID, Registered Full Name, and 4-Digit Recovery PIN to reset your password.")
            reset_role = st.radio(
                "Select Account Role to Reset",
                ["Student", "Faculty", "Admin"],
                horizontal=True,
                key="reset_role_radio"
            )

            id_hint = {
                "Student": "AKTU Roll Number (e.g., 2504920100346)",
                "Faculty": "Faculty ID (e.g., FAC001)",
                "Admin": "Admin Username (admin)"
            }[reset_role]

            name_hint = {
                "Student": "Registered Full Name (e.g., Manas Srivastav)",
                "Faculty": "Registered Faculty Name (e.g., Mr. Vishal)",
                "Admin": "Admin Name (KCC ERP Administrator)"
            }[reset_role]

            with st.form("verified_reset_form"):
                r_id = st.text_input(id_hint)
                r_name = st.text_input(name_hint)
                r_pin = st.text_input("4-Digit Recovery PIN (Default: 1234 | Admin: 9999)", type="password", max_chars=4)
                r_new_pw = st.text_input("New Password", type="password")
                r_conf_pw = st.text_input("Confirm New Password", type="password")

                if st.form_submit_button("✅ Verify Identity & Reset Password", width="stretch"):
                    if r_new_pw != r_conf_pw:
                        st.error("New password and confirmation do not match.")
                    else:
                        ok, msg = verify_and_reset_password(reset_role, r_id, r_name, r_pin, r_new_pw)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

            if st.button("⬅️ Back to Login", key="back_to_login_btn", width="stretch"):
                st.session_state.show_forgot_pw = False
                st.rerun()

    with col_demo:
        st.subheader("⚡ Quick Persona Demo Access")
        st.caption("One-click login for live viva")

        if st.button("🎓 Student — Manas Srivastav (Section B-3)", key="demo_st1", width="stretch"):
            complete_login(quick_demo_login("Student", "2504920100346"))

        if st.button("🎓 Student — Ananya Singh (Section B-2)", key="demo_st2", width="stretch"):
            complete_login(quick_demo_login("Student", "2504920100201"))

        if st.button("👨‍🏫 Faculty — Mr. Vishal (Python | B-2, B-3, B-4, B-6)", key="demo_fac1", width="stretch"):
            complete_login(quick_demo_login("Faculty", "FAC001"))

        if st.button("👩‍🏫 Faculty — Arya Devi (COA | B-2, B-3, B-4, B-6)", key="demo_fac2", width="stretch"):
            complete_login(quick_demo_login("Faculty", "FAC002"))

        if st.button("👨‍🏫 Faculty — Mr. Satyam (DSTL | B-2, B-3, B-4, B-6)", key="demo_fac3", width="stretch"):
            complete_login(quick_demo_login("Faculty", "FAC003"))

        if st.button("🛡️ Admin — Full KCC ERP Control", key="demo_adm", width="stretch"):
            complete_login(quick_demo_login("Admin", "admin"))

    st.stop()


# ==================== AUTHENTICATED ERP WORKSPACE ====================
user = st.session_state.auth_user
role = user["role"]


# =====================================================================
# PERSONA 1: STUDENT PORTAL
# =====================================================================
if role == "Student":
    student = fetch_student_by_id(user["id"])

    with st.sidebar:
        st.markdown("### 🧑‍🎓 Student Profile")
        st.markdown(render_avatar_html(student, size=120), unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="text-align:center; padding-bottom:10px;">
                <h4 style="margin:0;">{student['name']}</h4>
                <p style="margin:2px 0; color:{text_muted}; font-size:0.9rem;">Roll No: <b>{student['roll_no']}</b></p>
                <p style="margin:2px 0; font-size:0.88rem;">{student['branch']} &bull; <b>{student['section']}</b></p>
                <span style="background:{code_bg}; color:{accent_color}; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:700;">
                    {student['semester']}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        with st.expander("🎨 Customize Avatar & Doodle", expanded=False):
            st.caption("Official Name, Roll No & Section are locked by Admin.")
            avatar_mode = st.radio(
                "Avatar Option",
                ["Pre-built Doodle", "Upload My Photo"],
                index=0 if student["avatar_mode"] == "Pre-built Doodle" else 1,
                label_visibility="collapsed"
            )
            doodle_keys = list(DOODLES.keys())
            d_idx = doodle_keys.index(student["doodle_name"]) if student["doodle_name"] in doodle_keys else 0
            selected_doodle = student["doodle_name"]
            uploaded_bytes = student["photo_blob"]

            if avatar_mode == "Pre-built Doodle":
                selected_doodle = st.selectbox("Pick a Cute & Cool Doodle", doodle_keys, index=d_idx)
                preview_svg = base64.b64encode(DOODLES[selected_doodle].strip().encode("utf-8")).decode("utf-8")
                st.markdown(f'<div style="text-align:center;"><img src="data:image/svg+xml;base64,{preview_svg}" width="80"/></div>', unsafe_allow_html=True)
            else:
                uploaded_file = st.file_uploader("Upload Photo (JPG / PNG)", type=["jpg", "jpeg", "png"])
                if uploaded_file is not None:
                    uploaded_bytes = uploaded_file.read()

            if st.button("💾 Save Avatar", width="stretch"):
                update_student_avatar_and_cgpa(
                    student["id"], student["prev_credits"], student["prev_cgpa"],
                    avatar_mode, selected_doodle, uploaded_bytes
                )
                st.success("Avatar updated!")
                st.rerun()

        render_sidebar_password_changer("Student", student["id"], student["recovery_pin"])

        st.divider()
        if st.button("🚪 Logout", key="st_logout", width="stretch"):
            logout_user()

    st.title("🎓 Smart AKTU CGPA, Credit & Attendance Manager")
    st.markdown(
        f'<p style="font-size:1.25rem; font-weight:500; color:{text_muted}; margin-top:-10px; margin-bottom:18px;">'
        f'Welcome, <strong style="color:{text_main};">{student["name"]}</strong> &nbsp;|&nbsp; '
        f'<span style="color:{accent_color}; font-weight:700;">{student["section"]}</span> &nbsp;|&nbsp; KCC Institute of Technology and Management'
        f'</p>',
        unsafe_allow_html=True
    )

    if "st_page" not in st.session_state:
        st.session_state.st_page = "attendance"

    nav1, nav2, nav3 = st.columns([1.25, 1.45, 1.25])
    with nav1:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.st_page == "attendance":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("📊 My Attendance & 75% Predictor", key="st_nav_att", width="stretch"):
            if st.session_state.st_page != "attendance":
                st.session_state.st_page = "attendance"
                st.rerun()

    with nav2:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.st_page == "sgpa":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("🏆 Show Result (SGPA & CGPA)", key="st_nav_sgpa", width="stretch"):
            if st.session_state.st_page != "sgpa":
                st.session_state.st_page = "sgpa"
                st.rerun()

    with nav3:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.st_page == "timetable":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("🗓️ Class Timetable", key="st_nav_tt", width="stretch"):
            if st.session_state.st_page != "timetable":
                st.session_state.st_page = "timetable"
                st.rerun()

    if st.session_state.st_page == "attendance":
        st.subheader(f"Subject-Wise Attendance ({student['section']})")
        live_student_attendance_panel(student["id"], student["section"])

    elif st.session_state.st_page == "sgpa":
        st.subheader(f"My University Result — {student['name']} ({student['roll_no']})")
        st_res_df = fetch_student_semester_results(student["roll_no"])

        if st_res_df.empty:
            st.info(f"No published semester result found for Roll No {student['roll_no']} yet.")
        else:
            sem_filter_opt = st.selectbox(
                "Show Result by Semester",
                ["All Semesters", "Semester 1", "Semester 2"],
                key="erp_res_sem_picker",
            )
            head_r = st_res_df.iloc[0]
            overall_cgpa_val = float(head_r["cgpa"])
            m_a, m_b, m_c = st.columns(3)
            m_a.metric("Student & Roll No", f"{head_r['student_name']}", f"Roll: {student['roll_no']}")
            m_b.metric("Result Status", f"{head_r['result_status']}", f"Branch: {head_r['branch']}")
            m_c.metric("Overall CGPA", f"{overall_cgpa_val:.2f}", f"Equivalent %: {overall_cgpa_val * 10:.1f}%")

            sem_list = ["Semester 1", "Semester 2"] if sem_filter_opt == "All Semesters" else [sem_filter_opt]
            for s_name in sem_list:
                sub_sem_df = st_res_df[st_res_df["semester"] == s_name]
                if not sub_sem_df.empty:
                    sem_sgpa_val = float(sub_sem_df.iloc[0]["sgpa"])
                    st.markdown(f"##### 📘 {s_name} — SGPA: `{sem_sgpa_val:.2f}`")
                    disp_res = sub_sem_df[["subject_name", "credits", "marks_100", "grade"]].rename(columns={
                        "subject_name": "Subject",
                        "credits": "Credits",
                        "marks_100": "Marks /100",
                        "grade": "Grade",
                    })
                    st.markdown(render_clean_table(disp_res), unsafe_allow_html=True)

    elif st.session_state.st_page == "timetable":
        render_student_timetable_section(student["section"])


# =====================================================================
# PERSONA 2: FACULTY PORTAL
# =====================================================================
elif role == "Faculty":
    conn = get_connection()
    fac_info = read_df("SELECT * FROM faculty WHERE id = ?", conn, params=(user["id"],)).iloc[0]
    assigned_df = read_df("""
        SELECT fa.id AS assign_id, fa.section, fa.appointed_at, sc.id AS subject_id, sc.code, sc.name
        FROM faculty_assignments fa
        JOIN subject_catalog sc ON fa.subject_id = sc.id
        WHERE fa.faculty_id = ?
        ORDER BY fa.section, sc.code
    """, conn, params=(user["id"],))
    eff_fac_tt = get_effective_faculty_timetable(fac_info["faculty_code"], conn)
    sec_tt_cache = {
        sec_n: get_effective_section_timetable(sec_n, conn)
        for sec_n in assigned_df["section"].unique()
    } if not assigned_df.empty else {}
    conn.close()

    with st.sidebar:
        st.markdown("### 👨‍🏫 Faculty Profile")
        st.markdown(
            f"""
            <div style="background:{code_bg}; border-radius:16px; padding:16px; text-align:center;">
                <div style="font-size:2.6rem;">👨‍🏫</div>
                <h4 style="margin:6px 0 2px 0;">{fac_info['name']}</h4>
                <p style="margin:0; color:{text_muted}; font-size:0.88rem;">ID: <b>{fac_info['faculty_code']}</b></p>
                <p style="margin:4px 0; font-size:0.85rem;">{fac_info['designation']}</p>
                <span style="background:{card_bg}; color:{accent_color}; padding:3px 10px; border-radius:12px; font-size:0.78rem; font-weight:700;">
                    {fac_info['department']}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()
        st.markdown("**Appointed Sections & Today's Time:**")
        if assigned_df.empty:
            st.warning("No sections appointed yet.")
        else:
            for _, arow in assigned_df.iterrows():
                t_day, t_slots = get_today_section_slots_from_grid(
                    eff_fac_tt,
                    arow["section"],
                    section_tt=sec_tt_cache.get(arow["section"]),
                    fac_name=fac_info["name"],
                    subj_code=arow["code"],
                )
                time_summary = ", ".join(t_slots) if t_slots else "Free today"
                st.markdown(
                    f"- **{arow['section']}** — `{arow['code']}` ({arow['name']})<br>"
                    f"<span style='font-size:0.8rem; color:{accent_color}; font-weight:600;'>🕒 Today ({t_day}): {time_summary}</span>",
                    unsafe_allow_html=True
                )

        st.divider()
        render_sidebar_password_changer("Faculty", int(fac_info["id"]), fac_info["recovery_pin"])

        st.divider()
        if st.button("🚪 Logout", key="fac_logout", width="stretch"):
            logout_user()

    st.title("👨‍🏫 Faculty Attendance & Class Management Portal")
    st.markdown(
        f'<p style="font-size:1.2rem; font-weight:500; color:{text_muted}; margin-top:-10px; margin-bottom:18px;">'
        f'Welcome, <strong style="color:{text_main};">{fac_info["name"]}</strong> &nbsp;|&nbsp; KCC Institute of Technology and Management'
        f'</p>',
        unsafe_allow_html=True
    )

    if assigned_df.empty:
        st.warning("You have not been appointed to any section yet. Please contact the Admin.")
    else:
        if "fac_page" not in st.session_state:
            st.session_state.fac_page = "mark"

        fnav1, fnav2, fnav3 = st.columns([1.25, 1.35, 1.35])
        with fnav1:
            st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
            if st.session_state.fac_page == "mark":
                st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
            if st.button("📝 Mark Class Attendance", key="fac_nav_mark", width="stretch"):
                if st.session_state.fac_page != "mark":
                    st.session_state.fac_page = "mark"
                    st.rerun()

        with fnav2:
            st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
            if st.session_state.fac_page == "shortage":
                st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
            if st.button("⚠️ Section Shortage Report", key="fac_nav_short", width="stretch"):
                if st.session_state.fac_page != "shortage":
                    st.session_state.fac_page = "shortage"
                    st.rerun()

        with fnav3:
            st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
            if st.session_state.fac_page == "timetable":
                st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
            if st.button("🗓️ My Lecture Timetable", key="fac_nav_tt", width="stretch"):
                if st.session_state.fac_page != "timetable":
                    st.session_state.fac_page = "timetable"
                    st.rerun()

        if st.session_state.fac_page == "timetable":
            render_faculty_timetable_view(fac_info["faculty_code"], fac_info["name"], eff_fac_tt)
        else:
            options_labels = [
                f"{r['section']} | {r['code']} - {r['name']}"
                for _, r in assigned_df.iterrows()
            ]
            sel_idx = st.selectbox("Select Appointed Section & Subject", range(len(options_labels)), format_func=lambda i: options_labels[i])
            chosen = assigned_df.iloc[sel_idx]
            target_section = chosen["section"]
            target_sub_id = int(chosen["subject_id"])
            appointed_at_str = str(chosen.get("appointed_at", "2026-08-01"))[:10]

            roster_df = fetch_faculty_roster_since_appointment(target_section, target_sub_id, appointed_at_str)

            if st.session_state.fac_page == "mark":
                st.subheader(f"Roster: {target_section} — {chosen['code']} ({chosen['name']}) [{len(roster_df)} Students]")
                st.caption(f"Appointed on: {appointed_at_str} • Classes & logs counted from appointment date onward (starts at 0/0 until marked).")
                class_date = st.date_input("Lecture Date", value=date.today(), key="fac_lec_date")

                if roster_df.empty:
                    st.info("No students enrolled in this section yet.")
                else:
                    st.markdown("#### Quick Individual Marking (Instant Update)")
                    for _, srow in roster_df.iterrows():
                        rec_id = int(srow["record_id"])
                        att = int(srow["attended"])
                        tot = int(srow["total"])
                        pct = (att / tot * 100) if tot > 0 else 0.0
                        is_safe = pct >= 75.0
                        badge_color = "#15803D" if (is_safe and is_light_ui) else ("#4ADE80" if is_safe else ("#B91C1C" if is_light_ui else "#F87171"))

                        r_c1, r_c2, r_c3, r_c4 = st.columns([2.6, 1.3, 1.0, 1.0])
                        with r_c1:
                            st.markdown(
                                f"<div style='padding-top:8px;'><b>{srow['student_name']}</b> "
                                f"<span style='color:{text_muted};'>({srow['roll_no']})</span></div>",
                                unsafe_allow_html=True
                            )
                        with r_c2:
                            st.markdown(
                                f"<div style='padding-top:8px; font-weight:700; color:{badge_color};'>"
                                f"{att}/{tot} ({pct:.1f}%)</div>",
                                unsafe_allow_html=True
                            )
                        with r_c3:
                            st.markdown('<span class="tag-present"></span>', unsafe_allow_html=True)
                            if st.button("✅ Present", key=f"fpres_{rec_id}", width="stretch"):
                                mark_attendance_record(rec_id, "Present", class_date)
                                st.rerun()
                        with r_c4:
                            st.markdown('<span class="tag-absent"></span>', unsafe_allow_html=True)
                            if st.button("❌ Absent", key=f"fabs_{rec_id}", width="stretch"):
                                mark_attendance_record(rec_id, "Absent", class_date)
                                st.rerun()

                    st.divider()

                    with st.expander("✏️ Edit Previous Attendance (Fix Mistaken Present / Absent on Any Date)", expanded=False):
                        st.caption("Select a student to correct their attendance status on any date marked under your appointment:")
                        edit_st_idx = st.selectbox(
                            "Choose Student to Edit",
                            range(len(roster_df)),
                            format_func=lambda i: f"{roster_df.iloc[i]['roll_no']} — {roster_df.iloc[i]['student_name']}",
                            key="fac_edit_st_select"
                        )
                        edit_rec_id = int(roster_df.iloc[edit_st_idx]["record_id"])
                        edit_st_name = roster_df.iloc[edit_st_idx]["student_name"]
                        st_logs = fetch_record_logs_with_ids(edit_rec_id, min_date_str=appointed_at_str)

                        if not st_logs:
                            st.info("No classes marked yet under this appointment (0 classes taken so far).")
                        else:
                            log_options = [
                                f"{d_str}  |  Currently: {'✅ Present' if st_v == 'Present' else '❌ Absent'}"
                                for _, d_str, st_v in st_logs
                            ]
                            sel_log_idx = st.selectbox(
                                f"Select Date Entry for {edit_st_name}",
                                range(len(log_options)),
                                format_func=lambda i: log_options[i],
                                key="fac_edit_log_select"
                            )
                            chosen_log_id, chosen_date_str, chosen_status = st_logs[sel_log_idx]
                            try:
                                parsed_dt = datetime.strptime(chosen_date_str, "%Y-%m-%d").date()
                            except ValueError:
                                parsed_dt = date.today()

                            ec1, ec2, ec3, ec4 = st.columns([1.3, 1.3, 1.1, 1.0])
                            with ec1:
                                updated_dt = st.date_input("Date", value=parsed_dt, key=f"ed_dt_{chosen_log_id}")
                            with ec2:
                                updated_status = st.selectbox(
                                    "Corrected Status",
                                    ["Present", "Absent"],
                                    index=0 if chosen_status == "Present" else 1,
                                    key=f"ed_st_{chosen_log_id}"
                                )
                            with ec3:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                if st.button("💾 Save Correction", key=f"ed_save_{chosen_log_id}", width="stretch"):
                                    edit_attendance_log_entry(
                                        chosen_log_id, edit_rec_id, updated_status, updated_dt.strftime("%Y-%m-%d")
                                    )
                                    st.success(f"Updated {edit_st_name} on {updated_dt.strftime('%d %b %Y')} to {updated_status}!")
                                    st.rerun()
                            with ec4:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                if st.button("🗑️ Remove Entry", key=f"ed_del_{chosen_log_id}", width="stretch"):
                                    delete_attendance_log_entry(chosen_log_id, edit_rec_id)
                                    st.warning(f"Removed mistaken entry on {chosen_date_str} for {edit_st_name}.")
                                    st.rerun()

                    st.divider()
                    st.markdown("#### Bulk Class Attendance Submission")
                    st.caption("Ticked students will be marked Present; unticked students will be marked Absent for the Lecture Date above.")
                    with st.form("bulk_att_form"):
                        bulk_choices = {}
                        for _, srow in roster_df.iterrows():
                            rec_id = int(srow["record_id"])
                            bulk_choices[rec_id] = st.checkbox(
                                f"{srow['roll_no']} — {srow['student_name']} (Present)",
                                value=True,
                                key=f"chk_{rec_id}"
                            )
                        if st.form_submit_button("📤 Submit Full Class Attendance", width="stretch"):
                            pres_cnt = sum(1 for v in bulk_choices.values() if v)
                            abs_cnt = len(bulk_choices) - pres_cnt
                            for rec_id, is_pres in bulk_choices.items():
                                mark_attendance_record(rec_id, "Present" if is_pres else "Absent", class_date)
                            st.success(
                                f"Logged {pres_cnt} Present and {abs_cnt} Absent for {target_section} on {class_date.strftime('%d %b %Y')}!"
                            )
                            st.rerun()

            elif st.session_state.fac_page == "shortage":
                st.subheader(f"Students Below 75% Attendance — {target_section} ({chosen['code']})")
                if not roster_df.empty:
                    report_rows = []
                    for _, srow in roster_df.iterrows():
                        att_val = int(srow["attended"])
                        tot_val = int(srow["total"])
                        pct, status, rec_txt = analyze_attendance(att_val, tot_val)
                        if pct < 75.0:
                            report_rows.append({
                                "Roll No": srow["roll_no"],
                                "Student Name": srow["student_name"],
                                "Attended": att_val,
                                "Total": tot_val,
                                "Percentage (%)": round(pct, 2),
                                "Status": status,
                                "Action Required": rec_txt
                            })
                    rep_df = pd.DataFrame(report_rows)
                    st.markdown(render_clean_table(rep_df), unsafe_allow_html=True)


# =====================================================================
# PERSONA 3: ADMIN PORTAL
# =====================================================================
elif role == "Admin":
    conn_adm = get_connection()
    adm_row = read_df("SELECT * FROM admin_settings WHERE id = 1", conn_adm).iloc[0]
    conn_adm.close()

    with st.sidebar:
        st.markdown("### 🛡️ Admin Control Center")
        st.markdown(
            f"""
            <div style="background:{code_bg}; border-radius:16px; padding:16px; text-align:center;">
                <div style="font-size:2.6rem;">🛡️</div>
                <h4 style="margin:6px 0 2px 0;">{adm_row['full_name']}</h4>
                <p style="margin:0; color:{text_muted}; font-size:0.85rem;">Full Institutional Access</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.divider()
        st.caption("Manage students across B-2, B-3, B-4 & B-6, appoint or remove faculty, reset user credentials, and export shortage reports.")

        render_sidebar_password_changer("Admin", 1, adm_row["recovery_pin"])

        st.divider()
        if st.button("🚪 Logout", key="adm_logout", width="stretch"):
            logout_user()

    st.title("🛡️ KCC Smart AKTU ERP — Admin Control Panel")
    st.markdown(
        f'<p style="font-size:1.2rem; font-weight:500; color:{text_muted}; margin-top:-10px; margin-bottom:18px;">'
        'Full Database Control &bull; SHA-256 Protected Accounts, Students, Faculty Appointments &amp; Analytics'
        '</p>',
        unsafe_allow_html=True
    )

    if "adm_page" not in st.session_state:
        st.session_state.adm_page = "overview"

    anav1, anav2, anav3, anav4 = st.columns(4)
    with anav1:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.adm_page == "overview":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("📊 Overview & Shortages", key="adm_nav_ov", width="stretch"):
            if st.session_state.adm_page != "overview":
                st.session_state.adm_page = "overview"
                st.rerun()

    with anav2:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.adm_page == "students":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("🎓 Manage Students", key="adm_nav_st", width="stretch"):
            if st.session_state.adm_page != "students":
                st.session_state.adm_page = "students"
                st.rerun()

    with anav3:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.adm_page == "faculty":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("👨‍🏫 Appoint Faculty", key="adm_nav_fac", width="stretch"):
            if st.session_state.adm_page != "faculty":
                st.session_state.adm_page = "faculty"
                st.rerun()

    with anav4:
        st.markdown('<span class="nav-pill-tag"></span>', unsafe_allow_html=True)
        if st.session_state.adm_page == "subjects":
            st.markdown('<span class="nav-active"></span>', unsafe_allow_html=True)
        if st.button("📚 Subject Catalog", key="adm_nav_sub", width="stretch"):
            if st.session_state.adm_page != "subjects":
                st.session_state.adm_page = "subjects"
                st.rerun()

    conn = get_connection()

    if st.session_state.adm_page == "overview":
        st.subheader("Department-Wide Analytics & 75% Shortage Monitor")
        st_count = read_df("SELECT COUNT(*) AS c FROM students", conn).iloc[0]["c"]
        fac_count = read_df("SELECT COUNT(*) AS c FROM faculty", conn).iloc[0]["c"]
        sub_count = read_df("SELECT COUNT(*) AS c FROM subject_catalog", conn).iloc[0]["c"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Enrolled Students", f"{int(st_count)} (10 per Section)")
        m2.metric("Appointed Faculty", int(fac_count))
        m3.metric("Active AKTU Subjects", int(sub_count))

        st.divider()
        all_rec_df = read_df("""
            SELECT s.roll_no AS "Roll No", s.name AS "Student Name", s.section AS "Section",
                   sc.code AS "Subject Code", sc.name AS "Subject Name",
                   ss.attended AS "Attended", ss.total AS "Total",
                   ROUND(CAST(CASE WHEN ss.total > 0 THEN (ss.attended * 100.0 / ss.total) ELSE 0 END AS NUMERIC), 2) AS "Attendance (%)"
            FROM student_subjects ss
            JOIN students s ON ss.student_id = s.id
            JOIN subject_catalog sc ON ss.subject_id = sc.id
            ORDER BY s.section, s.roll_no, sc.code
        """, conn)

        sec_filter = st.selectbox("Filter by Section", ["All Sections", "Section B-2", "Section B-3", "Section B-4", "Section B-6"])
        if sec_filter != "All Sections":
            all_rec_df = all_rec_df[all_rec_df["Section"] == sec_filter]

        shortage_only = all_rec_df[all_rec_df["Attendance (%)"] < 75.0]
        st.markdown(f"#### ⚠️ Students Below 75% Threshold ({len(shortage_only)} Subject Entries)")
        st.markdown(render_clean_table(shortage_only), unsafe_allow_html=True)

        csv_data = shortage_only.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Shortage List (CSV)",
            data=csv_data,
            file_name="kcc_attendance_shortage_report.csv",
            mime="text/csv"
        )

    elif st.session_state.adm_page == "students":
        st.subheader("Student Directory & Enrollment (Sections B-2, B-3, B-4, B-6)")
        sec_view = st.selectbox("Filter Roster by Section", ["All Sections", "Section B-2", "Section B-3", "Section B-4", "Section B-6"], key="adm_st_sec_filter")
        students_df = read_df(
            '''SELECT id, roll_no AS "Roll No", name AS "Name", branch AS "Branch", section AS "Section", '•••••••• (SHA-256)' AS "Security", recovery_pin AS "Recovery PIN" FROM students ORDER BY section, roll_no''',
            conn
        )
        if sec_view != "All Sections":
            students_df = students_df[students_df["Section"] == sec_view]

        st.markdown(render_clean_table(students_df.drop(columns=["id"])), unsafe_allow_html=True)

        st.divider()
        c_add, c_reset, c_del = st.columns([1.3, 1.15, 0.95])

        with c_add:
            st.markdown("##### ➕ Register New Student")
            with st.form("adm_add_student", clear_on_submit=True):
                s1, s2 = st.columns(2)
                st_name = s1.text_input("Full Name")
                st_roll = s2.text_input("AKTU Roll Number")
                s3, s4 = st.columns(2)
                st_branch = s3.text_input("Branch", value="B.Tech CSE")
                st_sec = s4.selectbox("Section", ["Section B-2", "Section B-3", "Section B-4", "Section B-6"])
                s5, s6 = st.columns(2)
                st_pw = s5.text_input("Password", value="student123")
                st_pin = s6.text_input("4-Digit PIN", value="1234", max_chars=4)

                if st.form_submit_button("Register Student", width="stretch"):
                    if not st_name.strip() or not st_roll.strip():
                        st.error("Name and Roll Number are required.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO students (roll_no, password, recovery_pin, name, branch, section, semester, theme_pref)
                                VALUES (?, ?, ?, ?, ?, ?, '3rd Semester', 'kcc')
                            """, (st_roll.strip(), hash_password(st_pw), st_pin.strip() or "1234", st_name.strip(), st_branch.strip(), st_sec))
                            new_st_id = cur.lastrowid
                            cur.execute("SELECT id FROM subject_catalog")
                            for (sid,) in cur.fetchall():
                                cur.execute("INSERT INTO student_subjects (student_id, subject_id, attended, total, grade) VALUES (?, ?, 0, 0, 'A (80-89)')", (new_st_id, sid))
                            conn.commit()
                            st.success(f"Registered {st_name} ({st_roll}) in {st_sec} with SHA-256 security!")
                            st.rerun()
                        except Exception:
                            conn.raw_conn.rollback()
                            st.error("A student with this Roll Number already exists.")

        with c_reset:
            st.markdown("##### 🔑 Quick Reset Password & PIN")
            if not students_df.empty:
                rst_st_label = st.selectbox("Select Student", students_df["Roll No"] + " — " + students_df["Name"], key="adm_rst_st_box")
                target_st_rno = rst_st_label.split(" — ")[0]
                rc1, rc2 = st.columns(2)
                custom_st_pw = rc1.text_input("New Password", value="student123", key="adm_st_new_pw")
                custom_st_pin = rc2.text_input("New 4-Digit PIN", value="1234", max_chars=4, key="adm_st_new_pin")

                if st.button("🔑 Save Custom Password & PIN", key="adm_st_custom_rst", width="stretch"):
                    ok, msg = admin_reset_credentials("Student", target_st_rno, custom_st_pw, custom_st_pin)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

                if st.button("⚡ Quick Reset to Default (student123 / 1234)", key="adm_st_def_rst", width="stretch"):
                    ok, msg = admin_reset_credentials("Student", target_st_rno, "student123", "1234")
                    if ok:
                        st.success(msg)
                        st.rerun()

        with c_del:
            st.markdown("##### 🗑️ Remove Student")
            if not students_df.empty:
                del_st_label = st.selectbox("Select Student", students_df["Roll No"] + " — " + students_df["Name"], key="adm_del_st_box")
                if st.button("Delete Student Record", key="adm_del_st_btn", width="stretch"):
                    target_rno = del_st_label.split(" — ")[0]
                    cur = conn.cursor()
                    cur.execute("DELETE FROM students WHERE roll_no = ?", (target_rno,))
                    conn.commit()
                    st.success("Student removed.")
                    st.rerun()

        st.divider()
        st.markdown("##### 📄 Add Result (Upload PDF or Word File)")
        st.caption("Matches Roll No & Name from the database with rows in your uploaded `.pdf` or `.docx` file (`Roll No | Name | Semester | Subject | Credits | Marks | Grade | SGPA | CGPA | Status`).")
        up_res_file = st.file_uploader("Upload Student Results File (.pdf or .docx)", type=["pdf", "docx"], key="adm_upload_res_file")
        if st.button("📤 Process & Update Student Results", key="adm_apply_res_btn"):
            extracted_res_txt = extract_text_from_upload(up_res_file)
            cnt_res, msg_res = apply_uploaded_results_to_db(extracted_res_txt, conn)
            if cnt_res > 0:
                st.success(msg_res)
                st.rerun()
            else:
                st.warning(msg_res)

        st.divider()
        st.markdown("##### 🗓️ Add Student Timetable (Upload PDF or Word File)")
        st.caption("Upload a `.pdf` or `.docx` timetable (`Day | P1 | P2 | P3 | P4 | LUNCH | P5 | P6 | P7`) to update a student section's timetable.")
        tt_st_sec = st.selectbox("Target Student Section", ["Section B-2", "Section B-3", "Section B-4", "Section B-6"], key="adm_tt_st_sec")
        up_st_tt_file = st.file_uploader("Upload Student Timetable File (.pdf or .docx)", type=["pdf", "docx"], key="adm_upload_st_tt_file")
        if st.button("📤 Update Student Section Timetable", key="adm_apply_st_tt_btn"):
            extracted_st_tt = extract_text_from_upload(up_st_tt_file)
            cnt_stt, msg_stt = apply_uploaded_timetable_to_db(extracted_st_tt, "student", tt_st_sec, conn)
            if cnt_stt > 0:
                st.success(msg_stt)
                st.rerun()
            else:
                st.warning(msg_stt)

    elif st.session_state.adm_page == "faculty":
        st.subheader("Faculty Roster & Section Appointments")
        fac_df = read_df('''SELECT id, faculty_code AS "Faculty ID", name AS "Name", department AS "Department", designation AS "Designation", created_at AS "Joined Date", '•••••••• (SHA-256)' AS "Security", recovery_pin AS "Recovery PIN" FROM faculty''', conn)
        st.markdown(render_clean_table(fac_df.drop(columns=["id"])), unsafe_allow_html=True)

        st.markdown("##### Current Section & Subject Appointments")
        assign_view = read_df("""
            SELECT fa.id, f.faculty_code AS "Faculty ID", f.name AS "Faculty Name",
                   fa.section AS "Appointed Section", sc.code AS "Subject Code", sc.name AS "Subject Name",
                   fa.appointed_at AS "Appointed Date"
            FROM faculty_assignments fa
            JOIN faculty f ON fa.faculty_id = f.id
            JOIN subject_catalog sc ON fa.subject_id = sc.id
            ORDER BY f.faculty_code, fa.section
        """, conn)
        st.markdown(render_clean_table(assign_view.drop(columns=["id"])), unsafe_allow_html=True)

        st.divider()
        col_f1, col_f2, col_f3, col_f4 = st.columns([1.15, 1.15, 1.15, 0.95])
        with col_f1:
            st.markdown("##### ➕ Add New Faculty")
            with st.form("adm_add_fac", clear_on_submit=True):
                f_code = st.text_input("Faculty ID (e.g., FAC004)")
                f_name = st.text_input("Faculty Name")
                f_desig = st.text_input("Designation", value="Assistant Professor")
                fc1, fc2 = st.columns(2)
                f_pw = fc1.text_input("Password", value="faculty123")
                f_pin = fc2.text_input("4-Digit PIN", value="1234", max_chars=4)
                if st.form_submit_button("Create Faculty Account", width="stretch"):
                    if not f_code.strip() or not f_name.strip():
                        st.error("Faculty ID and Name are required.")
                    else:
                        try:
                            cur = conn.cursor()
                            today_str = date.today().strftime("%Y-%m-%d")
                            cur.execute(
                                "INSERT INTO faculty (faculty_code, password, recovery_pin, name, department, designation, theme_pref, created_at) VALUES (?, ?, ?, ?, 'Computer Science & Engineering', ?, 'kcc', ?)",
                                (f_code.upper().strip(), hash_password(f_pw), f_pin.strip() or "1234", f_name.strip(), f_desig.strip(), today_str)
                            )
                            conn.commit()
                            st.success(f"Added {f_name} ({f_code.upper()}) on {today_str}!")
                            st.rerun()
                        except Exception:
                            conn.raw_conn.rollback()
                            st.error("Faculty ID already exists.")

        with col_f2:
            st.markdown("##### 📌 Appoint to Section")
            subs_cat = read_df("SELECT id, code, name FROM subject_catalog ORDER BY code", conn)
            sections_list = ["Section B-2", "Section B-3", "Section B-4", "Section B-6"]

            with st.form("adm_assign_fac"):
                sel_fac = st.selectbox("Select Faculty", fac_df["Faculty ID"] + " — " + fac_df["Name"]) if not fac_df.empty else None
                sel_sec = st.selectbox("Select Section", sections_list)
                sel_sub = st.selectbox("Select Subject", subs_cat["code"] + " — " + subs_cat["name"])
                if st.form_submit_button("Assign Section & Subject", width="stretch"):
                    if sel_fac:
                        fid = int(fac_df[fac_df["Faculty ID"] == sel_fac.split(" — ")[0]].iloc[0]["id"])
                        sid = int(subs_cat[subs_cat["code"] == sel_sub.split(" — ")[0]].iloc[0]["id"])
                        try:
                            cur = conn.cursor()
                            today_str = date.today().strftime("%Y-%m-%d")
                            cur.execute("INSERT INTO faculty_assignments (faculty_id, section, subject_id, appointed_at) VALUES (?, ?, ?, ?)", (fid, sel_sec, sid, today_str))
                            conn.commit()
                            st.success(f"Appointed {sel_fac} to {sel_sec} for {sel_sub} (starts at 0/0 classes)!")
                            st.rerun()
                        except Exception:
                            conn.raw_conn.rollback()
                            st.warning("This faculty member is already appointed to that section & subject.")

        with col_f3:
            st.markdown("##### 🔑 Reset Password & PIN")
            if not fac_df.empty:
                rst_fac_label = st.selectbox("Select Faculty", fac_df["Faculty ID"] + " — " + fac_df["Name"], key="adm_rst_fac_box")
                target_fac_code = rst_fac_label.split(" — ")[0]
                frc1, frc2 = st.columns(2)
                custom_fac_pw = frc1.text_input("New Password", value="faculty123", key="adm_fac_new_pw")
                custom_fac_pin = frc2.text_input("New 4-Digit PIN", value="1234", max_chars=4, key="adm_fac_new_pin")

                if st.button("🔑 Save Custom Password & PIN", key="adm_fac_custom_rst", width="stretch"):
                    ok, msg = admin_reset_credentials("Faculty", target_fac_code, custom_fac_pw, custom_fac_pin)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

                if st.button("⚡ Reset Default (faculty123 / 1234)", key="adm_fac_def_rst", width="stretch"):
                    ok, msg = admin_reset_credentials("Faculty", target_fac_code, "faculty123", "1234")
                    if ok:
                        st.success(msg)
                        st.rerun()

        with col_f4:
            st.markdown("##### 🗑️ Remove Faculty")
            if not fac_df.empty:
                del_fac_label = st.selectbox("Select Faculty", fac_df["Faculty ID"] + " — " + fac_df["Name"], key="adm_del_fac_box")
                if st.button("Delete Faculty Record", key="adm_del_fac_btn", width="stretch"):
                    target_fcode = del_fac_label.split(" — ")[0]
                    cur = conn.cursor()
                    cur.execute("DELETE FROM faculty WHERE faculty_code = ?", (target_fcode,))
                    conn.commit()
                    st.success("Faculty removed.")
                    st.rerun()

        st.divider()
        st.markdown("##### 🗓️ Add Teacher Timetable (Upload PDF or Word File)")
        st.caption("Upload a `.pdf` or `.docx` timetable (`Day | P1 | P2 | P3 | P4 | LUNCH | P5 | P6 | P7` with `B2/B3/B4/B6/Free`) to update a teacher's timetable.")
        if not fac_df.empty:
            tt_fac_pick = st.selectbox("Target Teacher", fac_df["Faculty ID"] + " — " + fac_df["Name"], key="adm_tt_fac_pick")
            target_tt_fcode = tt_fac_pick.split(" — ")[0].strip()
            up_fac_tt_file = st.file_uploader("Upload Teacher Timetable File (.pdf or .docx)", type=["pdf", "docx"], key="adm_upload_fac_tt_file")
            if st.button("📤 Update Teacher Timetable", key="adm_apply_fac_tt_btn"):
                extracted_fac_tt = extract_text_from_upload(up_fac_tt_file)
                cnt_ftt, msg_ftt = apply_uploaded_timetable_to_db(extracted_fac_tt, "faculty", target_tt_fcode, conn)
                if cnt_ftt > 0:
                    st.success(msg_ftt)
                    st.rerun()
                else:
                    st.warning(msg_ftt)

    elif st.session_state.adm_page == "subjects":
        st.subheader("Master AKTU Subject Catalog")
        cat_df = read_df('SELECT id, code AS "Code", name AS "Subject Name", credits AS "Credits" FROM subject_catalog ORDER BY code', conn)
        st.markdown(render_clean_table(cat_df.drop(columns=["id"])), unsafe_allow_html=True)

        st.divider()
        sc1, sc2 = st.columns([1.4, 1])
        with sc1:
            st.markdown("##### ➕ Add Subject to Master Catalog (Enrolls All Students)")
            with st.form("adm_add_sub", clear_on_submit=True):
                nc1, nc2, nc3 = st.columns(3)
                new_code = nc1.text_input("Subject Code (e.g., BCS304)")
                new_name = nc2.text_input("Subject Name")
                new_cred = nc3.number_input("Credits", min_value=0.0, max_value=10.0, value=4.0, step=0.5)
                if st.form_submit_button("Add Subject", width="stretch"):
                    if not new_code.strip() or not new_name.strip():
                        st.error("Enter both Subject Code and Name.")
                    else:
                        try:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO subject_catalog (code, name, credits) VALUES (?, ?, ?)", (new_code.upper().strip(), new_name.strip(), new_cred))
                            new_sid = cur.lastrowid
                            cur.execute("SELECT id FROM students")
                            for (stid,) in cur.fetchall():
                                cur.execute("INSERT INTO student_subjects (student_id, subject_id, attended, total, grade) VALUES (?, ?, 0, 0, 'A (80-89)')", (stid, new_sid))
                            conn.commit()
                            st.success(f"Added {new_code.upper()} to catalog and enrolled all students!")
                            st.rerun()
                        except Exception:
                            conn.raw_conn.rollback()
                            st.error("Subject code already exists.")

        with sc2:
            st.markdown("##### 🗑️ Delete Subject")
            if not cat_df.empty:
                del_sub = st.selectbox("Select Subject", cat_df["Code"] + " — " + cat_df["Subject Name"])
                if st.button("Delete Subject", width="stretch"):
                    target_code = del_sub.split(" — ")[0]
                    cur = conn.cursor()
                    cur.execute("DELETE FROM subject_catalog WHERE code = ?", (target_code,))
                    conn.commit()
                    st.success("Subject deleted.")
                    st.rerun()

    conn.close()