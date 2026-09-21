import streamlit as st
import psycopg
from psycopg.rows import dict_row

st.set_page_config(
    page_title="Nasze wesele",
    page_icon="💍",
    layout="wide"
)

# =========================
# POŁĄCZENIE Z BAZĄ
# =========================

def get_connection():
    return psycopg.connect(
        st.secrets["DATABASE_URL"],
        row_factory=dict_row
    )


def execute(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()


def fetch_all(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


# =========================
# TWORZENIE TABEL
# =========================

def init_db():
    execute("""
        create table if not exists categories (
            id bigserial primary key,
            name text not null,
            position integer default 0,
            created_at timestamp default now()
        );
    """)

    execute("""
        create table if not exists tasks (
            id bigserial primary key,
            category_id bigint references categories(id) on delete cascade,
            title text not null,
            completed boolean default false,
            notes text,
            created_at timestamp default now()
        );
    """)

    execute("""
        create table if not exists guests (
            id bigserial primary key,
            name text not null,
            side text,
            status text default 'Brak odpowiedzi',
            plus_one boolean default false,
            children integer default 0,
            accommodation boolean default false,
            transport boolean default false,
            diet text,
            notes text,
            created_at timestamp default now()
        );
    """)

    execute("""
        create table if not exists budget (
            id bigserial primary key,
            name text not null,
            category text,
            estimated_price numeric default 0,
            actual_price numeric default 0,
            deposit numeric default 0,
            paid boolean default false,
            notes text,
            created_at timestamp default now()
        );
    """)


init_db()


# =========================
# WYGLĄD
# =========================

st.markdown("""
<style>

.stApp {
    background-color: #faf8f5;
}

[data-testid="stSidebar"] {
    background-color: #eee6de;
}

.block-container {
    padding-top: 2rem;
}

div[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 15px;
    border: 1px solid #e5ddd5;
}

h1, h2, h3 {
    color: #55473d;
}

</style>
""", unsafe_allow_html=True)


# =========================
# MENU
# =========================

st.sidebar.title("💍 NASZE WESELE")
st.sidebar.caption("Planner organizacji")

page = st.sidebar.radio(
    "",
    [
        "🏠 Strona główna",
        "✅ Organizacja",
        "👥 Lista gości",
        "💰 Budżet"
    ]
)


# =========================
# STRONA GŁÓWNA
# =========================

if page == "🏠 Strona główna":

    st.title("💍 Nasze wesele")
    st.write("Wszystko, co trzeba zorganizować, w jednym miejscu.")

    tasks = fetch_all("select * from tasks")
    guests = fetch_all("select * from guests")
    budget = fetch_all("select * from budget")

    completed = sum(1 for task in tasks if task["completed"])

    confirmed = sum(
        1 for guest in guests
        if guest["status"] == "Potwierdzony"
    )

    actual_cost = sum(
        float(item["actual_price"] or 0)
        for item in budget
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Zadania",
        f"{completed}/{len(tasks)}"
    )

    col2.metric(
        "Goście",
        len(guests)
    )

    col3.metric(
        "Potwierdzili",
        confirmed
    )

    col4.metric(
        "Wydano",
        f"{actual_cost:,.0f} zł"
    )

    st.divider()

    st.subheader("Postęp organizacji")

    if tasks:

        progress = completed / len(tasks)

        st.progress(progress)

        st.write(
            f"Zrobione **{completed} z {len(tasks)} zadań**"
        )

    else:

        st.info(
            "Nie masz jeszcze żadnych zadań."
        )


# =========================
# ORGANIZACJA
# =========================

elif page == "✅ Organizacja":

    st.title("✅ Organizacja")

    tab1, tab2 = st.tabs([
        "📋 Zadania",
        "➕ Dodaj"
    ])

    categories = fetch_all(
        "select * from categories order by position, created_at"
    )

    tasks = fetch_all(
        "select * from tasks order by created_at"
    )

    with tab1:

        if not categories:
            st.info("Dodaj pierwszą kategorię.")

        for category in categories:

            category_tasks = [
                task for task in tasks
                if task["category_id"] == category["id"]
            ]

            with st.expander(
                f"📁 {category['name']}",
                expanded=True
            ):

                if not category_tasks:
                    st.caption("Brak zadań.")

                for task in category_tasks:

                    col1, col2 = st.columns([8, 1])

                    with col1:

                        checked = st.checkbox(
                            task["title"],
                            value=task["completed"],
                            key=f"task_{task['id']}"
                        )

                        if checked != task["completed"]:

                            execute(
                                """
                                update tasks
                                set completed = %s
                                where id = %s
                                """,
                                (checked, task["id"])
                            )

                            st.rerun()

                        if task["notes"]:
                            st.caption(task["notes"])

                    with col2:

                        if st.button(
                            "🗑️",
                            key=f"delete_task_{task['id']}"
                        ):

                            execute(
                                "delete from tasks where id = %s",
                                (task["id"],)
                            )

                            st.rerun()

    with tab2:

        st.subheader("Dodaj kategorię")

        with st.form("category_form"):

            category_name = st.text_input(
                "Nazwa kategorii",
                placeholder="np. Sala, Fotograf, Dekoracje"
            )

            if st.form_submit_button("Dodaj kategorię"):

                if category_name:

                    execute(
                        """
                        insert into categories (name)
                        values (%s)
                        """,
                        (category_name,)
                    )

                    st.rerun()

        st.divider()

        st.subheader("Dodaj zadanie")

        categories = fetch_all(
            "select * from categories order by position, created_at"
        )

        if categories:

            category_dict = {
                item["name"]: item["id"]
                for item in categories
            }

            with st.form("task_form"):

                task_name = st.text_input(
                    "Zadanie",
                    placeholder="np. podpisać umowę z fotografem"
                )

                selected_category = st.selectbox(
                    "Kategoria",
                    list(category_dict.keys())
                )

                notes = st.text_area(
                    "Notatka"
                )

                if st.form_submit_button("Dodaj zadanie"):

                    if task_name:

                        execute(
                            """
                            insert into tasks
                            (category_id, title, notes)
                            values (%s, %s, %s)
                            """,
                            (
                                category_dict[selected_category],
                                task_name,
                                notes
                            )
                        )

                        st.rerun()


# =========================
# GOŚCIE
# =========================

elif page == "👥 Lista gości":

    st.title("👥 Lista gości")

    guests = fetch_all(
        "select * from guests order by name"
    )

    confirmed = sum(
        1 for g in guests
        if g["status"] == "Potwierdzony"
    )

    declined = sum(
        1 for g in guests
        if g["status"] == "Odmówił"
    )

    waiting = len(guests) - confirmed - declined

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Wszyscy", len(guests))
    col2.metric("Potwierdzili", confirmed)
    col3.metric("Odmówili", declined)
    col4.metric("Brak odpowiedzi", waiting)

    tab1, tab2 = st.tabs([
        "👥 Goście",
        "➕ Dodaj gościa"
    ])

    with tab1:

        for guest in guests:

            with st.expander(
                f"👤 {guest['name']} — {guest['status']}"
            ):

                st.write(
                    f"**Strona:** {guest['side'] or '-'}"
                )

                st.write(
                    f"**Osoba towarzysząca:** "
                    f"{'Tak' if guest['plus_one'] else 'Nie'}"
                )

                st.write(
                    f"**Dzieci:** {guest['children']}"
                )

                st.write(
                    f"**Nocleg:** "
                    f"{'Tak' if guest['accommodation'] else 'Nie'}"
                )

                st.write(
                    f"**Transport:** "
                    f"{'Tak' if guest['transport'] else 'Nie'}"
                )

                if guest["diet"]:
                    st.write(
                        f"**Dieta / alergie:** {guest['diet']}"
                    )

                statuses = [
                    "Brak odpowiedzi",
                    "Potwierdzony",
                    "Odmówił"
                ]

                status = st.selectbox(
                    "Status",
                    statuses,
                    index=statuses.index(guest["status"]),
                    key=f"status_{guest['id']}"
                )

                if status != guest["status"]:

                    execute(
                        """
                        update guests
                        set status = %s
                        where id = %s
                        """,
                        (
                            status,
                            guest["id"]
                        )
                    )

                    st.rerun()

                if st.button(
                    "🗑️ Usuń gościa",
                    key=f"guest_delete_{guest['id']}"
                ):

                    execute(
                        "delete from guests where id = %s",
                        (guest["id"],)
                    )

                    st.rerun()

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
                "Dieta / alergie"
            )

            notes = st.text_area(
                "Uwagi"
            )

            if st.form_submit_button("Dodaj gościa"):

                if name:

                    execute(
                        """
                        insert into guests (
                            name,
                            side,
                            plus_one,
                            children,
                            accommodation,
                            transport,
                            diet,
                            notes
                        )
                        values (%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            name,
                            side,
                            plus_one,
                            children,
                            accommodation,
                            transport,
                            diet,
                            notes
                        )
                    )

                    st.rerun()


# =========================
# BUDŻET
# =========================

elif page == "💰 Budżet":

    st.title("💰 Budżet")

    budget = fetch_all(
        "select * from budget order by created_at"
    )

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
        "Planowany",
        f"{estimated:,.0f} zł"
    )

    col2.metric(
        "Faktyczny",
        f"{actual:,.0f} zł"
    )

    col3.metric(
        "Zaliczki",
        f"{deposits:,.0f} zł"
    )

    tab1, tab2 = st.tabs([
        "💳 Wydatki",
        "➕ Dodaj wydatek"
    ])

    with tab1:

        for item in budget:

            with st.expander(
                f"💳 {item['name']}"
            ):

                st.write(
                    f"Planowana cena: "
                    f"**{float(item['estimated_price'] or 0):,.0f} zł**"
                )

                st.write(
                    f"Faktyczna cena: "
                    f"**{float(item['actual_price'] or 0):,.0f} zł**"
                )

                st.write(
                    f"Zaliczka: "
                    f"**{float(item['deposit'] or 0):,.0f} zł**"
                )

                paid = st.checkbox(
                    "Opłacone",
                    value=item["paid"],
                    key=f"paid_{item['id']}"
                )

                if paid != item["paid"]:

                    execute(
                        """
                        update budget
                        set paid = %s
                        where id = %s
                        """,
                        (
                            paid,
                            item["id"]
                        )
                    )

                    st.rerun()

                if st.button(
                    "🗑️ Usuń",
                    key=f"budget_delete_{item['id']}"
                ):

                    execute(
                        "delete from budget where id = %s",
                        (item["id"],)
                    )

                    st.rerun()

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
                "Zaliczka",
                min_value=0.0,
                step=100.0
            )

            notes = st.text_area(
                "Uwagi"
            )

            if st.form_submit_button("Dodaj wydatek"):

                if name:

                    execute(
                        """
                        insert into budget (
                            name,
                            category,
                            estimated_price,
                            actual_price,
                            deposit,
                            notes
                        )
                        values (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            name,
                            category,
                            estimated_price,
                            actual_price,
                            deposit,
                            notes
                        )
                    )

                    st.rerun()
