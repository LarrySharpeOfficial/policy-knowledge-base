import hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_build():
 spec=importlib.util.spec_from_file_location('policy_build',ROOT/'scripts'/'build.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
class PolicyBuildTests(unittest.TestCase):
 def run_build(self): subprocess.run([sys.executable,str(ROOT/'scripts'/'build.py')],check=True,capture_output=True,text=True)
 def test_build_and_checksum(self):
  self.run_build(); payload=(ROOT/'dist'/'policy-snapshot-v0.1.0.json').read_bytes(); manifest=json.loads((ROOT/'dist'/'manifest.json').read_text()); self.assertEqual(hashlib.sha256(payload).hexdigest(),manifest['sha256']); self.assertEqual(manifest['policy_count'],3)
 def test_snapshot_is_deterministic(self):
  self.run_build(); first=(ROOT/'dist'/'policy-snapshot-v0.1.0.json').read_bytes(); self.run_build(); self.assertEqual(first,(ROOT/'dist'/'policy-snapshot-v0.1.0.json').read_bytes())
 def test_records_are_approved_published_and_sourced(self):
  mod=load_build(); policies=[mod.load_policy(p) for p in sorted((ROOT/'content'/'policies').glob('*.md'))]; self.assertTrue(all(p['editorial_status']=='approved' and p['publication_status']=='published' for p in policies)); self.assertTrue(all(p['sources'] and all(s['timestamp_url'] for s in p['sources']) for p in policies))
 def test_accessible_fallback_and_local_fetch(self):
  self.run_build(); text=(ROOT/'dist'/'index.html').read_text(); js=(ROOT/'dist'/'assets'/'app.js').read_text();
  for marker in ('href="#main"','role="status"','<noscript>','<label for="policy-search"'): self.assertIn(marker,text)
  self.assertIn('fetch("policy-snapshot-v0.1.0.json")',js); self.assertNotIn('https://',js)
if __name__=='__main__': unittest.main()
