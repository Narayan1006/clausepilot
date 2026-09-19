"""
ClausePilot Sample Document Generator.

Generates 4 synthetic legal documents for development and RAG testing.
These are entirely fictional documents. They are NOT legal advice.

Deliberate design choices for RAG testing:
- Explicit clauses with numbers
- Ambiguous language (INFERRED scenario)
- Missing information (NOT_FOUND scenario)
- Intentional inconsistencies within documents (CONFLICT scenario)
- Compensation details for comparison testing
"""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    PageBreak,
)
from reportlab.lib import colors

OUTPUT_DIR = Path(__file__).parent
W, H = letter


def _doc(filename: str, title: str) -> SimpleDocTemplate:
    path = OUTPUT_DIR / filename
    return SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title=title,
        author="ClausePilot (Synthetic — Not Legal Advice)",
    )


def _styles():
    s = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "CP_H1",
        parent=s["Heading1"],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    )
    h2 = ParagraphStyle(
        "CP_H2",
        parent=s["Heading2"],
        fontSize=13,
        spaceAfter=8,
        textColor=colors.HexColor("#16213e"),
    )
    body = ParagraphStyle(
        "CP_Body",
        parent=s["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=6,
    )
    warning = ParagraphStyle(
        "CP_Warning",
        parent=s["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        spaceAfter=4,
    )
    return h1, h2, body, warning


# ─────────────────────────────────────────────────────────────
# Document 1: Employment Contract A
# Deliberate: explicit notice period, ambiguous IP clause,
#             inconsistency between remote work and office clauses
# ─────────────────────────────────────────────────────────────

def generate_employment_a():
    doc = _doc("employment-contract-a.pdf", "Employment Agreement — Acme Corp")
    h1, h2, body, warning = _styles()

    story = [
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
        Spacer(1, 6),
        Paragraph("EMPLOYMENT AGREEMENT", h1),
        Paragraph(
            "This Employment Agreement (\"Agreement\") is entered into as of the "
            "1st day of March, 2025 (\"Effective Date\") between <b>Acme Corporation</b>, "
            "a company incorporated under the laws of the State of Delaware (\"Company\"), "
            "and <b>Jordan Riley</b> (\"Employee\").",
            body,
        ),
        Spacer(1, 12),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
        Spacer(1, 12),

        # Clause 1 — Position
        Paragraph("1. POSITION AND DUTIES", h2),
        Paragraph(
            "1.1 The Employee is hired as <b>Senior Software Engineer</b> in the "
            "Technology division. The Employee shall report to the Vice President of Engineering.",
            body,
        ),
        Paragraph(
            "1.2 The Employee agrees to devote full business time and attention to "
            "the duties of the position.",
            body,
        ),
        Spacer(1, 8),

        # Clause 2 — Compensation (explicit)
        Paragraph("2. COMPENSATION", h2),
        Paragraph(
            "2.1 <b>Base Salary</b>: The Company shall pay the Employee a base salary of "
            "<b>USD 145,000 (One Hundred Forty-Five Thousand US Dollars) per annum</b>, "
            "payable in equal bi-weekly instalments, subject to applicable tax withholdings.",
            body,
        ),
        Paragraph(
            "2.2 <b>Performance Bonus</b>: The Employee shall be eligible for an annual "
            "performance bonus of up to <b>20% of base salary</b>, at the sole discretion "
            "of the Company based on performance reviews conducted in Q4 of each year. "
            "The formula for bonus calculation is at the Company's discretion and may change "
            "from year to year.",  # <-- AMBIGUOUS: formula not specified
            body,
        ),
        Paragraph(
            "2.3 <b>Stock Options</b>: The Employee shall be granted options to purchase "
            "10,000 shares of the Company's common stock under the Company's 2024 Equity "
            "Incentive Plan. Vesting details and exercise terms shall be governed by a "
            "separate Stock Option Agreement to be executed within 30 days of the Effective Date.",  # <-- MISSING INFO
            body,
        ),
        Spacer(1, 8),

        # Clause 3 — Probation
        Paragraph("3. PROBATIONARY PERIOD", h2),
        Paragraph(
            "3.1 The first <b>ninety (90) days</b> of employment shall constitute a "
            "probationary period, during which either party may terminate this Agreement "
            "with <b>seven (7) days</b> written notice.",
            body,
        ),
        Spacer(1, 8),

        # Page break
        PageBreak(),

        # Clause 4 — Work Arrangement (CONFLICT with Clause 9)
        Paragraph("4. WORK ARRANGEMENT", h2),
        Paragraph(
            "4.1 The Employee's primary work location shall be the Company's headquarters "
            "at 100 Innovation Drive, San Francisco, CA 94105.",
            body,
        ),
        Paragraph(
            "4.2 <b>Remote Work</b>: The Employee may work remotely on a flexible basis "
            "subject to the requirements of the role and agreement with the direct manager. "
            "The Company supports a hybrid work environment.",  # <-- CONFLICTS with 9.1
            body,
        ),
        Spacer(1, 8),

        # Clause 5 — Leave
        Paragraph("5. LEAVE ENTITLEMENT", h2),
        Paragraph(
            "5.1 <b>Annual Leave</b>: The Employee is entitled to <b>twenty (20) business "
            "days</b> of paid annual leave per calendar year, accruing at 1.67 days per month.",
            body,
        ),
        Paragraph(
            "5.2 <b>Sick Leave</b>: The Employee is entitled to ten (10) days of paid "
            "sick leave per calendar year.",
            body,
        ),
        Spacer(1, 8),

        # Clause 6 — Termination
        Paragraph("6. TERMINATION", h2),
        Paragraph(
            "6.1 <b>Termination by Employee</b>: The Employee may terminate this Agreement "
            "by providing <b>sixty (60) calendar days</b> written notice to the Company.",
            body,
        ),
        Paragraph(
            "6.2 <b>Termination by Company</b>: The Company may terminate this Agreement "
            "by providing sixty (60) calendar days written notice, or pay in lieu of notice.",
            body,
        ),
        Paragraph(
            "6.3 <b>Termination for Cause</b>: The Company may terminate this Agreement "
            "immediately and without notice for cause, including but not limited to: "
            "misconduct, gross negligence, breach of confidentiality, or violation of "
            "Company policies.",
            body,
        ),
        Spacer(1, 8),

        # Clause 7 — Confidentiality
        PageBreak(),
        Paragraph("7. CONFIDENTIALITY", h2),
        Paragraph(
            "7.1 The Employee shall not, during or after the term of employment, "
            "disclose, use, or permit unauthorized access to any Confidential Information "
            "of the Company. \"Confidential Information\" means any non-public information "
            "relating to the Company's business, technology, customers, or strategy.",
            body,
        ),
        Paragraph(
            "7.2 These obligations shall survive the termination of employment for a period "
            "of <b>five (5) years</b>.",
            body,
        ),
        Spacer(1, 8),

        # Clause 8 — Intellectual Property
        Paragraph("8. INTELLECTUAL PROPERTY", h2),
        Paragraph(
            "8.1 Any work product, invention, or intellectual property created by the "
            "Employee during the course of employment, or using Company resources, "
            "shall be the exclusive property of the Company.",
            body,
        ),
        Paragraph(
            "8.2 The Employee shall promptly disclose all inventions to the Company and "
            "shall execute all documents necessary to assign such inventions to the Company.",
            body,
        ),
        Paragraph(
            "8.3 <b>Moonlighting</b>: The Agreement does not prohibit the Employee from "
            "engaging in personal projects outside work hours, provided such projects do "
            "not use Company resources or directly compete with Company business.",  # AMBIGUOUS
            body,
        ),
        Spacer(1, 8),

        # Clause 9 — Office Attendance (CONFLICT with Clause 4.2)
        Paragraph("9. ATTENDANCE AND AVAILABILITY", h2),
        Paragraph(
            "9.1 <b>Office Attendance</b>: The Employee is required to be present at the "
            "Company's office premises <b>Monday through Friday during standard business "
            "hours (9:00 AM – 5:00 PM local time)</b>, except when traveling for Company "
            "business or on approved leave.",  # <-- CONFLICTS with 4.2
            body,
        ),
        Spacer(1, 8),

        # Clause 10 — Non-Compete
        Paragraph("10. NON-COMPETE", h2),
        Paragraph(
            "10.1 For a period of <b>twelve (12) months</b> following termination of "
            "employment, the Employee agrees not to directly compete with the Company "
            "by engaging in any business that is substantially similar to the Company's "
            "core business in the United States.",
            body,
        ),
        Spacer(1, 8),

        # Clause 11 — Dispute Resolution
        PageBreak(),
        Paragraph("11. DISPUTE RESOLUTION", h2),
        Paragraph(
            "11.1 Any dispute arising out of or relating to this Agreement shall be "
            "subject to binding arbitration under the rules of the American Arbitration "
            "Association (AAA) in San Francisco, California.",
            body,
        ),
        Paragraph(
            "11.2 This Agreement shall be governed by the laws of the State of California.",
            body,
        ),
        Spacer(1, 8),

        # Clause 12 — Entire Agreement
        Paragraph("12. ENTIRE AGREEMENT", h2),
        Paragraph(
            "12.1 This Agreement constitutes the entire agreement between the parties "
            "with respect to the subject matter hereof and supersedes all prior agreements.",
            body,
        ),
        Spacer(1, 24),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
        Spacer(1, 12),
        Paragraph(
            "<b>ACME CORPORATION</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Name: Sarah Chen<br/>"
            "Title: Chief People Officer<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph(
            "<b>EMPLOYEE</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Name: Jordan Riley<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
    ]

    doc.build(story)
    print(f"  Generated: employment-contract-a.pdf")


# ─────────────────────────────────────────────────────────────
# Document 2: Employment Contract B (for comparison)
# Different company, different terms — suitable for comparison demo
# ─────────────────────────────────────────────────────────────

def generate_employment_b():
    doc = _doc("employment-contract-b.pdf", "Employment Agreement — Nexus Labs")
    h1, h2, body, warning = _styles()

    story = [
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
        Spacer(1, 6),
        Paragraph("EMPLOYMENT AGREEMENT", h1),
        Paragraph(
            "This Employment Agreement is entered into on the 15th day of March, 2025, "
            "between <b>Nexus Labs Inc.</b>, a Delaware corporation (\"Company\"), "
            "and <b>Jordan Riley</b> (\"Employee\").",
            body,
        ),
        Spacer(1, 12),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
        Spacer(1, 12),

        Paragraph("1. POSITION", h2),
        Paragraph(
            "1.1 The Employee is hired as <b>Lead Software Engineer</b> in the "
            "Product Engineering team. The Employee shall report to the CTO.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("2. COMPENSATION", h2),
        Paragraph(
            "2.1 <b>Base Salary</b>: USD <b>155,000 (One Hundred Fifty-Five Thousand US Dollars) "
            "per annum</b>, payable monthly.",
            body,
        ),
        Paragraph(
            "2.2 <b>Performance Bonus</b>: The Employee shall be eligible for a target "
            "annual bonus of <b>15% of base salary</b>. The bonus is calculated based on "
            "the Employee achieving individual OKRs (70% weight) and Company revenue "
            "targets (30% weight), as assessed in the annual performance review.",  # explicit formula
            body,
        ),
        Paragraph(
            "2.3 <b>Stock Options</b>: The Employee shall be granted options to purchase "
            "15,000 shares of common stock, vesting over <b>4 years with a 1-year cliff</b>. "
            "Unvested options are forfeited upon resignation.",  # explicit vesting
            body,
        ),
        Spacer(1, 8),

        Paragraph("3. PROBATIONARY PERIOD", h2),
        Paragraph(
            "3.1 The probationary period is <b>six (6) months</b>. During this period, "
            "the Company may terminate employment with <b>fourteen (14) days</b> written notice.",
            body,
        ),
        Spacer(1, 8),

        PageBreak(),
        Paragraph("4. WORK ARRANGEMENT", h2),
        Paragraph(
            "4.1 This is a <b>fully remote position</b>. The Employee may work from any "
            "location within the United States.",
            body,
        ),
        Paragraph(
            "4.2 The Employee is expected to be available during core hours: "
            "10:00 AM – 4:00 PM Pacific Time on business days.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("5. LEAVE", h2),
        Paragraph(
            "5.1 The Company offers <b>unlimited paid time off (PTO)</b> subject to manager "
            "approval and business needs. There is no formal accrual.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("6. TERMINATION", h2),
        Paragraph(
            "6.1 <b>Notice by Employee</b>: The Employee shall provide <b>thirty (30) "
            "calendar days</b> written notice prior to resignation.",
            body,
        ),
        Paragraph(
            "6.2 <b>Notice by Company</b>: The Company shall provide thirty (30) calendar "
            "days written notice or pay in lieu.",
            body,
        ),
        Paragraph(
            "6.3 <b>Immediate Termination</b>: Either party may terminate immediately for cause.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("7. CONFIDENTIALITY", h2),
        Paragraph(
            "7.1 Standard confidentiality obligations apply during employment and for "
            "<b>two (2) years</b> post-termination.",
            body,
        ),
        Spacer(1, 8),

        PageBreak(),
        Paragraph("8. INTELLECTUAL PROPERTY", h2),
        Paragraph(
            "8.1 All work product created during employment belongs to the Company.",
            body,
        ),
        Paragraph(
            "8.2 <b>Side Projects</b>: The Employee must obtain written approval from "
            "the Company before engaging in any paid consulting or side projects, "
            "regardless of whether Company resources are used.",  # stricter than Contract A
            body,
        ),
        Spacer(1, 8),

        Paragraph("9. SERVICE COMMITMENT", h2),
        Paragraph(
            "9.1 If the Employee voluntarily terminates employment within <b>eighteen (18) "
            "months</b> of the Effective Date, the Employee shall repay to the Company a "
            "pro-rated portion of the signing bonus (if any) received.",  # MISSING: signing bonus not mentioned
            body,
        ),
        Spacer(1, 8),

        Paragraph("10. NON-COMPETE", h2),
        Paragraph(
            "10.1 There is no non-compete restriction. The Employee is free to work for "
            "any employer after termination.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("11. DISPUTE RESOLUTION", h2),
        Paragraph(
            "11.1 Disputes shall be resolved through mediation in New York, New York. "
            "If mediation fails, disputes shall be submitted to the courts of New York.",
            body,
        ),
        Paragraph(
            "11.2 This Agreement is governed by the laws of the State of New York.",
            body,
        ),
        Spacer(1, 24),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
        Spacer(1, 12),
        Paragraph(
            "<b>NEXUS LABS INC.</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Name: Marcus Webb<br/>"
            "Title: Chief Executive Officer<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph(
            "<b>EMPLOYEE</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Name: Jordan Riley<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
    ]

    doc.build(story)
    print(f"  Generated: employment-contract-b.pdf")


# ─────────────────────────────────────────────────────────────
# Document 3: NDA
# ─────────────────────────────────────────────────────────────

def generate_nda():
    doc = _doc("nda-sample.pdf", "Non-Disclosure Agreement — Sample")
    h1, h2, body, warning = _styles()

    story = [
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
        Spacer(1, 6),
        Paragraph("MUTUAL NON-DISCLOSURE AGREEMENT", h1),
        Paragraph(
            "This Mutual Non-Disclosure Agreement (\"Agreement\") is entered into as of "
            "April 1, 2025, between <b>TechCo Inc.</b> (\"Party A\") and "
            "<b>InnovateCo Ltd.</b> (\"Party B\"), collectively referred to as the \"Parties\".",
            body,
        ),
        Spacer(1, 12),

        Paragraph("1. PURPOSE", h2),
        Paragraph(
            "The Parties wish to explore a potential business relationship and may disclose "
            "confidential information to each other. This Agreement governs such disclosures.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("2. DEFINITION OF CONFIDENTIAL INFORMATION", h2),
        Paragraph(
            "2.1 \"Confidential Information\" means any information disclosed by one Party "
            "(\"Disclosing Party\") to the other (\"Receiving Party\") that is marked as "
            "confidential or that a reasonable person would consider confidential.",
            body,
        ),
        Paragraph(
            "2.2 Confidential Information does not include information that: "
            "(a) is or becomes publicly available through no breach of this Agreement; "
            "(b) was rightfully known to the Receiving Party prior to disclosure; "
            "(c) is received from a third party without restriction; or "
            "(d) is independently developed by the Receiving Party.",
            body,
        ),
        Spacer(1, 8),

        PageBreak(),
        Paragraph("3. OBLIGATIONS", h2),
        Paragraph(
            "3.1 Each Receiving Party shall: (a) hold the Confidential Information in strict "
            "confidence; (b) not disclose it to third parties without prior written consent; "
            "and (c) use it solely for evaluating the potential business relationship.",
            body,
        ),
        Paragraph(
            "3.2 The Receiving Party may disclose Confidential Information to its employees "
            "and advisors on a need-to-know basis, provided such persons are bound by "
            "confidentiality obligations no less restrictive than those herein.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("4. TERM", h2),
        Paragraph(
            "4.1 This Agreement shall remain in effect for a period of <b>two (2) years</b> "
            "from the date of execution.",
            body,
        ),
        Paragraph(
            "4.2 Obligations regarding Confidential Information disclosed during the term "
            "shall survive for <b>three (3) years</b> after disclosure.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("5. RETURN OF INFORMATION", h2),
        Paragraph(
            "5.1 Upon request or termination of this Agreement, each Receiving Party shall "
            "promptly return or destroy all Confidential Information of the Disclosing Party.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("6. NO LICENSE", h2),
        Paragraph(
            "6.1 Nothing in this Agreement grants any license or right to use any "
            "Confidential Information except as expressly permitted herein.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("7. REMEDIES", h2),
        Paragraph(
            "7.1 The Parties acknowledge that breach of this Agreement may cause "
            "irreparable harm and that the Disclosing Party shall be entitled to seek "
            "injunctive relief in addition to any other remedies.",
            body,
        ),
        Spacer(1, 8),

        PageBreak(),
        Paragraph("8. GOVERNING LAW", h2),
        Paragraph(
            "8.1 This Agreement shall be governed by the laws of the State of Delaware.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("9. ENTIRE AGREEMENT", h2),
        Paragraph(
            "9.1 This Agreement constitutes the entire agreement between the Parties "
            "regarding confidentiality and supersedes all prior agreements on this subject.",
            body,
        ),
        Spacer(1, 24),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
        Spacer(1, 12),
        Paragraph(
            "<b>TECHCO INC.</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph(
            "<b>INNOVATECO LTD.</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
    ]

    doc.build(story)
    print(f"  Generated: nda-sample.pdf")


# ─────────────────────────────────────────────────────────────
# Document 4: Rental Agreement
# ─────────────────────────────────────────────────────────────

def generate_rental():
    doc = _doc("rental-agreement-sample.pdf", "Residential Lease Agreement — Sample")
    h1, h2, body, warning = _styles()

    story = [
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
        Spacer(1, 6),
        Paragraph("RESIDENTIAL LEASE AGREEMENT", h1),
        Paragraph(
            "This Residential Lease Agreement (\"Lease\") is entered into on May 1, 2025, "
            "between <b>PropertyCo LLC</b> (\"Landlord\") and <b>Alex Morgan</b> (\"Tenant\").",
            body,
        ),
        Spacer(1, 12),

        Paragraph("1. PREMISES", h2),
        Paragraph(
            "1.1 The Landlord agrees to lease to the Tenant the residential property "
            "located at <b>42 Maple Street, Apartment 3B, Chicago, IL 60601</b> "
            "(\"Premises\").",
            body,
        ),
        Spacer(1, 8),

        Paragraph("2. TERM", h2),
        Paragraph(
            "2.1 The lease term shall commence on May 1, 2025, and shall terminate on "
            "<b>April 30, 2026</b>, unless terminated earlier in accordance with this Lease.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("3. RENT", h2),
        Paragraph(
            "3.1 The Tenant agrees to pay monthly rent of <b>USD 2,400 (Two Thousand "
            "Four Hundred US Dollars)</b> due on the first day of each month.",
            body,
        ),
        Paragraph(
            "3.2 <b>Late Fee</b>: A late fee of USD 100 shall apply if rent is received "
            "after the 5th day of the month.",
            body,
        ),
        Paragraph(
            "3.3 <b>Rent Increases</b>: The Landlord may increase rent upon lease renewal "
            "with <b>sixty (60) days</b> written notice.",
            body,
        ),
        Spacer(1, 8),

        PageBreak(),
        Paragraph("4. SECURITY DEPOSIT", h2),
        Paragraph(
            "4.1 The Tenant shall pay a security deposit of <b>USD 4,800</b> (equal to "
            "two months' rent) prior to occupancy.",
            body,
        ),
        Paragraph(
            "4.2 The deposit shall be returned within <b>thirty (30) days</b> of "
            "lease termination, less any deductions for damage beyond normal wear and tear.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("5. UTILITIES", h2),
        Paragraph(
            "5.1 The Tenant is responsible for the following utilities: electricity, "
            "internet, and cable. Water and trash are included in the rent.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("6. PETS", h2),
        Paragraph(
            "6.1 <b>No pets are permitted</b> on the Premises without prior written "
            "consent of the Landlord.",
            body,
        ),
        Paragraph(
            "6.2 An additional pet deposit of USD 500 per pet is required if consent is granted.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("7. SUBLETTING", h2),
        Paragraph(
            "7.1 The Tenant may not sublet the Premises or any part thereof without "
            "prior written consent of the Landlord, which shall not be unreasonably withheld.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("8. MAINTENANCE", h2),
        Paragraph(
            "8.1 The Landlord shall maintain the Premises in habitable condition and "
            "shall be responsible for structural repairs.",
            body,
        ),
        Paragraph(
            "8.2 The Tenant shall be responsible for minor repairs costing less than "
            "<b>USD 150</b> per incident.",
            body,
        ),
        Spacer(1, 8),

        PageBreak(),
        Paragraph("9. TERMINATION", h2),
        Paragraph(
            "9.1 <b>Notice by Tenant</b>: The Tenant must provide <b>thirty (30) days</b> "
            "written notice to vacate. Failure to provide notice may result in forfeiture "
            "of the security deposit.",
            body,
        ),
        Paragraph(
            "9.2 <b>Early Termination</b>: The Tenant may terminate early by paying a "
            "fee equal to <b>two months' rent</b> and providing thirty (30) days notice.",
            body,
        ),
        Spacer(1, 8),

        Paragraph("10. GOVERNING LAW", h2),
        Paragraph(
            "10.1 This Lease shall be governed by the laws of the State of Illinois.",
            body,
        ),
        Spacer(1, 24),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
        Spacer(1, 12),
        Paragraph(
            "<b>LANDLORD</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Name: PropertyCo LLC<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph(
            "<b>TENANT</b><br/><br/>"
            "Signed: ___________________________<br/>"
            "Name: Alex Morgan<br/>"
            "Date: _____________________________",
            body,
        ),
        Spacer(1, 12),
        Paragraph("[SYNTHETIC DOCUMENT — NOT LEGAL ADVICE]", warning),
    ]

    doc.build(story)
    print(f"  Generated: rental-agreement-sample.pdf")


if __name__ == "__main__":
    print("Generating synthetic legal documents for ClausePilot development...")
    print("NOTE: These are fictional documents for testing only. NOT legal advice.\n")

    generate_employment_a()
    generate_employment_b()
    generate_nda()
    generate_rental()

    print(f"\nAll documents generated in: {OUTPUT_DIR}")
    print("\nDeliberate test features embedded:")
    print("  - employment-contract-a.pdf: CONFLICT in clauses 4.2 vs 9.1 (remote/office)")
    print("  - employment-contract-a.pdf: AMBIGUOUS bonus formula (clause 2.2)")
    print("  - employment-contract-a.pdf: MISSING stock option vesting details")
    print("  - employment-contract-b.pdf: Explicit bonus formula and vesting (for comparison)")
    print("  - employment-contract-b.pdf: Stricter side-project clause vs Contract A")
    print("  - employment-contract-b.pdf: Service commitment references missing signing bonus")
    print("  - nda-sample.pdf: Different term durations (2-year agreement vs 3-year obligation)")
