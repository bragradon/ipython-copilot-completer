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
To do so, you should use a MITM Proxy to capture the token from VS Code or PyCharm and then
set the `GITHUB_COPILOT_ACCESS_TOKEN` environment variable to the captured token.

## Operation modes

IPython Copilot Completer can operate in 3 modes: 'autosuggestion, 'keybinding', and 'inline'.
The default is 'autosuggestion'.

### Auto suggestions

You can configure IPython Copilot Completer to provide Copilot completions as inline auto-suggestions.
To do so, set the `GITHUB_COPILOT_AUTO_SUGGEST` environment variable to `1`.

### Keyboard shortcut

You can configure IPython Copilot Completer to provide Copilot completions only after hitting `ctrl-space` to trigger the completion.
The completions provided will replace the current line and can be accepted by pressing enter.
To do so, set the `GITHUB_COPILOT_KEY_BINDING` environment variable to `1`.

### Inlining Copilot completions

You can configure IPython Copilot Completer to have the Copilot completions inline with other completions.
They will appear inside the tab completion menu.
To do so, set the `GITHUB_COPILOT_INLINE_COMPLETIONS` environment variable to `1`.

Note: This will slow down tab completion as it will require an additional API call to GitHub Copilot for each completion.
It also returns only a single completion, so it is not as useful as the default behavior.


## License

IPython Copilot Completer is released under the [MIT License](LICENSE).
