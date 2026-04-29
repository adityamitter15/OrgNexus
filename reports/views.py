# File: reports/views.py - Aditya Mitter (W19869650)
"""PDF + Excel exports plus a 'teams without managers' helper.

Closes one of the brief's optional functional groups (Reports). PDFs
use reportlab and XLSX uses openpyxl - both are pure-Python so the
marker can run them without extra setup.
"""

from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from organisation.models import Department
from teams.models import Team

from .models import Project


@login_required
def report_index(request):
    """Page that links to PDF / XLSX / orphan-teams downloads."""
    return render(request, "reports/report_index.html")


@login_required
def teams_without_managers(request):
    """The brief lists 'teams without managers' as one of the canned
    reports we should expose."""
    qs = Team.objects.filter(manager__isnull=True).select_related("department")
    return render(
        request,
        "reports/teams_without_managers.html",
        {"teams": qs},
    )


@login_required
def pdf_report(request):
    """Single-shot PDF: dept-by-dept summary table + projects per dept."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("OrgNexus - Engineering portal report", styles["Title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "This report summarises the structure of Sky's engineering "
            "registry as captured in OrgNexus.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 0.6 * cm))

    # Department summary table.
    rows = [["Department", "Teams", "Projects"]]
    depts = (
        Department.objects.annotate(
            num_teams=Count("teams", distinct=True),
            num_projects=Count("projects", distinct=True),
        ).order_by("name")
    )
    for d in depts:
        rows.append([d.name, str(d.num_teams), str(d.num_projects)])

    table = Table(rows, colWidths=[8 * cm, 3 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B4965")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(table)

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("Teams without a manager", styles["Heading2"]))
    orphans = Team.objects.filter(manager__isnull=True).select_related("department")
    if not orphans.exists():
        story.append(Paragraph("None - every team currently has a manager.",
                               styles["BodyText"]))
    else:
        rows = [["Team", "Department"]]
        for t in orphans:
            rows.append([t.name, t.department.name])
        ot = Table(rows, colWidths=[8 * cm, 6 * cm])
        ot.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B4965")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ]
            )
        )
        story.append(ot)

    doc.build(story)
    buffer.seek(0)

    resp = HttpResponse(buffer.read(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="orgnexus_report.pdf"'
    return resp


@login_required
def xlsx_report(request):
    """Same data as the PDF, but in a workbook the user can pivot."""

    wb = Workbook()
    ws = wb.active
    ws.title = "Departments"
    ws.append(["Department", "Teams", "Projects"])
    for d in Department.objects.annotate(
        num_teams=Count("teams", distinct=True),
        num_projects=Count("projects", distinct=True),
    ).order_by("name"):
        ws.append([d.name, d.num_teams, d.num_projects])

    ws2 = wb.create_sheet("Teams")
    ws2.append(["Team", "Department", "Manager", "Type", "Members"])
    for t in Team.objects.select_related("department", "manager", "team_type"):
        ws2.append(
            [
                t.name,
                t.department.name,
                t.manager.get_display_name() if t.manager else "",
                t.team_type.type_name if t.team_type else "",
                t.member_count(),
            ]
        )

    ws3 = wb.create_sheet("Projects")
    ws3.append(["Project", "Department", "Status", "Lead"])
    for p in Project.objects.select_related("department", "lead"):
        ws3.append(
            [
                p.name,
                p.department.name,
                p.get_status_display(),
                p.lead.get_display_name() if p.lead else "",
            ]
        )

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    resp = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="orgnexus_report.xlsx"'
    return resp
