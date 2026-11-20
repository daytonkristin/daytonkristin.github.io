import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "veriproof" / "build_veriproof_site.py"

class StorefrontBuildTests(unittest.TestCase):
    def test_catalog_is_authoritative(self):
        catalog = json.loads((ROOT / "veriproof/products.json").read_text())
        products = {p["id"]: p for p in catalog["products"]}
        self.assertEqual(products["SignalIndex"]["price_usd"], 2500)
        self.assertEqual(products["gem-platform"]["price_usd"], 1950)
        self.assertEqual(len(products), 2)
    def test_two_tier_names_preserve_technical_ids_and_prices(self):
        catalog=json.loads((ROOT/'veriproof/products.json').read_text())
        table={p['id']:p for p in catalog['products']}
        self.assertEqual(table['gem-platform']['name'],'VeriProof AI Router')
        self.assertEqual(table['SignalIndex']['name'],'VeriProof SignalIndex')
        self.assertEqual(table['gem-platform']['price_usd'],1950)
        self.assertEqual(table['SignalIndex']['price_usd'],2500)
        self.assertEqual(table['gem-platform']['checkout_url'],'https://ailoopguard.gumroad.com/l/gruqi')
        self.assertEqual(table['SignalIndex']['checkout_url'],'https://ailoopguard.gumroad.com/l/jygsd')

    def test_catalog_has_all_existing_checkout_and_proof_urls(self):
        catalog = json.loads((ROOT / "veriproof/products.json").read_text())
        links = json.dumps(catalog)
        for url in [
            "https://ailoopguard.gumroad.com/l/gruqi",
            "https://ailoopguard.gumroad.com/l/jygsd",
            "https://github.com/daytonkristin/gem-platform-proof",
            "https://github.com/daytonkristin/signalindex-proof",
            "https://github.com/daytonkristin/gem-platform-proof/releases/tag/v1.0-proof",
            "https://github.com/daytonkristin/signalindex-proof/blob/main/sample-receipt.json",
        ]: self.assertIn(url, links)
    def test_generator_check_does_not_mutate(self):
        before = {f: (ROOT / "veriproof" / f).read_bytes() for f in
                  ("index.html", "llms.txt", "sitemap.xml", "robots.txt")}
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "--check"],
                          cwd=ROOT, capture_output=True).returncode, 0)
        after = {f: (ROOT / "veriproof" / f).read_bytes() for f in before}
        self.assertEqual(before, after)
    def test_generator_rejects_unverified_links(self):
        # A malformed catalog must not be allowed into a generated site.
        code = (ROOT / "veriproof/build_veriproof_site.py").read_text()
        self.assertIn("urlsplit", code)
    def test_launch_drafts_not_sent_or_published(self):
        code = SCRIPT.read_text()
        self.assertNotIn("requests.post(", code)
        self.assertNotIn("subprocess.run(['git', 'push'", code)
        self.assertIn("launch", code)
    def test_catalog_change_regenerates_site_without_manual_html(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'veriproof'
            shutil.copytree(ROOT/'veriproof',dst)
            c=json.loads((dst/'products.json').read_text())
            new={**c['products'][0], 'id':'FutureExample', 'name':'FutureExample',
                 'price_usd':2000}
            c['products'].append(new)
            (dst/'products.json').write_text(json.dumps(c))
            result=subprocess.run([sys.executable,str(dst/'build_veriproof_site.py')],
                                  capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('FutureExample',(dst/'index.html').read_text())
            self.assertIn('FutureExample',(dst/'llms.txt').read_text())
            self.assertIn('sitemap.xml',(dst/'robots.txt').read_text())

    def test_rejects_catalog_unsafe_urls_without_mutating_site(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'veriproof'
            shutil.copytree(ROOT/'veriproof',dst)
            c=json.loads((dst/'products.json').read_text())
            c['products'][0]['checkout_url']='javascript:alert(1)'
            (dst/'products.json').write_text(json.dumps(c))
            original=(dst/'index.html').read_bytes()
            result=subprocess.run([sys.executable,str(dst/'build_veriproof_site.py')],
                                  capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual((dst/'index.html').read_bytes(),original)

    def test_generated_assets_retains_original_design_and_disclosure(self):
        html = (ROOT/"veriproof/index.html").read_text()
        llms = (ROOT/"veriproof/llms.txt").read_text()
        self.assertIn("google-site-verification", html)
        self.assertIn("#72e8cb", html)
        self.assertIn("No latency, savings, independent security certification", html)
        self.assertIn("no independent security certification", llms)
        self.assertIn("ailoopguard.support@gmail.com", html)
        self.assertIn("Synthetic example receipt", llms)

if __name__ == "__main__": unittest.main()
