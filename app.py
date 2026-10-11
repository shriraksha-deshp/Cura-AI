"""Cura AI Streamlit user interface.
Run with: python -m streamlit run app.py
"""
from cura_core import *

# Pre-create a demo account so evaluators can log in immediately, even after the
# hosting platform restarts and wipes the database.
DEMO_USER, DEMO_PASS = "demo", "demo1234"

@st.cache_resource
def seed_demo_account():
    if create_user(DEMO_USER, DEMO_PASS, "91-1234-5678-9012"):
        save_details(DEMO_USER, "Demo", "User", 28, "Male", 170, 70.0, 80.0)
    return True

seed_demo_account()

# -------------------- UI theme --------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
@keyframes pageFadeIn { from {opacity:0; transform:translateY(5px)} to {opacity:1; transform:translateY(0)} }
.stApp {
    font-family:'Plus Jakarta Sans',sans-serif;
    background-color:#FAF7FF;
    background-image:radial-gradient(at 0% 0%,#EDE9FE 0,transparent 48%),
                     radial-gradient(at 100% 0%,#E0F2FE 0,transparent 48%),
                     radial-gradient(at 100% 100%,#DCFCE7 0,transparent 48%),
                     radial-gradient(at 0% 100%,#FFE4E6 0,transparent 48%);
    background-attachment:fixed; animation:pageFadeIn .35s ease-out;
}
header[data-testid="stHeader"] {background:transparent}
footer,#MainMenu {visibility:hidden}
.block-container {padding-top:1.6rem;max-width:1300px}
[data-testid="stSidebar"] {background:rgba(255,255,255,.88);backdrop-filter:blur(12px);border-right:1px solid #E2E8F0}
[class*="st-key-card_"],[data-testid="stForm"] {
    background:rgba(255,255,255,.9)!important;border:1px solid rgba(255,255,255,.9)!important;
    border-radius:20px!important;padding:22px!important;box-shadow:0 5px 24px rgba(100,116,139,.10)!important;
}
.stButton>button {border-radius:12px!important;font-weight:600!important;transition:all .18s ease}
.stButton>button:hover {transform:translateY(-1px);box-shadow:0 5px 15px rgba(99,102,241,.16)}
button[kind="primary"] {background:linear-gradient(135deg,#6366F1,#8B5CF6)!important;color:white!important;border:0!important}
.brand {font-size:1.45rem;font-weight:800;color:#4F46E5;margin:3px 0}
.tagline {font-size:.83rem;color:#7C3AED;font-weight:600;margin-bottom:12px}
.hello {font-size:1.8rem;font-weight:800;color:#1E1B4B;margin-bottom:0}
.muted {color:#64748B;font-size:.88rem}
.stat {border-radius:16px;padding:16px;min-height:100px;border:1px solid #E0E7FF}
.stat .lbl {font-size:.78rem;color:#64748B;font-weight:700;text-transform:uppercase}
.stat .val {font-size:1.6rem;font-weight:800;color:#4338CA;margin:5px 0}
.stat .sub {font-size:.78rem;color:#6366F1}
.cal {width:100%;border-collapse:collapse}
.cal th {color:#94A3B8;font-size:.75rem;padding:6px}
.cal td {text-align:center;padding:3px;font-size:.85rem}
.cal td span {display:inline-block;width:29px;height:29px;line-height:29px;border-radius:9px;color:#475569}
.cal td.rec span {background:#818CF8;color:white;font-weight:700}
.cal td.today span {outline:2px solid #6366F1}
.med {display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #F1F5F9}
.pill {width:36px;height:36px;border-radius:11px;background:#EEF2FF;display:flex;align-items:center;justify-content:center}
"""

st.set_page_config(page_title="Cura AI", page_icon="🩺", layout="wide")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

if "selected_language" not in st.session_state:
    st.session_state["selected_language"] = "ENGLISH"

def start_session(username, abha):
    st.session_state["user"] = username
    st.session_state["abha"] = abha
    st.session_state.pop("result", None)
    st.rerun()

def login_screen():
    with st.sidebar:
        lang = st.selectbox(
            f"🌐 {t('summary_lang')}", LANG_OPTIONS,
            index=LANG_OPTIONS.index(st.session_state.get("selected_language", "ENGLISH"))
        )
        st.session_state["selected_language"] = lang

    _, middle, _ = st.columns([1, 1.25, 1])
    with middle:
        with st.container(key="card_login"):
            st.markdown(f'<div class="brand">{t("brand")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tagline">{t("tagline")}</div>', unsafe_allow_html=True)
            st.caption(t("signin_caption"))
            login_tab, signup_tab = st.tabs([f"🔑 {t('login')}", f"🌱 {t('create_account')}"])
            with login_tab:
                username = st.text_input(t("username"), key="login_username").strip().lower()
                password = st.text_input(t("password"), type="password", key="login_password")
                if st.button(t("login"), type="primary", use_container_width=True, key="login_button"):
                    abha = check_login(username, password)
                    if abha is None:
                        st.error(t("wrong_login"))
                    else:
                        start_session(username, abha)
            with signup_tab:
                username = st.text_input(t("choose_username"), key="signup_username").strip().lower()
                password = st.text_input(t("choose_password"), type="password", key="signup_password")
                abha = st.text_input(t("mock_abha"), value="", key="signup_abha")
                if st.button(t("create_account"), use_container_width=True, key="signup_button"):
                    if len(username) < 3 or len(password) < 6:
                        st.error(t("validation_err"))
                    elif not create_user(username, password, abha):
                        st.error(t("user_taken"))
                    else:
                        start_session(username, abha)
            st.caption(f"🛡️ {t('disclaimer')}")

if "user" not in st.session_state:
    login_screen()
    st.stop()

profile = st.session_state["user"]
abha = st.session_state.get("abha", "")
me = get_details(profile)
display_name = f"{me.get('first_name') or ''} {me.get('last_name') or ''}".strip() or profile

menu_map = {
    "dashboard": t("menu_dashboard"),
    "upload": t("menu_upload"),
    "timeline": t("menu_timeline"),
    "details": t("menu_details"),
}

with st.sidebar:
    st.markdown(f'<div class="brand">{t("brand")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tagline">{t("tagline")}</div>', unsafe_allow_html=True)
    selected_page = st.radio("Menu", list(menu_map.values()), label_visibility="collapsed")
    st.divider()
    st.markdown(f"**👤 {html.escape(display_name)}**")
    st.caption(f"🪪 {t('mock_abha')}: `{html.escape(abha or 'Not provided')}`")
    lang = st.selectbox(
        f"🌐 {t('summary_lang')}", LANG_OPTIONS,
        index=LANG_OPTIONS.index(st.session_state.get("selected_language", "ENGLISH"))
    )
    if lang != st.session_state.get("selected_language"):
        st.session_state["selected_language"] = lang
        st.rerun()
    if st.button(f"🚪 {t('logout')}", use_container_width=True):
        for key in ("user", "abha", "result"):
            st.session_state.pop(key, None)
        st.rerun()
    st.caption(t("demo_notice"))

def stat_card(label, value, sub):
    return (
        f'<div class="stat"><div class="lbl">{label}</div>'
        f'<div class="val">{value}</div><div class="sub">{sub}</div></div>'
    )

def calendar_card(records):
    marked = {}
    for record in records:
        try:
            day = datetime.strptime(record["date"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        marked.setdefault((day.year, day.month), set()).add(day.day)
    today = date.today()
    months = sorted(set(marked) | {(today.year, today.month)}, reverse=True)
    with st.container(key="card_calendar"):
        st.markdown("**🗓️ Health calendar**")
        selected_month = st.selectbox(
            "Month", months, label_visibility="collapsed",
            format_func=lambda item: f"{calendar.month_name[item[1]]} {item[0]}"
        )
        rows = []
        for week in calendar.monthcalendar(*selected_month):
            cells = []
            for day in week:
                if day == 0:
                    cells.append("<td></td>")
                else:
                    classes = []
                    if day in marked.get(selected_month, set()):
                        classes.append("rec")
                    if selected_month == (today.year, today.month) and day == today.day:
                        classes.append("today")
                    cells.append(f'<td class="{" ".join(classes)}"><span>{day}</span></td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")
        headings = "".join(f"<th>{name}</th>" for name in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"))
        st.markdown(
            f'<table class="cal"><tr>{headings}</tr>{"".join(rows)}</table>',
            unsafe_allow_html=True
        )
        st.caption(t("cal_blue"))

def treatment_card(records):
    latest = next((r for r in reversed(records) if r["data"].get("medicines")), None)
    with st.container(key="card_medicines"):
        st.markdown(f"**{t('your_treatment')}**")
        if not latest:
            st.caption(t("treatment_empty"))
            return
        st.caption(f"{t('from')} {latest['date']}")
        for medicine in latest["data"].get("medicines", [])[:5]:
            if not isinstance(medicine, dict):
                continue
            detail = " · ".join(
                str(medicine.get(k) or "") for k in ("dose", "frequency", "duration")
                if medicine.get(k)
            )
            st.markdown(
                f'<div class="med"><div class="pill">💊</div><div><b>{html.escape(str(medicine.get("name") or "Unknown"))}</b><br>'
                f'<span class="muted">{html.escape(detail)}</span></div></div>',
                unsafe_allow_html=True
            )

def page_dashboard():
    records = load_records(profile)
    left_header, right_header = st.columns([3, 1])
    with left_header:
        st.markdown(
            f'<div class="hello">{t("hello")}, {html.escape(me.get("first_name") or profile)} ✨</div>'
            f'<p class="muted">{len(records)} {t("saved_reports")}</p>',
            unsafe_allow_html=True
        )
    with right_header:
        if st.button(t("quick_edit"), use_container_width=True):
            quick_edit_dialog(profile, me)

    left, right = st.columns([2.3, 1], gap="medium")
    with left:
        with st.container(key="card_trends"):
            st.markdown(f"**{t('test_trends')}**")
            test_names = sorted({
                str(test.get("name")) for record in records
                for test in record["data"].get("tests", [])
                if isinstance(test, dict) and test.get("name")
            })
            if test_names:
                selected_test = st.selectbox("Test parameter", test_names, label_visibility="collapsed")
                points = []
                for record in records:
                    for test in record["data"].get("tests", []):
                        if isinstance(test, dict) and test.get("name") == selected_test:
                            number = to_num(test.get("value"))
                            if number is not None:
                                points.append((record["date"], number))
                if points:
                    df = pd.DataFrame(points, columns=["Date", selected_test])
                    df = df.groupby("Date", as_index=True)[selected_test].last().sort_index()
                    st.area_chart(df, height=240)
                    if len(df) < 2:
                        st.caption(t("trend_hint"))
                else:
                    st.info(t("trend_empty"))
            else:
                st.write(t("trend_empty"))

        weight = me.get("weight_kg")
        height = me.get("height_cm")
        age = me.get("age")
        bmi = bmi_info(me)
        cols = st.columns(4, gap="small")
        cols[0].markdown(stat_card(f"⚖️ {t('weight')}", f"{weight:g} kg" if weight else "—", "Profile"), unsafe_allow_html=True)
        cols[1].markdown(stat_card(f"📏 {t('height')}", f"{height:g} cm" if height else "—", "Profile"), unsafe_allow_html=True)
        cols[2].markdown(stat_card(f"🎂 {t('age')}", f"{age} yrs" if age else "—", "Profile"), unsafe_allow_html=True)
        cols[3].markdown(stat_card(f"📊 {t('bmi')}", f"{bmi[0]:.1f}" if bmi and bmi[0] is not None else "—", "Screening measure"), unsafe_allow_html=True)
        if not bmi:
            st.caption(t("add_details_hint"))
        elif bmi[0] is not None:
            if bmi[1] == "ok":
                st.success(bmi[2])
            else:
                st.warning(bmi[2])

        with st.container(key="card_questions"):
            st.markdown(f"**{t('questions_for_doc')}**")
            latest = next((r for r in reversed(records) if r["data"].get("questions_for_doctor")), None)
            if not latest:
                st.caption(t("questions_empty"))
            else:
                for index, question in enumerate(latest["data"]["questions_for_doctor"][:5]):
                    st.checkbox(str(question), key=f"question_{latest['id']}_{index}")
    with right:
        calendar_card(records)
        treatment_card(records)

def page_upload():
    st.markdown(f'<div class="hello">📄 {t("upload_title")}</div>', unsafe_allow_html=True)
    with st.container(key="card_upload"):
        uploaded = st.file_uploader(
            t("upload_label"), type=["png", "jpg", "jpeg", "pdf"],
            help="Avoid uploading documents unless you have permission to process them."
        )
        if uploaded and st.button(t("analyze_btn"), type="primary", use_container_width=True):
            if not api_key():
                st.error(t("api_key_err"))
            else:
                with st.spinner(t("reading_doc")):
                    try:
                        lang_for_prompt = {
                            "ENGLISH": "English", "HINDI": "Hindi",
                            "TELUGU": "Telugu", "TAMIL": "Tamil", "KANNADA": "Kannada"
                        }.get(st.session_state["selected_language"], "English")
                        st.session_state["result"] = analyze(uploaded, lang_for_prompt, me)
                        st.session_state["result_file_name"] = uploaded.name
                        st.success("Analysis completed. Review all extracted information carefully.")
                    except Exception as exc:
                        st.error(f"{t('read_err')} {exc}")

    if "result" in st.session_state:
        with st.container(key="card_result"):
            result = st.session_state["result"]
            show_report(result)
            if not has_findings(result):
                st.divider()
                st.subheader(t("no_findings"))
                st.write(t("bmi_note_intro"))
                show_bmi(me)
            preview = {"id": str(uuid.uuid4()), "date": str(result.get("document_date") or date.today()),
                       "type": result.get("document_type") or "other", "data": result}
            st.download_button(
                t("export_fhir"), data=to_fhir_bundle(profile, abha, me, [preview]),
                file_name="cura_fhir_preview.json", mime="application/json",
                use_container_width=True, key="export_preview"
            )
            if st.button(t("save_timeline"), type="primary", use_container_width=True):
                try:
                    save_record(profile, result)
                    st.session_state.pop("result", None)
                    st.session_state.pop("result_file_name", None)
                    st.success(t("saved_success"))
                    st.rerun()
                except sqlite3.Error as exc:
                    st.error(f"Could not save the report: {exc}")

def page_timeline():
    st.markdown(f'<div class="hello">{t("timeline_title")}</div>', unsafe_allow_html=True)
    records = load_records(profile)
    if not records:
        with st.container(key="card_empty_timeline"):
            st.write(t("timeline_empty"))
        return

    st.download_button(
        t("export_all"), data=to_fhir_bundle(profile, abha, me, records),
        file_name=f"cura_fhir_{profile}.json", mime="application/json", key="export_all"
    )
    for record in reversed(records):
        with st.container(key=f"card_record_{record['id']}"):
            col_a, col_b = st.columns([4, 1.4])
            with col_a:
                st.markdown(f"**🗓️ {html.escape(record['date'])}** · `{html.escape(record['type'].replace('_', ' ').upper())}`")
                summary = str(record["data"].get("summary") or t("no_summary"))
                st.caption(summary[:180] + ("…" if len(summary) > 180 else ""))
            with col_b:
                if st.button(t("inspect"), key=f"inspect_{record['id']}", use_container_width=True):
                    report_dialog(record["data"])
                st.download_button(
                    t("export_fhir"), data=to_fhir_bundle(profile, abha, me, [record]),
                    file_name=f"cura_fhir_{record['date']}_{record['id'][:8]}.json",
                    mime="application/json", key=f"export_{record['id']}", use_container_width=True
                )
                with st.popover("⋯"):
                    if st.button(t("delete"), key=f"delete_{record['id']}", type="secondary"):
                        delete_record(profile, record["id"])
                        st.rerun()

def page_details():
    st.markdown(f'<div class="hello">{t("details_title")}</div>', unsafe_allow_html=True)
    st.caption(t("details_caption"))
    with st.container(key="card_profile_form"):
        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            first = c1.text_input(t("first_name"), value=me.get("first_name") or "")
            last = c2.text_input(t("last_name"), value=me.get("last_name") or "")
            age = c1.number_input(t("age_label"), min_value=0, max_value=120, value=int(me.get("age") or 20), step=1)
            genders = [t("female"), t("male"), t("other"), t("prefer_not")]
            current_gender = me.get("gender")
            gender_index = genders.index(current_gender) if current_gender in genders else 0
            gender = c2.selectbox(t("gender_label"), genders, index=gender_index)
            height = c1.number_input(t("height_label"), min_value=50, max_value=250, value=int(me.get("height_cm") or 170), step=1)
            weight = c2.number_input(t("weight_label"), min_value=10.0, max_value=300.0, value=float(me.get("weight_kg") or 70.0), step=0.5)
            waist = c1.number_input(t("waist_label"), min_value=30.0, max_value=200.0, value=float(me.get("waist_cm") or 80.0), step=0.5)
            submitted = st.form_submit_button(f"✨ {t('save_details_btn')}", type="primary")
        if submitted:
            if not first.strip() or not 1 <= int(age) <= 120:
                st.error(t("required_err"))
            else:
                save_details(profile, first.strip(), last.strip(), int(age), gender,
                             int(height), float(weight), float(waist))
                st.success(t("details_saved"))
                st.rerun()
    with st.container(key="card_bmi"):
        show_bmi(me)

routing = {
    menu_map["dashboard"]: page_dashboard,
    menu_map["upload"]: page_upload,
    menu_map["timeline"]: page_timeline,
    menu_map["details"]: page_details,
}
routing[selected_page]()
st.caption(f"🛡️ {t('disclaimer')}")
