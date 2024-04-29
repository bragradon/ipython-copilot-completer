# IPython Copilot Completer

IPython Copilot Completer is a plugin for the IPython interactive shell that provides line completion using GitHub Copilot.

## Installation

```bash
# Method 1: wheel
V="0.0.10"
wget https://github.com/bragradon/ipython-copilot-completer/releases/download/v$V/IPython_Copilot_Completer-$V-py3-none-any.whl
pip install IPython_Copilot_Completer-$V-py3-none-any.whl

# Method 2: local install
git clone https://github.com/bragradon/ipython-copilot-completer.git
cd ipython-copilot-completer
pip install -e .
```

Once installed, you can activate the plugin by running the following command in an IPython session:

```python
%load_ext copilot_completer
```

## Configuration

You will need to provide a GitHub Copilot API Token to use IPython Copilot Completer.
You can obtain a token by running the following magic command in an IPython session:

```python
%copilot_login
```

This will open a browser window where you can log in to GitHub and generate a token.

Save the token and set it via the `GITHUB_COPILOT_ACCESS_TOKEN` environment variable so you don't have to login again next time.

## Usage

Suggestions will automatically show up while you're typing. Press right arrow key to accept them.

## License

IPython Copilot Completer is released under the [MIT License](LICENSE).
