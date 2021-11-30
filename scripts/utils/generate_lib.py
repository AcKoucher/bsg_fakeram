import os
import math
import time
import datetime
import sys

################################################################################
# GENERATE LIBERTY VIEW
#
# Generate a .lib file based on the given SRAM.
################################################################################

def generate_lib( mem ):

    # Make sure the data types are correct
    name              = str(mem.name)
    depth             = int(mem.depth)
    bits              = int(mem.width_in_bits)
    area              = float(mem.area_um2)
    x                 = float(mem.width_um)
    y                 = float(mem.height_um)
    tsetup_ns         = float(mem.t_setup_ns)
    thold_ns          = float(mem.t_hold_ns)
    tcq_ns            = float(mem.access_time_ns)
    voltage           = float(mem.process.voltage)
    min_period_ns     = float(mem.cycle_time_ns)
    fo4_ns            = float(mem.fo4_ps)/1e3
    min_driver_in_cap_pf = float(mem.cap_input_pf)
    leakage_mw        = float(mem.standby_leakage_per_bank_mW)
    clkpindynamic_mw  = float(mem.pin_dynamic_power_mW)
    pindynamic_mw     = float(mem.pin_dynamic_power_mW)*1e-2

    time_unit         = str(mem.process.liberty_time_unit)
    cap_unit          = str(mem.process.liberty_cap_unit)
    power_unit        = str(mem.process.liberty_power_unit)

    if time_unit == "ns":
        tsetup = tsetup_ns
        thold = thold_ns
        tcq = tcq_ns
        min_period = min_period_ns
        fo4 = fo4_ns
    elif time_unit == "ps":
        tsetup = tsetup_ns * 1e+3
        thold = thold_ns * 1e+3
        tcq = tcq_ns * 1e+3
        min_period = min_period_ns * 1e+3
        fo4 = fo4_ns * 1e+3
    else:
        print("unknown libertyTimeUnit")
        sys.exit()

    if cap_unit == "pf":
        min_driver_in_cap = min_driver_in_cap_pf
    elif cap_unit == "ff":
        min_driver_in_cap = min_driver_in_cap_pf * 1e+3
    else:
        print("unknown libertyCapUnit")
        sys.exit()

    if power_unit == "uw":
        clkpindynamic = clkpindynamic_mw * 1e+3
        pindynamic = pindynamic_mw * 1e+3
        leakage = leakage_mw * 1e+3
    elif power_unit == "nw":
        clkpindynamic = clkpindynamic_mw * 1e+6
        pindynamic = pindynamic_mw * 1e+6
        leakage = leakage_mw * 1e+6
    else:
        print("unknown libertyPowerUnit")
        sys.exit()

    # Only support 1RW srams. At some point, expose these as well!
    num_rwport = mem.rw_ports

    # Number of bits for address
    addr_width    = math.ceil(math.log2(mem.depth))
    addr_width_m1 = addr_width-1

    # Get the date
    d = datetime.date.today()
    date = d.isoformat()
    current_time = time.strftime("%H:%M:%SZ", time.gmtime())

    # TODO: Arbitrary indicies for the NLDM table. This is used for Clk->Q arcs
    # as well as setup/hold times. We only have a single value for these, there
    # are two options. 1. adding some sort of static variation of the single
    # value for each table entry, 2. use the same value so all interpolated
    # values are the same. The 1st is more realistic but depend on good variation
    # values which is process sepcific and I don't have a strategy for
    # determining decent variation values without breaking NDA so right now we
    # have no variations.
    #
    # The table indicies are main min/max values for interpolation. The tools
    # typically don't like extrapolation so a large range is nice, but makes the
    # single value strategy described above even more unrealistic.
    #
    min_slew = 1   * fo4               ;# arbitrary (1x fo4, fear that 0 would cause issues)
    max_slew = 25  * fo4               ;# arbitrary (25x fo4 as ~100x fanout ... i know that is not really how it works)
    min_load = 1   * min_driver_in_cap ;# arbitrary (1x driver, fear that 0 would cause issues)
    max_load = 100 * min_driver_in_cap ;# arbitrary (100x driver)

    slew_indicies = '%.3f, %.3f' % (min_slew, max_slew) ;# input pin transisiton with between 1xfo4 and 100xfo4
    load_indicies = '%.3f, %.3f' % (min_load, max_load) ;# output capacitance table between a 1x and 32x inverter

    # Start generating the LIB file

    LIB_file = open(os.sep.join([mem.results_dir, name + '.lib']), 'w')

    LIB_file.write( 'library(%s) {\n' % name)
    LIB_file.write( '    technology (cmos);\n')
    LIB_file.write( '    delay_model : table_lookup;\n')
    LIB_file.write( '    revision : 1.0;\n')
    LIB_file.write( '    date : "%s %s";\n' % (date, current_time))
    LIB_file.write( '    comment : "SRAM";\n')
    LIB_file.write( '    time_unit : "1%s";\n' % time_unit)
    LIB_file.write( '    voltage_unit : "1V";\n')
    LIB_file.write( '    current_unit : "1uA";\n')
    LIB_file.write( '    leakage_power_unit : "1%s";\n' % power_unit)
    LIB_file.write( '    nom_process : 1;\n')
    LIB_file.write( '    nom_temperature : 25.000;\n')
    LIB_file.write( '    nom_voltage : %s;\n' % voltage)
    LIB_file.write( '    capacitive_load_unit (1,%s);\n\n' % cap_unit)
    LIB_file.write( '    pulling_resistance_unit : "1kohm";\n\n')
    LIB_file.write( '    operating_conditions(tt_1.0_25.0) {\n')
    LIB_file.write( '        process : 1;\n')
    LIB_file.write( '        temperature : 25.000;\n')
    LIB_file.write( '        voltage : %s;\n' % voltage)
    LIB_file.write( '        tree_type : balanced_tree;\n')
    LIB_file.write( '    }\n')
    LIB_file.write( '\n')

    LIB_file.write( '    /* default attributes */\n')
    LIB_file.write( '    default_cell_leakage_power : 0;\n')
    LIB_file.write( '    default_fanout_load : 1;\n')
    LIB_file.write( '    default_inout_pin_cap : 0.0;\n')
    LIB_file.write( '    default_input_pin_cap : 0.0;\n')
    LIB_file.write( '    default_output_pin_cap : 0.0;\n')
    LIB_file.write( '    default_input_pin_cap : 0.0;\n')
    LIB_file.write( '    default_max_transition : %.3f;\n\n' % max_slew)
    LIB_file.write( '    default_operating_conditions : tt_1.0_25.0;\n')
    LIB_file.write( '    default_leakage_power_density : 0.0;\n')
    LIB_file.write( '\n')

    LIB_file.write( '    /* additional header data */\n')
    LIB_file.write( '    slew_derate_from_library : 1.000;\n')
    LIB_file.write( '    slew_lower_threshold_pct_fall : 20.000;\n')
    LIB_file.write( '    slew_upper_threshold_pct_fall : 80.000;\n')
    LIB_file.write( '    slew_lower_threshold_pct_rise : 20.000;\n')
    LIB_file.write( '    slew_upper_threshold_pct_rise : 80.000;\n')
    LIB_file.write( '    input_threshold_pct_fall : 50.000;\n')
    LIB_file.write( '    input_threshold_pct_rise : 50.000;\n')
    LIB_file.write( '    output_threshold_pct_fall : 50.000;\n')
    LIB_file.write( '    output_threshold_pct_rise : 50.000;\n\n')
    LIB_file.write( '\n')

    #  LIB_file.write( '    /* k-factors */\n')
    #  LIB_file.write( '    k_process_cell_fall : 1;\n')
    #  LIB_file.write( '    k_process_cell_leakage_power : 0;\n')
    #  LIB_file.write( '    k_process_cell_rise : 1;\n')
    #  LIB_file.write( '    k_process_fall_transition : 1;\n')
    #  LIB_file.write( '    k_process_hold_fall : 1;\n')
    #  LIB_file.write( '    k_process_hold_rise : 1;\n')
    #  LIB_file.write( '    k_process_internal_power : 0;\n')
    #  LIB_file.write( '    k_process_min_pulse_width_high : 1;\n')
    #  LIB_file.write( '    k_process_min_pulse_width_low : 1;\n')
    #  LIB_file.write( '    k_process_pin_cap : 0;\n')
    #  LIB_file.write( '    k_process_recovery_fall : 1;\n')
    #  LIB_file.write( '    k_process_recovery_rise : 1;\n')
    #  LIB_file.write( '    k_process_rise_transition : 1;\n')
    #  LIB_file.write( '    k_process_setup_fall : 1;\n')
    #  LIB_file.write( '    k_process_setup_rise : 1;\n')
    #  LIB_file.write( '    k_process_wire_cap : 0;\n')
    #  LIB_file.write( '    k_process_wire_res : 0;\n')
    #  LIB_file.write( '    k_temp_cell_fall : 0.000;\n')
    #  LIB_file.write( '    k_temp_cell_rise : 0.000;\n')
    #  LIB_file.write( '    k_temp_hold_fall : 0.000;\n')
    #  LIB_file.write( '    k_temp_hold_rise : 0.000;\n')
    #  LIB_file.write( '    k_temp_min_pulse_width_high : 0.000;\n')
    #  LIB_file.write( '    k_temp_min_pulse_width_low : 0.000;\n')
    #  LIB_file.write( '    k_temp_min_period : 0.000;\n')
    #  LIB_file.write( '    k_temp_rise_propagation : 0.000;\n')
    #  LIB_file.write( '    k_temp_fall_propagation : 0.000;\n')
    #  LIB_file.write( '    k_temp_rise_transition : 0.0;\n')
    #  LIB_file.write( '    k_temp_fall_transition : 0.0;\n')
    #  LIB_file.write( '    k_temp_recovery_fall : 0.000;\n')
    #  LIB_file.write( '    k_temp_recovery_rise : 0.000;\n')
    #  LIB_file.write( '    k_temp_setup_fall : 0.000;\n')
    #  LIB_file.write( '    k_temp_setup_rise : 0.000;\n')
    #  LIB_file.write( '    k_volt_cell_fall : 0.000;\n')
    #  LIB_file.write( '    k_volt_cell_rise : 0.000;\n')
    #  LIB_file.write( '    k_volt_hold_fall : 0.000;\n')
    #  LIB_file.write( '    k_volt_hold_rise : 0.000;\n')
    #  LIB_file.write( '    k_volt_min_pulse_width_high : 0.000;\n')
    #  LIB_file.write( '    k_volt_min_pulse_width_low : 0.000;\n')
    #  LIB_file.write( '    k_volt_min_period : 0.000;\n')
    #  LIB_file.write( '    k_volt_rise_propagation : 0.000;\n')
    #  LIB_file.write( '    k_volt_fall_propagation : 0.000;\n')
    #  LIB_file.write( '    k_volt_rise_transition : 0.0;\n')
    #  LIB_file.write( '    k_volt_fall_transition : 0.0;\n')
    #  LIB_file.write( '    k_volt_recovery_fall : 0.000;\n')
    #  LIB_file.write( '    k_volt_recovery_rise : 0.000;\n')
    #  LIB_file.write( '    k_volt_setup_fall : 0.000;\n')
    #  LIB_file.write( '    k_volt_setup_rise : 0.000;\n')
    #  LIB_file.write( '\n')

    LIB_file.write( '    lu_table_template(%s_mem_out_slew_template) {\n' % name )
    LIB_file.write( '        variable_1 : total_output_net_capacitance;\n')
    LIB_file.write( '            index_1 ("1000, 1001");\n')
    LIB_file.write( '    }\n')
    LIB_file.write( '    library_features(report_delay_calculation);\n')
    LIB_file.write( '    type (%s_DATA) {\n' % name )
    LIB_file.write( '        base_type : array ;\n')
    LIB_file.write( '        data_type : bit ;\n')
    LIB_file.write( '        bit_width : %d;\n' % bits)
    LIB_file.write( '        bit_from : %d;\n' % (int(bits)-1))
    LIB_file.write( '        bit_to : 0 ;\n')
    LIB_file.write( '        downto : true ;\n')
    LIB_file.write( '    }\n')
    LIB_file.write( '    type (%s_ADDRESS) {\n' % name)
    LIB_file.write( '        base_type : array ;\n')
    LIB_file.write( '        data_type : bit ;\n')
    LIB_file.write( '        bit_width : %d;\n' % addr_width)
    LIB_file.write( '        bit_from : %d;\n' % addr_width_m1)
    LIB_file.write( '        bit_to : 0 ;\n')
    LIB_file.write( '        downto : true ;\n')
    LIB_file.write( '    }\n')

    LIB_file.write( 'cell(%s) {\n' % name )
    LIB_file.write( '    area : %.3f;\n' % area)
    #LIB_file.write( '    dont_use : true;\n')
    #LIB_file.write( '    dont_touch : true;\n')
    LIB_file.write( '    interface_timing : true;\n')
    LIB_file.write( '    memory() {\n')
    LIB_file.write( '        type : ram;\n')
    LIB_file.write( '        address_width : %d;\n' % addr_width)
    LIB_file.write( '        word_width : %d;\n' % bits)
    LIB_file.write( '    }\n')

    LIB_file.write('    pin(clk)   {\n')
    LIB_file.write('        direction : input;\n')
    LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap*5)) ;# Clk pin is usually higher cap for fanout control, assuming an x5 driver.
    LIB_file.write('        clock : true;\n')
    #LIB_file.write('        max_transition : 0.01;\n') # Max rise/fall time
    #LIB_file.write('        min_pulse_width_high : %.3f ;\n' % (min_period))
    #LIB_file.write('        min_pulse_width_low  : %.3f ;\n' % (min_period))
    LIB_file.write('        min_period           : %.3f ;\n' % (min_period))
    #LIB_file.write('        minimum_period(){\n')
    #LIB_file.write('            constraint : %.3f ;\n' % min_period)
    #LIB_file.write('            when : "1";\n')
    #LIB_file.write('            sdf_cond : "1";\n')
    #LIB_file.write('        }\n')

    # This is wrong. internal power is not the same as dynamuc power. -cherry
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            rise_power(scalar) {\n')
    LIB_file.write('                values ("%.3f")\n' % clkpindynamic)
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(scalar) {\n')
    LIB_file.write('                values ("%.3f")\n' % clkpindynamic)
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')
    LIB_file.write('\n')

    for i in range(int(num_rwport)) :
      LIB_file.write('    bus(rd_out)   {\n')
      LIB_file.write('        bus_type : %s_DATA;\n' % name)
      LIB_file.write('        direction : output;\n')
      LIB_file.write('        max_capacitance : %.3f;\n' % max_load) ;# Based on 32x inverter being a common max (or near max) inverter
      LIB_file.write('        memory_read() {\n')
      LIB_file.write('            address : addr_in;\n')
      LIB_file.write('        }\n')
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin : "clk" ;\n')
      LIB_file.write('            timing_type : rising_edge;\n')
      LIB_file.write('            timing_sense : non_unate;\n')
      LIB_file.write('            cell_rise(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tcq)
      LIB_file.write('            }\n')
      LIB_file.write('            cell_fall(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tcq)
      LIB_file.write('            }\n')
      LIB_file.write('            rise_transition(%s_mem_out_slew_template) {\n' % name)
      LIB_file.write('                index_1 ("%s");\n' % load_indicies)
      LIB_file.write('                values ("%.3f, %.3f")\n' % (min_slew, max_slew))
      LIB_file.write('            }\n')
      LIB_file.write('            fall_transition(%s_mem_out_slew_template) {\n' % name)
      LIB_file.write('                index_1 ("%s");\n' % load_indicies)
      LIB_file.write('                values ("%.3f, %.3f")\n' % (min_slew, max_slew))
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('    }\n')

    for i in range(int(num_rwport)) :
      LIB_file.write('    pin(we_in){\n')
      LIB_file.write('        direction : input;\n')
      LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin : clk;\n')
      LIB_file.write('            timing_type : setup_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('        } \n')
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin : clk;\n')
      LIB_file.write('            timing_type : hold_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('        internal_power(){\n')
      LIB_file.write('            rise_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('    }\n')

    LIB_file.write('    pin(ce_in){\n')
    LIB_file.write('        direction : input;\n')
    LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : clk;\n')
    LIB_file.write('            timing_type : setup_rising ;\n')
    LIB_file.write('            rise_constraint(scalar) {\n')
    LIB_file.write('                values ("%.3f");\n' % tsetup)
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(scalar) {\n')
    LIB_file.write('                values ("%.3f");\n' % tsetup)
    LIB_file.write('            }\n')
    LIB_file.write('        } \n')
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : clk;\n')
    LIB_file.write('            timing_type : hold_rising ;\n')
    LIB_file.write('            rise_constraint(scalar) {\n')
    LIB_file.write('                values ("%.3f");\n' % thold)
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(scalar) {\n')
    LIB_file.write('                values ("%.3f");\n' % thold)
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            rise_power(scalar) {\n')
    LIB_file.write('                values ("%.3f");\n' % pindynamic)
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(scalar) {\n')
    LIB_file.write('                values ("%.3f");\n' % pindynamic)
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')

    for i in range(int(num_rwport)) :
      LIB_file.write('    bus(addr_in)   {\n')
      LIB_file.write('        bus_type : %s_ADDRESS;\n' % name)
      LIB_file.write('        direction : input;\n')
      LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin : clk;\n')
      LIB_file.write('            timing_type : setup_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('        } \n')
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin : clk;\n')
      LIB_file.write('            timing_type : hold_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('        internal_power(){\n')
      LIB_file.write('            rise_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('    }\n')

    for i in range(int(num_rwport)) :
      LIB_file.write('    bus(wd_in)   {\n')
      LIB_file.write('        bus_type : %s_DATA;\n' % name)
      LIB_file.write('        memory_write() {\n')
      LIB_file.write('            address : addr_in;\n')
      LIB_file.write('            clocked_on : "clk";\n')
      LIB_file.write('        }\n')
      LIB_file.write('        direction : input;\n')
      LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin     : clk;\n')
      LIB_file.write('            timing_type     : setup_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('        } \n')
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin     : clk;\n')
      LIB_file.write('            timing_type     : hold_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('        internal_power(){\n')
      LIB_file.write('            when : "(! (we_in) )";\n')
      LIB_file.write('            rise_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('        internal_power(){\n')
      LIB_file.write('            when : "(we_in)";\n')
      LIB_file.write('            rise_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('    }\n')

    for i in range(int(num_rwport)) :
      LIB_file.write('    bus(w_mask_in)   {\n')
      LIB_file.write('        bus_type : %s_DATA;\n' % name)
      LIB_file.write('        memory_write() {\n')
      LIB_file.write('            address : addr_in;\n')
      LIB_file.write('            clocked_on : "clk";\n')
      LIB_file.write('        }\n')
      LIB_file.write('        direction : input;\n')
      LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin     : clk;\n')
      LIB_file.write('            timing_type     : setup_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % tsetup)
      LIB_file.write('            }\n')
      LIB_file.write('        } \n')
      LIB_file.write('        timing() {\n')
      LIB_file.write('            related_pin     : clk;\n')
      LIB_file.write('            timing_type     : hold_rising ;\n')
      LIB_file.write('            rise_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_constraint(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % thold)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('        internal_power(){\n')
      LIB_file.write('            when : "(! (we_in) )";\n')
      LIB_file.write('            rise_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('        internal_power(){\n')
      LIB_file.write('            when : "(we_in)";\n')
      LIB_file.write('            rise_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('            fall_power(scalar) {\n')
      LIB_file.write('                values ("%.3f");\n' % pindynamic)
      LIB_file.write('            }\n')
      LIB_file.write('        }\n')
      LIB_file.write('    }\n')

    LIB_file.write('    cell_leakage_power : %.3f;\n' % (leakage))
    LIB_file.write('}\n')

    LIB_file.write('\n')
    LIB_file.write('}\n')

    LIB_file.close()

