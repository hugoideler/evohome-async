#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
"""Provides handling of TCC zones (heating and DHW)."""

from __future__ import annotations

from datetime import datetime as dt
import json
from typing import TYPE_CHECKING, Final, NoReturn

from .const import API_STRFTIME
from .exceptions import InvalidSchedule
from .schema import SCH_ZONE_STATUS, SCH_SCHEDULE
from .schema.const import (
    SZ_ACTIVE_FAULTS,
    SZ_DAILY_SCHEDULES,
    SZ_DAY_OF_WEEK,
    SZ_DHW_STATE,
    SZ_FOLLOW_SCHEDULE,
    SZ_HEAT_SETPOINT_VALUE,
    SZ_MODEL_TYPE,
    SZ_NAME,
    SZ_PERMANENT_OVERRIDE,
    SZ_SCHEDULE_CAPABILITIES,
    SZ_SETPOINT_CAPABILITIES,
    SZ_SETPOINT_MODE,
    SZ_SETPOINT_STATUS,
    SZ_SWITCHPOINTS,
    SZ_TEMPERATURE,
    SZ_TEMPERATURE_STATUS,
    SZ_TEMPERATURE_ZONE,
    SZ_TEMPORARY_OVERRIDE,
    SZ_TIME_OF_DAY,
    SZ_TIME_UNTIL,
    SZ_ZONE_ID,
    SZ_ZONE_TYPE,
)

if TYPE_CHECKING:
    import logging

    from . import Broker, ControlSystem
    from .typing import _EvoDictT, _EvoListT, _ZoneIdT


CAPITALIZED_KEYS = (
    SZ_DAILY_SCHEDULES,  #
    SZ_DAY_OF_WEEK,  #
    SZ_DHW_STATE,
    SZ_SWITCHPOINTS,  #
    SZ_TEMPERATURE,  # should be SZ_HEAT_SETPOINT?
    SZ_TIME_OF_DAY,  #
)


class _ZoneBaseDeprecated:
    """Deprecated attributes and methods removed from the evohome-client namespace."""

    @property
    def zone_type(self) -> NoReturn:
        raise NotImplementedError("ZoneBase.zone_type is deprecated, use ._type")

    async def schedule(self) -> NoReturn:
        raise NotImplementedError(
            "ZoneBase.schedule() is deprecrated, use .get_schedule()"
        )


class _ZoneBase(_ZoneBaseDeprecated):
    """Provide the base for temperatureZone / domesticHotWater Zones."""

    STATUS_SCHEMA = dict

    _id: str  # .zoneId or .dhwId
    _type: str  # Literal["temperatureZone", "domesticHotWater"]

    def __init__(self, tcs: ControlSystem) -> None:
        self.tcs = tcs

        self._broker: Broker = tcs._broker
        self._logger: logging.Logger = tcs._logger

        self._status: _EvoDictT = {}

    def __str__(self) -> str:
        return f"{self._id} ({self._type})"

    async def _refresh_status(self) -> _EvoDictT:
        """Update the dhw/zone with its latest status (also returns the status).

        It will be more efficient to call Location.refresh_status().
        """

        status: _EvoDictT = await self._broker.get(
            f"{self._type}/{self._id}/status", schema=self.STATUS_SCHEMA
        )  # type: ignore[assignment]

        self._update_status(status)
        return status

    def _update_status(self, status: _EvoDictT) -> None:
        self._status = status

    # status attrs...
    @property
    def activeFaults(self) -> None | _EvoListT:
        return self._status.get(SZ_ACTIVE_FAULTS)

    @property
    def temperatureStatus(self) -> None | _EvoDictT:
        return self._status.get(SZ_TEMPERATURE_STATUS)

    async def get_schedule(self) -> _EvoDictT:
        """Get the schedule for this dhw/zone object."""

        self._logger.debug(f"Getting schedule of {self._id} ({self._type})...")

        schedule = await self._broker.get(
            f"{self._type}/{self._id}/schedule", schema=SCH_SCHEDULE
        )

        response_text = json.dumps(schedule)  # FIXME
        for key_name in CAPITALIZED_KEYS:  # an anachronism from evohome-client
            response_text = response_text.replace(key_name, key_name.capitalize())

        result: _EvoDictT = json.loads(response_text)
        # change the day name string to an ordinal (Monday = 0)
        for day_of_week, setpoints in enumerate(result[SZ_DAILY_SCHEDULES.capitalize()]):
            setpoints[SZ_DAY_OF_WEEK.capitalize()] = day_of_week

        return result

    async def set_schedule(self, schedule: _EvoDictT | str) -> None:
        """Set the schedule for this dhw/zone object."""

        self._logger.debug(f"Setting schedule of {self._id} ({self._type})...")

        if isinstance(schedule, dict):
            try:
                json.dumps(schedule)
            except (OverflowError, TypeError, ValueError) as exc:
                raise InvalidSchedule(f"Invalid schedule: {exc}")

        elif isinstance(schedule, str):
            try:
                schedule = json.loads(schedule)
            except json.JSONDecodeError as exc:
                raise InvalidSchedule(f"Invalid schedule: {exc}")

        else:
            raise InvalidSchedule(f"Invalid schedule type: {type(schedule)}")

        _ = await self._broker.put(
            f"{self._type}/{self._id}/schedule", json=schedule, schema=SCH_SCHEDULE
        )  # except exceptions.InvalidSchedule, exceptions.FailedRequest


