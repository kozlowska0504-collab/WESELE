import streamlit as st
from supabase import create_client
from supabase.client import ClientOptions

# =========================
# KONFIGURACJA
# =========================

st.set_page_config(
    page_title="Nasze wesele",
    page_icon="💍",
    layout="wide"
)

# Dane Supabase będą zapisane jako sekrety,
# a NIE bezpośrednio w kodzie na GitHubie.
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_KEY"],
    options=ClientOptions(schema="public")
)


# =========================
# WYGLĄD
# =========================

st.markdown("""
<style>

    .stApp {
        background-color: #faf8f5;
    }

    h1, h2, h3 {
        color: #4b4038;
    }

    [data-testid="stSidebar"] {
        background-color: #f1ebe5;
    }

    div[data-testid="stMetric"] {
        background: white;
        border-radius: 16px;
        padding: 15px;
        border: 1px solid #e8e0d8;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

</style>
""", unsafe_allow_html=True)


# =========================
# FUNKCJE
# =========================

def get_categories():
    response = (
        supabase
        .table("categories")
        .select("*")
        .order("position")
        .execute()
    )
    return response.data


def get_tasks():
    response = (
        supabase
        .table("tasks")
        .select("*")
        .order("created_at")
        .execute()
    )
    return response.data


def get_guests():
    response = (
        supabase
        .table("guests")
        .select("*")
        .order("name")
        .execute()
    )
    return response.data


def get_budget():
    response = (
        supabase
        .table("budget")
        .select("*")
        .order("created_at")
        .execute()
    )
    return response.data


# =========================
# MENU
# =========================

st.sidebar.title("💍 NASZE WESELE")
st.sidebar.caption("Planner organizacji")

page = st.sidebar.radio(
    "Menu",
    [
        "🏠 Strona główna",
        "✅ Organizacja",
        "👥 Lista gości",
        "💰 Budżet"
    ],
    label_visibility="collapsed"
)


# =========================
# STRONA GŁÓWNA
# =========================

if page == "🏠 Strona główna":

    st.title("💍 Nasze wesele")
    st.write("Wszystko, co trzeba zorganizować, w jednym miejscu.")

    categories = get_categories()
    tasks = get_tasks()
    guests = get_guests()
    budget = get_budget()

    completed_tasks = sum(
        1 for task in tasks
        if task["completed"]
    )

    all_tasks = len(tasks)

    confirmed_guests = sum(
        1 for guest in guests
        if guest["status"] == "Potwierdzony"
    )

    estimated_budget = sum(
        float(item["estimated_price"] or 0)
        for item in budget
    )

    actual_budget = sum(
        float(item["actual_price"] or 0)
        for item in budget
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Zadania",
            f"{completed_tasks}/{all_tasks}"
        )

    with col2:
        st.metric(
            "Goście",
            len(guests)
        )

    with col3:
        st.metric(
            "Potwierdzili",
            confirmed_guests
        )

    with col4:
        st.metric(
            "Wydano",
            f"{actual_budget:,.2f} zł"
        )

    st.divider()

    st.subheader("Postęp organizacji")

    if all_tasks > 0:
        progress = completed_tasks / all_tasks
        st.progress(progress)

        st.write(
            f"Ukończono **{completed_tasks} z {all_tasks} zadań**."
        )
    else:
        st.info(
            "Nie masz jeszcze żadnych zadań. "
            "Dodaj pierwsze w zakładce Organizacja."
        )

    st.divider()

    st.subheader("Budżet")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Planowany",
            f"{estimated_budget:,.2f} zł"
        )

    with col2:
        st.metric(
            "Wydano",
            f"{actual_budget:,.2f} zł"
        )

    with col3:
        remaining = estimated_budget - actual_budget

        st.metric(
            "Pozostało",
            f"{remaining:,.2f} zł"
        )


# =========================
# ORGANIZACJA
# =========================

