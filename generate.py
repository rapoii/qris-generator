"""
QRIS Generator CLI.

Usage:
    python generate.py <amount>              Generate QRIS for amount
    python generate.py 15000                 → output/qris_Rp15.000.png
    python generate.py 5000 10000 50000      Batch generate multiple amounts
    python generate.py --decode <image>      Decode existing QRIS QR image
"""

import argparse
import sys
from pathlib import Path

# Fix sys.path: remove hermes venv to avoid broken PIL import
sys.path = [p for p in sys.path if "hermes" not in p.lower()]

from qris_gen.core import build_qris_payload, parse_payload, verify_crc
from qris_gen.renderer import render_qris, render_batch


# Default merchant config (from decoded rapoi QRIS)
DEFAULT_MERCHANT = {
    "nmid": "ID1025460925684",
    "merchant_name": "rapoi",
    "dana_account": "936009150000077253",
    "dana_sub_account": "000077253",
    "category": "UMI",
    "mcc": "7372",
    "currency": "360",
    "country": "ID",
    "city": "0293",
    "postal_code": "42125",
}


def decode_qris_image(image_path: str) -> dict:
    """Decode QRIS from image file."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode
    except ImportError:
        print("Install: pip install pyzbar pillow")
        sys.exit(1)
    
    img = Image.open(image_path)
    results = zbar_decode(img)
    
    if not results:
        print(f"ERROR: No QR code found in {image_path}")
        sys.exit(1)
    
    payload = results[0].data.decode("utf-8")
    parsed = parse_payload(payload)
    
    # Pretty print
    print(f"Payload ({len(payload)} chars):")
    print(f"  {payload}\n")
    
    print("Parsed:")
    print(f"  Type       : {parsed.get('initiation_type', '?')}")
    print(f"  Provider   : {parsed.get('dana_account_info', {}).get('sub', {}).get('00', '?')}")
    print(f"  NMID       : {parsed.get('qris_merchant_info', {}).get('sub', {}).get('02', '?')}")
    print(f"  Merchant   : {parsed.get('merchant_name', '?')}")
    print(f"  Amount     : Rp{parsed.get('amount', '?')}")
    print(f"  Currency   : {parsed.get('currency_code', '?')} ({parsed.get('currency', '?')})")
    print(f"  Country    : {parsed.get('country', '?')}")
    print(f"  City       : {parsed.get('merchant_city', '?')}")
    print(f"  Postal     : {parsed.get('postal_code', '?')}")
    print(f"  MCC        : {parsed.get('mcc', '?')}")
    print(f"  CRC Valid  : {verify_crc(payload)}")
    
    return parsed


def generate_qris(amounts: list[int], output_dir: str = "output", show: bool = False):
    """Generate QRIS images for given amounts."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    print(f"QRIS Generator v1.0.0")
    print(f"Merchant : {DEFAULT_MERCHANT['merchant_name']}")
    print(f"NMID     : {DEFAULT_MERCHANT['nmid']}")
    print(f"Provider : DANA ({DEFAULT_MERCHANT['dana_account']})")
    print(f"Output   : {out.resolve()}")
    print()
    
    for amount in amounts:
        # Build payload
        payload = build_qris_payload(amount=amount, **DEFAULT_MERCHANT)
        
        # Verify CRC
        crc_ok = verify_crc(payload)
        
        # Generate image
        path = render_batch(
            payload=payload,
            amount=amount,
            merchant_name=DEFAULT_MERCHANT["merchant_name"],
            nmid=DEFAULT_MERCHANT["nmid"],
            output_dir=str(out),
        )
        
        print(f"  Rp{amount:>10,}  →  {Path(path).name}  (CRC: {'OK' if crc_ok else 'FAIL'})")
        
        # Re-verify by re-parsing
        parsed = parse_payload(payload)
        assert parsed.get("amount") == str(amount), f"Amount mismatch: {parsed.get('amount')} != {amount}"
    
    print(f"\nDone! {len(amounts)} QRIS generated in {out.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="QRIS Generator - Generate QRIS QR codes with any nominal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py 5000                    Single QR
  python generate.py 1000 5000 10000 50000   Batch generate
  python generate.py --decode qris.png        Decode QRIS image
  python generate.py --payload 5000           Show raw payload only
        """,
    )
    parser.add_argument(
        "amounts",
        nargs="*",
        type=int,
        help="Amount(s) in IDR (e.g., 5000 10000 50000)",
    )
    parser.add_argument(
        "-d", "--decode",
        type=str,
        metavar="IMAGE",
        help="Decode QRIS from image file",
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
        help="Show raw payload only (no image)",
    )
    
    args = parser.parse_args()
    
    if args.decode:
        decode_qris_image(args.decode)
        return
    
    if not args.amounts:
        parser.print_help()
        print("\nError: Provide at least one amount")
        sys.exit(1)
    
    if args.payload:
        for amount in args.amounts:
            p = build_qris_payload(amount=amount, **DEFAULT_MERCHANT)
            print(f"Rp{amount:,}: {p}")
            print(f"  CRC OK: {verify_crc(p)}")
        return
    
    generate_qris(args.amounts, args.output)


if __name__ == "__main__":
    main()
