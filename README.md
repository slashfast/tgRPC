# tgRPC
## Getting started
Clone repo and create the `.env` file:
```bash
git clone https://github.com/slashfast/tgRPC.git
cd tgRPC
touch .env
```
Fill in all empty environment variables in the `.env` file:
```bash
BOT_TOKEN=
RPC_ENDPOINT=127.0.0.1
RPC_PORT=7000
RPC_USER=
RPC_PASSWORD=
WALLET_PASSWORD=
```
Install [Poetry](https://python-poetry.org/docs), and then install all bot dependencies:
```bash
pip3 install poetry
poetry install
```
Almost done:
```bash
python3 main.py
```

## License
See [LICENSE](https://github.com/slashfast/tgRPC/blob/master/LICENSE)

