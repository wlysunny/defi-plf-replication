* Re-estimate the authors' VECMs with a different variable order (see analysis_plans/vecm_normalisation_check.md)
capture log close
log using "results/vecm/normalisation_log.txt", text replace
foreach cur in dai usdc {
    clear
    import delimited "data/stata/interest_rates_`cur'.csv", encoding(ISO-8859-2)
    gen date = date(v1, "YMD###")
    tsset date
    local L = cond("`cur'" == "dai", 5, 3)
    display _n "==================== `cur': authors' order (c a d) ===================="
    vec c_`cur' a_`cur' d_`cur', rank(2) lags(`L')
    scalar ll_orig = e(ll)
    matrix pi_orig = e(pi)
    display _n "==================== `cur': new order (d c a) ===================="
    vec d_`cur' c_`cur' a_`cur', rank(2) lags(`L')
    scalar ll_new = e(ll)
    matrix pi_new = e(pi)
    display _n "`cur' log likelihood: authors' order = " %12.6f ll_orig "   new order = " %12.6f ll_new
    matrix list pi_orig, format(%9.5f)
    matrix list pi_new, format(%9.5f)
}
log close
