import json,unittest,hashlib
from pathlib import Path
from urllib.robotparser import RobotFileParser
ROOT=Path(__file__).resolve().parents[1]
POLICY='https://daytonkristin.github.io/veriproof/rights.html'
class SelectiveDisclosureTests(unittest.TestCase):
    def test_all_discovery_surfaces_link_same_rights_policy(self):
        for f in ('veriproof/index.html','veriproof/assumption-drift.html','veriproof/rights.html','veriproof/templates/index.html'):
            raw=(ROOT/f).read_text()
            self.assertIn('name="tdm-policy" content="'+POLICY+'"',raw,f)
            self.assertIn('All rights reserved',raw,f)
        self.assertIn(POLICY,(ROOT/'veriproof/llms.txt').read_text())
        self.assertEqual(json.loads((ROOT/'.well-known/agent.json').read_text())['rights']['policy_url'],POLICY)
    def test_tdm_scope_includes_machine_descriptor(self):
        rules=json.loads((ROOT/'.well-known/tdmrep.json').read_text())
        self.assertEqual({r['location'] for r in rules},{'/veriproof/','/.well-known/agent.json'})
        self.assertTrue(all(r['tdm-reservation']==1 and r['tdm-policy']==POLICY for r in rules))
    def test_path_copy_does_not_contradict_root_policy(self):
        for f in ('robots.txt','veriproof/robots.txt'):
            p=RobotFileParser();p.parse((ROOT/f).read_text().splitlines())
            for bot in ('GPTBot','Google-Extended','ClaudeBot','CCBot','Bytespider','Amazonbot','Applebot-Extended'):
                self.assertFalse(p.can_fetch(bot,POLICY))
            for bot in ('Googlebot','Bingbot','OAI-SearchBot','ChatGPT-User','Claude-SearchBot'):
                self.assertTrue(p.can_fetch(bot,POLICY))
    def test_no_checkout_or_sample_mutation(self):
        a=json.loads((ROOT/'.well-known/agent.json').read_text())
        self.assertIsNone(a['offers'][0]['payment']['checkout_url'])
        self.assertFalse(a['offers'][0]['delivery']['automated_live'])
        self.assertEqual(hashlib.sha256((ROOT/'veriproof/assumption-drift-sample.json').read_bytes()).hexdigest(),'5b74adeb56e4d9c98059f1dc9a60bbc67eef7f1ae0ea3e08edda5587f963d352')
    def test_security_contact_is_not_testing_authorization(self):
        raw=(ROOT/'.well-known/security.txt').read_text()
        self.assertIn('Contact: mailto:ailoopguard.support@gmail.com',raw)
        self.assertIn('Expires:',raw)
        self.assertIn('no authorization',raw.lower())
