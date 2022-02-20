import asyncio
import socketio

URI = 'wss://api-v4.zerion.io/'
API_TOKEN = 'Demo.ukEVQp6L5vfgxcz4sBke7XvS873GMYHy'
ORIGIN = 'http://localhost:3000'

sio = socketio.AsyncClient(logger=False, engineio_logger=False)

CONNECTED_TO_SOCKET = False

ADDRESS_PORTFOLIO = None
ADDRESS_ASSETS = None
ADDRESS_DEPOSITS = None
ADDRESS_LOANS = None
ADDRESS_STAKED_ASSETS = None
ADDRESS_LOCKED_ASSETS = None


@sio.event(namespace='/address')
async def connect():
    global CONNECTED_TO_SOCKET
    print('Connected to /address namespace!')
    CONNECTED_TO_SOCKET = True


async def connect_to_socket():
    await sio.connect(
        f'{URI}/?api_token={API_TOKEN}',
        headers={'Origin': ORIGIN},
        namespaces=['/address'],
        transports=['websocket']
    )


@sio.on('received address portfolio', namespace='/address')
def received_address_portfolio(data):
    global ADDRESS_PORTFOLIO
    print('Address portfolio is received')
    ADDRESS_PORTFOLIO = data['payload']['portfolio']

@sio.on('received address assets', namespace='/address')
def received_address_assets(data):
    global ADDRESS_ASSETS
    print('Address assets are received')
    ADDRESS_ASSETS = data['payload']['assets']

@sio.on('received address deposits', namespace='/address')
def received_address_assets(data):
    global ADDRESS_DEPOSITS
    print('Address deposits are received')
    ADDRESS_DEPOSITS = data['payload']['deposits']

@sio.on('received address loans', namespace='/address')
def received_address_assets(data):
    global ADDRESS_LOANS
    print('Address loans are received')
    ADDRESS_LOANS = data['payload']['loans']

@sio.on('received address staked-assets', namespace='/address')
def received_address_assets(data):
    global ADDRESS_STAKED_ASSETS
    print('Address staked assets are received')
    ADDRESS_STAKED_ASSETS = data['payload']['staked-assets']

@sio.on('received address locked-assets', namespace='/address')
def received_address_assets(data):
    global ADDRESS_LOCKED_ASSETS
    print('Address locked assets are received')
    ADDRESS_LOCKED_ASSETS = data['payload']['locked-assets']

def results_ready() -> bool:
    requested_entities = (
        ADDRESS_PORTFOLIO, ADDRESS_ASSETS, ADDRESS_DEPOSITS,
        ADDRESS_LOANS, ADDRESS_STAKED_ASSETS, ADDRESS_LOCKED_ASSETS
    )
    return not any(x is None for x in requested_entities)

async def main(address: str):
    # Initiate the connection with the websocket
    await connect_to_socket()

    # Wait until the connection is established
    while not CONNECTED_TO_SOCKET:
        await asyncio.sleep(0)

    # Request address information
    await sio.emit('subscribe', {
        'scope': ['portfolio', 'assets', 'deposits', 'loans', 'staked-assets', 'locked-assets'],
        'payload': {
            'address': address,
            'currency': 'usd',
            'portfolio_fields': 'all'
        }
    }, namespace='/address')

    # Wait until all information about the address is received
    while not results_ready():
        await asyncio.sleep(0)

    print('------')
    print(
        f'Address {address} has:',
        f' - {len(ADDRESS_ASSETS)} assets worth of ${ADDRESS_PORTFOLIO["assets_value"]}',
        f' - {len(ADDRESS_DEPOSITS)} deposits worth of ${ADDRESS_PORTFOLIO["deposited_value"]}',
        f' - {len(ADDRESS_LOANS)} loans worth of ${ADDRESS_PORTFOLIO["borrowed_value"]}',
        f' - {len(ADDRESS_STAKED_ASSETS)} staked assets worth of ${ADDRESS_PORTFOLIO["staked_value"]}',
        f' - {len(ADDRESS_LOCKED_ASSETS)} locked assets worth of ${ADDRESS_PORTFOLIO["locked_value"]}',
        sep='\n',
    )

if __name__ == '__main__':
    test_address = '0x7e5ce10826ee167de897d262fcc9976f609ecd2b'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(test_address))
