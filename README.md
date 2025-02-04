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

As CGRA-Flow requires GUI, a script is provided for setting up the display:
```sh
 docker pull cgra/cgra-flow:20241028

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
 docker pull cgra/cgra-flow:20241028
 docker run -it cgra/cgra-flow:20241028
 source /WORK_REPO/venv/bin/activate
```

Execution
--------------------------------------------------------
```sh
 # Startup theme mode selector UI
 python launch.py
```


Mac user common issues
--------------------------------------------------------
> xauth command not found (XQuartz is missing on mac)
```sh
# install XQuartz
brew install --cask xquartz
# open XQuartz
open -a XQuartz
```
> _tkinter.TclError: couldn't connect to display "10.0.0.204:xx (Display not setup correctly)
```sh
# try enable all access
xhost+
# check display is valid or not
echo $DISPLAY
# if above command shows nothing, it means display is not set properly by XQuartz. Try manually assign a display number, for example 0
export DISPLAY=:0
xhost +
# modify run_mac_docker.sh line 8 
DISP_NUM=0

```

Installation
--------------------------------------------------------

CGRA-Flow requires Python3.7.

Refer to the build [scripts](https://github.com/tancheng/CGRA-Flow/blob/master/.github/workflows/main.yml) or look into specific repo for the manual installation if you don't want to use docker.


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
