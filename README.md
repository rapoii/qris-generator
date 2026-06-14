# QRIS Generator

Generator QRIS QR code dengan nominal bebas untuk **semua merchant**.

Support: DANA, GoPay, ShopeePay, OVO, LinkAja, BCA, BRI, Mandiri, BNI, dan semua provider QRIS Indonesia lainnya.

## Fitur

- **Setup wizard** — scan QRIS QR merchant Anda, tool otomatis ekstrak semua data
- **Generate QR** — masukkan nominal apapun, dapat QR code QRIS langsung
- **Batch** — generate banyak nominal sekaligus
- **Multi-profile** — simpan beberapa merchant, switch kapan saja
- **Decode** — baca QRIS dari gambar manapun
- **Provider-agnostic** — bukan hanya DANA, tapi SEMUA provider

## Instalasi

```bash
cd qris-generator
pip install pillow qrcode pyzbar
```

> **Note (Windows):** `pyzbar` membutuhkan `zbarimg`. Install dari: https://github.com/NaturalHistoryMuseum/pyzbar
> **Note (Linux):** `sudo apt install libzbar0`

## Quick Start

### 1. Setup merchant Anda

```bash
python generate.py setup
```

Tool akan minta:
1. **Path gambar QRIS** — screenshot/foto QRIS merchant Anda
2. **Nama profile** — misalnya `warung`, `toko_abc`
3. Otomatis decode dan simpan semua data merchant

**Cara mendapatkan QRIS:**
1. Buka aplikasi bank/e-wallet (DANA, GoPay, BCA, dll)
2. Menu "Terima Pembayaran" / "QRIS Merchant" / "Tampilkan QRIS"
3. Screenshot QRIS yang muncul
4. Simpan sebagai file PNG/JPG

### 2. Generate QR code

```bash
# Single
python generate.py 25000
# → output/qris_Rp25.000.png

# Batch
python generate.py 5000 10000 25000 50000 100000
```

### 3. Lainnya

```bash
# List profiles
python generate.py --list

# Pakai profile tertentu
python generate.py --profile warung 25000

# Decode QRIS apapun
python generate.py --decode qris_merchant.png

# Lihat detail profile
python generate.py --show
python generate.py --show warung

# Hapus profile
python generate.py --delete warung

# Set default
python generate.py --set-default warung

# Raw payload (tanpa gambar)
python generate.py --payload 25000
```

## Config

Disimpan di `~/.qris_generator/config.json`:

```json
{
  "default_profile": "warung",
  "profiles": {
    "warung": {
      "provider": "DANA",
      "gui": "ID.DANA.WWW",
      "merchant_name": "TOKO RAJA",
      "mcc": "7372",
      "tag26_raw": "0011ID.DANA.WWW...",
      "tag51_raw": "0013ID.CO.QRIS.WWW...",
      "tag26_sub": {"00": "ID.DANA.WWW", "01": "936009150000077253", "02": "000077253", "03": "UMI"},
      "tag51_sub": {"00": "ID.CO.QRIS.WWW", "02": "ID1025460925684", "03": "UMI"},
      "city": "0293",
      "postal_code": "42125",
      "currency": "360",
      "country": "ID"
    }
  }
}
```

## Arsitektur

```
qris-generator/
├── generate.py           # CLI entry point
├── qris_gen/
│   ├── __init__.py
│   ├── core.py           # TLV builder, CRC-16, parser
│   ├── renderer.py       # QR image renderer (PIL + qrcode)
│   └── config.py         # Config/profile management, provider detection
├── output/               # Generated QR images
└── README.md
```

## Supported Providers

| Provider | GUI |
|----------|-----|
| DANA | ID.DANA.WWW |
| GoPay/GrabPay | ID.CO.GRABWALKING.WWW |
| ShopeePay | ID.CO.SHOOPEE.WWW |
| OVO | ID.CO.OCBC.NISP |
| LinkAja | ID.CO.LINKAJA.WWW |
| BCA | ID.CO.BCA.WWW |
| BRI | ID.CO.BRI.WWW |
| Mandiri | ID.CO.MANDIRI.WWW |
| BNI | ID.CO.BNI.WWW |
| BSI | ID.CO.BSI.WWW |
| CIMB Niaga | ID.CO.CIMBNIAGA.WWW |
| DOKU | ID.CO.DOKU.WWW |
| Jenius | ID.CO.JENIUS.WWW |
| ...dan lainnya | Auto-detected |

## License

MIT
