# Statute vectors checked against official sources

Written by `bench/verify_statutes.py` (`mise run verify:statutes`). A verdict doesn't change a vector's provenance.

| Set | Vectors | Verified by source | Contradicted | Unverifiable |
|---|---:|---:|---:|---:|
| statutes | 93 | 92 | 0 | 1 |
| statutes-proposed | 21 | 21 | 0 | 0 |
| **all** | 114 | 113 | 0 | 1 |

## Contradicted

None.

## Settled by the maintainer's rulings

Claims no machine source settles, answered once per form, code, span pattern or vector in `verification/statutes/rulings.json`.

- owner-ruled 2026-10-25 (A63): 46 vectors (code 18, existence 18, form 11, span 10)

## What needs a person

### Span judgments

- whitespace inside a section (`10 -236b`): 1 (`conn_gen_stat/1`)

## Verdicts

| Vector | Provenance | Verdict |
|---|---|---|
| `statutes/find/conn_general_statutes/0` | hand-checked | verified-by-source:cap-case-metadata+cga+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/conn_general_statutes/1` | hand-checked | verified-by-source:cap-case-metadata+cga+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/conn_general_statutes_revision/0` | verified | verified-by-source:cap-case-metadata+cga+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/conn_general_statutes_revision/1` | verified | verified-by-source:cap-case-metadata+cga+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/conn_practice_book/0` | verified | verified-by-source:cap-case-metadata+ct-judicial+owner-ruling-A63+stare-pub-cap |
| `statutes/find/conn_practice_book/1` | verified | verified-by-source:cap-case-metadata+ct-judicial+owner-ruling-A63+stare-pub-cap |
| `statutes/find/conn_gen_stat/0` | hand-checked | verified-by-source:cga+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/conn_gen_stat/1` | hand-checked | unverifiable:span |
| `statutes/find/ga_ocga/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/ga_ocga/1` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ga_o_c_g_a/0` | verified | verified-by-source:owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ga_o_c_g_a/1` | verified | verified-by-source:owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/ariz_ars/0` | hand-checked | verified-by-source:azleg+cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ariz_ars/1` | hand-checked | verified-by-source:azleg+cap-case-metadata+reporters-db@v3.2.67 |
| `statutes/find/haw_hrs/0` | hand-checked | verified-by-source:cap-case-metadata+hawaii-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/haw_hrs/1` | hand-checked | verified-by-source:cap-case-metadata+hawaii-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nc_ncgs/0` | hand-checked | verified-by-source:cap-case-metadata+ncleg+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nc_ncgs/1` | hand-checked | verified-by-source:cap-case-metadata+ncleg+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nc_gs/0` | hand-checked | verified-by-source:ncleg+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nc_gs/1` | hand-checked | verified-by-source:ncleg+reporters-db@v3.2.67 |
| `statutes/find/nd_ndcc/0` | hand-checked | verified-by-source:cap-case-metadata+nd-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nd_ndcc/1` | hand-checked | verified-by-source:cap-case-metadata+nd-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/tenn_tca/0` | verified | verified-by-source:courtlistener-api+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/tenn_tca/1` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/pa_cs/0` | hand-checked | verified-by-source:cap-case-metadata+pa-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/pa_cs/1` | hand-checked | verified-by-source:cap-case-metadata+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_csa/0` | hand-checked | verified-by-source:courtlistener-api+pa-legislature+reporters-db@v3.2.67 |
| `statutes/find/pa_csa/1` | hand-checked | verified-by-source:cap-case-metadata+pa-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/pa_ps/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63 |
| `statutes/find/pa_ps/1` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+stare-pub-cap |
| `statutes/find/me_mrs/0` | hand-checked | verified-by-source:cap-case-metadata+maine-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/me_mrs/1` | hand-checked | verified-by-source:cap-case-metadata+maine-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/me_mrsa/0` | verified | verified-by-source:maine-legislature+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/me_mrsa/1` | hand-checked | verified-by-source:cap-case-metadata+maine-legislature+reporters-db@v3.2.67 |
| `statutes/find/vt_vsa/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/vt_vsa/1` | hand-checked | verified-by-source:cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap+vermont-legislature |
| `statutes/find/okla_os/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/okla_os/1` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/ny_penal_law/0` | hand-checked | verified-by-source:cap-case-metadata+ny-openleg+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ny_penal_law/1` | hand-checked | verified-by-source:cap-case-metadata+ny-openleg+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ny_judiciary_law/0` | hand-checked | verified-by-source:cap-case-metadata+ny-openleg+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ny_family_ct_act/0` | verified | verified-by-source:cap-case-metadata+ny-openleg+owner-ruling-A63+stare-pub-cap |
| `statutes/find/ny_family_ct_act/1` | verified | verified-by-source:cap-case-metadata+ny-openleg+owner-ruling-A63+stare-pub-cap |
| `statutes/find/cal_pen_code/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap-case-metadata+reporters-db@v3.2.67 |
| `statutes/find/cal_pen_code/1` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/cal_code_civ_proc/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/cal_code_civ_proc/1` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/cal_evid_code/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/cal_evid_code/1` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+cap-case-metadata+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/cal_civ_code/0` | hand-checked | verified-by-source:ca-leginfo-pubinfo-2025+reporters-db@v3.2.67 |
| `statutes/find/tex_small_caps/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_small_caps/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_no_space/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+stare-pub-cap+texas-legislative-council |
| `statutes/find/tex_no_space/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_penal_code_ann/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/tex_penal_code_ann/1` | hand-checked | verified-by-source:reporters-db@v3.2.67+texas-legislative-council |
| `statutes/find/mass_g_l_c/0` | hand-checked | verified-by-source:cap-case-metadata+ma-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/mass_g_l_c/1` | hand-checked | verified-by-source:cap-case-metadata+ma-legislature+reporters-db@v3.2.67 |
| `statutes/find/mass_gen_laws_ch/0` | hand-checked | verified-by-source:ma-legislature+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nm_nmsa/0` | verified | verified-by-source:cap-case-metadata+nmcc-nmonesource+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/nm_nmsa/1` | verified | verified-by-source:cap-case-metadata+nmcc-nmonesource+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/mich_mcl/0` | verified | verified-by-source:mi-legislature+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/mich_mcl/1` | verified | verified-by-source:mi-legislature+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ala_code_1975/0` | verified | verified-by-source:alison+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ala_code_1975/1` | verified | verified-by-source:alison+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/ark_aca/0` | verified | verified-by-source:owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/ark_aca/1` | verified | verified-by-source:owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/la_rev_stat/0` | verified | verified-by-source:la-legislature+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/la_rev_stat/1` | verified | verified-by-source:la-legislature+owner-ruling-A63+reporters-db@v3.2.67 |
| `statutes/find/ri_gl_1956/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+ri-legislature |
| `statutes/find/ri_gl_1956/1` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+ri-legislature |
| `statutes/find/wva_code/0` | verified | verified-by-source:owner-ruling-A63+reporters-db@v3.2.67+wv-legislature |
| `statutes/find/wva_code/1` | verified | verified-by-source:cap-case-metadata+reporters-db@v3.2.67+wv-legislature |
| `statutes/find/wis_stat_caps/0` | hand-checked | verified-by-source:reporters-db@v3.2.67+wi-legislature |
| `statutes/find/usc/0` | hand-checked | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes/find/usc/1` | hand-checked | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67 |
| `statutes/find/cfr/0` | hand-checked | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes/find/cfr/1` | hand-checked | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes/find/fed_r_evid/0` | verified | verified-by-source:govinfo-uscode-2024+owner-ruling-A63+stare-pub-cap |
| `statutes/find/fed_r_evid/1` | verified | verified-by-source:govinfo-uscode-2024+owner-ruling-A63 |
| `statutes/find/fed_r_crim_p/0` | verified | verified-by-source:govinfo-uscode-2024+owner-ruling-A63+stare-pub-cl |
| `statutes/find/fed_r_crim_p/1` | verified | verified-by-source:govinfo-uscode-2024+owner-ruling-A63 |
| `statutes/find/fed_r_app_p/0` | verified | verified-by-source:govinfo-uscode-2024+owner-ruling-A63 |
| `statutes/find/fed_r_app_p/1` | verified | verified-by-source:govinfo-uscode-2024+owner-ruling-A63 |
| `statutes/find/tex_r_p/0` | verified | verified-by-source:owner-ruling-A63+txcourts |
| `statutes/find/tex_r_p/1` | verified | verified-by-source:owner-ruling-A63+txcourts |
| `statutes/find/pa_r_civ_p/0` | verified | verified-by-source:owner-ruling-A63 |
| `statutes/find/mich_ct_r/0` | verified | verified-by-source:owner-ruling-A63 |
| `statutes/find/state_const/0` | verified | verified-by-source:owner-ruling-A63 |
| `statutes/find/state_const/1` | verified | verified-by-source:iga-constitution+owner-ruling-A63+stare-pub-cap |
| `statutes/find/state_const/2` | verified | verified-by-source:nmcc-nmonesource+owner-ruling-A63 |
| `statutes/find/nycrr/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes/find/njac/0` | verified | verified-by-source:cap-case-metadata+owner-ruling-A63+reporters-db@v3.2.67+stare-pub-cap |
| `statutes-proposed/find/fed_r_civ_p/0` | proposed | verified-by-source:govinfo-uscode-2024 |
| `statutes-proposed/find/fed_r_civ_p/1` | proposed | verified-by-source:govinfo-uscode-2024 |
| `statutes-proposed/find/fed_r_civ_p/2` | proposed | verified-by-source:govinfo-uscode-2024 |
| `statutes-proposed/find/us_const/0` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/1` | proposed | verified-by-source:gpo-constitution+stare-pub-cap |
| `statutes-proposed/find/us_const/2` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/us_const/3` | proposed | verified-by-source:gpo-constitution |
| `statutes-proposed/find/treas_reg/0` | proposed | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67 |
| `statutes-proposed/find/treas_reg/1` | proposed | verified-by-source:ecfr-2026-10-01+reporters-db@v3.2.67+stare-pub-cap |
| `statutes-proposed/find/ussg/0` | proposed | verified-by-source:ussc-guidelines-2025 |
| `statutes-proposed/find/ussg/1` | proposed | verified-by-source:ussc-guidelines-2025 |
| `statutes-proposed/find/fed_reg/0` | proposed | verified-by-source:govinfo-fr-link |
| `statutes-proposed/find/fed_reg/1` | proposed | verified-by-source:govinfo-fr-link |
| `statutes-proposed/find/stat/0` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/stat/1` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/pub_l/0` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67+stare-pub-cap |
| `statutes-proposed/find/pub_l/1` | proposed | verified-by-source:govinfo-statute+reporters-db@v3.2.67 |
| `statutes-proposed/find/usc_et_seq/0` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67+stare-pub-cap |
| `statutes-proposed/find/usc_et_seq/1` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67+stare-pub-cap |
| `statutes-proposed/find/usc_range/0` | proposed | verified-by-source:govinfo-uscode-2024+reporters-db@v3.2.67+stare-pub-cl |
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
| https://data.stare.pub/cap/a2d/432.zip#json/0419-01.json | 2026-10-25 | 33344 | `635d592f7830e357` |
| https://data.stare.pub/cap/a2d/799.zip#json/0931-01.json | 2026-10-25 | 28491 | `ac7b9c7aa5d5156c` |
| https://data.stare.pub/cap/a2d/923.zip#json/1244-01.json | 2026-10-25 | 15331 | `67ada1903f53ee0a` |
| https://data.stare.pub/cap/a3d/134.zip#json/1062-01.json | 2026-10-25 | 17106 | `501e849a9b35e06e` |
| https://data.stare.pub/cap/a3d/139.zip#json/0904-01.json | 2026-10-25 | 47135 | `a390a8e60b2f5e84` |
| https://data.stare.pub/cap/a3d/140.zip#json/1249-01.json | 2026-10-25 | 43185 | `b4816562ef9ce421` |
| https://data.stare.pub/cap/a3d/147.zip#json/0536-01.json | 2026-10-25 | 227449 | `fb4d52270db70d2e` |
| https://data.stare.pub/cap/ad2d/190.zip#json/0744-01.json | 2026-10-25 | 7156 | `db448e87b05f27db` |
| https://data.stare.pub/cap/ad3d/122.zip#json/1232-02.json | 2026-10-25 | 3150 | `e7b71fa899f95b4e` |
| https://data.stare.pub/cap/ad3d/43.zip#json/0632-01.json | 2026-10-25 | 3391 | `77861609aa579522` |
| https://data.stare.pub/cap/ariz/190.zip#json/0441-01.json | 2026-10-25 | 41197 | `1bcb8fca02ea6708` |
| https://data.stare.pub/cap/ariz/220.zip#json/0189-01.json | 2026-10-25 | 31695 | `37de4d3413b3bc0e` |
| https://data.stare.pub/cap/cal-4th/52.zip#json/0769-01.json | 2026-10-25 | 293419 | `e5d32f96c28e9983` |
| https://data.stare.pub/cap/cal-app-3d/125.zip#json/0220-01.json | 2026-10-25 | 17625 | `150be1115ed2401f` |
| https://data.stare.pub/cap/cal-app-3d/149.zip#json/0938-01.json | 2026-10-25 | 9071 | `8b653878273befd9` |
| https://data.stare.pub/cap/cal-app-4th/1.zip#json/1041-01.json | 2026-10-25 | 27310 | `c6b23ef8d78bf409` |
| https://data.stare.pub/cap/cal-app-4th/231.zip#json/1337-01.json | 2026-10-25 | 71772 | `9d0b6570fd7dec1f` |
| https://data.stare.pub/cap/cal-app-4th/7.zip#json/1450-01.json | 2026-10-25 | 16381 | `3580d905c3ac64c8` |
| https://data.stare.pub/cap/conn-app/116.zip#json/0112-01.json | 2026-10-25 | 86793 | `f167ddf30edaf33f` |
| https://data.stare.pub/cap/conn-app/116.zip#json/0758-01.json | 2026-10-25 | 55332 | `50143529fc423dfc` |
| https://data.stare.pub/cap/conn-app/128.zip#json/0425-01.json | 2026-10-25 | 60674 | `1c2618930b87a74b` |
| https://data.stare.pub/cap/conn/267.zip#json/0539-01.json | 2026-10-25 | 90479 | `13276cfb5dc64259` |
| https://data.stare.pub/cap/f-appx/665.zip#json/0082-01.json | 2026-10-25 | 13052 | `e2422c29f482483e` |
| https://data.stare.pub/cap/f-supp-2d/130.zip#json/0450-01.json | 2026-10-25 | 459811 | `24fb22f82574d7f7` |
| https://data.stare.pub/cap/f-supp-2d/333.zip#json/1344-01.json | 2026-10-25 | 32310 | `53436c4a0a821d51` |
| https://data.stare.pub/cap/f-supp-2d/60.zip#json/0566-01.json | 2026-10-25 | 39635 | `38c4c5ba24f44b20` |
| https://data.stare.pub/cap/f-supp/393.zip#json/0553-01.json | 2026-10-25 | 31579 | `050163bb07b4807a` |
| https://data.stare.pub/cap/f-supp/407.zip#json/1326-01.json | 2026-10-25 | 79306 | `0eba02b3a2a58719` |
| https://data.stare.pub/cap/f-supp/508.zip#json/0078-01.json | 2026-10-25 | 27936 | `c10e021ba469a3fb` |
| https://data.stare.pub/cap/f-supp/543.zip#json/1052-01.json | 2026-10-25 | 17942 | `1a5b14301b3d4e51` |
| https://data.stare.pub/cap/f-supp/742.zip#json/0544-01.json | 2026-10-25 | 20265 | `7d27981b6d411e11` |
| https://data.stare.pub/cap/f-supp/76.zip#json/0121-01.json | 2026-10-25 | 55772 | `cd88c586adc8f479` |
| https://data.stare.pub/cap/f-supp/791.zip#json/0014-01.json | 2026-10-25 | 22278 | `4d4594b5f5560a7e` |
| https://data.stare.pub/cap/f-supp/862.zip#json/0962-01.json | 2026-10-25 | 101657 | `8eaae31cdfee8bae` |
| https://data.stare.pub/cap/f-supp/969.zip#json/0397-01.json | 2026-10-25 | 26986 | `13e545afafabb7ba` |
| https://data.stare.pub/cap/f2d/292.zip#json/0645-01.json | 2026-10-25 | 21610 | `398b7a8d357c6070` |
| https://data.stare.pub/cap/f3d/594.zip#json/0832-01.json | 2026-10-25 | 54146 | `c30bfac5d43b2dbe` |
| https://data.stare.pub/cap/ga-app/306.zip#json/0689-01.json | 2026-10-25 | 18205 | `48b374cfcfe77abf` |
| https://data.stare.pub/cap/ga/258.zip#json/0856-01.json | 2026-10-25 | 22594 | `a9e4cd9dadf8ca1a` |
| https://data.stare.pub/cap/haw/118.zip#json/0001-01.json | 2026-10-25 | 72291 | `ee7b8d4adbee064d` |
| https://data.stare.pub/cap/haw/131.zip#json/0043-01.json | 2026-10-25 | 77599 | `e6c1883771d90d91` |
| https://data.stare.pub/cap/ill-app-3d/197.zip#json/0400-01.json | 2026-10-25 | 17027 | `683c2ad6c6ea898f` |
| https://data.stare.pub/cap/ind/256.zip#json/0058-01.json | 2026-10-25 | 14885 | `20c7750283417506` |
| https://data.stare.pub/cap/mass-app-ct/65.zip#json/0073-01.json | 2026-10-25 | 46148 | `124d7ce4e1bd6b21` |
| https://data.stare.pub/cap/mass/384.zip#json/0368-01.json | 2026-10-25 | 17858 | `a0ea1c2c635f35fc` |
| https://data.stare.pub/cap/misc2d/163.zip#json/0208-01.json | 2026-10-25 | 9204 | `5bf85ad1392ffcdc` |
| https://data.stare.pub/cap/misc3d/48.zip#json/0374-01.json | 2026-10-25 | 15593 | `a1336ecbaea1560d` |
| https://data.stare.pub/cap/misc3d/8.zip#json/0904-01.json | 2026-10-25 | 37871 | `cfa6ed50db1deec4` |
| https://data.stare.pub/cap/nc-app/201.zip#json/0146-01.json | 2026-10-25 | 21524 | `702e2ba023847ed4` |
| https://data.stare.pub/cap/nj-super/304.zip#json/0168-01.json | 2026-10-25 | 59179 | `8bffc8cad7e516a0` |
| https://data.stare.pub/cap/nm/128.zip#json/0618-01.json | 2026-10-25 | 44358 | `b8a80e756598dfa6` |
| https://data.stare.pub/cap/nm/137.zip#json/0589-01.json | 2026-10-25 | 47022 | `749f8a04973e9849` |
| https://data.stare.pub/cap/nw2d/891.zip#json/0760-01.json | 2026-10-25 | 24313 | `0ad4cae75b50b305` |
| https://data.stare.pub/cap/nw2d/932.zip#json/0893-01.json | 2026-10-25 | 17000 | `7a383028e0c65185` |
| https://data.stare.pub/cap/p2d/987.zip#json/1210-01.json | 2026-10-25 | 28567 | `2d27f527597ef8bc` |
| https://data.stare.pub/cap/p3d/383.zip#json/0773-01.json | 2026-10-25 | 39680 | `bb8f47650f7f7e24` |
| https://data.stare.pub/cap/pa-super/370.zip#json/0444-01.json | 2026-10-25 | 48618 | `f09e4b2854425583` |
| https://data.stare.pub/cap/ri/106.zip#json/0199-01.json | 2026-10-25 | 28952 | `d477548e61178a77` |
| https://data.stare.pub/cap/ri/113.zip#json/0232-01.json | 2026-10-25 | 34761 | `2bfd5a1d3be51ce8` |
| https://data.stare.pub/cap/se2d/805.zip#json/0751-01.json | 2026-10-25 | 42300 | `1095fe05a6313305` |
| https://data.stare.pub/cap/so3d/129.zip#json/0300-01.json | 2026-10-25 | 26112 | `9c4ba46f04035ea1` |
| https://data.stare.pub/cap/so3d/217.zip#json/0906-01.json | 2026-10-25 | 69965 | `2c101342a555ba98` |
| https://data.stare.pub/cap/sw2d/755.zip#json/0793-01.json | 2026-10-25 | 23690 | `9c33fde66993ffe4` |
| https://data.stare.pub/cap/sw3d/451.zip#json/0028-01.json | 2026-10-25 | 148577 | `ffce7165074f1406` |
| https://data.stare.pub/cap/vt/190.zip#json/0188-01.json | 2026-10-25 | 19012 | `0f59cce59b6ab42f` |
| https://data.stare.pub/cap/vt/199.zip#json/0019-01.json | 2026-10-25 | 147491 | `140e537cafba4aec` |
| https://data.stare.pub/cap/w-va/229.zip#json/0073-01.json | 2026-10-25 | 67881 | `0ef87d6622bc79e3` |
| https://data.stare.pub/cl/c/553757/c5a49c62b9762f75.json.gz | 2026-10-25 | 4458 | `9560b21835e2c669` |
| https://data.stare.pub/cl/c/8242608/b7d7acd3f7aa3474.json.gz | 2026-10-25 | 42303 | `7471c2d8d42df4f8` |
| https://docs.legis.wisconsin.gov/statutes/statutes/706/09 | 2026-10-18 | 95515 | `8184d1a627ddbd91` |
| https://downloads.leginfo.legislature.ca.gov/pubinfo_2025.zip#bytes=0-33554431 | 2026-10-25 | 33554432 | `fb48f8296ea37734` |
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
| https://legislature.vermont.gov/statutes/chapter/24/081 | 2026-10-25 | 58549 | `817360a5ac725111` |
| https://legislature.vermont.gov/statutes/chapter/24/115 | 2026-10-25 | 58428 | `a974cc321b9a6b1c` |
| https://legislature.vermont.gov/statutes/chapter/24/117 | 2026-10-25 | 79850 | `e1b287b5d3cf9666` |
| https://legislature.vermont.gov/statutes/chapter/24/118 | 2026-10-25 | 59150 | `d6112b5e6defd62e` |
| https://legislature.vermont.gov/statutes/chapter/24/120 | 2026-10-25 | 65646 | `adb88e9f936030b0` |
| https://legislature.vermont.gov/statutes/chapter/24/126 | 2026-10-25 | 60305 | `51a99311eeded352` |
| https://legislature.vermont.gov/statutes/title/24 | 2026-10-25 | 75304 | `97a3807228db8f07` |
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
| https://www.courtlistener.com/api/rest/v4/clusters/4566113/?fields=docket | 2026-10-20 | 71 | `0b9b3bcb2cd223b2` |
| https://www.courtlistener.com/api/rest/v4/courts/pasuperct/?fields=id,full_name,jurisdiction | 2026-10-20 | 83 | `c83ac545e1b8882e` |
| https://www.courtlistener.com/api/rest/v4/courts/tennctapp/?fields=id,full_name,jurisdiction | 2026-10-20 | 82 | `2c30dbafa6b06f5f` |
| https://www.courtlistener.com/api/rest/v4/dockets/232989/?fields=court_id | 2026-10-20 | 24 | `6ce974ba6bc70f63` |
| https://www.courtlistener.com/api/rest/v4/dockets/8217234/?fields=court_id | 2026-10-20 | 24 | `6094d139c64f7195` |
| https://www.courtlistener.com/api/rest/v4/opinions/1072657/?fields=cluster | 2026-10-20 | 73 | `fc0251c13087fae2` |
| https://www.courtlistener.com/api/rest/v4/opinions/4343366/?fields=cluster | 2026-10-20 | 73 | `0897d287bdb3238e` |
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
