/* 
Author: Sergio P.
Date: 12/04/2025

(Must run after import.do)
Tests variables
Includes:
	Panel Unit Root 
		LLC
		IPS
	Panel Cointegration
		Kao
		Pedroni
*/
	
// Unit root
global var_tests ///
	ln_Sg_pc ln_Mi_c ln_Mi_e ln_gdp_pc ln_Pg ln_Pe ///
	
capture program drop dounitroot

program dounitroot
	di `"{hline 60}"'
	di "Variable" _col(25) "Level" _col(45) "Difference"
	di `"{hline 60}"'
	foreach var of varlist $var_tests {
		quietly {
			xtunitroot llc `var', lags(aic 2) demean
			local t1 = r(tds)
			local p1 = r(p_tds)
			xtunitroot llc D.`var', lags(aic 2) demean
			local t2 = r(tds)
			local p2 = r(p_tds)
			xtunitroot ips `var', lags(aic 2) demean
			local t3 = r(wtbar)
			local p3 = r(p_wtbar)
			xtunitroot ips D.`var', lags(aic 2) demean
			local t4 = r(wtbar)
			local p4 = r(p_wtbar)
		}
		di "`var'"
		di `"{hline 60}"'
		di "LLC" _col(20) %5.3f `t1' " (" %5.3f `p1' ")" _col(40) %5.3f `t2' " (" %5.3f `p2' ")"
		di "IPS" _col(20) %5.3f `t3' " (" %5.3f `p3' ")" _col(40) %5.3f `t4' " (" %5.3f `p4' ")"
		di `"{hline 60}"'
	}	
	end
	
dounitroot

// Cointegration
global var_tests ///
	ln_Sg_pc ln_Mi_c ln_Mi_e ln_Pg ln_Pe d_ln_gdp ///

xtcointtest kao $var_tests
xtcointtest pedroni $var_tests