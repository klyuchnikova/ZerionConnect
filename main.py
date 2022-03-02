import asyncio

import socketio
from quart import Quart, jsonify

global ADDRESS_PROFILE, ADDRESS_ASSETS
ADDRESS_PORTFOLIO = None
ADDRESS_ASSETS = None

client = socketio.AsyncClient()

app = Quart(__name__)


def process_profile():
    global ADDRESS_PORTFOLIO
    profile = dict.fromkeys(["assets_value", "absolute_change_24h", "relative_change_24h"])
    for key in profile.keys():
        profile[key] = ADDRESS_PORTFOLIO.get(key, None)
    ADDRESS_PORTFOLIO = None
    return profile


def process_assets():
    global ADDRESS_ASSETS
    assets = [dict() for i in range(len(ADDRESS_ASSETS.keys()))]
    for i, (asset_id, asset_info) in enumerate(ADDRESS_ASSETS.items()):
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
            current_asset_price = asset_value
        assets[i] = {
            "id": asset_id,
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


async def request_profile(token, action='get'):
    if action not in ['get', 'subscribe', 'unsubscribed']:
        return Exception(f"Bad request to server: there's no such action as {action}")
    global ADDRESS_PORTFOLIO
    await client.emit(action, {
        'scope': ['portfolio'],
        'payload': {
            'address': token,
            'currency': 'usd',
        }
    }, namespace='/address')
    while ADDRESS_PORTFOLIO is None:
        await asyncio.sleep(0)


async def request_assets(token, action='get'):
    global ADDRESS_ASSETS
    await client.emit(action, {
        'scope': ['assets'],
        'payload': {
            'address': token,
            'currency': 'usd',
        }
    }, namespace='/address')
    while ADDRESS_ASSETS is None:
        await asyncio.sleep(0)


async def get_all(token):
    global ADDRESS_PORTFOLIO
    global ADDRESS_ASSETS

    await client.emit('subscribe', {
        'scope': ['portfolio', 'assets'],
        'payload': {
            'address': token,
            'currency': 'usd'
        }
    }, namespace='/address')
    while ADDRESS_PORTFOLIO is None or ADDRESS_ASSETS is None:
        await asyncio.sleep(0)

    while ADDRESS_ASSETS is None:
        await asyncio.sleep(0)


@app.route("/")
async def connect():
    # perform multiple async requests concurrently
    await connect_socket()
    return "Connected"


@app.route('/profile/<user_token>', methods=['GET'])
async def get_profile_info(user_token):
    print(f"received request for profile of user {user_token}")
    await request_profile(user_token)
    response = process_profile()
    return jsonify(response)


@app.route('/subscribe/profile/<user_token>', methods=['GET'])
async def subscribe_profile_info(user_token):
    print(f"received request for profile of user {user_token}")
    await request_profile(user_token, 'subscribe')
    response = process_profile()
    return jsonify(response)


@app.route('/subscribe/assets/<user_token>', methods=['GET'])
async def subscribe_assets_info(user_token):
    print(f"received request for assets of user {user_token}")
    await request_assets(user_token, 'subscribe')
    response = process_assets()
    return jsonify(response)


if __name__ == "__main__":
    port = '8080'
    app.run(port=port, host='0.0.0.0', debug=True, use_reloader=False)
