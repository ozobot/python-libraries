# ozobot-cli

A command-line interface for working with Ozobots.

See the [monorepo](https://github.com/ozobot/python-libraries) for more details.

## Usage

Scan for nearby Ozobots over BLE, stopping after 5 seconds:

```sh
ozobot scan --timeout 5
```

Stream results as a JSON array, stopping once 3 unique devices are seen:

```sh
ozobot scan --json --max-devices 3
```

Throttle repeat sightings of the same device to once per 10 seconds:

```sh
ozobot scan --refresh 10
```
