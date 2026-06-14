"""
QRIS Generator CLI — Universal Merchant Tool.

Setup:
    python generate.py setup                    Interactive setup wizard

Generate:
    python generate.py 25000                    Single QR Rp25.000
    python generate.py 10000 25000 50000        Batch

Decode:
    python generate.py --decode qris.png        Decode any QRIS image

Profiles:
    python generate.py --list                   List merchant profiles
    python generate.py --profile warung 25000   Use specific profile
    python generate.py --delete warung          Delete profile
    python generate.py --set-default warung     Set default profile
"""

import argparse
import json
import sys
from pathlib import Path

# Fix sys.path: remove hermes venv to avoid broken PIL/qrcode import conflicts.
# Users should install deps with their own Python, not hermes' internal venv.
sys.path = [p for p in sys.path if "hermes" not in p.lower()]

from qris_gen.core import build_qris_payload, parse_payload, verify_crc
from qris_gen.renderer import render_qris, render_batch
from qris_gen.config import (
    load_config,
    save_config,
    get_profile,
    save_profile,
    delete_profile,
    detect_provider,
    extract_profile_from_parsed,
    print_profile,
    config_path,
)


# ──────────────────────────────────────────────
#  DECODE
# ──────────────────────────────────────────────

def decode_qris_image(image_path: str, verbose: bool = True) -> dict:
    """Decode QRIS from image file. Returns parsed dict."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode
    except ImportError:
        print("ERROR: Install dependencies: pip install pyzbar pillow")
        sys.exit(1)

    img = Image.open(image_path)
    results = zbar_decode(img)

    if not results:
        print(f"ERROR: Tidak ada QR code ditemukan di {image_path}")
        sys.exit(1)

    payload = results[0].data.decode("utf-8")
    parsed = parse_payload(payload)

    if verbose:
        # Determine provider
        tag26 = parsed.get("provider_account_info", {})
        gui = ""
        if isinstance(tag26, dict):
            gui = tag26.get("sub", {}).get("00", "")
        provider = detect_provider(gui)

        nmid = ""
        tag51 = parsed.get("merchant_account_info", {})
        if isinstance(tag51, dict):
            nmid = tag51.get("sub", {}).get("02", "")

        print(f"Payload ({len(payload)} chars):")
        print(f"  {payload}\n")
        print("Parsed:")
        print(f"  Tipe       : {parsed.get('initiation_type', '?')}")
        print(f"  Provider   : {provider}")
        print(f"  GUI        : {gui}")
        print(f"  NMID       : {nmid}")
        print(f"  Merchant   : {parsed.get('merchant_name', '?')}")
        print(f"  MCC        : {parsed.get('mcc', '?')}")
        print(f"  Amount     : Rp{parsed.get('amount', '-')}")
        print(f"  Currency   : {parsed.get('currency_code', '?')} ({parsed.get('currency', '?')})")
        print(f"  Country    : {parsed.get('country', '?')}")
        print(f"  City       : {parsed.get('merchant_city', '?')}")
        print(f"  Postal     : {parsed.get('postal_code', '?')}")
        print(f"  CRC Valid  : {verify_crc(payload)}")

    return parsed


# ──────────────────────────────────────────────
#  SETUP WIZARD
# ──────────────────────────────────────────────

def setup_wizard():
    """Interactive setup: decode QRIS image → save as profile."""
    print("=" * 50)
    print("  QRIS Generator — Setup Wizard")
    print("=" * 50)
    print()
    print("Siapkan QRIS QR code merchant Anda.")
    print("Bisa dari: screenshot QRIS statis, foto QR code, atau file gambar.")
    print()
    print("Cara mendapatkan QRIS:")
    print("  1. Buka aplikasi bank/e-wallet (DANA, GoPay, BCA, dll)")
    print("  2. Buka menu 'Terima Pembayaran' / 'QRIS Merchant'")
    print("  3. Screenshot QRIS code yang muncul")
    print("  4. Simpan sebagai file gambar (PNG/JPG)")
    print()

    # Step 1: Get image path
    while True:
        image_path = input("Path gambar QRIS: ").strip().strip('"').strip("'")
        if not image_path:
            print("ERROR: Masukkan path gambar QRIS.")
            continue
        if not Path(image_path).exists():
            print(f"ERROR: File tidak ditemukan: {image_path}")
            continue
        break

    # Step 2: Decode
    print(f"\nMembaca QR code dari {image_path}...")
    parsed = decode_qris_image(image_path, verbose=True)
    profile = extract_profile_from_parsed(parsed)

    # Validate
    if not profile.get("tag26_raw"):
        print("\nERROR: Tag 26 (provider account info) tidak ditemukan!")
        print("Pastikan gambar berisi QR code QRIS yang valid.")
        sys.exit(1)

    # Step 3: Show extracted data
    print("\n" + "=" * 50)
    print("  Data yang diekstrak:")
    print("=" * 50)
    print_profile(profile)

    # Step 4: Confirm & name profile
    print()
    while True:
        name = input("Nama profile (contoh: 'warung', 'toko', 'nama_anda'): ").strip()
        if not name:
            print("ERROR: Nama profile tidak boleh kosong.")
            continue
        if " " in name:
            print("ERROR: Nama profile tidak boleh ada spasi. Gunakan underscore (_) jika perlu.")
            continue
        break

    # Step 5: Check existing & save
    cfg = load_config()
    if name in cfg.get("profiles", {}):
        overwrite = input(f"Profile '{name}' sudah ada. Timpa? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Dibatalkan.")
            return

    make_default = False
    if cfg.get("profiles"):
        set_default = input(f"Jadikan '{name}' sebagai default? (Y/n): ").strip().lower()
        make_default = set_default != "n"
    else:
        make_default = True

    cfg = save_profile(cfg, name, profile, make_default=make_default)
    save_config(cfg)

    print(f"\n✓ Profile '{name}' berhasil disimpan!")
    print(f"  Config: {config_path()}")
    print(f"\nUntuk generate QRIS:")
    print(f"  python generate.py 25000              # default profile")
    print(f"  python generate.py --profile {name} 25000  # profile spesifik")


# ──────────────────────────────────────────────
#  GENERATE
# ──────────────────────────────────────────────

def generate_qris(amounts: list[int], profile: dict, profile_name: str = "", output_dir: str = "output"):
    """Generate QRIS images for given amounts using a profile."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    merchant_name = profile.get("merchant_name", "Merchant")
    nmid = profile.get("tag51_sub", {}).get("02", "")
    provider = profile.get("provider", "")

    print(f"QRIS Generator v2.0.0")
    print(f"Profile  : {profile_name or '(default)'}")
    print(f"Merchant : {merchant_name}")
    if nmid:
        print(f"NMID     : {nmid}")
    print(f"Provider : {provider}")
    print(f"Output   : {out.resolve()}")
    print()

    for amount in amounts:
        payload = build_qris_payload(
            amount=amount,
            tag26_raw=profile.get("tag26_raw", ""),
            tag51_raw=profile.get("tag51_raw", ""),
            merchant_name=merchant_name,
            mcc=profile.get("mcc", "7372"),
            currency=profile.get("currency", "360"),
            country=profile.get("country", "ID"),
            city=profile.get("city", ""),
            postal_code=profile.get("postal_code", ""),
            additional_raw=profile.get("additional_raw", ""),
            dynamic=True,
        )

        crc_ok = verify_crc(payload)

        path = render_batch(
            payload=payload,
            amount=amount,
            merchant_name=merchant_name,
            nmid=nmid,
            provider=provider,
            output_dir=str(out),
        )

        print(f"  Rp{amount:>10,}  →  {Path(path).name}  (CRC: {'OK' if crc_ok else 'FAIL'})")

        # Verify
        parsed = parse_payload(payload)
        assert parsed.get("amount") == str(amount), f"Amount mismatch: {parsed.get('amount')} != {amount}"

    print(f"\nSelesai! {len(amounts)} QRIS di-generate di {out.resolve()}")


