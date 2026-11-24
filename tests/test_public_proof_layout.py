import hashlib
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'veriproof'
class PublicProofTests(unittest.TestCase):
    def test_visible_proof_boundaries_and_digest(self):
        page=(ROOT/'assumption-drift.html').read_text()
        for heading in ('1. Failure mode','2. Minimal reproduction','3. Verification record','4. Bounded audit pilot'):
            self.assertIn(heading,page)
        self.assertIn(hashlib.sha256((ROOT/'assumption-drift-sample.json').read_bytes()).hexdigest(),page)
        self.assertIn('Integrity does not establish correctness',page)
        self.assertIn('Scope review required before payment',page)
