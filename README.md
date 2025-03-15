<p align="center">
<img
    style="display: block; 
           margin-left: auto;
           margin-right: auto;
           width: 30%;"
    src="https://raw.githubusercontent.com/Railway-Op-Sim/RailOSLauncher/main/img/RailOSLauncher.png" 
    alt="Our logo">
</img>
</p>

# Discord Launcher for Railway Operation Simulator
RailOSLauncher provides a wrapper for the standard `railway.exe`/`RailOS64.exe`/`RailOS32.exe` provided by Railway Operation Simulator with the added feature of being able to broadcast your in game status as Discord activity.
The activity displayed includes operation mode (e.g. building or running a simulation), and if operating, which simulation is being run (and where metadata has been provided) the country it is
based in.

## Installation

If Railway Operation Simulator is installed in the default location (as per Chocolatey install) of `C:\Program Files\Railway_Operation_Simulator\` the `RailOSLauncher.exe` can be executed from any location.

Alternatively place the folder `RailOSLauncher` into the directory `<railos-installation>/Railway` where `railos-installation` is the location of your Railway Operation Simulator installation.

### Placing External to RailOS
If you want to install the launcher external to the RailOS create a shortcut in Windows and update the `Target` argument to point to the location of the program executable:

```sh
RailOSLauncher.exe --railos-location <railos-path>
```

## Building
The application is built using Pyinstaller under Poetry, to build it you will first need to download the Discord SDK from [here](https://dl-game-sdk.discordapp.net/2.5.6/discord_game_sdk.zip).
