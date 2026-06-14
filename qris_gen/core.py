"""
QRIS EMVCo MPM TLV Builder + CRC-16/CCITT-FALSE Calculator.

Constructs valid QRIS payloads from merchant data and amount.
"""

import struct


def crc16_ccitt_false(data: str) -> str:
    """
    Calculate CRC-16/CCITT-FALSE checksum.
    
    Used by EMVCo QR spec for payload validation.
    Polynomial: 0x1021, Init: 0xFFFF, No final XOR.
    
    Args:
        data: Payload string (everything before CRC tag)
    
    Returns:
        4-char uppercase hex string
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
    return format(crc, '04X')


def tlv(tag: str, value: str) -> str:
    """Build single TLV entry: tag (2 chars) + length (2 chars, zero-padded) + value."""
    return f"{tag}{len(value):02d}{value}"


def sub_tlv(entries: list[tuple[str, str]]) -> str:
    """Build concatenated sub-TLV entries. Each entry is (tag, value)."""
    return "".join(tlv(tag, val) for tag, val in entries)


def build_qris_payload(
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
    """
    Build complete QRIS EMVCo MPM payload string.
    
    Args:
        amount: Transaction amount in IDR (e.g. 15000 for Rp15.000)
        nmid: National Merchant ID (e.g. "ID1025460925684")
        merchant_name: Display name (max 25 chars recommended)
        dana_account: DANA account number
        dana_sub_account: DANA sub-account identifier
        category: UMI category code
        mcc: Merchant Category Code (4 digits)
        currency: ISO 4217 numeric code ("360" = IDR)
        country: ISO 3166-1 alpha-2 ("ID")
        city: City code
        postal_code: Postal/ZIP code
        dynamic: True = Dynamic (Tag 01=12, amount embedded), False = Static (Tag 01=11)
    
    Returns:
        Complete QRIS payload string ready for QR encoding
    """
    # Format amount (remove decimals if whole number)
    if isinstance(amount, float) and amount == int(amount):
        amount_str = str(int(amount))
    elif isinstance(amount, float):
        amount_str = f"{amount:.2f}"
    else:
        amount_str = str(int(amount))
    
    # --- Tag 26: DANA Account Info ---
    dana_info = sub_tlv([
        ("00", "ID.DANA.WWW"),        # GUI (Global Unique Identifier)
        ("01", dana_account),          # DANA account number
        ("02", dana_sub_account),      # Sub-account
        ("03", category),              # Category
    ])
    
    # --- Tag 51: QRIS National Merchant Info ---
    qris_info = sub_tlv([
        ("00", "ID.CO.QRIS.WWW"),     # QRIS GUI
        ("02", nmid),                  # National Merchant ID
        ("03", category),              # Category
    ])
    
    # --- Tag 62: Additional Data ---
    additional = sub_tlv([
        ("60", sub_tlv([
            ("00", "ID.DANA.WWW"),     # Reference label provider
        ])),
    ])
    
    # --- Assemble main payload ---
    parts = []
    parts.append(tlv("00", "01"))                              # Payload Format Indicator
    parts.append(tlv("01", "12" if dynamic else "11"))         # Point of Initiation Method
    parts.append(tlv("26", dana_info))                         # Merchant Account Info (DANA)
    parts.append(tlv("51", qris_info))                         # Merchant Account Info (QRIS)
    parts.append(tlv("52", mcc))                               # Merchant Category Code
    parts.append(tlv("53", currency))                          # Transaction Currency
    parts.append(tlv("54", amount_str))                        # Transaction Amount
    parts.append(tlv("58", country))                           # Country Code
    parts.append(tlv("59", merchant_name))                     # Merchant Name
    parts.append(tlv("60", city))                              # Merchant City
    parts.append(tlv("61", postal_code))                       # Postal Code
    parts.append(tlv("62", additional))                        # Additional Data
    
    # Concatenate all parts
    payload_no_crc = "".join(parts)
    
    # --- Tag 63: CRC-16/CCITT-FALSE ---
    # CRC covers everything INCLUDING "6304" prefix
    crc_input = payload_no_crc + "6304"
    crc_value = crc16_ccitt_false(crc_input)
    
    return payload_no_crc + "6304" + crc_value


def parse_payload(payload: str) -> dict:
    """
    Parse QRIS EMVCo MPM payload into structured dict.
    
    Args:
        payload: Raw QRIS payload string
    
    Returns:
        Dict with parsed tags and values
    """
    result = {}
    i = 0
    while i < len(payload):
        if i + 4 > len(payload):
            break
        tag = payload[i:i+2]
        try:
            length = int(payload[i+2:i+4])
        except ValueError:
            break
        value = payload[i+4:i+4+length]
        
        # Tag names
        tag_names = {
            "00": "payload_format",
            "01": "initiation_method",
            "26": "dana_account_info",
            "51": "qris_merchant_info",
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
        
        # Parse sub-TLV for nested tags
        if tag in ("26", "51", "62"):
            sub = {}
            j = 0
            while j < len(value):
                if j + 4 > len(value):
                    break
                st = value[j:j+2]
                sl = int(value[j+2:j+4])
                sv = value[j+4:j+4+sl]
                sub[st] = sv
                j += 4 + sl
            result[name] = {"raw": value, "sub": sub}
        else:
            result[name] = value
        
        # Human-readable mappings
        if tag == "01":
            result["initiation_type"] = "Dynamic" if value == "12" else "Static"
        elif tag == "53":
            currencies = {"360": "IDR", "840": "USD"}
            result["currency_code"] = currencies.get(value, value)
        
        i += 4 + length
    
    return result


def verify_crc(payload: str) -> bool:
    """Verify CRC-16 checksum of a QRIS payload."""
    # Find CRC tag position
    crc_pos = payload.find("6304")
    if crc_pos == -1:
        return False
    
    payload_no_crc = payload[:crc_pos]
    crc_stored = payload[crc_pos + 4:]
    crc_calculated = crc16_ccitt_false(payload_no_crc + "6304")
    
    return crc_stored == crc_calculated
