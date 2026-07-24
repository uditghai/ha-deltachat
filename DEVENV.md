# Development Environment Setup for Delta Chat Integration for Home Assistant
1. Clone [repo](https://github.com/uditghai/ha-deltachat) into a local folder location
1. Follow setup to configure home assistant developer environment using dev containers https://developers.home-assistant.io/docs/development_environment/
1. Add another mount at root level for the integration in `devcontainer.json` for the dev containers as below
    ```
    "mounts": [
    "source=<location_of_ha-deltachat_clone_from_above>/ha-deltachat/custom_components/deltachat,target=/workspaces/core/config/custom_components/deltachat,type=bind"
    ],
    ```
1. Any changes done on the local clone will be reflected in the delta chat add on in the dev container
1. if you create a separate environment for type checking of code for `ha-deltachat`, please install the following packages
    ```
    pip install deltachat-rpc-client
    ```
1. To run the server, In the core [Dev Container: Home Assistant Dev] VS Code window -> select the command Tasks: Run Task -> Run Home Assistant Core
1. Home assistant is now running with the DeltaChat addon on localhost:8123

## Reference Documentation

### Delta Chat
* Pip deltachat-rpc
    * https://pypi.org/project/deltachat-rpc-server/
    * https://pypi.org/project/deltachat-rpc-client/
* Deltachat Documentation
    * https://py.delta.chat/jsonrpc/intro.html
* Codebase for chatmail core
    * https://github.com/chatmail/core/tree/main
### Home Assistant
* Developer Guide
    * https://developers.home-assistant.io/docs/development_environment/
* Codebase for Home Assistant core
    * https://github.com/home-assistant/core