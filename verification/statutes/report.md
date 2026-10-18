# Statute vectors checked against official sources

Written by `bench/verify_statutes.py` (`mise run verify:statutes`). A verdict doesn't change a vector's provenance.

| Set | Vectors | Verified by source | Contradicted | Unverifiable |
|---|---:|---:|---:|---:|
| statutes | 78 | 19 | 0 | 59 |
| statutes-proposed | 36 | 21 | 0 | 15 |
| **all** | 114 | 40 | 0 | 74 |

## Contradicted

None.

## What needs a person

### Code forms: one answer covers every vector with the form

- `A.C.A.` means `Ark. Code Ann.` (Arkansas): 2 (`ark_aca/0`, `ark_aca/1`)
- `A.R.S.` means `Ariz. Rev. Stat.` (Arizona): 2 (`ariz_ars/0`, `ariz_ars/1`)
- `Code Civ. Proc.` means `Cal. Civ. Proc. Code` (California): 2 (`cal_code_civ_proc/0`, `cal_code_civ_proc/1`)
- `Family Ct Act` means `N.Y. Family Ct Act` (New York): 2 (`ny_family_ct_act/0`, `ny_family_ct_act/1`)
- `G.L.` means `R.I. Gen. Laws` (Rhode Island): 2 (`ri_gl_1956/0`, `ri_gl_1956/1`)
- `La.Rev.Stat.` means `La. Stat. Ann.` (Louisiana): 2 (`la_rev_stat/0`, `la_rev_stat/1`)
- `M.C.L.A.` means `Mich. Comp. Laws` (Michigan): 2 (`mich_mcl/0`, `mich_mcl/1`)
- `M.R.S.A.` means `Me. Rev. Stat. Ann.` (Maine): 2 (`me_mrsa/0`, `me_mrsa/1`)
- `NMSA` means `N.M. Stat. Ann.` (New Mexico): 2 (`nm_nmsa/0`, `nm_nmsa/1`)
- `O.C.G.A.` means `Ga. Code Ann.` (Georgia): 2 (`ga_o_c_g_a/0`, `ga_o_c_g_a/1`)
- `OCGA` means `Ga. Code Ann.` (Georgia): 2 (`ga_ocga/0`, `ga_ocga/1`)
- `Pa.C.S.` means `Pa. Cons. Stat.` (Pennsylvania): 2 (`pa_cs/0`, `pa_cs/1`)
- `Penal Law` means `N.Y. Penal Law` (New York): 2 (`ny_penal_law/0`, `ny_penal_law/1`)
- `T.C.A.` means `Tenn. Code Ann.` (Tennessee): 2 (`tenn_tca/0`, `tenn_tca/1`)
- `West Virginia Code` means `W. Va. Code` (West Virginia): 2 (`wva_code/0`, `wva_code/1`)
- `Evid. Code` means `Cal. Evid. Code` (California): 1 (`cal_evid_code/1`)
- `G. L.` means `Mass. Gen. Laws` (Massachusetts): 1 (`mass_g_l_c/0`)
- `G.L.` means `Mass. Gen. Laws` (Massachusetts): 1 (`mass_g_l_c/1`)
- `HRS` means `Haw. Rev. Stat.` (Hawaii): 1 (`haw_hrs/1`)
- `MCR` means `Mich. Ct. R.` (Michigan): 1 (`mich_ct_r/0`)
- `N.D.C.C.` means `N.D. Cent. Code` (North Dakota): 1 (`nd_ndcc/1`)
- `N.J.A.C.` means `N.J. Admin. Code` (New Jersey): 1 (`njac/0`)
- `NYCRR` means `N.Y. Comp. Codes R. & Regs.` (New York): 1 (`nycrr/0`)
- `O.S.` means `Okla. Stat.` (Oklahoma): 1 (`okla_os/1`)
- `P.S.` means `Pa. Stat. Ann.` (Pennsylvania): 1 (`pa_ps/0`)
- `Pa.C.S.A.` means `Pa. Cons. Stat.` (Pennsylvania): 1 (`pa_csa/0`)
- `Pen. Code` means `Cal. Pen. Code` (California): 1 (`cal_pen_code/0`)

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

