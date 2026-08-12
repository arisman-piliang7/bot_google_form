import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Configuration Halaman Streamlit
st.set_page_config(
    page_title="Sistem Manajemen Data & Credential", 
    page_icon="🔒", 
    layout="wide"
)

# 1. AUTENTIKASI PASSWORD
APP_PASSWORD = "BananaPineaple100%"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(
        "<h2 style='text-align: center;'>Akses Terbatas</h2>", unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            password_input = st.text_input("Masukkan Password Akses:", type="password")
            submit_login = st.form_submit_button("Masuk Form", use_container_width=True)

            if submit_login:
                if password_input == APP_PASSWORD:
                    st.session_state["authenticated"] = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("Password salah! Akses ditolak.")
    st.stop()


# 2. KONEKSI KE GOOGLE SHEETS
@st.cache_resource
def init_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Penanganan kunci private jika tersimpan sebagai string bergaris baru
        p_key = creds_dict.get("private_key", "")
        if isinstance(p_key, list):
            creds_dict["private_key"] = "\n".join(p_key)
        elif isinstance(p_key, str):
            creds_dict["private_key"] = p_key.replace("\\n", "\n")

        creds = Credentials.from_service_account_info(
            creds_dict, scopes=scope
        )
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)
    return client


# Function dengan cache untuk membaca data dari sheet
@st.cache_data(ttl=60)
def fetch_sheet_data(sheet_id):
    client = init_connection()
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet.get_all_values()


SHEET_ID = "1VgRaez8C_L9jjURWJr4PD7pMqJHJt5fw"

try:
    client = init_connection()
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets: {e}")
    st.stop()

st.title("🔒 Sistem Manajemen Data & Credential")

# LIST KATEGORI OPSI
KATEGORI_OPTIONS = [
    "Perbankan & Keuangan",
    "Akademis & Pendidikan",
    "Pekerjaan & Karir",
    "Layanan Pemerintah & Administrasi",
    "Productivity & Cloud",
    "Domain & Hosting",
    "Hiburan, Sosmed & Properti",
]

tab1, tab2 = st.tabs(["📝 Input Data Baru", "🔍 Pencarian Data"])

# 3. TAB INPUT DATA
with tab1:
    st.subheader("Form Input Data Baru")

    with st.form("input_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)

        with col_a:
            selected_kategori = st.selectbox(
                "Pilih Kategori:",
                ["-- Pilih Kategori --"]
                + KATEGORI_OPTIONS
                + ["Lainnya (Ketik Manual)"],
            )
            if selected_kategori == "Lainnya (Ketik Manual)":
                kategori = st.text_input("Ketik Kategori Manual:")
            elif selected_kategori != "-- Pilih Kategori --":
                kategori = selected_kategori
            else:
                kategori = ""

            nama_layanan = st.text_input("Nama Layanan / Platform *")
            url = st.text_input("URL / Link Akses")
            username = st.text_input("Username / Email / ID")

        with col_b:
            password = st.text_input("Password / PIN", type="password")
            detail = st.text_input("No. HP / Rekening / Detail")
            catatan = st.text_area("Catatan / Keterangan")

        btn_submit = st.form_submit_button("Simpan Data", use_container_width=True)

        if btn_submit:
            if not nama_layanan or not kategori:
                st.warning("⚠️ Kategori dan Nama Layanan wajib diisi!")
            else:
                try:
                    new_row = [
                        str(kategori),
                        str(nama_layanan),
                        str(url) if url else "-",
                        str(username) if username else "-",
                        str(password) if password else "-",
                        str(detail) if detail else "-",
                        str(catatan) if catatan else "-",
                    ]

                    sheet.append_row(new_row)

                    all_values = sheet.get_all_values()
                    last_row_index = len(all_values)

                    st.success(
                        f"✅ Data berhasil disimpan pada baris ke-{last_row_index}!"
                    )
                    st.cache_data.clear()
                except Exception as err:
                    st.error(f"❌ Gagal menyimpan data: {err}")

# 4. TAB PENCARIAN DATA
with tab2:
    st.subheader("Pencarian Data Credential")

    search_keyword = st.text_input(
        "Masukkan kata kunci (Kategori, Nama Layanan, atau Username):"
    )

    try:
        data = fetch_sheet_data(SHEET_ID)
        if len(data) >= 4:
            headers = data[2]
            df = pd.DataFrame(data[3:], columns=headers)

            if search_keyword:
                mask = df.apply(
                    lambda row: row.astype(str).str.contains(
                        search_keyword, case=False, na=False
                    )
                ).any(axis=1)
                df_filtered = df[mask]
            else:
                df_filtered = df

            st.write(f"Menampilkan **{len(df_filtered)}** data:")
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data di spreadsheet.")

    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
