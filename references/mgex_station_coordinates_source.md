# MGEX station truth-coordinate source

`data/external/mgex_station_truth_coordinates.csv` holds each station's approximate ECEF position (ITRF, meters), taken directly from the station's official IGS site log's "Approximate Position" section — not derived or estimated. Used as ground truth to compute RTKLIB BDS-only SPP horizontal/vertical error in Stage 2.

- JFNG (Jiufeng, Hubei, China): https://files.igs.org/pub/station/log/jfng00chn_20231211.log
- URUM (Urumqi, China): https://files.igs.org/pub/station/log/urum00chn_20230119.log
- HKWS (Wong Shek, Hong Kong): https://files.igs.org/pub/station/log/hkws00hkg_20240417.log

Precision note: site-log "Approximate Position" values are typically accurate to within a few meters — sufficient for this project (SPP error at meter-scale, thresholds T = 2/5/10 m), but not survey-grade (mm-level ITRF solutions would need a full multi-year IGS combined solution instead, which wasn't necessary here per the "look it up" scope decision).