- `Conn. Gen. Stat.`: cga.ct.gov didn't answer from here on 2026-10-18, and it publishes sections inside chapter pages: 6 (`conn_general_statutes/0`, `conn_general_statutes/1`, `conn_general_statutes_revision/0`, `conn_general_statutes_revision/1`, `conn_gen_stat/0`, `conn_gen_stat/1`)
- `Ga. Code Ann.`: Georgia's official code is online through LexisNexis; not used: 4 (`ga_ocga/0`, `ga_ocga/1`, `ga_o_c_g_a/0`, `ga_o_c_g_a/1`)
- `Ala. Code`: alison.legislature.state.al.us renders sections client-side: 2 (`ala_code_1975/0`, `ala_code_1975/1`)
- `Ark. Code Ann.`: Arkansas's official code is online through LexisNexis; not used: 2 (`ark_aca/0`, `ark_aca/1`)
- `Cal. Civ. Proc. Code`: as Cal. Pen. Code: 2 (`cal_code_civ_proc/0`, `cal_code_civ_proc/1`)
- `Cal. Evid. Code`: as Cal. Pen. Code: 2 (`cal_evid_code/0`, `cal_evid_code/1`)
- `Cal. Pen. Code`: leginfo.legislature.ca.gov answered HTTP 403 to scripted requests; its bulk pubinfo archive isn't wired in: 2 (`cal_pen_code/0`, `cal_pen_code/1`)
- `Conn. Practice Book`: the Practice Book is a PDF on jud.ct.gov; not wired in: 2 (`conn_practice_book/0`, `conn_practice_book/1`)
- `Haw. Rev. Stat.`: capitol.hawaii.gov answered HTTP 403 to scripted requests: 2 (`haw_hrs/0`, `haw_hrs/1`)
- `La. Stat. Ann.`: legis.la.gov addresses sections by document id; not wired in: 2 (`la_rev_stat/0`, `la_rev_stat/1`)
- `N.D. Cent. Code`: ndlegis.gov publishes chapter PDFs; PDF text isn't read here: 2 (`nd_ndcc/0`, `nd_ndcc/1`)
- `N.M. Stat. Ann.`: nmonesource.com addresses sections by document id; not wired in: 2 (`nm_nmsa/0`, `nm_nmsa/1`)
- `N.Y. Family Ct Act`: as N.Y. Penal Law: 2 (`ny_family_ct_act/0`, `ny_family_ct_act/1`)
- `N.Y. Penal Law`: nysenate.gov answered HTTP 403 to scripted requests; its Open Legislation API needs a key: 2 (`ny_penal_law/0`, `ny_penal_law/1`)
- `Okla. Stat.`: OSCN addresses sections by document id; not wired in: 2 (`okla_os/0`, `okla_os/1`)
- `Pa. Stat. Ann.`: Purdon's title and section numbers have no official per-section source; palegis.us indexes unconsolidated statutes by act: 2 (`pa_ps/0`, `pa_ps/1`)
- `Tenn. Code Ann.`: Tennessee's official code is online through LexisNexis; not used: 2 (`tenn_tca/0`, `tenn_tca/1`)
- `Vt. Stat. Ann.`: legislature.vermont.gov paths need the chapter; not wired in: 2 (`vt_vsa/0`, `vt_vsa/1`)
- `Cal. Civ. Code`: as Cal. Pen. Code: 1 (`cal_civ_code/0`)
- `Ind. Const.`: no official source wired in: 1 (`state_const/1`)
- `Mich. Ct. R.`: the rules are a PDF on courts.michigan.gov; not wired in: 1 (`mich_ct_r/0`)
- `N.J. Admin. Code`: the N.J.A.C. is online through LexisNexis; not used: 1 (`njac/0`)
- `N.M. Const.`: no official source wired in: 1 (`state_const/2`)
- `N.Y. Comp. Codes R. & Regs.`: the official NYCRR is online through Thomson Reuters Westlaw; not used: 1 (`nycrr/0`)
- `N.Y. Judiciary Law`: as N.Y. Penal Law: 1 (`ny_judiciary_law/0`)
- `Ohio Const.`: codes.ohio.gov renders sections client-side: 1 (`state_const/0`)
- `Pa. R. Civ. P.`: pacodeandbulletin.gov returned no rule text without scripting: 1 (`pa_r_civ_p/0`)
- `Tex. R. App. P.`: the rules are a PDF on txcourts.gov; not wired in: 1 (`tex_r_p/1`)
- `Tex. R. Civ. P.`: the rules are a PDF on txcourts.gov; not wired in: 1 (`tex_r_p/0`)

