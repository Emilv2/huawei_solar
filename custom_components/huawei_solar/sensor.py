import voluptuous as vol
import logging
from homeassistant.components.sensor import PLATFORM_SCHEMA
from huawei_solar import HuaweiSolar, ReadException
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, POWER_WATT
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Huawei Inverter"

CONF_OPTIMIZERS = "optimizers"
CONF_BATTERY = "battery"

ATTR_MODEL_ID = "model_id"
ATTR_SERIAL_NUMBER = "serial_number"

ATTR_NB_PV_STRINGS = "nb_pv_strings"
ATTR_RATED_POWER = "rated_power"
ATTR_GRID_STANDARD = "grid_standard"
ATTR_GRID_COUNTRY = "grid_country"
ATTR_DAILY_YIELD = "daily_yield"
ATTR_TOTAL_YIELD = "total_yield"
ATTR_DAY_POWER_PEAK = "day_active_power_peak"
ATTR_REACTIVE_POWER = "reactive_power"
ATTR_POWER_FACTOR = "power_factor"
ATTR_EFFICIENCY = "efficiency"
ATTR_GRID_FREQUENCY = "grid_frequency"
ATTR_GRID_VOLTAGE = "grid_voltage"
ATTR_GRID_CURRENT = "grid_current"
ATTR_LINE_VOLTAGE_A_B = "line_voltage_A_B"
ATTR_LINE_VOLTAGE_B_C = "line_voltage_B_C"
ATTR_LINE_VOLTAGE_C_A = "line_voltage_C_A"
ATTR_PHASE_A_VOLTAGE = "phase_A_voltage"
ATTR_PHASE_B_VOLTAGE = "phase_B_voltage"
ATTR_PHASE_C_VOLTAGE = "phase_C_voltage"
ATTR_PHASE_A_CURRENT = "phase_A_current"
ATTR_PHASE_B_CURRENT = "phase_B_current"
ATTR_PHASE_C_CURRENT = "phase_C_current"
ATTR_POWER_METER_ACTIVE_POWER = "power_meter_active_power"
ATTR_INPUT_POWER = "input_power"
ATTR_GRID_A_VOLTAGE = "grid_A_voltage"
ATTR_GRID_B_VOLTAGE = "grid_B_voltage"
ATTR_GRID_C_VOLTAGE = "grid_C_voltage"
ATTR_ACTIVE_GRID_A_CURRENT = "active_grid_A_current"
ATTR_ACTIVE_GRID_B_CURRENT = "active_grid_B_current"
ATTR_ACTIVE_GRID_C_CURRENT = "active_grid_C_current"
ATTR_ACTIVE_GRID_POWER_FACTOR = "active_grid_power_factor"
ATTR_ACTIVE_GRID_FREQUENCY = "active_grid_frequency"
ATTR_GRID_EXPORTED_ENERGY = "grid_exported_energy"
ATTR_GRID_ACCUMULATED_ENERGY = "grid_accumulated_energy"
ATTR_ACTIVE_GRID_A_B_VOLTAGE = "active_grid_A_B_voltage"
ATTR_ACTIVE_GRID_B_C_VOLTAGE = "active_grid_B_C_voltage"
ATTR_ACTIVE_GRID_C_A_VOLTAGE = "active_grid_C_A_voltage"
ATTR_ACTIVE_GRID_A_POWER = "active_grid_A_power"
ATTR_ACTIVE_GRID_B_POWER = "active_grid_B_power"
ATTR_ACTIVE_GRID_C_POWER = "active_grid_C_power"
ATTR_STARTUP_TIME = "startup_time"
ATTR_SHUTDOWN_TIME = "shutdown_time"
ATTR_INTERNAL_TEMPERATURE = "internal_temperature"
ATTR_DEVICE_STATUS = "device_status"
ATTR_NB_OPTIMIZERS = "nb_optimizers"
ATTR_NB_ONLINE_OPTIMIZERS = "nb_online_optimizers"
ATTR_SYSTEM_TIME = "system_time"
ATTR_STORAGE_STATUS = "storage_status"
ATTR_STORAGE_CHARGE_DISCHARGE_POWER = "storage_charge_discharge_power"
ATTR_STORAGE_CURRENT_DAY_CHARGE_CAPACITY = "storage_current_day_charge_capacity"
ATTR_STORAGE_CURRENT_DAY_DISCHARGE_CAPACITY = (
    "storage_current_day_discharge_capacity"
)
ATTR_STORAGE_WORKING_MODE = "storage_working_mode"
ATTR_STORAGE_TIME_OF_USE_PRICE = "storage_time_of_use_price"
ATTR_STORAGE_LCOE = "storage_lcoe"
ATTR_STORAGE_MAXIMUM_CHARGING_POWER = "storage_maximum_charging_power"
ATTR_STORAGE_MAXIMUM_DISCHARGING_POWER = "storage_maximum_discharging_power"
ATTR_STORAGE_POWER_LIMIT_GRID_TIED_POINT = "storage_power_limit_grid_tied_point"
ATTR_STORAGE_CHARGING_CUTOFF_CAPACITY = "storage_charging_cutoff_capacity"
ATTR_STORAGE_DISCHARGING_CUTOFF_CAPACITY = "storage_discharging_cutoff_capacity"
ATTR_STORAGE_FORCED_CHARGING_AND_DISCHARGING_PERIOD = (
    "storage_forced_charging_and_discharging_period"
)
ATTR_STORAGE_FORCED_CHARGING_AND_DISCHARGING_POWER = (
    "storage_forced_charging_and_discharging_power"
)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_OPTIMIZERS, default=False): cv.boolean,
        vol.Optional(CONF_BATTERY, default=False): cv.boolean,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("Setup Huawei Inverter")

    host = config[CONF_HOST]
    try:
        inverter = HuaweiSolar(host)
    except Exception as ex:
        _LOGGER.error("could not connect to Huawei inverter: %s", ex)
        return False
    _LOGGER.debug("created inverter")
    entities = []
    entities.append(
        HuaweiSolarSensor(inverter, config[CONF_OPTIMIZERS], config[CONF_BATTERY])
    )

    add_entities(entities, True)
    _LOGGER.debug("added entities")


