import sys
from pathlib import Path
sys.path.append(str(Path('').resolve().parent))
from pprint import pprint
# pprint(sys.path)

from SETTINGS.settings__ import info_bmq
from pybit.unified_trading import HTTP

mode = info_bmq['MODE']

session = HTTP(
    demo=False if mode.upper() == 'NODEMO' else True,
    api_key=info_bmq['API_EXCHANGE'],
    api_secret=info_bmq['API_2_EXCHANGE']
)