# rsu-protocol

## Introduction
This paper proposed a specification for a network protocol that will be used for remote software
update of devices over the internet. The remote software update (RSU) protocol will lie on top of
QUIC and will live in the user space of both the server and the devices. 

The RSU protocol acts as a communication channel between a central server and the remote
devices. Through this network, the remote devices can request software updates from the server and the server can send software updates to the devices.

The RSU protocol is implemented in Python.



## Demo Video
Watch this video on youtube: [RSU Protocol Demo](https://youtu.be/JYie57dOFFs)


## Implementation Summary
Read the implementation summary [here](./P3-Implementation%20Summary.pdf)


## Features
- **Secure Communication**: The RSU protocol uses TLS 1.3 to secure the communication between the server and the devices.
- **Reliable Communication**: The RSU protocol uses QUIC to provide reliable communication between the server and the devices.
- **Software Update**: The RSU protocol allows the devices to request software updates from the server and the server to send software updates to the devices.


## Installation

**1. Generate Certificates (Optional)**

```bash
sh ./certs/generate.sh
```

**2. Create a virtual environment**
```bash
python3 -m venv .venv
```
**3. Activate the virtual environment**
```bash
source ./.venv/bin/activate
```
**4. Install the requirements**
```bash
pip install -r requirements.txt
```

**5. Run the server**
```bash
python3 rsu.py server
```

Optional arguments:

- `--cert`: The path to the server certificate file. Default: `certs/server.crt`
- `--key`: The path to the server private key file. Default: `certs/server.key`
- `--port`: The port number to listen on. Default: `4433`
- `--host`: The host address to listen on. Default: `localhost`


**6. Run the client**<br>
The client should be run only after the server is running.

```bash
python3 rsu.py client
```

Optional arguments:
- `--cert`: The path to the client certificate file. Default: `certs/client.crt`
- `--key`: The path to the client private key file. Default: `certs/client.key`
- `--port`: The port number to connect to. Default: `4433`
- `--host`: The host address to connect to. Default: `localhost`

