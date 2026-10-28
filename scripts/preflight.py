#!/usr/bin/env python3
"""Read-only capability discovery. Does not install, download, render or create a PPTX."""
import argparse
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


def package_status(module, distribution):
    available = importlib.util.find_spec(module) is not None
    version = None
    if available:
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            pass
    return {"available": available, "version": version}


def inspect_node_project(project, node):
    if project is None:
        return {"checked": False, "reason": "Pass --node-project to check the generation dependency."}
    if node is None:
        return {"checked": False, "reason": "Node executable not found."}
    project = project.resolve()
    if not project.is_dir():
        return {"checked": False, "reason": "Node project directory does not exist.", "project": str(project)}
    # Read package metadata from the resolved entry. Some versions do not export package.json.
    code = r"""
const fs = require('node:fs');
const path = require('node:path');
try {
  const entry = require.resolve('pptxgenjs');
  let directory = path.dirname(entry);
  let metadata;
  for (;;) {
    const candidate = path.join(directory, 'package.json');
    if (fs.existsSync(candidate)) {
      const value = JSON.parse(fs.readFileSync(candidate, 'utf8'));
      if (value.name === 'pptxgenjs') { metadata = value; break; }
    }
    const parent = path.dirname(directory);
    if (parent === directory) throw new Error('pptxgenjs package metadata not found');
    directory = parent;
  }
  console.log(JSON.stringify({available:true,entry,version:metadata.version}));
} catch (error) {
  console.log(JSON.stringify({available:false,error:error.message}));
}
"""
    process = subprocess.run([node, "-e", code], cwd=project, capture_output=True, text=True, timeout=20)
    if process.returncode:
        return {"checked": True, "available": False, "project": str(project), "error": process.stderr.strip()}
    return {"checked": True, "project": str(project), **json.loads(process.stdout)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node-project", type=Path, help="Explicit project with an already installed pptxgenjs dependency")
    args = parser.parse_args()
    python_ok = sys.version_info >= (3, 10)
    node = shutil.which("node")
    packages = {
        "pdfplumber": package_status("pdfplumber", "pdfplumber"),
        "pypdfium2": package_status("pypdfium2", "pypdfium2"),
        "pillow": package_status("PIL", "pillow"),
    }
    try:
        pptxgenjs = inspect_node_project(args.node_project, node)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        pptxgenjs = {"checked": True, "available": False, "error": str(error)}
    report = {
        "python": {"executable": sys.executable, "version": sys.version.split()[0], "minimum_ok": python_ok},
        "node": node,
        "packages": packages,
        "pptxgenjs": pptxgenjs,
        "capabilities": {
            "pptx_object_and_relationship_audit": python_ok,
            "pdf_measurement": python_ok and packages["pdfplumber"]["available"],
            "local_pdf_preview": python_ok and packages["pdfplumber"]["available"] and packages["pypdfium2"]["available"],
            "macos_font_registry_probe": sys.platform == "darwin" and shutil.which("system_profiler") is not None,
            "scene_generation_dependency_resolved": bool(node and pptxgenjs.get("available")),
        },
        "not_checked": ["Hana App tool availability", "font families and weights", "actual Office rendering", "GUI editing", "new PPT end-to-end generation"],
        "side_effects": "none; no installation or presentation generation",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not python_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