class Zone(_ZoneBase):
    """Instance of a TCS's heating zone (temperatureZone)."""

    STATUS_SCHEMA = SCH_ZONE_STATUS
    _type = SZ_TEMPERATURE_ZONE

    def __init__(self, tcs: ControlSystem, config: _EvoDictT) -> None:
        super().__init__(tcs)

        self._config: Final[_EvoDictT] = config

        assert self.zoneId, "Invalid config dict"
        self._id = self.zoneId

    # config attrs...
    @property
    def zoneId(self) -> _ZoneIdT:
        return self._config[SZ_ZONE_ID]

    @property
    def modelType(self) -> str:
        return self._config[SZ_MODEL_TYPE]

    @property
    def setpointCapabilities(self) -> dict:
        return self._config[SZ_SETPOINT_CAPABILITIES]

    @property
    def scheduleCapabilities(self) -> dict:
        return self._config[SZ_SCHEDULE_CAPABILITIES]

    @property
    def zoneType(self) -> str:
        return self._config[SZ_ZONE_TYPE]

    # status attrs...
    @property
    def name(self) -> str:
        return self._config.get(SZ_NAME) or self._config[SZ_NAME]

    @property
    def setpointStatus(self) -> None | dict:
        return self._status.get(SZ_SETPOINT_STATUS)

    async def _set_mode(self, heat_setpoint: dict) -> None:
        """TODO"""

        _ = await self._broker.put(
            f"{self._type}/{self._id}/heatSetpoint", json=heat_setpoint  # schema=
        )  # except exceptions.FailedRequest

    async def set_temperature(
        self, temperature: float, /, *, until: None | dt = None
    ) -> None:
        """Set the temperature of the given zone."""

        if until is None:  # NOTE: beware that these may be case-sensitive
            mode = {
                SZ_SETPOINT_MODE: SZ_PERMANENT_OVERRIDE,
                SZ_HEAT_SETPOINT_VALUE: temperature,
                SZ_TIME_UNTIL: None,
            }
        else:
            mode = {
                SZ_SETPOINT_MODE: SZ_TEMPORARY_OVERRIDE,
                SZ_HEAT_SETPOINT_VALUE: temperature,
                SZ_TIME_UNTIL: until.strftime(API_STRFTIME),
            }

        await self._set_mode(mode)

    async def cancel_temp_override(self) -> None:
        """Cancel an override to the zone temperature."""

        mode = {
            SZ_SETPOINT_MODE: SZ_FOLLOW_SCHEDULE,
            SZ_HEAT_SETPOINT_VALUE: 0.0,
            SZ_TIME_UNTIL: None,
        }

        await self._set_mode(mode)
