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
[![Linux](https://svgshare.com/i/Zhy.svg)](https://svgshare.com/i/Zhy.svg)

CGRA-Flow is an integrated framework for CGRA compilation, exploration, synthesis, and development. It collects and integrates various open-source CGRA repos/components.

User Interface Snapshot/Demo
--------------------------------------------------------------------------
![Capture](https://user-images.githubusercontent.com/6756658/213010564-fa74b34e-218f-435e-9e8e-ef5a40f8899d.PNG)

A demo at repl.it (https://repl.it/@ChengTan/cgra-flow) shows some features of CGRA-Flow (the verilog generation and evaluation are not available due to the limited support of python environment). To explore all the features, please setup CGRA-Flow locally.


License
--------------------------------------------------------------------------

CGRA-Flow is offered under the terms of the Open Source Initiative BSD 3-Clause License. More information about this license can be found here:

  - http://choosealicense.com/licenses/bsd-3-clause
  - http://opensource.org/licenses/BSD-3-Clause


Installation
--------------------------------------------------------

CGRA-Flow requires Python3.7.

Refer to the build [scripts](https://github.com/tancheng/CGRA-Flow/blob/master/.github/workflows/main.yml) or look into specific repo for the installation.


Execution
--------------------------------------------------------
```
 $ mkdir build && cd build
 $ python ../launchUI.py
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

Publications leveraging (parts of) CGRA-Flow toolchain
--------------------------------------------------------------------------
- _"An Architecture Interface and Offload Model for Low-Overhead, Near-Data, Distributed Accelerators."_ MICRO'22.
- _"MATCHA: A Fast and Energy-Efficient Accelerator for Fully Homomorphic Encryption over the Torus."_ DAC'22.
- _"DRIPS: Dynamic Rebalancing of Pipelined Streaming Applications on CGRAs."_ HPCA'22.
- _"ARENA: Asynchronous Reconfigurable Accelerator Ring to Enable Data-Centric Parallel Computing."_ TPDS'21.
- _"Ultra-Elastic CGRAs for Irregular Loop Specialization."_ HPCA'21.
