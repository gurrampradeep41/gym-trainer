import html
from datetime import date, timedelta
import pandas as pd
import streamlit as st

from config import get_setting
from db import (
    initialize_database,
    database_health,
    create_client_account,
    fetch_all,
    create_phase4_tables,
    create_phase5_tables,
    create_phase6_tables,
    create_phase9_tables,
)
from auth import (
    bootstrap_trainer,
    authenticate,
    logout_current_user,
    enforce_session_timeout,
    require_role,
)
from security import (
    hash_password,
    validate_password,
    validate_username,
)
from ai_service import generate_ai_response
from report_service import generate_client_pdf_report
from services import (
    verify_trainer,
    verify_client,
    get_ai_client_context,
    get_my_notifications,
    get_unread_notification_count,
    mark_notification_read,
    mark_all_notifications_read,
    delete_my_notification,
    get_trainer_analytics,
    get_client_report_data,
    get_my_report_data,
    get_my_client_profile,
    get_my_trainer_information,
    get_my_dashboard,
    get_my_account_status,
    initialize_trainer_profile,
    get_trainer_profile,
    update_trainer_profile,
    dashboard_statistics,
    get_pending_requests,
    approve_client,
    reject_client,
    get_all_clients,
    get_client_details,
    update_client_details,
    activate_client,
    deactivate_client,
    get_recent_clients,
    get_audit_logs,
    add_weight_entry,
    get_client_weight_history,
    add_body_measurement,
    get_client_measurement_history,
    get_my_weight_history,
    get_my_measurement_history,
    get_my_progress_summary,
    create_workout_plan,
    add_workout_exercise,
    get_trainer_workout_plans,
    get_trainer_plan_exercises,
    delete_workout_exercise,
    update_workout_plan_status,
    get_workout_adherence,
    get_client_workout_activity,
    get_my_workout_plans,
    get_my_workout_exercises,
    mark_exercise_complete,
    get_my_workout_completions,
    create_diet_plan,
    add_diet_meal,
    get_trainer_diet_plans,
    get_trainer_diet_meals,
    delete_diet_meal,
    update_diet_plan_status,
    get_client_nutrition_activity,
    get_diet_plan_adherence,
    get_my_diet_plans,
    get_my_diet_meals,
    log_meal_consumption,
    get_my_meal_logs,
    get_my_nutrition_summary,
)

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="FITPRO | Trainer Dashboard",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap'
);

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background:
    radial-gradient(
        ellipse at 10% 5%,
        rgba(220,38,38,0.15),
        transparent 35%
    ),
    linear-gradient(
        135deg,
        #080808,
        #111111,
        #190909
    );
    color: #ffffff;
}

.block-container {
    max-width: 1350px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #ffffff;
    font-weight: 800;
}

[data-testid="stSidebar"] {
    background: #101010;
    border-right: 1px solid #333333;
}

[data-testid="stMetric"] {
    background: #181818;
    border: 1px solid #383838;
    padding: 18px;
    border-radius: 15px;
}

[data-testid="stMetricValue"] {
    color: #ef4444;
}

[data-testid="stForm"] {
    background: #171717;
    padding: 20px;
    border: 1px solid #333333;
    border-radius: 15px;
}

