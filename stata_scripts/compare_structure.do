/* 
Author: Sergio P.
Date: 09/03/2026

(Must run after import.do)
Estimates and compares models of gasoline sales regression
*/

// Global lists
global dep ln_Sg_pc

global gdp d_ln_gdp
	
global moto ln_Mi_c ln_Mi_e
	
global W ln_W_adj_Mi_e

global l_gaso ln_Pg ln_l1_Pg ln_l2_Pg

global l_eth ln_Pe ln_l1_Pe ln_l2_Pe 
	
global dumm_t y2020 ipi_red 

global dumm_s d_NO d_NE d_SE d_CW

// Set-up
preserve
eststo clear

// M0
eststo: quiet xtgls $dep $l_gaso $l_eth $gdp $moto $W $dumm_t $dumm_s, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// M1
eststo: quiet xtgls $dep ln_Pg ln_Pe $gdp, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// M2
eststo: quiet xtgls $dep $l_gaso $l_eth $gdp, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// M3
eststo: quiet xtgls $dep $l_gaso $l_eth $gdp $moto, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// M4
eststo: quiet xtgls $dep $l_gaso $l_eth $gdp $moto $dumm_t, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// M5
eststo: quiet xtgls $dep $l_gaso $l_eth $gdp $moto $dumm_s, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// M5
eststo: quiet xtgls $dep $l_gaso $l_eth $gdp $moto $dumm_t $dumm_s, ///
	panels(het) corr(psar1) igls nmk iterate(10000)
capture drop pred
capture drop resid_sq
predict pred
gen resid_sq = (exp($dep) - exp(pred))^2
quiet sum resid_sq
estadd scalar CV = (100*sqrt(r(sum) / (r(N) - (e(n_cf) + e(n_cv) + e(n_cr))))) / 0.1820338
estadd scalar Coefficients = e(n_cf) + e(n_cv) + e(n_cr)

// Terminal
esttab, not nonumbers mtitles("M0" "M1" "M2" "M3" "M4" "M5" "M6") b(3) stats(CV) label

// LaTeX
esttab using "tab_structure.tex", ///
replace booktabs label compress ///
alignment(D{.}{.}{-1}) width(0.9\hsize) ///
not star(* 0.1 ** 0.05 *** 0.01) b(3) ///
nonumbers mtitles("M0" "M1" "M2" "M3" "M4" "M5" "M6") ///
order($indep $dumm) ///
stats(N Coefficients CV, ///
	labels("Observations" "Estimated Params." "CV (%)") ///
	fmt(%9.0fc %9.0fc %9.2fc) ///
)
