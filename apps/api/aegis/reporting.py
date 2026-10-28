from io import BytesIO
from html import escape
from datetime import datetime, timezone
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from .analyst import RuleBasedAnalyst
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from pathlib import Path
_font_dir = Path(reportlab.__file__).parent / 'fonts'
pdfmetrics.registerFont(TTFont('Vera', str(_font_dir / 'Vera.ttf')))
pdfmetrics.registerFont(TTFont('VeraBold', str(_font_dir / 'VeraBd.ttf')))


def render_pdf(snapshot,branding=None):
    output=BytesIO()
    doc=SimpleDocTemplate(output,pagesize=(595,842),rightMargin=42,leftMargin=42,topMargin=48,bottomMargin=45,title='AEGIS Authorized Configuration Assessment')
    styles=getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName='VeraBold' if style.name.startswith('Heading') or style.name=='Title' else 'Vera'
        style.spaceAfter=9
    styles.add(ParagraphStyle(name='Brand',fontName='VeraBold',fontSize=26,leading=32,textColor=colors.HexColor(branding['color'] if branding else '#123842'),spaceAfter=16))
    story=[]
    def p(text,style='BodyText'):
        story.append(Paragraph(escape(str(text)),styles[style]))
    if branding and branding.get('logo_png'):
        import base64
        from reportlab.platypus import Image
        logo=Image(BytesIO(base64.b64decode(branding['logo_png'])))
        ratio=min(160/logo.imageWidth,70/logo.imageHeight)
        logo.drawWidth=logo.imageWidth*ratio;logo.drawHeight=logo.imageHeight*ratio
        story.append(logo)
    p(branding['name'] if branding else 'AEGIS / Security Cloud','Brand')
    if branding:
        p(branding.get('cover',''));p(branding.get('contact',''))
        p('Prepared from AEGIS recorded assessment evidence; branding does not alter findings or certify security.')
    p('AUTHORIZED CONFIGURATION ASSESSMENT','Heading2')
    p(snapshot['organization'],'Heading1')
    p(snapshot['origin'])
    p('Assessment: '+snapshot['job_id'])
    p('UTC: '+datetime.fromtimestamp(snapshot['date'],timezone.utc).isoformat())
    p('Scope & methodology','Heading2')
    p('Bounded GET requests to the exact authorized origin and explicitly listed paths: '+', '.join(snapshot.get('scope',{}).get('paths',['/']))+'. Response configuration and TLS inspection only. No redirects followed or automatic crawling.')
    p('Result: '+snapshot['status'])
    summary=RuleBasedAnalyst().explain([f['rule'] for f in snapshot['findings']])
    p('Executive summary','Heading2');p(summary['summary']);p(summary['business_impact'])
    counts={s:sum(f['severity']==s for f in snapshot['findings']) for s in ('critical','high','medium','low')}
    table=Table([['Severity','Observations']]+[[k.title(),str(v)] for k,v in counts.items()],colWidths=[350,150])
    table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Vera'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#123842')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('BOTTOMPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.append(table)
    comparison=snapshot.get('comparison')
    if comparison:
        story.append(PageBreak())
        p('Full supported-profile remediation retest','Heading2')
        p('Baseline assessment: '+comparison['baseline_job_id'])
        p('Original observation: '+comparison['original'])
        p(' | '.join(f'{key.title()}: {len(comparison[key])}' for key in ('resolved','unresolved','new','unverified')))
        for key in ('resolved','unresolved','new'):
            p(key.title()+': '+(', '.join(comparison[key]) or 'None'))
        for item in comparison['unverified']:
            p('Unverified: '+item['rule']+' - '+item['reason'])
        p(comparison['assurance'])
    manifest=snapshot.get('profile')
    if manifest:
        p('Executed profile: '+manifest['version'])
        p('Executed checks: '+', '.join(manifest['executed']))
        for rule,reason in manifest['not_performed'].items():p('Not performed: '+rule+' - '+reason)
    advisories=snapshot.get('advisory_evaluation',[])
    if advisories:
        p('Relevant advisory evaluation','Heading2')
        for item in advisories:p(item['advisory_id']+' / '+item['status']+' / '+item['verification'])
        p('These inventory-based advisory matches are separate from confirmed response observations. They are not verified fixed by this HTTP profile.')
    if snapshot['findings']:
        story.append(PageBreak())
        p('Technical observations','Heading2')
    for f in snapshot['findings']:
        start=len(story)
        p(f['title'],'Heading3');p(f"Severity: {f['severity']} | Confidence: {f['confidence']} | Rule: {f['rule']}")
        p('Evidence: '+f['evidence']);p('Recommended action: '+f['remediation'])
        p('Classification: observed configuration signal; exploitability is not established. Severity is qualitative, not a CVSS score.')
        group=story[start:]
        del story[start:]
        story.append(KeepTogether(group))
    p('Limitations & retesting','Heading2');p(summary['limitations']);p('Validate each approved change and run a new authorized assessment. Absence in this response is not proof of global resolution. This report does not certify the website as secure.')
    def footer(canvas,document):
        canvas.setFont('Vera',7);canvas.setFillColor(colors.grey);canvas.drawString(42,25,'CONFIDENTIAL  /  Authorized customer assessment  /  Payments disabled');canvas.drawRightString(553,25,str(document.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    output.seek(0)
    return output


def render_remediation_document(data, kind):
    """Customer-facing snapshot from authorized DB records, not internal notes."""
    output=BytesIO()
    title={'quotation':'Remediation quotation','progress':'Remediation progress summary',
           'completion':'Remediation completion summary'}[kind]
    doc=SimpleDocTemplate(output,pagesize=(595,842),rightMargin=42,leftMargin=42,
        topMargin=48,bottomMargin=45,title=title)
    styles=getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName='VeraBold' if style.name.startswith('Heading') or style.name=='Title' else 'Vera'
        style.spaceAfter=9
    story=[]
    def p(text,style='BodyText'):
        # Paragraph escaping prevents supplied scope from becoming document markup.
        for line in str(text).splitlines() or ['']:
            story.append(Paragraph(escape(line),styles[style]))
    p('AEGIS / Security Cloud','Title');p(title,'Heading1')
    p(data['organization'],'Heading2');p(data['origin'])
    p('Request: '+data['id']);p('Generated UTC: '+datetime.now(timezone.utc).isoformat())
    p('Status: '+data['status']);p('Payments disabled. No payment has been collected. This is not an invoice or receipt.')
    p('Finding under review','Heading2');p(data['finding_title'])
    p('Agreed or proposed scope','Heading2');p(data['scope'] or 'No formal scope has been issued.')
    p('Preliminary engineering estimate');p(data['estimate'])
    p('Pricing and payment processing are disabled. Approval covers the proposed technical scope only.')
    p('Customer acceptance: '+(datetime.fromtimestamp(data['accepted_at'],timezone.utc).isoformat() if data['accepted_at'] else 'Not accepted'))
    if kind!='quotation':
        p('Full supported reassessment','Heading2')
        retest=data['retest']
        if not retest:p('No approved reassessment has been completed. No verified fix is claimed.')
        else:
            p('Retest status: '+retest['status']);p('Assessment: '+str(retest['job_id'] or 'Not launched'))
            comparison=retest['comparison']
            for key in ('resolved','unresolved','new','unverified'):
                if key in comparison:p(f'{key.title()}: {len(comparison[key])}')
            if comparison.get('failure'):p(comparison['failure'])
            for item in comparison.get('unverified',[]):p(item['rule']+': '+item['reason'])
            p('Relevant advisory runtime verification gaps: '+str(len(comparison.get('advisories',[]))))
    p('Limitations','Heading2')
    p('Only the approved non-destructive assessment profile and authorized scope were assessed. Passing these checks does not certify the website or guarantee that no vulnerabilities remain. No production website was modified automatically by AEGIS.')
    def footer(canvas,document):
        canvas.setFont('Vera',7);canvas.drawString(42,25,'CONFIDENTIAL / Authorized workspace / Payments disabled')
        canvas.drawRightString(553,25,str(document.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    output.seek(0);return output


def render_launch_review_pdf(review):
    """Read-only account-scoped Launch Guard evidence, explicitly *not* a security certificate.

    The caller must authorize access to review.org_id before invoking this renderer.
    Supplied repository names, check labels and paths are escaped and length-bounded.
    """
    result = review.result if isinstance(review.result, dict) else {}
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(595, 842), rightMargin=42,
                            leftMargin=42, topMargin=48, bottomMargin=45,
                            title='AEGIS Launch Guard — advisory evidence')
    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'VeraBold'
    styles['BodyText'].fontName = 'Vera'
    styles['Heading2'].fontName = 'VeraBold'
    styles['Heading3'].fontName = 'VeraBold'
    styles['BodyText'].spaceAfter = 7
    story = []

    def paragraph(label, value='', *, style='BodyText', max_chars=400):
        rendered = (str(label) + str(value))[:max_chars]
        story.append(Paragraph(escape(rendered), styles[style]))

    paragraph('AEGIS / LAUNCH GUARD', style='Title')
    paragraph('Read-only, advisory GitHub pull-request evidence', style='Heading2')
    paragraph('Repository: ', review.repository, max_chars=240)
    paragraph('Commit: ', review.revision, max_chars=100)
    paragraph('Review ID: ', review.id, max_chars=140)
    paragraph('Pull request: ', result.get('pull_request', 'not recorded'))
    paragraph('Recorded UTC: ', datetime.fromtimestamp(review.created, timezone.utc).isoformat())
    paragraph('CI evidence status: ', result.get('ci', 'unverified'))
    paragraph('Evidence complete: ', result.get('evidence_complete', False))
    paragraph('Staging: ', result.get('staging', 'not_run'))
    paragraph('Dependency audit: ', result.get('dependency_audit', 'not_performed'))
    paragraph('Release gate: ', result.get('release_gate', 'advisory_only'))
    paragraph('NOT A CERTIFICATION: a passing CI status is not a security audit. '
              'This report does not approve deployment, merge a PR, certify a product, '
              'or establish that staging and dependency analysis were completed.')

    reviews = result.get('required_reviews')
    paragraph('Manual reviews indicated', style='Heading2')
    if isinstance(reviews, list) and reviews:
        for category in reviews[:40]:
            paragraph('Review: ', category, max_chars=220)
    else:
        paragraph('None flagged by the available path-only signals; not proof of safety.')
    paragraph('Recorded checks', style='Heading2')
    checks = result.get('checks')
    if isinstance(checks, list) and checks:
        for check in checks[:100]:
            if isinstance(check, dict):
                paragraph('Check: ', f"{check.get('name','')} / {check.get('status','')} / {check.get('conclusion','')}", max_chars=320)
    else:
        paragraph('No complete checks recorded.')
    paragraph('Changed files (up to 100)', style='Heading2')
    files = result.get('changed_files')
    if isinstance(files, list) and files:
        for entry in files[:100]:
            if isinstance(entry, dict):
                paragraph('File: ', f"{entry.get('path','')} [{entry.get('status','unknown')}]", max_chars=460)
    else:
        paragraph('No changed-file evidence recorded.')
    paragraph('Limits', style='Heading2')
    paragraph('This is a snapshot of recorded, scoped GitHub API response metadata. '
              'It is not independently notarized, may be incomplete or stale after the recorded revision, '
              'and does not execute code, discover vulnerabilities, validate a running release or deploy changes.')

    def footer(canvas, document):
        canvas.setFont('Vera', 7)
        canvas.drawString(42, 25, 'CONFIDENTIAL / Authorized workspace / Advisory only / No deployment')
        canvas.drawRightString(553, 25, str(document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    output.seek(0)
    return output


def render_health_monitor_pdf(monitor, origin, authorization, observations):
    """A bounded PDF of recorded, customer-authorized health samples, not an uptime SLA.

    The caller MUST verify monitor.org_id membership before calling the renderer.
    Observations are an incomplete time-window sample, never continuous monitoring.
    """
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(595, 842), rightMargin=42,
                            leftMargin=42, topMargin=48, bottomMargin=45,
                            title='AEGIS Website Health — observed checks')
    styles = getSampleStyleSheet()
    for name in ('Title', 'Heading2'):
        styles[name].fontName = 'VeraBold'
    styles['BodyText'].fontName = 'Vera'
    styles['BodyText'].spaceAfter = 8
    story = []

    def p(label, value='', *, style='BodyText', limit=380):
        story.append(Paragraph(escape((str(label) + str(value))[:limit]), styles[style]))

    p('AEGIS / WEBSITE HEALTH', style='Title')
    p('Recorded authorized endpoint observations', style='Heading2')
    p('Asset origin: ', origin, limit=240)
    p('Monitor ID: ', monitor.id, limit=150)
    p('Monitor state: ', 'enabled' if monitor.enabled else 'disabled')
    p('Most recent status: ', monitor.last_status)
    p('Check interval (seconds): ', monitor.interval_seconds)
    p('Consent expiry (UTC): ', datetime.fromtimestamp(authorization.expires, timezone.utc).isoformat()
      if authorization is not None else 'authorization unavailable')
    p('Recorded observations: ', len(observations))
    statuses = {}
    for item in observations[:100]:
        label = str(item.status)[:40]
        statuses[label] = statuses.get(label, 0) + 1
    p('Observed status counts: ', ', '.join(f'{key}: {value}' for key, value in sorted(statuses.items())) or 'none')
    p('This report lists up to 100 recent samples; no continuous uptime percentage, '
      'contractual service-level guarantee, domain expiry date or security certification is inferred.')
    p('Recent observations (newest first)', style='Heading2')
    for item in observations[:100]:
        when = datetime.fromtimestamp(item.created, timezone.utc).isoformat()
        detail = (f'{when} / {str(item.status)[:40]} / HTTP: '
                  f'{item.http_status if item.http_status is not None else "unavailable"} / '
                  f'Latency: {round(item.response_ms)} ms' if isinstance(item.response_ms, (float,int)) else
                  f'{when} / {str(item.status)[:40]} / HTTP: '
                  f'{item.http_status if item.http_status is not None else "unavailable"} / Latency: unavailable')
        p('', detail, limit=430)
    p('Methodology and limits', style='Heading2')
    p('Each entry represents one approved bounded HTTP GET. An unobserved period is unknown, '
      'not up. Checks stop when authorization or ownership expires or is revoked. '
      'This document is not a security scan, AutoFix authorization or verified availability SLA.')

    def footer(canvas, document):
        canvas.setFont('Vera', 7)
        canvas.drawString(42, 25, 'CONFIDENTIAL / Recorded samples only / No uptime guarantee')
        canvas.drawRightString(553, 25, str(document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    output.seek(0)
    return output


def render_intelligence_pdf(org_id, inventory, impacts, generated_at=None):
    """Recorded, tenant-filtered inventory matches; *not* confirmed vulnerabilities.

    Route must authorize membership before fetching the tenant's rows. All free
    text is escaped and bounded to avoid HTML interpretation or giant PDF output.
    """
    import time as _time
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(595, 842), rightMargin=42,
                            leftMargin=42, topMargin=48, bottomMargin=45,
                            title='AEGIS Intelligence — inventory match evidence')
    styles = getSampleStyleSheet()
    for key in ('Title', 'Heading2'):
        styles[key].fontName = 'VeraBold'
    styles['BodyText'].fontName = 'Vera'
    styles['BodyText'].spaceAfter = 7
    story = []

    def p(label, value='', style='BodyText', limit=370):
        story.append(Paragraph(escape((str(label) + str(value))[:limit]), styles[style]))

    p('AEGIS / VULNERABILITY INTELLIGENCE', style='Title')
    p('Authorized workspace inventory and advisory matches', style='Heading2')
    p('Workspace ID: ', org_id, limit=150)
    now = _time.time() if generated_at is None else generated_at
    p('Generated UTC: ', datetime.fromtimestamp(now, timezone.utc).isoformat())
    p('Inventory rows included: ', min(len(inventory), 100))
    p('Advisory matches included: ', min(len(impacts), 100))
    p('Not a vulnerability finding: package and version matches alone do not prove '
      'that code is reachable, deployed, exploitable, or fixed. External advisories '
      'and approval statuses may have changed since synchronization.')
    p('Declared inventory (up to 100 rows)', style='Heading2')
    if not inventory:
        p('No declared inventory available in the sampled records.')
    for item in inventory[:100]:
        p('Component: ', f"{item.get('ecosystem', '?')} / {item.get('package', '?')} / "
          f"{item.get('version') or 'unknown'}", limit=300)
        p('Asset association: ', item.get('asset_id') or 'unavailable')
    p('Potential advisory matches (up to 100 rows)', style='Heading2')
    if not impacts:
        p('No recorded advisory matches; this is not evidence of absence of risk.')
    for item in impacts[:100]:
        p('Advisory: ', item.get('identifier') or 'unavailable', limit=150)
        p('Classification: ', item.get('status') or 'unverified', limit=130)
        p('Asset association: ', item.get('asset_id') or 'unavailable', limit=170)
        p('Matching evidence: ', item.get('reason') or 'unavailable', limit=350)
    p('Evidence limits', style='Heading2')
    p('Only a bounded snapshot of customer-declared inventory and stored advisory '
      'matches is shown. Missing or cross-workspace references are marked unavailable. '
      'This report performs no live scan, dependency audit, exploit validation, '
      'or remediation check. It is not an AEGIS security certification.')

    doc.build(story)
    output.seek(0)
    return output
