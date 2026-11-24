import json,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((ROOT/'.well-known/agent.json').read_text())
        self.sample=json.loads((ROOT/'veriproof/assumption-drift-sample.json').read_text())
    def test_offer_matches_existing_scope_and_public_identity(self):
        offer=self.manifest['offers'][0]
        for k in ('name','amount_cents','currency','integrations','max_rules','scope_url','contact'):
            self.assertEqual(offer[k],self.sample['offer'][k])
        self.assertEqual(self.manifest['publisher'],'VeriProof Systems')
        self.assertEqual(offer['payment']['candidate_provider'],'Stripe')
        self.assertEqual(offer['availability'],'scope_review_only')
        self.assertIsNone(offer['payment']['checkout_url'])
        self.assertIsNone(offer['delivery']['endpoint'])
        self.assertFalse(offer['delivery']['automated_live'])
    def test_free_diagnostic_is_reproducible_and_bound_to_public_sample(self):
        demo=self.manifest['diagnostic']
        self.assertEqual(demo['sample_reference'],self.sample['sample_reference'])
        self.assertEqual(demo['sha256'],hashlib.sha256((ROOT/'veriproof/assumption-drift-sample.json').read_bytes()).hexdigest())
        mismatches=[x for x in self.sample['cases'] if x['expected_allow']!=x['illustrative_allow']]
        self.assertEqual(demo['gap_count'],len(mismatches))
        self.assertEqual(demo['next_action'],'request_scope_review')
    def test_discovery_and_authority_boundaries(self):
        m=self.manifest
        self.assertIn('https://daytonkristin.github.io/.well-known/agent.json',(ROOT/'veriproof/llms.txt').read_text())
        self.assertEqual(m['schema'],'veriproof-service-discovery-v1')
        self.assertFalse(m['receipt_policy']['receipt_id_is_bearer_credential'])
        self.assertEqual(set(m['receipt_policy']['required_bindings']),{'authenticated_buyer','accepted_scope','request_sha256','provider_account','amount_currency','unique_payment_id'})
        self.assertFalse(m['receipt_policy']['public_receipt_submission'])
        raw=(ROOT/'.well-known/agent.json').read_text().lower()
        self.assertNotIn('axiom',raw)
        self.assertNotIn('cs_test_',raw)
        self.assertNotIn('pi_',raw)
