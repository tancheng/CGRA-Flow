export PLATFORM  = asap7
export DESIGN_NAME  = CgraTemplateRTL
export VERILOG_FILES = $(sort $(wildcard ./designs/src/$(DESIGN_NAME)/*.v))
export SDC_FILE  = ./designs/$(PLATFORM)/$(DESIGN_NAME)/constraint.sdc
#export ABC_AREA             = 1
export SYNTH_HIERARCHICAL = 1
export RTLMP_FLOW = True
export ENABLE_DPO = True
export CORE_UTILIZATION  = 10
export CORE_ASPECT_RATIO  = 1
export GPL_ROUTABILITY_DRIVEN = 1
export CORE_MARGIN  = 5
export PLACE_DENSITY = 0.2
export TNS_END_PERCENT = 100
export CTS_BUF_CELL = BUFx8_ASAP7_75t_R
#export CTS_BUF_DISTANCE = 10000
# If this design isn't quickly done in detailed routing, something is wrong.
# At time of adding this option, only 12 iterations were needed for 0
# violations.
export DETAILED_ROUTE_ARGS  = -save_guide_updates -verbose 1 -droute_end_iter 45
export RECOVER_POWER = 50
# since we are specifying DETAILED_ROUTE_ARGS, we need to communicate the
# same information to other stages in the flow.
export MIN_ROUTING_LAYER = M1
export MAX_ROUTING_LAYER = M7

export VIA_IN_PIN_MIN_LAYER = 1
export VIA_IN_PIN_MAX_LAYER = 1

# works with 28 or more iterations as of writing, so give it a few more.
export GLOBAL_ROUTE_ARGS=-congestion_iterations 40 -verbose
#export FASTROUTE_TCL = ./designs/$(PLATFORM)/TileRTL__286c363070523335/fastroute.tcl

export configure_cts_characterization [-max_slew max_slew][-max_cap max_cap][-slew_steps slew_steps] [-cap_steps cap_steps]

#export global_placement  [-routability_driven] [-routability_check_overflow routability_check_overflow] [-routability_max_density routability_max_density]
export global_placement = -routability_driven -routability_check_overflow 0.15 -routability_max_density 0.5
#export detailed_route_debug -dr

export REMOVE_CELLS_FOR_EQY = TAPCELL*
export GPL_TIMING_DRIVEN = 0
