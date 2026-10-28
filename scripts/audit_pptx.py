#!/usr/bin/env python3
"""Audit existing PPTX relationships and referenced charts/notes without modifying the presentation."""
import argparse
import json
from pathlib import Path
import posixpath
from zipfile import BadZipFile, ZipFile

from inspect_deck import NS, relationships, xml

CHART = "{http://schemas.openxmlformats.org/drawingml/2006/chart}chart"
RID = "{" + NS["r"] + "}id"


def owner_of_relationship_part(part):
    if part == "_rels/.rels":
        return ""
    folder, name = posixpath.split(part)
    if posixpath.basename(folder) != "_rels":
        raise ValueError("Invalid relationship part location: " + part)
    return posixpath.join(posixpath.dirname(folder), name[:-5])


def audit(source):
    with ZipFile(source) as archive:
        members = set(archive.namelist())
        missing = []
        external = 0
        checked = 0
        for part in sorted(members):
            if not part.endswith(".rels"):
                continue
            owner = owner_of_relationship_part(part)
            if owner and owner not in members:
                missing.append({"relationship_part": part, "missing_owner": owner})
            for relation in xml(archive, part):
                checked += 1
                if relation.get("TargetMode") == "External":
                    external += 1
                    continue
                target = relation.get("Target", "")
                resolved = target.lstrip("/") if target.startswith("/") else posixpath.normpath(
                    posixpath.join(posixpath.dirname(owner), target))
                if not target or resolved not in members:
                    missing.append({"relationship_part": part, "target": resolved})
        presentation = xml(archive, "ppt/presentation.xml")
        order = presentation.findall("p:sldIdLst/p:sldId", NS)
        slide_relations = relationships(archive, "ppt/presentation.xml")
        slides = []
        all_charts = set()
        all_workbooks = set()
        all_notes = set()
        for index, slide_id in enumerate(order, 1):
            relation = slide_relations.get(slide_id.get(RID), {})
            part = relation.get("target")
            if relation.get("external") or part not in members:
                missing.append({"slide": index, "issue": "slide_relationship_unresolved"})
                continue
            root = xml(archive, part)
            local = relationships(archive, part)
            charts = []
            notes = []
            for chart in root.iter(CHART):
                linked = local.get(chart.get(RID), {})
                chart_part = linked.get("target")
                if linked.get("external") or chart_part not in members or linked.get("type") != "chart":
                    missing.append({"slide": index, "issue": "chart_relationship_unresolved", "id": chart.get(RID)})
                    continue
                xml(archive, chart_part)
                workbook_parts = []
                for link in relationships(archive, chart_part).values():
                    if link["type"] == "package" and not link["external"]:
                        workbook_parts.append(link["target"])
                charts.append({"part": chart_part, "embedded_workbooks": workbook_parts})
                all_charts.add(chart_part)
                all_workbooks.update(workbook_parts)
            for linked in local.values():
                if linked["type"] == "notesSlide" and not linked["external"]:
                    notes.append(linked["target"])
                    if linked["target"] in members:
                        xml(archive, linked["target"])
                    all_notes.add(linked["target"])
            slides.append({"slide": index, "part": part, "charts": charts, "notes_parts": notes})
        return {
            "file": str(source), "slide_count": len(order), "zip_parts": len(members),
            "checked_relationships": checked, "external_relationship_count": external,
            "missing_internal_relationships": missing,
            "referenced_chart_count": len(all_charts), "referenced_workbook_count": len(all_workbooks),
            "referenced_notes_count": len(all_notes), "slides": slides,
            "structural_pass": not missing,
            "limits": ["No scientific, numeric or visual judgment is made.",
                       "External relationships are counted, not fetched or validated.",
                       "Object-level editability requires the separate requirements inspection.",
                       "Office rendering and GUI editing are not performed."],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing PPTX to inspect; never modified")
    parser.add_argument("--out", type=Path, help="Optional new JSON report; existing files are rejected")
    args = parser.parse_args()
    source = args.source.resolve()
    if args.out and args.out.resolve() == source:
        parser.error("The report path must differ from the input presentation.")
    try:
        report = audit(source)
    except (BadZipFile, KeyError, ValueError, OSError) as error:
        print(json.dumps({"structural_pass": False, "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
    summary = {key: value for key, value in report.items() if key != "slides"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not report["structural_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
