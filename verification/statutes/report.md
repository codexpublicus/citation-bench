# Statute vectors checked against official sources

Written by `bench/verify_statutes.py` (`mise run verify:statutes`). A verdict doesn't change a vector's provenance.

| Set | Vectors | Verified by source | Contradicted | Unverifiable |
|---|---:|---:|---:|---:|
| statutes | 78 | 45 | 2 | 31 |
| statutes-proposed | 36 | 21 | 0 | 15 |
| **all** | 114 | 66 | 2 | 46 |

## Contradicted

- `statutes/find/vt_vsa/0`: existence: § 4407 falls inside chapter 117's sections but isn't one (https://legislature.vermont.gov/statutes/chapter/24/117)
- `statutes/find/nm_nmsa/0`: existence: no § 32A-I-29 in https://nmonesource.com/nmos/nmsa-unanno/en/18532/1/document.do

## Checks not run

Checks against a keyed source that didn't run: its key wasn't in the environment, or its rate limit ran out. A rerun with the keys set (the operator's mise env) runs them and reuses what's cached.

- citing court not checked: CourtListener's rate limit was reached: 12

## What needs a person

### Code forms: one answer covers every vector with the form

- `A.C.A.` means `Ark. Code Ann.` (Arkansas): 2 (`ark_aca/0`, `ark_aca/1`)
- `G.L.` means `R.I. Gen. Laws` (Rhode Island): 2 (`ri_gl_1956/0`, `ri_gl_1956/1`)
- `La.Rev.Stat.` means `La. Stat. Ann.` (Louisiana): 2 (`la_rev_stat/0`, `la_rev_stat/1`)
- `M.C.L.A.` means `Mich. Comp. Laws` (Michigan): 2 (`mich_mcl/0`, `mich_mcl/1`)
- `O.C.G.A.` means `Ga. Code Ann.` (Georgia): 2 (`ga_o_c_g_a/0`, `ga_o_c_g_a/1`)
- `West Virginia Code` means `W. Va. Code` (West Virginia): 2 (`wva_code/0`, `wva_code/1`)
- `M.R.S.A.` means `Me. Rev. Stat. Ann.` (Maine): 1 (`me_mrsa/0`)
- `MCR` means `Mich. Ct. R.` (Michigan): 1 (`mich_ct_r/0`)
- `N.J.A.C.` means `N.J. Admin. Code` (New Jersey): 1 (`njac/0`)
- `NYCRR` means `N.Y. Comp. Codes R. & Regs.` (New York): 1 (`nycrr/0`)

### Code abbreviations not in reporters-db or the conventions

- `Conn. Practice Book` (Connecticut): is this the code's standard abbreviation?: 2 (`conn_practice_book/0`, `conn_practice_book/1`)
- `Fed. R. App. P.` (United States): is this the code's standard abbreviation?: 2 (`fed_r_app_p/0`, `fed_r_app_p/1`)
- `Fed. R. Crim. P.` (United States): is this the code's standard abbreviation?: 2 (`fed_r_crim_p/0`, `fed_r_crim_p/1`)
- `Fed. R. Evid.` (United States): is this the code's standard abbreviation?: 2 (`fed_r_evid/0`, `fed_r_evid/1`)
- `N.Y. Family Ct Act` (New York): is this the code's standard abbreviation?: 2 (`ny_family_ct_act/0`, `ny_family_ct_act/1`)
- `Pa. Stat. Ann.` (Pennsylvania): is this the code's standard abbreviation?: 2 (`pa_ps/0`, `pa_ps/1`)
- `Ind. Const.` (Indiana): is this the code's standard abbreviation?: 1 (`state_const/1`)
- `N.M. Const.` (New Mexico): is this the code's standard abbreviation?: 1 (`state_const/2`)
- `Ohio Const.` (Ohio): is this the code's standard abbreviation?: 1 (`state_const/0`)
- `Pa. R. Civ. P.` (Pennsylvania): is this the code's standard abbreviation?: 1 (`pa_r_civ_p/0`)
- `Tex. R. App. P.` (Texas): is this the code's standard abbreviation?: 1 (`tex_r_p/1`)
- `Tex. R. Civ. P.` (Texas): is this the code's standard abbreviation?: 1 (`tex_r_p/0`)

### Span judgments

- in-span text not in any field: `####,`: 5 (`nm_nmsa/0`, `nm_nmsa/1`, `ala_code_1975/0`, `ala_code_1975/1`, `ri_gl_1956/0`)
- in-span text not in any field: `####`: 2 (`okla_os/0`, `okla_os/1`)
- in-span text not in any field: `(Rev. to ####)`: 2 (`conn_general_statutes_revision/0`, `conn_general_statutes_revision/1`)
- in-span text not in any field: `#### (#### Reenactment)`: 1 (`ri_gl_1956/1`)
- whitespace inside a section (`10 -236b`): 1 (`conn_gen_stat/1`)

### No machine source for the section's existence

- `Ga. Code Ann.`: Georgia's official code is online through LexisNexis; not used: 4 (`ga_ocga/0`, `ga_ocga/1`, `ga_o_c_g_a/0`, `ga_o_c_g_a/1`)
- `Ark. Code Ann.`: Arkansas's official code is online through LexisNexis; not used: 2 (`ark_aca/0`, `ark_aca/1`)
- `Okla. Stat.`: the robots.txt of both oscn.net and oklegislature.gov disallows every path to every crawler: 2 (`okla_os/0`, `okla_os/1`)
- `Pa. Stat. Ann.`: Purdon's title and section numbers have no official per-section source; palegis.us indexes unconsolidated statutes by act: 2 (`pa_ps/0`, `pa_ps/1`)
- `Tenn. Code Ann.`: Tennessee's official code is online through LexisNexis; not used: 2 (`tenn_tca/0`, `tenn_tca/1`)
- `Mich. Ct. R.`: courts.michigan.gov, which publishes the rules, has a robots.txt that disallows every path to every crawler: 1 (`mich_ct_r/0`)
- `N.J. Admin. Code`: the N.J.A.C. is online through LexisNexis; not used: 1 (`njac/0`)
- `N.Y. Comp. Codes R. & Regs.`: the official NYCRR is online through Thomson Reuters Westlaw; not used: 1 (`nycrr/0`)
- `Ohio Const.`: codes.ohio.gov, the only official text, has a robots.txt that disallows every path to every crawler: 1 (`state_const/0`)
- `Pa. R. Civ. P.`: pacodeandbulletin.gov, which publishes the rules (231 Pa. Code), has a robots.txt that disallows every path to every crawler: 1 (`pa_r_civ_p/0`)

## Verdicts

| Vector | Provenance | Verdict |
|---|---|---|
| `statutes/find/conn_general_statutes/0` | hand-checked | verified-by-source:cap+cap-case-metadata+cga+reporters-db@v3.2.67 |
| `statutes/find/conn_general_statutes/1` | hand-checked | verified-by-source:cap+cap-case-metadata+cga+reporters-db@v3.2.67 |
| `statutes/find/conn_general_statutes_revision/0` | hand-checked | unverifiable:span |
| `statutes/find/conn_general_statutes_revision/1` | hand-checked | unverifiable:span |
| `statutes/find/conn_practice_book/0` | hand-checked | unverifiable:code |
| `statutes/find/conn_practice_book/1` | hand-checked | unverifiable:code |
| `statutes/find/conn_gen_stat/0` | hand-checked | verified-by-source:cga+reporters-db@v3.2.67 |
| `statutes/find/conn_gen_stat/1` | hand-checked | unverifiable:span |
| `statutes/find/ga_ocga/0` | hand-checked | unverifiable:existence |
| `statutes/find/ga_ocga/1` | hand-checked | unverifiable:existence |
| `statutes/find/ga_o_c_g_a/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/ga_o_c_g_a/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/ariz_ars/0` | hand-checked | verified-by-source:azleg+courtlistener-api+reporters-db@v3.2.67 |
| `statutes/find/ariz_ars/1` | hand-checked | verified-by-source:azleg+courtlistener-api+reporters-db@v3.2.67 |
| `statutes/find/haw_hrs/0` | hand-checked | verified-by-source:cap+cap-case-metadata+hawaii-legislature+reporters-db@v3.2.67 |
| `statutes/find/haw_hrs/1` | hand-checked | verified-by-source:courtlistener-api+hawaii-legislature+reporters-db@v3.2.67 |
| `statutes/find/nc_ncgs/0` | hand-checked | verified-by-source:cap+cap-case-metadata+ncleg+reporters-db@v3.2.67 |
| `statutes/find/nc_ncgs/1` | hand-checked | verified-by-source:cap+cap-case-metadata+ncleg+reporters-db@v3.2.67 |
| `statutes/find/nc_gs/0` | hand-checked | verified-by-source:ncleg+reporters-db@v3.2.67 |
| `statutes/find/nc_gs/1` | hand-checked | verified-by-source:ncleg+reporters-db@v3.2.67 |
| `statutes/find/nd_ndcc/0` | hand-checked | verified-by-source:cap+cap-case-metadata+nd-legislature+reporters-db@v3.2.67 |
| `statutes/find/nd_ndcc/1` | hand-checked | verified-by-source:courtlistener-api+nd-legislature+reporters-db@v3.2.67 |
| `statutes/find/tenn_tca/0` | hand-checked | unverifiable:existence |
| `statutes/find/tenn_tca/1` | hand-checked | unverifiable:existence |
| `statutes/find/pa_cs/0` | hand-checked | verified-by-source:courtlistener-api+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_cs/1` | hand-checked | verified-by-source:courtlistener-api+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_csa/0` | hand-checked | verified-by-source:courtlistener-api+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_csa/1` | hand-checked | verified-by-source:cap+cap-case-metadata+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_ps/0` | hand-checked | unverifiable:code, existence |
| `statutes/find/pa_ps/1` | hand-checked | unverifiable:code, existence |
| `statutes/find/me_mrs/0` | hand-checked | verified-by-source:cap+cap-case-metadata+maine-legislature+reporters-db@v3.2.67 |
| `statutes/find/me_mrs/1` | hand-checked | verified-by-source:cap+cap-case-metadata+maine-legislature+reporters-db@v3.2.67 |
| `statutes/find/me_mrsa/0` | hand-checked | unverifiable:form |
| `statutes/find/me_mrsa/1` | hand-checked | verified-by-source:courtlistener-api+maine-legislature+reporters-db@v3.2.67 |
| `statutes/find/vt_vsa/0` | hand-checked | contradicted:existence: § 4407 falls inside chapter 117's sections but isn't one (https://legislature.vermont.gov/statutes/chapter/24/117) |
| `statutes/find/vt_vsa/1` | hand-checked | verified-by-source:cap+cap-case-metadata+reporters-db@v3.2.67+vermont-legislature |
| `statutes/find/okla_os/0` | hand-checked | unverifiable:existence, span |
| `statutes/find/okla_os/1` | hand-checked | unverifiable:existence, span |
| `statutes/find/ny_penal_law/0` | hand-checked | verified-by-source:courtlistener-api+ny-openleg+reporters-db@v3.2.67 |
| `statutes/find/ny_penal_law/1` | hand-checked | verified-by-source:courtlistener-api+ny-openleg+reporters-db@v3.2.67 |
| `statutes/find/ny_judiciary_law/0` | hand-checked | verified-by-source:cap+cap-case-metadata+ny-openleg+reporters-db@v3.2.67 |
| `statutes/find/ny_family_ct_act/0` | hand-checked | unverifiable:code |
| `statutes/find/ny_family_ct_act/1` | hand-checked | unverifiable:code |
| `statutes/find/cal_pen_code/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+courtlistener-api+reporters-db@v3.2.67 |
| `statutes/find/cal_pen_code/1` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap+cap-case-metadata+reporters-db@v3.2.67 |
| `statutes/find/cal_code_civ_proc/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+courtlistener-api+reporters-db@v3.2.67 |
| `statutes/find/cal_code_civ_proc/1` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+courtlistener-api+reporters-db@v3.2.67 |
| `statutes/find/cal_evid_code/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap+cap-case-metadata+reporters-db@v3.2.67 |
| `statutes/find/cal_evid_code/1` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+courtlistener-api+reporters-db@v3.2.67 |
| `statutes/find/cal_civ_code/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+reporters-db@v3.2.67 |
| `statutes/find/tex_small_caps/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_small_caps/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_no_space/0` | hand-checked | verified-by-source:cap+reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_no_space/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_penal_code_ann/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_penal_code_ann/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/mass_g_l_c/0` | hand-checked | verified-by-source:courtlistener-api+ma-legislature+reporters-db@v3.2.67 |
| `statutes/find/mass_g_l_c/1` | hand-checked | verified-by-source:courtlistener-api+ma-legislature+reporters-db@v3.2.67 |
| `statutes/find/mass_gen_laws_ch/0` | hand-checked | verified-by-source:ma-legislature+reporters-db@v3.2.67 |
| `statutes/find/nm_nmsa/0` | hand-checked | contradicted:existence: no § 32A-I-29 in https://nmonesource.com/nmos/nmsa-unanno/en/18532/1/document.do |
| `statutes/find/nm_nmsa/1` | hand-checked | unverifiable:span |
| `statutes/find/mich_mcl/0` | hand-checked | unverifiable:form |
| `statutes/find/mich_mcl/1` | hand-checked | unverifiable:form |
| `statutes/find/ala_code_1975/0` | hand-checked | unverifiable:span |
| `statutes/find/ala_code_1975/1` | hand-checked | unverifiable:span |
| `statutes/find/ark_aca/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/ark_aca/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/la_rev_stat/0` | hand-checked | unverifiable:form |
| `statutes/find/la_rev_stat/1` | hand-checked | unverifiable:form |
| `statutes/find/ri_gl_1956/0` | hand-checked | unverifiable:form, span |
| `statutes/find/ri_gl_1956/1` | hand-checked | unverifiable:form, span |
| `statutes/find/wva_code/0` | hand-checked | unverifiable:form |
| `statutes/find/wva_code/1` | hand-checked | unverifiable:form |
| `statutes/find/wis_stat_caps/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+wi-legislature |
| `statutes/find/usc/0` | hand-checked | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes/find/usc/1` | hand-checked | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes/find/cfr/0` | hand-checked | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes/find/cfr/1` | hand-checked | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes-proposed/find/fed_r_civ_p/0` | proposed | verified-by-source:govinfo-uscode-2024 |
| `statutes-proposed/find/fed_r_civ_p/1` | proposed | verified-by-source:govinfo-uscode-2024 |
| `statutes-proposed/find/fed_r_civ_p/2` | proposed | verified-by-source:govinfo-uscode-2024 |
| `statutes-proposed/find/fed_r_evid/0` | proposed | unverifiable:code |
| `statutes-proposed/find/fed_r_evid/1` | proposed | unverifiable:code |
| `statutes-proposed/find/fed_r_crim_p/0` | proposed | unverifiable:code |
| `statutes-proposed/find/fed_r_crim_p/1` | proposed | unverifiable:code |
| `statutes-proposed/find/fed_r_app_p/0` | proposed | unverifiable:code |
| `statutes-proposed/find/fed_r_app_p/1` | proposed | unverifiable:code |
| `statutes-proposed/find/tex_r_p/0` | proposed | unverifiable:code |
| `statutes-proposed/find/tex_r_p/1` | proposed | unverifiable:code |
| `statutes-proposed/find/pa_r_civ_p/0` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/mich_ct_r/0` | proposed | unverifiable:existence, form |
| `statutes-proposed/find/us_const/0` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/1` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/2` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/3` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/state_const/0` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/state_const/1` | proposed | unverifiable:code |
| `statutes-proposed/find/state_const/2` | proposed | unverifiable:code |
| `statutes-proposed/find/nycrr/0` | proposed | unverifiable:existence, form |
| `statutes-proposed/find/njac/0` | proposed | unverifiable:existence, form |
| `statutes-proposed/find/treas_reg/0` | proposed | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes-proposed/find/treas_reg/1` | proposed | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes-proposed/find/ussg/0` | proposed | verified-by-source:ussc-guidelines-2025 |
| `statutes-proposed/find/ussg/1` | proposed | verified-by-source:ussc-guidelines-2025 |
| `statutes-proposed/find/fed_reg/0` | proposed | verified-by-source:govinfo-fr-link |
| `statutes-proposed/find/fed_reg/1` | proposed | verified-by-source:govinfo-fr-link |
| `statutes-proposed/find/stat/0` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/stat/1` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/pub_l/0` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/pub_l/1` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/usc_et_seq/0` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes-proposed/find/usc_et_seq/1` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes-proposed/find/usc_range/0` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes-proposed/find/usc_range/1` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |

## Sources used

| URL | Retrieved | Bytes | SHA-256 |
|---|---|---:|---|
| http://certificates.godaddy.com/repository/gdig2.crt | 2026-10-18 | 1236 | `973a41276ffd01e0` |
| https://alison.legislature.state.al.us/graphql?query=query%28%24displayId%3A+String%21%29%7BcodesOfAlabama%28where%3A%7Btype%3A%7Beq%3ASection%7D%2CdisplayId%3A%7Beq%3A%24displayId%7D%7D%29%7Bdata%7BdisplayId+title%7D%7D%7D&variables=%7B%22displayId%22%3A+%2212-2-7%22%7D | 2026-10-18 | 130 | `e32c7b902b235c0d` |
| https://alison.legislature.state.al.us/graphql?query=query%28%24displayId%3A+String%21%29%7BcodesOfAlabama%28where%3A%7Btype%3A%7Beq%3ASection%7D%2CdisplayId%3A%7Beq%3A%24displayId%7D%7D%29%7Bdata%7BdisplayId+title%7D%7D%7D&variables=%7B%22displayId%22%3A+%2225-5-1%22%7D | 2026-10-18 | 99 | `2676e795d9084d21` |
| https://code.wvlegislature.gov/31-1-15/ | 2026-10-18 | 40139 | `8491d2872b4f8df3` |
| https://code.wvlegislature.gov/56-6-31/ | 2026-10-18 | 44556 | `693677696d02e655` |
| https://data.capitol.hawaii.gov/hrscurrent/ | 2026-10-18 | 2128 | `212f935aa1e4edc4` |
| https://data.capitol.hawaii.gov/hrscurrent/Vol05_Ch0261-0319/HRS0291E/HRS_0291E-0021.htm | 2026-10-18 | 9152 | `466db453566c270b` |
| https://data.capitol.hawaii.gov/hrscurrent/Vol14_Ch0701-0853/HRS0707/HRS_0707-0721.htm | 2026-10-18 | 3938 | `8e2f6ee014d15e3a` |
| https://docs.legis.wisconsin.gov/statutes/statutes/706/09 | 2026-10-18 | 95515 | `8184d1a627ddbd91` |
| https://downloads.leginfo.legislature.ca.gov/pubinfo_2025.zip#bytes=0-33554431 | 2026-10-18 | 33554432 | `4b741426c9e8c84c` |
| https://iga.in.gov/publications/indiana_constitution/Constitution%20(as%20amended%202024).pdf | 2026-10-18 | 171051 | `0711f8e2bdcb51e3` |
| https://legislation.nysenate.gov/api/3/laws/FCT/1033-B | 2026-10-20 | 3874 | `9ceb64c9f531e4f0` |
| https://legislation.nysenate.gov/api/3/laws/FCT/352.2 | 2026-10-20 | 13038 | `2613ce8a9f70b5a0` |
| https://legislation.nysenate.gov/api/3/laws/JUD/468-A | 2026-10-20 | 4498 | `27ed116334079ba3` |
| https://legislation.nysenate.gov/api/3/laws/PEN/180.05 | 2026-10-20 | 2880 | `69382a2795cbbc59` |
| https://legislation.nysenate.gov/api/3/laws/PEN/70.06 | 2026-10-20 | 10175 | `b55b183fbe83814d` |
| https://legislature.maine.gov/statutes/1/title1sec402.html | 2026-10-18 | 48892 | `4d965854b6c7328a` |
| https://legislature.maine.gov/statutes/11/title11sec1-203.html | 2026-10-18 | 9232 | `22009510bb98d7e1` |
| https://legislature.maine.gov/statutes/15/title15sec2115-A.html | 2026-10-18 | 18779 | `3c8209a1c9993b3e` |
| https://legislature.maine.gov/statutes/19-A/title19-Asec1653.html | 2026-10-18 | 80149 | `ea2010ffd24c776a` |
| https://legislature.vermont.gov/statutes/chapter/24/081 | 2026-10-18 | 58549 | `7ebd5585177bf6a8` |
| https://legislature.vermont.gov/statutes/chapter/24/115 | 2026-10-18 | 58428 | `efec69337a833e95` |
| https://legislature.vermont.gov/statutes/chapter/24/117 | 2026-10-18 | 79850 | `6c99dd47b5269e1a` |
| https://legislature.vermont.gov/statutes/chapter/24/118 | 2026-10-18 | 59150 | `aa1c6adcc95ee132` |
| https://legislature.vermont.gov/statutes/chapter/24/120 | 2026-10-18 | 65646 | `6e38e62cfbdb2fae` |
| https://legislature.vermont.gov/statutes/chapter/24/126 | 2026-10-18 | 60305 | `862f4e24f30d57c1` |
| https://legislature.vermont.gov/statutes/title/24 | 2026-10-18 | 75304 | `b437705da83e7f3c` |
| https://malegislature.gov/Laws/GeneralLaws/Chapter184/Section15 | 2026-10-18 | 81354 | `5a90d3adfaf50c3e` |
| https://malegislature.gov/Laws/GeneralLaws/Chapter260/Section2A | 2026-10-18 | 73446 | `1162013886cfdf9b` |
| https://malegislature.gov/Laws/GeneralLaws/Chapter278/Section33E | 2026-10-18 | 74745 | `77fac6d4742f81c4` |
| https://ndlegis.gov/cencode/t19c03-4.pdf | 2026-10-18 | 83496 | `584d85a6b29cf7ae` |
| https://ndlegis.gov/cencode/t23c06.pdf | 2026-10-18 | 127283 | `efd9e918efaa462f` |
| https://nmonesource.com/nmos/c/en/5916/1/document.do | 2026-10-18 | 7413964 | `06d371e024550ba7` |
| https://nmonesource.com/nmos/nmsa-unanno/en/18532/1/document.do | 2026-10-18 | 1980025 | `93064b4fc5fadc88` |
| https://nmonesource.com/nmos/nmsa-unanno/en/18541/1/document.do | 2026-10-18 | 410939 | `6f056359211217d7` |
| https://nmonesource.com/nmos/nmsa-unanno/en/nav_date.do?iframe=true | 2026-10-18 | 39863 | `6956d66ced228b52` |
| https://nmonesource.com/nmos/nmsa-unanno/en/nav_date.do?page=1&iframe=true | 2026-10-18 | 39874 | `dd172e07dd8557b9` |
| https://nmonesource.com/nmos/nmsa-unanno/en/nav_date.do?page=2&iframe=true | 2026-10-18 | 40087 | `641259830154fb00` |
| https://nmonesource.com/nmos/nmsa-unanno/en/nav_date.do?page=3&iframe=true | 2026-10-18 | 40034 | `f32ac2d81bdbe4e2` |
| https://nmonesource.com/nmos/nmsa-unanno/en/nav_date.do?page=4&iframe=true | 2026-10-18 | 24138 | `68659ffaf74f3143` |
| https://raw.githubusercontent.com/freelawproject/reporters-db/v3.2.67/reporters_db/data/laws.json | 2026-10-18 | 211528 | `cba1f8f2225a2760` |
| https://static.case.law/a3d/134/cases/1062-01.json | 2026-10-18 | 17106 | `501e849a9b35e06e` |
| https://static.case.law/a3d/139/cases/0904-01.json | 2026-10-18 | 47135 | `a390a8e60b2f5e84` |
| https://static.case.law/a3d/140/cases/1249-01.json | 2026-10-18 | 43185 | `b4816562ef9ce421` |
| https://static.case.law/ad3d/122/cases/1232-02.json | 2026-10-18 | 3150 | `e7b71fa899f95b4e` |
| https://static.case.law/cal-4th/52/cases/0769-01.json | 2026-10-18 | 293419 | `e5d32f96c28e9983` |
| https://static.case.law/cal-app-4th/231/cases/1337-01.json | 2026-10-18 | 71772 | `9d0b6570fd7dec1f` |
| https://static.case.law/conn-app/116/cases/0112-01.json | 2026-10-18 | 86793 | `f167ddf30edaf33f` |
| https://static.case.law/conn-app/116/cases/0758-01.json | 2026-10-18 | 55332 | `50143529fc423dfc` |
| https://static.case.law/conn-app/128/cases/0425-01.json | 2026-10-18 | 60674 | `1c2618930b87a74b` |
| https://static.case.law/conn/267/cases/0539-01.json | 2026-10-18 | 90479 | `13276cfb5dc64259` |
| https://static.case.law/haw/118/cases/0001-01.json | 2026-10-18 | 72291 | `ee7b8d4adbee064d` |
| https://static.case.law/nc-app/201/cases/0146-01.json | 2026-10-18 | 21524 | `702e2ba023847ed4` |
| https://static.case.law/nw2d/891/cases/0760-01.json | 2026-10-18 | 24313 | `0ad4cae75b50b305` |
| https://static.case.law/p3d/383/cases/0773-01.json | 2026-10-18 | 39680 | `bb8f47650f7f7e24` |
| https://static.case.law/pa-super/370/cases/0444-01.json | 2026-10-18 | 48618 | `f09e4b2854425583` |
| https://static.case.law/se2d/805/cases/0751-01.json | 2026-10-18 | 42300 | `1095fe05a6313305` |
| https://static.case.law/so3d/217/cases/0906-01.json | 2026-10-18 | 69965 | `2c101342a555ba98` |
| https://static.case.law/sw3d/451/cases/0028-01.json | 2026-10-18 | 148577 | `ffce7165074f1406` |
| https://static.case.law/vt/190/cases/0188-01.json | 2026-10-18 | 19012 | `0f59cce59b6ab42f` |
| https://static.case.law/vt/199/cases/0019-01.json | 2026-10-18 | 147491 | `140e537cafba4aec` |
| https://tcss.legis.texas.gov/resources/FA/htm/FA.54.htm | 2026-10-18 | 215450 | `f5208d35e88244b8` |
| https://tcss.legis.texas.gov/resources/PE/htm/PE.1.htm | 2026-10-18 | 35667 | `2e34c7b8b9a48bbd` |
| https://tcss.legis.texas.gov/resources/PE/htm/PE.3.htm | 2026-10-18 | 19870 | `031c804625144d3d` |
| https://tcss.legis.texas.gov/resources/PE/htm/PE.36.htm | 2026-10-18 | 35232 | `c9b863b99baea3a4` |
| https://tcss.legis.texas.gov/resources/PE/htm/PE.9.htm | 2026-10-18 | 41526 | `1f7d415f4f4fdc68` |
| https://tcss.legis.texas.gov/resources/PR/htm/PR.204.htm | 2026-10-18 | 28886 | `127ce162725fec5f` |
| https://webserver.rilegislature.gov/Statutes/TITLE24/24-10/24-10-1.htm | 2026-10-18 | 4036 | `50ad3e2f85dee289` |
| https://webserver.rilegislature.gov/Statutes/TITLE39/39-3/39-3-11.htm | 2026-10-18 | 8202 | `4fdfeef114eafe62` |
| https://www.azleg.gov/ars/12/02101.htm | 2026-10-18 | 3675 | `932de813453c1457` |
| https://www.azleg.gov/ars/32/01451.htm | 2026-10-18 | 14886 | `162a49f869da6d3e` |
| https://www.cga.ct.gov/current/pub/chap_170.htm | 2026-10-18 | 785200 | `59d2a5c54436f955` |
| https://www.cga.ct.gov/current/pub/chap_319a.htm | 2026-10-18 | 563668 | `12600b721582c2ff` |
| https://www.cga.ct.gov/current/pub/chap_926.htm | 2026-10-18 | 176362 | `29bd29d8f82067f1` |
| https://www.cga.ct.gov/current/pub/chap_951.htm | 2026-10-18 | 92053 | `64f059094af25b8e` |
| https://www.cga.ct.gov/current/pub/chap_952.htm | 2026-10-18 | 1300036 | `f53e86c7ddd84ea9` |
| https://www.cga.ct.gov/current/pub/title_10.htm | 2026-10-18 | 14522 | `5ec794ca0d08cf6c` |
| https://www.cga.ct.gov/current/pub/title_17a.htm | 2026-10-18 | 8587 | `ac748e06c3c7fa8b` |
| https://www.cga.ct.gov/current/pub/title_52.htm | 2026-10-18 | 15085 | `872b09649dd03518` |
| https://www.cga.ct.gov/current/pub/title_53a.htm | 2026-10-18 | 6164 | `3ac7ae8f74e40edc` |
| https://www.courtlistener.com/api/rest/v4/clusters/1072657/?fields=docket | 2026-10-20 | 70 | `297875a810e4d30c` |
| https://www.courtlistener.com/api/rest/v4/clusters/1194895/?fields=docket | 2026-10-20 | 70 | `69cd195c76a0a0e5` |
| https://www.courtlistener.com/api/rest/v4/clusters/1255323/?fields=docket | 2026-10-20 | 71 | `469fb248bbb535f5` |
| https://www.courtlistener.com/api/rest/v4/clusters/1401377/?fields=docket | 2026-10-20 | 71 | `b4f577c635a9f56a` |
| https://www.courtlistener.com/api/rest/v4/clusters/1460811/?fields=docket | 2026-10-20 | 71 | `16eca8b94b4f2bca` |
| https://www.courtlistener.com/api/rest/v4/clusters/1463254/?fields=docket | 2026-10-20 | 71 | `b23e6fb0e84e8924` |
| https://www.courtlistener.com/api/rest/v4/clusters/1469130/?fields=docket | 2026-10-20 | 71 | `b934b23c0439c60d` |
| https://www.courtlistener.com/api/rest/v4/clusters/1503218/?fields=docket | 2026-10-20 | 70 | `a64dd115cae0e133` |
| https://www.courtlistener.com/api/rest/v4/clusters/2113659/?fields=docket | 2026-10-20 | 71 | `bccce020dce38f2d` |
| https://www.courtlistener.com/api/rest/v4/clusters/2135107/?fields=docket | 2026-10-20 | 71 | `dabe697fd9fe4fda` |
| https://www.courtlistener.com/api/rest/v4/clusters/2149269/?fields=docket | 2026-10-20 | 71 | `785c1efbd3adff79` |
| https://www.courtlistener.com/api/rest/v4/clusters/2275138/?fields=docket | 2026-10-20 | 71 | `d6c3645f03a1f4a6` |
| https://www.courtlistener.com/api/rest/v4/clusters/2278575/?fields=docket | 2026-10-20 | 71 | `dfaa236777758705` |
| https://www.courtlistener.com/api/rest/v4/clusters/2321051/?fields=docket | 2026-10-20 | 71 | `c19e2a2dd394634a` |
| https://www.courtlistener.com/api/rest/v4/clusters/2398329/?fields=docket | 2026-10-20 | 71 | `b3be8976b57affe7` |
| https://www.courtlistener.com/api/rest/v4/clusters/2500776/?fields=docket | 2026-10-20 | 71 | `19b7d8adf965df62` |
| https://www.courtlistener.com/api/rest/v4/clusters/2502448/?fields=docket | 2026-10-20 | 71 | `f6865314718e454c` |
| https://www.courtlistener.com/api/rest/v4/clusters/2570257/?fields=docket | 2026-10-20 | 71 | `12abe8d715e9e70e` |
| https://www.courtlistener.com/api/rest/v4/clusters/2626767/?fields=docket | 2026-10-20 | 71 | `37f6e30c904e0031` |
| https://www.courtlistener.com/api/rest/v4/clusters/2644498/?fields=docket | 2026-10-20 | 69 | `8b8d6d0ae05a5895` |
| https://www.courtlistener.com/api/rest/v4/clusters/4566113/?fields=docket | 2026-10-20 | 71 | `0b9b3bcb2cd223b2` |
| https://www.courtlistener.com/api/rest/v4/clusters/4656024/?fields=docket | 2026-10-20 | 72 | `5cdaac8de901cc59` |
| https://www.courtlistener.com/api/rest/v4/clusters/5149665/?fields=docket | 2026-10-20 | 72 | `77c04d749c970255` |
| https://www.courtlistener.com/api/rest/v4/clusters/5246401/?fields=docket | 2026-10-20 | 72 | `cb2580f6dac47997` |
| https://www.courtlistener.com/api/rest/v4/clusters/6093617/?fields=docket | 2026-10-20 | 72 | `498e0dc19a05b683` |
| https://www.courtlistener.com/api/rest/v4/clusters/6355826/?fields=docket | 2026-10-20 | 72 | `8c2d293975bba2a1` |
| https://www.courtlistener.com/api/rest/v4/clusters/6356479/?fields=docket | 2026-10-20 | 72 | `0562c45f51637fa5` |
| https://www.courtlistener.com/api/rest/v4/clusters/6356874/?fields=docket | 2026-10-20 | 72 | `a70cc47b0f7b881b` |
| https://www.courtlistener.com/api/rest/v4/clusters/6588192/?fields=docket | 2026-10-20 | 72 | `2bed5713f6c58a96` |
| https://www.courtlistener.com/api/rest/v4/clusters/6596983/?fields=docket | 2026-10-20 | 72 | `f1a66342978cba68` |
| https://www.courtlistener.com/api/rest/v4/clusters/78542/?fields=docket | 2026-10-20 | 70 | `2b10d4f0a10a64d0` |
| https://www.courtlistener.com/api/rest/v4/courts/arizctapp/?fields=id,full_name,jurisdiction | 2026-10-20 | 80 | `b6f7bd9d27dbdd49` |
| https://www.courtlistener.com/api/rest/v4/courts/ca11/?fields=id,full_name,jurisdiction | 2026-10-20 | 88 | `eae80b60136d383b` |
| https://www.courtlistener.com/api/rest/v4/courts/calctapp/?fields=id,full_name,jurisdiction | 2026-10-20 | 78 | `8b9b0b0d9b7590bd` |
| https://www.courtlistener.com/api/rest/v4/courts/ga/?fields=id,full_name,jurisdiction | 2026-10-20 | 69 | `e8ccf47f6f1b848c` |
| https://www.courtlistener.com/api/rest/v4/courts/gactapp/?fields=id,full_name,jurisdiction | 2026-10-20 | 78 | `3e59cee42c22f851` |
| https://www.courtlistener.com/api/rest/v4/courts/gand/?fields=id,full_name,jurisdiction | 2026-10-20 | 76 | `71319e14167d14e1` |
| https://www.courtlistener.com/api/rest/v4/courts/haw/?fields=id,full_name,jurisdiction | 2026-10-20 | 66 | `fa99a90f7d6e05fd` |
| https://www.courtlistener.com/api/rest/v4/courts/mass/?fields=id,full_name,jurisdiction | 2026-10-20 | 83 | `2e007494aac106af` |
| https://www.courtlistener.com/api/rest/v4/courts/massappct/?fields=id,full_name,jurisdiction | 2026-10-20 | 80 | `afc8542a077d7a8a` |
| https://www.courtlistener.com/api/rest/v4/courts/me/?fields=id,full_name,jurisdiction | 2026-10-20 | 76 | `156a59cbf6d71444` |
| https://www.courtlistener.com/api/rest/v4/courts/med/?fields=id,full_name,jurisdiction | 2026-10-20 | 71 | `7f42a4b3e1783029` |
| https://www.courtlistener.com/api/rest/v4/courts/mied/?fields=id,full_name,jurisdiction | 2026-10-20 | 77 | `45d82da393e3b8aa` |
| https://www.courtlistener.com/api/rest/v4/courts/nd/?fields=id,full_name,jurisdiction | 2026-10-20 | 71 | `25bc93b93f36adbe` |
| https://www.courtlistener.com/api/rest/v4/courts/nmctapp/?fields=id,full_name,jurisdiction | 2026-10-20 | 78 | `b62f2d8030138bfa` |
| https://www.courtlistener.com/api/rest/v4/courts/nyappdiv/?fields=id,full_name,jurisdiction | 2026-10-20 | 116 | `d259d9068ce26339` |
| https://www.courtlistener.com/api/rest/v4/courts/nycfamct/?fields=id,full_name,jurisdiction | 2026-10-20 | 78 | `48d3351593e1334e` |
| https://www.courtlistener.com/api/rest/v4/courts/nycrimct/?fields=id,full_name,jurisdiction | 2026-10-20 | 90 | `1a6eb22b7d4d617d` |
| https://www.courtlistener.com/api/rest/v4/courts/okla/?fields=id,full_name,jurisdiction | 2026-10-20 | 72 | `7aa8f3f96415e99d` |
| https://www.courtlistener.com/api/rest/v4/courts/pa/?fields=id,full_name,jurisdiction | 2026-10-20 | 74 | `6dc9e2b81959b520` |
| https://www.courtlistener.com/api/rest/v4/courts/pacommwct/?fields=id,full_name,jurisdiction | 2026-10-20 | 87 | `f857dbe4bbc894aa` |
| https://www.courtlistener.com/api/rest/v4/courts/pasuperct/?fields=id,full_name,jurisdiction | 2026-10-20 | 83 | `c83ac545e1b8882e` |
| https://www.courtlistener.com/api/rest/v4/courts/tennctapp/?fields=id,full_name,jurisdiction | 2026-10-20 | 82 | `2c30dbafa6b06f5f` |
| https://www.courtlistener.com/api/rest/v4/dockets/1024599/?fields=court_id | 2026-10-20 | 19 | `940865efa1dd0527` |
| https://www.courtlistener.com/api/rest/v4/dockets/1027904/?fields=court_id | 2026-10-20 | 17 | `0a850ee7113a06cc` |
| https://www.courtlistener.com/api/rest/v4/dockets/1557513/?fields=court_id | 2026-10-20 | 17 | `a591899cfe460ecb` |
| https://www.courtlistener.com/api/rest/v4/dockets/1604835/?fields=court_id | 2026-10-20 | 19 | `b8233b6e3570bc55` |
| https://www.courtlistener.com/api/rest/v4/dockets/16110473/?fields=court_id | 2026-10-20 | 17 | `68340829a4e0761e` |
| https://www.courtlistener.com/api/rest/v4/dockets/1620886/?fields=court_id | 2026-10-20 | 24 | `17008e1e8cdf0199` |
| https://www.courtlistener.com/api/rest/v4/dockets/1961778/?fields=court_id | 2026-10-20 | 19 | `7b5192a9d31873da` |
| https://www.courtlistener.com/api/rest/v4/dockets/1963000/?fields=court_id | 2026-10-20 | 23 | `af5baa898846ad77` |
| https://www.courtlistener.com/api/rest/v4/dockets/2017813/?fields=court_id | 2026-10-20 | 23 | `af5baa898846ad77` |
| https://www.courtlistener.com/api/rest/v4/dockets/213462/?fields=court_id | 2026-10-20 | 19 | `77566a103cc259b2` |
| https://www.courtlistener.com/api/rest/v4/dockets/2162030/?fields=court_id | 2026-10-20 | 23 | `af5baa898846ad77` |
| https://www.courtlistener.com/api/rest/v4/dockets/2165307/?fields=court_id | 2026-10-20 | 23 | `af5baa898846ad77` |
| https://www.courtlistener.com/api/rest/v4/dockets/2191147/?fields=court_id | 2026-10-20 | 24 | `17008e1e8cdf0199` |
| https://www.courtlistener.com/api/rest/v4/dockets/2243691/?fields=court_id | 2026-10-20 | 22 | `dff5ab199b6885e6` |
| https://www.courtlistener.com/api/rest/v4/dockets/232989/?fields=court_id | 2026-10-20 | 24 | `6ce974ba6bc70f63` |
| https://www.courtlistener.com/api/rest/v4/dockets/2368221/?fields=court_id | 2026-10-20 | 19 | `4cf10a25e1d79545` |
| https://www.courtlistener.com/api/rest/v4/dockets/2436058/?fields=court_id | 2026-10-20 | 22 | `28fdfbcc45a1467b` |
| https://www.courtlistener.com/api/rest/v4/dockets/2533617/?fields=court_id | 2026-10-20 | 24 | `b7c2a3432ff2f58c` |
| https://www.courtlistener.com/api/rest/v4/dockets/43247/?fields=court_id | 2026-10-20 | 18 | `7649947645f15f8b` |
| https://www.courtlistener.com/api/rest/v4/dockets/524321/?fields=court_id | 2026-10-20 | 24 | `b7c2a3432ff2f58c` |
| https://www.courtlistener.com/api/rest/v4/dockets/60463837/?fields=court_id | 2026-10-20 | 17 | `9dd96378a985b31d` |
| https://www.courtlistener.com/api/rest/v4/dockets/60576730/?fields=court_id | 2026-10-20 | 24 | `6ce974ba6bc70f63` |
| https://www.courtlistener.com/api/rest/v4/dockets/62453741/?fields=court_id | 2026-10-20 | 23 | `ca605e446c956171` |
| https://www.courtlistener.com/api/rest/v4/dockets/63006078/?fields=court_id | 2026-10-20 | 23 | `a59f2308805ca993` |
| https://www.courtlistener.com/api/rest/v4/dockets/63006735/?fields=court_id | 2026-10-20 | 23 | `a59f2308805ca993` |
| https://www.courtlistener.com/api/rest/v4/dockets/63007130/?fields=court_id | 2026-10-20 | 23 | `f455fbb75e5add9e` |
| https://www.courtlistener.com/api/rest/v4/dockets/63518200/?fields=court_id | 2026-10-20 | 24 | `ee8ccae1b10d90ba` |
| https://www.courtlistener.com/api/rest/v4/dockets/63527189/?fields=court_id | 2026-10-20 | 22 | `28fdfbcc45a1467b` |
| https://www.courtlistener.com/api/rest/v4/dockets/8217234/?fields=court_id | 2026-10-20 | 24 | `6094d139c64f7195` |
| https://www.courtlistener.com/api/rest/v4/dockets/993380/?fields=court_id | 2026-10-20 | 18 | `4d4e4427df6d8bec` |
| https://www.courtlistener.com/api/rest/v4/opinions/1072657/?fields=cluster | 2026-10-20 | 73 | `fc0251c13087fae2` |
| https://www.courtlistener.com/api/rest/v4/opinions/1194895/?fields=cluster | 2026-10-20 | 73 | `e0facb8eb8f85240` |
| https://www.courtlistener.com/api/rest/v4/opinions/1255323/?fields=cluster | 2026-10-20 | 73 | `6d7ce20d4cb46ce3` |
| https://www.courtlistener.com/api/rest/v4/opinions/1401377/?fields=cluster | 2026-10-20 | 73 | `fd8478244994b624` |
| https://www.courtlistener.com/api/rest/v4/opinions/1460811/?fields=cluster | 2026-10-20 | 73 | `1245976254e33a06` |
| https://www.courtlistener.com/api/rest/v4/opinions/1463254/?fields=cluster | 2026-10-20 | 73 | `4fdd44e1bdaf8d30` |
| https://www.courtlistener.com/api/rest/v4/opinions/1469130/?fields=cluster | 2026-10-20 | 73 | `0780cf37af9816d3` |
| https://www.courtlistener.com/api/rest/v4/opinions/1503218/?fields=cluster | 2026-10-20 | 73 | `ab48c58b3be3db1b` |
| https://www.courtlistener.com/api/rest/v4/opinions/2113659/?fields=cluster | 2026-10-20 | 73 | `44d4bf721ef2eea4` |
| https://www.courtlistener.com/api/rest/v4/opinions/2135107/?fields=cluster | 2026-10-20 | 73 | `ea487c76ee4ccb95` |
| https://www.courtlistener.com/api/rest/v4/opinions/2149269/?fields=cluster | 2026-10-20 | 73 | `98c81426dc3163f2` |
| https://www.courtlistener.com/api/rest/v4/opinions/2275138/?fields=cluster | 2026-10-20 | 73 | `9cf3b13011f634c1` |
| https://www.courtlistener.com/api/rest/v4/opinions/2278575/?fields=cluster | 2026-10-20 | 73 | `a671a438c477e3fc` |
| https://www.courtlistener.com/api/rest/v4/opinions/2321051/?fields=cluster | 2026-10-20 | 73 | `bd79437629a46233` |
| https://www.courtlistener.com/api/rest/v4/opinions/2398329/?fields=cluster | 2026-10-20 | 73 | `22119140ab2e19cf` |
| https://www.courtlistener.com/api/rest/v4/opinions/2500776/?fields=cluster | 2026-10-20 | 73 | `a7f9b298710c3ee6` |
| https://www.courtlistener.com/api/rest/v4/opinions/2502448/?fields=cluster | 2026-10-20 | 73 | `8d5d9ba8c94df26d` |
| https://www.courtlistener.com/api/rest/v4/opinions/2570257/?fields=cluster | 2026-10-20 | 73 | `b1d57eba7fccb3d9` |
| https://www.courtlistener.com/api/rest/v4/opinions/2626767/?fields=cluster | 2026-10-20 | 73 | `25c17ffd58de4bd5` |
| https://www.courtlistener.com/api/rest/v4/opinions/2644498/?fields=cluster | 2026-10-20 | 73 | `c963af1d66fbfdec` |
| https://www.courtlistener.com/api/rest/v4/opinions/4343366/?fields=cluster | 2026-10-20 | 73 | `0897d287bdb3238e` |
| https://www.courtlistener.com/api/rest/v4/opinions/4433277/?fields=cluster | 2026-10-20 | 73 | `a9bea2c8fb6933e6` |
| https://www.courtlistener.com/api/rest/v4/opinions/4970825/?fields=cluster | 2026-10-20 | 73 | `9030b418b72f2787` |
| https://www.courtlistener.com/api/rest/v4/opinions/5072472/?fields=cluster | 2026-10-20 | 73 | `cac851db3d4efb8a` |
| https://www.courtlistener.com/api/rest/v4/opinions/5958060/?fields=cluster | 2026-10-20 | 73 | `62ac87a83f61f612` |
| https://www.courtlistener.com/api/rest/v4/opinions/6224542/?fields=cluster | 2026-10-20 | 73 | `aaaa52bb10030941` |
| https://www.courtlistener.com/api/rest/v4/opinions/6225195/?fields=cluster | 2026-10-20 | 73 | `dd3599a134065059` |
| https://www.courtlistener.com/api/rest/v4/opinions/6225590/?fields=cluster | 2026-10-20 | 73 | `724b11d0ff15badb` |
| https://www.courtlistener.com/api/rest/v4/opinions/6462542/?fields=cluster | 2026-10-20 | 73 | `08274813119775f5` |
| https://www.courtlistener.com/api/rest/v4/opinions/6472086/?fields=cluster | 2026-10-20 | 73 | `89e5fdf559d4091d` |
| https://www.courtlistener.com/api/rest/v4/opinions/78542/?fields=cluster | 2026-10-20 | 71 | `bf4dfa4d4963d2e0` |
| https://www.ecfr.gov/api/versioner/v1/structure/2026-10-01/title-25.json | 2026-10-18 | 1688966 | `75578ae09f3bca7e` |
| https://www.ecfr.gov/api/versioner/v1/structure/2026-10-01/title-26.json | 2026-10-18 | 2022515 | `3b460699588bae45` |
| https://www.ecfr.gov/api/versioner/v1/structure/2026-10-01/title-40.json | 2026-10-18 | 9395956 | `a1075ffa9b788006` |
| https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/html/CDOC-110hdoc50.htm | 2026-10-18 | 298236 | `e8a9606e762ea07e` |
| https://www.govinfo.gov/link/fr/11/5593 | 2026-10-18 | 78 | `9f24f6698f9e7b9d` |
| https://www.govinfo.gov/link/fr/50/40293 | 2026-10-18 | 80 | `545e0c8fdad17088` |
| https://www.govinfo.gov/metadata/pkg/STATUTE-112/mods.xml | 2026-10-18 | 2373696 | `d318fcfdf59f4559` |
| https://www.govinfo.gov/metadata/pkg/STATUTE-87/mods.xml | 2026-10-18 | 2716308 | `2c2f5722bd0c68c3` |
| https://www.govinfo.gov/metadata/pkg/STATUTE-88/mods.xml | 2026-10-18 | 4105166 | `256ac7d04318b1f9` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title10/mods.xml | 2026-10-18 | 59625382 | `d64ecdf7e9f720a5` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title18/mods.xml | 2026-10-18 | 17920559 | `00adbdc751c12800` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title21/mods.xml | 2026-10-18 | 8936598 | `ec71e4b67494cc53` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title25/mods.xml | 2026-10-18 | 16249854 | `f38e98aa99d78789` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title28/mods.xml | 2026-10-18 | 13235138 | `63b10e16b6a5a6a3` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title29/mods.xml | 2026-10-18 | 10072797 | `55b6c944b3d13dd2` |
| https://www.govinfo.gov/metadata/pkg/USCODE-2024-title45/mods.xml | 2026-10-18 | 3494927 | `dbcc96092c153760` |
| https://www.jud.ct.gov/Publications/PracticeBook/PB.pdf | 2026-10-18 | 24019149 | `bb406ab49314de7f` |
| https://www.legis.la.gov/legis/Law.aspx?d=107262 | 2026-10-18 | 25756 | `0fea6e5dcd251b25` |
| https://www.legis.la.gov/legis/Law.aspx?d=408539 | 2026-10-18 | 21717 | `7a30d93b8259a297` |
| https://www.legis.la.gov/legis/Laws_Toc.aspx?folder=75&level=Parent | 2026-10-18 | 86685 | `44f615e83ad19ae8` |
| https://www.legis.la.gov/legis/Laws_Toc.aspx?folder=75&level=Parent#postback=TITLE 13 | 2026-10-18 | 1824663 | `995c2a07f03978f9` |
| https://www.legis.la.gov/legis/Laws_Toc.aspx?folder=75&level=Parent#postback=TITLE 9 | 2026-10-18 | 2060003 | `795446a94dc6d4fd` |
| https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-257-520 | 2026-10-18 | 27577 | `f24ef7b214570fd2` |
| https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-600-6013 | 2026-10-18 | 31460 | `780369394425a4a6` |
| https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_1/GS_1-420.html | 2026-10-18 | 1734 | `004307100b711558` |
| https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_15A/GS_15A-544.5.html | 2026-10-18 | 12761 | `e694c4d396c95c6c` |
| https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_15A/GS_15A-910.html | 2026-10-18 | 3076 | `b407dd706f6b83ab` |
| https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_163/GS_163-122.html | 2026-10-18 | 12381 | `46a22beb9a82d761` |
| https://www.palegis.us/statutes/consolidated/view-statute?txtType=HTM&ttl=42&div=0&chapter=7&section=8&subsctn=0&iFrame=true | 2026-10-18 | 6876 | `3f19abc41aa66ab9` |
| https://www.palegis.us/statutes/consolidated/view-statute?txtType=HTM&ttl=42&div=0&chapter=97&section=81&subsctn=0&iFrame=true | 2026-10-18 | 11669 | `e096791cff28b0cd` |
| https://www.palegis.us/statutes/consolidated/view-statute?txtType=HTM&ttl=58&div=0&chapter=32&section=2&subsctn=0&iFrame=true | 2026-10-18 | 3918 | `c5268ed39731a309` |
| https://www.palegis.us/statutes/consolidated/view-statute?txtType=HTM&ttl=75&div=0&chapter=15&section=43&subsctn=0&iFrame=true | 2026-10-18 | 17059 | `347644ee5fc0f7da` |
| https://www.txcourts.gov/media/1463134/texas-rules-of-appellate-procedure-02062026.pdf | 2026-10-18 | 1910974 | `28d0d6236d84e174` |
| https://www.txcourts.gov/media/1463426/texas-rules-of-civil-procedure.pdf | 2026-10-18 | 1760656 | `bd9d874a40e3fdd9` |
| https://www.ussc.gov/guidelines/2025-guidelines-manual | 2026-10-18 | 171898 | `f9698d73ca5945f2` |