elif page == "✅ Organizacja":

    st.title("✅ Organizacja")

    categories = get_categories()
    tasks = get_tasks()

    tab1, tab2 = st.tabs(
        [
            "📋 Zadania",
            "➕ Dodaj"
        ]
    )

    # ---------- ZADANIA ----------

    with tab1:

        if not categories:

            st.info(
                "Najpierw dodaj kategorię."
            )

        for category in categories:

            category_id = category["id"]
            category_name = category["name"]

            category_tasks = [
                task
                for task in tasks
                if task["category_id"] == category_id
            ]

            with st.expander(
                f"📁 {category_name} ({len(category_tasks)})",
                expanded=True
            ):

                if not category_tasks:
                    st.caption(
                        "Brak zadań w tej kategorii."
                    )

                for task in category_tasks:

                    col1, col2 = st.columns(
                        [8, 1]
                    )

                    with col1:

                        checked = st.checkbox(
                            task["title"],
                            value=task["completed"],
                            key=f"task_{task['id']}"
                        )

                        if checked != task["completed"]:

                            supabase.table(
                                "tasks"
                            ).update(
                                {
                                    "completed": checked
                                }
                            ).eq(
                                "id",
                                task["id"]
                            ).execute()

                            st.rerun()

                        if task["notes"]:
                            st.caption(
                                task["notes"]
                            )

                    with col2:

                        if st.button(
                            "🗑️",
                            key=f"delete_task_{task['id']}"
                        ):

                            supabase.table(
                                "tasks"
                            ).delete().eq(
                                "id",
                                task["id"]
                            ).execute()

                            st.rerun()

    # ---------- DODAWANIE ----------

    with tab2:

        st.subheader("Dodaj kategorię")

        with st.form("category_form"):

            category_name = st.text_input(
                "Nazwa kategorii",
                placeholder="np. Sala, Fotograf, Dekoracje"
            )

            submit_category = st.form_submit_button(
                "Dodaj kategorię"
            )

            if submit_category and category_name:

                supabase.table(
                    "categories"
                ).insert(
                    {
                        "name": category_name
                    }
                ).execute()

                st.success(
                    "Kategoria została dodana."
                )

                st.rerun()

        st.divider()

        st.subheader("Dodaj zadanie")

        categories = get_categories()

        if categories:

            category_names = {
                category["name"]: category["id"]
                for category in categories
            }

            with st.form("task_form"):

                task_title = st.text_input(
                    "Zadanie",
                    placeholder="np. podpisać umowę z fotografem"
                )

                selected_category = st.selectbox(
                    "Kategoria",
                    list(category_names.keys())
                )

                task_notes = st.text_area(
                    "Notatka",
                    placeholder="Opcjonalnie..."
                )

                submit_task = st.form_submit_button(
                    "Dodaj zadanie"
                )

                if submit_task and task_title:

                    supabase.table(
                        "tasks"
                    ).insert(
                        {
                            "title": task_title,
                            "category_id":
                                category_names[selected_category],
                            "notes": task_notes,
                            "completed": False
                        }
                    ).execute()

                    st.success(
                        "Zadanie zostało dodane."
                    )

                    st.rerun()

        else:

            st.warning(
                "Najpierw dodaj kategorię."
            )


# =========================
# LISTA GOŚCI
# =========================

elif page == "👥 Lista gości":

    st.title("👥 Lista gości")

    guests = get_guests()

    total_guests = len(guests)

    confirmed = sum(
        1 for guest in guests
        if guest["status"] == "Potwierdzony"
    )

    declined = sum(
        1 for guest in guests
        if guest["status"] == "Odmówił"
    )

    waiting = total_guests - confirmed - declined

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Wszyscy",
        total_guests
    )

    col2.metric(
        "Potwierdzili",
        confirmed
    )

    col3.metric(
        "Odmówili",
        declined
    )

    col4.metric(
        "Brak odpowiedzi",
        waiting
    )

    tab1, tab2 = st.tabs(
        [
            "👥 Goście",
            "➕ Dodaj gościa"
        ]
    )

    # ---------- LISTA ----------

    with tab1:

        if not guests:

            st.info(
                "Lista gości jest jeszcze pusta."
            )

        for guest in guests:

            with st.expander(
                f"👤 {guest['name']} — {guest['status']}"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Strona:** "
                        f"{guest['side'] or '-'}"
                    )

                    st.write(
                        f"**Osoba towarzysząca:** "
                        f"{'Tak' if guest['plus_one'] else 'Nie'}"
                    )

                    st.write(
                        f"**Dzieci:** "
                        f"{guest['children'] or 0}"
                    )

                with col2:

                    st.write(
                        f"**Nocleg:** "
                        f"{'Tak' if guest['accommodation'] else 'Nie'}"
                    )

                    st.write(
                        f"**Transport:** "
                        f"{'Tak' if guest['transport'] else 'Nie'}"
                    )

                    st.write(
                        f"**Dieta:** "
                        f"{guest['diet'] or '-'}"
                    )

                if guest["notes"]:

                    st.write(
                        f"**Uwagi:** {guest['notes']}"
                    )

                status = st.selectbox(
                    "Status",
                    [
                        "Brak odpowiedzi",
                        "Potwierdzony",
                        "Odmówił"
                    ],
                    index=[
                        "Brak odpowiedzi",
                        "Potwierdzony",
                        "Odmówił"
                    ].index(guest["status"]),
                    key=f"guest_status_{guest['id']}"
                )

                if status != guest["status"]:

                    supabase.table(
                        "guests"
                    ).update(
                        {
                            "status": status
                        }
                    ).eq(
                        "id",
                        guest["id"]
                    ).execute()

                    st.rerun()

                if st.button(
                    "🗑️ Usuń gościa",
                    key=f"delete_guest_{guest['id']}"
                ):

                    supabase.table(
                        "guests"
                    ).delete().eq(
                        "id",
                        guest["id"]
                    ).execute()

                    st.rerun()

    # ---------- DODAWANIE ----------

    with tab2:

        with st.form("guest_form"):

            name = st.text_input(
                "Imię i nazwisko"
            )

            side = st.selectbox(
                "Strona",
                [
                    "Wspólni",
                    "Panna Młoda",
                    "Pan Młody"
                ]
            )

            status = st.selectbox(
                "Status",
                [
                    "Brak odpowiedzi",
                    "Potwierdzony",
                    "Odmówił"
                ]
            )

            plus_one = st.checkbox(
                "Osoba towarzysząca"
            )

            children = st.number_input(
                "Liczba dzieci",
                min_value=0,
                step=1
            )

            accommodation = st.checkbox(
                "Potrzebuje noclegu"
            )

            transport = st.checkbox(
                "Potrzebuje transportu"
            )

            diet = st.text_input(
                "Dieta / alergie",
                placeholder="np. wegetariańska"
            )

            notes = st.text_area(
                "Uwagi"
            )

            submit_guest = st.form_submit_button(
                "Dodaj gościa"
            )

            if submit_guest and name:

                supabase.table(
                    "guests"
                ).insert(
                    {
                        "name": name,
                        "side": side,
                        "status": status,
                        "plus_one": plus_one,
                        "children": children,
                        "accommodation": accommodation,
                        "transport": transport,
                        "diet": diet,
                        "notes": notes
                    }
                ).execute()

                st.success(
                    "Gość został dodany."
                )

                st.rerun()


