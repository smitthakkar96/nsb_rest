from flask import Flask, request, jsonify
from woocommerce import API
import constants
import pymysql.cursors
from flask_cors import CORS
import eventlet

eventlet.monkey_patch()


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

connection = pymysql.connect(host='localhost', user='root', db='NSB', cursorclass=pymysql.cursors.DictCursor)


def init():
    sql = "CREATE TABLE IF NOT EXISTS cart (uuid varchar(100), id INTEGER PRIMARY KEY auto_increment, productId int, productName text, productImage text, quantity int, price int, store varchar(10))"
    with connection.cursor() as cursor:
        cursor.execute(sql)
    connection.commit()

init()


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
    uuid = request.json.get('uuid', 'undefined1')
    shipping = request.json.get('billing')
    items = request.json.get('line_items')
    shipping_lines = [
        {
            "method_id": "flat_rate",
            "method_title": "Flat Rate",
            "total": 10
        }
    ]
    order = {
        "payment_method" : paymentMethod,
        "payment_method_title" : paymentMethod,
        "billing" : billing,
        "shipping" : shipping,
        "line_items" : items,
        "shipping_lines" : shipping_lines
    }

    with connection.cursor() as cursor:
        sql = "delete from cart where uuid ='" + uuid + "'";
        cursor.execute(sql)
    with eventlet.Timeout(100):
        LY_api.post("orders", order)
        WD_api.post("orders", order)


    return jsonify({"response" : "success"})

@app.route('/api/cancel', methods = ['POST'])
def cancel():
    #import pdb; pdb.set_trace()
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


@app.route('/api/cart/<uuid>', methods = ['GET'])
def getMyCart(uuid):
    # import pdb; pdb.set_trace()
    sql = "select * from cart where uuid='" + uuid + "'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
    data = []
    for row in cursor:
        data.append(row)
    connection.commit()
    return jsonify({"response" : data})

@app.route('/api/addItem', methods = ['POST'])
def addItem():
    # import pdb; pdb.set_trace()
    uuid = request.json.get("uuid", 'undefined')
    productId = request.json["productId"]
    productName = request.json["productName"]
    quantity = request.json["quantity"]
    productImage = request.json["productImage"]
    price = request.json["productPrice"]
    store = request.json["store"]
    sql = "INSERT INTO CART (uuid, productId, productName, productImage, quantity, price, store) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    with connection.cursor() as cursor:
        cursor.execute(sql, (uuid, productId, productName, productImage, quantity, price, store))
    connection.commit()
    return jsonify({"response" : "success"})

@app.route('/api/updateQuantity', methods = ['POST'])
def updateQuantity():
    productId = request.json.get('productId')
    userId = request.json.get('uuid', 'undefined')
    quantity = request.json.get('quantity')
    sql = 'UPDATE CART SET quantity=' + str(quantity) + ' where uuid="' + userId + '" and productId=' + str(productId)
    with connection.cursor() as cursor:
        cursor.execute(sql)
    connection.commit()
    return jsonify({"response" : "success"})

@app.route('/api/checkIfExist/<uuid>/<productId>')
def checkIfExist(uuid, productId):
    sql = 'select * from cart where uuid="' + uuid + '" and productId=' + productId
    with connection.cursor() as cursor:
        cursor.execute(sql)
    for row in cursor:
        return jsonify({"response" : True})
    return jsonify({"response" : False})



if __name__ == '__main__':
    app.run(debug=True)
