# Home Assistant Monit Integration

This custom component allows Home Assistant to integrate with the Monit monitoring system. It periodically downloads an XML file from Monit and creates binary sensor entities for each check Monit has. Entities are created dynamically as they are added to Monit and removed when they are no longer present.

## Features

- Periodically poll Monit for status updates, times checks to match when Monit would poll
- Create binary sensor entities for each Monit check.
- Support for multiple Monit servers.

## Configuration

### Configuration Parameters

- **URL or hostname of the server** (required)
- **Username & password** (optional)

## Installation

1. **Using HACS (Home Assistant Community Store)**
- Go to HACS in Home Assistant.
- Click on "Integrations".
- Click on the "+" button.
- Search for "Monit".
- Click "Install".

2. **Manual Installation**
- Download the `monit` directory from the latest release.
- Copy the `monit` directory to your `custom_components` directory in Home Assistant.
- Restart Home Assistant.

## Usage

1. Go to Home Assistant and navigate to **Configuration** > **Devices & Services**.
2. Click on **Add Integration**.
3. Search for "Monit" and select it.
4. Follow the prompts to set up the Monit integration.

## Development

### Setup

1. Clone this repository.
2. Open the repository in Visual Studio Code.
3. Use the provided `devcontainer.json` for a pre-configured development environment.

### Commands

- **Run Home Assistant**: `scripts/develop`
- **Run Tests**: `pytest`

### Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information.

## Acknowledgements

- Most of the integration has been written by ChatGPT.
- This integration is based on the Home Assistant integration blueprint.
