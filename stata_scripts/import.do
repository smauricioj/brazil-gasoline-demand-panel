/* 
Author: Sergio P.
Date: 12/04/2025

Imports panel dataset and
sets up the regression variables,
*/

// Import
clear all
import excel "data_stata_pre.xlsx", sheet("Sheet1") firstrow

// Panel set
xtset i t

gen d_ln_gdp = ln_gdp_pc - ln_l1_gdp_pc

// Dummies
// Years
// IPI
gen ipi_red = 1 if t >= 2015
replace ipi_red = 0 if ipi_red ==.
// Covid
gen y2020 = 1 if t == 2020
replace y2020 = 0 if y2020 ==.
// Regions
// Centro-oeste
gen d_CW = 1 if floor(i/10) == 5
replace d_CW = 0 if d_CW==.
// Sul
gen d_SO = 1 if floor(i/10) == 4
replace d_SO = 0 if d_SO==.
// Sudeste
gen d_SE = 1 if floor(i/10) == 3
replace d_SE = 0 if d_SE==.
// Nordeste
gen d_NE = 1 if floor(i/10) == 2
replace d_NE = 0 if d_NE==.
// Norte
gen d_NO = 1 if floor(i/10) == 1
replace d_NO = 0 if d_NO==.


// Labels
capture label var y2020 "Dum. 2020"
capture label var ipi_red "Dum. IPI"
capture label var d_CW "Dum. Center West"
capture label var d_SO "Dum. South"
capture label var d_SE "Dum. South East"
capture label var d_NE "Dum. North East"
capture label var d_NO "Dum. North"
capture label var i "State ID"
capture label var t "Year"
capture label var ln_Sg_pc "Gasoline sales"
capture label var ln_Pg "Gasoline price (Pg)"
capture label var ln_l1_Pg "Pg L1"
capture label var ln_l2_Pg "Pg L2"
capture label var ln_Pe "Ethanol price (Pe)"
capture label var ln_l1_Pe "Pe L1"
capture label var ln_l2_Pe "Pe L2"
capture label var ln_Mi_c "ICE"
capture label var ln_W_adj_Mi_c "ICE spillover"
capture label var ln_Mi_e "EV"
capture label var ln_W_adj_Mi_e "EV spillover"
capture label var ln_gdp_pc "GDP"
capture label var ln_l1_gdp_pc "GDP L1"
capture label var d_ln_gdp "GDP (Diff.)"