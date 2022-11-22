<p align="center">
<img
    style="display: block; 
           margin-left: auto;
           margin-right: auto;
           width: 30%;"
    src="https://raw.githubusercontent.com/Railway-Op-Sim/ROSLauncher/main/img/RailOSLauncher.png" 
    alt="Our logo">
</img>
</p>

# Discord Launcher for Railway Operation Simulator
RailOSLauncher provides a wrapper for the standard `railway.exe` provided by Railway Operation Simulator with the added feature of being able to broadcast your in game status as Discord activity.
The activity displayed includes operation mode (e.g. building or running a simulation), and if operating, which simulation is being run (and where metadata has been provided) the country it is
based in.

## Installation
Place the folder `RailOSLauncher` into the directory `<ros-installation>/Railway` where `ros-installation` is the location of your Railway Operation Simulator installation. Unfortunately we cannot directly provide the required SDKs
from Discord due to Licensing so you will need to download these yourself here [here](https://dl-game-sdk.discordapp.net/2.5.6/discord_game_sdk.zip). Place the DLL `discord_game_sdk.dll` into a folder `lib` within the launcher directory. The end directory structure in your ROS installation should look like:

```sh
|-- railway.exe
`-- RailOSLauncher
    |-- lib
    |   `-- discord_game_sdk.dll
    `-- ros_launcher.exe
```

## Building
The application is built using Pyinstaller under Poetry, to build it you will first need to download the Discord SDK from [here](https://dl-game-sdk.discordapp.net/2.5.6/discord_game_sdk.zip).
