import base64
import math
import sqlite3
import pandas as pd
import streamlit as st

# -------------------- PAGE CONFIGURATION --------------------
st.set_page_config(
    page_title="AKTU Smart Academic Manager",
    page_icon="🎓",
    layout="wide"
)

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

# -------------------- BUILT-IN CUTE & COOL DOODLES (OFFLINE SVG) --------------------
DOODLES = {
    "🐱 Cyber Cat (Cool Shades)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#FFE8A3"/><polygon points="26,48 34,18 52,38" fill="#FF9F43" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><polygon points="94,48 86,18 68,38" fill="#FF9F43" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><circle cx="60" cy="66" r="34" fill="#FFBE76" stroke="#2D3436" stroke-width="3"/><rect x="33" y="54" width="23" height="14" rx="4" fill="#1E272E"/><rect x="64" y="54" width="23" height="14" rx="4" fill="#1E272E"/><line x1="56" y1="60" x2="64" y2="60" stroke="#1E272E" stroke-width="3"/><line x1="37" y1="57" x2="43" y2="65" stroke="#00D2D3" stroke-width="2.5"/><line x1="68" y1="57" x2="74" y2="65" stroke="#00D2D3" stroke-width="2.5"/><polygon points="56,74 64,74 60,79" fill="#FF6B81"/><path d="M52,83 Q60,90 68,83" fill="none" stroke="#2D3436" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "🤖 Chill Robo (Coder Bot)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#DFF9FB"/><line x1="60" y1="16" x2="60" y2="30" stroke="#2D3436" stroke-width="3.5"/><circle cx="60" cy="14" r="5" fill="#FF4757"/><rect x="28" y="30" width="64" height="56" rx="14" fill="#70A1FF" stroke="#2D3436" stroke-width="3"/><rect x="36" y="42" width="48" height="24" rx="8" fill="#1E272E"/><circle cx="48" cy="54" r="5" fill="#2ED573"/><circle cx="72" cy="54" r="5" fill="#2ED573"/><rect x="46" y="73" width="28" height="6" rx="3" fill="#FFFFFF"/><rect x="19" y="48" width="9" height="20" rx="4" fill="#FFA502" stroke="#2D3436" stroke-width="2.5"/><rect x="92" y="48" width="9" height="20" rx="4" fill="#FFA502" stroke="#2D3436" stroke-width="2.5"/></svg>',
    "🐼 Study Panda (Geek Mode)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#E8F8F5"/><circle cx="32" cy="34" r="13" fill="#2D3436"/><circle cx="88" cy="34" r="13" fill="#2D3436"/><circle cx="60" cy="64" r="35" fill="#FFFFFF" stroke="#2D3436" stroke-width="3"/><ellipse cx="45" cy="60" rx="10" ry="8" fill="#2D3436"/><ellipse cx="75" cy="60" rx="10" ry="8" fill="#2D3436"/><circle cx="45" cy="60" r="12" fill="none" stroke="#0984E3" stroke-width="3"/><circle cx="75" cy="60" r="12" fill="none" stroke="#0984E3" stroke-width="3"/><line x1="57" y1="60" x2="63" y2="60" stroke="#0984E3" stroke-width="3"/><circle cx="46" cy="59" r="3" fill="#FFFFFF"/><circle cx="76" cy="59" r="3" fill="#FFFFFF"/><ellipse cx="60" cy="73" rx="5" ry="3.5" fill="#2D3436"/><path d="M53,81 Q60,87 67,81" fill="none" stroke="#2D3436" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "🦊 Hoodie Fox (Dev Vibes)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#FAD390"/><polygon points="25,52 30,18 52,38" fill="#E55039" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><polygon points="95,52 90,18 68,38" fill="#E55039" stroke="#2D3436" stroke-width="3" stroke-linejoin="round"/><path d="M26,62 Q60,24 94,62 Q86,96 60,98 Q34,96 26,62 Z" fill="#EB2F06" stroke="#2D3436" stroke-width="3"/><path d="M28,66 Q45,68 60,86 Q75,68 92,66 Q82,95 60,97 Q38,95 28,66 Z" fill="#FFFFFF"/><circle cx="45" cy="60" r="4" fill="#2D3436"/><circle cx="75" cy="60" r="4" fill="#2D3436"/><circle cx="60" cy="78" r="4.5" fill="#2D3436"/><path d="M54,85 Q60,90 66,85" fill="none" stroke="#2D3436" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "🐸 Chill Frog (Headphones)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#D5F5E3"/><path d="M24,62 A36,36 0 0,1 96,62" fill="none" stroke="#2D3436" stroke-width="5"/><circle cx="42" cy="38" r="13" fill="#2ECC71" stroke="#2D3436" stroke-width="3"/><circle cx="78" cy="38" r="13" fill="#2ECC71" stroke="#2D3436" stroke-width="3"/><circle cx="42" cy="38" r="6" fill="#FFFFFF"/><circle cx="78" cy="38" r="6" fill="#FFFFFF"/><circle cx="43" cy="38" r="3" fill="#2D3436"/><circle cx="79" cy="38" r="3" fill="#2D3436"/><ellipse cx="60" cy="68" rx="36" ry="26" fill="#2ECC71" stroke="#2D3436" stroke-width="3"/><rect x="17" y="54" width="10" height="22" rx="5" fill="#FF4757" stroke="#2D3436" stroke-width="2.5"/><rect x="93" y="54" width="10" height="22" rx="5" fill="#FF4757" stroke="#2D3436" stroke-width="2.5"/><path d="M44,72 Q60,84 76,72" fill="none" stroke="#2D3436" stroke-width="3" stroke-linecap="round"/></svg>',
    "🚀 Astro Bear (Space Explorer)": '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg"><circle cx="60" cy="60" r="58" fill="#2C3A47"/><circle cx="24" cy="28" r="2" fill="#FFF"/><circle cx="94" cy="26" r="2.5" fill="#FFF"/><circle cx="96" cy="88" r="2" fill="#FFF"/><circle cx="60" cy="62" r="42" fill="#74B9FF" fill-opacity="0.35" stroke="#DFE6E9" stroke-width="3.5"/><circle cx="38" cy="38" r="10" fill="#A0522D" stroke="#2D3436" stroke-width="2.5"/><circle cx="82" cy="38" r="10" fill="#A0522D" stroke="#2D3436" stroke-width="2.5"/><circle cx="60" cy="64" r="27" fill="#CD853F" stroke="#2D3436" stroke-width="2.5"/><ellipse cx="60" cy="71" rx="11" ry="8" fill="#FFEAA7"/><circle cx="50" cy="58" r="3.5" fill="#2D3436"/><circle cx="70" cy="58" r="3.5" fill="#2D3436"/><circle cx="60" cy="68" r="3.5" fill="#2D3436"/><path d="M55,74 Q60,78 65,74" fill="none" stroke="#2D3436" stroke-width="2" stroke-linecap="round"/></svg>',
}


