import streamlit as st
import requests

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛЕЙ ---
st.set_page_config(page_title="Онлайн-библиотека учебников", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    .rule-card-container {
        position: relative;
    }
    .rule-card {
        animation: fadeIn 0.4s ease-in-out;
        padding: 30px;
        border-radius: 16px;
        background-color: #ffffff;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        max-height: 75vh;
        overflow-y: auto;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(8px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .hl-yellow { background-color: #fff3cd; padding: 2px 4px; border-radius: 3px; color: #000; }
    .hl-green { background-color: #d1e7dd; padding: 2px 4px; border-radius: 3px; color: #000; }
    .hl-red { background-color: #f8d7da; padding: 2px 4px; border-radius: 3px; color: #000; }
    
    .book-text-content {
        white-space: pre-wrap; 
        line-height: 1.6;      
        font-size: 1.05rem;
    }

    button[aria-label="Collapse sidebar"]::after {
        content: " { Спрятать";
        font-weight: bold;
    }
    section[data-testid="stSidebarCollapsedControl"] button::after {
        content: " } Открыть меню";
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- ПОДКЛЮЧЕНИЕ К SUPABASE ЧЕРЕЗ REST API ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Не найдены ключи Supabase в `st.secrets`! Проверьте настройки на Streamlit Cloud.")
    st.stop()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДБ И СТОРАДЖА ---
def db_get(table, query_params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query_params}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code == 204 or not res.text.strip():
            return []
        res.raise_for_status()
        return res.json()
    except Exception:
        return []

def db_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.post(url, headers=HEADERS, json=data, timeout=20)
    res.raise_for_status()
    return res.json()

def db_patch(table, query_params, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query_params}"
    res = requests.patch(url, headers=HEADERS, json=data, timeout=20)
    res.raise_for_status()
    return res.json()

def db_delete(table, query_params):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query_params}"
    res = requests.delete(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return res.json()

def storage_upload(bucket, file_path, file_bytes, file_mime="image/jpeg"):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": file_mime,
        "x-upsert": "true"
    }
    res = requests.post(url, headers=headers, data=file_bytes, timeout=30)
    res.raise_for_status()
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"

# --- ВЫНЕСЕННАЯ ПОВТОРЯЮЩАЯСЯ ФУНКЦИЯ ДЛЯ ЗАГРУЗКИ КАРТИНОК ---
def upload_and_save_images(book_id, page_id, files):
    """Загружает список файлов в Supabase Storage и сохраняет их ссылки в БД."""
    for idx, f in enumerate(files):
        file_path = f"book_{book_id}_page_{page_id}_{idx}_{f.name}"
        img_url = storage_upload("book-images", file_path, f.getvalue(), f.type)
        db_post("page_images", {
            "page_id": page_id,
            "image_url": img_url
        })

# --- СЕКРЕТНЫЙ ПАРОЛЬ АДМИНИСТРАТОРА ---
ADMIN_PASSWORD = "$8157#@G05pl"

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# --- ЭКРАН 1: ВЫБОР РЕЖИМА ВХОДА ---
if st.session_state.auth_mode is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([0.2, 0.6, 0.2])
    
    with col_m:
        st.markdown("""
            <div style="text-align: center; background: linear-gradient(135deg, #1f4037 0%, #99f2c8 100%); padding: 40px; border-radius: 20px; color: white; box-shadow: 0px 8px 25px rgba(0,0,0,0.15);">
                <h2>📚 Онлайн-библиотека учебников</h2>
                <p style="opacity: 0.9;">Выберите режим доступа для продолжения работы</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        btn_guest, btn_admin = st.columns(2)
        with btn_guest:
            if st.button("👥 Войти как Гость", use_container_width=True, type="secondary"):
                st.session_state.auth_mode = "guest"
                st.rerun()
        with btn_admin:
            if st.button("🔐 Режим Администратора", use_container_width=True, type="primary"):
                st.session_state.auth_mode = "prompt_admin"
                st.rerun()
    st.stop()

if st.session_state.auth_mode == "prompt_admin":
    col_l, col_m, col_r = st.columns([0.3, 0.4, 0.3])
    with col_m:
        st.subheader("🔑 Проверка доступа")
        pwd_input = st.text_input("Введите секретный пароль администратора:", type="password")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state.auth_mode = None
                st.rerun()
        with col_b2:
            if st.button("Войти 🔓", use_container_width=True, type="primary"):
                if pwd_input == ADMIN_PASSWORD:
                    st.session_state.auth_mode = "admin"
                    st.rerun()
                else:
                    st.error("Неверный пароль доступа!")
    st.stop()

is_admin = (st.session_state.auth_mode == "admin")

# --- ЗАГРУЗКА СПИСКА КНИГ ---
books_list = []
try:
    books_list = db_get("books", "order=id.asc")
except Exception:
    books_list = []

# --- ЭКРАН 2: ВЫБОР УЧЕБНИКА ---
if st.session_state.selected_book_id is None:
    st.markdown("<br>", unsafe_allow_html=True)
    col_t1, col_t2 = st.columns([0.8, 0.2])
    with col_t1:
        st.title("📚 Выберите учебник")
    with col_t2:
        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.auth_mode = None
            st.rerun()
            
    st.write("---")
    
    if not books_list:
        st.info("📖 Пока нет ни одного учебника. Администратор может создать его ниже!")
    else:
        cols = st.columns(3)
        for idx, book in enumerate(books_list):
            with cols[idx % 3]:
                gradient = book.get("color", "linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%)")
                st.markdown(f"""
                    <div style="background: {gradient}; padding: 35px 20px; border-radius: 18px; color: white; text-align: center; box-shadow: 0px 8px 20px rgba(0,0,0,0.12); margin-bottom: 20px;">
                        <h3 style="margin: 0; text-shadow: 0px 2px 4px rgba(0,0,0,0.2);">📖 {book['title']}</h3>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Открыть учебник", key=f"open_book_{book['id']}", use_container_width=True):
                    st.session_state.selected_book_id = book['id']
                    st.session_state.current_page = 1
                    st.rerun()

    if is_admin:
        st.write("---")
        with st.expander("➕ Создать новый учебник (предмет)"):
            new_book_title = st.text_input("Название учебника (например, Алгебра или Физика):")
            picked_color = st.color_picker("Выберите базовый цвет обложки:", "#ff7e5f")
            cover_gradient = f"linear-gradient(135deg, {picked_color} 0%, #2c3e50 100%)"
            
            if st.button("💾 Создать книгу", type="primary"):
                if new_book_title:
                    try:
                        db_post("books", {
                            "title": new_book_title,
                            "color": cover_gradient
                        })
                        st.success(f"Учебник '{new_book_title}' успешно создан!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"❌ Ошибка: {err}")
                else:
                    st.error("Введите название книги!")
    st.stop()

# --- ЭКРАН 3: ПРОСМОТР КОНКРЕТНОГО УЧЕБНИКА ---
current_book = next((b for b in books_list if b["id"] == st.session_state.selected_book_id), None)
if not current_book:
    st.error("Учебник не найден!")
    if st.button("Вернуться к списку"):
        st.session_state.selected_book_id = None
        st.rerun()
    st.stop()

all_pages = []
try:
    all_pages = db_get("pages", f"book_id=eq.{current_book['id']}&order=id.asc")
except Exception:
    all_pages = []

total_rules_pages = len(all_pages)
max_pages = 1 + total_rules_pages

if st.session_state.current_page > max_pages:
    st.session_state.current_page = max_pages

current_page_id = None
p_title, p_grade, p_text = "", "", ""
if st.session_state.current_page > 1:
    db_page_idx = st.session_state.current_page - 2
    if db_page_idx < len(all_pages):
        page_item = all_pages[db_page_idx]
        current_page_id = page_item["id"]
        p_grade = page_item.get("grade", "")
        p_title = page_item.get("title", "")
        p_text = page_item.get("text_content", "")

# --- БОКОВАЯ ПАНЕЛЬ УЧЕБНИКА ---
with st.sidebar:
    if st.button("🔙 К выбору учебников", use_container_width=True, type="secondary"):
        st.session_state.selected_book_id = None
        st.session_state.current_page = 1
        st.rerun()
        
    st.write("---")
    
    # --- БЫСТРЫЙ ВЫБОР КЛАССА ---
    st.subheader("🎯 Переход по классам")
    available_grades = [f"{i} класс" for i in range(5, 12)]
    selected_grade_filter = st.selectbox("Выберите класс:", ["Все классы"] + available_grades)
    
    if selected_grade_filter != "Все классы":
        found_idx = next((i for i, p in enumerate(all_pages) if p.get("grade") == selected_grade_filter), None)
        if found_idx is not None:
            if st.button(f"Перейти к {selected_grade_filter}", type="primary", use_container_width=True):
                st.session_state.current_page = found_idx + 2  # +2 из-за обложки
                st.rerun()
        else:
            st.caption(f"В этом учебнике нет тем для {selected_grade_filter}")

    st.write("---")
    if is_admin:
        st.success("🔓 Режим редактирования")
        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.auth_mode = None
            st.session_state.selected_book_id = None
            st.rerun()
            
        st.write("---")
        menu_mode = st.radio(
            "Действие:", 
            ["➕ Создать страницу", "✏️ Редактировать текущую"], 
            disabled=(st.session_state.current_page == 1),
            key="admin_menu_mode"
        )
        
        if menu_mode == "➕ Создать страницу":
            st.subheader("➕ Новая страница")
            next_page_num = total_rules_pages + 2
            grade = st.selectbox("Класс:", available_grades)
            rule_title = st.text_input("Название темы:")
            uploaded_files = st.file_uploader("Фото (необязательно):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            rule_text = st.text_area("Описание / Формулы:", height=200)
            
            if st.button("💾 Сохранить страницу", type="primary"):
                if rule_title:
                    insert_res = db_post("pages", {
                        "book_id": current_book["id"],
                        "page_number": next_page_num,
                        "grade": grade,
                        "title": rule_title,
                        "text_content": rule_text
                    })
                    
                    if insert_res and uploaded_files:
                        new_page_id = insert_res[0]["id"]
                        upload_and_save_images(current_book["id"], new_page_id, uploaded_files)
                            
                    st.success("Страница сохранена!")
                    st.rerun()
                else:
                    st.error("Введите название темы!")
                    
        elif menu_mode == "✏️ Редактировать текущую" and current_page_id is not None:
            st.subheader(f"✏️ Правка стр. № {st.session_state.current_page}")
            default_class_index = available_grades.index(p_grade) if p_grade in available_grades else 0
            
            edit_grade = st.selectbox("Класс:", available_grades, index=default_class_index, key="edit_grade")
            edit_title = st.text_input("Тема:", value=p_title, key="edit_title")
            delete_old_photos = st.checkbox("🗑️ Заменить старые фото новыми", key="del_old_photos")
            edit_files = st.file_uploader("Добавить фото:", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="edit_files")
            edit_text = st.text_area("Описание:", value=p_text, height=200, key="edit_text")
            
            if st.button("🔄 Обновить", type="primary"):
                db_patch("pages", f"id=eq.{current_page_id}", {
                    "grade": edit_grade, "title": edit_title, "text_content": edit_text
                })
                
                if delete_old_photos:
                    try:
                        db_delete("page_images", f"page_id=eq.{current_page_id}")
                    except Exception:
                        pass
                
                if edit_files:
                    upload_and_save_images(current_book["id"], current_page_id, edit_files)
                
                st.success("Изменения сохранены!")
                st.rerun()
        
        st.write("---")
        st.write("🎨 Цветные маркеры:")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🟡"): st.code('<span class="hl-yellow">текст</span>')
        with c2:
            if st.button("🟢"): st.code('<span class="hl-green">текст</span>')
        with c3:
            if st.button("🔴"): st.code('<span class="hl-red">текст</span>')
    else:
        st.info("📖 Режим просмотра учебника.")

# --- ДИАЛОГ УДАЛЕНИЯ ---
@st.dialog("⚠️ Подтверждение удаления")
def confirm_delete_dialog(p_id, title, page_num):
    st.write(f"Удалить страницу **№ {page_num}** ({title})?")
    col_c, col_d = st.columns(2)
    with col_c:
        if st.button("Отмена"): st.rerun()
    with col_d:
        if st.button("Удалить", type="primary"):
            try: db_delete("page_images", f"page_id=eq.{p_id}")
            except Exception: pass
            db_delete("pages", f"id=eq.{p_id}")
            st.toast("Страница удалена!")
            st.session_state.current_page = 1
            st.rerun()

# --- ОТОБРАЖЕНИЕ ОБЛОЖКИ ИЛИ СТРАНИЦ ---
if st.session_state.current_page == 1:
    bg_gradient = current_book.get("color", "linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%)")
    st.markdown(f"""
        <div style="text-align: center; padding: 80px 40px; background: {bg_gradient}; color: white; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.15); margin: 20px auto; max-width: 700px;">
            <h1 style="text-shadow: 0px 2px 5px rgba(0,0,0,0.2);">📖 {current_book['title']}</h1>
            <p style="font-size: 1.2rem; opacity: 0.9; margin-top: 15px;">Онлайн-сборник теоретического материала</p>
            <div style="margin-top: 40px; font-weight: bold; background: rgba(255,255,255,0.25); padding: 10px 20px; border-radius: 30px; display: inline-block;">
                Используйте боковое меню для выбора класса или листайте страницы 👇
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    if current_page_id is not None:
        images_records = []
        try:
            images_records = db_get("page_images", f"page_id=eq.{current_page_id}")
        except Exception:
            pass

        st.markdown('<div class="rule-card-container">', unsafe_allow_html=True)
        if is_admin:
            c_head, c_edit, c_del = st.columns([0.8, 0.1, 0.1])
            with c_head:
                st.caption(f"📚 {current_book['title']} | {p_grade} | Стр: {st.session_state.current_page}")
                st.header(p_title)
            with c_edit:
                if st.button("✏️"):
                    st.session_state.admin_menu_mode = "✏️ Редактировать текущую"
                    st.rerun()
            with c_del:
                if st.button("🗑️"):
                    confirm_delete_dialog(current_page_id, p_title, st.session_state.current_page)
        else:
            st.caption(f"📚 {current_book['title']} | {p_grade} | Стр: {st.session_state.current_page}")
            st.header(p_title)

        st.markdown('<div class="rule-card">', unsafe_allow_html=True)
        if images_records:
            col_media, col_text = st.columns([1, 1])
            with col_media:
                st.subheader("📸 Иллюстрации / Фото:")
                for img_row in images_records:
                    img_url = img_row.get("image_url")
                    if img_url:
                        st.image(img_url, use_container_width=True)
            with col_text:
                st.subheader("📌 Подзаголовок / Описание (формулы, правила):")
                st.markdown(f'<div class="book-text-content">{p_text}</div>', unsafe_allow_html=True)
        else:
            st.subheader("📌 Подзаголовок / Описание (формулы, правила):")
            st.markdown(f'<div class="book-text-content">{p_text}</div>', unsafe_allow_html=True)
                    
        st.markdown('</div></div>', unsafe_allow_html=True)

# --- НАВИГАЦИЯ ПО СТРАНИЦАМ ---
st.write("---")
st.markdown(f"<center><h4>Страница <b>{st.session_state.current_page}</b> из {max_pages}</h4></center>", unsafe_allow_html=True)

nav_back_cols = st.columns(4)
with nav_back_cols[0]:
    if st.button("⏮️ -25", disabled=(st.session_state.current_page - 25 < 1), key="b25"):
        st.session_state.current_page -= 25; st.rerun()
with nav_back_cols[1]:
    if st.button("⏪ -5", disabled=(st.session_state.current_page - 5 < 1), key="b5"):
        st.session_state.current_page -= 5; st.rerun()
with nav_back_cols[2]:
    if st.button("◀️ -2", disabled=(st.session_state.current_page - 2 < 1), key="b2"):
        st.session_state.current_page -= 2; st.rerun()
with nav_back_cols[3]:
    if st.button(f"⬅️ Назад", disabled=(st.session_state.current_page - 1 < 1), key="b1"):
        st.session_state.current_page -= 1; st.rerun()

nav_forward_cols = st.columns(4)
with nav_forward_cols[0]:
    if st.button("Вперед +1 ➡️", disabled=(st.session_state.current_page + 1 > max_pages), key="f1"):
        st.session_state.current_page += 1; st.rerun()
with nav_forward_cols[1]:
    if st.button("Вперед +2 ▶️", disabled=(st.session_state.current_page + 2 > max_pages), key="f2"):
        st.session_state.current_page += 2; st.rerun()
with nav_forward_cols[2]:
    if st.button("Вперед +5 ⏩", disabled=(st.session_state.current_page + 5 > max_pages), key="f5"):
        st.session_state.current_page += 5; st.rerun()
with nav_forward_cols[3]:
    if st.button("Вперед +25 ⏭️", disabled=(st.session_state.current_page + 25 > max_pages), key="f25"):
        st.session_state.current_page += 25; st.rerun()
