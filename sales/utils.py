import io
from reportlab.lib.pagesizes import A6
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_invoice_pdf(sale):
    """
    Génère une facture PDF en mémoire pour une vente donnée.
    """
    buffer = io.BytesIO()

    # Configuration du document (Format A6 idéal pour les reçus/factures)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A6,
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15
    )

    elements = []
    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,  # Centré
        spaceAfter=4
    )

    sub_title_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        alignment=1,
        spaceAfter=10
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        spaceAfter=2
    )

    # 1. En-tête de la Pharmacie
    elements.append(Paragraph("<b>BECKYPHARMA</b>", title_style))

    # Pharmacie
    pharmacy_name = sale.pharmacy.name if hasattr(sale, 'pharmacy') else "Pharmacie"
    elements.append(Paragraph(f"Pharmacie : <b>{pharmacy_name}</b>", sub_title_style))

    # Numéro de reçu
    elements.append(Paragraph(f"<b>Reçu N° :</b> #{sale.id}", normal_style))

    # Agent
    agent_name = sale.agent.username if hasattr(sale, 'agent') and sale.agent else "Caisse"
    elements.append(Paragraph(f"<b>Agent :</b> {agent_name}", normal_style))

    # Date
    sale_date = sale.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(sale, 'created_at') else ""
    elements.append(Paragraph(f"<b>Date :</b> {sale_date}", normal_style))

    elements.append(Spacer(1, 10))

    # 2. Tableau des Articles
    data = [["Produit", "Qté", "P.U", "Total"]]

    # Parcourir les articles de la vente
    # Remplacez 'items' si votre relation s'appelle différemment dans models.py
    sale_items = sale.items.all() if hasattr(sale, 'items') else []
    for item in sale_items:
        data.append([
            item.product.name[:18],  # Nom tronqué si trop long
            str(item.quantity),
            f"{item.unit_price:.2f}",
            f"{item.total_price:.2f}"
        ])

    # Largeurs des colonnes pour format ticket A6
    table = Table(data, colWidths=[110, 30, 45, 50])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 10))

    # 3. Total
    total_amount = getattr(sale, 'total_amount', 0.00)
    total_style = ParagraphStyle(
        'TotalStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=2  # Aligné à droite
    )
    elements.append(Paragraph(f"TOTAL : {total_amount:.2f} $", total_style))
    elements.append(Spacer(1, 15))

    # 4. Pied de page
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        alignment=1
    )
    elements.append(Paragraph("Merci de votre confiance !", footer_style))
    elements.append(Paragraph("Les médicaments vendus ne sont ni repris ni échangés.", footer_style))

    # Génération du PDF dans le buffer
    doc.build(elements)
    buffer.seek(0)
    return buffer