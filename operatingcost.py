def operatingcost(RESULT, DATA, COST, reaction_time, regen_time, carbur_time,
                  catalyst_required, pred, catalyst_cooling, data_type):
    un = DATA['UNIT']['NAME']

    # Reaction section
    rxn_material = COST['chemical']['natural_gas'] * pred[0]
    rxn_utility  = abs(pred[1]) * COST['utility']['natural_gas_fired']
    reaction_cost = rxn_material + rxn_utility
    reaction_breakdown = {'CH4_material': rxn_material, 'utility': rxn_utility}

    # Regeneration section
    cost_fired = abs(pred[2]) * COST['utility']['natural_gas_fired']
    cost_cw1   = (3.968e6 / 30) * (abs(pred[3]) / regen_time) * COST['chemical']['fresh_water']
    cost_cw2   = pred[4] * (3.968e6 / 30) * COST['chemical']['fresh_water'] * 15
    cost_elec_r = pred[5] * COST['utility']['electricity'] * 0
    regen_cost  = cost_fired + cost_cw1 + cost_cw2 + cost_elec_r
    regeneration_breakdown = {'fired_heat': cost_fired, 'cw1': cost_cw1,
                              'cw2': cost_cw2, 'elec': cost_elec_r}

    # Carburization section
    cost_car_fired = abs(pred[6]) * COST['utility']['natural_gas_fired']
    carbur_cost    = cost_car_fired
    carburization_breakdown = {'firedheat': cost_car_fired}

    # Separation section
    cost_HP  = abs(pred[7]) * COST['utility']['HP']
    cost_LP  = abs(pred[8]) * COST['utility']['LP']
    cost_cw_sep = (3.968e6 / 30) * abs(pred[9]) * COST['chemical']['fresh_water']

    Q_ref = abs(pred[10])
    temp  = DATA['UNIT']['TEMP'][un.index('B11')]
    if   temp < -67.7778: ref_cost = COST['utility']['Rn150'] * Q_ref
    elif temp < -34.4444: ref_cost = COST['utility']['Rn90']  * Q_ref
    elif temp < -12.2222: ref_cost = COST['utility']['Rn30']  * Q_ref
    elif temp <   4.4444: ref_cost = COST['utility']['Rn10']  * Q_ref
    elif temp <  37.7777: ref_cost = COST['utility']['chw']   * Q_ref
    else:                 ref_cost = COST['utility']['cw']    * Q_ref * (3.968e6 / 30)

    cost_elec_sep = pred[11] * COST['utility']['electricity']
    sep_cost = cost_HP + cost_LP + cost_cw_sep + ref_cost + cost_elec_sep
    separation_breakdown = {'HP': cost_HP, 'LP': cost_LP, 'cw': cost_cw_sep,
                            'ref': ref_cost, 'elec': cost_elec_sep}

    OPEX_table = {
        'reaction_material': rxn_material, 'reaction_utility': rxn_utility,
        'reaction_total':    reaction_cost,
        'regen_fired':       cost_fired,   'regen_cw1': cost_cw1,
        'regen_cw2':         cost_cw2,     'regen_elec': cost_elec_r,
        'regen_total':       regen_cost,
        'carbur_fired':      cost_car_fired,'carbur_total': carbur_cost,
        'sep_HP':            cost_HP,       'sep_LP': cost_LP,
        'sep_cw':            cost_cw_sep,   'sep_ref': ref_cost,
        'sep_elec':          cost_elec_sep, 'sep_total': sep_cost,
    }

    return (OPEX_table, reaction_cost, regen_cost, carbur_cost, sep_cost,
            reaction_breakdown, separation_breakdown,
            regeneration_breakdown, carburization_breakdown)
