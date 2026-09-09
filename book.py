import streamlit as st
import sqlite3
import io
from PIL import Image

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛЕЙ ---
st.set_page_config(page_title="Правила 5-11 класс", page_icon="📐", layout="wide")

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
    .book-cover {
        text-align: center;
        padding: 80px 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.15);
        margin: 40px auto;
        max-width: 700px;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(8px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .hl-yellow { background-color: #fff3cd; padding: 2px 4px; border-radius: 3px; color: #000; }
    .hl-green { background-color: #d1e7dd; padding: 2px 4px; border-radius: 3px; color: #000; }
    .hl-red { background-color: #f8d7da; padding: 2px 4px; border-radius: 3px; color: #000; }
    
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

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect("algebra_book.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_number INTEGER,
        grade TEXT,
        title TEXT,
        text_content TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS page_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER,
        image_bytes BLOB,
        FOREIGN KEY(page_id) REFERENCES pages(id) ON DELETE CASCADE
    )
""")
conn.commit()

# --- СЕКРЕТНЫЙ ПАРОЛЬ АДМИНИСТРАТОРА ---
ADMIN_PASSWORD = "$8157#@G05pl"

# Инициализируем состояние сессии для авторизации
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None  # Варианты: None, "guest", "admin"

# --- ГЛАВНОЕ СТАРТОВОЕ МЕНЮ (ЕСЛИ РЕЖИМ НЕ ВЫБРАН) ---
if st.session_state.auth_mode is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([0.2, 0.6, 0.2])
    
    with col_m:
        st.markdown("""
            <div style="text-align: center; background-color: #f8f9fa; padding: 40px; border-radius: 20px; box-shadow: 0px 4px 20px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
                <h2>📖 Добро пожаловать в онлайн-книгу правил</h2>
                <p style="color: #6c757d;">Пожалуйста, выберите режим доступа для продолжения работы со сборником</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        btn_guest, btn_admin = st.columns(2)
        
        with btn_guest:
            if st.button("👥 Войти как Гость (Учитель)", use_container_width=True, type="secondary"):
                st.session_state.auth_mode = "guest"
                st.rerun()
                
        with btn_admin:
            if st.button("🔐 Режим Администратора", use_container_width=True, type="primary"):
                st.session_state.auth_mode = "prompt_admin"
                st.rerun()

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

# Определяем статус админа для отрисовки элементов
is_admin = (st.session_state.auth_mode == "admin")

# --- ПОДГОТОВКА ДАННЫХ И СЧЕТЧИКОВ СТРАНИЦ ---
cursor.execute("SELECT COUNT(*) FROM pages")
total_rules_pages = cursor.fetchone()[0]
max_pages = 1 + total_rules_pages

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if st.session_state.current_page > max_pages:
    st.session_state.current_page = max_pages

# Загружаем текущие данные для отображения и изменения
current_page_id = None
p_title, p_grade, p_text = "", "", ""
if st.session_state.current_page > 1:
    db_page_idx = st.session_state.current_page - 2
    cursor.execute("SELECT id, page_number, grade, title, text_content FROM pages ORDER BY id ASC")
    all_pages = cursor.fetchall()
    if db_page_idx < len(all_pages):
        current_page_id, p_num, p_grade, p_title, p_text = all_pages[db_page_idx]

# --- БОКОВАЯ ПАНЕЛЬ (АДМИНКА) ---
with st.sidebar:
    if is_admin:
        st.success("🔓 Режим редактирования активен")
        if st.button("🚪 Выйти из админки", use_container_width=True):
            st.session_state.auth_mode = None
            st.rerun()
        st.write("---")
        
        menu_mode = st.radio(
            "Выберите действие:", 
            ["➕ Создать новую", "✏️ Редактировать текущую"], 
            disabled=(st.session_state.current_page == 1),
            key="admin_menu_mode"
        )
        
        if st.session_state.current_page == 1 and menu_mode == "✏️ Редактировать текущую":
            st.warning("Обложку нельзя редактировать. Перелистните страницу вперед.")
            
        elif menu_mode == "➕ Создать новую":
            st.subheader("➕ Создать новую страницу")
            next_page_num = total_rules_pages + 2  
            st.info(f"Будет создана страница № {next_page_num}")
            
            grade = st.selectbox("Выберите класс:", [f"{i} класс" for i in range(5, 12)])
            rule_title = st.text_input("Название правила/темы:")
            uploaded_files = st.file_uploader("Загрузите фото (можно несколько):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            rule_text = st.text_area("Текст правила / Заметки:")
            if st.button("💾 Опубликовать страницу в книгу", type="primary"):
                if rule_title:
                    cursor.execute(
                        "INSERT INTO pages (page_number, grade, title, text_content) VALUES (?, ?, ?, ?)",
                        (next_page_num, grade, rule_title, rule_text)
                    )
                    page_id = cursor.lastrowid
                    
                    if uploaded_files:
                        for f in uploaded_files:
                            img_blob = f.getvalue()
                            cursor.execute("INSERT INTO page_images (page_id, image_bytes) VALUES (?, ?)", (page_id, img_blob))
                    
                    conn.commit()
                    st.success(f"Страница №{next_page_num} сохранена!")
                    st.rerun()
                else:
                    st.error("Введите название темы!")
                    
        elif menu_mode == "✏️ Редактировать текущую" and current_page_id is not None:
            st.subheader(f"✏️ Изменение страницы № {st.session_state.current_page}")
            
            classes_list = [f"{i} класс" for i in range(5, 12)]
            default_class_index = classes_list.index(p_grade) if p_grade in classes_list else 0
            
            edit_grade = st.selectbox("Класс:", classes_list, index=default_class_index, key="edit_grade")
            edit_title = st.text_input("Название темы:", value=p_title, key="edit_title")
            edit_text = st.text_area("Текст и конспект:", value=p_text, key="edit_text")
            
            st.write("🖼️ Изменение фотографий:")
            delete_old_photos = st.checkbox("🗑️ Удалить старые фото перед загрузкой новых", key="del_old_photos")
            edit_files = st.file_uploader("Добавить новые фото к этой теме:", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="edit_files")
            
            if st.button("🔄 Сохранить изменения", type="primary"):
                cursor.execute(
                    "UPDATE pages SET grade = ?, title = ?, text_content = ? WHERE id = ?",
                    (edit_grade, edit_title, edit_text, current_page_id)
                )
                
                if delete_old_photos:
                    cursor.execute("DELETE FROM page_images WHERE page_id = ?", (current_page_id,))
                
                if edit_files:
                    for f in edit_files:
                        img_blob = f.getvalue()
                        cursor.execute("INSERT INTO page_images (page_id, image_bytes) VALUES (?, ?)", (current_page_id, img_blob))
                
                conn.commit()
                st.success("Изменения успешно сохранены!")
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
        st.info("📖 Книга открыта в режиме 'Только просмотр' для учителя.")

# --- ФУНКЦИЯ ДИАЛОГОВОГО ОКНА УДАЛЕНИЯ ---
@st.dialog("⚠️ Подтверждение удаления")
def confirm_delete_dialog(p_id, title, page_num):
    st.write(f"Вы точно хотите удалить страницу **№ {page_num}**?")
    st.write(f"Тема: *{title}*")
    st.write("Это действие нельзя будет отменить.")
    
    col_cancel, col_del = st.columns(2)
    with col_cancel:
        if st.button("Отмена", use_container_width=True):
            st.rerun()
    with col_del:
        if st.button("Удалить", type="primary", use_container_width=True):
            cursor.execute("DELETE FROM pages WHERE id = ?", (p_id,))
            cursor.execute("DELETE FROM page_images WHERE page_id = ?", (p_id,))
            conn.commit()
            st.toast("Страница успешно удалена!")
            st.session_state.current_page = 1
            st.rerun()

# --- ОТОБРАЖЕНИЕ КНИГИ ---
if st.session_state.auth_mode is not None and st.session_state.auth_mode != "prompt_admin":
    if st.session_state.current_page == 1:
        st.markdown("""
            <div class="book-cover">
                <h1>📐 Правила 5-11 класс Алгебра</h1>
                <p style="font-size: 1.2rem; opacity: 0.8; margin-top: 15px;">Онлайн-сборник классных работ и теоретического материала</p>
                <div style="margin-top: 40px; font-weight: bold; background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 30px; display: inline-block;">
                    📖 Используйте кнопки внизу, чтобы листать тетрадь
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    else:
        if current_page_id is not None:
            cursor.execute("SELECT image_bytes FROM page_images WHERE page_id = ?", (current_page_id,))
            images_records = cursor.fetchall()
    
            st.markdown('<div class="rule-card-container">', unsafe_allow_html=True)
            
            if is_admin:
                col_header, col_edit_btn, col_delete_btn = st.columns([0.8, 0.1, 0.1])
                with col_header:
                    st.caption(f"📚 {p_grade} | Страница учебника: {st.session_state.current_page}")
                    st.header(p_title)
                with col_edit_btn:
                    if st.button("✏️", help="Редактировать эту страницу"):
                        st.session_state.admin_menu_mode = "✏️ Редактировать текущую"
                        st.rerun()
                with col_delete_btn:
                    if st.button("🗑️", help="Удалить эту страницу"):
                        confirm_delete_dialog(current_page_id, p_title, st.session_state.current_page)
            else:
                st.caption(f"📚 {p_grade} | Страница учебника: {st.session_state.current_page}")
                st.header(p_title)
    
            st.markdown('<div class="rule-card">', unsafe_allow_html=True)
            
            col_content, col_text = st.columns(2)
            
            with col_content:
                if images_records:
                    st.subheader("📸 Снимки классной работы:")
                    for img_row in images_records:
                        img_bytes = img_row[0]
                        image = Image.open(io.BytesIO(img_bytes))
                        st.image(image, use_container_width=True)
                else:
                    st.info("Для этой страницы изображения не загружались.")
                    
            with col_text:
                st.subheader("📝 Конспект и правила:")
                st.markdown(p_text, unsafe_allow_html=True)
                        
            st.markdown('</div></div>', unsafe_allow_html=True)
    
    # --- КНОПКИ НАВИГАЦИИ (ПОДВАЛ) ---
    st.write("---")
    st.markdown(f"<center><h4>Страница <b>{st.session_state.current_page}</b> из {max_pages}</h4></center>", unsafe_allow_html=True)
    
    nav_back_cols = st.columns(4)
    with nav_back_cols[0]:
        if st.button("⏮️ -25 страниц", disabled=(st.session_state.current_page - 25 < 1), key="b25"):
            st.session_state.current_page -= 25
            st.rerun()
    with nav_back_cols[1]:
        if st.button("⏪ -5 страниц", disabled=(st.session_state.current_page - 5 < 1), key="b5"):
            st.session_state.current_page -= 5
            st.rerun()
    with nav_back_cols[2]:
        if st.button("◀️ -2 страницы", disabled=(st.session_state.current_page - 2 < 1), key="b2"):
            st.session_state.current_page -= 2
            st.rerun()
    with nav_back_cols[3]:
        if st.button("⬅️ Назад (-1)", disabled=(st.session_state.current_page - 1 < 1), key="b1"):
            st.session_state.current_page -= 1
            st.rerun()
    
    nav_forward_cols = st.columns(4)
    with nav_forward_cols[0]:
        if st.button("Вперед (+1) ➡️", disabled=(st.session_state.current_page + 1 > max_pages), key="f1"):
            st.session_state.current_page += 1
            st.rerun()
    with nav_forward_cols[1]:
        if st.button("Вперед (+2) ▶️", disabled=(st.session_state.current_page + 2 > max_pages), key="f2"):
            st.session_state.current_page += 2
            st.rerun()
    with nav_forward_cols[2]:
        if st.button("Вперед (+5) ⏩", disabled=(st.session_state.current_page + 5 > max_pages), key="f5"):
            st.session_state.current_page += 5
            st.rerun()
    with nav_forward_cols[3]:
        if st.button("Вперед (+25) ⏭️", disabled=(st.session_state.current_page + 25 > max_pages), key="f25"):
            st.session_state.current_page += 25
            st.rerun()
