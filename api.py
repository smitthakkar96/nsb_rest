from flask import Flask, request, jsonify
from woocommerce import API
import constants
import pymysql.cursors
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

WD_api = API(
    url = constants.WD_URL,
    consumer_key = constants.WD_CONSUMER_KEY,
    consumer_secret = constants.WD_CONSUMER_SECRET,
    wp_api=True,
    version="wc/v1"
)

LY_api = API(
    url = constants.LY_URL,
    consumer_key = constants.LY_CONSUMER_KEY,
    consumer_secret = constants.LY_CONSUMER_SECRET,
    wp_api=True,
    version="wc/v1"
)

@app.route('/api/products')
def products():
    # import pdb; pdb.set_trace()
    store = request.args.get('store')
    page = request.args.get('page', 1)
    categories = request.args.get('categories')

    filters = ""
    if categories is not None:
        filters='filter[product_cat]=' + categories
    if store == 'LY':
        return jsonify({"response" : LY_api.get('products?page={0}&per_page={1}&{2}&'.format(page, 10, filters)).json()})
    elif store == 'WD':
        return jsonify({"response" : WD_api.get('products?page={0}&per_page={1}'.format(page, 10, filters)).json()})
    else:
        return response({"response" : "store not found"}), 400

@app.route('/api/orders', methods = ['POST'])
def order():
    paymentMethod = request.json.get('payment_method')
    paid = True
    if paymentMethod == "COD":
        paid = False
    billing = request.json.get('billing')
    shipping = request.json.get('billing')
    items = request.json.get('line_items')
    shipping_lines = [
        {
            "method_id": "flat_rate",
            "method_title": "Flat Rate",
            "total": 10
        }
    ]

    shop = request.json.get("shop")

    order = {
        "payment_method" : paymentMethod,
        "payment_method_title" : paymentMethod,
        "billing" : billing,
        "shipping" : shipping,
        "line_items" : items,
        "shipping_lines" : shipping_lines
    }

    if shop == "LY":
        return jsonify({"response" : LY_api.post("orders", order).json()})
    elif shop == "WD":
        return jsonify({"response" : WD_api.post("orders", order).json()})
    else:
        return jsonify({"response" : "store not found"}), 400

@app.route('/api/cancel', methods = ['POST'])
def cancel():
    #import pdb; pdb.set_trace()
    connection = pymysql.connect(host='localhost', user='root', db='NSB', cursorclass=pymysql.cursors.DictCursor)
    store = request.json.get('store')
    orderId = request.json.get('orderId')
    try:
        with connection.cursor() as cursor:
            sql = "insert into orders (oid, store, status, refund_status) values (%s, %s, %s, %s)"
            cursor.execute(sql, (orderId, store, "cancelled", False))
        connection.commit()
        return jsonify({"response" : "cancelled"})
    except Exception as e:
        print e
        return jsonify({"response" : "something went wrong"}), 400

@app.route('/api/orders/<store>/<orderId>', methods=['GET'])
def getOrderId(store, orderId):
    if store == "LY":
        return jsonify({"response" : LY_api.get('orders/{0}'.format(orderId)).json()})
    elif store == "WD":
        return jsonify({"response" : WD_api.get('orders/{0}'.format(orderId)).json()})
    else:
        return jsonify({"response" : "store not found"}), 400


if __name__ == '__main__':
    app.run(debug=True)