## Verdicts

| Vector | Provenance | Verdict |
|---|---|---|
| `statutes/find/conn_general_statutes/0` | hand-checked | unverifiable:existence |
| `statutes/find/conn_general_statutes/1` | hand-checked | unverifiable:existence |
| `statutes/find/conn_general_statutes_revision/0` | hand-checked | unverifiable:existence, span |
| `statutes/find/conn_general_statutes_revision/1` | hand-checked | unverifiable:existence, span |
| `statutes/find/conn_practice_book/0` | hand-checked | unverifiable:code, existence |
| `statutes/find/conn_practice_book/1` | hand-checked | unverifiable:code, existence |
| `statutes/find/conn_gen_stat/0` | hand-checked | unverifiable:existence |
| `statutes/find/conn_gen_stat/1` | hand-checked | unverifiable:existence, span |
| `statutes/find/ga_ocga/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/ga_ocga/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/ga_o_c_g_a/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/ga_o_c_g_a/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/ariz_ars/0` | hand-checked | unverifiable:form |
| `statutes/find/ariz_ars/1` | hand-checked | unverifiable:form |
| `statutes/find/haw_hrs/0` | hand-checked | unverifiable:existence |
| `statutes/find/haw_hrs/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/nc_ncgs/0` | hand-checked | verified-by-source:cap+cap-case-metadata+ncleg+reporters-db@v3.2.67 |
| `statutes/find/nc_ncgs/1` | hand-checked | verified-by-source:cap+cap-case-metadata+ncleg+reporters-db@v3.2.67 |
| `statutes/find/nc_gs/0` | hand-checked | verified-by-source:ncleg+reporters-db@v3.2.67 |
| `statutes/find/nc_gs/1` | hand-checked | verified-by-source:ncleg+reporters-db@v3.2.67 |
| `statutes/find/nd_ndcc/0` | hand-checked | unverifiable:existence |
| `statutes/find/nd_ndcc/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/tenn_tca/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/tenn_tca/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/pa_cs/0` | hand-checked | unverifiable:form |
| `statutes/find/pa_cs/1` | hand-checked | unverifiable:form |
| `statutes/find/pa_csa/0` | hand-checked | unverifiable:form |
| `statutes/find/pa_csa/1` | hand-checked | verified-by-source:cap+cap-case-metadata+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_ps/0` | hand-checked | unverifiable:code, existence, form |
| `statutes/find/pa_ps/1` | hand-checked | unverifiable:code, existence |
| `statutes/find/me_mrs/0` | hand-checked | verified-by-source:cap+cap-case-metadata+maine-legislature+reporters-db@v3.2.67 |
| `statutes/find/me_mrs/1` | hand-checked | verified-by-source:cap+cap-case-metadata+maine-legislature+reporters-db@v3.2.67 |
| `statutes/find/me_mrsa/0` | hand-checked | unverifiable:form |
| `statutes/find/me_mrsa/1` | hand-checked | unverifiable:form |
| `statutes/find/vt_vsa/0` | hand-checked | unverifiable:existence |
| `statutes/find/vt_vsa/1` | hand-checked | unverifiable:existence |
| `statutes/find/okla_os/0` | hand-checked | unverifiable:existence, span |
| `statutes/find/okla_os/1` | hand-checked | unverifiable:existence, form, span |
| `statutes/find/ny_penal_law/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/ny_penal_law/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/ny_judiciary_law/0` | hand-checked | unverifiable:existence |
| `statutes/find/ny_family_ct_act/0` | hand-checked | unverifiable:code, existence, form |
| `statutes/find/ny_family_ct_act/1` | hand-checked | unverifiable:code, existence, form |
| `statutes/find/cal_pen_code/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/cal_pen_code/1` | hand-checked | unverifiable:existence |
| `statutes/find/cal_code_civ_proc/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/cal_code_civ_proc/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/cal_evid_code/0` | hand-checked | unverifiable:existence |
| `statutes/find/cal_evid_code/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/cal_civ_code/0` | hand-checked | unverifiable:existence |
| `statutes/find/tex_small_caps/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_small_caps/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_no_space/0` | hand-checked | verified-by-source:cap+reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_no_space/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_penal_code_ann/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_penal_code_ann/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/mass_g_l_c/0` | hand-checked | unverifiable:form |
| `statutes/find/mass_g_l_c/1` | hand-checked | unverifiable:form |
| `statutes/find/mass_gen_laws_ch/0` | hand-checked | verified-by-source:ma-legislature+reporters-db@v3.2.67 |
| `statutes/find/nm_nmsa/0` | hand-checked | unverifiable:existence, form, span |
| `statutes/find/nm_nmsa/1` | hand-checked | unverifiable:existence, form, span |
| `statutes/find/mich_mcl/0` | hand-checked | unverifiable:form |
| `statutes/find/mich_mcl/1` | hand-checked | unverifiable:form |
| `statutes/find/ala_code_1975/0` | hand-checked | unverifiable:existence, span |
| `statutes/find/ala_code_1975/1` | hand-checked | unverifiable:existence, span |
| `statutes/find/ark_aca/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/ark_aca/1` | hand-checked | unverifiable:existence, form |
| `statutes/find/la_rev_stat/0` | hand-checked | unverifiable:existence, form |
| `statutes/find/la_rev_stat/1` | hand-checked | unverifiable:existence, form |
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
| `statutes-proposed/find/tex_r_p/0` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/tex_r_p/1` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/pa_r_civ_p/0` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/mich_ct_r/0` | proposed | unverifiable:existence, form |
| `statutes-proposed/find/us_const/0` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/1` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/2` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/3` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/state_const/0` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/state_const/1` | proposed | unverifiable:code, existence |
| `statutes-proposed/find/state_const/2` | proposed | unverifiable:code, existence |
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
| https://code.wvlegislature.gov/31-1-15/ | 2026-10-18 | 40139 | `8491d2872b4f8df3` |
| https://code.wvlegislature.gov/56-6-31/ | 2026-10-18 | 44556 | `693677696d02e655` |
| https://docs.legis.wisconsin.gov/statutes/statutes/706/09 | 2026-10-18 | 95515 | `8184d1a627ddbd91` |
| https://legislature.maine.gov/statutes/1/title1sec402.html | 2026-10-18 | 48892 | `4d965854b6c7328a` |
| https://legislature.maine.gov/statutes/11/title11sec1-203.html | 2026-10-18 | 9232 | `22009510bb98d7e1` |
| https://legislature.maine.gov/statutes/15/title15sec2115-A.html | 2026-10-18 | 18779 | `3c8209a1c9993b3e` |
| https://legislature.maine.gov/statutes/19-A/title19-Asec1653.html | 2026-10-18 | 80149 | `ea2010ffd24c776a` |
| https://malegislature.gov/Laws/GeneralLaws/Chapter184/Section15 | 2026-10-18 | 81354 | `5a90d3adfaf50c3e` |
| https://malegislature.gov/Laws/GeneralLaws/Chapter260/Section2A | 2026-10-18 | 73446 | `1162013886cfdf9b` |
| https://malegislature.gov/Laws/GeneralLaws/Chapter278/Section33E | 2026-10-18 | 74745 | `77fac6d4742f81c4` |
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
| https://www.ussc.gov/guidelines/2025-guidelines-manual | 2026-10-18 | 171898 | `f9698d73ca5945f2` |
