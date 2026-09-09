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

# --- ПРОВЕРКА ПОЧТЫ АДМИНИСТРАТОРА ---
MY_EMAIL = "ilakulakov8@gmail.com"

try:
    user_email = st.user.email
except:
    user_email = None

if user_email is None:
    is_admin = True  
else:
    is_admin = (user_email.lower() == MY_EMAIL.lower())

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    if is_admin:
        st.success("🔓 Режим редактирования (ilakulakov8)")
        st.write("---")
        st.subheader("➕ Создать новую страницу")
        
        cursor.execute("SELECT COUNT(*) FROM pages")
        total_in_db = cursor.fetchone()[0] # Исправлено: извлекаем число из кортежа
        next_page_num = total_in_db + 2  
        
        st.info(f"Будет создана страница № {next_page_num}")
        
        grade = st.selectbox("Выберите класс:", [f"{i} класс" for i in range(5, 12)])
        rule_title = st.text_input("Название правила/темы:")
        uploaded_files = st.file_uploader("Загрузите фото (можно несколько):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        rule_text = st.text_area("Текст правила / Заметки:")
        
        st.write("🎨 Цветные маркеры:")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🟡"): st.code('<span class="hl-yellow">текст</span>')
        with c2:
            if st.button("🟢"): st.code('<span class="hl-green">текст</span>')
        with c3:
            if st.button("🔴"): st.code('<span class="hl-red">текст</span>')

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
    else:
        st.info("📖 Книга открыта в режиме 'Только просмотр' для учителя.")

# --- СЧЕТЧИК СТРАНИЦ ---
cursor.execute("SELECT COUNT(*) FROM pages")
total_rules_pages = cursor.fetchone()[0] # Исправлено: извлекаем число из кортежа
max_pages = 1 + total_rules_pages

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if st.session_state.current_page > max_pages:
    st.session_state.current_page = max_pages

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
    db_page_idx = st.session_state.current_page - 2
    cursor.execute("SELECT id, page_number, grade, title, text_content FROM pages ORDER BY id ASC")
    all_pages = cursor.fetchall()
    
    current_page_data = all_pages[db_page_idx]
    page_id, p_num, p_grade, p_title, p_text = current_page_data
    
    cursor.execute("SELECT image_bytes FROM page_images WHERE page_id = ?", (page_id,))
    images_records = cursor.fetchall()

    st.markdown('<div class="rule-card-container">', unsafe_allow_html=True)
    
    if is_admin:
        col_header, col_delete_btn = st.columns([0.9, 0.1])
        with col_header:
            st.caption(f"📚 {p_grade} | Страница учебника: {st.session_state.current_page}")
            st.header(p_title)
        with col_delete_btn:
            if st.button("🗑️", help="Удалить эту страницу"):
                confirm_delete_dialog(page_id, p_title, st.session_state.current_page)
    else:
        st.caption(f"📚 {p_grade} | Страница учебника: {st.session_state.current_page}")
        st.header(p_title)

    st.markdown('<div class="rule-card">', unsafe_allow_html=True)
    
    col_content, col_text = st.columns(2)
    
    with col_content:
        if images_records:
            st.subheader("📸 Снимки классной работы:")
            for img_row in images_records:
                img_bytes = img_row[0] # Исправлено: берем первый элемент из кортежа строки БД
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

curr = st.session_state.current_page

# Ряд НАЗАД (Исправлено обращение к индексам списка колонок)
nav_back_cols = st.columns(4)
with nav_back_cols[0]:
    if st.button("⏮️ -25 страниц", disabled=(curr - 25 < 1), key="b25"):
        st.session_state.current_page -= 25
        st.rerun()
with nav_back_cols[1]:
    if st.button("⏪ -5 страниц", disabled=(curr - 5 < 1), key="b5"):
        st.session_state.current_page -= 5
        st.rerun()
with nav_back_cols[2]:
    if st.button("◀️ -2 страницы", disabled=(curr - 2 < 1), key="b2"):
        st.session_state.current_page -= 2
        st.rerun()
with nav_back_cols[3]:
    if st.button("⬅️ Назад (-1)", disabled=(curr - 1 < 1), key="b1"):
        st.session_state.current_page -= 1
        st.rerun()

# Ряд ВПЕРЕД (Исправлено обращение к индексам списка колонок)
nav_forward_cols = st.columns(4)
with nav_forward_cols[0]:
    if st.button("Вперед (+1) ➡️", disabled=(curr + 1 > max_pages), key="f1"):
        st.session_state.current_page += 1
        st.rerun()
with nav_forward_cols[1]:
    if st.button("Вперед (+2) ▶️", disabled=(curr + 2 > max_pages), key="f2"):
        st.session_state.current_page += 2
        st.rerun()
with nav_forward_cols[2]:
    if st.button("Вперед (+5) ⏩", disabled=(curr + 5 > max_pages), key="f5"):
        st.session_state.current_page += 5
        st.rerun()
with nav_forward_cols[3]:
    if st.button("Вперед (+25) ⏭️", disabled=(curr + 25 > max_pages), key="f25"):
        st.session_state.current_page += 25
        st.rerun()