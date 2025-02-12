# OTT Parsivel2 - I/O Plugin
Waggle Sensor Plugin for the [OTT Parsivel2 - Laser Disdrometer](https://www.ott.com/products/meteorological-sensors-26/ott-parsivel2-laser-weather-sensor-2392/).<br>

The plugin establishes a serial connection wtih the Parsivel2, writes data at user defined frequencies to a local file, and uploads to Beehive via the [Waggle](https://github.com/waggle-sensor) Plugin.

## Science
The OTT Parsivel2 is a laser disdrometer which is capable of measuring all types of preciptiation. The Parsivel2 classifies hydrometeors into 32 separate size and velocity classes, allowing users to calculate the type, amount, and intensity of preciptiation. From this particle size distribution, users are capable of calculating the equivalent radar reflectivity factor, among other parameters, to investigate microphyiscal characteristics of precipitation. 

## Usage

To execute the plugin use the following workflow:

### Conda Environment
A `environment.yml` file has been included within this repository to allow users to reproduce the application's conda environment.

#### Build the Conda Environment (if not previously created)
```bash
conda env create -f environment.yml
```

#### Activate the Conda Environment
```bash
conda activate waggle_parsivel
```
### Determine Serial Port
PySerial offers a handy toolist to list all serial ports currently in use. 
To determine the port for the instrument, run:
```bash
python -m serial.tools.list_ports
```

Otherwise, check USB devices locally:
```bash
ls -lh /dev/ttyUSB*
```

The default serial settings for the OTT Parsivel2 are
1. Baud Rate = 19200
1. Data Bits = 8
1. Parity = None
1. Stop Bits = 1

### Deployment

To execute the OTT Parsivel2 I/O Plugin:

#### Waggle Node (locally)
1. Before deploying the plugin locally on the waggle node, pull any recent changes and build the image
```bash
cd waggle-parsivel-io
sudo pluginctl build .
```
2. Next, deploy the plugin via `pluginctl`
```bash
sudo pluginctl deploy -n parsivel --selector zone=core --privileged 10.31.81.1:5000/local/waggle-parsivel-io
```
3. Verify the image deployed successfully
```bash
sudo pluginctl ps
```
#### Examples:
1. To change the default serial device:
```bash
sudo pluginctl deploy -n parsivel --selector zone=core --privileged 10.31.81.1:5000/local/waggle-parsivel-io -- --device /dev/ttyUSB5
```
1. To enable printing information to screen:
```bash
sudo pluginctl deploy -n parsivel --selector zone=core --privileged 10.31.81.1:5000/local/waggle-parsivel-io -- --verbose
```
1. To change the frequency of file generation to hourly:
```bash
sudo pluginctl deploy -n parsivel --selector zone=core --privileged 10.31.81.1:5000/local/waggle-parsivel-io -- --freq 60
```

#### Locally
If utilizing a local computer and not the Waggle node, reference the application directly
```bash
python app.py --device "/dev/ttyUSB5" --verbose
```

## Access the Data
```python
import sage_data_client

df = sage_data_client.query(
    start="2025-02-12T16:00:00Z",
    end="2025-02-12T17:00:00.000Z", 
    filter={
        "plugin": "10.31.81.1:5000/local/waggle-parsivel-io.*",
        "vsn": "W09F"
    }
)
```