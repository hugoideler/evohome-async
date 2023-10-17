#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
"""evohomeasync2 - Schema for RESTful API Config JSON."""
from __future__ import annotations

import voluptuous as vol  # type: ignore[import]

from .const import (
    REGEX_DHW_ID,
    REGEX_SYSTEM_ID,
    REGEX_ZONE_ID,
    SZ_ALLOWED_MODES,
    SZ_ALLOWED_SETPOINT_MODES,
    SZ_ALLOWED_STATES,
    SZ_ALLOWED_SYSTEM_MODES,
    SZ_CAN_BE_PERMANENT,
    SZ_CAN_BE_TEMPORARY,
    SZ_CAN_CONTROL_COOL,
    SZ_CAN_CONTROL_HEAT,
    SZ_CURRENT_OFFSET_MINUTES,
    SZ_DHW,
    SZ_DHW_ID,
    SZ_DHW_STATE_CAPABILITIES_RESPONSE,
    SZ_DISPLAY_NAME,
    SZ_GATEWAYS,
    SZ_LOCATION_INFO,
    SZ_MAX_DURATION,
    SZ_MAX_HEAT_SETPOINT,
    SZ_SETPOINT_VALUE_RESOLUTION,
    SZ_MAX_SWITCHPOINTS_PER_DAY,
    SZ_MIN_HEAT_SETPOINT,
    SZ_MIN_SWITCHPOINTS_PER_DAY,
    SZ_MODEL_TYPE,
    SZ_NAME,
    SZ_OFFSET_MINUTES,
    SZ_SCHEDULE_CAPABILITIES,
    SZ_SCHEDULE_CAPABILITIES_RESPONSE,
    SZ_SETPOINT_CAPABILITIES,
    SZ_SUPPORTS_DAYLIGHT_SAVING,
    SZ_SYSTEM_ID,
    SZ_SYSTEM_MODE,
    SZ_TEMPERATURE_CONTROL_SYSTEMS,
    SZ_TIME_ZONE,
    SZ_TIME_ZONE_ID,
    SZ_TIMING_MODE,
    SZ_TIMING_RESOLUTION,
    SZ_VALUE_RESOLUTION,
    SZ_ZONE_ID,
    SZ_ZONE_TYPE,
    SZ_ZONES,
)
from .const import (
    ZoneMode,
    DhwState,
    SystemMode,
    TcsModelType,
    ZoneModelType,
    ZoneType,
)

SCH_SYSTEM_MODE_PERM = vol.Schema(
    {
        vol.Required(SZ_SYSTEM_MODE): vol.Any(
            str(SystemMode.AUTO),
            str(SystemMode.AUTO_WITH_RESET),
            str(SystemMode.HEATING_OFF),
        ),
        vol.Required(SZ_CAN_BE_PERMANENT): True,
        vol.Required(SZ_CAN_BE_TEMPORARY): False,
    },
    extra=vol.PREVENT_EXTRA,
)  # TODO: does this apply to DHW?

