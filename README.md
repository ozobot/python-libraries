# Ozobot Python libraries

A monorepo repository with Python libraries for Ozobot Evo and Ari control. The libraries can be used both in the [Ozobot Editor](https://editor.ozobot.com) and
locally on your computer.

## Installation
All the libraries are hosted on [PyPI](https://pypi.org/user/ozobot/).

```sh
  pip install ozobot-ari
```

or

```sh
  pip install ozobot-evo
```

## Repository contents
The repository contains several directories with packages implementing either robot control functionality or a backend functionality used by the user facing control libraries.
Users are generally interested in the control libraries:

 - [`ozobot-ari`](/ozobot-ari) for Ari
 - [`ozobot-evo`](/ozobot-evo) for Evo
 - [`ozobot-actors`](/ozobot-actors) used by Blockly exported programs for Ari and Evo 

But there are also other back end libraries such as:

 - [`ozobot-ble`](/ozobot-ble)
 - [`ozobot-jsonrpc`](/ozobot-jsonrpc)
 - [`ozobot-webrtc`](/ozobot-webrtc)

## Development
TBD
