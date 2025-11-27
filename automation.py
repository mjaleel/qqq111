import streamlit as st
import sqlite3
from hashlib import sha256

# -----------------------------
# إعداد قاعدة البيانات
# -----------------------------
conn = sqlite3.connect('employees.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    iban TEXT,
    employee_number TEXT
)
''')
conn.commit()


# -----------------------------
# دوال مساعدة
# -----------------------------
def hash_password(password):
    return sha256(password.encode()).hexdigest()

def check_login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    return c.fetchone() is not None

def add_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def add_employee(name, iban, emp_number):
    c.execute("INSERT INTO employees (name, iban, employee_number) VALUES (?, ?, ?)",
              (name, iban, emp_number))
    conn.commit()

def get_all_employees():
    c.execute("SELECT * FROM employees")
    return c.fetchall()


# -----------------------------
# إعداد Streamlit
# -----------------------------
st.set_page_config(page_title="نظام الموظفين", page_icon=":clipboard:", layout="wide")

# -----------------------------
# إعداد حالة الجلسة
# -----------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''


# -----------------------------
# واجهة تسجيل الدخول
# -----------------------------
if not st.session_state.logged_in:
    st.title("تسجيل الدخول")

    username = st.text_input("اسم المستخدم", key="login_user")
    password = st.text_input("كلمة المرور", type="password", key="login_pass")

    if st.button("تسجيل الدخول"):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("تم تسجيل الدخول!")
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور خاطئة")

    st.markdown("---")
    st.subheader("إنشاء مستخدم جديد (اختياري)")

    new_user = st.text_input("يوزر جديد", key="new_user")
    new_pass = st.text_input("باسورد جديد", type="password", key="new_pass")

    if st.button("إضافة مستخدم جديد"):
        if add_user(new_user, new_pass):
            st.success("تم إنشاء المستخدم بنجاح!")
        else:
            st.error("المستخدم موجود مسبقًا")


# -----------------------------
# واجهة البرنامج بعد تسجيل الدخول
# -----------------------------
else:
    st.sidebar.title(f"مرحبًا، {st.session_state.username}")

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    menu = st.sidebar.selectbox("القائمة", ["الصفحة الرئيسية", "إضافة موظف", "صفحة الأدمن"])

    # -----------------------------
    # الصفحة الرئيسية
    # -----------------------------
    if menu == "الصفحة الرئيسية":
        st.header("الصفحة الرئيسية")
        st.info("استخدم القائمة الجانبية للانتقال بين الصفحات.")


    # -----------------------------
    # إضافة موظف
    # -----------------------------
    elif menu == "إضافة موظف":
        st.header("إضافة موظف جديد")

        # عدد مرات إنشاء الفورم → لتغيير keys ديناميكية
        if 'form_counter' not in st.session_state:
            st.session_state.form_counter = 0

        # زر لإعادة عرض الفورم فارغًا
        if st.button("إضافة موظف جديد"):
            st.session_state.form_counter += 1
            st.rerun()

        # keys ديناميكية للفورم
        key_name = f"name_{st.session_state.form_counter}"
        key_iban = f"iban_{st.session_state.form_counter}"
        key_emp = f"emp_{st.session_state.form_counter}"

        with st.form(key=f'employee_form_{st.session_state.form_counter}'):
            name = st.text_input("الاسم", key=key_name)
            iban = st.text_input("IBAN", key=key_iban)
            emp_number = st.text_input("الرقم الوظيفي", key=key_emp)

            submit_button = st.form_submit_button("حفظ الموظف")

            if submit_button:
                if name and iban and emp_number:
                    add_employee(name, iban, emp_number)
                    st.success(f"تمت إضافة الموظف: {name}")

                    # بعد الحفظ → زيادة counter → الفورم التالي سيظهر فارغًا
                    st.session_state.form_counter += 1
                    st.rerun()
                else:
                    st.error("الرجاء ملء جميع الحقول")


    # -----------------------------
    # صفحة الأدمن
    # -----------------------------
    elif menu == "صفحة الأدمن":
        st.header("جميع بيانات الموظفين")

        # زر حذف جميع البيانات مباشرة
        if st.button("حذف كل بيانات الموظفين"):
            c.execute("DELETE FROM employees")
            conn.commit()
            st.success("تم حذف جميع بيانات الموظفين!")
            st.rerun()

        data = get_all_employees()

        formatted = [
            {"ID": row[0], "الاسم": row[1], "IBAN": row[2], "الرقم الوظيفي": row[3]}
            for row in data
        ]

        if formatted:
            st.dataframe(formatted, use_container_width=True)
        else:
            st.info("لا توجد بيانات موظفين بعد.")
