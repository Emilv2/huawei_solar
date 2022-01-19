# Huawei Solar sensor
This code is a custom component to read the data from Huawei inverters

## Install

### Available with HACS (Home Assistant Community Store)
This is a custom component. Custom components are not installed by default in your Home Assistant installation. [HACS](https://github.com/custom-components/hacs) is an Home Assistant store integration from which this integration can be easily installed and updated. By using HACS you will also make sure that any new versions are installed by default and as simple as the installation itself.
Currently this custom component is not in the HACS repositories, in the [HACS documentation](https://hacs.xyz/docs/faq/custom_repositories/) you can find how to add a custom repository.

### Manual
Copy the `custom_components` folder into your HA configuration folder (if you already have the `custom_components` folder, copy the `huawei_solar` folder into it).

Then configure the sensors by setting up the huawei_solar platform in `configuration.yaml`.

## Options

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| host | string | **Required** | hostname or ip address
| optimizers | boolean | **Optional** | Set to true if you have optimizers and want to see information about them.
| battery | boolean | **Optional** | Set to true if you have a battery and want to see information about it.
| slave | int | **Optional** | Set the slave unit, set `slave = 1` when using the dongle.
| port | int | **Optional** | Set the inverter ModBus TCP port 

**Example:**

```yaml
sensor:
  - platform: huawei_solar   
    host: '192.168.0.123'
    optimizers: true
    battery: true
    slave: 1
    port: 6607
```

## Troubleshooting

If you are using the SDongle to communicate with your inverter, make sure the following conditions are met

- Dongle Firmware must be at least at version SPC123 (You can ask the support to update yours remotely, provide your dongle SN. Alternatively obtain the firmware file from support and install it through the App by connecting to the Dongle management Wi-Fi (available for 3 minutes after startup).)
- In the Dongle settings (Settings/Communication settings/Dongle Configuration, log in as installer to the inverter), make sure to set Modbus-TCP to Enable(unrestricted) or set an allowed IP if using restricted mode
- According to the [Modbus TCP Guide](https://forum.huawei.com/enterprise/en/modbus-tcp-guide/thread/789585-100027), the inverter needs at least version SPC139
- set `slave: 1` as described above
- Make sure no other client is accessing the Modbus TCP interface

If it is still not working after that, restart the inverter and try again.

## Breaking Changes

### `1.0.0`

- Sensors names now include the serial number. If you have existing templates/lovelace/automations you should update those to the new name or use the UI to change the name back to the old name.
- the `daily_yield`, `total_yield`, `storage_charge_discharge_power`, `storage_total_charge` and `storage_total_discharge` are now separate sensors instead of attributes.
