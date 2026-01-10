#!/bin/bash


WORK_REPO="/WORK_REPO/CGRA-Flow"
VECTOR_CGRA_BUILD="$WORK_REPO/VectorCGRA/build"
OPENROAD_FLOW_DIR="/OpenROAD-flow-scripts/flow"

# Design Specifics
DESIGN_NAME="CgraTemplateRTL"
SRC_V_FILE="CgraTemplateRTL__provided__pickled.v"
OUT_V_FILE="CgraTemplateRTL.v"


echo "➡️ Current directory: $(pwd)"

# Check if VectorCGRA build directory exists
if [ ! -d "$VECTOR_CGRA_BUILD" ]; then
    echo "❌ Error: Build directory $VECTOR_CGRA_BUILD not found."
    exit 1
fi

cd "$VECTOR_CGRA_BUILD" || exit

# Converts systemverilog to verilog.
if [ -f "$SRC_V_FILE" ]; then
    echo "Converting SystemVerilog to Verilog..."
    sv2v "$SRC_V_FILE" > "$OUT_V_FILE"
else
    echo "❌ Error: Source file $SRC_V_FILE not found in $(pwd)"
    exit 1
fi


echo "Setting up OpenROAD flow directories..."

# Source directory for RTL
mkdir -p "$OPENROAD_FLOW_DIR/designs/src/$DESIGN_NAME/"
cp "$VECTOR_CGRA_BUILD/$OUT_V_FILE" "$OPENROAD_FLOW_DIR/designs/src/$DESIGN_NAME/"

# Platform directory (ASAP7)
ASAP7_DIR="$OPENROAD_FLOW_DIR/designs/asap7/$DESIGN_NAME"
mkdir -p "$ASAP7_DIR"

# Check for config and constraint files before copying
if [ -f "$WORK_REPO/docker/config.mk" ] && [ -f "$WORK_REPO/docker/constraint.sdc" ]; then
    cp "$WORK_REPO/docker/config.mk" "$ASAP7_DIR/"
    cp "$WORK_REPO/docker/constraint.sdc" "$ASAP7_DIR/"
else
    echo "❌ Error: Docker config.mk or constraint.sdc missing in $WORK_REPO/docker/"
    exit 1
fi

#Executes OpenROAD Flow.
echo "🚀 Starting OpenROAD Flow..."
cd "$OPENROAD_FLOW_DIR" || exit
# The routing stage involves intensive memory read/write operations.​
# Please ensure the server has ~100 GB of RAM available.
make DESIGN_CONFIG="$ASAP7_DIR/config.mk"
