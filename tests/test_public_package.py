"""Portable package checks; no model calls, presentation generation or network access."""
import ast
import csv
import json
from pathlib import Path
import re
import struct
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class PublicPackageTests(unittest.TestCase):
    def test_core_layout(self):
        for name in ['SKILL.md', 'README.md', 'README.zh-CN.md', 'LICENSE', 'MANIFEST.md',
                     'references/platform-contract.md', 'references/audience-content.md',
                     'references/cover-and-navigation.md', 'assets/job-contract.json',
                     'assets/frontmatter-contract.json', 'assets/platform-contract.json']:
            self.assertTrue((ROOT / name).is_file(), name)
        scripts = {p.name for p in (ROOT / 'scripts').glob('*') if p.is_file()}
        self.assertEqual(scripts, {'preflight.py', 'inspect_deck.py', 'audit_pptx.py',
                                   'check_fonts.py', 'build_deck.mjs', 'apply_ooxml_styles.py'})

    def test_local_markdown_links(self):
        for source in ROOT.rglob('*.md'):
            if '.git' in source.parts:
                continue
            for target in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
                if re.match(r'\w+://|#', target):
                    continue
                local = (source.parent / target.split('#', 1)[0]).resolve()
                self.assertTrue(local.exists(), f'{source.name}: {target}')

    def test_json_csv_templates(self):
        for source in ROOT.rglob('*.json'):
            if '.git' not in source.parts:
                json.loads(source.read_text(encoding='utf-8'))
        for source in (ROOT / 'assets').glob('*.csv'):
            header = next(csv.reader(source.read_text(encoding='utf-8').splitlines()))
            self.assertEqual(len(header), len(set(header)), source.name)
        job = json.loads((ROOT / 'assets/job-contract.json').read_text(encoding='utf-8'))
        self.assertTrue({'platform_contract', 'frontmatter_contract', 'audience_review'} <= job.keys())

    def test_python_syntax(self):
        for source in ROOT.rglob('*.py'):
            if '.git' not in source.parts:
                ast.parse(source.read_text(encoding='utf-8'), filename=str(source))

    def test_branding_and_host_metadata(self):
        for name in ['icon.svg', 'banner.svg']:
            root = ET.parse(ROOT / 'assets' / name).getroot()
            self.assertTrue(root.tag.endswith('svg'))
            self.assertNotIn('<script', (ROOT / 'assets' / name).read_text(encoding='utf-8'))
        png = (ROOT / 'assets/icon.png').read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', png[16:24]), (1024, 1024))
        metadata = (ROOT / 'agents/openai.yaml').read_text(encoding='utf-8')
        for path in ['./assets/icon.svg', './assets/icon.png']:
            self.assertIn(path, metadata)
            self.assertTrue((ROOT / path).is_file())
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(skill.startswith('---\n'))
        self.assertIn('name: research-ppt-sop', skill)
        self.assertIn('icon: assets/icon.png', skill)

    def test_review_examples_preserve_scope(self):
        examples = json.loads((ROOT / 'assets/revision-examples.json').read_text(encoding='utf-8'))['examples']
        by_id = {example['id']: example for example in examples}
        self.assertEqual(len(by_id), 5)
        for example in examples:
            for key in ['source_facts', 'after', 'keep', 'reason']:
                self.assertTrue(example[key], example['id'])
        valid = by_id['preserve_valid_scientific_qualification']
        self.assertEqual(valid['before'], valid['after'])
        separate = by_id['classification_not_updated_angle_readouts']['after']
        self.assertIn('Classifier-A', separate)
        self.assertIn('AngleEstimator-B', separate)
        self.assertIn('未更新方位预测', separate)


if __name__ == '__main__':
    unittest.main()
