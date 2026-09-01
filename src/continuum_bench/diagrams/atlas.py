"""Readable PDF schema atlas; runnable with a separate ReportLab interpreter."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path


def build_atlas(data: dict, destination: Path) -> int:
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        LongTable, PageBreak, Paragraph, SimpleDocTemplate,
        Spacer, TableStyle,
    )

    fonts = Path(reportlab.__file__).parent / 'fonts'
    pdfmetrics.registerFont(TTFont('AtlasSans', str(fonts / 'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('AtlasSans-Bold', str(fonts / 'VeraBd.ttf')))
    pdfmetrics.registerFontFamily('AtlasSans', normal='AtlasSans', bold='AtlasSans-Bold')
    styles = getSampleStyleSheet()
    for name in ('Title', 'Heading1', 'Heading2', 'BodyText'):
        styles[name].fontName = 'AtlasSans-Bold' if name != 'BodyText' else 'AtlasSans'
    styles['Title'].fontSize, styles['Title'].leading = 22, 28
    styles['Heading1'].fontSize, styles['Heading1'].leading = 16, 21
    styles['Heading2'].fontSize, styles['Heading2'].leading = 11, 16
    styles['Heading2'].spaceBefore = 6
    styles['BodyText'].fontSize, styles['BodyText'].leading = 9, 13
    cell = ParagraphStyle('Cell', fontName='AtlasSans', fontSize=8, leading=11,
                          wordWrap='CJK', alignment=TA_LEFT, spaceAfter=0)
    head = ParagraphStyle('Head', parent=cell, fontName='AtlasSans-Bold')
    width, height = A4
    inner = width - 72
    story = []
    nodes = {node['id']: node for node in data['nodes']}

    def paragraph(text: str, style=cell):
        return Paragraph(escape(text).replace('\n', '<br/>'), style)

    def table(headers: list[str], rows: list[list[str]], fractions: list[float]):
        values = [[paragraph(value, head) for value in headers]]
        values += [[paragraph(str(value)) for value in row] for row in rows]
        item = LongTable(values, colWidths=[inner * fraction for fraction in fractions],
                         repeatRows=1, hAlign='LEFT')
        item.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6EBEF')),
            ('LINEBELOW', (0, 0), (-1, 0), .6, colors.HexColor('#6D7B87')),
            ('LINEBELOW', (0, 1), (-1, -1), .25, colors.HexColor('#DDE2E6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        return item

    story.append(Paragraph('Continuum monitoring ontology', styles['Title']))
    story.append(Paragraph('Complete schema atlas', styles['Heading1']))
    story.append(paragraph('Release ' + data['ontology_version'] + ' | ' + data['ontology_revision'], styles['BodyText']))
    story.append(Spacer(1, 16))
    story.append(paragraph(
        'Companion to the simplified and complete conceptual graphs. This atlas '
        'keeps every declared class and property readable at normal print size. '
        'It describes the asserted TBox, including the benchmark deployment '
        'extension and external vocabulary declarations, not individual users '
        'or experimental events.', styles['BodyText']))
    story.append(Spacer(1, 14))
    labels = {'named_classes': 'Named classes', 'anonymous_expressions': 'Anonymous class expressions',
              'object_properties': 'Object properties', 'datatype_properties': 'Datatype properties',
              'annotation_properties': 'Annotation properties', 'subclass_axioms': 'Subclass axioms'}
    story.append(table(['Schema inventory', 'Count'],
                       [[label, str(data['counts'][key])] for key, label in labels.items()], [.8, .2]))
    story.append(Spacer(1, 16))
    story.append(paragraph('Reading the diagrams', styles['Heading2']))
    story.append(paragraph(
        'Solid arrows are object-property domain-to-range projections, not '
        'mandatory links, cardinalities or a workflow. Hollow arrows point from '
        'a subclass to its parent. OR identifies an explicit union; multiple '
        'asserted domains or ranges are combined with AND. "Not declared" means '
        'the source supplies no constraint; no class is invented to fill that gap. '
        'Datatype properties are attributes. Annotation properties and additional '
        'schema axioms are listed separately.', styles['BodyText']))
    story.append(Spacer(1, 10))
    story.append(paragraph(
        'The simplified graph is a deliberately selected subset. The full map is '
        'a zoomable vector supplement, not a figure to shrink onto one paper '
        'column. Colors identify modules; names, borders and line styles retain '
        'meaning in grayscale. Class/individual punning is marked explicitly. '
        'SPARQL and SHACL enforcement is not inferred from a diagram.', styles['BodyText']))

    for module, definition in data['modules'].items():
        classes = sorted((n for n in data['nodes'] if n['kind'] == 'class' and n['module'] == module),
                         key=lambda n: n['qname'])
        props = sorted((p for p in data['properties'] if p['module'] == module), key=lambda p: p['qname'])
        if not classes and not props:
            continue
        story.append(PageBreak())
        story.append(Paragraph(escape(definition[0]), styles['Heading1']))
        story.append(paragraph(f'{len(classes)} named classes | {len(props)} properties', styles['BodyText']))
        story.append(Spacer(1, 12))
        if classes:
            story.append(Paragraph('Classes and asserted parents', styles['Heading2']))
            rows = []
            for node in classes:
                parents = [nodes[e['target']]['qname'] for e in data['edges']
                           if e['kind'] == 'subclass' and e['source'] == node['id']]
                rows.append([node['qname'] + (' [punned]' if node['punned'] else ''),
                             '\n'.join(parents) or '-', node['label']])
            story.append(table(['Class', 'subClassOf', 'English label'], rows, [.35, .28, .37]))
        for kind, title in [('object_property', 'Object properties'),
                            ('datatype_property', 'Datatype properties'),
                            ('annotation_property', 'Annotation properties')]:
            subset = [prop for prop in props if prop['kind'] == kind]
            if not subset:
                continue
            story.append(Spacer(1, 8))
            story.append(Paragraph(title, styles['Heading2']))
            rows = [[p['qname'] + ('\n' + ', '.join(p['characteristics']) if p['characteristics'] else ''),
                     p['domain_text'], p['range_text']] for p in subset]
            story.append(table(['Property', 'Asserted domain', 'Asserted range'], rows, [.32, .35, .33]))

    story.append(PageBreak())
    story.append(Paragraph('Additional axioms and provenance', styles['Heading1']))
    extra = [edge for edge in data['edges'] if edge['kind'] not in
             {'domain', 'range', 'subclass', 'union_member', 'intersection_member'}]
    if extra:
        story.append(table(['Subject', 'Axiom', 'Object'],
            [[nodes[e['source']]['qname'], e['kind'], nodes[e['target']]['qname']] for e in extra], [.36, .25, .39]))
        story.append(Spacer(1, 16))
    story.append(paragraph(
        'Full IRIs, expression members, declaration source files and comments '
        'are retained in data/schema.json and the CSV inventories. GraphML '
        'retains term identity and schema edges for graph editors, not the full OWL model. '
        'No additional ontology is imported from the network. The hashes below '
        f'identify the exact {len(data["sources"])} runtime inputs, including the deployment extension.',
        styles['BodyText']))
    story.append(Spacer(1, 12))
    story.append(table(['Source', 'SHA-256'], [[s['path'], s['sha256']] for s in data['sources']], [.42, .58]))

    def page_frame(canvas, document):
        canvas.saveState()
        canvas.setTitle('Continuum monitoring ontology - complete schema atlas')
        canvas.setAuthor('Continuum Monitoring project')
        canvas.setFont('AtlasSans', 8)
        canvas.setFillColor(colors.HexColor('#46545E'))
        canvas.drawString(36, height - 24, 'CONTINUUM MONITORING | SCHEMA ATLAS')
        canvas.drawString(36, 22, data['ontology_revision'])
        canvas.drawRightString(width - 36, 22, str(document.page))
        canvas.restoreState()

    destination.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(destination), pagesize=A4, leftMargin=36, rightMargin=36,
                                 topMargin=48, bottomMargin=42, invariant=1)
    document.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    return document.page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    pages = build_atlas(json.loads(args.input.read_text(encoding='utf-8')), args.output)
    print(json.dumps({'atlas_pages': pages}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
