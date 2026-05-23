import numpy as np


def catalyst_get(initial_yield, deact_r, regen_r, hours_per_cycle,
                 COST, ratio, catalyst_ratio=1):
    BASE_TOL  = 0.0036
    BASE_NAPH = 0.021
    BASE_COKE = 0.021

    init_tol  = BASE_TOL  * catalyst_ratio
    init_naph = BASE_NAPH * catalyst_ratio
    init_coke = BASE_COKE * catalyst_ratio

    min_yield = initial_yield * ratio
    init_vec  = np.array([initial_yield, init_tol, init_naph, init_coke])

    bed = {1: {'current': init_vec.copy(), 'cycle_start': init_vec.copy()},
           2: {'current': init_vec.copy(), 'cycle_start': init_vec.copy()}}

    yields               = []
    cycle_yields         = []
    avg_yields_per_cycle = []
    replacement_times    = {1: [], 2: []}
    regen_cycle_times    = []
    regen_count = 0

    cycle   = 1
    hour    = 1
    op_hour = 1

    while True:
        b = 2 - (cycle % 2)

        yields.append([cycle, hour] + bed[b]['current'].tolist())
        cycle_yields.append(bed[b]['current'].copy())

        if hour % hours_per_cycle != 0:
            bed[b]['current'] = bed[b]['cycle_start'] * (1 - deact_r * op_hour)
            op_hour += 1

        if hour % hours_per_cycle == 0:
            avg = np.mean(cycle_yields, axis=0)
            avg_yields_per_cycle.append([cycle] + avg.tolist())
            op_hour = 1

            if cycle % 2 == 1:
                if bed[1]['current'][0] < min_yield:
                    replacement_times[1].append([cycle, hour])
                else:
                    if cycle == 1:
                        if bed[1]['current'][0] > initial_yield * regen_r:
                            # First cycle was too short: restart with +1 hr
                            bed[1] = {'current': init_vec.copy(),
                                      'cycle_start': init_vec.copy()}
                            bed[2] = {'current': init_vec.copy(),
                                      'cycle_start': init_vec.copy()}
                            yields               = []
                            avg_yields_per_cycle = []
                            hours_per_cycle     += 1
                            hour    = 0
                            cycle   = 0
                            op_hour = 1
                        else:
                            bed[1]['current']     = init_vec * regen_r
                            bed[1]['cycle_start'] = bed[1]['current'].copy()
                            regen_count += 1
                            regen_cycle_times.append([cycle, regen_count])
                    else:
                        prev_start = np.array(yields[(cycle-1)*hours_per_cycle][2:])
                        bed[1]['current']     = prev_start * regen_r
                        bed[1]['cycle_start'] = bed[1]['current'].copy()
                        regen_count += 1
                        regen_cycle_times.append([cycle, regen_count])

            else:
                if bed[2]['current'][0] < min_yield:
                    replacement_times[2].append([cycle, hour])
                    break
                else:
                    if cycle == 2:
                        bed[2]['current']     = init_vec * regen_r
                        bed[2]['cycle_start'] = bed[2]['current'].copy()
                    else:
                        prev_start = np.array(yields[(cycle-1)*hours_per_cycle][2:])
                        bed[2]['current']     = prev_start * regen_r
                        bed[2]['cycle_start'] = bed[2]['current'].copy()

            cycle       += 1
            cycle_yields = []

        hour += 1

    replacement_interval = replacement_times[2][0][1]
    replacement_per_year = round(COST['utility']['operating_hour']
                                 / replacement_interval, 2)

    yield_result = {
        'all':                np.array(yields),
        'cycle_mean':         np.array(avg_yields_per_cycle),
        'replacement':        replacement_per_year,
        'replacement_matrix': np.array(replacement_times[2]),
        'hour':               hour,
        'regeneration_num':   regen_count,
        'regeneration_cycle': np.array(regen_cycle_times),
    }
    return yield_result, hours_per_cycle
