def operating2(COST, RESULT):
    Total_salaries = (1664000 * 1.15) * (COST['IX_LABOR'].iloc[31][1]
                                         / COST['IX_LABOR'].iloc[17][1])
    Labor_burden       = Total_salaries * 0.9
    Maintenance        = 0.03  * RESULT['ISBL']
    Property_insurance = 0.007 * RESULT['FCI']

    return Total_salaries + Labor_burden + Maintenance + Property_insurance
