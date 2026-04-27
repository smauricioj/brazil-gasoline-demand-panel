/* 
Author: Sergio P.
Date: 12/04/2025
(Must run after import.do)
Creates and estimates models of gasoline sales regression
*/
// Global lists
global dep ln_Sg_pc
global indep ///
	L.ln_Sg_pc ///
	ln_Pg ln_l1_Pg ln_l2_Pg ///
	ln_Pe ln_l1_Pe ln_l2_Pe ///
	d_ln_gdp ///
	ln_Mi_c ln_Mi_e ///
	ln_W_adj_Mi_e ///
	y2020 ipi_red ///
	d_NO d_NE d_SE d_CW
	
// Regressão
xtgls $dep $indep , panels(het) corr(psa1) igls nmk iterate(10000)

// Salva resultados de e() antes de qualquer preserve/restore
// (preserve/restore apaga os resultados de e())
matrix b_est  = e(b)
matrix V_est  = e(V)
matrix S_est  = e(Sigma)
local  rho_str = e(rho)
local  n_g     = e(N_g)

// ── Aba 1: Predições ─────────────────────────────────────────────────────────
preserve
	capture drop pred
	predict pred
	export excel using "fgls_results.xlsx", ///
		sheet("predictions") sheetreplace first(var)
restore

// ── Aba 2: Parâmetros do painel (rho e sigma) ────────────────────────────────
preserve
	clear
	set obs `n_g'
	gen panel_id = _n
	gen rho      = .
	gen sigma    = .
	tokenize `rho_str'
	forvalues i = 1/`n_g' {
		replace rho   = ``i''                    in `i'
		replace sigma = sqrt(S_est[`i', `i'])    in `i'
	}
	export excel using "fgls_results.xlsx", ///
		sheet("parameters") sheetreplace first(var)
restore

// ── Aba 3: Coeficientes estimados (beta) ─────────────────────────────────────
preserve
	clear
	local varnames : colnames b_est
	local k = colsof(b_est)
	set obs `k'
	gen str32 variable = ""
	gen      beta      = .
	forvalues i = 1/`k' {
		local vname : word `i' of `varnames'
		replace variable = "`vname'"       in `i'
		replace beta     = b_est[1, `i']   in `i'
	}
	export excel using "fgls_results.xlsx", ///
		sheet("beta") sheetreplace first(var)
restore

// ── Aba 4: Matriz de covariância dos coeficientes (e(V)) ─────────────────────
putexcel set "fgls_results.xlsx", sheet("cov_matrix") modify
putexcel A1 = matrix(V_est), names