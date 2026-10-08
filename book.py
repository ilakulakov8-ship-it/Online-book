import streamlit as st
import requests

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

# --- СЕКРЕТНЫЙ ПАРОЛЬ АДМИНИСТРАТОРА ---
ADMIN_PASSWORD = "$8157#@G05pl"

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None

# --- ГЛАВНОЕ СТАРТОВОЕ МЕНЮ ---
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

is_admin = (st.session_state.auth_mode == "admin")

# Получаем все страницы через REST
all_pages = []
try:
    all_pages = db_get("pages", "order=id.asc")
except Exception as e:
    st.exception(e)
    st.stop()

total_rules_pages = len(all_pages)
max_pages = 1 + total_rules_pages

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

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
            rule_title = st.text_input("Название темы:")
            uploaded_files = st.file_uploader("Загрузить фото (необязательно):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            rule_text = st.text_area("Подзаголовок / Описание (формулы, правила, текст):", height=200)
            
            if st.button("💾 Опубликовать страницу в книгу", type="primary"):
                if rule_title:
                    insert_res = db_post("pages", {
                        "page_number": next_page_num,
                        "grade": grade,
                        "title": rule_title,
                        "text_content": rule_text
                    })
                    
                    if insert_res and uploaded_files:
                        new_page_id = insert_res[0]["id"]
                        for idx, f in enumerate(uploaded_files):
                            file_path = f"page_{new_page_id}_{idx}_{f.name}"
                            img_url = storage_upload("book-images", file_path, f.getvalue(), f.type)
                            db_post("page_images", {
                                "page_id": new_page_id,
                                "image_url": img_url
                            })
                            
                    st.success(f"Страница №{next_page_num} сохранена в облако!")
                    st.rerun()
                else:
                    st.error("Введите название темы!")
                    
        elif menu_mode == "✏️ Редактировать текущую" and current_page_id is not None:
            st.subheader(f"✏️ Изменение страницы № {st.session_state.current_page}")
            
            classes_list = [f"{i} класс" for i in range(5, 12)]
            default_class_index = classes_list.index(p_grade) if p_grade in classes_list else 0
            
            edit_grade = st.selectbox("Класс:", classes_list, index=default_class_index, key="edit_grade")
            edit_title = st.text_input("Название темы:", value=p_title, key="edit_title")
            
            delete_old_photos = st.checkbox("🗑️ Заменить старые фото новыми", key="del_old_photos")
            edit_files = st.file_uploader("Добавить фото:", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="edit_files")
            
            edit_text = st.text_area("Подзаголовок / Описание (формулы, правила, текст):", value=p_text, height=200, key="edit_text")
            
            if st.button("🔄 Сохранить изменения", type="primary"):
                db_patch("pages", f"id=eq.{current_page_id}", {
                    "grade": edit_grade,
                    "title": edit_title,
                    "text_content": edit_text
                })
                
                if delete_old_photos:
                    try:
                        db_delete("page_images", f"page_id=eq.{current_page_id}")
                    except Exception:
                        pass
                
                if edit_files:
                    for idx, f in enumerate(edit_files):
                        file_path = f"page_{current_page_id}_edit_{idx}_{f.name}"
                        img_url = storage_upload("book-images", file_path, f.getvalue(), f.type)
                        db_post("page_images", {
                            "page_id": current_page_id,
                            "image_url": img_url
                        })
                
                st.success("Изменения успешно сохранены!")
                st.rerun()

        st.write("---")
        st.write("🎨 Цветные маркеры (вставлять в текст):")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🟡"): st.code('<span class="hl-yellow">текст</span>')
        with c2:
            if st.button("🟢"): st.code('<span class="hl-green">текст</span>')
        with c3:
            if st.button("🔴"): st.code('<span class="hl-red">текст</span>')
    else:
        st.info("📖 Книга открыта в режиме 'Только просмотр' для учителя.")

# --- ДИАЛОГОВОЕ ОКНО УДАЛЕНИЯ ---
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
            try:
                db_delete("page_images", f"page_id=eq.{p_id}")
            except Exception:
                pass
            db_delete("pages", f"id=eq.{p_id}")
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
            images_records = []
            try:
                images_records = db_get("page_images", f"page_id=eq.{current_page_id}")
            except Exception:
                pass
    
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
