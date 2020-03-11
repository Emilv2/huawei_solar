# Huawei Solar sensor
This code is a custom component to read the data from Huawei inverters

## Install

Copy these files to custom_components/huawei_solar/

Then configure the sensors by setting up the stib platform in `configuration.yaml`.

## Options

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| host | string | **Required** | hostname or ip address

**Example:**

```yaml
sensor:
  - platform: huawei_solar   
    host: '192.168.0.123'
```
