## Usage

Use this command for local checks:

```bash
uv run chainlit run src/app.py -h
```

Use this command when you want to expose the app with an explicit host and port (for example, access from another device on your network):

```bash
uv run chainlit run src/app.py --host 0.0.0.0 --port 8000 -h
```