FROM openroad/orfs@sha256:0d0dd3d8d346360a71f6325ce776a984c5a6296fc6e51956b53f136e1dd13462

# Sets Environment Variables.
ENV DEBIAN_FRONTEND=noninteractive \
    VERILATOR_ROOT=/WORK_REPO/verilator \
    PYMTL_VERILATOR_INCLUDE_DIR=/WORK_REPO/verilator/share/verilator/include \
    YOSYS_EXE="/OpenROAD-flow-scripts/tools/install/yosys/bin/yosys" \
    OPENROAD_EXE="/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad" \
    LLVM_RELEASE_URL="https://github.com/tancheng/CGRA-Flow/releases/download/llvm-project-6146a88-prebuild/llvm-project-6146a88-prebuild.tar.xz"
ENV PATH="/WORK_REPO/CGRA-Flow/tools/sv2v/bin:$PATH"
ENV PATH="/WORK_REPO/CGRA-Flow/tools/OpenROAD-flow-scripts/tools/install/OpenROAD/bin:$PATH"
ENV PATH="/WORK_REPO/verilator/bin/:$PATH"
ENV PATH="/WORK_REPO/llvm-project/build/bin:$PATH"

SHELL ["/bin/bash", "-c"]

# Install System Dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    llvm-12 llvm-12-dev llvm-12-tools clang-12 \
    graphviz libffi-dev python3-tk vim \
    wget curl git cmake make build-essential ninja-build \
    && curl -sSL https://get.haskellstack.org/ | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setups Workspace and Clones Repo.
WORKDIR /WORK_REPO
RUN git clone --recursive https://github.com/tancheng/CGRA-Flow.git \
    && ln -s /OpenROAD-flow-scripts/ /WORK_REPO/CGRA-Flow/tools/

# Builds C++ Tools (CGRA-Mapper, Cacti, sv2v)
RUN cd /WORK_REPO/CGRA-Flow/CGRA-Mapper && \
    mkdir build && cd build && cmake .. && make -j$(nproc) \
    && cd /WORK_REPO/CGRA-Flow/tools/cacti && make -j$(nproc) \
    && cd /WORK_REPO/CGRA-Flow/tools/sv2v && make -j$(nproc)

# Installs Verilator (Pre-compiled binary)
RUN wget https://github.com/tancheng/pymtl-verilator/raw/master/verilator-travis-4.036.tar.gz \
    && tar -C /WORK_REPO -xzf verilator-travis-4.036.tar.gz \
    && rm verilator-travis-4.036.tar.gz

# Python Environment Setup
RUN python3 -m venv /WORK_REPO/venv \
    && source /WORK_REPO/venv/bin/activate \
    && pip3 install --no-cache-dir py==1.11.0 wheel py-markdown-table pillow customtkinter PyYAML \
    && pip3 install --no-cache-dir -U git+https://github.com/tancheng/pymtl3.1@yo-struct-list-fix \
    && cd /WORK_REPO/CGRA-Flow/tools/mflowgen && pip3 install -e . \
    && rm -rf /root/.cache/pip

# Final Build Step for mflowgen
RUN source /WORK_REPO/venv/bin/activate && \
    cd /WORK_REPO/CGRA-Flow/tools/mflowgen && \
    mkdir -p build && cd build && \
    mflowgen run --design ../designs/GcdUnit && \
    make 3

# Download and extract pre-built LLVM.
RUN wget ${LLVM_RELEASE_URL} \
    && tar -xJf llvm-project-6146a88.tar.xz \
    && rm llvm-project-6146a88.tar.xz

# Build dataflow
RUN source /WORK_REPO/venv/bin/activate && \
    cd /WORK_REPO/CGRA-Flow/dataflow && \
    mkdir -p build && cd build \
    && cmake -G Ninja .. \
      -DLLVM_DIR=/WORK_REPO/llvm-project/build/lib/cmake/llvm \
      -DMLIR_DIR=/WORK_REPO/llvm-project/build/lib/cmake/mlir \
      -DMLIR_SOURCE_DIR=/WORK_REPO/llvm-project/mlir \
      -DMLIR_BINARY_DIR=/WORK_REPO/llvm-project/build \
      -DCMAKE_CXX_FLAGS="-std=c++17" \
    && ninja

WORKDIR /WORK_REPO/CGRA-Flow/build
CMD ["tail", "-f", "/dev/null"]
