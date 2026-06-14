"""
QRIS QR Code Image Renderer.

Generates styled QR images matching the standard QRIS display format:
- Merchant name at top
- Amount below
- QRIS logo
- QR code with red accent bars
- Provider + NMID at bottom
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise ImportError("Pillow required: pip install pillow")

try:
    import qrcode
except ImportError:
    raise ImportError("qrcode required: pip install qrcode")


# QRIS brand colors
RED_ACCENT = (220, 38, 38)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (80, 80, 80)


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a clean font, fallback to default."""
    font_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _get_font_bold(size: int) -> ImageFont.FreeTypeFont:
    """Try to load bold variant."""
    bold_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/tahomabd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in bold_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return _get_font(size)


def render_qris(
    payload: str,
    amount: int,
    merchant_name: str,
    nmid: str = "",
    provider: str = "",
    output_path: str | None = None,
    qr_size: int = 400,
) -> Image.Image:
    """
    Generate QRIS-styled QR code image.

    Args:
        payload: Raw QRIS payload string
        amount: Amount in IDR (for display)
        merchant_name: Merchant display name
        nmid: National Merchant ID (optional)
        provider: Provider name (optional, displayed at bottom)
        output_path: If set, save PNG to this path
        qr_size: QR code pixel size

    Returns:
        PIL Image object
    """
    # Generate QR code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    # Layout constants
    padding = 30
    text_area_top = 50
    qr_y_start = 160
    bottom_text_y = qr_y_start + qr_size + 25
    total_height = bottom_text_y + 80
    total_width = qr_size + padding * 2

    # Create canvas
    canvas = Image.new("RGB", (total_width, total_height), WHITE)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_name = _get_font_bold(22)
    font_amount = _get_font_bold(28)
    font_qris = _get_font_bold(18)
    font_nmid = _get_font(13)
    font_provider = _get_font(12)

    center_x = total_width // 2

    # --- Merchant Name ---
    name_bbox = draw.textbbox((0, 0), merchant_name, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text(
        (center_x - name_w // 2, text_area_top),
        merchant_name,
        fill=BLACK,
        font=font_name,
    )

    # --- Amount ---
    amount_str = f"Rp{amount:,.0f}".replace(",", ".")
    amt_bbox = draw.textbbox((0, 0), amount_str, font=font_amount)
    amt_w = amt_bbox[2] - amt_bbox[0]
    draw.text(
        (center_x - amt_w // 2, text_area_top + 35),
        amount_str,
        fill=BLACK,
        font=font_amount,
    )

    # --- QRIS label ---
    qris_text = "\u300cQRIS\u300d"
    qris_bbox = draw.textbbox((0, 0), qris_text, font=font_qris)
    qris_w = qris_bbox[2] - qris_bbox[0]
    draw.text(
        (center_x - qris_w // 2, text_area_top + 75),
        qris_text,
        fill=BLACK,
        font=font_qris,
    )

    # --- QR Code ---
    qr_x = center_x - qr_size // 2
    canvas.paste(qr_img, (qr_x, qr_y_start))

    # --- Red accent bars ---
    bar_width = 8
    draw.rectangle(
        [qr_x - bar_width, qr_y_start, qr_x - 1, qr_y_start + qr_size],
        fill=RED_ACCENT,
    )
    br_x = qr_x + qr_size
    br_y = qr_y_start + qr_size
    draw.rectangle(
        [qr_x + qr_size // 2, br_y, br_x + bar_width, br_y + bar_width],
        fill=RED_ACCENT,
    )
    draw.rectangle(
        [br_x, qr_y_start + qr_size // 2, br_x + bar_width, br_y + bar_width],
        fill=RED_ACCENT,
    )

    # --- Provider (new) ---
    if provider:
        prov_text = provider
        prov_bbox = draw.textbbox((0, 0), prov_text, font=font_provider)
        prov_w = prov_bbox[2] - prov_bbox[0]
        draw.text(
            (center_x - prov_w // 2, bottom_text_y),
            prov_text,
            fill=GRAY,
            font=font_provider,
        )
        nmid_y_offset = bottom_text_y + 18
    else:
        nmid_y_offset = bottom_text_y

    # --- NMID ---
    if nmid:
        nmid_text = f"NMID : {nmid}"
        nmid_bbox = draw.textbbox((0, 0), nmid_text, font=font_nmid)
        nmid_w = nmid_bbox[2] - nmid_bbox[0]
        draw.text(
            (center_x - nmid_w // 2, nmid_y_offset),
            nmid_text,
            fill=GRAY,
            font=font_nmid,
        )

    if output_path:
        canvas.save(output_path, "PNG", quality=95)

    return canvas


def render_batch(
    payload: str,
    amount: int,
    merchant_name: str,
    nmid: str = "",
    provider: str = "",
    output_dir: str = ".",
    filename_prefix: str = "qris",
) -> str:
    """Generate and save QRIS image with auto-naming. Returns path."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    amount_str = f"{amount:,}".replace(",", ".")
    filename = f"{filename_prefix}_Rp{amount_str}.png"
    output_path = out_dir / filename

    render_qris(payload, amount, merchant_name, nmid, provider, str(output_path))
    return str(output_path)
