import io
import json
import logging
from typing import Any, Dict

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from lxml import etree

logger = logging.getLogger(__name__)


def export_to_excel(artifacts: dict) -> bytes:
    """Export project artifacts to Excel workbook bytes."""
    wb = openpyxl.Workbook()

    # ─── Summary sheet ──────────────────────────────────────────────────────────
    ws_summary = wb.active
    ws_summary.title = "Summary"
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="2563EB")

    ws_summary.append(["Project", artifacts.get("projectName", "")])
    ws_summary.append(["Jira Key", artifacts.get("jiraProjectKey", "")])
    ws_summary.append([])
    ws_summary.append(["Metric", "Count"])
    for col_idx, cell in enumerate(ws_summary[4], start=1):
        cell.font = header_font
        cell.fill = header_fill

    ws_summary.append(["Epics", artifacts.get("totalEpics", 0)])
    ws_summary.append(["Features", artifacts.get("totalFeatures", 0)])
    ws_summary.append(["Use Cases", artifacts.get("totalUseCases", 0)])
    ws_summary.append(["Test Cases", artifacts.get("totalTestCases", 0)])

    # ─── Test Cases sheet ───────────────────────────────────────────────────────
    ws_tc = wb.create_sheet("Test Cases")
    headers = ["Epic", "Feature", "Use Case", "Test Case ID", "Title", "Description",
               "Steps", "Expected Result", "Priority", "Jira Key", "Compliance"]
    ws_tc.append(headers)
    for cell in ws_tc[1]:
        cell.font = header_font
        cell.fill = header_fill

    for epic in artifacts.get("epics", []):
        for feature in epic.get("features", []):
            for uc in feature.get("useCases", []):
                for tc in uc.get("testCases", []):
                    steps = "\n".join(tc.get("steps", []))
                    ws_tc.append([
                        epic.get("title", ""),
                        feature.get("title", ""),
                        uc.get("title", ""),
                        tc.get("id", ""),
                        tc.get("title", ""),
                        tc.get("description", ""),
                        steps,
                        tc.get("expectedResult", ""),
                        tc.get("priority", ""),
                        tc.get("jiraIssueKey", ""),
                        ", ".join(tc.get("complianceMapping", [])),
                    ])

    # Auto-fit columns
    for ws in [ws_summary, ws_tc]:
        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_to_xml(artifacts: dict) -> bytes:
    """Export project artifacts to XML bytes."""
    root = etree.Element("Project")
    root.set("name", artifacts.get("projectName", ""))
    root.set("jiraKey", artifacts.get("jiraProjectKey", ""))

    for epic in artifacts.get("epics", []):
        epic_el = etree.SubElement(root, "Epic")
        epic_el.set("id", epic.get("id", ""))
        epic_el.set("title", epic.get("title", ""))
        epic_el.set("jiraKey", epic.get("jiraIssueKey", "") or "")

        for feature in epic.get("features", []):
            feat_el = etree.SubElement(epic_el, "Feature")
            feat_el.set("id", feature.get("id", ""))
            feat_el.set("title", feature.get("title", ""))
            feat_el.set("jiraKey", feature.get("jiraIssueKey", "") or "")

            for uc in feature.get("useCases", []):
                uc_el = etree.SubElement(feat_el, "UseCase")
                uc_el.set("id", uc.get("id", ""))
                uc_el.set("title", uc.get("title", ""))
                uc_el.set("jiraKey", uc.get("jiraIssueKey", "") or "")

                for tc in uc.get("testCases", []):
                    tc_el = etree.SubElement(uc_el, "TestCase")
                    tc_el.set("id", tc.get("id", ""))
                    tc_el.set("title", tc.get("title", ""))
                    tc_el.set("priority", tc.get("priority", ""))
                    tc_el.set("jiraKey", tc.get("jiraIssueKey", "") or "")
                    steps_el = etree.SubElement(tc_el, "Steps")
                    for step in tc.get("steps", []):
                        s = etree.SubElement(steps_el, "Step")
                        s.text = step
                    exp_el = etree.SubElement(tc_el, "ExpectedResult")
                    exp_el.text = tc.get("expectedResult", "")

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
