import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.robotparser import RobotFileParser
ROOT = Path(__file__).resolve().parents[1]
class HeadMeta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        if tag == 'head': self.in_head = True
        if tag == 'meta' and self.in_head:
            a = dict(attrs)
            self.meta.setdefault(a.get('name'), []).append(a.get('content'))
    def handle_endtag(self, tag):
        if tag == 'head': self.in_head = False
class RightsPolicyTests(unittest.TestCase):
    def test_root_policy_blocks_named_training_bots_and_preserves_search(self):
        p=RobotFileParser()
        p.parse((ROOT/'robots.txt').read_text().splitlines())
        url='https://daytonkristin.github.io/veriproof/'
        for bot in ('GPTBot','Google-Extended','ClaudeBot','CCBot','Bytespider','Amazonbot','Applebot-Extended'):
            self.assertFalse(p.can_fetch(bot,url),bot)
        for bot in ('Googlebot','Bingbot','OAI-SearchBot','ChatGPT-User','Claude-User','Perplexity-User'):
            self.assertTrue(p.can_fetch(bot,url),bot)
    def test_tdm_reservation_is_scoped_to_storefront(self):
        self.assertEqual(json.loads((ROOT/'.well-known/tdmrep.json').read_text()),[{'location':'/veriproof/','tdm-reservation':1}])
    def test_jekyll_includes_well_known(self):
        self.assertIn('".well-known"',(ROOT/'_config.yml').read_text())
    def test_all_storefront_heads_reserve_tdm_without_claiming_a_timestamp(self):
        for name in ('veriproof/templates/index.html','veriproof/index.html','veriproof/assumption-drift.html'):
            h=HeadMeta()
            raw=(ROOT/name).read_text()
            h.feed(raw)
            self.assertEqual(h.meta.get('tdm-reservation'),['1'],name)
            self.assertNotIn('RFC 3161 verified',raw)
if __name__=='__main__':unittest.main()