# =========================
# BUDŻET
# =========================

elif page == "💰 Budżet":

    st.title("💰 Budżet")

    budget = get_budget()

    estimated = sum(
        float(item["estimated_price"] or 0)
        for item in budget
    )

    actual = sum(
        float(item["actual_price"] or 0)
        for item in budget
    )

    deposits = sum(
        float(item["deposit"] or 0)
        for item in budget
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Planowany budżet",
        f"{estimated:,.2f} zł"
    )

    col2.metric(
        "Faktyczny koszt",
        f"{actual:,.2f} zł"
    )

    col3.metric(
        "Wpłacone zaliczki",
        f"{deposits:,.2f} zł"
    )

    tab1, tab2 = st.tabs(
        [
            "💳 Wydatki",
            "➕ Dodaj wydatek"
        ]
    )

    # ---------- WYDATKI ----------

    with tab1:

        if not budget:

            st.info(
                "Nie dodano jeszcze żadnych wydatków."
            )

        for item in budget:

            with st.expander(
                f"💳 {item['name']}"
            ):

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Plan",
                    f"{float(item['estimated_price'] or 0):,.2f} zł"
                )

                col2.metric(
                    "Koszt",
                    f"{float(item['actual_price'] or 0):,.2f} zł"
                )

                col3.metric(
                    "Zaliczka",
                    f"{float(item['deposit'] or 0):,.2f} zł"
                )

                if item["category"]:

                    st.write(
                        f"**Kategoria:** {item['category']}"
                    )

                if item["notes"]:

                    st.write(
                        f"**Uwagi:** {item['notes']}"
                    )

                paid = st.checkbox(
                    "Opłacone",
                    value=item["paid"],
                    key=f"paid_{item['id']}"
                )

                if paid != item["paid"]:

                    supabase.table(
                        "budget"
                    ).update(
                        {
                            "paid": paid
                        }
                    ).eq(
                        "id",
                        item["id"]
                    ).execute()

                    st.rerun()

                if st.button(
                    "🗑️ Usuń",
                    key=f"delete_budget_{item['id']}"
                ):

                    supabase.table(
                        "budget"
                    ).delete().eq(
                        "id",
                        item["id"]
                    ).execute()

                    st.rerun()

    # ---------- DODAWANIE ----------

    with tab2:

        with st.form("budget_form"):

            name = st.text_input(
                "Nazwa",
                placeholder="np. Fotograf"
            )

            category = st.text_input(
                "Kategoria",
                placeholder="np. Usługodawcy"
            )

            estimated_price = st.number_input(
                "Planowana cena",
                min_value=0.0,
                step=100.0
            )

            actual_price = st.number_input(
                "Faktyczna cena",
                min_value=0.0,
                step=100.0
            )

            deposit = st.number_input(
                "Wpłacona zaliczka",
                min_value=0.0,
                step=100.0
            )

            notes = st.text_area(
                "Uwagi"
            )

            submit_budget = st.form_submit_button(
                "Dodaj wydatek"
            )

            if submit_budget and name:

                supabase.table(
                    "budget"
                ).insert(
                    {
                        "name": name,
                        "category": category,
                        "estimated_price": estimated_price,
                        "actual_price": actual_price,
                        "deposit": deposit,
                        "paid": False,
                        "notes": notes
                    }
                ).execute()

                st.success(
                    "Wydatek został dodany."
                )

                st.rerun()
