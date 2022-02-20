import asyncio
import threading
import socketio
from flask import Flask, request, jsonify

global ADDRESS_PORTFOLIO, ADDRESS_ASSETS
ADDRESS_PORTFOLIO = None
ADDRESS_ASSETS = None

loop = asyncio.get_event_loop()
client = socketio.AsyncClient()

app = Flask(__name__)


def process_portfolio():
    global ADDRESS_PORTFOLIO
    portfolio = dict.fromkeys(["assets_value", "absolute_change_24h", "relative_change_24h"])
    for key in portfolio.keys():
        portfolio[key] = ADDRESS_PORTFOLIO.get(key, None)
    ADDRESS_PORTFOLIO = None
    return portfolio


def process_assets():
    global ADDRESS_ASSETS
    assets = dict()
    for asset_id, asset_info in ADDRESS_ASSETS.items():
        asset = asset_info.get('asset', dict())
        quantity = asset_info.get("quantity", None)

        if type(asset) != dict:
            asset = dict()
        name = asset.get("name", None)
        try:
            relative_change_24h = asset.get("price", dict()).get("relative_change_24h", None)
            asset_value = asset.get("price", dict()).get("value", None)
        except:
            relative_change_24h = None
            asset_value = None

        if asset_value is None:
            current_asset_price = None
        else:
            current_asset_price = asset_value * (10**asset.get("decimals", 0))
        assets[asset_id] = {
            "name": name,
            "icon_url": asset.get("icon_url", None),
            "relative_change_24h": relative_change_24h,
            "current_price": current_asset_price,
            "quantity": quantity}
    ADDRESS_ASSETS = None
    return assets


async def connect_socket():
    URI = 'wss://api-v4.zerion.io/'
    API_TOKEN = 'Demo.ukEVQp6L5vfgxcz4sBke7XvS873GMYHy'
    await client.connect(url=f'{URI}/?api_token={API_TOKEN}',
                         headers={'Origin': 'http://localhost:3000'},
                         namespaces=['/address'],
                         transports=['websocket'])
    print(f"Connection successful")


@client.on('received address portfolio', namespace='/address')
def received_address_portfolio(data):
    global ADDRESS_PORTFOLIO
    print('Address portfolio is received')
    ADDRESS_PORTFOLIO = data['payload']['portfolio']


@client.on('received address assets', namespace='/address')
def received_address_assets(data):
    global ADDRESS_ASSETS
    print('Address assets are received')
    ADDRESS_ASSETS = data['payload']['assets']


async def get_portfolio(token):
    global ADDRESS_PORTFOLIO
    await client.emit('subscribe', {
        'scope': ['portfolio'],
        'payload': {
            'address': token,
            'currency': 'usd',
            'portfolio_fields': ["assets_value", "absolute_change_24h", "relative_change_24h"]
        }
    }, namespace='/address')
    while ADDRESS_PORTFOLIO is None:
        await asyncio.sleep(0)


async def get_all(token):
    global ADDRESS_PORTFOLIO
    global ADDRESS_ASSETS

    await client.emit('subscribe', {
        'scope': ['portfolio', 'assets'],
        'payload': {
            'address': token,
            'currency': 'usd',
            'portfolio_fields': ["assets_value", "absolute_change_24h", "relative_change_24h"]
        }
    }, namespace='/address')
    while ADDRESS_PORTFOLIO is None or ADDRESS_ASSETS is None:
        await asyncio.sleep(0)

    while ADDRESS_ASSETS is None:
        await asyncio.sleep(0)


@app.route("/")
def connect():
    # perform multiple async requests concurrently
    loop.run_until_complete(connect_socket())
    return "Connected"


@app.route('/get_all_info', methods=['GET'])
def get_all_info():
    user_token = request.form.get('user_token')
    loop.run_until_complete(
        get_all(user_token)
    )
    profile = process_portfolio()
    assets = process_assets()
    return jsonify({'profile': profile, 'assets': assets})


"""
@app.route('/get_profile_info', methods=['GET'])
def get_profile_info():
    user_token = request.form.get('user_token')
    loop.run_until_complete(
        get_assets(user_token)
    )
    response = process_assets()
    return jsonify(response)

@app.route('/get_asset_info', methods=['GET'])
async def get_assets_info():
    user_token = request.form.get('user_token')
    loop.run_until_complete(
        get_portfolio(user_token)
    )
    response = process_portfolio()
    return jsonify(response)
"""
if __name__ == "__main__":
    port = '8000'
    threading.Thread(target=lambda: app.run(port=port, debug=True, use_reloader=False)).start()
    threading.Thread(target=lambda: loop.run_until_complete(connect_socket()))