class HuaweiSolarSensor(Entity):
    def __init__(self, inverter, optimizers, battery_installed):
        self._inverter = inverter
        self._optimizers = optimizers
        self._battery_installed = battery_installed
        self._hidden = False
        self._unit = POWER_WATT
        self._icon = "mdi:solar-power"
        self._name = self._inverter.get("model_name").value
        self._model_id = self._inverter.get("model_id").value
        self._serial_number = self._inverter.get("serial_number").value
        self._nb_pv_strings = self._inverter.get("nb_pv_strings").value
        self._pv_strings_voltage = [None] * self._nb_pv_strings
        self._pv_strings_current = [None] * self._nb_pv_strings
        self._rated_power = self._inverter.get("rated_power").value

        if optimizers:
            self._nb_optimizers = self._inverter.get("nb_optimizers").value
        else:
            self._nb_optimizers = 0

        tmp = self._inverter.get("grid_code").value
        self._grid_standard = tmp.standard
        self._grid_country = tmp.country

        self._last_update = None

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
    def device_state_attributes(self):
        attributes = {
            ATTR_MODEL_ID: self._model_id,
            ATTR_SERIAL_NUMBER: self._serial_number,
            ATTR_NB_PV_STRINGS: self._nb_pv_strings,
            ATTR_RATED_POWER: self._rated_power,
            ATTR_GRID_STANDARD: self._grid_standard,
            ATTR_GRID_COUNTRY: self._grid_country,
            ATTR_DAILY_YIELD: self._daily_yield,
            ATTR_TOTAL_YIELD: self._total_yield,
            ATTR_GRID_VOLTAGE: self._grid_voltage,
            ATTR_GRID_CURRENT: self._grid_current,
            ATTR_LINE_VOLTAGE_A_B: self._line_voltage_A_B,
            ATTR_LINE_VOLTAGE_B_C: self._line_voltage_B_C,
            ATTR_LINE_VOLTAGE_C_A: self._line_voltage_C_A,
            ATTR_PHASE_A_VOLTAGE: self._phase_A_voltage,
            ATTR_PHASE_B_VOLTAGE: self._phase_B_voltage,
            ATTR_PHASE_C_VOLTAGE: self._phase_C_voltage,
            ATTR_PHASE_A_CURRENT: self._phase_A_current,
            ATTR_PHASE_B_CURRENT: self._phase_B_current,
            ATTR_PHASE_C_CURRENT: self._phase_C_current,
            ATTR_DAY_POWER_PEAK: self._day_active_power_peak,
            ATTR_REACTIVE_POWER: self._reactive_power,
            ATTR_POWER_FACTOR: self._power_factor,
            ATTR_EFFICIENCY: self._efficiency,
            ATTR_GRID_FREQUENCY: self._grid_frequency,
            ATTR_POWER_METER_ACTIVE_POWER: self._power_meter_active_power,
            ATTR_INPUT_POWER: self.input_power,
            ATTR_GRID_A_VOLTAGE: self._grid_A_voltage,
            ATTR_GRID_B_VOLTAGE: self._grid_B_voltage,
            ATTR_GRID_C_VOLTAGE: self._grid_C_voltage,
            ATTR_ACTIVE_GRID_A_CURRENT: self._active_grid_A_current,
            ATTR_ACTIVE_GRID_B_CURRENT: self._active_grid_B_current,
            ATTR_ACTIVE_GRID_C_CURRENT: self._active_grid_C_current,
            ATTR_ACTIVE_GRID_POWER_FACTOR: self._active_grid_power_factor,
            ATTR_ACTIVE_GRID_FREQUENCY: self._active_grid_frequency,
            ATTR_GRID_EXPORTED_ENERGY: self._grid_exporterd_energy,
            ATTR_GRID_ACCUMULATED_ENERGY: self._grid_accumulated_energy,
            ATTR_ACTIVE_GRID_A_B_VOLTAGE: self._active_grid_A_B_voltage,
            ATTR_ACTIVE_GRID_B_C_VOLTAGE: self._active_grid_B_C_voltage,
            ATTR_ACTIVE_GRID_C_A_VOLTAGE: self._active_grid_C_A_voltage,
            ATTR_ACTIVE_GRID_A_POWER: self._active_grid_A_power,
            ATTR_ACTIVE_GRID_B_POWER: self._active_grid_B_power,
            ATTR_ACTIVE_GRID_C_POWER: self._active_grid_C_power,
            ATTR_STARTUP_TIME: self._startup_time.isoformat(),
            ATTR_SHUTDOWN_TIME: self._shutdown_time.isoformat(),
            ATTR_INTERNAL_TEMPERATURE: self._internal_temperature,
            ATTR_DEVICE_STATUS: self._device_status,
            ATTR_NB_OPTIMIZERS: self._nb_optimizers,
            ATTR_SYSTEM_TIME: self._system_time,
        }
        for i in range(int(self._nb_pv_strings)):
            attributes[f"pv_string_{i+1:02}_voltage"] = self._pv_strings_voltage[i]
            attributes[f"pv_string_{i+1:02}_current"] = self._pv_strings_current[i]

        if self._nb_optimizers:
            attributes[ATTR_NB_ONLINE_OPTIMIZERS] = self._nb_online_optimizers

        if self._battery_installed:
            attributes[ATTR_STORAGE_STATUS] = self._storage_status
            attributes[
                ATTR_STORAGE_CHARGE_DISCHARGE_POWER
            ] = self._storage_charge_discharge_power
            attributes[
                ATTR_STORAGE_CURRENT_DAY_CHARGE_CAPACITY
            ] = self._storage_current_day_charge_capacity
            attributes[
                ATTR_STORAGE_CURRENT_DAY_DISCHARGE_CAPACITY
            ] = self._storage_current_day_discharge_capacity
            attributes[ATTR_STORAGE_WORKING_MODE] = self._storage_working_mode
            attributes[ATTR_STORAGE_TIME_OF_USE_PRICE] = self._storage_time_of_use_price
            attributes[ATTR_STORAGE_LCOE] = self._storage_lcoe
            attributes[
                ATTR_STORAGE_MAXIMUM_CHARGING_POWER
            ] = self._storage_maximum_charging_power
            attributes[
                ATTR_STORAGE_MAXIMUM_DISCHARGING_POWER
            ] = self._storage_maximum_discharging_power
            attributes[
                ATTR_STORAGE_POWER_LIMIT_GRID_TIED_POINT
            ] = self._storage_power_limit_grid_tied_point
            attributes[
                ATTR_STORAGE_CHARGING_CUTOFF_CAPACITY
            ] = self._storage_charging_cutoff_capacity
            attributes[
                ATTR_STORAGE_DISCHARGING_CUTOFF_CAPACITY
            ] = self._storage_discharging_cutoff_capacity
            attributes[
                ATTR_STORAGE_FORCED_CHARGING_AND_DISCHARGING_PERIOD
            ] = self._storage_forced_charging_and_discharging_period
            attributes[
                ATTR_STORAGE_FORCED_CHARGING_AND_DISCHARGING_POWER
            ] = self._storage_forced_charging_and_discharging_power

        return attributes

    @property
    def unit_of_measurement(self):
        return self._unit

    def update(self):
        self._state = self._inverter.get("active_power").value
        self._power_meter_active_power = self._inverter.get(
            "power_meter_active_power"
        ).value
        self.input_power = self._inverter.get("input_power").value
        self._daily_yield = self._inverter.get("daily_yield_energy").value
        self._total_yield = self._inverter.get("accumulated_yield_energy").value
        self._reactive_power = self._inverter.get("reactive_power").value
        self._power_factor = self._inverter.get("power_factor").value
        self._efficiency = self._inverter.get("efficiency").value
        self._line_voltage_A_B = self._inverter.get("line_voltage_A_B").value
        self._line_voltage_B_C = self._inverter.get("line_voltage_B_C").value
        self._line_voltage_C_A = self._inverter.get("line_voltage_C_A").value
        self._phase_A_voltage = self._inverter.get("phase_A_voltage").value
        self._phase_B_voltage = self._inverter.get("phase_B_voltage").value
        self._phase_C_voltage = self._inverter.get("phase_C_voltage").value
        self._phase_A_current = self._inverter.get("phase_A_current").value
        self._phase_B_current = self._inverter.get("phase_B_current").value
        self._phase_C_current = self._inverter.get("phase_C_current").value
        self._grid_voltage = self._line_voltage_A_B
        self._grid_current = self._phase_A_current
        self._grid_frequency = self._inverter.get("grid_frequency").value
        self._grid_A_voltage = self._inverter.get("grid_A_voltage").value
        self._grid_B_voltage = self._inverter.get("grid_B_voltage").value
        self._grid_C_voltage = self._inverter.get("grid_C_voltage").value
        self._active_grid_A_current = self._inverter.get("active_grid_A_current").value
        self._active_grid_B_current = self._inverter.get("active_grid_B_current").value
        self._active_grid_C_current = self._inverter.get("active_grid_C_current").value
        self._active_grid_power_factor = self._inverter.get(
            "active_grid_power_factor"
        ).value
        self._active_grid_frequency = self._inverter.get("active_grid_frequency").value
        self._grid_exporterd_energy = self._inverter.get("grid_exporterd_energy").value
        self._grid_accumulated_energy = self._inverter.get(
            "grid_accumulated_energy"
        ).value
        self._active_grid_A_B_voltage = self._inverter.get(
            "active_grid_A_B_voltage"
        ).value
        self._active_grid_B_C_voltage = self._inverter.get(
            "active_grid_B_C_voltage"
        ).value
        self._active_grid_C_A_voltage = self._inverter.get(
            "active_grid_C_A_voltage"
        ).value
        self._active_grid_A_power = self._inverter.get("active_grid_A_power").value
        self._active_grid_B_power = self._inverter.get("active_grid_B_power").value
        self._active_grid_C_power = self._inverter.get("active_grid_C_power").value
        self._startup_time = self._inverter.get("startup_time").value.time()
        self._shutdown_time = self._inverter.get("shutdown_time").value.time()
        self._system_time = self._inverter.get("system_time").value
        self._internal_temperature = self._inverter.get("internal_temperature").value
        self._device_status = self._inverter.get("device_status").value

        if self._nb_optimizers:
            self._nb_online_optimizers = self._inverter.get(
                "nb_online_optimizers"
            ).value

        if self._battery_installed:
            self._storage_status = self._inverter.get("storage_status").value
            self._storage_charge_discharge_power = self._inverter.get(
                "storage_charge_discharge_power"
            ).value
            self._storage_current_day_charge_capacity = self._inverter.get(
                "storage_current_day_charge_capacity"
            ).value
            self._storage_current_day_discharge_capacity = self._inverter.get(
                "storage_current_day_discharge_capacity"
            ).value
            self._storage_working_mode = self._inverter.get(
                "storage_working_mode"
            ).value
            self._storage_time_of_use_price = self._inverter.get(
                "storage_time_of_use_price"
            ).value
            self._storage_lcoe = self._inverter.get("storage_lcoe").value
            self._storage_maximum_charging_power = self._inverter.get(
                "storage_maximum_charging_power"
            ).value
            self._storage_maximum_discharging_power = self._inverter.get(
                "storage_maximum_discharging_power"
            ).value
            self._storage_power_limit_grid_tied_point = self._inverter.get(
                "storage_power_limit_grid_tied_point"
            ).value
            self._storage_charging_cutoff_capacity = self._inverter.get(
                "storage_charging_cutoff_capacity"
            ).value
            self._storage_discharging_cutoff_capacity = self._inverter.get(
                "storage_discharging_cutoff_capacity"
            ).value
            self._storage_forced_charging_and_discharging_period = self._inverter.get(
                "storage_forced_charging_and_discharging_period"
            ).value
            self._storage_forced_charging_and_discharging_power = self._inverter.get(
                "storage_forced_charging_and_discharging_power"
            ).value

        self._day_active_power_peak = self._inverter.get("day_active_power_peak").value
        for i in range(int(self._nb_pv_strings)):
            self._pv_strings_voltage[i] = self._inverter.get(
                f"pv_{i+1:02}_voltage"
            ).value
            self._pv_strings_current[i] = self._inverter.get(
                f"pv_{i+1:02}_current"
            ).value
