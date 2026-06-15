# QRIS Generator — Dokumentasi Lengkap

![Banner](banner.png)

> **Generator QRIS QR code universal** — buat QRIS dengan nominal bebas untuk merchant manapun.  
> Support semua provider: DANA, GoPay, ShopeePay, OVO, LinkAja, BCA, BRI, Mandiri, BNI, dan lainnya.

**Versi:** 2.0.0  
**GitHub:** [github.com/rapoii/qris-generator](https://github.com/rapoii/qris-generator)  
**License:** MIT

---

## Daftar Isi

1. [Instalasi](#1-instalasi)
2. [Quick Start](#2-quick-start)
3. [Setup Wizard Walkthrough](#3-setup-wizard-walkthrough)
4. [Multi-Profile Management](#4-multi-profile-management)
5. [Format QRIS EMVCo MPM](#5-format-qris-emvco-mpm)
6. [Provider yang Didukung](#6-provider-yang-didukung)
7. [Referensi Python API](#7-referensi-python-api)
8. [Algoritma CRC-16/CCITT-FALSE](#8-algoritma-crc-16ccitt-false)
9. [FAQ](#9-faq)
10. [Panduan Berkontribusi](#10-panduan-berkontribusi)

---

## 1. Instalasi

### Prasyarat

| Prasyarat | Versi Minimum | Keterangan |
|-----------|---------------|------------|
| Python    | 3.10+         | Direkomendasikan 3.12 |
| pip       | 22+           | Untuk install dependencies |
| zbar      | 0.23+         | Library decode QR code (dibutuhkan pyzbar) |

### Windows

#### Langkah 1 — Install Python

Download Python dari [python.org](https://www.python.org/downloads/).  
Saat install, centang **"Add Python to PATH"**.

#### Langkah 2 — Install zbar (wajib untuk pyzbar)

`pyzbar` membutuhkan library `zbar` di sistem. Dua opsi:

**Opsi A — vcpkg (rekomended):**
```powershell
# Install vcpkg jika belum ada
git clone https://github.com/microsoft/vcpkg.git C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
C:\vcpkg\vcpkg install zbar
```

**Opsi B — Download pre-built:**
Download dari [pyzbar Windows install guide](https://github.com/NaturalHistoryMuseum/pyzbar#windows).  
Pastikan file `libzbar-64.dll` ada di PATH atau di direktori yang sama.

#### Langkah 3 — Clone & install dependencies

```bash
git clone https://github.com/rapoii/qris-generator.git
cd qris-generator
pip install pillow qrcode pyzbar
```

### Linux (Ubuntu/Debian)

```bash
# Install system dependency
sudo apt update
sudo apt install -y libzbar0 python3-pip git

# Clone & install
git clone https://github.com/rapoii/qris-generator.git
cd qris-generator
pip install pillow qrcode pyzbar
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install -y zbar python3-pip git
git clone https://github.com/rapoii/qris-generator.git
cd qris-generator
pip install pillow qrcode pyzbar
```

### macOS

```bash
# Install system dependency
brew install zbar

# Clone & install
git clone https://github.com/rapoii/qris-generator.git
cd qris-generator
pip install pillow qrcode pyzbar
```

### Verifikasi Instalasi

```bash
python generate.py --list
```

Jika tidak error, instalasi berhasil.

### Struktur Proyek

```
qris-generator/
├── generate.py           # CLI entry point
├── qris_gen/
│   ├── __init__.py       # Versi package (v2.0.0)
│   ├── core.py           # TLV builder, CRC-16 calculator, payload parser
│   ├── config.py         # Config/profile management, provider detection
│   └── renderer.py       # QR image renderer (Pillow + qrcode)
├── docs/
│   ├── banner.png        # Banner image
│   └── DOCUMENTATION.md  # Dokumentasi ini
├── output/               # QRIS images yang di-generate
└── README.md
```

---

## 2. Quick Start

### Langkah 1 — Setup merchant

```bash
python generate.py setup
```

Tool akan meminta:
1. **Path gambar QRIS** — screenshot/foto QRIS statis merchant Anda
2. **Nama profile** — misalnya `warung`, `toko_abc`
3. Otomatis decode dan simpan semua data merchant

### Langkah 2 — Generate QR code

```bash
# Single — satu nominal
python generate.py 25000
# Output: output/qris_Rp25.000.png

# Batch — beberapa nominal sekaligus
python generate.py 5000 10000 25000 50000 100000
```

### Langkah 3 — Scan & terima pembayaran

Buka file PNG hasil generate di `output/`.  
Pelanggan scan QR code tersebut menggunakan aplikasi pembayaran apapun (DANA, GoPay, BCA, dll).

### Contoh Output

```
QRIS Generator v2.0.0
Profile  : warung
Merchant : TOKO RAJA
NMID     : ID1025460925684
Provider : DANA
Output   : C:\Users\rafi\qris-generator\output

  Rp     5.000  →  qris_Rp5.000.png   (CRC: OK)
  Rp    10.000  →  qris_Rp10.000.png  (CRC: OK)
  Rp    25.000  →  qris_Rp25.000.png  (CRC: OK)
  Rp    50.000  →  qris_Rp50.000.png  (CRC: OK)
  Rp   100.000  →  qris_Rp100.000.png (CRC: OK)

Selesai! 5 QRIS di-generate di C:\Users\rafi\qris-generator\output
```

---

## 3. Setup Wizard Walkthrough

Setup wizard adalah fitur utama untuk pertama kali menggunakan tool. Wizard membaca QRIS QR code merchant Anda, mengekstrak semua data, dan menyimpannya sebagai profile.

### Menjalankan Wizard

```bash
python generate.py setup
```

### Langkah-detail

#### 3.1 Persiapan QRIS

Sebelum menjalankan wizard, siapkan gambar QRIS merchant:

1. Buka aplikasi bank atau e-wallet (DANA, GoPay, BCA, BRI, OVO, dll)
2. Masuk ke menu **"Terima Pembayaran"** / **"QRIS Merchant"** / **"Tampilkan QRIS"**
3. **Screenshot** atau **foto** QRIS yang muncul
4. Simpan sebagai file gambar (`.png`, `.jpg`, `.jpeg`)

> **Penting:** Gunakan QRIS **statis** (tanpa nominal). QRIS statis bisa dipakai untuk nominal berapapun.

#### 3.2 Jalankan Wizard

```
==================================================
  QRIS Generator — Setup Wizard
==================================================

Siapkan QRIS QR code merchant Anda.
Bisa dari: screenshot QRIS statis, foto QR code, atau file gambar.

Cara mendapatkan QRIS:
  1. Buka aplikasi bank/e-wallet (DANA, GoPay, BCA, dll)
  2. Buka menu 'Terima Pembayaran' / 'QRIS Merchant'
  3. Screenshot QRIS code yang muncul
  4. Simpan sebagai file gambar (PNG/JPG)

Path gambar QRIS: /path/to/qris_screenshot.png
```

#### 3.3 Dekode Otomatis

Tool otomatis membaca QR code dan menampilkan hasil decode:

```
Membaca QR code dari qris_screenshot.png...
Payload (195 chars):
  00020101021226630011ID.DANA.WWW01...

Parsed:
  Tipe       : Static
  Provider   : DANA
  GUI        : ID.DANA.WWW
  NMID       : ID1025460925684
  Merchant   : TOKO RAJA
  MCC        : 7372
  Amount     : Rp-
  Currency   : IDR (360)
  Country    : ID
  City       : 0293
  Postal     : 42125
  CRC Valid  : True
```

#### 3.4 Data yang Diekstrak

```
==================================================
  Data yang diekstrak:
==================================================
  Provider   : DANA
  GUI        : ID.DANA.WWW
  Merchant   : TOKO RAJA
  NMID       : ID1025460925684
  MCC        : 7372
  City       : 0293
  Postal     : 42125
  Currency   : 360
  Country    : ID
  Tag26 Raw  : 0011ID.DANA.WWW011993600915000007725302...
  Tag51 Raw  : 0013ID.CO.QRIS.WWW0217ID1025460925684...
```

#### 3.5 Penamaan Profile

```
Nama profile (contoh: 'warung', 'toko', 'nama_anda'): warung
```

> **Aturan nama:** Tidak boleh kosong, tidak boleh ada spasi. Gunakan underscore (`_`) sebagai pengganti spasi.

#### 3.6 Konfigurasi Selesai

```
Profile 'warung' sudah ada. Timpa? (y/N): n
Jadikan 'warung' sebagai default? (Y/n): y

✓ Profile 'warung' berhasil disimpan!
  Config: /home/user/.qris_generator/config.json

Untuk generate QRIS:
  python generate.py 25000              # default profile
  python generate.py --profile warung 25000  # profile spesifik
```

---

## 4. Multi-Profile Management

QRIS Generator mendukung beberapa merchant profile sekaligus. Cocok untuk pengelola yang mengelola beberapa toko.

### Perintah Profile

| Perintah | Fungsi |
|----------|--------|
| `python generate.py setup` | Tambah profile baru |
| `python generate.py --list` | Lihat semua profile |
| `python generate.py --show` | Detail default profile |
| `python generate.py --show nama` | Detail profile tertentu |
| `python generate.py --set-default nama` | Ubah default profile |
| `python generate.py --delete nama` | Hapus profile |
| `python generate.py --profile nama 25000` | Generate pakai profile tertentu |

### Menambah Profile Baru

```bash
# Tambah merchant baru
python generate.py setup

# Atau decode QRIS langsung jadi profile
python generate.py --decode qris_baru.png
# → Akan ditawari untuk simpan sebagai profile
```

### Contoh Multi-Profile

```bash
# Setup 3 merchant berbeda
python generate.py setup    # → "warung" (DANA)
python generate.py setup    # → "toko_abc" (GoPay)
python generate.py setup    # → "kafe_xyz" (BCA)

# List semua
python generate.py --list
```

Output:
```
Config: /home/user/.qris_generator/config.json
========================================
  warung ★
    Provider : DANA
    Merchant : TOKO RAJA
    NMID     : ID1025460925684

  toko_abc
    Provider : GrabPay/GoPay
    Merchant : TOKO ABC JAYA
    NMID     : ID1025478901234

  kafe_xyz
    Provider : BCA
    Merchant : KAFE XYZ
    NMID     : ID1025434567890

★ = default profile
```

### Generate dengan Profile Spesifik

```bash
# Pakai default profile (warung)
python generate.py 25000

# Pakai profile tertentu
python generate.py --profile toko_abc 25000
python generate.py --profile kafe_xyz 10000 20000 30000
```

### Lokasi Config

Config disimpan di:
- **Windows:** `C:\Users\<username>\.qris_generator\config.json`
- **Linux/Mac:** `~/.qris_generator/config.json`

---

## 5. Format QRIS EMVCo MPM

QRIS menggunakan standar **EMVCo Merchant Presented Mode (MPM)** — format QR code yang sama dengan yang digunakan secara internasional.

### Struktur Payload

Setiap payload QRIS adalah string yang terdiri dari elemen **TLV (Tag-Length-Value)**:

```
[Tag 2 digit][Length 2 digit][Value ...]
```

Contoh: `52047372` artinya:
- Tag: `52` (Merchant Category Code)
- Length: `04` (4 karakter)
- Value: `7372`

### Tabel Tag QRIS

| Tag | Nama | Wajib | Contoh Value | Keterangan |
|-----|------|-------|-------------|------------|
| `00` | Payload Format Indicator | ✅ | `01` | Selalu `01` |
| `01` | Point of Initiation Method | ✅ | `11`/`12` | `11`=Static, `12`=Dynamic |
| `02`-`25` | Merchant Account Info | ❌ | - | Reserved |
| `26` | Merchant Account Info (Provider) | ✅ | *(nested TLV)* | Info akun provider (DANA, GoPay, dll) |
| `27`-`50` | Merchant Account Info | ❌ | - | Reserved |
| `51` | Merchant Account Info (QRIS Nasional) | ✅ | *(nested TLV)* | Info merchant QRIS nasional |
| `52` | Merchant Category Code (MCC) | ✅ | `7372` | Kategori usaha (ISO 18245) |
| `53` | Transaction Currency | ✅ | `360` | ISO 4217 (`360`=IDR) |
| `54` | Transaction Amount | ⚠️ | `25000` | Nominal (wajib untuk Dynamic QR) |
| `55` | Tip/Convenience Indicator | ❌ | - | - |
| `56`-`57` | - | ❌ | - | Reserved |
| `58` | Country Code | ✅ | `ID` | ISO 3166-1 alpha-2 |
| `59` | Merchant Name | ✅ | `TOKO RAJA` | Nama merchant |
| `60` | Merchant City | ✅ | `0293` | Kota merchant |
| `61` | Postal Code | ❌ | `42125` | Kode pos |
| `62` | Additional Data | ❌ | *(nested TLV)* | Data tambahan |
| `63` | CRC | ✅ | `3A4B` | CRC-16/CCITT-FALSE checksum |

### Struktur Nested Tag 26 (Provider Account Info)

| Sub-Tag | Nama | Contoh | Keterangan |
|---------|------|--------|------------|
| `00` | Global Unique Identifier (GUI) | `ID.DANA.WWW` | Identifier provider |
| `01` | Account Number | `936009150000077253` | Nomor akun merchant |
| `02` | Merchant ID / Sub-Account | `000007725` | Sub-identifier |
| `03` | Category / Criteria | `UMI` | Kategori merchant |

### Struktur Nested Tag 51 (QRIS Nasional)

| Sub-Tag | Nama | Contoh | Keterangan |
|---------|------|--------|------------|
| `00` | Global Unique Identifier | `ID.CO.QRIS.WWW` | Selalu `ID.CO.QRIS.WWW` |
| `02` | National Merchant ID (NMID) | `ID1025460925684` | ID merchant nasional |
| `03` | Category | `UMI` | Kategori merchant |

### Contoh Parse Payload

Payload QRIS contoh:
```
00020101021226630011ID.DANA.WWW011993600915000007725302110000077250303UMI51560013ID.CO.QRIS.WWW0217ID10254609256840303UMI5204737253033605405250005802ID5908TOKO RAJA600502936105421256304xxxx
```

Dibaca:

| Posisi | Tag | Length | Value | Arti |
|--------|-----|--------|-------|------|
| 0-7 | `00` | `02` | `01` | Payload Format: EMVCo MPM |
| 8-15 | `01` | `02` | `12` | Dynamic QR |
| 16-78 | `26` | `63` | *(nested)* | Provider: DANA |
| ... | `52` | `04` | `7372` | MCC: Digital Goods |
| ... | `53` | `03` | `360` | Currency: IDR |
| ... | `54` | `05` | `25000` | Amount: Rp25.000 |
| ... | `58` | `02` | `ID` | Country: Indonesia |
| ... | `59` | `08` | `TOKO RAJA` | Merchant name |
| ... | `60` | `05` | `0293` | City code |
| ... | `63` | `04` | `xxxx` | CRC-16 checksum |

---

## 6. Provider yang Didukung

QRIS Generator mendukung **semua provider** QRIS Indonesia. Provider dideteksi otomatis dari **Global Unique Identifier (GUI)** di Tag 26 sub-tag `00`.

### E-Wallet

| Provider | GUI (Tag 26.00) | Tipe |
|----------|-----------------|------|
| DANA | `ID.DANA.WWW` | E-Wallet |
| GoPay | `ID.CO.GOPAY.WWW` | E-Wallet |
| GoPay/GrabPay | `ID.CO.GRABWALKING.WWW` | E-Wallet |
| GrabPay | `ID.CO.GRAB.WWW` | E-Wallet |
| ShopeePay | `ID.CO.SHOOPEE.WWW` | E-Wallet |
| ShopeePay | `ID.CO.SHOOPEEPAY.WWW` | E-Wallet |
| OVO | `ID.CO.OVO.WWW` | E-Wallet |
| OVO (OCBC) | `ID.CO.OCBC.NISP` | E-Wallet |
| LinkAja | `ID.CO.LINKAJA.WWW` | E-Wallet |
| iSaku | `ID.CO.ISAKU.WWW` | E-Wallet |
| DOKU | `ID.CO.DOKU.WWW` | E-Wallet |
| Jenius | `ID.CO.JENIUS.WWW` | E-Wallet |

### Bank Umum

| Provider | GUI (Tag 26.00) | Tipe |
|----------|-----------------|------|
| BCA | `ID.CO.BCA.WWW` | Bank |
| BRI | `ID.CO.BRI.WWW` | Bank |
| Mandiri | `ID.CO.MANDIRI.WWW` | Bank |
| BNI | `ID.CO.BNI.WWW` | Bank |
| BSI | `ID.CO.BSI.WWW` | Bank (Syariah) |
| CIMB Niaga | `ID.CO.CIMBNIAGA.WWW` | Bank |
| Muamalat | `ID.CO.BANKMUAMALAT.WWW` | Bank (Syariah) |
| Permata | `ID.CO.PERMATA.WWW` | Bank |
| Maybank | `ID.CO.MAYBANK.WWW` | Bank |
| BTPN | `ID.CO.BTPN.WWW` | Bank |
| Panin | `ID.CO.PANIN.WWW` | Bank |
| Mega | `ID.CO.MEGA.WWW` | Bank |
| Bukopin | `ID.CO.BUKOPIN.WWW` | Bank |
| Sinarmas | `ID.CO.SINARMAS.WWW` | Bank |
| Danamon | `ID.CO.BANKDANAMON.WWW` | Bank |
| Nobu Bank | `ID.CO.NOBUBANK.WWW` | Bank |
| BTN | `ID.CO.BANKBTN.WWW` | Bank |
| DKI | `ID.CO.BANKDKI.WWW` | Bank |

### QRIS Nasional

| Provider | GUI (Tag 51.00) | Tipe |
|----------|-----------------|------|
| QRIS Nasional | `ID.CO.QRIS.WWW` | Nasional |

> **Catatan:** Provider yang tidak terdaftar di atas akan tetap berfungsi. Tool menggunakan raw payload langsung dari QRIS yang di-decode, sehingga provider apapun bisa direplikasi. Jika GUI tidak dikenali, tool menampilkan `Unknown (<GUI>)`.

### Menambah Provider Baru

Provider dideteksi dari `PROVIDER_MAP` di `qris_gen/config.py`. Untuk menambah:

```python
# qris_gen/config.py
PROVIDER_MAP: dict[str, str] = {
    # ... existing entries ...
    "ID.CO.BANKBARU.WWW": "Bank Baru",
}
```

---

## 7. Referensi Python API

Modul `qris_gen` bisa dipakai langsung dari Python tanpa CLI.

### Import

```python
from qris_gen.core import build_qris_payload, parse_payload, verify_crc
from qris_gen.config import extract_profile_from_parsed, detect_provider
from qris_gen.renderer import render_qris, render_batch
```

---

### `core.build_qris_payload()`

Bangun payload QRIS EMVCo MPM lengkap dari data merchant dan nominal.

```python
def build_qris_payload(
    amount: int | float,
    tag26_raw: str = "",
    tag51_raw: str = "",
    merchant_name: str = "",
    mcc: str = "7372",
    currency: str = "360",
    country: str = "ID",
    city: str = "",
    postal_code: str = "",
    additional_raw: str = "",
    dynamic: bool = True,
) -> str
```

**Parameter:**

| Parameter | Tipe | Default | Keterangan |
|-----------|------|---------|------------|
| `amount` | `int \| float` | *(wajib)* | Nominal transaksi dalam IDR |
| `tag26_raw` | `str` | `""` | Raw Tag 26 string (info akun provider) |
| `tag51_raw` | `str` | `""` | Raw Tag 51 string (info merchant QRIS nasional) |
| `merchant_name` | `str` | `""` | Nama tampilan merchant |
| `mcc` | `str` | `"7372"` | Merchant Category Code (ISO 18245) |
| `currency` | `str` | `"360"` | ISO 4217 numeric (`360`=IDR) |
| `country` | `str` | `"ID"` | ISO 3166-1 alpha-2 |
| `city` | `str` | `""` | Kota / kode kota |
| `postal_code` | `str` | `""` | Kode pos |
| `additional_raw` | `str` | `""` | Raw Tag 62 string (data tambahan) |
| `dynamic` | `bool` | `True` | `True`=Dynamic (nominal embedded), `False`=Static |

**Return:** `str` — payload QRIS lengkap termasuk CRC, siap untuk encoding ke QR.

**Contoh:**

```python
# Contoh dengan raw tags dari decoded QRIS
payload = build_qris_payload(
    amount=25000,
    tag26_raw="0011ID.DANA.WWW011993600915000007725302110000077250303UMI",
    tag51_raw="0013ID.CO.QRIS.WWW0217ID10254609256840303UMI",
    merchant_name="TOKO RAJA",
    city="0293",
    postal_code="42125",
    additional_raw="60210011ID.DANA.WWW",
)
print(payload)
# 00020101021226630011ID.DANA.WWW...63043A4B
```

---

### `core.parse_payload()`

Parse string payload QRIS menjadi dict terstruktur.

```python
def parse_payload(payload: str) -> dict
```

**Parameter:**

| Parameter | Tipe | Keterangan |
|-----------|------|------------|
| `payload` | `str` | Raw QRIS payload string |

**Return:** `dict` dengan key:

| Key | Tipe | Contoh | Keterangan |
|-----|------|--------|------------|
| `payload_format` | `str` | `"01"` | Payload format indicator |
| `initiation_method` | `str` | `"12"` | `11`=Static, `12`=Dynamic |
| `initiation_type` | `str` | `"Dynamic"` | Human-readable initiation type |
| `provider_account_info` | `dict` | `{"raw": "...", "sub": {...}}` | Tag 26 dengan nested sub-tags |
| `merchant_account_info` | `dict` | `{"raw": "...", "sub": {...}}` | Tag 51 dengan nested sub-tags |
| `mcc` | `str` | `"7372"` | Merchant Category Code |
| `currency` | `str` | `"360"` | ISO 4217 numeric |
| `currency_code` | `str` | `"IDR"` | Currency label |
| `amount` | `str` | `"25000"` | Nominal transaksi |
| `country` | `str` | `"ID"` | Country code |
| `merchant_name` | `str` | `"TOKO RAJA"` | Nama merchant |
| `merchant_city` | `str` | `"0293"` | Kota |
| `postal_code` | `str` | `"42125"` | Kode pos |
| `additional_data` | `dict` | `{"raw": "...", "sub": {...}}` | Tag 62 |
| `crc` | `str` | `"3A4B"` | CRC-16 checksum |
| `_raw_payload` | `str` | *(full payload)* | Payload asli |

**Contoh:**

```python
parsed = parse_payload(payload)
print(parsed["merchant_name"])          # "TOKO RAJA"
print(parsed["initiation_type"])        # "Dynamic"
print(parsed["provider_account_info"]["sub"]["00"])  # "ID.DANA.WWW"
print(parsed["currency_code"])          # "IDR"
```

---

### `core.verify_crc()`

Verifikasi checksum CRC-16 payload QRIS.

```python
def verify_crc(payload: str) -> bool
```

**Parameter:**

| Parameter | Tipe | Keterangan |
|-----------|------|------------|
| `payload` | `str` | Payload QRIS lengkap (termasuk CRC) |

**Return:** `bool` — `True` jika CRC valid, `False` jika corrupt/tidak ada CRC.

**Contoh:**

```python
valid = verify_crc(payload)
print(valid)  # True

# Cek payload dari QR scan
from pyzbar.pyzbar import decode
from PIL import Image
img = Image.open("qris_merchant.png")
data = decode(img)[0].data.decode()
print(verify_crc(data))  # True
```

---

### `config.extract_profile_from_parsed()`

Ekstrak data profile dari hasil `parse_payload()`. Berguna untuk membuat profile dari QRIS yang di-decode.

```python
def extract_profile_from_parsed(parsed: dict) -> dict
```

**Parameter:**

| Parameter | Tipe | Keterangan |
|-----------|------|------------|
| `parsed` | `dict` | Hasil dari `parse_payload()` |

**Return:** `dict` dengan key:

| Key | Tipe | Contoh | Keterangan |
|-----|------|--------|------------|
| `provider` | `str` | `"DANA"` | Nama provider terdeteksi |
| `gui` | `str` | `"ID.DANA.WWW"` | Global Unique Identifier |
| `tag26_raw` | `str` | `"0011ID.DANA.WWW..."` | Raw Tag 26 untuk rebuild |
| `tag51_raw` | `str` | `"0013ID.CO.QRIS.WWW..."` | Raw Tag 51 untuk rebuild |
| `tag26_sub` | `dict` | `{"00": "ID.DANA.WWW", ...}` | Sub-tag Tag 26 |
| `tag51_sub` | `dict` | `{"00": "ID.CO.QRIS.WWW", ...}` | Sub-tag Tag 51 |
| `merchant_name` | `str` | `"TOKO RAJA"` | Nama merchant |
| `nmid` | `str` | `"ID1025460925684"` | National Merchant ID |
| `mcc` | `str` | `"7372"` | Merchant Category Code |
| `currency` | `str` | `"360"` | ISO 4217 currency code |
| `country` | `str` | `"ID"` | Country code |
| `city` | `str` | `"0293"` | Kota |
| `postal_code` | `str` | `"42125"` | Kode pos |
| `initiation_type` | `str` | `"Dynamic"` / `"Static"` | Tipe QR |
| `additional_raw` | `str` | `"60210011ID.DANA.WWW"` | Raw Tag 62 |
| `source_payload` | `str` | *(full payload)* | Payload asli |

**Contoh:**

```python
from qris_gen.core import parse_payload
from qris_gen.config import extract_profile_from_parsed, save_config, save_profile, load_config

parsed = parse_payload(payload_string)
profile = extract_profile_from_parsed(parsed)

print(profile["provider"])      # "DANA"
print(profile["nmid"])           # "ID1025460925684"
print(profile["tag26_raw"])     # "0011ID.DANA.WWW0119936009150000077253..."

# Simpan sebagai profile
cfg = load_config()
cfg = save_profile(cfg, "my_merchant", profile)
save_config(cfg)
```

---

### `renderer.render_qris()`

Generate gambar QR code bergaya QRIS.

```python
def render_qris(
    payload: str,
    amount: int,
    merchant_name: str,
    nmid: str = "",
    provider: str = "",
    output_path: str | None = None,
    qr_size: int = 400,
) -> Image.Image
```

**Parameter:**

| Parameter | Tipe | Default | Keterangan |
|-----------|------|---------|------------|
| `payload` | `str` | *(wajib)* | Raw QRIS payload string |
| `amount` | `int` | *(wajib)* | Nominal dalam IDR (untuk tampilan) |
| `merchant_name` | `str` | *(wajib)* | Nama tampilan merchant |
| `nmid` | `str` | `""` | National Merchant ID (opsional) |
| `provider` | `str` | `""` | Nama provider (opsional, tampil di bawah QR) |
| `output_path` | `str \| None` | `None` | Path file PNG output (opsional) |
| `qr_size` | `int` | `400` | Ukuran QR code dalam pixel |

**Return:** `PIL.Image.Image` — objek gambar Pillow.

**Layout output:**

```
┌─────────────────────────┐
│      TOKO RAJA          │  ← Merchant name (bold, 22pt)
│      Rp25.000           │  ← Amount (bold, 28pt)
│       「QRIS」           │  ← QRIS label (bold, 18pt)
│                         │
│  ████ QR CODE ████████  │  ← QR code (400x400px default)
│  █                   █  │
│  █                   █  │  ← Red accent bars di kiri & kanan bawah
│  █████████████████████  │
│         DANA            │  ← Provider name (12pt, gray)
│    NMID : ID102...      │  ← NMID (13pt, gray)
└─────────────────────────┘
```

**Contoh:**

```python
from qris_gen.core import build_qris_payload
from qris_gen.renderer import render_qris

payload = build_qris_payload(
    amount=25000,
    tag26_raw=profile["tag26_raw"],
    tag51_raw=profile["tag51_raw"],
    merchant_name="TOKO RAJA",
    city=profile["city"],
    postal_code=profile["postal_code"],
    additional_raw=profile["additional_raw"],
)

# Simpan langsung ke file
img = render_qris(
    payload=payload,
    amount=25000,
    merchant_name="TOKO RAJA",
    nmid="ID1025460925684",
    provider="DANA",
    output_path="qris_Rp25.000.png",
)

# Atau manipulasi dulu sebelum simpan
img = render_qris(payload=payload, amount=25000, merchant_name="TOKO RAJA")
img.show()  # Tampilkan di image viewer
```

---

### `renderer.render_batch()`

Generate dan simpan QRIS image dengan auto-naming.

```python
def render_batch(
    payload: str,
    amount: int,
    merchant_name: str,
    nmid: str = "",
    provider: str = "",
    output_dir: str = ".",
    filename_prefix: str = "qris",
) -> str
```

**Parameter:**

| Parameter | Tipe | Default | Keterangan |
|-----------|------|---------|------------|
| `payload` | `str` | *(wajib)* | Raw QRIS payload |
| `amount` | `int` | *(wajib)* | Nominal |
| `merchant_name` | `str` | *(wajib)* | Nama merchant |
| `nmid` | `str` | `""` | NMID |
| `provider` | `str` | `""` | Provider |
| `output_dir` | `str` | `"."` | Direktori output |
| `filename_prefix` | `str` | `"qris"` | Prefix nama file |

**Return:** `str` — path file yang di-generate.

**Contoh:**

```python
path = render_batch(
    payload=payload,
    amount=25000,
    merchant_name="TOKO RAJA",
    provider="DANA",
    output_dir="output",
)
print(path)  # "output/qris_Rp25.000.png"
```

---

### Contoh Lengkap: End-to-End

```python
from qris_gen.core import build_qris_payload, parse_payload, verify_crc
from qris_gen.config import extract_profile_from_parsed, load_config, save_profile, save_config
from qris_gen.renderer import render_batch

# 1. Decode QRIS merchant dari gambar (sekali saja)
from pyzbar.pyzbar import decode
from PIL import Image

img = Image.open("qris_screenshot.png")
raw = decode(img)[0].data.decode("utf-8")
parsed = parse_payload(raw)
profile = extract_profile_from_parsed(parsed)

# 2. Simpan profile
cfg = load_config()
cfg = save_profile(cfg, "toko_saya", profile, make_default=True)
save_config(cfg)

# 3. Generate QRIS untuk berbagai nominal
for amount in [5000, 10000, 25000, 50000]:
    payload = build_qris_payload(
        amount=amount,
        tag26_raw=profile["tag26_raw"],
        tag51_raw=profile["tag51_raw"],
        merchant_name=profile["merchant_name"],
        mcc=profile["mcc"],
        currency=profile["currency"],
        country=profile["country"],
        city=profile["city"],
        postal_code=profile["postal_code"],
        additional_raw=profile["additional_raw"],
    )

    assert verify_crc(payload), "CRC check failed!"

    path = render_batch(
        payload=payload,
        amount=amount,
        merchant_name=profile["merchant_name"],
        nmid=profile["nmid"],
        provider=profile["provider"],
        output_dir="output",
    )
    print(f"Rp{amount:,} → {path}")
```

---

## 8. Algoritma CRC-16/CCITT-FALSE

QRIS menggunakan checksum **CRC-16/CCITT-FALSE** untuk memverifikasi integritas payload. Tag `63` di akhir payload menyimpan 4 karakter hex dari CRC-16 ini.

### Parameter Algoritma

| Parameter | Nilai | Keterangan |
|-----------|-------|------------|
| Polinomial | `0x1021` | x^16 + x^12 + x^5 + 1 |
| Init Value | `0xFFFF` | Nilai awal register |
| Reflected Input | Tidak | Data tidak di-reflect |
| Reflected Output | Tidak | Output tidak di-reflect |
| Final XOR | `0x0000` | Tidak ada XOR final |
| Output | 4 hex char | Uppercase, zero-padded |

### Cara Kerja

1. Ambil seluruh payload **tanpa** CRC (sampai sebelum `6304`)
2. Tambah string `"6304"` di belakang (Tag 63, Length 04)
3. Hitung CRC-16 dari string tersebut
4. Hasil CRC (4 hex char) ditempelkan di akhir payload

### Implementasi Python

```python
def crc16_ccitt_false(data: str) -> str:
    """
    CRC-16/CCITT-FALSE checksum.
    Polynomial: 0x1021, Init: 0xFFFF, No final XOR.
    """
    crc = 0xFFFF
    for char in data:
        crc ^= (ord(char) << 8)       # XOR byte masuk ke MSB register
        for _ in range(8):             # Proses 8 bit per karakter
            if crc & 0x8000:           # Cek bit tertinggi
                crc = (crc << 1) ^ 0x1021  # Shift + XOR polinomial
            else:
                crc <<= 1              # Shift saja
            crc &= 0xFFFF             # Batasi 16 bit
    return format(crc, "04X")          # Output 4 hex char uppercase
```

### Verifikasi CRC

```python
def verify_crc(payload: str) -> bool:
    """Verifikasi CRC-16 payload QRIS."""
    crc_pos = payload.find("6304")        # Cari Tag 63
    if crc_pos == -1:
        return False                       # Tidak ada CRC
    payload_no_crc = payload[:crc_pos]    # Payload tanpa CRC
    crc_stored = payload[crc_pos + 4:]    # CRC yang tersimpan
    crc_calculated = crc16_ccitt_false(payload_no_crc + "6304")
    return crc_stored == crc_calculated
```

### Contoh Perhitungan Manual

Misal payload (tanpa CRC):
```
0002010102115204737253033605802ID5904TEST6002ID
```

Langkah:
1. Tambah `"6304"` → `0002010102115204737253033605802ID5904TEST6002ID6304`
2. Hitung CRC-16/CCITT-FALSE dari string di atas
3. Misal hasil: `ABCD`
4. Payload final: `0002010102115204737253033605802ID5904TEST6002ID6304ABCD`

### Mengapa CRC Penting?

- Semua aplikasi pembayaran (DANA, GoPay, BCA, dll) **memverifikasi CRC** sebelum memproses pembayaran
- Payload dengan CRC salah **akan ditolak** oleh scanner
- QRIS Generator menghitung CRC otomatis — Anda tidak perlu khawatir
- Tool juga bisa memverifikasi CRC dari QRIS manapun via `verify_crc()`

---

## 9. FAQ

### Umum

**Q: Apakah tool ini legal?**

Ya. Tool ini hanya membuat QR code dari data merchant yang sudah Anda miliki. QRIS merchant Anda sendiri bersifat publik — siapapun boleh scan dan melihatnya. Tool ini hanya mempermudah membuat QR dengan nominal tertentu.

**Q: Apakah QRIS yang di-generate bisa dipakai untuk menerima pembayaran?**

Ya, **100% identik** dengan QRIS asli. Tool ini menghasilkan payload yang byte-for-byte sama dengan QRIS dari bank/e-wallet. Telah diverifikasi dengan membandingkan payload dari merchant QRIS real.

**Q: Berapa batas nominal yang bisa di-generate?**

Tidak ada batasan dari tool ini. Batas nominal ditentukan oleh provider (DANA, BCA, dll), biasanya:
- E-Wallet: Rp1 — Rp20.000.000
- Bank: Rp1 — Rp50.000.000
- Tergantung aturan merchant masing-masing

**Q: Bisa untuk QRIS statis?**

Ya. QRIS statis dari merchant bisa di-decode dan di-generate dengan nominal apapun. Tool otomatis mengubah `initiation_method` dari `11` (static) menjadi `12` (dynamic) sehingga nominal ter-embed.

### Teknis

**Q: `pyzbar` error saat import?**

```bash
# Windows: pastikan zbar library terinstall
# Download dari https://github.com/NaturalHistoryMuseum/pyzbar

# Linux:
sudo apt install libzbar0

# macOS:
brew install zbar
```

**Q: Font tidak tampil di gambar QR?**

Tool otomatis mencari font system (Segoe UI, Arial, DejaVu Sans). Jika tidak ditemukan, fallback ke font default PIL. Install font jika perlu:

```bash
# Linux
sudo apt install fonts-dejavu-core

# macOS — font sudah tersedia default
```

**Q: Gambar QR tidak bisa di-scan?**

Pastikan:
1. Payload asli valid (CRC OK). Jalankan: `python generate.py --decode qris.png`
2. Gambar cukup besar dan kontras tinggi
3. Jangan resize QR code terlalu kecil (minimal 200x200px)
4. Pastikan QR code tidak terpotong

**Q: `Tag 26 tidak ditemukan` saat setup?**

Gambar yang di-upload bukan QRIS valid. Pastikan:
1. Gambar berisi QR code yang jelas dan tidak blur
2. QR code benar-benar QRIS (bukan QR code URL/link biasa)
3. Coba ambil screenshot ulang dengan kualitas lebih baik

**Q: Bisa generate QRIS untuk merchant lain (bukan milik saya)?**

Secara teknis ya — jika Anda punya akses ke QRIS statis merchant tersebut (yang bersifat publik). Namun pembayaran tetap masuk ke rekening merchant yang bersangkutan, bukan ke Anda.

**Q: Dimana config disimpan?**

- **Windows:** `C:\Users\<username>\.qris_generator\config.json`
- **Linux/Mac:** `~/.qris_generator/config.json`

**Q: Bagaimana cara backup profile?**

```bash
# Copy file config
cp ~/.qris_generator/config.json ~/backup_qris_config.json

# Restore
cp ~/backup_qris_config.json ~/.qris_generator/config.json
```

**Q: Bisa pakai tanpa generate gambar (payload saja)?**

```bash
python generate.py --payload 25000
# Output: raw payload string tanpa gambar

# Atau dari Python API
from qris_gen.core import build_qris_payload
payload = build_qris_payload(amount=25000, tag26_raw="...", ...)
```

---

## 10. Panduan Berkontribusi

### Memulai

```bash
# 1. Fork repository di GitHub
# 2. Clone fork Anda
git clone https://github.com/<username>/qris-generator.git
cd qris-generator

# 3. Buat virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 4. Install dependencies
pip install pillow qrcode pyzbar

# 5. Buat branch baru
git checkout -b feature/fitur-baru
```

### Standar Kode

- **Python 3.10+** — gunakan type hints modern (`str | None` bukan `Optional[str]`)
- **Docstring** — setiap fungsi publik harus punya docstring
- **Naming** — `snake_case` untuk fungsi/variabel, `UPPER_CASE` untuk konstanta
- **Tidak ada dependency baru** tanpa diskusi — Pillow, qrcode, pyzbar sudah cukup

### Struktur Pull Request

1. Satu PR per fitur/fix
2. Jelaskan **apa** yang diubah dan **mengapa**
3. Test manual sebelum submit:
   ```bash
   # Test setup
   python generate.py setup
   
   # Test generate
   python generate.py 10000 25000 50000
   
   # Test decode
   python generate.py --decode output/qris_Rp25.000.png
   
   # Test CRC
   python generate.py --payload 25000
   ```
4. Pastikan CRC output valid

### Area Kontribusi

| Area | Difficulty | Deskripsi |
|------|-----------|-----------|
| Tambah provider | Mudah | Tambah entry ke `PROVIDER_MAP` di `config.py` |
| Perbaiki font | Mudah | Tambah path font baru ke `renderer.py` |
| Unit test | Sedang | Tambah test suite untuk `core.py` |
| Web interface | Lanjut | Buat Flask/Streamlit frontend |
| Batch CSV | Sedang | Generate dari file CSV nominal |
| SVG output | Sedang | Generate QR sebagai SVG alih-alih PNG |
| i18n | Mudah | Terjemahkan output CLI ke bahasa lain |

### Melaporkan Bug

Buka [GitHub Issues](https://github.com/rapoii/qris-generator/issues) dengan:

1. **Deskripsi** — apa yang terjadi
2. **Steps to reproduce** — langkah untuk mereproduksi
3. **Expected vs actual** — yang diharapkan vs yang terjadi
4. **Environment** — OS, Python versi, versi tool
5. **Payload** — raw QRIS payload jika relevan (tanpa data sensitif)

### Tips Pengembangan

```bash
# Debug payload
python -c "
from qris_gen.core import parse_payload, verify_crc
payload = '...'  # paste payload di sini
print(parse_payload(payload))
print('CRC valid:', verify_crc(payload))
"

# Debug config
python -c "
from qris_gen.config import load_config
import json
print(json.dumps(load_config(), indent=2))
"
```

---

## Referensi

| Standar | Dokumen |
|---------|---------|
| EMVCo QR Code Specification | [emvco.com](https://www.emvco.com/emv-technologies/qrcodes/) |
| ISO 18245 (MCC) | Kode kategori merchant |
| ISO 4217 (Currency) | `360` = IDR |
| ISO 3166-1 (Country) | `ID` = Indonesia |
| QRIS Spesifikasi | [qris.id](https://qris.id) |

---

*Terakhir diperbarui: Juni 2025*  
*QRIS Generator v2.0.0 — MIT License*