# ──────────────────────────────────────────────
#  LIST / DELETE / SET-DEFAULT
# ──────────────────────────────────────────────

def list_profiles():
    """List all saved profiles."""
    cfg = load_config()
    profiles = cfg.get("profiles", {})
    default = cfg.get("default_profile")

    if not profiles:
        print("Belum ada profile tersimpan.")
        print(f"Jalankan: python generate.py setup")
        return

    print(f"Config: {config_path()}")
    print(f"{'=' * 40}")
    for name, data in profiles.items():
        marker = " ★" if name == default else ""
        provider = data.get("provider", "?")
        merchant = data.get("merchant_name", "?")
        nmid = data.get("tag51_sub", {}).get("02", "")
        print(f"  {name}{marker}")
        print(f"    Provider : {provider}")
        print(f"    Merchant : {merchant}")
        if nmid:
            print(f"    NMID     : {nmid}")
        print()
    print(f"★ = default profile")


def cmd_delete_profile(name: str):
    """Delete a profile."""
    cfg = load_config()
    confirm = input(f"Hapus profile '{name}'? (y/N): ").strip().lower()
    if confirm != "y":
        print("Dibatalkan.")
        return
    cfg = delete_profile(cfg, name)
    save_config(cfg)
    print(f"✓ Profile '{name}' dihapus.")


def cmd_set_default(name: str):
    """Set default profile."""
    cfg = load_config()
    if name not in cfg.get("profiles", {}):
        print(f"ERROR: Profile '{name}' tidak ditemukan.")
        sys.exit(1)
    cfg["default_profile"] = name
    save_config(cfg)
    print(f"✓ Default profile: {name}")


# ──────────────────────────────────────────────
#  SHOW PROFILE
# ──────────────────────────────────────────────

