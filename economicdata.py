def economicdata(RESULT):
    ISBL = RESULT['CAPEX']['CBM']
    RESULT['ISBL'] = ISBL

    # Direct costs
    cost_warehouse         = 0.04  * ISBL
    cost_site_development  = 0.09  * ISBL
    cost_additional_piping = 0.045 * ISBL
    TDC = ISBL + cost_warehouse + cost_site_development + cost_additional_piping

    # Indirect costs
    cost_prorateable = 0.10 * TDC
    cost_field       = 0.10 * TDC
    cost_homeoffice  = 0.20 * TDC
    cost_contingency = 0.10 * TDC
    cost_others      = 0.10 * TDC
    TIC = cost_prorateable + cost_field + cost_homeoffice + cost_contingency + cost_others

    FCI = TDC + TIC
    RESULT['FCI'] = FCI

    cost_land            = 1.18 * TDC * 0.02
    cost_working_capital = 0.05 * FCI

    RESULT['TCI_land']            = cost_land
    RESULT['TCI_working_capital'] = cost_working_capital
    RESULT['TCI_total']           = FCI + cost_land + cost_working_capital

    RESULT['TCI'] = {
        'ISBL':              ISBL,
        'warehouse':         cost_warehouse,
        'site_development':  cost_site_development,
        'additional_piping': cost_additional_piping,
        'TDC':               TDC,
        'prorateable':       cost_prorateable,
        'field':             cost_field,
        'homeoffice':        cost_homeoffice,
        'contingency':       cost_contingency,
        'others':            cost_others,
        'TIC':               TIC,
        'FCI':               FCI,
        'land':              cost_land,
        'working_capital':   cost_working_capital,
        'TCI':               FCI + cost_land + cost_working_capital,
    }

    return RESULT