SCH_SYSTEM_MODE_TEMP = vol.Schema(
    {
        vol.Required(SZ_SYSTEM_MODE): vol.Any(
            str(SystemMode.AUTO_WITH_ECO),
            str(SystemMode.AWAY),
            str(SystemMode.CUSTOM),
            str(SystemMode.DAY_OFF),
        ),
        vol.Required(SZ_CAN_BE_PERMANENT): True,
        vol.Required(SZ_CAN_BE_TEMPORARY): True,
        vol.Required(SZ_MAX_DURATION): str,  # "99.00:00:00"
        vol.Required(SZ_TIMING_RESOLUTION): str,  # "1.00:00:00"
        vol.Required(SZ_TIMING_MODE): vol.Any("Duration", "Period"),  # Duration, Period
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_ALLOWED_SYSTEM_MODE = vol.Any(SCH_SYSTEM_MODE_PERM, SCH_SYSTEM_MODE_TEMP)

SCH_DHW_STATE_CAPABILITIES_RESPONSE = vol.Schema(
    {
        vol.Required(SZ_ALLOWED_STATES): [m.value for m in DhwState],
        vol.Required(SZ_ALLOWED_MODES): [m.value for m in ZoneMode],
        vol.Required(SZ_MAX_DURATION): str,  # "1.00:00:00"
        vol.Required(SZ_TIMING_RESOLUTION): vol.Datetime(
            format="00:%M:00"
        ),  # "00:10:00"
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_SCHEDULE_CAPABILITIES_RESPONSE = vol.Schema(
    {
        vol.Required(SZ_MAX_SWITCHPOINTS_PER_DAY): int,  # 6
        vol.Required(SZ_MIN_SWITCHPOINTS_PER_DAY): int,  # 1
        vol.Required(SZ_TIMING_RESOLUTION): vol.Datetime(
            format="00:%M:00"
        ),  # "00:10:00"
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_DHW = vol.Schema(
    {
        vol.Required(SZ_DHW_ID): vol.Match(REGEX_DHW_ID),
        vol.Required(
            SZ_DHW_STATE_CAPABILITIES_RESPONSE
        ): SCH_DHW_STATE_CAPABILITIES_RESPONSE,
        vol.Required(
            SZ_SCHEDULE_CAPABILITIES_RESPONSE
        ): SCH_SCHEDULE_CAPABILITIES_RESPONSE,
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_SETPOINT_CAPABILITIES = vol.Schema(
    {
        vol.Required(SZ_MAX_HEAT_SETPOINT): float,  # 35.0
        vol.Required(SZ_MIN_HEAT_SETPOINT): float,  # 5.0
        vol.Required(SZ_VALUE_RESOLUTION): float,  # 0.5
        vol.Required(SZ_CAN_CONTROL_HEAT): bool,
        vol.Required(SZ_CAN_CONTROL_COOL): bool,
        vol.Required(SZ_ALLOWED_SETPOINT_MODES): [m.value for m in ZoneMode],
        vol.Required(SZ_MAX_DURATION): str,  # "1.00:00:00"
        vol.Required(SZ_TIMING_RESOLUTION): vol.Datetime(
            format="00:%M:00"
        ),  # "00:10:00"
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_SCHEDULE_CAPABILITIES = SCH_SCHEDULE_CAPABILITIES_RESPONSE.extend(
    {
        vol.Required(SZ_SETPOINT_VALUE_RESOLUTION): float,
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_ZONE = vol.Schema(
    {
        vol.Required(SZ_ZONE_ID): vol.Match(REGEX_ZONE_ID),
        vol.Required(SZ_MODEL_TYPE): vol.Any(*[m.value for m in ZoneModelType]),
        vol.Required(SZ_NAME): str,
        vol.Required(SZ_SETPOINT_CAPABILITIES): SCH_SETPOINT_CAPABILITIES,
        vol.Required(SZ_SCHEDULE_CAPABILITIES): SCH_SCHEDULE_CAPABILITIES,
        vol.Required(SZ_ZONE_TYPE): vol.Any(*[m.value for m in ZoneType]),
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_TEMPERATURE_CONTROL_SYSTEM = vol.Schema(
    {
        vol.Required(SZ_SYSTEM_ID): vol.Match(REGEX_SYSTEM_ID),
        vol.Required(SZ_MODEL_TYPE): vol.Any(*[m.value for m in TcsModelType]),
        vol.Required(SZ_ALLOWED_SYSTEM_MODES): [SCH_ALLOWED_SYSTEM_MODE],
        vol.Required(SZ_ZONES): vol.All([SCH_ZONE], vol.Length(min=1, max=12)),
        vol.Optional(SZ_DHW): SCH_DHW,
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_GATEWAY = vol.Schema(
    {vol.Required(SZ_TEMPERATURE_CONTROL_SYSTEMS): [SCH_TEMPERATURE_CONTROL_SYSTEM]},
    extra=vol.PREVENT_EXTRA,
)

SCH_TIME_ZONE = vol.Schema(
    {
        vol.Required(SZ_TIME_ZONE_ID): str,
        vol.Required(SZ_DISPLAY_NAME): str,
        vol.Required(SZ_OFFSET_MINUTES): int,
        vol.Required(SZ_CURRENT_OFFSET_MINUTES): int,
        vol.Required(SZ_SUPPORTS_DAYLIGHT_SAVING): bool,
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_LOCATION_INFO = vol.Schema(
    {
        vol.Required(SZ_TIME_ZONE): SCH_TIME_ZONE,
    },
    extra=vol.PREVENT_EXTRA,
)

SCH_CONFIG = vol.Schema(
    {
        vol.Required(SZ_LOCATION_INFO): SCH_LOCATION_INFO,
        vol.Required(SZ_GATEWAYS): [SCH_GATEWAY],
    },
    extra=vol.PREVENT_EXTRA,
)