<pre>
========================================================

   ________________  ___         ________
  / ____/ ____/ __ \/   |       / ____/ /___ _      __
 / /   / / __/ /_/ / /| |______/ /_  / / __ \ | /| / /
/ /___/ /_/ / _, _/ ___ /_____/ __/ / / /_/ / |/ |/ /
\____/\____/_/ |_/_/  |_|    /_/   /_/\____/|__/|__/


========================================================
</pre>
[![Github Action](https://github.com/tancheng/CGRA-Flow/actions/workflows/main.yml/badge.svg)](https://github.com/tancheng/CGRA-Flow/actions/workflows/main.yml)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

CGRA-Flow is an integrated framework for CGRA compilation, exploration, synthesis, and development.

User Interface Snapshot/Demo
--------------------------------------------------------------------------
![20241028](https://github.com/user-attachments/assets/305fa79d-73b9-4512-ab85-0cecc6153986)

A demo at repl.it (https://repl.it/@ChengTan/cgra-flow) shows some features of CGRA-Flow (the verilog generation and evaluation are not available due to *repl.it*'s limited support of python environment). To explore all the features, please setup CGRA-Flow locally or leverage the docker image.


Docker
--------------------------------------------------------
The docker image is available
[here](https://hub.docker.com/r/cgra/cgra-flow/tags).
The Neura artifact is available on the [neura-asplos-ae](https://github.com/tancheng/CGRA-Flow/tree/neura-asplos-ae) branch.

> **Recommended machine configuration**
> * CPU: >= 6 cores
> * Memory: 25~30G
>
> **2x2 tiles run time**:
> | clk_period (ps) | frequency (Hz) | time (hour) |
> |-------|-------|-------|
> | 1000            | 1G             | ~40         |
> | 10,000          | 100M           | ~7          |
> | 100,000         | 10M            | ~7          |

> [!TIP]
> If you encounter an OOM (out of memory) error during the RTL2Layout stage, this indicates insufficient memory on your machine.
> Based on our experience, routing for a single CGRA with 2×2 tiles requires approximately 100 GB of memory.
> You can switch to a machine with larger memory capacity to proceed with RTL2Layout.
> We provided a RTL2Layout [script](https://github.com/tancheng/CGRA-Flow/blob/master/Rtl2Layout.sh) without invoking the GUI. Please ensure to modify any custom parameters accordingly.

As CGRA-Flow requires GUI, a script is provided for setting up the display:
```sh
 docker pull cgra/neura-flow:latest

 # For Mac users:
 sh ./run_mac_docker.sh

 # Windows Docker customtkinter style UI (Please setup GUI (X-11) first)
 # In WSL, execute below script, it will enter container and config x11 DISPLAY automatically
 sh ./run_windows_docker.sh

 # Don't forget to activate the python virtual environment once you are in the container:
 source /WORK_REPO/venv/bin/activate
```

Otherwise, if you don't need the GUI, development can be performed in the container with the environment well set up:
```sh
 docker pull cgra/neura-flow:latest
 docker run -it cgra/neura-flow:latest
 source /WORK_REPO/venv/bin/activate
```

Building Docker Image from Dockerfile
--------------------------------------------------------
If you prefer to build the Docker image locally:

```sh
 # For Intel/AMD CPU(x86_64)
 docker build -t cgra/neura-flow:latest .
 # For Apple Silicon(arm64)
 docker buildx build --platform linux/amd64 -t cgra/neura-flow:latest .
```

Execution
--------------------------------------------------------
```sh
 # Startup theme mode selector UI
 python launch.py
```


Mac user [debugging and troubleshooting steps doc](/doc/debug/DEBUGGING.md)
--------------------------------------------------------

Installation
--------------------------------------------------------

CGRA-Flow requires Python3.7.

Refer to the build [scripts](https://github.com/tancheng/CGRA-Flow/blob/master/.github/workflows/main.yml) or look into specific repo for the manual installation if you don't want to use docker.

Contribution Guide
--------------------------------------------------------
👋 Welcome Contributors!

To contribute to this project, you can clone the Github repository and mount it as a volume 
in the Docker container. This allow you to edit code on your host machine while testing changes inside
the container environment.
Update the Docker run command to mount your local repository(take `run_windows_docker.sh` as an example):
```shell
IMAGE=cgra/neura-flow:latest
CONTAINER=neuraflow
XSOCK=/tmp/.X11-unix
# for developer: mount the upstream repo to the container.
# Please update the path to the actual path on your machine.
MOUNT_PATH=/path/to/your/cloned/CGRA-Flow:/path/to/container
sudo docker run \
    -it \
    --name=$CONTAINER \
    -v $XSOCK:$XSOCK:rw \
    -v $MOUNT_PATH \
    -e DISPLAY=$DISPLAY \
    $IMAGE \
    /bin/bash
```

Citation
--------------------------------------------------------------------------
```
@inproceedings{tan2020opencgra,
  title={OpenCGRA: An open-source unified framework for modeling, testing, and evaluating CGRAs},
  author={Tan, Cheng and Xie, Chenhao and Li, Ang and Barker, Kevin J and Tumeo, Antonino},
  booktitle={2020 IEEE 38th International Conference on Computer Design (ICCD)},
  pages={381--388},
  year={2020},
  organization={IEEE}
}
```


License
--------------------------------------------------------------------------

CGRA-Flow is offered under the terms of the Open Source Initiative BSD 3-Clause License. More information about this license can be found here:

  - http://choosealicense.com/licenses/bsd-3-clause
  - http://opensource.org/licenses/BSD-3-Clause



OpenAI GPT (coming soon)
--------------------------------------------------------------------------
[Arch Wizard](https://chat.openai.com/g/g-fUWqOuKFe-arch-wizard).

![](https://github.com/tancheng/CGRA-Flow/assets/6756658/07db560a-65aa-4bed-8f0a-f0b3c07df893)
