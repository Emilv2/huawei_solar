import asyncio
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    ATTR_LAST_RESET,
    ATTR_STATE_CLASS,
    PLATFORM_SCHEMA,
    STATE_CLASS_MEASUREMENT,
)
from homeassistant.const import (
    CONF_HOST,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import utc_from_timestamp

from huawei_solar import AsyncHuaweiSolar, ConnectionException, ReadException

_LOGGER = logging.getLogger(__name__)


SCAN_INTERVAL = timedelta(seconds=60)

# don't overload the poor thing
DEFAULT_COOLDOWN_INTERVAL = 0.1
# throttle reconnect attempts
DEFAULT_RECONNECT_INTERVAL = 30

CONF_OPTIMIZERS = "optimizers"
CONF_BATTERY = "battery"
CONF_SLAVE = "slave"

STATE_REGISTER = "active_power"

ATTR_GRID_CODE = "grid_code"
ATTR_SERIAL_NUMBER = "serial_number"
ATTR_NB_PV_STRINGS = "nb_pv_strings"


STATIC_ATTR_LIST = [
    "model_id",
    "model_name",
    ATTR_SERIAL_NUMBER,
    "rated_power",
    ATTR_NB_PV_STRINGS,
]

STATIC_ATTR_GRID_LIST = [
    "grid_standard",
    "grid_country",
]

DYNAMIC_ATTR_LIST = [
    "day_active_power_peak",
    "reactive_power",
    "power_factor",
    "efficiency",
    "grid_frequency",
    "grid_voltage",
    "grid_current",
    "line_voltage_A_B",
    "line_voltage_B_C",
    "line_voltage_C_A",
    "phase_A_voltage",
    "phase_B_voltage",
    "phase_C_voltage",
    "phase_A_current",
    "phase_B_current",
    "phase_C_current",
    "power_meter_active_power",
    "input_power",
    "grid_A_voltage",
    "grid_B_voltage",
    "grid_C_voltage",
    "active_grid_A_current",
    "active_grid_B_current",
    "active_grid_C_current",
    "active_grid_power_factor",
    "active_grid_frequency",
    "grid_exported_energy",
    "grid_accumulated_energy",
    "active_grid_A_B_voltage",
    "active_grid_B_C_voltage",
    "active_grid_C_A_voltage",
    "active_grid_A_power",
    "active_grid_B_power",
    "active_grid_C_power",
    "startup_time",
    "shutdown_time",
    "internal_temperature",
    "device_status",
    "system_time",
]

ATTR_DAILY_YIELD = "daily_yield_energy"
ATTR_ACCUMULATED_YIELD = "accumulated_yield_energy"

ENTITY_SENSOR_LIST = [
    ATTR_DAILY_YIELD,
    ATTR_ACCUMULATED_YIELD,
]


ATTR_NB_OPTIMIZERS = "nb_optimizers"
ATTR_NB_ONLINE_OPTIMIZERS = "nb_online_optimizers"


ATTR_STORAGE_CHARGE_DISCHARGE_POWER = "storage_charge_discharge_power"
ATTR_STORAGE_TOTAL_CHARGE = "storage_total_charge"
ATTR_STORAGE_TOTAL_DISCHARGE = "storage_total_discharge"

BATTERY_ENTITY_SENSOR_LIST = [
    ATTR_STORAGE_CHARGE_DISCHARGE_POWER,
    ATTR_STORAGE_TOTAL_CHARGE,
    ATTR_STORAGE_TOTAL_DISCHARGE,
]


BATTERY_ATTR_LIST = [
    "storage_running_status",
    "storage_current_day_charge_capacity",
    "storage_current_day_discharge_capacity",
    "storage_working_mode_a",
    "storage_unit_1_working_mode_b",
    "storage_time_of_use_price",
    "storage_lcoe",
    "storage_maximum_charging_power",
    "storage_maximum_discharging_power",
    "storage_power_limit_grid_tied_point",
    "storage_charging_cutoff_capacity",
    "storage_discharging_cutoff_capacity",
    "storage_forced_charging_and_discharging_period",
    "storage_forced_charging_and_discharging_power",
    "storage_state_of_capacity",
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_OPTIMIZERS, default=False): cv.boolean,
        vol.Optional(CONF_BATTERY, default=False): cv.boolean,
        vol.Optional(CONF_SLAVE, default=0): int,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Create the sensor."""
    _LOGGER.debug("Setup Huawei Inverter")

    static_attributes = {}

    try:
        inverter = AsyncHuaweiSolar(
            host=config[CONF_HOST], loop=hass.loop, slave=config[CONF_SLAVE]
        )

        for register in STATIC_ATTR_LIST:
            static_attributes[register] = (await inverter.get(register)).value
            _LOGGER.debug("get sensor static attribute: %s", register)
            await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)

        register = ATTR_GRID_CODE
        tmp = (await inverter.get(register)).value
        _LOGGER.debug("get sensor static attribute: %s", register)
        static_attributes[STATIC_ATTR_GRID_LIST[0]] = tmp.standard
        static_attributes[STATIC_ATTR_GRID_LIST[1]] = tmp.country
        await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)

        if config[CONF_OPTIMIZERS]:
            register = ATTR_NB_OPTIMIZERS
            static_attributes[register] = (await inverter.get(register)).value
            _LOGGER.debug("get sensor static attribute: %s", register)
            await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)

    except ConnectionException as ex:
        _LOGGER.error("could not connect to Huawei inverter: %s", ex)
        await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)
        return False

    except ReadException as ex:
        _LOGGER.error("could not get register '%s': %s", register, ex)
        await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)
        return False

    _LOGGER.debug("created inverter")

    huawei_solar_sensor = HuaweiSolarSensor(
        inverter=inverter,
        optimizers_installed=config[CONF_OPTIMIZERS],
        battery_installed=config[CONF_BATTERY],
        static_attributes=static_attributes,
    )

    entities = [
        huawei_solar_sensor,
        HuaweiSolarDailyYieldSensor(
            inverter=inverter,
            unit=ENERGY_KILO_WATT_HOUR,
            icon="mdi:solar-power",
            device_class=DEVICE_CLASS_ENERGY,
            parent_sensor=huawei_solar_sensor,
            register=ATTR_DAILY_YIELD,
            name_prefix="daily_yield",
        ),
        HuaweiSolarTotalYieldSensor(
            inverter=inverter,
            unit=ENERGY_KILO_WATT_HOUR,
            icon="mdi:solar-power",
            device_class=DEVICE_CLASS_ENERGY,
            parent_sensor=huawei_solar_sensor,
            register=ATTR_ACCUMULATED_YIELD,
            name_prefix="total_yield",
        ),
    ]

    if config[CONF_BATTERY]:
        entities.extend(
            [
                HuaweiSolarEntitySensor(
                    inverter=inverter,
                    unit=POWER_WATT,
                    icon="mdi:solar-power",
                    device_class=DEVICE_CLASS_POWER,
                    parent_sensor=huawei_solar_sensor,
                    register=ATTR_STORAGE_CHARGE_DISCHARGE_POWER,
                ),
                HuaweiSolarTotalYieldSensor(
                    inverter=inverter,
                    unit=ENERGY_KILO_WATT_HOUR,
                    icon="mdi:solar-power",
                    device_class=DEVICE_CLASS_ENERGY,
                    parent_sensor=huawei_solar_sensor,
                    register=ATTR_STORAGE_TOTAL_CHARGE,
                ),
                HuaweiSolarTotalYieldSensor(
                    inverter=inverter,
                    unit=ENERGY_KILO_WATT_HOUR,
                    icon="mdi:solar-power",
                    device_class=DEVICE_CLASS_ENERGY,
                    parent_sensor=huawei_solar_sensor,
                    register=ATTR_STORAGE_TOTAL_DISCHARGE,
                ),
            ]
        )

    async_add_entities(entities, True)
    _LOGGER.debug("added entities")


class HuaweiSolarSensor(Entity):
    def __init__(
        self, inverter, optimizers_installed, battery_installed, static_attributes
    ):
        self._inverter = inverter
        self._optimizers_installed = optimizers_installed
        self._battery_installed = battery_installed
        self._hidden = False
        self._unit = POWER_WATT
        self._icon = "mdi:solar-power"
        self._available = False
        self._state = None
        self.sensor_states = {}
        self._attributes = static_attributes
        self._name = (
            self._attributes["model_name"] + "_" + self._attributes["serial_number"]
        )
        self._unique_id = self._name
        self._pv_strings_voltage = [None] * self._attributes[ATTR_NB_PV_STRINGS]
        self._pv_strings_current = [None] * self._attributes[ATTR_NB_PV_STRINGS]

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def unique_id(self):
        """Unique ID of the Huawei Solar sensor"""
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._state

    @property
    def device_class(self):
        return DEVICE_CLASS_POWER

    @property
    def device_state_attributes(self):
        attribute_list = DYNAMIC_ATTR_LIST + STATIC_ATTR_LIST + STATIC_ATTR_GRID_LIST
        attribute_list.append(ATTR_NB_PV_STRINGS)

        if self._optimizers_installed:
            attribute_list = attribute_list + [
                ATTR_NB_OPTIMIZERS,
                ATTR_NB_ONLINE_OPTIMIZERS,
            ]

        if self._battery_installed:
            attribute_list = attribute_list + BATTERY_ATTR_LIST

        attributes = {key: self._attributes.get(key, None) for key in attribute_list}

        for i in range(int(self._attributes[ATTR_NB_PV_STRINGS] or 0)):
            attributes[f"pv_string_{i+1:02}_voltage"] = self._pv_strings_voltage[i]
            attributes[f"pv_string_{i+1:02}_current"] = self._pv_strings_current[i]

        return attributes

    @property
    def unit_of_measurement(self):
        return self._unit

    async def async_update(self):
        try:
            self._state = (await self._inverter.get(STATE_REGISTER)).value
            self._available = True
            await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
        except (ReadException, ConnectionException) as ex:
            self._available = False
            _LOGGER.error("could not get register '%s': %s", STATE_REGISTER, ex)
            await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)

        for register in DYNAMIC_ATTR_LIST:
            try:
                self._attributes[register] = (await self._inverter.get(register)).value
                _LOGGER.debug("get register: %s", register)
                await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
            except (ReadException, ConnectionException) as ex:
                _LOGGER.error("could not get register '%s': %s", register, ex)
                await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)

        for i in range(int(self._attributes[ATTR_NB_PV_STRINGS] or 0)):
            try:
                register = f"pv_{i+1:02}_voltage"
                self._pv_strings_voltage[i] = (await self._inverter.get(register)).value
                _LOGGER.debug("get register: %s", register)
                await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
                register = f"pv_{i+1:02}_current"
                self._pv_strings_current[i] = (await self._inverter.get(register)).value
                _LOGGER.debug("get register: %s", register)
                await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
            except (ReadException, ConnectionException) as ex:
                _LOGGER.error("could not get register %s", ex)
                await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)

        if self._optimizers_installed:
            try:
                self._attributes[ATTR_NB_ONLINE_OPTIMIZERS] = (
                    await self._inverter.get(ATTR_NB_ONLINE_OPTIMIZERS)
                ).value
                _LOGGER.debug("get register: %s", register)
                await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
            except (ReadException, ConnectionException) as ex:
                _LOGGER.error(
                    "could not get register '%s': %s", ATTR_NB_ONLINE_OPTIMIZERS, ex
                )
                await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)

        # values for other entity sensors
        # Asynchronously calling update from a different sensors does not work
        for register in ENTITY_SENSOR_LIST:
            try:
                self.sensor_states[register] = (
                    await self._inverter.get(register)
                ).value
                _LOGGER.debug("get register: %s", register)
                await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
            except (ReadException, ConnectionException) as ex:
                _LOGGER.error("could not get register '%s': %s", register, ex)
                await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)

        if self._battery_installed:
            for register in BATTERY_ENTITY_SENSOR_LIST:
                try:
                    self.sensor_states[register] = (
                        await self._inverter.get(register)
                    ).value
                    _LOGGER.debug("get register: %s", register)
                    await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
                except (ReadException, ConnectionException) as ex:
                    _LOGGER.error("could not get register '%s': %s", register, ex)
                    await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)

            for register in BATTERY_ATTR_LIST:
                try:
                    self._attributes[register] = (
                        await self._inverter.get(register)
                    ).value
                    _LOGGER.debug("get register: %s", register)
                    await asyncio.sleep(DEFAULT_COOLDOWN_INTERVAL)
                except (ReadException, ConnectionException) as ex:
                    _LOGGER.error("could not get register '%s': %s", register, ex)
                    await asyncio.sleep(DEFAULT_RECONNECT_INTERVAL)


class HuaweiSolarEntitySensor(Entity):
    def __init__(
        self,
        inverter,
        unit,
        icon,
        device_class,
        parent_sensor,
        register,
        name_prefix=None,
    ):
        self._inverter = inverter
        self._hidden = False
        self._available = False
        self._unit = unit
        self._icon = icon
        self._parent_sensor = parent_sensor
        self._register = register
        if name_prefix:
            self._name = (
                name_prefix + "_" + self._parent_sensor._attributes[ATTR_SERIAL_NUMBER]
            )
        else:
            self._name = (
                register + "_" + self._parent_sensor._attributes[ATTR_SERIAL_NUMBER]
            )
        self._unique_id = self._name
        self._device_class = device_class

    @property
    def unique_id(self):
        """Unique ID of the Huawei Solar entity sensor"""
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._parent_sensor.sensor_states.get(self._register, None)

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def device_state_attributes(self):
        return {
            ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
        }

    @property
    def device_class(self):
        return self._device_class

    @property
    def available(self):
        """Return True if entity is available."""
        return self._parent_sensor.available


class HuaweiSolarDailyYieldSensor(HuaweiSolarEntitySensor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def device_state_attributes(self):
        system_time = self._parent_sensor._attributes.get("system_time", None)
        if system_time is not None:
            last_reset = system_time.replace(hour=0, minute=0, second=0)
        else:
            last_reset = None

        return {
            **super().device_state_attributes,
            ATTR_LAST_RESET: last_reset,
        }


class HuaweiSolarTotalYieldSensor(HuaweiSolarEntitySensor):
    @property
    def device_state_attributes(self):
        return {
            **super().device_state_attributes,
            ATTR_LAST_RESET: utc_from_timestamp(0),
        }
