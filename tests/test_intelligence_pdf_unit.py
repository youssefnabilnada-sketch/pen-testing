"""No external data: bounded, safe advisory-match PDF reporting."""
import unittest
from io import BytesIO
from pypdf import PdfReader
from aegis.reporting import render_intelligence_pdf


class IntelligencePDFTests(unittest.TestCase):
    def read(self, inventory=None, impacts=None):
        pdf = render_intelligence_pdf('test-org', inventory or [], impacts or [], generated_at=0).getvalue()
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertLess(len(pdf), 500_000)
        return ' '.join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)

    def test_no_matches_never_claims_clean_system(self):
        result = self.read()
        self.assertIn('No recorded advisory matches', result)
        self.assertIn('not evidence of absence of risk', result)
        self.assertIn('not an AEGIS security certification', result)

    def test_inventory_matches_are_labeled_unverified(self):
        result = self.read(
            [{'ecosystem':'npm','package':'foo','version':'2.0','asset_id':'asset-1'}],
            [{'identifier':'CVE-TEST','status':'potentially_affected',
              'asset_id':'asset-1','reason':'customer-declared version match'}])
        self.assertIn('CVE-TEST', result)
        self.assertIn('potentially_affected', result)
        self.assertIn('package and version matches alone do not prove', result)

    def test_markup_and_missing_refs_are_safe(self):
        hostile = '<img src="file:///etc/passwd">' * 100
        result = self.read([{'package':hostile,'ecosystem':'npm','asset_id':None}],
                           [{'identifier':None,'asset_id':None,'status':'unverified','reason':hostile}])
        self.assertIn('unavailable', result)
        self.assertNotIn('/etc/passwd/', result)

    def test_snapshot_is_bounded_to_one_hundred_items(self):
        inventory = [{'ecosystem':'npm','package':f'item-{i}','version':'1', 'asset_id':None}
                     for i in range(150)]
        result = self.read(inventory, [])
        self.assertIn('Inventory rows included: 100', result)
        self.assertNotIn('item-149', result)


if __name__ == '__main__':
    unittest.main()
