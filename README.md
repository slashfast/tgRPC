# tgRPC
## Getting started
Clone repo:
```bash
git clone https://github.com/slashfast/tgRPC.git
cd tgRPC
```
Fill in all empty environment variables in the `.env` file:
```bash
BOT_TOKEN=
RPC_ENDPOINT=127.0.0.1
RPC_PORT=7000
RPC_USER=
RPC_PASSWORD=
WALLET_PASSWORD=
API=https://mempool.space
USER_ID=
DATA_PATH=data.json
```
Install [Poetry](https://python-poetry.org/docs/):
```bash
pip3 install poetry
```
And almost done:
```bash
poetry install
python3 main.py
```

## License
See [LICENSE](https://github.com/slashfast/tgRPC/blob/master/LICENSE)

