"""Generación de archivos PDF con las etiquetas de las pacas."""

import io
import uuid

import qrcode
from qrcode.image.pil import PilImage
from barcode import Code128
from barcode.writer import ImageWriter
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .labels import _texto_qr
from .models import ArchivoEtiquetas


def _reader(imagen):
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def _url_ficha(paca, base_url=None):
    from django.urls import reverse
    from urllib.parse import urljoin

    base = settings.SITE_URL or base_url
    if not base:
        return None
    ruta = reverse("ficha_paca_corta", args=[paca.codigo_unico])
    return urljoin(base.rstrip("/") + "/", ruta.lstrip("/"))


def generar_pdf_etiquetas(pacas, base_url=None):
    """Devuelve el PDF de las etiquetas como bytes."""
    buffer = io.BytesIO()
    ancho, alto = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    margen = 12
    columnas = 3
    filas = 8
    celda_ancho = (ancho - 2 * margen) / columnas
    celda_alto = (alto - 2 * margen) / filas

    for indice, paca in enumerate(pacas):
        if indice and indice % (columnas * filas) == 0:
            pdf.showPage()

        pos = indice % (columnas * filas)
        col = pos % columnas
        fila = pos // columnas
        x = margen + col * celda_ancho
        y = alto - margen - (fila + 1) * celda_alto

        pdf.setLineWidth(0.6)
        pdf.rect(x, y, celda_ancho, celda_alto)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(x + celda_ancho / 2, y + celda_alto - 12, "VELPACK S.A.")
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawCentredString(
            x + celda_ancho / 2, y + celda_alto - 23, paca.codigo_unico
        )

        codigo_barras = Code128(
            paca.codigo_unico,
            writer=ImageWriter(),
        ).render(
            {
                "module_width": 0.3,
                "module_height": 8,
                "font_size": 6,
                "write_text": False,
                "quiet_zone": 1,
                "background": "white",
                "foreground": "black",
            }
        )
        pdf.drawImage(
            _reader(codigo_barras),
            x + 12,
            y + celda_alto - 43,
            width=celda_ancho - 24,
            height=18,
        )

        qr = qrcode.make(
            _texto_qr(paca, _url_ficha(paca, base_url)),
            image_factory=PilImage,
            box_size=4,
            border=1,
        )
        tamano_qr = 32
        pdf.drawImage(
            _reader(qr),
            x + celda_ancho - tamano_qr - 6,
            y + 6,
            width=tamano_qr,
            height=tamano_qr,
        )

        pdf.setFont("Helvetica", 7)
        pdf.drawString(
            x + 8,
            y + celda_alto - 57,
            f"{paca.detalle.producto.nombre} / {paca.detalle.color.nombre}",
        )
        pdf.drawString(x + 8, y + 27, f"Lote {paca.lote:02d}")
        pdf.drawString(x + 8, y + 17, f"Paca #{paca.numero_paca}")

    pdf.save()
    return buffer.getvalue()


def generar_archivo_pdf(pacas, descripcion, produccion=None, base_url=None):
    """Genera y guarda el PDF, devolviendo el registro ``ArchivoEtiquetas``."""
    contenido = generar_pdf_etiquetas(pacas, base_url=base_url)
    nombre = f"etiquetas_{timezone.localdate():%Y%m%d}_{uuid.uuid4().hex[:8]}.pdf"
    archivo = ArchivoEtiquetas(
        descripcion=descripcion[:200],
        cantidad_pacas=len(pacas),
        produccion=produccion,
    )
    archivo.archivo.save(nombre, ContentFile(contenido), save=False)
    archivo.save()
    return archivo
