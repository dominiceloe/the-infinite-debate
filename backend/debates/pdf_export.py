"""
PDF export functionality for debates.
Generates professionally formatted PDFs with citations using ReportLab.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from core.sanitization import sanitize_markdown
import html


def generate_debate_pdf(debate):
    """
    Generate a PDF export of a debate.

    Args:
        debate: Debate instance

    Returns:
        bytes: PDF file content
    """
    # Create a BytesIO buffer
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Get debate data
    participants = debate.participants.all().order_by('birth_year')
    messages = debate.messages.all().select_related('persona').prefetch_related(
        'text_citations__primary_text'
    )

    # Group messages by round
    rounds = {}
    for message in messages:
        round_num = message.round_number
        if round_num not in rounds:
            rounds[round_num] = []
        rounds[round_num].append(message)

    # Define styles
    styles = get_custom_styles()

    # Build the PDF content
    elements.extend(build_header(debate, styles))
    elements.extend(build_participants_section(participants, styles))

    if debate.summary:
        elements.extend(build_summary_section(debate.summary, styles))

    elements.extend(build_transcript_section(rounds, styles))
    elements.extend(build_footer(debate, styles))

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def get_custom_styles():
    """Define custom paragraph styles for the PDF."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))

    # Topic style
    styles.add(ParagraphStyle(
        name='Topic',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))

    # Metadata style
    styles.add(ParagraphStyle(
        name='Metadata',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=20,
        alignment=TA_CENTER,
    ))

    # Section heading
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
    ))

    # Subsection heading
    styles.add(ParagraphStyle(
        name='SubsectionHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    ))

    # Persona name
    styles.add(ParagraphStyle(
        name='PersonaName',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#3498db'),
        spaceAfter=4,
        fontName='Helvetica-Bold',
    ))

    # Message content
    styles.add(ParagraphStyle(
        name='MessageContent',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14,
    ))

    # Citation style
    styles.add(ParagraphStyle(
        name='Citation',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=4,
        leftIndent=20,
        fontName='Helvetica-Oblique',
    ))

    # Footer style
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
    ))

    return styles


def build_header(debate, styles):
    """Build the header section with title and metadata."""
    elements = []

    # Title - escape HTML to prevent XSS
    safe_title = html.escape(debate.title)
    elements.append(Paragraph(safe_title, styles['CustomTitle']))
    elements.append(Spacer(1, 0.1*inch))

    # Topic - escape HTML to prevent XSS
    safe_topic = html.escape(debate.topic)
    topic_text = f"<b>Topic:</b> {safe_topic}"
    elements.append(Paragraph(topic_text, styles['Topic']))
    elements.append(Spacer(1, 0.1*inch))

    # Metadata
    metadata_text = (
        f"Created: {debate.created_at.strftime('%B %d, %Y')} | "
        f"Depth: {debate.get_depth_level_display()} | "
        f"Rounds: {debate.rounds_completed}"
    )
    elements.append(Paragraph(metadata_text, styles['Metadata']))

    # Separator line
    elements.append(Spacer(1, 0.2*inch))

    return elements


def build_participants_section(participants, styles):
    """Build the participants section."""
    elements = []

    elements.append(Paragraph("Participants", styles['SectionHeading']))
    elements.append(Spacer(1, 0.1*inch))

    for persona in participants:
        # Persona name
        elements.append(Paragraph(persona.name, styles['PersonaName']))

        # Details
        years = f"{persona.birth_year}-{persona.death_year or 'present'}"
        details = f"{years} | {persona.category.title()}"
        elements.append(Paragraph(details, styles['Metadata']))

        # Title/description
        if persona.title:
            elements.append(Paragraph(persona.title, styles['Normal']))

        elements.append(Spacer(1, 0.15*inch))

    elements.append(Spacer(1, 0.2*inch))

    return elements


def build_summary_section(summary, styles):
    """Build the summary section."""
    elements = []

    elements.append(Paragraph("Summary", styles['SectionHeading']))
    elements.append(Spacer(1, 0.1*inch))

    # Summary text
    elements.append(Paragraph(summary, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    return elements


def build_transcript_section(rounds, styles):
    """Build the debate transcript section."""
    elements = []

    elements.append(Paragraph("Debate Transcript", styles['SectionHeading']))
    elements.append(Spacer(1, 0.15*inch))

    for round_num in sorted(rounds.keys()):
        # Round heading
        round_heading = f"Round {round_num}"
        elements.append(Paragraph(round_heading, styles['SubsectionHeading']))
        elements.append(Spacer(1, 0.1*inch))

        for message in rounds[round_num]:
            # Keep message together on same page
            message_elements = []

            # Persona name - escape HTML
            safe_persona_name = html.escape(message.persona.name)
            message_elements.append(Paragraph(safe_persona_name, styles['PersonaName']))

            # Message content - sanitize markdown first, then escape for PDF
            safe_content = html.escape(sanitize_markdown(message.content))
            message_elements.append(Paragraph(safe_content, styles['MessageContent']))

            # Citations
            citations = message.text_citations.all()
            if citations:
                message_elements.append(Spacer(1, 0.05*inch))
                citation_heading = Paragraph("<b>Citations:</b>", styles['Citation'])
                message_elements.append(citation_heading)

                for citation in citations:
                    text = citation.primary_text
                    citation_text = f"• <b>{text.title}</b>"

                    if text.author:
                        citation_text += f" by {text.author}"

                    if text.source_url:
                        citation_text += f' <link href="{text.source_url}" color="blue">[View Source]</link>'

                    if citation.quote_text:
                        quote_preview = citation.quote_text[:100]
                        if len(citation.quote_text) > 100:
                            quote_preview += '...'
                        citation_text += f'<br/><i>"{quote_preview}"</i>'

                    message_elements.append(Paragraph(citation_text, styles['Citation']))

            message_elements.append(Spacer(1, 0.15*inch))

            # Keep message together
            elements.append(KeepTogether(message_elements))

        elements.append(Spacer(1, 0.2*inch))

    return elements


def build_footer(debate, styles):
    """Build the footer section."""
    elements = []

    elements.append(Spacer(1, 0.3*inch))

    footer_text = (
        f"Generated by The Infinite Debate | "
        f"{debate.created_at.strftime('%B %d, %Y')}"
    )
    elements.append(Paragraph(footer_text, styles['Footer']))

    return elements
