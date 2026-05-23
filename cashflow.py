def cashflow(RESULT, COST, benzene_cost, rat_selling=1):
    FCI       = RESULT['FCI']
    Equity    = COST['info']['equity']
    APR       = COST['info']['loan_APR']
    Loan_term = COST['info']['loanterm']
    tax_rate  = COST['info']['federal_taxrate']
    disc_rate = COST['info']['discount_rate']

    FCI_first, FCI_second, FCI_third = 0.08, 0.6, 0.32
    Annual_loan = FCI*(1-Equity)*APR*((1+APR)**Loan_term)/((1+APR)**Loan_term-1)

    cepci_2024 = float(COST['CEPCI'].iloc[27]['CEPCI'])
    cepci_1998 = float(COST['CEPCI'][COST['CEPCI']['YEAR']==1998]['CEPCI'].iloc[0])
    Bags_repl_5yr = COST['info']['No_bags'] * COST['info']['bag_cost'] * (cepci_2024/cepci_1998)

    prices = {'H2':   COST['chemical']['hydrogen'] * rat_selling,
              'benz': benzene_cost,
              'tol':  COST['chemical']['toluene'],
              'naph': COST['chemical']['napht']}
    rev = {k: RESULT['product_sales_summary'][k] * prices[k] for k in prices}
    total_rev = sum(rev.values())
    revenue   = {**rev, 'total': total_rev}

    years = list(range(-2, 31))
    keys  = ['FCI','land','wc','loan_pmt','loan_int','loan_prin',
             'sales','cat_cost','bags','opex','fixed_opex',
             'total_prod_cost','depreciation','remaining',
             'net_rev','losses_fwd','taxable','tax',
             'cash_income','discount','pv','cum_pv']
    CF = {yr: {k: 0.0 for k in keys} for yr in years}

    # CAPEX disbursement
    CF[-2]['FCI']  = FCI*Equity*FCI_first
    CF[-1]['FCI']  = FCI*Equity*FCI_second
    CF[ 0]['FCI']  = FCI*Equity*FCI_third
    CF[-2]['land'] = RESULT['TCI_land']
    CF[ 0]['wc']   = RESULT['TCI_working_capital']
    CF[30]['land'] = RESULT['TCI_land']
    CF[30]['wc']   = RESULT['TCI_working_capital']

    # Loan principal accumulation during construction
    CF[-2]['loan_prin'] = FCI*(1-Equity)*FCI_first
    CF[-1]['loan_prin'] = CF[-2]['loan_prin'] + FCI*(1-Equity)*FCI_second
    CF[ 0]['loan_prin'] = CF[-1]['loan_prin'] + FCI*(1-Equity)*FCI_third
    for yr in [-2,-1,0]:
        CF[yr]['loan_int'] = CF[yr]['loan_prin'] * APR

    # Loan repayment (operating years 1-10)
    for yr in range(1, 11):
        CF[yr]['loan_pmt']  = Annual_loan
        CF[yr]['loan_int']  = CF[yr-1]['loan_prin'] * APR
        CF[yr]['loan_prin'] = CF[yr-1]['loan_prin'] - (Annual_loan - CF[yr]['loan_int'])

    # Sales (3.5/4 of full output in startup year)
    for i, yr in enumerate(range(1, 31)):
        CF[yr]['sales'] = total_rev * (3.5/4) if i == 0 else total_rev

    # Catalyst replacement
    rep_cost = COST['chemical']['MoHZSM'] * RESULT['catalyst'] * RESULT['yield']['replacement'] * 2
    for yr in range(1, 31):
        CF[yr]['cat_cost'] = rep_cost

    # Baghouse replacement every 5 years
    for yr in [5, 10, 15, 20, 25, 30]:
        CF[yr]['bags'] = Bags_repl_5yr

    # OPEX
    for yr in range(1, 31):
        CF[yr]['opex']            = RESULT['annual_operatingcost']
        CF[yr]['fixed_opex']      = RESULT['fixed_operating_cost']
        CF[yr]['total_prod_cost'] = (CF[yr]['cat_cost'] + CF[yr]['bags']
                                     + CF[yr]['opex']   + CF[yr]['fixed_opex'])

    # Declining-balance depreciation (d=0.2857, fully depreciated in 8 years)
    d = 0.2857
    D = [0]*21
    R = [0]*21
    D[0] = FCI*d
    R[0] = FCI - D[0]
    for i in range(1, 7):
        D[i] = R[i-1]*d
        R[i] = R[i-1] - D[i]
    D[7] = R[6]
    R[7] = 0
    for i in range(8, 21):
        D[i] = 0
        R[i] = 0
    for i, yr in enumerate(range(1, 22)):
        CF[yr]['depreciation'] = D[i]
        CF[yr]['remaining']    = R[i]

    # Net revenue
    for yr in range(1, 31):
        CF[yr]['net_rev'] = (CF[yr]['sales']
                             - CF[yr]['loan_int']
                             - CF[yr]['total_prod_cost']
                             - CF[yr]['depreciation'])

    # Loss carry-forward and taxable income
    CF[1]['losses_fwd'] = 0
    for yr in range(1, 30):
        CF[yr]['taxable']       = CF[yr]['net_rev'] + CF[yr]['losses_fwd']
        CF[yr+1]['losses_fwd']  = CF[yr]['taxable'] if CF[yr]['taxable'] <= 0 else 0

    for yr in range(1, 31):
        CF[yr]['tax'] = 0 if CF[yr]['taxable'] < 0 else CF[yr]['taxable'] * tax_rate

    # Annual cash income
    for yr in [-2, -1, 0]:
        CF[yr]['cash_income'] = -(CF[yr]['FCI'] + CF[yr]['land']
                                  + CF[yr]['wc'] + CF[yr]['loan_int'])
    for yr in range(1, 31):
        extra = (CF[yr]['land'] + CF[yr]['wc']) if yr == 30 else 0
        CF[yr]['cash_income'] = (CF[yr]['net_rev'] + extra
                                 - CF[yr]['tax']
                                 - CF[yr]['loan_pmt']
                                 + CF[yr]['loan_int']
                                 + CF[yr]['depreciation'])

    # Discounting and NPV
    cum = 0
    for yr in years:
        CF[yr]['discount'] = 1 / (1 + disc_rate)**yr
        CF[yr]['pv']       = CF[yr]['cash_income'] * CF[yr]['discount']
        cum               += CF[yr]['pv']
        CF[yr]['cum_pv']   = cum

    npv = CF[30]['cum_pv']
    return CF, npv, revenue
