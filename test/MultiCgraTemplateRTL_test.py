import sys
import os
# Add project root to sys.path so we can import VectorCGRA
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from VectorCGRA.multi_cgra.test import MeshMultiCgraTemplateRTL_test

def test_mesh_multi_cgra_universal(cmdline_opts, arch_yaml_path = "../build/arch.yaml"):
    """
    Test case for mesh multi-CGRA.
    Args:
        cmdline_opts: Command line options.
        arch_yaml_path: Relative path to the architecture YAML file.
    """
    arch_yaml_path = os.path.join(os.path.dirname(__file__), arch_yaml_path)
    print(f"arch_yaml_path: {arch_yaml_path}")
    MeshMultiCgraTemplateRTL_test.test_mesh_multi_cgra_universal(cmdline_opts, arch_yaml_path)
