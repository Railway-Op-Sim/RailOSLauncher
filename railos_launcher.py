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
import logging
import os.path
import pathlib

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
    _version: str = "v0.1.5-alpha"
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

    def __init__(self, railos_location: pathlib.Path, sdk_directory: pathlib.Path, debug: bool = False) -> None:
        if not railos_location.exists():
            raise FileNotFoundError(
                f"Cannot location Railway Operation Simulator, path '{railos_location}' "
                "does not exist"
            )
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self._logger.info(self._welcome_message.format(version=self._version))
        self._start: datetime.datetime = datetime.datetime.now()
        self._running: bool = True
        self._mode: dict[str, Level1Mode | Level2OperMode | None] = {"main": None, "oper": None}
        self._railos_loc: pathlib.Path = railos_location
        self._session_ini_file: pathlib.Path = self._railos_loc.joinpath("session.ini")
        self._discord: discordsdk.Discord = discordsdk.Discord(
            int(self._app_id), discordsdk.CreateFlags.default, sdk_directory
        )
        self._discord.get_user_manager().on_current_user_update = (
            self.on_curr_user_update
        )
        self._activity.assets.large_image = self._logo_key
        self._activity.assets.large_text = ""
        self._activity.name = ""
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
            try:
                self._discord.run_callbacks()
            except discordsdk.exception.DiscordException:
                break

    def _load_session_ini(self) -> configparser.ConfigParser:
        if not os.path.exists(self._session_ini_file):
            raise FileNotFoundError(
                f"Expected session metadata file '{self._session_ini_file}', but file does not exist"
            )

        _parser = configparser.ConfigParser()

        if not _parser.read(self._session_ini_file):
            raise configparser.ParsingError(f"{self._session_ini_file}")

        return _parser

    def _load_metadata(self, parser: configparser.ConfigParser) -> dict[str, typing.Any]:
        try:
            _metadata_file: str = parser.get("session", "metadata_file")

            if not _metadata_file or not os.path.exists(_metadata_file):
                return {}

            return toml.load(_metadata_file)
        except configparser.NoOptionError:
            self._logger.warning(
                "Failed to retrieve metadata, no Metadata file was specified in INI file."
            )
            return {}
        except configparser.NoSectionError:
            self._logger.warning(
                "Failed to retrieve metadata, no Metadata file was specified in INI file."
            )
            return {}

    def _update_status(self, parser: configparser.ConfigParser) -> None:
        try:
            _top_mode = Level1Mode(parser.getint("session", "main_mode"))
            _oper_mode = Level2OperMode(parser.getint("session", "operation_mode"))
        except configparser.NoOptionError:
            self._logger.warning("Failed to retrieve session information from INI file")

            return
        except configparser.NoSectionError:
            self._logger.warning(
                "Failed to retrieve current mode information from INI file"
            )

            return
        except AttributeError as e:
            self._logger.error(
                f"Retrieval of session information failed with '{e}'"
            )

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
                _activity = "Editing "
            elif _top_mode == Level1Mode.TimetableMode:
                _activity = "Timetabling "
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
            except configparser.NoOptionError as e:
                self._logger.error("Failed to find key 'railway' in INI file")

                return
            except configparser.NoSectionError as e:
                self._logger.error("Failed to find section 'session' in INI file")

                return
            except AttributeError as e:
                self._logger.error(
                    f"Retrieval of session information failed with '{e}'"
                )

                return

        if self._activity.details != _new_status and _new_status:
            self._activity.details = _new_status
            self._discord.get_activity_manager().update_activity(
                self._activity, self.activity_callback
            )

    async def _check_for_temp(self) -> None:
        while self._running:
            await asyncio.sleep(2)
            try:
                _parser = self._load_session_ini()
            except configparser.ParsingError:
                self._logger.warning(
                    "Failed to parse contents of session data, got empty list."
                )
                continue
            try:
                self._running = _parser.getboolean("session", "running")
            except configparser.NoOptionError:
                self._logger.error("Failed to find key 'running' in INI file")

                continue
            except configparser.NoSectionError:
                self._logger.error("Failed to find section 'session' in INI file")

                continue
            except AttributeError as e:
                self._logger.error(f"Retrieval of 'running' state failed with '{e}'")

                continue

            if self._running:
                self._update_status(_parser)

    async def _run_railos(self) -> None:
        _railos_binaries: typing.List[str] = ["railway.exe", "RailOS64.exe", "RailOS32.exe"]
        if _railos_exe := next(
            (
                os.path.join(self._railos_loc, binary)
                for binary in _railos_binaries
                if os.path.exists(os.path.join(self._railos_loc, binary))
            ),
            None,
        ):
            await asyncio.create_subprocess_shell(_railos_exe)
        else:
            raise FileNotFoundError(
                f"No executable found at location '{self._railos_loc}'"
            )

    async def _main(self):
        await asyncio.gather(
            self._run_sdk(), self._check_for_temp(), self._run_railos()
        )

    def run(self):
        self._start = datetime.datetime.now()
        self._discord.get_activity_manager().update_activity(
            self._activity, self.activity_callback
        )
        asyncio.run(self._main())


if __name__ in "__main__":
    import argparse
    import os
    import sys
    import sysconfig

    _parser = argparse.ArgumentParser()

    _ros_loc = pathlib.Path(os.environ.get("ProgramFiles", "C:\\Program Files")).joinpath("Railway_Operation_Simulator", "Railway")

    if getattr(sys, 'frozen', False):
        _default_loc = pathlib.Path(sysconfig.get_paths()["purelib"]).parents[1]
        if not _ros_loc.exists():
            _ros_loc = pathlib.Path(sys.executable).parent
    else:
        _default_loc = pathlib.Path(__file__).parent
        if not _ros_loc.exists():
            _ros_loc = _default_loc

    _parser.add_argument(
        "--railos-location",
        help="Location of the RailOS executable file",
        default=f"{_ros_loc}",
    )
    _parser.add_argument(
        "--sdk-dir",
        help="Location of Discord SDK",
        default=f"{_default_loc}"
    )
    _parser.add_argument(
        "--debug", action="store_true", default=False, help="Run in debug mode"
    )
    _args = _parser.parse_args()
    _railos_loc = pathlib.Path(_args.railos_location)
    _sdk_dir = pathlib.Path(_args.sdk_dir)

    if not _railos_loc.exists():
        raise AssertionError(
            f"Launcher failed, could not find Railway Operation Simulator 'railway.exe/RailOS64.exe/RailOS32.exe' at '{_railos_loc}'"
        )

    DiscordBroadcaster(_railos_loc, _sdk_dir, _args.debug).run()