.stButton > button,
.stFormSubmitButton > button {
    background: #dc2626;
    color: white;
    border: 1px solid #ef4444;
    border-radius: 10px;
    font-weight: 700;
    min-height: 2.6rem;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #991b1b;
    color: white;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
textarea {
    background: #191919 !important;
    color: white !important;
    border-color: #444444 !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #ef4444;
    border-bottom-color: #dc2626;
}

.fitpro-hero {
    background: linear-gradient(
        120deg,
        #171717,
        #260d0d,
        #450a0a
    );
    border: 1px solid #541c1c;
    border-radius: 20px;
    padding: 30px;
}

.fitpro-kicker {
    color: #ef4444;
    font-weight: 800;
    letter-spacing: 3px;
}

.fitpro-title {
    font-size: 42px;
    font-weight: 900;
    color: white;
}

.fitpro-red {
    color: #ef4444;
}

.small-muted {
    color: #a3a3a3;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# WELCOME & LOGIN SCREENS
# ==================================================

def welcome_screen():
    st.markdown("""
    <div class="fitpro-hero">
        <div class="fitpro-kicker">
            FITNESS MANAGEMENT SYSTEM
        </div>
        <div class="fitpro-title">
            WELCOME TO
            <span class="fitpro-red"> FITPRO</span>
        </div>
        <p class="small-muted">
            Train harder. Get stronger. Achieve more.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")


def login_screen():
    welcome_screen()

    login_tab, register_tab = st.tabs([
        "Trainer / Client Login",
        "Client Registration"
    ])

    with login_tab:
        left, center, right = st.columns([1, 1.2, 1])

        with center:
            st.subheader("Welcome Back")

            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "LOGIN",
                    use_container_width=True
                )

            if submitted:
                user, error = authenticate(username, password)

                if error:
                    st.error(error)
                else:
                    st.session_state["user"] = user
                    st.success("Login successful!")
                    st.rerun()

    with register_tab:
        st.info("Client registration requires trainer approval.")

        with st.form("registration_form"):
            full_name = st.text_input("Full name")
            username = st.text_input("Choose username")
            email = st.text_input("Email")
            phone = st.text_input("Phone number")
            password = st.text_input("Create password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")

            age = st.number_input(
                "Age",
                min_value=16,
                max_value=100,
                value=25
            )

            height = st.number_input(
                "Height (cm)",
                min_value=100.0,
                max_value=250.0,
                value=170.0
            )

            goal = st.selectbox(
                "Fitness goal",
                [
                    "Fat loss",
                    "Muscle gain",
                    "Strength",
                    "General fitness",
                    "Endurance"
                ]
            )

            submitted = st.form_submit_button(
                "SUBMIT REQUEST",
                use_container_width=True
            )

        if submitted:
            valid_user, user_error = validate_username(username)
            valid_pass, pass_error = validate_password(password)

            if not full_name.strip():
                st.error("Full name is required.")
            elif not valid_user:
                st.error(user_error)
            elif not valid_pass:
                st.error(pass_error)
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    create_client_account(
                        username.strip(),
                        hash_password(password),
                        full_name.strip(),
                        email.strip(),
                        phone.strip(),
                        int(age),
                        float(height),
                        goal
                    )
                    st.success(
                        "Registration submitted! "
                        "Wait for trainer approval."
                    )
                except Exception:
                    st.error(
                        "Registration failed. "
                        "Username may already exist."
                    )


# ==================================================
# NOTIFICATIONS
# ==================================================

def show_notification_summary(user):
    try:
        count = get_unread_notification_count(int(user["id"]))
        if count:
            st.info(f"🔔 {count} unread notification(s)")
        else:
            st.caption("🔔 No unread notifications")
    except Exception:
        st.caption("🔔 Notifications unavailable")


def notification_center(user):
    user_id = int(user["id"])

    st.markdown("## 🔔 Notifications")

    try:
        unread_count = get_unread_notification_count(user_id)
        notifications = get_my_notifications(user_id)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.metric("Unread notifications", unread_count)

        with col2:
            if unread_count > 0:
                if st.button(
                    "Mark all as read",
                    key=f"mark_all_notifications_{user_id}"
                ):
                    mark_all_notifications_read(user_id)
                    st.toast("All notifications marked as read.", icon="✅")
                    st.rerun()

        if not notifications:
            st.info("You're all caught up. No notifications yet.")
            return

        st.divider()

        for item in notifications:
            (
                notification_id,
                notification_type,
                title,
                message,
                is_read,
                created_at
            ) = item

            with st.container(border=True):
                col1, col2 = st.columns([5, 1])

                with col1:
                    if int(is_read) == 0:
                        st.markdown(f"🔴 **{title}**")
                    else:
                        st.markdown(f"**{title}**")

                    st.write(message)
                    st.caption(
                        f"{notification_type.replace('_', ' ').title()} · "
                        f"{created_at}"
                    )

                with col2:
                    if int(is_read) == 0:
                        if st.button(
                            "Read",
                            key=f"read_notification_{notification_id}"
                        ):
                            mark_notification_read(user_id, notification_id)
                            st.rerun()

                    if st.button(
                        "Delete",
                        key=f"delete_notification_{notification_id}"
                    ):
                        delete_my_notification(user_id, notification_id)
                        st.toast("Notification deleted.", icon="🗑️")
                        st.rerun()

    except Exception as e:
        st.error("Unable to load notifications.")
        print(f"Notification error: {e}")


# ==================================================
# TRAINER PAGES
# ==================================================

def dashboard_header(profile):
    st.markdown("""
    <div class="fitpro-hero">
        <div class="fitpro-kicker">
            TRAINER CONTROL CENTER
        </div>
        <div class="fitpro-title">
            TRAIN.
            <span class="fitpro-red">TRACK.</span>
            TRANSFORM.
        </div>
        <p class="small-muted">
            Manage your gym and clients from one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    col1, col2 = st.columns([1, 4])

    with col1:
        if profile and profile[4]:
            try:
                st.image(profile[4], use_container_width=True)
            except Exception:
                st.markdown("### 🏋️")
        else:
            st.markdown("## 🏋️")

    with col2:
        st.subheader(profile[1] if profile else "Trainer")
        st.write((profile[2] if profile else None) or "Personal Trainer")
        st.caption((profile[3] if profile else None) or "Fitness Professional")


def dashboard_overview(user):
    st.header("Dashboard Overview")

    stats = dashboard_statistics(user["id"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Clients", stats["total"])
    col2.metric("Active Clients", stats["active"])
    col3.metric("Pending Requests", stats["pending"])
    col4.metric("Rejected Clients", stats["rejected"])

    st.write("")
    st.subheader("Recent Registrations")

    recent = get_recent_clients(user["id"], limit=10)

    if recent:
        df = pd.DataFrame(
            recent,
            columns=[
                "Client Name",
                "Username",
                "Status",
                "Registered Date"
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No client registrations found.")


def trainer_profile_page(user):
    st.header("Trainer Profile Management")

    profile = get_trainer_profile(user["id"])

    if not profile:
        st.error("Trainer profile not found.")
        return

    st.subheader("Current Profile")

    col1, col2 = st.columns([1, 3])

    with col1:
        if profile[4]:
            try:
                st.image(profile[4], width=180)
            except Exception:
                st.info("Unable to load profile photo.")
        else:
            st.markdown("## 🏋️")

    with col2:
        st.markdown(f"### {profile[1]}")
        st.write(profile[2])
        st.write(profile[3])
        st.write(profile[5])
        st.caption(profile[6] or "")

    st.divider()
    st.subheader("Edit Trainer Information")

    with st.form("trainer_profile_form"):
        name = st.text_input("Trainer Name", value=profile[1] or "")
        title = st.text_input("Professional Title", value=profile[2] or "")
        experience = st.text_input("Experience", value=profile[3] or "")
        photo_url = st.text_input("Profile Photo URL (HTTPS)", value=profile[4] or "")
        achievements = st.text_area(
            "Achievements",
            value=profile[5] or "",
            height=120,
            help="Separate achievements with semicolons."
        )
        bio = st.text_area(
            "Trainer Biography",
            value=profile[6] or "",
            height=150
        )

        save = st.form_submit_button("SAVE PROFILE", use_container_width=True)

    if save:
        if photo_url and not photo_url.startswith("https://"):
            st.error("Please use a secure HTTPS photo URL.")
        else:
            try:
                update_trainer_profile(
                    user["id"],
                    name,
                    title,
                    experience,
                    photo_url,
                    achievements,
                    bio
                )
                st.success("Trainer profile updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(str(e))


def registration_requests_page(user):
    st.header("Client Registration Requests")

    requests = get_pending_requests(user["id"])

    if not requests:
        st.success("No pending registration requests.")
        return

    st.write(f"Pending requests: {len(requests)}")

    for request in requests:
        (
            client_user_id,
            username,
            full_name,
            email,
            phone,
            age,
            height,
            goal,
            created_at
        ) = request

        with st.container(border=True):
            st.subheader(full_name)
            st.write(f"Username: {username}")
            st.write(f"Email: {email or 'Not provided'}")
            st.write(f"Phone: {phone or 'Not provided'}")
            st.write(f"Age: {age}")
            st.write(f"Height: {height} cm")
            st.write(f"Fitness Goal: {goal}")
            st.caption(f"Registration date: {created_at}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "ACCEPT CLIENT",
                    key=f"approve_{client_user_id}",
                    use_container_width=True
                ):
                    approve_client(user["id"], client_user_id)
                    st.success("Client approved.")
                    st.rerun()

            with col2:
                if st.button(
                    "REJECT CLIENT",
                    key=f"reject_{client_user_id}",
                    use_container_width=True
                ):
                    reject_client(user["id"], client_user_id)
                    st.warning("Client request rejected.")
                    st.rerun()


def client_management_page(user):
    st.header("Client Management")

    clients = get_all_clients(user["id"])

    if not clients:
        st.info("No clients registered yet.")
        return

    search = st.text_input("Search by client name or username")
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "active", "pending", "rejected", "disabled"]
    )

    filtered = []
    for client in clients:
        name = str(client[2]).lower()
        username = str(client[3]).lower()
        status = str(client[9]).lower()

        search_match = (
            search.lower() in name
            or search.lower() in username
        )
        status_match = (
            status_filter == "All"
            or status == status_filter
        )

        if search_match and status_match:
            filtered.append(client)

    st.write(f"Matching clients: {len(filtered)}")

    if filtered:
        df = pd.DataFrame([
            {
                "Client ID": c[0],
                "Name": c[2],
                "Username": c[3],
                "Email": c[4],
                "Age": c[6],
                "Goal": c[8],
                "Status": c[9]
            }
            for c in filtered
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("View / Edit Client")

    selected = st.selectbox(
        "Select Client",
        clients,
        format_func=lambda c: f"{c[2]} (@{c[3]}) — {c[9]}"
    )

    if not selected:
        return

    client_id = int(selected[0])
    details = get_client_details(user["id"], client_id)

    if not details:
        st.error("Client not found.")
        return

    st.markdown(f"### {details[2]}")
    st.caption(f"Account: {details[3]} | Status: {details[9]}")
    st.write("Registered:", details[10])

    with st.form(f"edit_client_{client_id}"):
        full_name = st.text_input("Full Name", value=details[2] or "")
        email = st.text_input("Email", value=details[4] or "")
        phone = st.text_input("Phone", value=details[5] or "")
        age = st.number_input(
            "Age",
            min_value=16,
            max_value=100,
            value=int(details[6] or 25)
        )
        height = st.number_input(
            "Height (cm)",
            min_value=100.0,
            max_value=250.0,
            value=float(details[7] or 170.0)
        )

        goals = [
            "Fat loss",
            "Muscle gain",
            "Strength",
            "General fitness",
            "Endurance"
        ]
        current_goal = details[8] or "General fitness"
        goal_options = goals.copy()
        if current_goal not in goal_options:
            goal_options.append(current_goal)

        goal = st.selectbox(
            "Fitness Goal",
            goal_options,
            index=goal_options.index(current_goal)
        )

        save = st.form_submit_button(
            "UPDATE CLIENT DETAILS",
            use_container_width=True
        )

    if save:
        try:
            update_client_details(
                user["id"],
                client_id,
                full_name,
                email,
                phone,
                int(age),
                float(height),
                goal
            )
            st.success("Client details updated.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.subheader("Account Status Management")

    if details[9] == "active":
        if st.button(
            "DEACTIVATE CLIENT ACCOUNT",
            key=f"deactivate_{client_id}"
        ):
            deactivate_client(user["id"], details[1])
            st.success("Client account deactivated.")
            st.rerun()

    elif details[9] in ("disabled", "rejected"):
        if st.button(
            "ACTIVATE CLIENT ACCOUNT",
            key=f"activate_{client_id}"
        ):
            activate_client(user["id"], details[1])
            st.success("Client account activated.")
            st.rerun()

    elif details[9] == "pending":
        st.info(
            "This client is pending approval. "
            "Use Registration Requests to review the application."
        )


def security_page(user):
    st.header("Security & System Activity")

    try:
        if database_health():
            st.success("Turso database connection successful.")
        else:
            st.error("Database health check failed.")
    except Exception as e:
        st.error(str(e))

    st.divider()
    st.subheader("Account Security")
    st.write("Authentication: Phase 1 bcrypt implementation")
    st.write("Authorization: Trainer role validation")
    st.write("Client onboarding: Approval required")
    st.write("Login protection: Failed-attempt lockout")
    st.write("Session: Idle timeout enabled")

    st.divider()
    st.subheader("Recent Activity Logs")

    logs = get_audit_logs(user["id"], limit=50)

    if logs:
        df = pd.DataFrame(
            logs,
            columns=["Event", "Username", "Details", "Timestamp"]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No activity logs available.")


# ==========================================================
# PHASE 4 - TRAINER & CLIENT FITNESS PROGRESS PAGES
# ==========================================================

def trainer_progress_page(user):
    st.title("📈 Fitness Progress Tracking")
    st.caption("Record and monitor your clients' fitness progress.")

    trainer_id = user["id"]

    clients = fetch_all("""
        SELECT c.user_id, c.full_name, u.username
        FROM clients c
        INNER JOIN users u ON c.user_id = u.id
        WHERE u.role = 'client'
          AND u.status = 'active'
        ORDER BY c.full_name
    """)

    if not clients:
        st.info("No active clients available.")
        return

    client_options = {
        f"{row[1]} (@{row[2]})": row[0]
        for row in clients
    }

    selected_name = st.selectbox(
        "Select client",
        list(client_options.keys())
    )
    client_id = client_options[selected_name]

    tab1, tab2, tab3 = st.tabs([
        "⚖️ Weight Tracking",
        "📏 Body Measurements",
        "📊 Progress History"
    ])

    with tab1:
        st.subheader("Record Body Weight")

        with st.form("weight_entry_form"):
            weight = st.number_input(
                "Weight (kg)",
                min_value=1.0,
                max_value=500.0,
                value=70.0,
                step=0.1
            )
            recorded_on = st.date_input("Recording date", value=date.today())
            notes = st.text_area(
                "Notes",
                placeholder="Workout progress, observations..."
            )
            submitted = st.form_submit_button(
                "Save Weight Entry",
                use_container_width=True
            )

            if submitted:
                try:
                    add_weight_entry(
                        trainer_id,
                        client_id,
                        weight,
                        recorded_on.isoformat(),
                        notes
                    )
                    st.success("Weight entry saved successfully.")
                    st.rerun()
                except (ValueError, PermissionError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Unable to save the weight entry.")

        st.divider()
        st.subheader("Weight History")

        try:
            weight_history = get_client_weight_history(trainer_id, client_id)
            if weight_history:
                for item in weight_history:
                    with st.container(border=True):
                        st.write(f"**Date:** {item[4]}")
                        st.write(f"**Weight:** {item[1]} kg")
                        st.write(
                            f"**BMI:** {item[2] if item[2] is not None else 'Not available'}"
                        )
                        if item[3]:
                            st.write(f"**Notes:** {item[3]}")
            else:
                st.info("No weight records available.")
        except Exception:
            st.error("Unable to load weight history.")

    with tab2:
        st.subheader("Record Body Measurements")

        with st.form("measurement_form"):
            col1, col2 = st.columns(2)

            with col1:
                waist = st.number_input("Waist (cm)", min_value=0.0, max_value=300.0, value=0.0)
                chest = st.number_input("Chest (cm)", min_value=0.0, max_value=300.0, value=0.0)
                hips = st.number_input("Hips (cm)", min_value=0.0, max_value=300.0, value=0.0)
                left_arm = st.number_input("Left arm (cm)", min_value=0.0, max_value=150.0, value=0.0)

            with col2:
                right_arm = st.number_input("Right arm (cm)", min_value=0.0, max_value=150.0, value=0.0)
                left_thigh = st.number_input("Left thigh (cm)", min_value=0.0, max_value=200.0, value=0.0)
                right_thigh = st.number_input("Right thigh (cm)", min_value=0.0, max_value=200.0, value=0.0)

            measurement_date = st.date_input(
                "Measurement date",
                value=date.today(),
                key="measurement_date"
            )
            measurement_notes = st.text_area("Measurement notes", key="measurement_notes")
            save_measurement = st.form_submit_button(
                "Save Measurements",
                use_container_width=True
            )

            if save_measurement:
                try:
                    values = [
                        waist, chest, hips, left_arm,
                        right_arm, left_thigh, right_thigh
                    ]
                    values = [value if value > 0 else None for value in values]

                    if all(value is None for value in values):
                        st.error("Enter at least one measurement.")
                    else:
                        add_body_measurement(
                            trainer_id,
                            client_id,
                            *values,
                            recorded_on=measurement_date.isoformat(),
                            notes=measurement_notes
                        )
                        st.success("Measurements saved successfully.")
                        st.rerun()
                except (ValueError, PermissionError) as error:
                    st.error(str(error))
                except Exception:
                    st.error("Unable to save measurements.")

        st.divider()
        st.subheader("Measurement History")

        try:
            measurements = get_client_measurement_history(trainer_id, client_id)
            if measurements:
                for item in measurements:
                    with st.container(border=True):
                        st.write(f"**Date:** {item[9]}")
                        measurement_names = [
                            "Waist", "Chest", "Hips",
                            "Left Arm", "Right Arm",
                            "Left Thigh", "Right Thigh"
                        ]
                        for index, name in enumerate(measurement_names):
                            value = item[index + 1]
                            if value is not None:
                                st.write(f"**{name}:** {value} cm")
                        if item[8]:
                            st.write(f"**Notes:** {item[8]}")
            else:
                st.info("No measurement records available.")
        except Exception:
            st.error("Unable to load measurement history.")

    with tab3:
        st.subheader("Client Weight Progress")

        try:
            history = get_client_weight_history(trainer_id, client_id)
            if history:
                chart_data = {
                    "Weight (kg)": [float(item[1]) for item in reversed(history)]
                }
                st.line_chart(chart_data)

                first_weight = float(history[-1][1])
                latest_weight = float(history[0][1])
                change = round(latest_weight - first_weight, 2)

                col1, col2, col3 = st.columns(3)
                col1.metric("Starting Weight", f"{first_weight} kg")
                col2.metric("Latest Weight", f"{latest_weight} kg")
                col3.metric("Total Change", f"{change} kg")

                st.caption(
                    "A negative change means weight decreased. "
                    "A positive change means weight increased."
                )
            else:
                st.info("Add weight entries to view the progress chart.")
        except Exception:
            st.error("Unable to calculate progress.")


def client_progress_page(client_user_id):
    st.title("📊 My Fitness Progress")
    st.caption("Track your fitness journey and progress.")

    try:
        summary = get_my_progress_summary(client_user_id)
        history = get_my_weight_history(client_user_id)
        measurements = get_my_measurement_history(client_user_id)

        if not history:
            st.info("Your trainer has not added any weight records yet.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Starting Weight", f"{summary['starting_weight']} kg")
            col2.metric("Current Weight", f"{summary['current_weight']} kg")
            col3.metric("Weight Change", f"{summary['weight_change']} kg")

            st.divider()
            st.subheader("My Weight Progress")

            chart_data = {
                "Weight (kg)": [float(item[0]) for item in history]
            }
            st.line_chart(chart_data)

            st.subheader("Weight History")
            for item in reversed(history):
                with st.container(border=True):
                    st.write(f"**Date:** {item[3]}")
                    st.write(f"**Weight:** {item[0]} kg")
                    bmi = item[1]
                    st.write(
                        f"**BMI:** {bmi if bmi is not None else 'Not available'}"
                    )
                    if item[2]:
                        st.write(f"**Trainer Notes:** {item[2]}")

        st.divider()
        st.subheader("My Body Measurements")

        if not measurements:
            st.info("No body measurements have been recorded yet.")
        else:
            measurement_names = [
                "Waist", "Chest", "Hips",
                "Left Arm", "Right Arm",
                "Left Thigh", "Right Thigh"
            ]
            for item in measurements:
                with st.container(border=True):
                    st.write(f"**Date:** {item[8]}")
                    for index, name in enumerate(measurement_names):
                        value = item[index]
                        if value is not None:
                            st.write(f"**{name}:** {value} cm")
                    if item[7]:
                        st.write(f"**Trainer Notes:** {item[7]}")

        st.caption(
            "Your progress records are entered and managed by your trainer."
        )

    except PermissionError:
        st.error("Your account does not have permission to view this page.")
        st.session_state.clear()
        st.rerun()
    except Exception:
        st.error("Unable to load your fitness progress.")


# ==========================================================
# PHASE 5 - WORKOUT MANAGEMENT PAGES
# ==========================================================

def trainer_workout_page(user):
    st.title("🏋️ Workout Plan Management")
    st.caption("Create, assign and monitor client workout plans.")

    trainer_id = user["id"]

    tab1, tab2, tab3 = st.tabs([
        "Create Plan",
        "Manage Plans",
        "Client Activity"
    ])

    with tab1:
        st.subheader("Create a New Workout Plan")

        clients = fetch_all("""
            SELECT c.user_id, c.full_name, u.username
            FROM clients c
            INNER JOIN users u ON u.id = c.user_id
            WHERE u.role = 'client'
              AND u.status = 'active'
            ORDER BY c.full_name
        """)

        if not clients:
            st.info("No active clients available.")
        else:
            client_options = {
                f"{row[1]} (@{row[2]})": row[0]
                for row in clients
            }

            selected_client = st.selectbox(
                "Select Client",
                list(client_options.keys()),
                key="workout_client"
            )

            with st.form("create_workout_plan_form"):
                plan_name = st.text_input(
                    "Workout Plan Name",
                    placeholder="Example: Beginner Strength Training"
                )
                description = st.text_area(
                    "Plan Description",
                    placeholder="Describe the purpose and focus of this plan."
                )
                duration = st.number_input(
                    "Duration (weeks)",
                    min_value=1,
                    max_value=52,
                    value=4
                )
                start_date = st.date_input("Start Date", value=date.today())

                create_plan = st.form_submit_button(
                    "Create Workout Plan",
                    use_container_width=True
                )

                if create_plan:
                    try:
                        plan_id = create_workout_plan(
                            trainer_id,
                            client_options[selected_client],
                            plan_name,
                            description,
                            duration,
                            start_date.isoformat()
                        )
                        st.session_state["new_workout_plan_id"] = plan_id
                        st.success("Workout plan created. Add exercises below.")
                    except (ValueError, PermissionError) as error:
                        st.error(str(error))
                    except Exception:
                        st.error("Unable to create workout plan.")

            new_plan_id = st.session_state.get("new_workout_plan_id")

            if new_plan_id:
                st.divider()
                st.subheader("Add Exercises to Your New Plan")

                try:
                    plans = get_trainer_workout_plans(trainer_id)
                    valid_plan_ids = [plan[0] for plan in plans]

                    if new_plan_id not in valid_plan_ids:
                        st.session_state.pop("new_workout_plan_id", None)
                        st.warning("The selected plan is unavailable.")
                    else:
                        with st.form("add_exercise_form"):
                            day = st.selectbox(
                                "Workout Day",
                                [
                                    "Monday", "Tuesday", "Wednesday",
                                    "Thursday", "Friday", "Saturday", "Sunday"
                                ]
                            )
                            exercise = st.text_input(
                                "Exercise Name",
                                placeholder="Example: Bench Press"
                            )

                            col1, col2 = st.columns(2)
                            with col1:
                                sets = st.number_input(
                                    "Sets",
                                    min_value=1,
                                    max_value=20,
                                    value=3
                                )
                                reps = st.text_input(
                                    "Reps",
                                    value="12",
                                    help="Examples: 12, 8-10, 30 seconds"
                                )
                            with col2:
                                rest = st.number_input(
                                    "Rest (seconds)",
                                    min_value=0,
                                    max_value=1800,
                                    value=60
                                )

                            instructions = st.text_area(
                                "Instructions",
                                placeholder="Exercise technique, equipment, etc."
                            )

                            add_exercise = st.form_submit_button(
                                "Add Exercise",
                                use_container_width=True
                            )

                            if add_exercise:
                                try:
                                    add_workout_exercise(
                                        trainer_id,
                                        new_plan_id,
                                        day,
                                        exercise,
                                        sets,
                                        reps,
                                        rest,
                                        instructions
                                    )
                                    st.success("Exercise added successfully.")
                                    st.rerun()
                                except (ValueError, PermissionError) as error:
                                    st.error(str(error))
                                except Exception:
                                    st.error("Unable to add exercise.")
                except Exception:
                    st.error("Unable to load the selected plan.")

    with tab2:
        st.subheader("Manage Workout Plans")

        try:
            plans = get_trainer_workout_plans(trainer_id)

            if not plans:
                st.info("No workout plans created yet.")
            else:
                plan_options = {
                    f"{plan[3]} – {plan[2]}": plan[0]
                    for plan in plans
                }

                selected_plan_name = st.selectbox(
                    "Choose Workout Plan",
                    list(plan_options.keys()),
                    key="manage_plan_select"
                )
                plan_id = plan_options[selected_plan_name]
                selected_plan = next(plan for plan in plans if plan[0] == plan_id)

                st.write(f"**Client:** {selected_plan[2]}")
                st.write(f"**Duration:** {selected_plan[5]} weeks")
                st.write(f"**Start:** {selected_plan[6]}")
                st.write(f"**End:** {selected_plan[7]}")
                st.write(f"**Status:** {selected_plan[8]}")

                if selected_plan[4]:
                    st.write(f"**Description:** {selected_plan[4]}")

                status_options = ["active", "paused", "completed"]
                new_status = st.selectbox(
                    "Plan Status",
                    status_options,
                    index=status_options.index(selected_plan[8])
                    if selected_plan[8] in status_options else 0,
                    key="plan_status"
                )

                if st.button("Update Plan Status"):
                    try:
                        update_workout_plan_status(trainer_id, plan_id, new_status)
                        st.success("Plan status updated.")
                        st.rerun()
                    except Exception:
                        st.error("Unable to update plan status.")

                st.divider()
                st.subheader("Exercises")

                exercises = get_trainer_plan_exercises(trainer_id, plan_id)
                if exercises:
                    for item in exercises:
                        with st.container(border=True):
                            st.write(f"**{item[2]}**")
                            st.write(f"Day: {item[1]}")
                            st.write(f"Sets: {item[3]}")
                            st.write(f"Reps: {item[4]}")
                            st.write(f"Rest: {item[5]} seconds")
                            if item[6]:
                                st.write(f"Instructions: {item[6]}")

                            if st.button(
                                "Delete Exercise",
                                key=f"delete_exercise_{item[0]}"
                            ):
                                try:
                                    delete_workout_exercise(
                                        trainer_id,
                                        plan_id,
                                        item[0]
                                    )
                                    st.success("Exercise deleted.")
                                    st.rerun()
                                except Exception:
                                    st.error("Unable to delete exercise.")
                else:
                    st.info("No exercises have been added.")

                st.divider()
                st.subheader("Workout Adherence")

                adherence = get_workout_adherence(trainer_id, plan_id)
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Exercises", adherence["total_exercises"])
                col2.metric("Completed Exercise Types", adherence["completed_entries"])
                col3.metric("Completion", f"{adherence['completion_percentage']}%")
                st.progress(min(adherence["completion_percentage"] / 100, 1.0))

        except PermissionError as error:
            st.error(str(error))
        except Exception:
            st.error("Unable to load workout plans.")

    with tab3:
        st.subheader("Client Workout Activity")

        clients = fetch_all("""
            SELECT c.user_id, c.full_name
            FROM clients c
            INNER JOIN users u ON u.id = c.user_id
            WHERE u.role = 'client'
              AND u.status = 'active'
            ORDER BY c.full_name
        """)

        if clients:
            client_options = {row[1]: row[0] for row in clients}
            selected = st.selectbox(
                "Select Client",
                list(client_options.keys()),
                key="activity_client"
            )

            try:
                activity = get_client_workout_activity(
                    trainer_id,
                    client_options[selected]
                )
                if activity:
                    for item in activity:
                        with st.container(border=True):
                            st.write(f"**Plan:** {item[0]}")
                            st.write(f"**Day:** {item[1]}")
                            st.write(f"**Exercise:** {item[2]}")
                            st.write(f"**Date:** {item[3]}")
                            if item[4] == 1:
                                st.success("Completed")
                            else:
                                st.warning("Not completed")
                            if item[5]:
                                st.write(f"Notes: {item[5]}")
                else:
                    st.info("No workout activity recorded yet.")
            except Exception:
                st.error("Unable to load client activity.")


def client_workout_page(client_user_id):
    st.title("💪 My Workout Plans")
    st.caption("View your assigned workouts and record your progress.")

    try:
        plans = get_my_workout_plans(client_user_id)

        if not plans:
            st.info("Your trainer has not assigned an active workout plan yet.")
            return

        plan_options = {
            f"{plan[1]} ({plan[4]} to {plan[5]})": plan[0]
            for plan in plans
        }

        selected_name = st.selectbox("Select Workout Plan", list(plan_options.keys()))
        plan_id = plan_options[selected_name]
        selected_plan = next(plan for plan in plans if plan[0] == plan_id)

        st.subheader(selected_plan[1])
        if selected_plan[2]:
            st.write(selected_plan[2])

        col1, col2, col3 = st.columns(3)
        col1.metric("Duration", f"{selected_plan[3]} weeks")
        col2.metric("Start Date", selected_plan[4])
        col3.metric("End Date", selected_plan[5])

        st.divider()

        exercises = get_my_workout_exercises(client_user_id, plan_id)
        completions = get_my_workout_completions(client_user_id, plan_id)
        today = date.today().isoformat()

        completed_today = {
            item[0]: item[2]
            for item in completions
            if item[1] == today
        }

        if not exercises:
            st.info("Your trainer has not added exercises yet.")
            return

        days = {}
        for exercise in exercises:
            days.setdefault(exercise[1], []).append(exercise)

        st.subheader("Your Workout Schedule")

        for day, day_exercises in days.items():
            with st.expander(day, expanded=True):
                for exercise in day_exercises:
                    exercise_id = exercise[0]
                    st.markdown(f"### {exercise[2]}")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Sets", exercise[3])
                    col2.metric("Reps", exercise[4])
                    col3.metric("Rest", f"{exercise[5]} sec")

                    if exercise[6]:
                        st.write(f"**Instructions:** {exercise[6]}")

                    is_completed = completed_today.get(exercise_id, 0) == 1
                    new_status = st.checkbox(
                        "Completed today",
                        value=bool(is_completed),
                        key=f"workout_done_{plan_id}_{exercise_id}_{today}"
                    )

                    if new_status != bool(is_completed):
                        try:
                            mark_exercise_complete(
                                client_user_id,
                                plan_id,
                                exercise_id,
                                today,
                                new_status
                            )
                            st.success("Workout progress updated.")
                            st.rerun()
                        except (ValueError, PermissionError) as error:
                            st.error(str(error))
                        except Exception:
                            st.error("Unable to update workout progress.")

                    st.divider()

        total = len(exercises)
        completed_count = sum(
            1 for exercise in exercises
            if completed_today.get(exercise[0], 0) == 1
        )
        percentage = round(completed_count / total * 100) if total else 0

        st.subheader("Today's Workout Progress")
        st.progress(percentage / 100)
        st.write(
            f"**{completed_count} of {total} exercises completed "
            f"({percentage}%).**"
        )

        st.divider()
        st.subheader("My Workout History")

        if completions:
            for item in completions:
                with st.container(border=True):
                    exercise_name = next(
                        (
                            exercise[2]
                            for exercise in exercises
                            if exercise[0] == item[0]
                        ),
                        "Exercise"
                    )
                    st.write(f"**Exercise:** {exercise_name}")
                    st.write(f"**Date:** {item[1]}")
                    if item[2] == 1:
                        st.success("Completed")
                    else:
                        st.warning("Not completed")
                    if item[3]:
                        st.write(f"**Notes:** {item[3]}")
        else:
            st.info("No workout completion history yet.")

    except PermissionError:
        st.error("You do not have permission to view this workout plan.")
        st.session_state.clear()
        st.rerun()
    except Exception:
        st.error("Unable to load your workout plans.")


# ==========================================================
# PHASE 6 - DIET & NUTRITION PAGES
# ==========================================================

def trainer_diet_page(user):
    st.title("🥗 Diet & Nutrition Management")
    st.caption("Create personalized nutrition plans for your clients.")

    trainer_id = user["id"]

    tab1, tab2, tab3 = st.tabs([
        "Create Diet Plan",
        "Manage Diet Plans",
        "Nutrition Activity"
    ])

    with tab1:
        st.subheader("Create a Diet Plan")

        clients = fetch_all("""
            SELECT c.user_id, c.full_name, u.username
            FROM clients c
            INNER JOIN users u ON u.id = c.user_id
            WHERE u.role = 'client'
              AND u.status = 'active'
            ORDER BY c.full_name
        """)

        if not clients:
            st.info("No active clients available.")
        else:
            client_options = {
                f"{row[1]} (@{row[2]})": row[0]
                for row in clients
            }

            selected_client = st.selectbox(
                "Select Client",
                list(client_options.keys()),
                key="diet_client"
            )

            with st.form("create_diet_plan_form"):
                plan_name = st.text_input(
                    "Diet Plan Name",
                    placeholder="Example: Fat Loss Nutrition Plan"
                )
                description = st.text_area("Diet Plan Description")

                st.markdown("### Daily Nutrition Targets")
                col1, col2 = st.columns(2)

                with col1:
                    calories = st.number_input(
                        "Daily Calories (kcal)",
                        min_value=1.0,
                        max_value=10000.0,
                        value=2000.0,
                        step=50.0
                    )
                    protein = st.number_input(
                        "Protein (g)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=100.0
                    )

                with col2:
                    carbs = st.number_input(
                        "Carbohydrates (g)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=200.0
                    )
                    fat = st.number_input(
                        "Fat (g)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=60.0
                    )

                duration = st.number_input(
                    "Plan Duration (weeks)",
                    min_value=1,
                    max_value=52,
                    value=4
                )
                start_date = st.date_input(
                    "Start Date",
                    value=date.today(),
                    key="diet_start_date"
                )

                create_plan = st.form_submit_button(
                    "Create Diet Plan",
                    use_container_width=True
                )

                if create_plan:
                    try:
                        plan_id = create_diet_plan(
                            trainer_id,
                            client_options[selected_client],
                            plan_name,
                            description,
                            calories,
                            protein,
                            carbs,
                            fat,
                            start_date.isoformat(),
                            duration
                        )
                        st.session_state["new_diet_plan_id"] = plan_id
                        st.success("Diet plan created. Add meals below.")
                    except (ValueError, PermissionError) as error:
                        st.error(str(error))
                    except Exception:
                        st.error("Unable to create diet plan.")

            new_plan_id = st.session_state.get("new_diet_plan_id")

            if new_plan_id:
                st.divider()
                st.subheader("Add Meals to Your New Plan")

                try:
                    plans = get_trainer_diet_plans(trainer_id)
                    valid_plan_ids = [plan[0] for plan in plans]

                    if new_plan_id not in valid_plan_ids:
                        st.session_state.pop("new_diet_plan_id", None)
                        st.warning("Selected diet plan is unavailable.")
                    else:
                        with st.form("add_diet_meal_form"):
                            meal_type = st.selectbox(
                                "Meal Type",
                                [
                                    "Breakfast",
                                    "Mid-Morning Snack",
                                    "Lunch",
                                    "Evening Snack",
                                    "Dinner",
                                    "Other"
                                ]
                            )
                            meal_name = st.text_input(
                                "Meal Name",
                                placeholder="Example: High Protein Breakfast"
                            )
                            food_items = st.text_area(
                                "Food Items",
                                placeholder="Example: 2 eggs, oats, banana"
                            )
                            quantity = st.text_input(
                                "Quantity / Serving Size",
                                placeholder="Example: 2 eggs, 50g oats"
                            )

                            st.markdown("### Meal Nutrition")
                            col1, col2 = st.columns(2)

                            with col1:
                                meal_calories = st.number_input(
                                    "Calories (kcal)",
                                    min_value=0.0,
                                    max_value=10000.0,
                                    value=0.0
                                )
                                meal_protein = st.number_input(
                                    "Protein (g)",
                                    min_value=0.0,
                                    max_value=1000.0,
                                    value=0.0
                                )

                            with col2:
                                meal_carbs = st.number_input(
                                    "Carbohydrates (g)",
                                    min_value=0.0,
                                    max_value=1000.0,
                                    value=0.0
                                )
                                meal_fat = st.number_input(
                                    "Fat (g)",
                                    min_value=0.0,
                                    max_value=1000.0,
                                    value=0.0
                                )

                            instructions = st.text_area(
                                "Instructions",
                                placeholder="Preparation, substitutions, timing..."
                            )

                            add_meal = st.form_submit_button(
                                "Add Meal",
                                use_container_width=True
                            )

                            if add_meal:
                                try:
                                    add_diet_meal(
                                        trainer_id,
                                        new_plan_id,
                                        meal_type,
                                        meal_name,
                                        food_items,
                                        quantity,
                                        meal_calories,
                                        meal_protein,
                                        meal_carbs,
                                        meal_fat,
                                        instructions
                                    )
                                    st.success("Meal added successfully.")
                                    st.rerun()
                                except (ValueError, PermissionError) as error:
                                    st.error(str(error))
                                except Exception:
                                    st.error("Unable to add meal.")
                except Exception:
                    st.error("Unable to load the new diet plan.")

    with tab2:
        st.subheader("Manage Diet Plans")

        try:
            plans = get_trainer_diet_plans(trainer_id)

            if not plans:
                st.info("No diet plans created yet.")
            else:
                plan_options = {
                    f"{plan[3]} – {plan[2]}": plan[0]
                    for plan in plans
                }

                selected_name = st.selectbox(
                    "Select Diet Plan",
                    list(plan_options.keys()),
                    key="manage_diet_plan"
                )
                plan_id = plan_options[selected_name]
                selected_plan = next(plan for plan in plans if plan[0] == plan_id)

                st.write(f"**Client:** {selected_plan[2]}")
                st.write(f"**Plan:** {selected_plan[3]}")
                st.write(f"**Daily Calories:** {selected_plan[5]} kcal")
                st.write(f"**Protein:** {selected_plan[6]} g")
                st.write(f"**Carbohydrates:** {selected_plan[7]} g")
                st.write(f"**Fat:** {selected_plan[8]} g")
                st.write(f"**Start Date:** {selected_plan[9]}")
                st.write(f"**End Date:** {selected_plan[10]}")
                st.write(f"**Status:** {selected_plan[11]}")

                status_options = ["active", "paused", "completed"]
                new_status = st.selectbox(
                    "Plan Status",
                    status_options,
                    index=(
                        status_options.index(selected_plan[11])
                        if selected_plan[11] in status_options else 0
                    ),
                    key="diet_plan_status"
                )

                if st.button("Update Diet Plan Status"):
                    try:
                        update_diet_plan_status(trainer_id, plan_id, new_status)
                        st.success("Diet plan status updated.")
                        st.rerun()
                    except Exception:
                        st.error("Unable to update diet plan status.")

                st.divider()
                st.subheader("Assigned Meals")

                meals = get_trainer_diet_meals(trainer_id, plan_id)
                if meals:
                    for meal in meals:
                        with st.container(border=True):
                            st.write(f"**{meal[1]} – {meal[2]}**")
                            st.write(f"**Food:** {meal[3]}")
                            st.write(f"**Quantity:** {meal[4]}")
                            st.write(f"**Calories:** {meal[5]} kcal")
                            st.write(f"**Protein:** {meal[6]} g")
                            st.write(f"**Carbs:** {meal[7]} g")
                            st.write(f"**Fat:** {meal[8]} g")

                            if meal[9]:
                                st.write(f"**Instructions:** {meal[9]}")

                            if st.button(
                                "Delete Meal",
                                key=f"delete_diet_meal_{meal[0]}"
                            ):
                                try:
                                    delete_diet_meal(trainer_id, plan_id, meal[0])
                                    st.success("Meal deleted.")
                                    st.rerun()
                                except Exception:
                                    st.error("Unable to delete meal.")
                else:
                    st.info("No meals have been added to this plan.")

                st.divider()
                st.subheader("Daily Meal Adherence")

                adherence = get_diet_plan_adherence(trainer_id, plan_id)
                col1, col2, col3 = st.columns(3)
                col1.metric("Planned Meals", adherence["total_meals"])
                col2.metric("Meals Consumed", adherence["consumed_meals"])
                col3.metric("Adherence", f"{adherence['adherence_percentage']}%")
                st.progress(min(adherence["adherence_percentage"] / 100, 1.0))
                st.caption("Adherence is calculated for today's date.")

        except PermissionError as error:
            st.error(str(error))
        except Exception:
            st.error("Unable to load diet plan details.")

    with tab3:
        st.subheader("Client Nutrition Activity")

        clients = fetch_all("""
            SELECT c.user_id, c.full_name
            FROM clients c
            INNER JOIN users u ON u.id = c.user_id
            WHERE u.role = 'client'
              AND u.status = 'active'
            ORDER BY c.full_name
        """)

        if clients:
            client_options = {row[1]: row[0] for row in clients}
            selected_client = st.selectbox(
                "Select Client",
                list(client_options.keys()),
                key="nutrition_activity_client"
            )
            activity_date = st.date_input(
                "Activity Date",
                value=date.today(),
                key="nutrition_activity_date"
            )

            try:
                activity = get_client_nutrition_activity(
                    trainer_id,
                    client_options[selected_client],
                    activity_date.isoformat()
                )
                if activity:
                    for item in activity:
                        with st.container(border=True):
                            st.write(f"**Plan:** {item[0]}")
                            st.write(f"**Meal:** {item[1]} – {item[2]}")
                            st.write(f"**Date:** {item[3]}")
                            if item[4] == 1:
                                st.success("Meal marked as consumed.")
                            else:
                                st.warning("Meal not consumed.")

                            st.write(
                                f"Calories: {item[5] if item[5] is not None else 'Planned estimate'}"
                            )
                            st.write(
                                f"Protein: {item[6] if item[6] is not None else 'Planned estimate'}"
                            )
                            st.write(
                                f"Carbs: {item[7] if item[7] is not None else 'Planned estimate'}"
                            )
                            st.write(
                                f"Fat: {item[8] if item[8] is not None else 'Planned estimate'}"
                            )
                            if item[9]:
                                st.write(f"**Notes:** {item[9]}")
                else:
                    st.info("No meal activity recorded for this date.")
            except Exception:
                st.error("Unable to load nutrition activity.")


def client_diet_page(client_user_id):
    st.title("🥗 My Diet & Nutrition")
    st.caption("View your diet plan and track your daily meals.")

    try:
        plans = get_my_diet_plans(client_user_id)

        if not plans:
            st.info("Your trainer has not assigned an active diet plan yet.")
            return

        plan_options = {
            f"{plan[1]} ({plan[7]} to {plan[8]})": plan[0]
            for plan in plans
        }

        selected_name = st.selectbox("Select Diet Plan", list(plan_options.keys()))
        plan_id = plan_options[selected_name]
        selected_plan = next(plan for plan in plans if plan[0] == plan_id)

        st.subheader(selected_plan[1])
        if selected_plan[2]:
            st.write(selected_plan[2])

        st.markdown("### Your Daily Nutrition Targets")
        col1, col2 = st.columns(2)
        col1.metric("Calories", f"{selected_plan[3]} kcal")
        col2.metric("Protein", f"{selected_plan[4]} g")

        col3, col4 = st.columns(2)
        col3.metric("Carbohydrates", f"{selected_plan[5]} g")
        col4.metric("Fat", f"{selected_plan[6]} g")

        st.caption(f"Plan duration: {selected_plan[7]} to {selected_plan[8]}")
        st.divider()

        selected_date = st.date_input(
            "Select Meal Tracking Date",
            value=date.today(),
            key="client_diet_tracking_date"
        )
        tracking_date = selected_date.isoformat()

        meals = get_my_diet_meals(client_user_id, plan_id)
        logs = get_my_meal_logs(client_user_id, plan_id, tracking_date)
        log_map = {row[0]: row for row in logs}

        st.subheader("Your Daily Meal Schedule")

        if not meals:
            st.info("Your trainer has not added meals yet.")
            return

        for meal in meals:
            meal_id = meal[0]
            existing_log = log_map.get(meal_id)
            is_consumed = existing_log[1] == 1 if existing_log else False

            with st.container(border=True):
                st.markdown(f"### {meal[1]} – {meal[2]}")
                st.write(f"**Food Items:** {meal[3]}")
                if meal[4]:
                    st.write(f"**Quantity:** {meal[4]}")

                col1, col2 = st.columns(2)
                col1.write(f"Calories: {meal[5]} kcal")
                col1.write(f"Protein: {meal[6]} g")
                col2.write(f"Carbs: {meal[7]} g")
                col2.write(f"Fat: {meal[8]} g")

                if meal[9]:
                    st.write(f"**Instructions:** {meal[9]}")

                with st.form(f"meal_log_form_{plan_id}_{meal_id}_{tracking_date}"):
                    consumed = st.checkbox(
                        "I consumed this meal",
                        value=is_consumed
                    )
                    notes = st.text_input(
                        "Notes (optional)",
                        value=existing_log[6] if existing_log else ""
                    )
                    save_meal = st.form_submit_button(
                        "Save Meal Status",
                        use_container_width=True
                    )

                    if save_meal:
                        try:
                            log_meal_consumption(
                                client_user_id,
                                plan_id,
                                meal_id,
                                tracking_date,
                                consumed,
                                notes=notes
                            )
                            st.success("Meal status saved.")
                            st.rerun()
                        except (ValueError, PermissionError) as error:
                            st.error(str(error))
                        except Exception:
                            st.error("Unable to save meal status.")

                if is_consumed:
                    st.success("Already marked as consumed.")
                else:
                    st.info("Not yet marked as consumed.")

        st.divider()
        st.subheader("Daily Nutrition Summary")

        summary = get_my_nutrition_summary(
            client_user_id,
            plan_id,
            tracking_date
        )

        col1, col2 = st.columns(2)
        col1.metric(
            "Meals Consumed",
            f"{summary['consumed_meals']} / {summary['total_meals']}"
        )
        col2.metric("Estimated Calories", f"{summary['calories']} kcal")

        col3, col4, col5 = st.columns(3)
        col3.metric("Protein", f"{summary['protein']} g")
        col4.metric("Carbs", f"{summary['carbs']} g")
        col5.metric("Fat", f"{summary['fat']} g")

        calorie_target = float(selected_plan[3] or 0)
        if calorie_target > 0:
            calorie_progress = min(summary["calories"] / calorie_target, 1.0)
            st.write("Calorie target progress")
            st.progress(calorie_progress)
            st.caption(
                f"{summary['calories']} of {calorie_target} kcal recorded."
            )

        st.caption(
            "Nutrition totals use the planned meal values as estimates "
            "unless actual intake values are recorded. "
            "They are not a substitute for measured food tracking."
        )

    except PermissionError:
        st.error("You do not have permission to access this diet plan.")
        st.session_state.clear()
        st.rerun()
    except Exception:
        st.error("Unable to load your diet plan.")


# ==========================================================
# PHASE 7 - TRAINER AI FITNESS ASSISTANT
# ==========================================================

def trainer_ai_page(user):
    st.title("🤖 FITPRO AI Assistant")
    st.caption("AI-powered fitness assistance for trainers.")

    trainer_id = user["id"]

    try:
        verify_trainer(trainer_id)
    except PermissionError:
        st.error("Trainer access required.")
        st.session_state.clear()
        st.rerun()
        return

    st.info(
        "AI-generated content is a draft. "
        "Review and approve it before assigning it to clients."
    )

    tab1, tab2 = st.tabs([
        "AI Fitness Tools",
        "AI Chat Assistant"
    ])

    with tab1:
        st.subheader("AI Fitness Tools")

        clients = fetch_all("""
            SELECT c.user_id, c.full_name, u.username
            FROM clients c
            INNER JOIN users u ON u.id = c.user_id
            WHERE u.role = 'client'
              AND u.status = 'active'
            ORDER BY c.full_name
        """)

        if not clients:
            st.info("No active clients available.")
        else:
            client_options = {
                f"{row[1]} (@{row[2]})": row[0]
                for row in clients
            }

            selected_client = st.selectbox(
                "Select Client",
                list(client_options.keys()),
                key="ai_selected_client"
            )
            client_id = client_options[selected_client]

            task_labels = {
                "Workout Plan Generator": "workout_plan",
                "Diet Plan Generator": "diet_plan",
                "Progress Analyzer": "progress_analysis",
                "Fitness Recommendations": "fitness_recommendations",
                "Client Summary Generator": "client_summary"
            }

            selected_task = st.selectbox(
                "Choose AI Tool",
                list(task_labels.keys())
            )

            trainer_instruction = st.text_area(
                "Additional Instructions",
                placeholder=(
                    "Example: Create a beginner-friendly "
                    "3-day workout plan using basic gym equipment."
                ),
                height=120
            )

            if st.button("Generate AI Suggestions", use_container_width=True):
                try:
                    with st.spinner("FITPRO AI is analyzing the records..."):
                        context = get_ai_client_context(trainer_id, client_id)
                        answer = generate_ai_response(
                            trainer_id,
                            task_labels[selected_task],
                            client_context=context,
                            question=trainer_instruction
                        )
                    st.session_state["fitpro_ai_result"] = answer
                except (ValueError, PermissionError) as error:
                    st.error(str(error))
                except Exception:
                    st.error(
                        "AI request failed. Check your Groq API "
                        "configuration, model availability and quota."
                    )

            result = st.session_state.get("fitpro_ai_result")
            if result:
                st.divider()
                st.subheader("AI Generated Draft")
                st.markdown(result)
                st.download_button(
                    "Download AI Draft",
                    data=result,
                    file_name="fitpro_ai_draft.md",
                    mime="text/markdown"
                )

    with tab2:
        st.subheader("Ask FITPRO AI")
        st.caption(
            "Ask general fitness-management questions. "
            "Do not include unnecessary personal or medical information."
        )

        question = st.text_area(
            "Your Question",
            placeholder=(
                "Example: What should a beginner focus on "
                "during the first four weeks of strength training?"
            ),
            height=150,
            key="fitpro_ai_question"
        )

        if st.button("Ask FITPRO AI", use_container_width=True):
            try:
                with st.spinner("Generating response..."):
                    answer = generate_ai_response(
                        trainer_id,
                        "general_chat",
                        question=question
                    )
                st.session_state["fitpro_ai_chat_answer"] = answer
            except (ValueError, PermissionError) as error:
                st.error(str(error))
            except Exception:
                st.error(
                    "Unable to connect to the AI service. "
                    "Check your API key and model configuration."
                )

        chat_answer = st.session_state.get("fitpro_ai_chat_answer")
        if chat_answer:
            st.divider()
            st.subheader("FITPRO AI Response")
            st.markdown(chat_answer)


# ==========================================================
# PHASE 8 - REPORTS & ANALYTICS
# ==========================================================

def _report_period_picker(key_prefix):
    today = date.today()
    default_start = today - timedelta(days=30)

    selected = st.date_input(
        "Report period",
        value=(default_start, today),
        key=f"{key_prefix}_period"
    )

    if not isinstance(selected, (tuple, list)) or len(selected) != 2:
        st.info("Select both a start date and an end date.")
        return None

    start_date, end_date = selected

    if start_date is None or end_date is None:
        st.info("Select both report dates.")
        return None

    if start_date > end_date:
        st.error("Start date cannot be after end date.")
        return None

    return start_date, end_date


def _show_client_report_analytics(report_data):
    weights = report_data["weights"]
    workouts = report_data["workouts"]
    diet_activity = report_data["diet_activity"]

    st.subheader("Weight Analytics")

    if weights:
        start_weight = float(weights[0][0])
        latest_weight = float(weights[-1][0])
        change = round(latest_weight - start_weight, 2)

        col1, col2, col3 = st.columns(3)
        col1.metric("Starting Weight", f"{start_weight:.2f} kg")
        col2.metric("Latest Weight", f"{latest_weight:.2f} kg")
        col3.metric("Weight Change", f"{change:+.2f} kg")

        st.line_chart({
            "Weight (kg)": [float(item[0]) for item in weights]
        })

        weight_table = [
            {
                "Date": item[3],
                "Weight (kg)": item[0],
                "BMI": item[1]
            }
            for item in weights
        ]
        st.dataframe(weight_table, use_container_width=True, hide_index=True)
    else:
        st.info("No weight entries in this report period.")

    st.divider()
    st.subheader("Workout Analytics")

    if workouts:
        completed = sum(1 for item in workouts if item[4] == 1)
        total = len(workouts)
        percentage = round(completed / total * 100, 1) if total else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Workout Entries", total)
        col2.metric("Completed", completed)
        col3.metric("Completion Rate", f"{percentage}%")

        st.progress(percentage / 100)

        workout_by_date = {}
        for item in workouts:
            day = item[3]
            workout_by_date.setdefault(day, {"Completed": 0, "Not completed": 0})
            if item[4] == 1:
                workout_by_date[day]["Completed"] += 1
            else:
                workout_by_date[day]["Not completed"] += 1

        sorted_dates = sorted(workout_by_date)

        st.dataframe(
            [
                {
                    "Date": day,
                    "Completed": workout_by_date[day]["Completed"],
                    "Not completed": workout_by_date[day]["Not completed"]
                }
                for day in sorted_dates
            ],
            use_container_width=True,
            hide_index=True
        )

        st.bar_chart({
            "Completed": [workout_by_date[day]["Completed"] for day in sorted_dates],
            "Not completed": [workout_by_date[day]["Not completed"] for day in sorted_dates]
        })
    else:
        st.info("No workout completion records in this period.")

    st.divider()
    st.subheader("Nutrition Analytics")

    if diet_activity:
        consumed = sum(1 for item in diet_activity if item[4] == 1)
        total = len(diet_activity)
        percentage = round(consumed / total * 100, 1) if total else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Meal Log Entries", total)
        col2.metric("Consumed", consumed)
        col3.metric("Meal Adherence", f"{percentage}%")

        st.progress(percentage / 100)

        diet_by_date = {}
        for item in diet_activity:
            day = item[3]
            diet_by_date.setdefault(day, {"Consumed": 0, "Not consumed": 0})
            if item[4] == 1:
                diet_by_date[day]["Consumed"] += 1
            else:
                diet_by_date[day]["Not consumed"] += 1

        sorted_dates = sorted(diet_by_date)

        st.dataframe(
            [
                {
                    "Date": day,
                    "Consumed": diet_by_date[day]["Consumed"],
                    "Not consumed": diet_by_date[day]["Not consumed"]
                }
                for day in sorted_dates
            ],
            use_container_width=True,
            hide_index=True
        )

        st.bar_chart({
            "Consumed": [diet_by_date[day]["Consumed"] for day in sorted_dates],
            "Not consumed": [diet_by_date[day]["Not consumed"] for day in sorted_dates]
        })
    else:
        st.info("No meal activity records in this period.")


def trainer_reports_page(user):
    st.title("📊 Reports & Analytics")
    st.caption("Review client performance and generate PDF reports.")

    trainer_id = user["id"]
    verify_trainer(trainer_id)

    tab1, tab2 = st.tabs(["Gym Analytics", "Client Reports"])

    with tab1:
        st.subheader("Gym Overview")

        try:
            stats = get_trainer_analytics(trainer_id)

            col1, col2, col3 = st.columns(3)
            col1.metric("Active Clients", stats["active_clients"])
            col2.metric("Pending Registrations", stats["pending_clients"])
            col3.metric("Workout Plans", stats["workout_plans"])

            col4, col5, col6 = st.columns(3)
            col4.metric("Diet Plans", stats["diet_plans"])
            col5.metric("Weight Records", stats["weight_entries"])
            col6.metric("Completed Workouts", stats["completed_workouts"])

            st.metric("Consumed Meal Entries", stats["consumed_meals"])
            st.caption(
                "These are cumulative database counts, not period-specific rates."
            )
        except Exception:
            st.error("Unable to load gym analytics.")

    with tab2:
        st.subheader("Individual Client Report")

        clients = fetch_all("""
            SELECT c.user_id, c.full_name, u.username
            FROM clients c
            INNER JOIN users u ON u.id = c.user_id
            WHERE u.role = 'client'
              AND u.status = 'active'
            ORDER BY c.full_name
        """)

        if not clients:
            st.info("No active clients available.")
            return

        client_options = {
            f"{row[1]} (@{row[2]})": row[0]
            for row in clients
        }

        selected_client = st.selectbox(
            "Select Client",
            list(client_options.keys()),
            key="report_selected_client"
        )
        client_id = client_options[selected_client]

        period = _report_period_picker("trainer_report")
        if period is None:
            return

        start_date, end_date = period

        try:
            report_data = get_client_report_data(
                trainer_id,
                client_id,
                start_date.isoformat(),
                end_date.isoformat()
            )

            _show_client_report_analytics(report_data)

            st.divider()
            st.subheader("Download Client Report")

            pdf_bytes = generate_client_pdf_report(
                report_data,
                generated_by="FITPRO Trainer"
            )

            st.download_button(
                "📄 Download Client PDF Report",
                data=pdf_bytes,
                file_name=f"fitpro_client_report_{start_date}_{end_date}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            st.divider()
            st.subheader("AI Report Summary")
            st.caption(
                "Optional trainer-only summary generated from the selected report records."
            )

            if st.button("Generate AI Report Summary", use_container_width=True):
                context = {
                    "report_period": {
                        "start": report_data["start_date"],
                        "end": report_data["end_date"]
                    },
                    "weights": report_data["weights"][-20:],
                    "measurements": report_data["measurements"][-10:],
                    "workouts": report_data["workouts"][-30:],
                    "diet_activity": report_data["diet_activity"][-30:]
                }

                with st.spinner("Generating report summary..."):
                    answer = generate_ai_response(
                        trainer_id,
                        "client_summary",
                        client_context=context,
                        question=(
                            "Summarize this client's recorded fitness "
                            "activity for the selected reporting period. "
                            "Separate facts from suggestions. Mention "
                            "missing data and avoid medical conclusions."
                        )
                    )

                st.session_state["phase8_ai_summary"] = {
                    "client_id": client_id,
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "answer": answer
                }

            saved_summary = st.session_state.get("phase8_ai_summary")
            if (
                saved_summary
                and saved_summary["client_id"] == client_id
                and saved_summary["start"] == start_date.isoformat()
                and saved_summary["end"] == end_date.isoformat()
            ):
                st.markdown(saved_summary["answer"])
                st.download_button(
                    "Download AI Summary",
                    data=saved_summary["answer"],
                    file_name="fitpro_ai_report_summary.md",
                    mime="text/markdown"
                )

        except PermissionError as error:
            st.error(str(error))
        except Exception:
            st.error("Unable to generate this client report.")


def client_reports_page(user):
    st.title("📊 My Reports & Analytics")
    st.caption("View and download your personal fitness report.")

    client_user_id = user["id"]

    try:
        verify_client(client_user_id)

        period = _report_period_picker("client_report")
        if period is None:
            return

        start_date, end_date = period

        report_data = get_my_report_data(
            client_user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )

        st.subheader("My Fitness Analytics")
        _show_client_report_analytics(report_data)

        st.divider()
        st.subheader("Download My Fitness Report")

        pdf_bytes = generate_client_pdf_report(
            report_data,
            generated_by="FITPRO"
        )

        st.download_button(
            "📄 Download My Fitness PDF",
            data=pdf_bytes,
            file_name=f"my_fitpro_report_{start_date}_{end_date}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.caption(
            "This report contains only your own recorded fitness information."
        )

    except PermissionError:
        st.error("You do not have permission to view this report.")
        st.session_state.clear()
        st.rerun()
    except Exception:
        st.error("Unable to generate your personal report.")


# ==================================================
# PHASE 3 - CLIENT DASHBOARD
# ==================================================

def client_dashboard(user):
    require_role(["client"])

    client_user_id = user["id"]

    try:
        dashboard = get_my_dashboard(client_user_id)
        profile = dashboard["profile"]
        trainer = dashboard["trainer"]
        account = get_my_account_status(client_user_id)
    except PermissionError:
        st.error("You are not authorized to access this account.")
        st.session_state.pop("user", None)
        st.rerun()
        return
    except Exception as e:
        st.error("Unable to load your dashboard.")
        st.code(str(e))
        return

    with st.sidebar:
        st.markdown("## 🔴 FITPRO")
        st.caption("CLIENT PORTAL")
        st.write(f"Welcome, {profile[2]}")
        show_notification_summary(user)

        st.divider()

        page = st.radio(
            "MY ACCOUNT",
            [
                "My Dashboard",
                "My Profile",
                "My Trainer",
                "My Account",
                "My Progress",
                "My Workouts",
                "My Diet",
                "My Reports",
                "Notifications"
            ]
        )

        st.divider()
        st.success("Account Active")

        if st.button("LOGOUT", use_container_width=True):
            logout_current_user()

    safe_client_name = html.escape(str(profile[2] or "Client"))

    def client_banner():
        st.markdown(f"""
        <div class="fitpro-hero">
            <div class="fitpro-kicker">
                YOUR FITNESS JOURNEY
            </div>
            <div class="fitpro-title">
                WELCOME,
                <span class="fitpro-red">
                    {safe_client_name}
                </span>
            </div>
            <p class="small-muted">
                Stay consistent. Stay strong.
                Your fitness journey starts here.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")

    if page == "My Dashboard":
        client_banner()
        st.header("My Fitness Overview")

        col1, col2, col3 = st.columns(3)
        col1.metric("My Fitness Goal", profile[8] or "Not assigned")
        col2.metric(
            "My Height",
            f"{profile[7]} cm" if profile[7] else "Not available"
        )
        col3.metric(
            "My Age",
            profile[6] if profile[6] else "Not available"
        )

        st.divider()
        st.subheader("My Personal Information")

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Name:** {profile[2]}")
            st.write(f"**Username:** {profile[3]}")
            st.write(f"**Email:** {profile[4] or 'Not provided'}")

        with c2:
            st.write(f"**Phone:** {profile[5] or 'Not provided'}")
            st.write(
                f"**Height:** {profile[7]} cm"
                if profile[7] else "**Height:** Not available"
            )
            st.write(f"**Goal:** {profile[8] or 'Not assigned'}")

        st.divider()
        st.subheader("Your Account")
        st.success(f"Account status: {account[2].upper()}")
        st.caption(f"Member since: {account[3]}")

        st.divider()
        st.subheader("Your Personal Trainer")

        if trainer:
            tc1, tc2 = st.columns([1, 3])
            with tc1:
                if trainer[3]:
                    st.image(trainer[3], use_container_width=True)
                else:
                    st.markdown("## 🏋️")

            with tc2:
                st.markdown(f"### {trainer[0]}")
                st.write(trainer[1] or "Fitness Trainer")
                st.write(f"Experience: {trainer[2] or 'Not specified'}")
                st.write(f"Achievements: {trainer[4] or 'Not specified'}")
        else:
            st.info("Trainer information is not available yet.")

    elif page == "My Profile":
        st.header("My Personal Profile")
        st.info(
            "Your personal information is managed by your gym trainer."
        )

        st.subheader("Personal Details")
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Full Name", value=profile[2] or "", disabled=True)
            st.text_input("Username", value=profile[3] or "", disabled=True)
            st.text_input("Email", value=profile[4] or "", disabled=True)

        with col2:
            st.text_input("Phone Number", value=profile[5] or "", disabled=True)
            st.text_input("Age", value=str(profile[6] or ""), disabled=True)
            st.text_input(
                "Height",
                value=f"{profile[7]} cm" if profile[7] else "",
                disabled=True
            )

        st.text_input("Fitness Goal", value=profile[8] or "", disabled=True)
        st.caption(
            "Contact your trainer if you need to correct your profile information."
        )

    elif page == "My Trainer":
        st.header("My Personal Trainer")

        if trainer:
            if trainer[3]:
                st.image(trainer[3], width=220)
            else:
                st.markdown("## 🏋️")

            st.subheader(trainer[0])
            st.write(trainer[1] or "Personal Trainer")
            st.write(f"Experience: {trainer[2] or 'Not specified'}")

            st.divider()
            st.subheader("Achievements")
            st.write(trainer[4] or "No achievements listed.")

            st.divider()
            st.subheader("About Trainer")
            st.write(trainer[5] or "No biography available.")
        else:
            st.warning("Trainer profile has not been configured.")

    elif page == "My Account":
        st.header("My Account Information")

        st.write(f"**Username:** {account[0]}")
        st.write(f"**Role:** {account[1].title()}")
        st.write(f"**Status:** {account[2].title()}")
        st.write(f"**Registration Date:** {account[3]}")

        st.divider()
        st.subheader("Account Security")
        st.success("Your account is authenticated.")
        st.write(
            "Your dashboard only retrieves information "
            "associated with your authenticated account."
        )
        st.warning("Never share your password with anyone.")

    elif page == "My Progress":
        client_progress_page(client_user_id)

    elif page == "My Workouts":
        client_workout_page(client_user_id)

    elif page == "My Diet":
        client_diet_page(client_user_id)

    elif page == "My Reports":
        client_reports_page(user)

    elif page == "Notifications":
        notification_center(user)


# ==================================================
# TRAINER MAIN DASHBOARD
# ==================================================

def trainer_dashboard(user):
    require_role(["trainer"])

    initialize_trainer_profile(user["id"])
    profile = get_trainer_profile(user["id"])

    dashboard_header(profile)

    with st.sidebar:
        st.markdown("## 🔴 FITPRO")
        st.caption("TRAINER CONTROL PANEL")
        show_notification_summary(user)

        st.divider()

        page = st.radio(
            "NAVIGATION",
            [
                "Dashboard",
                "Trainer Profile",
                "Registration Requests",
                "Client Management",
                "Fitness Progress",
                "Workout Management",
                "Diet & Nutrition",
                "AI Fitness Assistant",
                "Reports & Analytics",
                "Notifications",
                "Security"
            ]
        )

        st.divider()
        st.write(f"Logged in: {user['username']}")

        if st.button("LOGOUT", use_container_width=True):
            logout_current_user()

    if page == "Dashboard":
        dashboard_overview(user)
    elif page == "Trainer Profile":
        trainer_profile_page(user)
    elif page == "Registration Requests":
        registration_requests_page(user)
    elif page == "Client Management":
        client_management_page(user)
    elif page == "Fitness Progress":
        trainer_progress_page(user)
    elif page == "Workout Management":
        trainer_workout_page(user)
    elif page == "Diet & Nutrition":
        trainer_diet_page(user)
    elif page == "AI Fitness Assistant":
        trainer_ai_page(user)
    elif page == "Reports & Analytics":
        trainer_reports_page(user)
    elif page == "Notifications":
        notification_center(user)
    elif page == "Security":
        security_page(user)


# ==================================================
# APPLICATION ENTRY POINT
# ==================================================

def main():
    try:
        initialize_database()
        create_phase4_tables()
        create_phase5_tables()
        create_phase6_tables()
        create_phase9_tables()
        bootstrap_trainer()
    except Exception as e:
        st.error(
            "FITPRO initialization failed. "
            "Check your database configuration."
        )
        st.code(str(e))
        st.stop()

    if "user" not in st.session_state:
        login_screen()
        return

    enforce_session_timeout()

    user = st.session_state["user"]

    if user["role"] == "trainer":
        trainer_dashboard(user)
    elif user["role"] == "client":
        client_dashboard(user)
    else:
        st.session_state.pop("user", None)
        st.error("Invalid account role. Please log in again.")


if __name__ == "__main__":
    main()