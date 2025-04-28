A Home Assistant custom Integration for Controlling AC with help of Tuya IR blaster.

## Installation

- Download air folder and copy paste in the **Config/Custome_Components/**
  
- After that edit the **configuaration.yaml** file in the  **Home-assistant/Config/**
  

```yaml
climate:
    - platform: air
      name: "My AC"
      access_id: Add your Tuya cloud Access id here
      access_key: Replace with your Tuya cloud Secret Key
      device_id: Replace with your Tuya IR blaster id from the tuya iot cloud
      remote_id: Replace with your AC id from the tuya iot cloud
```
#### Note* - If still not appear as the entity then download Tuya connector library 

```yaml
        pip3 install tuya-connector-python
```
