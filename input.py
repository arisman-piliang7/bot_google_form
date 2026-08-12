import json
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
    # JUDUL HALAMAN LOGIN
    st.markdown(
        "<h2 style='text-align: center;'>Password Safer 1.0</h2>", unsafe_allow_html=True
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
    
    # FOOTER DI HALAMAN LOGIN
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray; font-size: 13px;'>Password Safer v1.0 &bull; Designed by Arisman</p>", 
        unsafe_allow_html=True
    )
    st.stop()


# 2. KONEKSI KE GOOGLE SHEETS
@st.cache_resource
def init_connection():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    if "gcp_service_account" in st.secrets and "json_data" in st.secrets["gcp_service_account"]:
        json_info = json.loads(st.secrets["gcp_service_account"]["json_data"])
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
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


SHEET_ID = "1zHHvE_3knrv8wsyYHQa7Rs0xx9y_iERCK1Di9VZ1A6s"

try:
    client = init_connection()
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets: {e}")
    st.stop()

# JUDUL DI HALAMAN UTAMA
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

tab1, tab2 = st.tabs(["📝 Input Data Baru", "🔍 Pencarian & Kelola Data"])

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

# 4. TAB PENCARIAN & KELOLA DATA (EDIT & HAPUS)
with tab2:
    st.subheader("Pencarian & Kelola Data Credential")

    search_keyword = st.text_input(
        "Masukkan kata kunci (Kategori, Nama Layanan, atau Username):"
    )

    try:
        data = fetch_sheet_data(SHEET_ID)
        if len(data) >= 2:
            headers = ["Kategori", "Nama Layanan", "URL / Link", "Username / Email / ID", "Password / PIN", "Detail / No. HP", "Catatan"]
            
            # Memasang indeks baris asli Google Sheets (Dimulai dari baris 3 jika ada header berlipat)
            start_row = 3 if len(data) > 2 and data[1][0] == "Kategori" else 2
            
            rows_data = []
            for idx, row in enumerate(data[start_row - 1:], start=start_row):
                # Filter agar baris header tidak ikut terbaca
                if row and row[0] != "Kategori":
                    rows_data.append({"Sheet_Row": idx, "data": row})
            
            # Konversi ke DataFrame
            parsed_rows = []
            for item in rows_data:
                r = item["data"]
                # Normalisasi panjang kolom
                while len(r) < len(headers):
                    r.append("-")
                r_dict = {"Sheet_Row": item["Sheet_Row"]}
                for h, val in zip(headers, r[:len(headers)]):
                    r_dict[h] = val
                parsed_rows.append(r_dict)

            df = pd.DataFrame(parsed_rows)

            if not df.empty:
                # Filter Pencarian
                if search_keyword:
                    mask = df[headers].apply(
                        lambda row: row.astype(str).str.contains(
                            search_keyword, case=False, na=False
                        )
                    ).any(axis=1)
                    df_filtered = df[mask]
                else:
                    df_filtered = df

                st.write(f"Menampilkan **{len(df_filtered)}** data:")
                # Tampilkan tabel tanpa kolom Sheet_Row
                st.dataframe(df_filtered[headers], use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("🛠️ Aksi Edit / Hapus Data")

                # Pilihan Baris Data untuk Diubah
                option_map = {
                    f"Baris {row['Sheet_Row']} | {row['Kategori']} - {row['Nama Layanan']} ({row['Username / Email / ID']})": row
                    for _, row in df_filtered.iterrows()
                }

                selected_option = st.selectbox(
                    "Pilih data yang ingin diedit atau dihapus:",
                    ["-- Pilih Data --"] + list(option_map.keys())
                )

                if selected_option != "-- Pilih Data --":
                    selected_data = option_map[selected_option]
                    row_index = int(selected_data["Sheet_Row"])

                    action = st.radio("Pilih Aksi:", ["Edit Data", "Hapus Data"], horizontal=True)

                    # FITUR EDIT DATA
                    if action == "Edit Data":
                        with st.form("edit_form"):
                            st.info(f"Mengedit data pada **Baris Ke-{row_index}**")
                            col_e1, col_e2 = st.columns(2)

                            with col_e1:
                                edit_kategori = st.text_input("Kategori", value=selected_data["Kategori"])
                                edit_layanan = st.text_input("Nama Layanan / Platform", value=selected_data["Nama Layanan"])
                                edit_url = st.text_input("URL / Link Akses", value=selected_data["URL / Link"])
                                edit_username = st.text_input("Username / Email / ID", value=selected_data["Username / Email / ID"])

                            with col_e2:
                                edit_password = st.text_input("Password / PIN", value=selected_data["Password / PIN"])
                                edit_detail = st.text_input("No. HP / Rekening / Detail", value=selected_data["Detail / No. HP"])
                                edit_catatan = st.text_area("Catatan / Keterangan", value=selected_data["Catatan"])

                            btn_update = st.form_submit_button("Simpan Perubahan", use_container_width=True)

                            if btn_update:
                                try:
                                    updated_row = [
                                        edit_kategori, edit_layanan, edit_url, 
                                        edit_username, edit_password, edit_detail, edit_catatan
                                    ]
                                    # Update cell spesifik di Google Sheets
                                    sheet.update(f"A{row_index}:G{row_index}", [updated_row])
                                    st.success(f"✅ Data baris ke-{row_index} berhasil diperbarui!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"❌ Gagal memperbarui data: {err}")

                    # FITUR HAPUS DATA
                    elif action == "Hapus Data":
                        st.warning(f"⚠️ Anda yakin ingin menghapus permanent data **{selected_data['Nama Layanan']}** (Baris ke-{row_index})?")
                        if st.button("🔴 Ya, Hapus Data Ini", use_container_width=True):
                            try:
                                sheet.delete_rows(row_index)
                                st.success("✅ Data berhasil dihapus dari Google Sheets!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as err:
                                st.error(f"❌ Gagal menghapus data: {err}")
            else:
                st.info("Belum ada data di spreadsheet.")
        else:
            st.info("Belum ada data di spreadsheet.")

    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")

# 5. FOOTER DI BAGIAN PALING BAWAH
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 13px;'>Password Safer v1.0 &bull; Designed by Arisman</p>", 
    unsafe_allow_html=True
)
