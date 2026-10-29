* Joint tests that a protocol's adjustment coefficients are all zero (see analysis_plans/vecm_normalisation_check.md)
capture log close
log using "results/vecm/weak_exogeneity_log.txt", text replace
foreach cur in dai usdc {
    clear
    quietly import delimited "data/stata/interest_rates_`cur'.csv", encoding(ISO-8859-2)
    quietly gen date = date(v1, "YMD###")
    quietly tsset date
    local L = cond("`cur'" == "dai", 5, 3)
    foreach order in "c a d" "d c a" {
        local vars
        foreach v of local order {
            local vars `vars' `v'_`cur'
        }
        quietly vec `vars', rank(2) lags(`L')
        display _n "`cur', variable order (`order'):"
        foreach v in c a d {
            quietly test [D_`v'_`cur']L._ce1 [D_`v'_`cur']L._ce2
            display "   alpha = 0 for `v':  chi2(" r(df) ") = " %8.3f r(chi2) "   p = " %6.4f r(p)
        }
    }
}
log close
