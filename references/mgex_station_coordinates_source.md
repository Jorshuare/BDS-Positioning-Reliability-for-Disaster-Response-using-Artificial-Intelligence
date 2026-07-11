# MGEX station truth-coordinate source

`data/external/mgex_station_truth_coordinates.csv` holds each station's approximate ECEF position (ITRF, meters), taken directly from the station's official IGS site log's "Approximate Position" section — not derived or estimated. Used as ground truth to compute RTKLIB BDS-only SPP horizontal/vertical error in Stage 2.

- JFNG (Jiufeng, Hubei, China): https://files.igs.org/pub/station/log/jfng00chn_20231211.log
- URUM (Urumqi, China): https://files.igs.org/pub/station/log/urum00chn_20230119.log
- HKWS (Wong Shek, Hong Kong): https://files.igs.org/pub/station/log/hkws00hkg_20240417.log

**What this is, precisely — and what it is not.** These are the station operator's self-reported "Approximate Position" field from the IGS site log, not a rigorously estimated multi-year ITRF combination solution. That distinction matters and shouldn't be blurred in the paper: call it "IGS site-log reference position," not "surveyed ITRF coordinate" or "ground truth" without qualification.

**Independent cross-check (2026-07-11):** an independently-obtained copy of this same file was provided and found byte-for-byte identical to the one already in use — the same three coordinate triplets, same source URLs. That's a genuine corroboration (two independent lookups converged on the same numbers), but it does not raise precision — both derivations read the same underlying site-log field, so this is not evidence of survey-grade accuracy, just evidence the site-log value was transcribed correctly.

**Investigated whether a tighter (genuinely independent, multi-year ITRF) solution was readily available, and it wasn't:** checked two IGS-published SINEX products (`igs.snx`, and a search for `igs2020.snx`) that looked like candidates for a proper ITRF2020-aligned combination solution. Both turned out to be generated directly from current IGS site logs ("`SLM2SNX`... generated daily from all current IGS site logs"), not from an independent multi-year GNSS processing combination — so they would only restate the same approximate value, not tighten it. A genuine mm-level ITRF2020 solution likely exists for these three long-standing stations (via the actual IGS reprocessing-campaign combined SINEX, or the ITRF website's interactive per-station query tool), but isn't reliably extractable by automated search/fetch — it would need to be sourced manually and substituted in if warranted.

**Precision and where it matters for this project:** site-log approximate positions are commonly good to within a few meters, not mm-level. Given this project's thresholds (T = 2, 5, 10 m), this is an acceptable, deliberate scope choice for T = 5 m and T = 10 m — but at **T = 2 m specifically, a several-meter truth-coordinate uncertainty is not negligible relative to the threshold itself**. Labels near the T = 2 m boundary should be read with that caveat explicitly stated in the paper, rather than treated as equally reliable as the 5 m/10 m results.
