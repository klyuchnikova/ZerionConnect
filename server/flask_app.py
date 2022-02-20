"""import asyncio
from flask import Flask, request, jsonify

global zerion_client

loop = asyncio.get_event_loop()
app = Flask(__name__)

async def abar(user_token):
    await asyncio.sleep(1)
    print(1)
    await asyncio.sleep(1)
    print(2)
    await asyncio.sleep(3)
    print(3)
    print(f"token : {user_token}")

@app.route('/get_profile_info', methods=['GET'])
async def get_profile_info():
    try:
        answer = await zerion_client.get_profile_info(user_token)
        print(f"flask sending profile info")
        return jsonify(answer)
    except:
        return jsonify({'user_token': user_token, 'ERROR': 'could\'t connect to Zerion'})

if __name__ == "__main__":
    app.run(port='8000', debug = False, use_reloader=False)
"""
import asyncio

import socketio
from flask import Flask, request, jsonify
from copy import deepcopy

loop = asyncio.get_event_loop()
client = socketio.AsyncClient()
app = Flask(__name__)


async def fetch():
    URI = 'wss://api-v4.zerion.io/'
    API_TOKEN = 'Demo.ukEVQp6L5vfgxcz4sBke7XvS873GMYHy'
    await client.connect(url=f'{URI}/?api_token={API_TOKEN}',
                                       headers={'Origin': 'http://localhost:3000'},
                                       namespaces=['/address'],
                                       transports=['websocket'])
    print(f"WTF???? IT WORKED????????????")

global ADDRESS_PORTFOLIO
ADDRESS_PORTFOLIO = None

@client.on('received address portfolio', namespace='/address')
def received_address_portfolio(data):
    global ADDRESS_PORTFOLIO
    print('Address portfolio is received')
    ADDRESS_PORTFOLIO = data['payload']['portfolio']

async def get_portfolio(token):
    global ADDRESS_PORTFOLIO
    await client.emit('subscribe', {
        'scope': ['portfolio'],
        'payload': {
            'address': token,
            'currency': 'usd',
            'portfolio_fields': 'all'
        }
    }, namespace='/address')
    while ADDRESS_PORTFOLIO is None:
        await asyncio.sleep(0)


def fight(responses):
    return "Why can't we all just get along?"


@app.route("/")
def index():
    # perform multiple async requests concurrently
    responses = loop.run_until_complete(
        fetch()
    )
    return fight(responses)

@app.route('/get_profile_info', methods=['GET'])
def get_profile_info():
    global ADDRESS_PORTFOLIO
    user_token = request.form.get('user_token')
    responses = loop.run_until_complete(
        get_portfolio(user_token)
    )
    response = deepcopy(ADDRESS_PORTFOLIO)
    ADDRESS_PORTFOLIO = None
    return jsonify(response)


if __name__ == "__main__":
    app.run(port='8000', debug=False, use_reloader=False)
