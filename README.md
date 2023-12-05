# IPython Copilot Completer

IPython Copilot Completer is a plugin for the IPython interactive shell that provides line completion using GitHub Copilot.

## Installation

To install IPython Copilot Completer, download the release wheel and run:

```bash
pip install IPython_Copilot_Completer-<version>-py3-none-any.whl
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

Alternatively, if you already have a token, you can set it via the `GITHUB_COPILOT_ACCESS_TOKEN` environment variable.

## License

IPython Copilot Completer is released under the [MIT License](LICENSE).
