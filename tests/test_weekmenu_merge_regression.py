import sys,unittest
sys.path.insert(0,'src')
from weekmenu_advies import _cost_of_lines
from test_weekmenu_advies import line
class MergeRegression(unittest.TestCase):
 def test_same_sku_different_effective_bundle_average(self):
  action={'multi_buy_quantity':2,'multi_buy_price':3,'price':1.5,'original_price':3,'url':'https://example.org/p'}
  a=line('spinazie',200,500,3,action)
  b=line('spinazie',600,500,1.5,action)
  basket=_cost_of_lines([a,b])
  self.assertEqual(len(basket['products']),1)
  self.assertEqual(basket['checkout'],3)
  self.assertEqual(basket['products'][0]['packages'],2)