# -------------------- DATABASE LAYER (SQLite) --------------------
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            credits REAL NOT NULL,
            attended INTEGER NOT NULL,
            total INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            roll_no TEXT NOT NULL,
            branch TEXT NOT NULL,
            section TEXT NOT NULL,
            semester TEXT NOT NULL,
            avatar_mode TEXT NOT NULL,
            doodle_name TEXT NOT NULL,
            photo_blob BLOB
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM student_profile")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO student_profile (id, name, roll_no, branch, section, semester, avatar_mode, doodle_name, photo_blob)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Manas Srivastav",
            "2504920100346",
            "B.Tech CSE",
            "Section B-3",
            "3rd Semester",
            "Pre-built Doodle",
            "🐱 Cyber Cat (Cool Shades)",
            None
        ))
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM subjects")
    if cur.fetchone()[0] == 0:
        sample_subjects = [
            ("BCS301", "Data Structures", 4.0, 26, 30, "A (80-89)"),
            ("BCS302", "Computer Organization & Architecture", 4.0, 21, 30, "B+ (70-79)"),
            ("BCS303", "Discrete Structures & Theory of Logic", 4.0, 24, 28, "A+ (90-100)"),
            ("BAS303", "Mathematics-IV", 4.0, 19, 28, "B (60-69)"),
            ("BCC302", "Python Programming", 2.0, 18, 20, "A+ (90-100)"),
            ("BCS351", "Data Structures Lab", 1.0, 11, 12, "A (80-89)"),
            ("BCS352", "COA Lab", 1.0, 9, 12, "B+ (70-79)"),
        ]
        cur.executemany(
            "INSERT INTO subjects (code, name, credits, attended, total, grade) VALUES (?, ?, ?, ?, ?, ?)",
            sample_subjects,
        )
        conn.commit()
    conn.close()


