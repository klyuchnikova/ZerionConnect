import asyncio
import threading
import socketio
from quart import Quart, request, jsonify

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


async def get_profile(token):
    global ADDRESS_PORTFOLIO
    await client.emit('subscribe', {
        'scope': ['portfolio'],
        'payload': {
            'address': token,
            'currency': 'usd',
        }
    }, namespace='/address')
    while ADDRESS_PORTFOLIO is None:
        await asyncio.sleep(0)

async def get_assets(token):
    global ADDRESS_ASSETS
    await client.emit('subscribe', {
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


@app.route('/get_all_info', methods=['GET'])
async def get_all_info():
    user_token = (await request.form)["user_token"]
    print(f"received request for all of user {user_token}")
    await get_profile(user_token)
    profile = process_profile()
    assets = process_assets()
    return jsonify({'portfolio': profile, 'assets': assets})


@app.route('/get_profile_info', methods=['GET'])
async def get_profile_info():
    user_token = (await request.form)["user_token"]
    print(f"received request for profile of user {user_token}")
    await get_profile(user_token)
    response = process_profile()
    return jsonify(response)

@app.route('/get_asset_info', methods=['GET'])
async def get_assets_info():
    #await request.get_data()  # Full raw body
    user_token = (await request.form)["user_token"]
    print(f"received request for assets of user {user_token}")
    await get_assets(user_token)
    response = process_assets()
    return jsonify(response)

if __name__ == "__main__":
    port = '8000'
    app.run(port=port, debug=True, use_reloader=False)
