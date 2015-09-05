import json
import os

__location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

products_path = os.path.join(__location__, 'products.json')
components_path = os.path.join(__location__, 'components.json')
fields_path = os.path.join(__location__, 'fields.json')
bug1_path = os.path.join(__location__, 'bug1.json')
bug2_path = os.path.join(__location__, 'bug2.json')

products = json.loads(open(products_path).read())
product_name = 'WorldControl'
components = json.loads(open(components_path).read())
fields = json.loads(open(fields_path).read())

bug1 = json.loads(open(bug1_path).read())
bug1_id = 12341
bug2 = json.loads(open(bug2_path).read())
bug2_id = 12342
