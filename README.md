
![Delta Chat Logo](https://delta.chat/assets/logos/delta-chat.svg)
# Delta Chat Integration for Home Assistant

An **unofficial** Home Assistant integration that allows you to use Delta Chat as a notification and interaction engine. Leverage the power of decentralized, e-mail-based messaging to control your smart home securely.

> [!IMPORTANT]  
> **Disclaimer**: This is an **unofficial** integration. It is not developed, maintained, or endorsed by the official Delta Chat team.


## 🚀 Features

*   **Instant Notifications**: Send alerts from Home Assistant to your Delta Chat app (individuals or groups).
    * Via Notifier (Using the notifier entity created by the Delta Chat Integration). This will use the "Active Contact" Control Dropdown to pick which chat(Contact / Group) to send the message to.
      ```yaml
      action: notify.send_message
      target:
        entity_id: notify.delta_chat_none
      data:
        message: Test Message
      ```

    * Via Send Message Action
      ```yaml
      action: deltachat.send_message
      data:
        // ID of integration. Use the UI mode in developer tools to get this ID
        from_account: 01FFFFFFFFFFFFFFFFFFFFFFFF 
        // Chat ID
        target: "12" 
        message: Test Message
      ```

*   **Two-Way Interaction**: Send commands from Delta Chat back to Home Assistant to trigger scripts or automations.
    * Use the `deltachat_message_received` event 
      ```yaml
      event_type: deltachat_message_received
      data:
        to: XXXXXXXXX@nine.testrun.org
        to_name: HA DeltaChat Test Bot
        text: Sample incoming message
        sender: 11
        chat_id: 12
      origin: LOCAL
      time_fired: "2026-06-18T13:36:05.611885+00:00"
      context:
        id: 01FFFFFFFFFFFFFFFFFFFFFFFF
        parent_id: null
        user_id: null
      ```
*   **Media Support**: Send snapshots from your security cameras or localized media files directly to your chats.

    __Sending Images from Home Assistant to DeltaChat__

      * Via Send Message Action with file
        ```yaml
        action: deltachat.send_message
        data:
          // ID of integration. Use the UI mode in developer tools to get this ID
          from_account: 01FFFFFFFFFFFFFFFFFFFFFFFF 
          // Chat ID
          target: "12"
          message: Test Message
          file:
            media_content_id: media-source://<source>
            media_content_type: image/gif
        ```

    __Sending Images from Delta Chat to Home Assistant__

    Once a file is injested via Delta Chat client and event is triggered `deltachat_message_received`, In Home Assistant, Natigate to Media -> Delta Chat -> <Account> -> <Chat> -> and you can see all media files recieved.

    ```yaml
    event_type: deltachat_message_received
    data:
      to: XXXXXXXXX@nine.testrun.org
      to_name: HA DeltaChat Test Bot
      text: my image [Image – 188.00 KiB]
      sender: 11
      chat_id: 12
    origin: LOCAL
    time_fired: "2026-06-18T13:40:53.622278+00:00"
    context:
      id: 01FFFFFFFFFFFFFFFFFFFFFFFF
      parent_id: null
      user_id: null
    ```

## 🛠️ Requirements

*   **HACS**: You already have HACS installed and configured on your Home Assistant Instance. if not, please follow the [HACS documentation](https://www.hacs.xyz/)


## 🛠️ Installation Steps

1. Open HACS
2. On the top right, click on 3 dots and select "Custom repositories"

<img src="https://github.com/user-attachments/assets/437c35d0-96c1-4858-9123-1e10b3fbad97" />

3. Add the Repository `https://github.com/uditghai/ha-deltachat` and Type as "Integration"

<img src="https://github.com/user-attachments/assets/3d68d207-90bb-49ca-873a-369203190c30" />
  
4. Click "ADD" 

<img src="https://github.com/user-attachments/assets/256b1e5e-a683-4dae-8354-4dac5e8ca82e" />

5. On HACS, Search for Delta Chat and download the latest release version.

<img src="https://github.com/user-attachments/assets/1bff7319-d640-45fa-bbac-e4c1bced61f0" />

<img src="https://github.com/user-attachments/assets/3d15e748-ddd5-4dfa-8352-b21766fb2cd0" />

<img src="https://github.com/user-attachments/assets/2c853a7e-b52d-4464-9e97-cd346537435c" />
 
6. Once Delta Chat Integration is downloaded, Go to "Settings" and Click on "Restart required" and then Submit on the pop-up. Once Home Assistant Restarts, Home Assistant Delta Chat Integration is installed and ready to be configured

<img src="https://github.com/user-attachments/assets/d3854b1e-737c-497c-8b3a-bfbff82d34fe" />

### 🛠️ Configuration

1. Go to "Settings" -> "Devices & Services" and Click on "Add integration"

<img src="https://github.com/user-attachments/assets/db49fddb-9179-47a2-8ad5-0d89e8605aed" />

2. Search for Delta Chat

<img src="https://github.com/user-attachments/assets/838f74d2-7f01-4b00-8f2c-1c958c3d03ee" />

3. On Delta Chat Setup, Select Create a new Bot profile (Chatmail)

<img src="https://github.com/user-attachments/assets/f13fc3af-da2c-439d-a8bb-becb738e9e64" />

4. Change the Bot Display name and Chatmail server (Optional)
    1. If you want to change the Chatmail server, use a similar format `dcaccount:https://nine.testrun.org/new` to configure a new account with a compatible chatmail server. **Please note that you cannot change the Chatmail Server after an account is configured, however you can create a new configuration and add a new Delta Chat Account using the integration**
    2. You may change the display name later using the Device screen. 

<img src="https://github.com/user-attachments/assets/01e5c380-83d4-4102-85fe-3ca4a27ef605" />

5. Add a Bio / Status as required and Submit

<img src="https://github.com/user-attachments/assets/9303a0f2-76f5-4378-ab00-bd4250279cda" />

6. Specify an Area or "Skip and finish"

<img src="https://github.com/user-attachments/assets/d8a9224f-3889-4759-a053-b488cb7c1349" />

7. Now your Delta Chat bot is ready

<img src="https://github.com/user-attachments/assets/0932bb3f-7223-4b59-ac42-3bd9bd9b704f" />

## Device View

**Device View** shows the following Configuration values (in Control section) which can be changed
1. Active Contact (Chat): The Contact / Group that will be notified when Delta Chat notification is used
2. Profile Bio: Bio of the Contact that you will see in Delta Chat
3. Profile Name: The Name of the Contact that you will see in Delta Chat


## Adding Contacts

1. Under Diagnostic, click on "Bot Status". The status of bot should be connected.
2. On the "Bot Status" pop up, Click on 3 dots on top right and select "Details" or Show More based on your HA version
3. From the Details pop up, Click on your "QR Uri".

<img src="https://github.com/user-attachments/assets/4ef0cd6a-cfbe-4f8d-be8e-f9c10cd59a73" />

4. It will open up a new page with QR code under "Tap if you have Delta Chat on another device"

<img src="https://github.com/user-attachments/assets/7eed9c29-6cad-4f02-b094-6aa3f38def89" />

5. Scan the QR code with the user account to whom you want to send a message
6. You can test sending a message from the user to the bot to verify if the delta chat bot received the message



## Known Issues
Please refer to [Release Notes](RELEASENOTES.md)

## Setting up Development Environment
Please refer to [Development Environment](DEVENV.md)


## 📜 Credits & Acknowledgments

### Delta Chat RPC Library
This integration is built upon the excellent work of the Delta Chat team. It utilizes the [deltachat-rpc-client](https://pypi.org) to bridge Home Assistant with the [deltachat-core-rust](https://github.com/chatmail/core) engine. 

### Branding & Assets
The Delta Chat logo and name are used for identification purposes only. All branding assets are sourced from the [official Delta Chat website](https://delta.chat). We give full credit to the original creators for their beautiful design and open-source contributions.

## Integration Status
This integration was created primarily for my personal use to get notifications and send commands to HA. it's currently in alpha stage and tested with a small set of accounts on HAOS only. If you had issues or would like any changes / enhancement, Please feel free to open an issue.

### Future Roadmap
* Ability to add profile image to account
* Backup and restore of configuration and chats
* Change the Disappearing Message settings from the integration
* Add few standard commands support
  * Trigger Automation
