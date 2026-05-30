
![Delta Chat Logo](https://delta.chat/assets/logos/delta-chat.svg)
# Delta Chat Integration for Home Assistant

An **unofficial** Home Assistant integration that allows you to use Delta Chat as a notification and interaction engine. Leverage the power of decentralized, e-mail-based messaging to control your smart home securely.

> [!IMPORTANT]  
> **Disclaimer**: This is an **unofficial** integration. It is not developed, maintained, or endorsed by the official Delta Chat team.

## 🚀 Features

*   **Instant Notifications**: Send alerts from Home Assistant to your Delta Chat app (individuals or groups).
*   **Two-Way Interaction**: Send commands from Delta Chat back to Home Assistant to trigger scripts or automations.
*   **Media Support**: Send snapshots from your security cameras or localized media files directly to your chats.
*   **Decentralized & Private**: Operates entirely over your existing e-mail infrastructure with no middle-man servers.

## 🛠️ Requirements

*   **E-mail Account**: A dedicated IMAP/SMTP account for your Home Assistant bot. If an E-mail account does not exists, you can create a Chatmail profile from within the Integration

## Steps to Add a user to DeltaChat bot
  1. Make sure your Delta chat account is added and configured via the "Add Integration" -> "Delta Chat" and account is created and configured.
  1. Go to your Delta chat integration -> Device (for the account from which you want to send the message)
  1. Under Diagnostic, click on "Bot Status". The status of bot should be connected.
  1. On the "Bot Status" pop up, Click on 3 dots on top right and select "Details"
  1. From the Details pop up, Click on your "QR Uri".
  1. It will open up a new page with QR code under "Tap if you have Delta Chat on another device"
  1. Scan the QR code with the user account to whom you want to send a message
  1. You can test sending a message from the user to the bot to verify if the delta chat bot received the message
  1. Now, you should be able to send message via the actions

## 📜 Credits & Acknowledgments

### Delta Chat RPC Library
This integration is built upon the excellent work of the Delta Chat team. It utilizes the [deltachat-rpc-client](https://pypi.org) to bridge Home Assistant with the [deltachat-core-rust](https://github.com/chatmail/core) engine. 

### Branding & Assets
The Delta Chat logo and name are used for identification purposes only. All branding assets are sourced from the [official Delta Chat website](https://delta.chat). We give full credit to the original creators for their beautiful design and open-source contributions.

## Integration Status
This integration was created primarily for my personal use to get notifications and send commands to HA. it's currently in alpha stage and tested with a small set of accounts on HAOS only. If you had issues or would like any changes / enhancement, Please feel free to open an issue. 
### Future Roadmap
* Add a notification / QR code after setting up the integration / account.
* Fix issues related to syncing of Profile Name and bio post initial setup.
* Backup configuration and chats
* Change the Disappearing Message settings from the integration
* Add few standard commands support
  * Trigger Automation
