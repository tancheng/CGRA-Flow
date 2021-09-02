"""
==========================================================================
CGRACL_test.py
==========================================================================
Test cases for CGRAs with CL data/config memory.

Author : Cheng Tan
  Date : Dec 28, 2019

"""

from pymtl3                       import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL

from ...lib.opt_type              import *
from ...lib.messages              import *
from ...lib.ctrl_helper           import *

from ...fu.flexible.FlexibleFuRTL import FlexibleFuRTL
from ...fu.single.AdderRTL        import AdderRTL
from ...fu.single.MulRTL          import MulRTL
from ...fu.single.PhiRTL          import PhiRTL
from ...fu.single.CompRTL         import CompRTL
from ...fu.single.MemUnitRTL      import MemUnitRTL
from ..CGRACL                     import CGRACL

import os

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DUT, FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 src_opt, preload_data, preload_const ):

    s.num_tiles = width * height
    AddrType = mk_bits( clog2( ctrl_mem_size ) )

    s.dut = DUT( FunctionUnit, FuList, DataType, PredicateType,
                 CtrlType, width, height, ctrl_mem_size, data_mem_size,
                 len( src_opt ), src_opt, preload_data, preload_const )

  def line_trace( s ):
    return s.dut.line_trace()

def run_sim( test_harness, max_cycles=7 ):
  test_harness.elaborate()
  test_harness.apply( SimulationPass() )
  test_harness.sim_reset()

  # Run simulation
  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while ncycles < max_cycles:
    test_harness.tick()
    ncycles += 1
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout
#  assert ncycles < max_cycles

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

#def test_cgra_2x2_universal():
#
#  num_tile_inports  = 4
#  num_tile_outports = 4
#  num_xbar_inports  = 6
#  num_xbar_outports = 8
#  ctrl_mem_size     = 8
#  width             = 2
#  height            = 2
#  RouteType     = mk_bits( clog2( num_xbar_inports + 1 ) )
#  AddrType      = mk_bits( clog2( ctrl_mem_size ) )
#  num_tiles     = width * height
#  ctrl_mem_size = 8
#  data_mem_size = 10
#  num_fu_in     = 4
#  DUT           = CGRACL
#  FunctionUnit  = FlexibleFuRTL
#  FuList        = [AdderRTL, MemUnitRTL]
#  DataType      = mk_data( 16, 1 )
#  CtrlType      = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
#  FuInType      = mk_bits( clog2( num_fu_in + 1 ) )
#  pickRegister  = [ FuInType( x+1 ) for x in range( num_fu_in ) ]
#  src_opt       = [[CtrlType( OPT_ADD_CONST, b1( 0 ), pickRegister, [
#                    RouteType(3), RouteType(2), RouteType(1), RouteType(0),
#                    RouteType(4), RouteType(4), RouteType(4), RouteType(4)], [b1(0)]*num_xbar_inports ),
#                    CtrlType( OPT_ADD, b1( 0 ), pickRegister, [
#                    RouteType(3),RouteType(2), RouteType(1), RouteType(0),
#                    RouteType(4), RouteType(4), RouteType(4), RouteType(4)], [b1(0)]*num_xbar_inports ),
#                    CtrlType( OPT_STR, b1( 0 ), pickRegister, [
#                    RouteType(3),RouteType(2), RouteType(1), RouteType(0),
#                    RouteType(4), RouteType(4), RouteType(4), RouteType(4)], [b1(0)]*num_xbar_inports ),
#                    CtrlType( OPT_SUB, b1( 0 ), pickRegister, [
#                    RouteType(3),RouteType(2), RouteType(1), RouteType(0),
#                    RouteType(4), RouteType(4), RouteType(4), RouteType(4)], [b1(0)]*num_xbar_inports ) ]
#                    for _ in range( num_tiles ) ]
#  print("see: ", src_opt)
#  preload_data  = [DataType(7, 1), DataType(7, 1), DataType(7, 1), DataType(7, 1)]
#  preload_const = [[DataType(2, 1)], [DataType(1, 1)],
#                   [DataType(4, 1)], [DataType(3, 1)]]
#  th = TestHarness( DUT, FunctionUnit, FuList, DataType, CtrlType,
#                    width, height, ctrl_mem_size, data_mem_size,
#                    src_opt, preload_data, preload_const )
#  run_sim( th )

def test_cgra_4x4_universal_fir():
  target_json = "config_fir.json"
  script_dir  = os.path.dirname(__file__)
  file_path   = os.path.join( script_dir, target_json )

  II                = 4
  num_tile_inports  = 4
  num_tile_outports = 4
  num_xbar_inports  = 6
  num_xbar_outports = 8
  ctrl_mem_size     = 8
  width             = 4
  height            = 4
  num_tiles         = width * height
  RouteType         = mk_bits( clog2( num_xbar_inports + 1 ) )
  AddrType          = mk_bits( clog2( ctrl_mem_size ) )
  num_tiles         = width * height
  ctrl_mem_size     = II
  data_mem_size     = 10
  num_fu_in         = 4
  DUT               = CGRACL
  FunctionUnit      = FlexibleFuRTL
  FuList            = [ AdderRTL, PhiRTL, MemUnitRTL, CompRTL, MulRTL ]
  DataType          = mk_data( 16, 1 )
  PredicateType     = mk_predicate( 1, 1 )
  CtrlType          = mk_ctrl( num_fu_in, num_xbar_inports, num_xbar_outports )
  FuInType          = mk_bits( clog2( num_fu_in + 1 ) )
  pickRegister      = [ FuInType( 0 ) for x in range( num_fu_in ) ]

  cgra_ctrl         = CGRACtrl( file_path, CtrlType, RouteType, width, height,
                                num_fu_in, num_xbar_inports, num_xbar_outports,
                                II )
  src_opt           = cgra_ctrl.get_ctrl()

  print(src_opt)

  preload_data      = [ DataType( 3, 1 ) ] * data_mem_size
  preload_const     = [ [ DataType( 1, 1 ) ] * II ] * num_tiles

  th = TestHarness( DUT, FunctionUnit, FuList, DataType, PredicateType,
                    CtrlType, width, height, ctrl_mem_size, data_mem_size,
                    src_opt, preload_data, preload_const )
  run_sim( th )

