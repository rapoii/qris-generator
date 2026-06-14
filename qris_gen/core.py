"""
QRIS EMVCo MPM TLV Builder + CRC-16/CCITT-FALSE Calculator.

Constructs valid QRIS payloads from merchant data and amount.
Provider-agnostic: reads raw Tag 26/51 sub-tags from config.
"""

from typing import Any


def crc16_ccitt_false(data: str) -> str:
    """
    CRC-16/CCITT-FALSE checksum.
    Polynomial: 0x1021, Init: 0xFFFF, No final XOR.
    """
    crc = 0xFFFF
    for char in data:
        crc ^= (ord(char) << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, "04X")


def tlv(tag: str, value: str) -> str:
    """Build single TLV: tag(2) + length(2, zero-padded) + value."""
    return f"{tag}{len(value):02d}{value}"


def sub_tlv(entries: list[tuple[str, str]]) -> str:
    """Build concatenated sub-TLV entries."""
    return "".join(tlv(tag, val) for tag, val in entries)


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
) -> str:
    """
    Build complete QRIS EMVCo MPM payload.

    Uses RAW Tag 26/51 strings extracted from decoded QRIS.
    This makes it provider-agnostic — works with DANA, GoPay, OVO, BCA, etc.

    Args:
        amount: Transaction amount in IDR
        tag26_raw: Raw Tag 26 string (provider account info, e.g. DANA/GoPay)
        tag51_raw: Raw Tag 51 string (QRIS national merchant info)
        merchant_name: Display name
        mcc: Merchant Category Code
        currency: ISO 4217 numeric code ("360" = IDR)
        country: ISO 3166-1 alpha-2
        city: City code/name
        postal_code: Postal code
        additional_raw: Raw Tag 62 string (additional data)
        dynamic: True = Dynamic QR (amount embedded), False = Static

    Returns:
        Complete QRIS payload string ready for QR encoding
    """
    # Format amount
    if isinstance(amount, float) and amount == int(amount):
        amount_str = str(int(amount))
    elif isinstance(amount, float):
        amount_str = f"{amount:.2f}"
    else:
        amount_str = str(int(amount))

    # --- Assemble main payload ---
    parts = []
    parts.append(tlv("00", "01"))                             # Payload Format Indicator
    parts.append(tlv("01", "12" if dynamic else "11"))        # Point of Initiation Method

    # Tag 26: Provider account info (use raw from decoded QRIS)
    if tag26_raw:
        parts.append(tlv("26", tag26_raw))

    # Tag 51: QRIS national merchant info (use raw from decoded QRIS)
    if tag51_raw:
        parts.append(tlv("51", tag51_raw))

    parts.append(tlv("52", mcc))                              # Merchant Category Code
    parts.append(tlv("53", currency))                         # Transaction Currency
    parts.append(tlv("54", amount_str))                       # Transaction Amount
    parts.append(tlv("58", country))                          # Country Code
    parts.append(tlv("59", merchant_name))                    # Merchant Name
    parts.append(tlv("60", city))                             # Merchant City
    parts.append(tlv("61", postal_code))                      # Postal Code

    # Tag 62: Additional data
    if additional_raw:
        parts.append(tlv("62", additional_raw))

    # Concatenate, compute CRC
    payload_no_crc = "".join(parts)
    crc_input = payload_no_crc + "6304"
    crc_value = crc16_ccitt_false(crc_input)

    return payload_no_crc + "6304" + crc_value


# --- Legacy wrapper for backward compat ---

def build_qris_payload_legacy(
    amount: int | float,
    nmid: str,
    merchant_name: str,
    dana_account: str,
    dana_sub_account: str = "000007725",
    category: str = "UMI",
    mcc: str = "7372",
    currency: str = "360",
    country: str = "ID",
    city: str = "0293",
    postal_code: str = "42125",
    dynamic: bool = True,
) -> str:
    """Legacy DANA-only builder. For backward compat only."""
    tag26 = sub_tlv([
        ("00", "ID.DANA.WWW"),
        ("01", dana_account),
        ("02", dana_sub_account),
        ("03", category),
    ])
    tag51 = sub_tlv([
        ("00", "ID.CO.QRIS.WWW"),
        ("02", nmid),
        ("03", category),
    ])
    tag62 = sub_tlv([
        ("60", sub_tlv([("00", "ID.DANA.WWW")])),
    ])
    return build_qris_payload(
        amount=amount,
        tag26_raw=tag26,
        tag51_raw=tag51,
        merchant_name=merchant_name,
        mcc=mcc,
        currency=currency,
        country=country,
        city=city,
        postal_code=postal_code,
        additional_raw=tag62,
        dynamic=dynamic,
    )


# --- Parsing ---

def parse_payload(payload: str) -> dict:
    """
    Parse QRIS EMVCo MPM payload into structured dict.

    Returns dict with parsed tags. Nested tags (26, 51, 62) have
    {"raw": str, "sub": {tag: value}} structure.
    """
    result: dict[str, Any] = {}
    i = 0
    while i < len(payload):
        if i + 4 > len(payload):
            break
        tag = payload[i : i + 2]
        try:
            length = int(payload[i + 2 : i + 4])
        except ValueError:
            break
        value = payload[i + 4 : i + 4 + length]

        tag_names = {
            "00": "payload_format",
            "01": "initiation_method",
            "26": "provider_account_info",
            "51": "merchant_account_info",
            "52": "mcc",
            "53": "currency",
            "54": "amount",
            "58": "country",
            "59": "merchant_name",
            "60": "merchant_city",
            "61": "postal_code",
            "62": "additional_data",
            "63": "crc",
        }
        name = tag_names.get(tag, f"tag_{tag}")

        if tag in ("26", "51", "62"):
            sub: dict[str, str] = {}
            j = 0
            while j < len(value):
                if j + 4 > len(value):
                    break
                st = value[j : j + 2]
                sl = int(value[j + 2 : j + 4])
                sv = value[j + 4 : j + 4 + sl]
                sub[st] = sv
                j += 4 + sl
            result[name] = {"raw": value, "sub": sub}
        else:
            result[name] = value

        if tag == "01":
            result["initiation_type"] = "Dynamic" if value == "12" else "Static"
        elif tag == "53":
            currencies = {"360": "IDR", "840": "USD"}
            result["currency_code"] = currencies.get(value, value)

        i += 4 + length

    # Keep raw payload for later use
    result["_raw_payload"] = payload
    return result


def verify_crc(payload: str) -> bool:
    """Verify CRC-16 checksum of a QRIS payload."""
    crc_pos = payload.find("6304")
    if crc_pos == -1:
        return False
    payload_no_crc = payload[:crc_pos]
    crc_stored = payload[crc_pos + 4 :]
    crc_calculated = crc16_ccitt_false(payload_no_crc + "6304")
    return crc_stored == crc_calculated
