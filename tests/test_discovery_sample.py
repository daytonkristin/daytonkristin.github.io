import json
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,parse_qs
ROOT=Path(__file__).resolve().parents[1]/'veriproof'
class Sample(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows=[]
        self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr' and 'data-case' in a:
            self.rows.append(a)
        if tag=='a':
            self.links.append(a.get('href',''))
class DiscoveryTests(unittest.TestCase):
    def test_public_sample_exhausts_boolean_domain_and_exposes_one_mismatch(self):
        p=Sample()
        p.feed((ROOT/'assumption-drift.html').read_text())
        self.assertEqual(len(p.rows),4)
        seen=set()
        mismatches=0
        for r in p.rows:
            paid,refunded=map(int,r['data-case'].split(','))
            seen.add((paid,refunded))
            expected=int(bool(paid and not refunded))
            flawed=paid
            self.assertEqual(int(r['data-expected']),expected)
            self.assertEqual(int(r['data-observed']),flawed)
            mismatches+=expected!=flawed
        self.assertEqual(seen,{(0,0),(0,1),(1,0),(1,1)})
        self.assertEqual(mismatches,1)
    def test_reference_visible_and_in_voluntary_contact_link(self):
        raw=(ROOT/'assumption-drift.html').read_text()
        marker=re.search(r'VP-AD-SYN-[A-F0-9]{24}',raw)
        self.assertIsNotNone(marker)
        self.assertIn('Public sample reference: '+marker.group(),raw)
        p=Sample();p.feed(raw)
        contacts=[parse_qs(urlsplit(x).query) for x in p.links if x.startswith('mailto:')]
        self.assertTrue(any(c.get('subject')==['VERIPROOF AUDIT PILOT'] and marker.group() in c.get('body',[''])[0] for c in contacts))
    def test_discovery_catalog_links_the_same_paid_pilot(self):
        raw=(ROOT/'llms.txt').read_text()
        self.assertIn('Assumption Drift & Policy Audit Pilot — $299',raw)
        self.assertIn('https://daytonkristin.github.io/veriproof/assumption-drift.html',raw)
    def test_demo_is_disclosed_and_not_proprietary(self):
        raw=(ROOT/'assumption-drift.html').read_text()
        self.assertIn('Fictional teaching example, not production code',raw)
        self.assertIn('Reuse of the reference is not proof of unauthorized access',raw)
        self.assertNotIn('RFC 3161 verified',raw)
if __name__=='__main__':unittest.main()
