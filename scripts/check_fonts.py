#!/usr/bin/env python3
"""Read installed macOS font registration; do not install, download or substitute fonts."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def normalized(value):
    return ''.join(c for c in value.casefold() if c.isalnum())


def available_families(value):
    found = set()
    if isinstance(value, dict):
        if value.get('enabled') == 'yes' and value.get('valid', 'yes') == 'yes':
            for key in ['family', 'fullname', '_name']:
                if isinstance(value.get(key), str):
                    found.add(value[key])
        for child in value.values():
            found.update(available_families(child))
    elif isinstance(value, list):
        for child in value:
            found.update(available_families(child))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--families', nargs='+', default=['Microsoft YaHei', 'Times New Roman'])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'darwin':
        raise SystemExit('This font-registry probe is macOS-only; use a platform-specific verified report elsewhere.')
    process = subprocess.run(['system_profiler', 'SPFontsDataType', '-json'],
                             check=True, capture_output=True, text=True, timeout=90)
    detected = available_families(json.loads(process.stdout))
    canonical = {normalized(name) for name in detected}
    aliases = {'Microsoft YaHei': ['Microsoft YaHei', '微软雅黑'],
               'Times New Roman': ['Times New Roman'], 'Cambria Math': ['Cambria Math'],
               'PingFang SC': ['PingFang SC', '苹方-简', '苹方 简'],
               '苹方-简': ['PingFang SC', '苹方-简', '苹方 简'],
               'Heiti SC': ['Heiti SC', '黑体-简', '黑体 简']}
    available = [name for name in args.families
                 if any(normalized(alias) in canonical for alias in aliases.get(name, [name]))]
    missing = [name for name in args.families if name not in available]
    report = {'source': 'macOS system_profiler SPFontsDataType', 'availableFamilies': available,
              'missingFamilies': missing, 'requestedFamilies': args.families,
              'limits': ['Application-private or cloud-loaded fonts are not covered by this OS registry probe.',
                         'Rendering evidence is still required to verify actual font use and weight.']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if missing:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
