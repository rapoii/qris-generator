"""
QRIS Generator — Config & Profile Management.

Stores merchant profiles in ~/.qris_generator/config.json
Each profile holds raw parsed data from a decoded QRIS image.
"""

import json
import sys
from pathlib import Path
from typing import Any

# --- Provider GUI detection ---

PROVIDER_MAP: dict[str, str] = {
    # E-Wallet
    "ID.DANA.WWW": "DANA",
    "ID.CO.GRABWALKING.WWW": "GrabPay/GoPay",
    "ID.CO.GOPAY.WWW": "GoPay",
    "ID.CO.GRAB.WWW": "GrabPay",
    "ID.CO.SHOOPEE.WWW": "ShopeePay",
    "ID.CO.SHOOPEEPAY.WWW": "ShopeePay",
    "ID.CO.OCBC.NISP": "OVO",
    "ID.CO.OVO.WWW": "OVO",
    "ID.CO.LINKAJA.WWW": "LinkAja",
    "ID.CO.DOKU.WWW": "DOKU",
    "ID.CO.JENIUS.WWW": "Jenius",
    "ID.CO.ISAKU.WWW": "iSaku",
    "ID.CO.MANDIRI.WWW": "Mandiri",
    "ID.CO.BCA.WWW": "BCA",
    "ID.CO.BRI.WWW": "BRI",
    "ID.CO.BNI.WWW": "BNI",
    "ID.CO.BSI.WWW": "BSI",
    "ID.CO.CIMBNIAGA.WWW": "CIMB Niaga",
    "ID.CO.BANKMUAMALAT.WWW": "Muamalat",
    "ID.CO.PERMATA.WWW": "Permata",
    "ID.CO.BANKDKI.WWW": "DKI",
    "ID.CO.MAYBANK.WWW": "Maybank",
    "ID.CO.BTPN.WWW": "BTPN",
    "ID.CO.PANIN.WWW": "Panin",
    "ID.CO.MEGA.WWW": "Mega",
    "ID.CO.BUKOPIN.WWW": "Bukopin",
    "ID.CO.SINARMAS.WWW": "Sinarmas",
    "ID.CO.BANKDANAMON.WWW": "Danamon",
    "ID.CO.NOBUBANK.WWW": "Nobu Bank",
    "ID.CO.BANKBTN.WWW": "BTN",
    "ID.CO.QRIS.WWW": "QRIS (Nasional)",
}

# --- Paths ---

def config_dir() -> Path:
    return Path.home() / ".qris_generator"

def config_path() -> Path:
    return config_dir() / "config.json"


# --- Config I/O ---

def load_config() -> dict:
    """Load config from disk. Returns empty structure if not found."""
    p = config_path()
    if not p.exists():
        return {"default_profile": None, "profiles": {}}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    """Save config to disk."""
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(config_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# --- Profile management ---

def get_profile(cfg: dict, name: str | None = None) -> dict:
    """Get a profile by name, or default profile. Raises if not found."""
    profiles = cfg.get("profiles", {})
    if not profiles:
        print("ERROR: Belum ada profile. Jalankan: python generate.py setup")
        sys.exit(1)

    if name:
        if name not in profiles:
            avail = ", ".join(profiles.keys())
            print(f"ERROR: Profile '{name}' tidak ditemukan.")
            print(f"Profile tersedia: {avail}")
            sys.exit(1)
        return profiles[name]

    # Use default
    default = cfg.get("default_profile")
    if default and default in profiles:
        return profiles[default]

    # Only one profile? Use it.
    if len(profiles) == 1:
        return next(iter(profiles.values()))

    print("ERROR: Ada beberapa profile. Pilih dengan --profile <nama>")
    for pname in profiles:
        print(f"  - {pname}")
    sys.exit(1)


def save_profile(cfg: dict, name: str, data: dict, make_default: bool = False) -> dict:
    """Save a merchant profile. Returns updated config."""
    cfg.setdefault("profiles", {})[name] = data
    if make_default or cfg.get("default_profile") is None:
        cfg["default_profile"] = name
    return cfg


def delete_profile(cfg: dict, name: str) -> dict:
    """Delete a profile. Returns updated config."""
    profiles = cfg.get("profiles", {})
    if name not in profiles:
        print(f"ERROR: Profile '{name}' tidak ditemukan.")
        sys.exit(1)
    del profiles[name]
    if cfg.get("default_profile") == name:
        cfg["default_profile"] = next(iter(profiles), None)
    return cfg


# --- Provider detection ---

def detect_provider(gui: str) -> str:
    """Detect provider name from GUI string."""
    # Exact match first
    if gui in PROVIDER_MAP:
        return PROVIDER_MAP[gui]
    # Prefix match
    for key, name in PROVIDER_MAP.items():
        if gui.startswith(key.rsplit(".", 1)[0]):
            return name
    return f"Unknown ({gui})"


def extract_profile_from_parsed(parsed: dict) -> dict:
    """
    Extract profile data from a parse_payload() result.
    Stores raw Tag 26/51 sub-tags so we can reconstruct any provider.
    """
    tag26 = parsed.get("provider_account_info", {})
    tag51 = parsed.get("merchant_account_info", {})
    # Handle legacy key names from v1
    if "dana_account_info" in parsed:
        tag26 = parsed["dana_account_info"]
    if "qris_merchant_info" in parsed:
        tag51 = parsed["qris_merchant_info"]

    # Detect provider from Tag 26 sub-tag 00 (GUI)
    gui = ""
    if isinstance(tag26, dict):
        gui = tag26.get("sub", {}).get("00", "")

    profile = {
        "provider": detect_provider(gui),
        "gui": gui,
        "tag26_raw": tag26.get("raw", ""),
        "tag51_raw": tag51.get("raw", ""),
        "tag26_sub": tag26.get("sub", {}),
        "tag51_sub": tag51.get("sub", {}),
        "merchant_name": parsed.get("merchant_name", ""),
        "nmid": tag51.get("sub", {}).get("02", ""),
        "mcc": parsed.get("mcc", ""),
        "currency": parsed.get("currency", "360"),
        "country": parsed.get("country", "ID"),
        "city": parsed.get("merchant_city", ""),
        "postal_code": parsed.get("postal_code", ""),
        "initiation_type": parsed.get("initiation_type", "Dynamic"),
        "additional_raw": parsed.get("additional_data", {}).get("raw", "") if isinstance(parsed.get("additional_data"), dict) else "",
        # Store full parsed for future reference
        "source_payload": parsed.get("_raw_payload", ""),
    }
    return profile


def print_profile(profile: dict, name: str = "") -> None:
    """Pretty-print a merchant profile."""
    if name:
        print(f"  Profile    : {name}")
    print(f"  Provider   : {profile.get('provider', '?')}")
    print(f"  GUI        : {profile.get('gui', '?')}")
    print(f"  Merchant   : {profile.get('merchant_name', '?')}")
    print(f"  NMID       : {profile.get('nmid', '?')}")
    print(f"  MCC        : {profile.get('mcc', '?')}")
    print(f"  City       : {profile.get('city', '?')}")
    print(f"  Postal     : {profile.get('postal_code', '?')}")
    print(f"  Currency   : {profile.get('currency', '?')}")
    print(f"  Country    : {profile.get('country', '?')}")
    print(f"  Tag26 Raw  : {profile.get('tag26_raw', '?')[:80]}...")
    print(f"  Tag51 Raw  : {profile.get('tag51_raw', '?')[:80]}...")
