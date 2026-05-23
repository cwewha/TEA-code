import numpy as np
from catalyst_get import catalyst_get
from operatingcost import operatingcost
from operating2 import operating2
from MSP import MSP
from cashflow import cashflow


def _calc_catalyst_cooling(DATA, catalyst_required, regen_time):
    if DATA is None:
        return 0.0
    try:
        names = list(DATA['UNIT']['NAME'])
        block_row = names.index('H2')
        conn = DATA['UNIT']['CONNECTION'][block_row]
        col_out = conn[1].index('P(OUT)')
        col_in  = conn[1].index('F(IN)')
        snames = list(DATA['STREAM']['NAME'])
        T_out = DATA['STREAM']['CIPTEMP'][snames.index(conn[0][col_out])]
        T_in  = DATA['STREAM']['CIPTEMP'][snames.index(conn[0][col_in])]
        Cp = 0.95
        Q  = (2.39e-10) * Cp * catalyst_required * (T_out - T_in) * 1000
        return abs(Q) / regen_time
    except Exception:
        return 0.0


def _run_cycles(model, RESULT, DATA, COST,
                reaction_time, regen_time, carbur_time,
                catalyst_required, catalyst_cooling, data_type):
    n = RESULT['yield']['cycle_mean'].shape[0]

    rxn_c=np.zeros(n); reg_c=np.zeros(n); car_c=np.zeros(n); sep_c=np.zeros(n)
    H2=np.zeros(n); benz=np.zeros(n); tol=np.zeros(n); naph=np.zeros(n)
    rxn_mat=np.zeros(n); rxn_uti=np.zeros(n)
    sep_HP=np.zeros(n); sep_LP=np.zeros(n); sep_cw=np.zeros(n)
    sep_ref=np.zeros(n); sep_el=np.zeros(n)
    reg_fh=np.zeros(n); reg_cw_arr=np.zeros(n); reg_el=np.zeros(n)
    car_fh=np.zeros(n)

    for i in range(n):
        x_in = np.array(RESULT['yield']['cycle_mean'][i, 1:5], dtype=np.float32)
        pred = model(x_in)

        _, rc, gc, cc, sc, rxn_bd, sep_bd, reg_bd, car_bd = operatingcost(
            RESULT, DATA, COST, reaction_time, regen_time, carbur_time,
            catalyst_required, pred, catalyst_cooling, data_type)

        rxn_c[i]=rc; reg_c[i]=gc; car_c[i]=cc; sep_c[i]=sc
        H2[i]=pred[12]; benz[i]=pred[13]; tol[i]=pred[14]; naph[i]=pred[15]
        rxn_mat[i]=rxn_bd['CH4_material']; rxn_uti[i]=rxn_bd['utility']
        sep_HP[i]=sep_bd['HP'];  sep_LP[i]=sep_bd['LP']
        sep_cw[i]=sep_bd['cw']; sep_ref[i]=sep_bd['ref']; sep_el[i]=sep_bd['elec']
        reg_fh[i]=reg_bd['fired_heat']
        reg_cw_arr[i]=reg_bd['cw1']+reg_bd['cw2']
        reg_el[i]=reg_bd['elec']
        car_fh[i]=car_bd['firedheat']

    rep    = RESULT['yield']['replacement']
    r1_idx = (RESULT['yield']['cycle_mean'][::2, 0]).astype(int) - 1
    n_r1   = len(r1_idx) - 1

    # Annualize: reaction/separation run during the full reaction_time of every
    # cycle; regeneration and carburization happen between cycles on each bed
    # (so x2), driven only by the odd-cycle indices.
    RESULT['annual_operatingcost'] = (
        np.sum(rxn_c) * reaction_time * rep
        + np.sum(reg_c[r1_idx[:n_r1]]) * regen_time * rep * 2
        + np.sum(car_c[r1_idx[:n_r1]]) * carbur_time * rep * 2
        + np.sum(sep_c) * reaction_time * rep
    )
    RESULT['annual'] = {
        'rxn':           np.sum(rxn_c)                * reaction_time * rep,
        'reg':           np.sum(reg_c[r1_idx[:n_r1]]) * regen_time    * rep * 2,
        'car':           np.sum(car_c[r1_idx[:n_r1]]) * carbur_time   * rep * 2,
        'sep':           np.sum(sep_c)                * reaction_time * rep,
        'rxn_material':  np.sum(rxn_mat)              * reaction_time * rep,
        'rxn_utility':   np.sum(rxn_uti)              * reaction_time * rep,
        'sep_HP':        np.sum(sep_HP)               * reaction_time * rep,
        'sep_LP':        np.sum(sep_LP)               * reaction_time * rep,
        'sep_cw':        np.sum(sep_cw)               * reaction_time * rep,
        'sep_ref':       np.sum(sep_ref)              * reaction_time * rep,
        'sep_elec':      np.sum(sep_el)               * reaction_time * rep,
        'reg_firedheat': np.sum(reg_fh[:n-2])         * regen_time    * rep,
        'reg_cw':        np.sum(reg_cw_arr[:n-2])     * regen_time    * rep,
        'reg_elec':      np.sum(reg_el[:n-2])         * regen_time    * rep,
    }
    RESULT['product_sales_summary'] = {
        'H2':   np.sum(H2)   * reaction_time * rep,
        'benz': np.sum(benz) * reaction_time * rep,
        'tol':  np.sum(tol)  * reaction_time * rep,
        'naph': np.sum(naph) * reaction_time * rep,
    }
    return RESULT


def Model_GSA(model, initial_yield, deact, regen, ratio,
              reaction_time, regen_time, carbur_time,
              COST, RESULT, DATA, catalyst_required, data_type=1, rat_selling=1):
    catalyst_ratio = initial_yield / 0.0552
    yield_res, reaction_time = catalyst_get(
        initial_yield, deact, regen, reaction_time, COST, ratio, catalyst_ratio)
    RESULT['yield'] = yield_res
    catalyst_cooling = _calc_catalyst_cooling(DATA, catalyst_required, regen_time)
    RESULT = _run_cycles(model, RESULT, DATA, COST,
                         reaction_time, regen_time, carbur_time,
                         catalyst_required, catalyst_cooling, data_type)
    RESULT['fixed_operating_cost'] = operating2(COST, RESULT)
    msp = MSP(RESULT, COST, rat_selling)
    CF, npv, revenue = cashflow(RESULT, COST, msp, rat_selling)
    return RESULT, CF, msp, npv, revenue, reaction_time
