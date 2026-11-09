"""Generación de etiquetas (código de barras Code128 y QR) para pacas.

Todo se genera en el servidor y se entrega como ``data:image/svg+xml`` para que
la impresión funcione incluso sin conexión a internet.
"""

import base64
import io
from urllib.parse import urljoin

import qrcode
import qrcode.image.svg
from barcode import Code128
from barcode.writer import SVGWriter
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


def _a_data_uri(svg):
    if isinstance(svg, str):
        svg = svg.encode("utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode("ascii")


def generar_barcode_svg(codigo):
    """Código de barras Code128 (soporta letras y números)."""
    generador = Code128(codigo, writer=SVGWriter())
    svg = generador.render(
        {
            "module_width": 0.28,
            "module_height": 11.0,
            "font_size": 7,
            "text_distance": 2.0,
            "quiet_zone": 1.5,
            "write_text": False,
            "background": "white",
            "foreground": "black",
        }
    )
    return svg


def generar_qr_svg(texto):
    """Código QR con la nota de trazabilidad de la paca."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(texto)
    qr.make(fit=True)

    imagen = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buffer = io.BytesIO()
    imagen.save(buffer)
    return buffer.getvalue()


def preparar_etiquetas(pacas, base_url=None):
    """Adjunta a cada paca las imágenes listas para la plantilla.

    El QR contiene una nota legible con el detalle de la paca y, si se recibe
    ``base_url``, también el enlace a su ficha pública.
    """
    base_url = settings.SITE_URL or base_url
    for paca in pacas:
        url_ficha = None
        if base_url:
            ruta = reverse("ficha_paca_corta", args=[paca.codigo_unico])
            url_ficha = urljoin(base_url.rstrip("/") + "/", ruta.lstrip("/"))
        qr_texto = _texto_qr(paca, url_ficha)
        paca.barcode_data_uri = _a_data_uri(generar_barcode_svg(paca.codigo_unico))
        paca.qr_data_uri = _a_data_uri(generar_qr_svg(qr_texto))
    return pacas


def _texto_qr(paca, url_ficha=None):
    """Nota legible que muestra el lector de QR antes de abrir la ficha web."""
    elaborado = timezone.localtime(paca.fecha_creacion)
    lineas = [
        "VELPACK S.A.",
        paca.codigo_unico,
        f"{paca.detalle.producto.nombre} / {paca.detalle.color.nombre}",
        f"Lote {paca.lote} - Paca #{paca.numero_paca}",
        f"Elaborado: {elaborado:%d/%m/%Y %H:%M}",
        f"Operador: {paca.detalle.produccion.operador.nombre_completo}",
    ]
    if url_ficha:
        lineas.append(f"Ficha: {url_ficha}")
    return "\n".join(lineas)