def cmd_show_profile(name: str | None):
    """Show details of a profile."""
    cfg = load_config()
    profile = get_profile(cfg, name)
    display_name = name or cfg.get("default_profile", "")
    print("=" * 50)
    print("  Detail Profile")
    print("=" * 50)
    print_profile(profile, display_name)
    # Show raw payloads
    print()
    print("Raw Tag 26:")
    print(f"  {profile.get('tag26_raw', '-')}")
    print("Raw Tag 51:")
    print(f"  {profile.get('tag51_raw', '-')}")
    if profile.get("source_payload"):
        print(f"\nPayload asli ({len(profile['source_payload'])} chars):")
        print(f"  {profile['source_payload']}")


# ──────────────────────────────────────────────
#  PAYLOAD-ONLY MODE
# ──────────────────────────────────────────────

def show_payload_only(amounts: list[int], profile: dict):
    """Print raw payloads without generating images."""
    for amount in amounts:
        payload = build_qris_payload(
            amount=amount,
            tag26_raw=profile.get("tag26_raw", ""),
            tag51_raw=profile.get("tag51_raw", ""),
            merchant_name=profile.get("merchant_name", ""),
            mcc=profile.get("mcc", "7372"),
            currency=profile.get("currency", "360"),
            country=profile.get("country", "ID"),
            city=profile.get("city", ""),
            postal_code=profile.get("postal_code", ""),
            additional_raw=profile.get("additional_raw", ""),
            dynamic=True,
        )
        print(f"Rp{amount:,}: {payload}")
        print(f"  CRC OK: {verify_crc(payload)}")


# ──────────────────────────────────────────────
#  MAIN CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="QRIS Generator — Generate QRIS QR codes untuk nominal apapun",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python generate.py setup                    Setup wizard
  python generate.py 5000                     Single QR
  python generate.py 1000 5000 10000 50000    Batch
  python generate.py --decode qris.png        Decode QRIS image
  python generate.py --list                   List profiles
  python generate.py --profile warung 25000   Use specific profile
  python generate.py --show                   Show default profile
  python generate.py --show warung            Show specific profile
  python generate.py --delete warung          Delete profile
  python generate.py --set-default warung     Set default profile
  python generate.py --payload 5000           Show raw payload only
        """,
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Amount(s) dalam IDR, atau 'setup' untuk wizard",
    )
    parser.add_argument(
        "-d", "--decode",
        type=str,
        metavar="IMAGE",
        help="Decode QRIS dari file gambar",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory (default: output/)",
    )
    parser.add_argument(
        "-p", "--payload",
        action="store_true",
        help="Tampilkan raw payload saja (tanpa gambar)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_profiles",
        help="List semua merchant profiles",
    )
    parser.add_argument(
        "--profile",
        type=str,
        metavar="NAME",
        help="Gunakan profile spesifik",
    )
    parser.add_argument(
        "--show",
        nargs="?",
        const="__DEFAULT__",
        metavar="NAME",
        help="Tampilkan detail profile",
    )
    parser.add_argument(
        "--delete",
        type=str,
        metavar="NAME",
        help="Hapus profile",
    )
    parser.add_argument(
        "--set-default",
        type=str,
        metavar="NAME",
        help="Set default profile",
    )

    args = parser.parse_args()

    # --- Commands that don't need profile ---

    if args.list_profiles:
        list_profiles()
        return

    if args.delete:
        cmd_delete_profile(args.delete)
        return

    if args.set_default:
        cmd_set_default(args.set_default)
        return

    if args.show is not None:
        name = args.show if args.show != "__DEFAULT__" else None
        cmd_show_profile(name)
        return

    if args.decode:
        decoded = decode_qris_image(args.decode)
        # Ask if user wants to save as profile
        cfg = load_config()
        tag26 = decoded.get("provider_account_info", {})
        gui = ""
        if isinstance(tag26, dict):
            gui = tag26.get("sub", {}).get("00", "")
        if gui:
            save_as = input("\nSimpan sebagai profile? (ketik nama atau Enter untuk skip): ").strip()
            if save_as:
                profile = extract_profile_from_parsed(decoded)
                cfg = save_profile(cfg, save_as, profile)
                save_config(cfg)
                print(f"✓ Profile '{save_as}' tersimpan.")
        return

    # --- Setup ---
    if not args.args:
        parser.print_help()
        print("\nERROR: Masukkan nominal atau jalankan 'setup'.")
        sys.exit(1)

    if args.args[0].lower() == "setup":
        setup_wizard()
        return

    # --- Generate mode ---

    # Parse amounts
    amounts = []
    for a in args.args:
        try:
            amounts.append(int(a))
        except ValueError:
            print(f"ERROR: '{a}' bukan angka yang valid.")
            sys.exit(1)

    if not amounts:
        print("ERROR: Masukkan minimal satu nominal.")
        sys.exit(1)

    # Load profile
    cfg = load_config()
    profile = get_profile(cfg, args.profile)

    if args.payload:
        show_payload_only(amounts, profile)
    else:
        profile_name = args.profile or cfg.get("default_profile", "")
        generate_qris(amounts, profile, profile_name, args.output)


if __name__ == "__main__":
    main()
