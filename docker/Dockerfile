FROM ubuntu:22.04

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV VERILATOR_ROOT=/WORK_REPO/verilator
ENV PYMTL_VERILATOR_INCLUDE_DIR=/WORK_REPO/verilator/share/verilator/include
ENV PATH="/WORK_REPO/CGRA-Flow/tools/sv2v/bin:$PATH"
ENV PATH="/WORK_REPO/CGRA-Flow/tools/oss-cad-suite/bin:$PATH"
ENV YOSYS_EXE="/WORK_REPO/CGRA-Flow/tools/oss-cad-suite/bin/yosys"
ENV OPENROAD_EXE="/usr/bin/openroad"
ENV PATH="/WORK_REPO/verilator/bin:$PATH"

RUN mkdir /WORK_REPO \
    && cd /WORK_REPO \
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
    && cd /WORK_REPO/CGRA-Flow/CGRA-Mapper \
    && mkdir build && cd build && cmake .. \
    # Build for CGRA-Mapper
    && make \
    # VectorCGRA Git Sumbodule Update
    && cd /WORK_REPO/CGRA-Flow/VectorCGRA \
    && git submodule update --init \
    && cd /WORK_REPO \
    && apt-get -y install wget \
    && wget https://github.com/tancheng/pymtl-verilator/raw/master/verilator-travis-4.036.tar.gz \
    && tar -C /WORK_REPO -xzf verilator-travis-4.036.tar.gz \
    && rm -f /WORK_REPO/verilator-travis-4.036.tar.gz \
    # Install dependencies for VectorCGRA
    && apt-get -y install graphviz \
    && apt-get -y install git libffi-dev \
    && apt-get -y install python3.10-venv \
    && python3 -m venv /WORK_REPO/venv \
    && source /WORK_REPO/venv/bin/activate \
    && pip install py==1.11.0 \
    && pip install wheel \
    && pip install -U git+https://github.com/tancheng/pymtl3.1@yo-struct-list-fix \
    && pip install hypothesis \
    && pip install pytest \
    && pip install py-markdown-table \
    # Test with pytest for VectorCGRA
    && cd /WORK_REPO/CGRA-Flow/VectorCGRA \
    && mkdir -p build && cd build \
    # Install dependencies for mflowgen
    && apt-get install -y yosys \
    # Build for mflowgen
    && cd /WORK_REPO/CGRA-Flow/tools/mflowgen \
    && pip install -e . \
    # Test for mflowgen
    && mkdir build && cd build \
    && mflowgen run --design ../designs/GcdUnit \
    && make 3 \
    # Build for cacti
    && cd /WORK_REPO/CGRA-Flow/tools/cacti \
    && make \
    # Install dependencies for sv2v \
    && apt-get install -y curl \
    && curl -sSL https://get.haskellstack.org/ | sh \
    && export PATH="/root/.local/bin:$PATH" \
    && stack upgrade \
    && cd /WORK_REPO/CGRA-Flow/tools/sv2v \
    && make \
    && export PATH="/WORK_REPO/CGRA-Flow/tools/sv2v/bin:$PATH" \
    # Install dependencies for tkinter
    && apt-get install -y python3-tk \
    && pip install pillow \
    && pip install customtkinter \
    # Test for tkinter
    && cd /WORK_REPO/CGRA-Flow \
    && mkdir build && cd build \
    && cp ../docker/config.mk ./ \
    && cp ../docker/constraint.sdc ./ \
    # Install OpenROAD
    && cd /WORK_REPO/CGRA-Flow/tools \
    && wget https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-08-05/openroad_2.0_amd64-ubuntu22.04-2024-08-05.deb \
    && wget https://www.klayout.org/downloads/Ubuntu-22/klayout_0.29.6-1_amd64.deb \
    && wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2024-09-20/oss-cad-suite-linux-x64-20240920.tgz \
    && apt-get update \
    && apt-get install -y --fix-broken \
    && dpkg -i klayout_0.29.6-1_amd64.deb || true \
    && apt-get install -y --fix-broken \
    && tar zxvf oss-cad-suite-linux-x64-20240920.tgz -C ./ \
    && apt-get install -y ./openroad_2.0_amd64-ubuntu22.04-2024-08-05.deb \
    && apt-get install -y time \
    && rm -f *.deb *.tgz

WORKDIR "/WORK_REPO/CGRA-Flow/build"
#CMD ["/WORK_REPO/venv/bin/python", "../mode_dark_light.py"]
CMD ["tail", "-f", "/dev/null"]
