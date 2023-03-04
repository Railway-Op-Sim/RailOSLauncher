"""
Railway Operation Simulator Discord Launcher
============================================

This launcher provides live information on the user's current Railway Operation Simulator
session, giving status updates such as which route is being operated and how long for.
As well as the mode (e.g. editting a timetable etc).
"""
__author__ = "Kristian Zarebski <krizar312@gmail.com>"
__date__ = "2022-02-08"
__license__ = "GPLv3"

import asyncio
import typing
import configparser
import datetime
import glob
import logging
import os.path

logging.basicConfig()

import discordsdk
import pycountry
import toml

from railostools.common.enumeration import Level1Mode, Level2OperMode


def alpha2_country_codes() -> typing.Dict[str, str]:
    return {
        country.alpha_2: country.name.lower().replace(" ", "-")
        for country in pycountry.countries
    }


class DiscordBroadcaster:
    _version: str = "v0.1.4"
    _app_id: str = "893179281189003274"
    _logger: logging.Logger = logging.getLogger("RailOSTools.Discord")
    _activity = discordsdk.Activity()
    _logo_key = "railway_operation_simulator_logo"
    _flags: typing.Dict[str, str] = alpha2_country_codes()
    _oper_mode_statuses: typing.Dict[Level2OperMode, str] = {
        Level2OperMode.NoOperMode: "",
        Level2OperMode.Paused: "Paused",
        Level2OperMode.Operating: "Operating",
        Level2OperMode.PreStart: "Loading",
    }
    _welcome_message = """
=============================================================================

                Railway Operation Simulator Discord Launcher
                                {version}

                            _____╔°_________
                                   ╱
                            ______╱__°╗_____

  This executable updates your user Discord status during a RailOS session!

=============================================================================
"""

    def __init__(self, railos_location: str, debug: bool=False) -> None:
        if not os.path.exists(railos_location):
            raise FileNotFoundError(
                f"Cannot location Railway Operation Simulator, path '{railos_location}' "
                "does not exist"
            )
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self._logger.info(self._welcome_message.format(version=self._version))
        self._start = datetime.datetime.now()
        self._running = True
        self._mode = {"main": "", "oper": ""}
        self._railos_loc = railos_location
        self._discord = discordsdk.Discord(
            int(self._app_id), discordsdk.CreateFlags.default
        )
        self._discord.get_user_manager().on_current_user_update = (
            self.on_curr_user_update
        )
        self._activity.assets.large_image = self._logo_key
        self._activity.assets.large_text = "Testing"
        self._activity.details = ""
        self._activity.state = ""

    def on_curr_user_update(self) -> None:
        user = self._discord.get_user_manager().get_current_user()
        self._logger.info(
            f"Updating activity for user : {user.username}#{user.discriminator}"
        )

    def activity_callback(self, result) -> None:
        if result == discordsdk.Result.ok:
            self._logger.info("Activity set successfully!")
        else:
            raise AssertionError(result)

    async def _run_sdk(self) -> None:
        while self._running:
            await asyncio.sleep(1 / 10.0)
            self._discord.run_callbacks()

    def _load_session_ini(self) -> configparser.ConfigParser:
        _session_data = os.path.join(self._railos_loc, "session.ini")

        if not os.path.exists(_session_data):
            raise FileNotFoundError(
                f"Expected session metadata file '{_session_data}', but file does not exist"
            )

        _parser = configparser.ConfigParser()
        _parser.read(_session_data)

        return _parser

    def _load_metadata(self, parser: configparser.ConfigParser) -> None:
        try:
            _metadata_file: str = parser.get("session", "metadata_file")
            return toml.load(_metadata_file)
        except configparser.NoOptionError:
            self._logger.warning("Failed to retrieve session information from INI file,"
                                 "this version of RailOSLauncher requires a RailOS version with API v1.2")
            return {}
        except configparser.NoSectionError:
            self._logger.warning("Failed to retrieve metadata file information from INI file,"
                                 "this version of RailOSLauncher requires a RailOS version with API v1.2")
            return {}

    def _update_status(self, parser: configparser.ConfigParser):
        try:
            _top_mode = Level1Mode(parser.getint("session", "main_mode"))
            _oper_mode = Level2OperMode(parser.getint("session", "operation_mode"))
        except configparser.NoOptionError:
            self._logger.warning("Failed to retrieve session information from INI file")
            return
        except configparser.NoSectionError:
            self._logger.warning("Failed to retrieve current mode information from INI file")
            return

        if self._mode["main"] == _top_mode and self._mode["oper"] == _oper_mode:
            return

        self._mode["main"] = _top_mode
        self._mode["oper"] = _oper_mode

        _activity = ""
        _new_status = ""

        if _top_mode == Level1Mode.OperMode:
            _activity = self._oper_mode_statuses[_oper_mode]
            self._activity.timestamps.start = datetime.datetime.timestamp(
                datetime.datetime.now()
            )
        else:
            if _top_mode == Level1Mode.TrackMode:
                _activity = "Editing"
            else:
                _activity = ""
                _new_status = ""
            self._activity.timestamps.start = 0

        if _activity:
            try:
                _current_rly = parser.get("session", "railway")
                _meta = self._load_metadata(parser)
                _current_rly = _current_rly.replace("_", " ").title()
                if _meta:
                    if "display_name" in _meta:
                        _current_rly = _meta["display_name"]
                    elif "name" in _meta:
                        _current_rly = _meta["name"]
                if _meta and "country_code" in _meta:
                    self._logger.info(
                        f"Recognised country code '{_meta['country_code']}'"
                    )
                    try:
                        self._activity.assets.small_image = self._flags[
                            _meta["country_code"]
                        ]
                    except KeyError:
                        self._logger.warning(
                            "No country found for simulation, no sub-icon will be used"
                        )
                _new_status = f"{_activity} {_current_rly}"
            except configparser.NoOptionError:
                self._logger.error("Failed to find key 'railway' in INI file")
            except configparser.NoSectionError:
                self._logger.error("Failed to find section 'session' in INI file")
            except AttributeError as e:
                self._logger.error(f"Retrieval of session information failed with '{e}'")

        if self._activity.details != _new_status and _new_status:
            self._activity.details = _new_status
            self._discord.get_activity_manager().update_activity(
                self._activity, self.activity_callback
            )

    async def _check_for_temp(self) -> None:
        while self._running:
            await asyncio.sleep(2)
            _parser = self._load_session_ini()
            try:
                self._running = _parser.getboolean("session", "running")
            except configparser.NoOptionError:
                self._logger.error("Failed to find key 'running' in INI file")
            except configparser.NoSectionError:
                self._logger.error("Failed to find section 'session' in INI file")
            except AttributeError as e:
                self._logger.error(f"Retrieval of 'running' state failed with '{e}'")
            self._update_status(_parser)

    async def _run_railos(self) -> None:
        if not os.path.exists(os.path.join(self._railos_loc, "railway.exe")):
            raise FileNotFoundError(
                f"No binary '{os.path.join(self._railos_loc, 'railway.exe')}' was found"
            )
        await asyncio.create_subprocess_shell(
            os.path.join(self._railos_loc, "railway.exe")
        )

    async def _main(self):
        await asyncio.gather(self._run_sdk(), self._check_for_temp(), self._run_railos())

    def run(self):
        self._start = datetime.datetime.now()
        self._discord.get_activity_manager().update_activity(
            self._activity, self.activity_callback
        )
        asyncio.run(self._main())


if __name__ in "__main__":
    import argparse
    _parser = argparse.ArgumentParser()
    _parser.add_argument("--railos-location", help="Location of the RailOS railway.exe file", default="..")
    _parser.add_argument("--debug", action="store_true", default=False, help="Run in debug mode")
    _args = _parser.parse_args()
    _railos_loc = _args.railos_location
    if not os.path.exists(_railos_loc):
        raise AssertionError(f"Launcher failed, could not find Railway Operation Simulator 'railway.exe' at '{_railos_loc}'")
    DiscordBroadcaster(_railos_loc, _args.debug).run()
