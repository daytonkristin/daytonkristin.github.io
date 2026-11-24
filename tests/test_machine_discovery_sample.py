import json,unittest
from pathlib import Path
from test_discovery_sample import Sample
ROOT=Path(__file__).resolve().parents[1]/'veriproof'
class MachineDiscoveryTests(unittest.TestCase):
    def test_machine_sample_matches_human_sample_and_scope(self):
        sample=json.loads((ROOT/'assumption-drift-sample.json').read_text())
        page=(ROOT/'assumption-drift.html').read_text()
        h=Sample();h.feed(page)
        self.assertEqual(sample['kind'],'synthetic_teaching_example')
        self.assertIn(sample['sample_reference'],page)
        self.assertEqual(sample['offer']['amount_cents'],29900)
        self.assertEqual(sample['offer']['currency'],'USD')
        self.assertEqual(sample['offer']['max_rules'],10)
        self.assertEqual(sample['offer']['integrations'],1)
        self.assertEqual(sample['offer']['acceptance'],'scope_review_required')
        expected=[{'paid':bool(int(row['data-case'].split(',')[0])),
                   'refunded':bool(int(row['data-case'].split(',')[1])),
                   'expected_allow':bool(int(row['data-expected'])),
                   'illustrative_allow':bool(int(row['data-observed']))} for row in h.rows]
        self.assertEqual(sample['cases'],expected)
        self.assertEqual(sum(c['expected_allow']!=c['illustrative_allow'] for c in sample['cases']),1)
        self.assertFalse(sample['live_customer_finding'])
        self.assertFalse(sample['checkout_active'])
    def test_discoverable_from_existing_public_catalog(self):
        self.assertIn('https://daytonkristin.github.io/veriproof/assumption-drift-sample.json',(ROOT/'llms.txt').read_text())
        self.assertIn('href="assumption-drift-sample.json"',(ROOT/'assumption-drift.html').read_text())
