# 🔴 QRIS Generator

Generate QRIS (Quick Response Code Indonesian Standard) QR codes with any nominal amount — no API needed.

![banner](docs/banner.png)

## What is this?

A Python tool that generates valid QRIS Dynamic QR codes from merchant data. Encode any amount into a scannable QRIS code that routes payments to your DANA/e-wallet account.

**How QRIS works:**
- QRIS uses EMVCo MPM (Merchant-Presented Mode) standard
- Data encoded as TLV (Tag-Length-Value) inside the QR code
- Dynamic QRIS (Tag 01=12) embeds the amount — different amount = different QR
- Static QRIS (Tag 01=11) — one QR, customer enters amount

## Install

```bash
pip install pillow qrcode pyzbar
```

`pyzbar` needs [zbar DLL](https://github.com/NaturalHistoryMuseum/pyzbar) on Windows — download `libzbar-64.dll` and put in PATH or script directory.

## Quick Start

```bash
# Single QR
python generate.py 5000

# Batch generate
python generate.py 1000 5000 10000 50000 100000

# Decode existing QRIS image
python generate.py --decode path/to/qris.png

# Show raw payload only
python generate.py --payload 15000
```

## Output

```
QRIS Generator v1.0.0
Merchant : rapoi
NMID     : ID1025460925684
Provider : DANA (936009150000077253)

  Rp     5,000  →  qris_Rp5.000.png  (CRC: OK)
  Rp    10,000  →  qris_Rp10.000.png  (CRC: OK)
  Rp    15,000  →  qris_Rp15.000.png  (CRC: OK)
  Rp   999,999  →  qris_Rp999.999.png (CRC: OK)

Done! 4 QRIS generated in ./output
```

## QRIS EMVCo Structure

Every QRIS QR code contains this TLV payload:

| Tag | Name | Example | Note |
|-----|------|---------|------|
| `00` | Payload Format | `01` | EMVCo v1 |
| `01` | Initiation Method | `12` | 11=Static, **12=Dynamic** |
| `26` | DANA Account Info | Sub-TLV | Provider routing |
| `26.00` | GUI | `ID.DANA.WWW` | Provider identifier |
| `26.01` | Account | `936009150000077253` | Your account |
| `51` | QRIS National Info | Sub-TLV | QRIS standard |
| `51.02` | **NMID** | `ID1025460925684` | National Merchant ID |
| `52` | MCC | `7372` | Category code |
| `53` | Currency | `360` | IDR (ISO 4217) |
| `54` | **Amount** | `5000` | **Rp5.000** |
| `58` | Country | `ID` | Indonesia |
| `59` | Merchant | `rapoi` | Display name |
| `63` | CRC | `879E` | CRC-16/CCITT-FALSE |

**Why different amount = different QR?** Only Tag `54` (amount) and Tag `63` (CRC) change. Everything else stays identical. The CRC auto-recalculates from the payload.

## Use as Library

```python
from qris_gen.core import build_qris_payload, verify_crc, parse_payload
from qris_gen.renderer import render_qris

# Build payload
payload = build_qris_payload(
    amount=25000,
    nmid="ID1025460925684",
    merchant_name="rapoi",
    dana_account="936009150000077253",
)

# Verify CRC
assert verify_crc(payload)

# Generate image
img = render_qris(payload, amount=25000, merchant_name="rapoi", 
                  nmid="ID1025460925684", output_path="qris_25k.png")

# Parse any QRIS payload
parsed = parse_payload(payload)
print(parsed["amount"])  # "25000"
print(parsed["merchant_name"])  # "rapoi"
```

## Customizing Merchant Data

Edit `DEFAULT_MERCHANT` in `generate.py`:

```python
DEFAULT_MERCHANT = {
    "nmid": "ID1025460925684",      # Your NMID
    "merchant_name": "rapoi",       # Display name
    "dana_account": "936009150000077253",  # DANA account
    "dana_sub_account": "000077253",
    "category": "UMI",
    "mcc": "7372",                  # Merchant Category Code
    "currency": "360",              # IDR
    "country": "ID",
    "city": "0293",
    "postal_code": "42125",
}
```

## How to get NMID / Merchant Data?

1. Register as QRIS merchant through DANA, GoPay, BCA, or any Payment Service Provider
2. They give you a QR code — decode it with `python generate.py --decode your_qris.png`
3. Copy the decoded NMID, account info, etc. into `DEFAULT_MERCHANT`
4. Now generate unlimited QR codes with any amount

## Verification

This tool generates **byte-for-byte identical payloads** compared to real QRIS codes from merchant apps. Verified by:
1. Generating QRIS for Rp5.000, Rp12.358, Rp10.000, Rp15.000
2. Decoding the original merchant QR images
3. Comparing payloads — **100% match** (including CRC)

## Project Structure

```
qris-generator/
├── generate.py          # CLI entry point
├── qris_gen/
│   ├── __init__.py
│   ├── core.py          # TLV builder + CRC-16 calculator + parser
│   └── renderer.py      # QR image generator with QRIS styling
├── output/              # Generated QR images
└── README.md
```

## License

MIT

## Disclaimer

This tool generates valid QRIS QR codes for educational and operational purposes. The QR code itself is just a data container — actual payment routing is handled by Bank Indonesia's payment system. You need a registered merchant account (NMID) for payments to work.