def fetch_profile():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, roll_no, branch, section, semester, avatar_mode, doodle_name, photo_blob FROM student_profile WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return {
        "name": row[0],
        "roll_no": row[1],
        "branch": row[2],
        "section": row[3],
        "semester": row[4],
        "avatar_mode": row[5],
        "doodle_name": row[6],
        "photo_blob": row[7],
    }


def save_profile(name, roll_no, branch, section, semester, avatar_mode, doodle_name, photo_blob):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE student_profile
        SET name = ?, roll_no = ?, branch = ?, section = ?, semester = ?,
            avatar_mode = ?, doodle_name = ?, photo_blob = ?
        WHERE id = 1
    """, (name.strip(), roll_no.strip(), branch.strip(), section.strip(), semester, avatar_mode, doodle_name, photo_blob))
    conn.commit()
    conn.close()


def fetch_subjects():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM subjects ORDER BY code", conn)
    conn.close()
    return df


def update_attendance(subject_id, attended, total):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE subjects SET attended = ?, total = ? WHERE id = ?", (attended, total, subject_id))
    conn.commit()
    conn.close()


def update_grade(subject_id, grade):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE subjects SET grade = ? WHERE id = ?", (grade, subject_id))
    conn.commit()
    conn.close()


def add_subject(code, name, credits, attended, total, grade):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO subjects (code, name, credits, attended, total, grade) VALUES (?, ?, ?, ?, ?, ?)",
        (code.upper().strip(), name.strip(), credits, attended, total, grade),
    )
    conn.commit()
    conn.close()


def delete_subject(subject_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()


# -------------------- CORE LOGIC / ALGORITHMS --------------------
def analyze_attendance(attended, total, target=0.75):
    if total == 0:
        return 0.0, "No Classes", "Add total classes held."
    pct = (attended / total) * 100
    if pct >= target * 100:
        can_bunk = math.floor((attended - target * total) / target)
        return pct, "Safe (>= 75%)", f"Can skip {can_bunk} class(es) and still stay above {int(target*100)}%"
    else:
        must_attend = math.ceil((target * total - attended) / (1 - target))
        return pct, "Shortage (< 75%)", f"Attend {must_attend} more class(es) to reach {int(target*100)}%"


def calculate_sgpa(df):
    if df.empty:
        return 0.0, 0.0
    total_credits = df["credits"].sum()
    earned_points = sum(
        row["credits"] * GRADE_POINTS.get(row["grade"], 0)
        for _, row in df.iterrows()
    )
    sgpa = earned_points / total_credits if total_credits > 0 else 0.0
    return round(sgpa, 2), total_credits


def render_avatar_html(profile, size=115):
    if profile["avatar_mode"] == "Upload My Photo" and profile["photo_blob"]:
        b64_img = base64.b64encode(profile["photo_blob"]).decode("utf-8")
        img_src = f"data:image/png;base64,{b64_img}"
    else:
        svg_code = DOODLES.get(profile["doodle_name"], list(DOODLES.values())[0]).strip()
        b64_svg = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
        img_src = f"data:image/svg+xml;base64,{b64_svg}"

    return f"""
    <div style="display:flex; justify-content:center; margin-bottom:10px;">
        <img src="{img_src}" style="width:{size}px; height:{size}px; border-radius:50%;
             object-fit:cover; border:3px solid #4F8BF9; box-shadow:0 4px 10px rgba(0,0,0,0.15);" />
    </div>
    """


def render_horizontal_attendance_chart(summary_df, target_pct=75):
    legend_html = (
        f'<div style="display:flex; justify-content:space-between; align-items:center; '
        f'flex-wrap:wrap; gap:8px; margin-bottom:14px; font-size:0.9rem;">'
        f'<div>'
        f'<span style="display:inline-block; width:12px; height:12px; background:#22C55E; border-radius:3px; margin-right:6px;"></span>'
        f'<b>Safe (≥ {target_pct}%)</b>'
        f'    '
        f'<span style="display:inline-block; width:12px; height:12px; background:#EF4444; border-radius:3px; margin-right:6px;"></span>'
        f'<b>Shortage (< {target_pct}%)</b>'
        f'</div>'
        f'<div style="color:#888;">Dashed line = {target_pct}% required threshold</div>'
        f'</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)

    for _, row in summary_df.iterrows():
        pct = float(row["Percentage (%)"])
        is_safe = pct >= target_pct
        bar_color = "#22C55E" if is_safe else "#EF4444"
        text_color = "#16A34A" if is_safe else "#DC2626"
        bg_tint = "rgba(34, 197, 94, 0.08)" if is_safe else "rgba(239, 68, 68, 0.08)"
        border_tint = "rgba(34, 197, 94, 0.35)" if is_safe else "rgba(239, 68, 68, 0.35)"
        bar_width = max(min(pct, 100.0), 10.0)
        icon = "✅" if is_safe else "⚠️"

        card_html = (
            f'<div style="width:100%; background:{bg_tint}; border:1px solid {border_tint}; '
            f'border-radius:10px; padding:12px 16px; margin-bottom:12px; box-sizing:border-box;">'
            f'<div style="position:relative; width:100%; height:30px; background:rgba(128,128,128,0.2); '
            f'border-radius:7px; overflow:hidden;">'
            f'<div style="width:{bar_width}%; height:100%; background:{bar_color}; border-radius:7px; '
            f'display:flex; align-items:center; justify-content:flex-end; padding-right:12px; '
            f'color:#FFFFFF; font-weight:700; font-size:0.95rem; box-sizing:border-box;">'
            f'{pct:.2f}%'
            f'</div>'
            f'<div style="position:absolute; left:{target_pct}%; top:0; bottom:0; width:2px; '
            f'border-left:2px dashed #1E293B; opacity:0.85;"></div>'
            f'</div>'
            f'<div style="margin-top:8px; font-size:0.98rem; font-weight:700;">'
            f'{row["Code"]} — {row["Subject Name"]} '
            f'<span style="font-weight:400; color:gray; font-size:0.86rem;">({row["Attended"]}/{row["Total"]} classes)</span>'
            f'</div>'
            f'<div style="margin-top:3px; font-size:0.9rem; font-weight:600; color:{text_color};">'
            f'{icon} {row["Smart Recommendation"]}'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


# -------------------- INITIALIZE DATA --------------------
init_db()
profile = fetch_profile()
df = fetch_subjects()

# -------------------- SIDEBAR: STUDENT PROFILE --------------------
with st.sidebar:
    st.markdown("### 🧑‍🎓 Student Profile")
    st.markdown(render_avatar_html(profile, size=120), unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="text-align:center; padding-bottom:10px;">
            <h4 style="margin:0;">{profile['name']}</h4>
            <p style="margin:2px 0; color:gray; font-size:0.9rem;">Roll No: <b>{profile['roll_no']}</b></p>
            <p style="margin:2px 0; font-size:0.88rem;">{profile['branch']} • {profile['section']}</p>
            <span style="background:#4F8BF922; color:#4F8BF9; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;">
                {profile['semester']}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    with st.expander("✏️ Edit Profile & Avatar", expanded=False):
        p_name = st.text_input("Student Name", value=profile["name"])
        p_roll = st.text_input("AKTU Roll Number", value=profile["roll_no"])
        p_branch = st.text_input("Branch / Course", value=profile["branch"])
        p_sec = st.text_input("Section", value=profile["section"])
        sem_options = ["1st Semester", "2nd Semester", "3rd Semester", "4th Semester", "5th Semester", "6th Semester", "7th Semester", "8th Semester"]
        sem_idx = sem_options.index(profile["semester"]) if profile["semester"] in sem_options else 2
        p_sem = st.selectbox("Current Semester", sem_options, index=sem_idx)

        st.markdown("**Choose Profile Picture Style:**")
        avatar_mode = st.radio(
            "Avatar Option",
            ["Pre-built Doodle", "Upload My Photo"],
            index=0 if profile["avatar_mode"] == "Pre-built Doodle" else 1,
            label_visibility="collapsed"
        )

        doodle_keys = list(DOODLES.keys())
        d_idx = doodle_keys.index(profile["doodle_name"]) if profile["doodle_name"] in doodle_keys else 0
        selected_doodle = profile["doodle_name"]
        uploaded_bytes = profile["photo_blob"]

        if avatar_mode == "Pre-built Doodle":
            selected_doodle = st.selectbox("Pick a Cute & Cool Doodle", doodle_keys, index=d_idx)
            preview_svg = base64.b64encode(DOODLES[selected_doodle].strip().encode("utf-8")).decode("utf-8")
            st.markdown(
                f'<div style="text-align:center;"><img src="data:image/svg+xml;base64,{preview_svg}" width="80"/></div>',
                unsafe_allow_html=True
            )
        else:
            uploaded_file = st.file_uploader("Upload Photo (JPG / PNG)", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                uploaded_bytes = uploaded_file.read()

        if st.button("💾 Save Profile", width="stretch"):
            if not p_name.strip() or not p_roll.strip():
                st.error("Name and Roll Number cannot be empty.")
            else:
                save_profile(p_name, p_roll, p_branch, p_sec, p_sem, avatar_mode, selected_doodle, uploaded_bytes)
                st.success("Profile updated!")
                st.rerun()

# -------------------- MAIN HEADER --------------------
st.title("🎓 Smart AKTU CGPA, Credit & Attendance Manager")
st.caption(f"Welcome, {profile['name']} ({profile['roll_no']}) | KCC Institute of Technology and Management (CC 492)")

tab1, tab2, tab3 = st.tabs([
    "📊 Attendance & 75% Predictor",
    "🏆 SGPA, CGPA & 160-Credit Tracker",
    "⚙️ Manage Subjects (CRUD)"
])

# ==================== TAB 1: ATTENDANCE TRACKER ====================
with tab1:
    st.subheader("Subject-Wise Attendance & 75% Threshold Analysis")

    if df.empty:
        st.warning("No subjects found. Add subjects in the 'Manage Subjects' tab.")
    else:
        total_att = df["attended"].sum()
        total_cls = df["total"].sum()
        overall_pct = (total_att / total_cls * 100) if total_cls > 0 else 0.0
        shortage_count = sum(
            1 for _, r in df.iterrows() if (r["total"] > 0 and (r["attended"] / r["total"]) < 0.75)
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Attendance", f"{overall_pct:.2f}%", f"{total_att}/{total_cls} Classes")
        c2.metric("AKTU Minimum Requirement", "75.00%", "Mandatory for End-Sem")
        c3.metric("Subjects in Shortage", f"{shortage_count} Subject(s)", delta_color="inverse")

        st.divider()

        records = []
        for _, row in df.iterrows():
            pct, status, action = analyze_attendance(row["attended"], row["total"])
            records.append({
                "Code": row["code"],
                "Subject Name": row["name"],
                "Attended": row["attended"],
                "Total": row["total"],
                "Percentage (%)": round(pct, 2),
                "Status": status,
                "Smart Recommendation": action
            })

        summary_df = pd.DataFrame(records)

        st.markdown("#### Horizontal Attendance Bar Chart (75% Target Analysis)")
        render_horizontal_attendance_chart(summary_df, target_pct=75)

        st.markdown("#### Quick Attendance Updater (Live Demo)")
        selected_code = st.selectbox(
            "Select Subject to Mark Attendance",
            df["code"] + " - " + df["name"]
        )
        sel_row = df[df["code"] == selected_code.split(" - ")[0]].iloc[0]

        col_a, col_b, _ = st.columns([1, 1, 2])
        with col_a:
            if st.button("✅ Mark Present (+1)", width="stretch"):
                update_attendance(int(sel_row["id"]), int(sel_row["attended"]) + 1, int(sel_row["total"]) + 1)
                st.rerun()
        with col_b:
            if st.button("❌ Mark Absent (+1)", width="stretch"):
                update_attendance(int(sel_row["id"]), int(sel_row["attended"]), int(sel_row["total"]) + 1)
                st.rerun()

        st.divider()
        st.markdown("#### Detailed Subject Attendance Table")
        st.dataframe(summary_df, width="stretch", hide_index=True)

# ==================== TAB 2: SGPA, CGPA & CREDITS ====================
with tab2:
    st.subheader("AKTU SGPA, CGPA & 160-Credit Degree Progress")

    sgpa, sem_credits = calculate_sgpa(df)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("##### Current Semester Grade Simulator")
        for _, row in df.iterrows():
            g_col1, g_col2 = st.columns([2, 1.5])
            g_col1.write(f"**{row['code']}** — {row['name']} ({row['credits']} Cr)")
            grade_keys = list(GRADE_POINTS.keys())
            curr_idx = grade_keys.index(row["grade"]) if row["grade"] in grade_keys else 0
            new_grade = g_col2.selectbox(
                f"Grade_{row['id']}",
                grade_keys,
                index=curr_idx,
                label_visibility="collapsed"
            )
            if new_grade != row["grade"]:
                update_grade(int(row["id"]), new_grade)
                st.rerun()

    with col2:
        st.markdown("##### Previous Semesters & Overall CGPA")
        prev_credits = st.number_input("Credits Earned in Previous Semesters", min_value=0.0, max_value=140.0, value=40.0, step=1.0)
        prev_cgpa = st.number_input("Previous CGPA (0.00 - 10.00)", min_value=0.0, max_value=10.0, value=8.15, step=0.05)

        total_degree_credits = prev_credits + sem_credits
        overall_cgpa = (
            ((prev_cgpa * prev_credits) + (sgpa * sem_credits)) / total_degree_credits
            if total_degree_credits > 0 else 0.0
        )

        st.metric("Current Semester SGPA", f"{sgpa:.2f}", f"{sem_credits} Credits")
        st.metric("Projected Overall CGPA", f"{overall_cgpa:.2f}", f"Equivalent %: {overall_cgpa * 10:.1f}%")

        progress = min(total_degree_credits / 160.0, 1.0)
        st.markdown(f"**AKTU B.Tech Degree Credit Progress:** `{total_degree_credits:.0f} / 160 Credits`")
        st.progress(progress)

# ==================== TAB 3: CRUD OPERATIONS ====================
with tab3:
    st.subheader("Database Management (Add / Remove Subjects)")

    with st.form("add_subject_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        new_code = f1.text_input("Subject Code (e.g., BCS301)")
        new_name = f2.text_input("Subject Name")
        new_credits = f3.number_input("Credits", min_value=0.0, max_value=10.0, value=4.0, step=0.5)

        f4, f5, f6 = st.columns(3)
        new_att = f4.number_input("Classes Attended", min_value=0, max_value=200, value=15)
        new_tot = f5.number_input("Total Classes Held", min_value=0, max_value=200, value=20)
        new_grade = f6.selectbox("Expected Grade", list(GRADE_POINTS.keys()))

        submitted = st.form_submit_button("➕ Add Subject to Database")
        if submitted:
            if not new_code or not new_name:
                st.error("Please enter both Subject Code and Subject Name.")
            elif new_att > new_tot:
                st.error("Classes attended cannot exceed total classes held.")
            else:
                try:
                    add_subject(new_code, new_name, new_credits, int(new_att), int(new_tot), new_grade)
                    st.success(f"Added {new_code.upper()} successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("A subject with this code already exists.")

    st.divider()
    st.markdown("##### Delete Existing Subject")
    if not df.empty:
        del_choice = st.selectbox("Select Subject to Delete", df["code"] + " - " + df["name"], key="del_box")
        if st.button("🗑️ Delete Selected Subject"):
            del_id = int(df[df["code"] == del_choice.split(" - ")[0]].iloc[0]["id"])
            delete_subject(del_id)
            st.success("Subject deleted.")
            st.rerun()