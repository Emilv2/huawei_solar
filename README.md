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

**Example:**

```yaml
sensor:
  - platform: huawei_solar   
    host: '192.168.0.123'
    optimizers: true
    battery: true
    slave: 1
```
