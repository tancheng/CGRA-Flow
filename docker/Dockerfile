FROM ubuntu:22.04

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/verilator/bin:$PATH"
ENV VERILATOR_ROOT=/root/verilator
ENV PYMTL_VERILATOR_INCLUDE_DIR=/root/verilator/share/verilator/include

RUN mkdir ${HOME}/cgra \
    && cd ${HOME}/cgra \
    && apt-get -y update \
    && apt-get -y install git \
    && apt-get -y install python3.10 \
    && apt-get -y install python3-pip \
    && git clone https://github.com/tancheng/CGRA-Flow.git \
    && cd CGRA-Flow \
    && git submodule update --init \
    # Install LLVM and Clang for CGRA-Mapper
    && apt-get -y install cmake \
    && apt-get -y install llvm-12 llvm-12-dev llvm-12-tools clang-12 \
    && apt-get -y install build-essential \
    # Configure CMake for CGRA-Mapper
    && cd ${HOME}/cgra/CGRA-Flow/CGRA-Mapper \
    && mkdir build && cd build && cmake .. \
    # Build for CGRA-Mapper
    && make \
    # VectorCGRA Git Sumbodule Update
    && cd ${HOME}/cgra/CGRA-Flow/VectorCGRA \
    && git submodule update --init \
    && apt-get -y install wget \
    && wget https://github.com/tancheng/pymtl-verilator/raw/master/verilator-travis-4.036.tar.gz \
    && tar -C ${HOME} -xzf verilator-travis-4.036.tar.gz \
    && rm -f ${HOME}/verilator-travis-4.036.tar.gz \
    # Install dependencies for VectorCGRA
    && apt-get -y install graphviz \
    && apt-get -y install git libffi-dev \
    && apt-get -y install python3.10-venv \
    && python3 -m venv ${HOME}/venv \
    && pip install py==1.11.0 \
    && pip install wheel \
    && pip install -U git+https://github.com/tancheng/pymtl3.1@yo-struct-list-fix \
    && pip install hypothesis \
    && pip install pytest \
    && pip install py-markdown-table \
    # Test with pytest for VectorCGRA
    && cd ${HOME}/cgra/CGRA-Flow/VectorCGRA \
    && mkdir -p build && cd build \
    # Install dependencies for mflowgen
    && apt-get install -y yosys \
    # Build for mflowgen
    && cd ${HOME}/cgra/CGRA-Flow/tools/mflowgen \
    && pip install -e . \
    # Test for mflowgen
    && mkdir build && cd build \
    && mflowgen run --design ../designs/GcdUnit \
    && make 3 \
    # Build for cacti
#    && cd ${HOME}/cgra/CGRA-Flow/tools/cacti \
#    && make \
    # Install dependencies for sv2v \
    # && stack upgrade \
#    && cd ${HOME}/cgra/CGRA-Flow/tools/sv2v \
#    && make \
    # Install dependencies for tkinter
    && apt-get install -y python3-tk \
    # && source ${HOME}/venv/bin/activate \
    && pip install pillow \
    # Test for tkinter
    && cd ${HOME}/cgra/CGRA-Flow \
    && mkdir build && cd build \
    && source ${HOME}/venv/bin/activate

ENTRYPOINT ["python", "../mode_dark_light.py"]
#CMD ["tail", "-f", "/dev/null"]