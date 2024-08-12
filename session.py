from pybit.unified_trading import HTTP
from settings__ import files_content

session = HTTP(
    demo=False if files_content['MODE'].upper() == 'NODEMO' else True,
    api_key=files_content['API_EXCHANGE'],
    api_secret=files_content['API_2_EXCHANGE']
)

session_ = HTTP()