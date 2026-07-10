# Stage 1 — Data Intake Manifest

## MGEX static stations

Broadcast nav files present for day(s): [('2023', '344'), ('2023', '352')]

- **JFNG** day 344/2023: OK — systems present: ['C', 'E', 'G', 'J', 'L2X', 'L6I', 'L7X', 'R', 'S', 'S1P']
- **JFNG** day 352/2023: OK — systems present: ['C', 'E', 'G', 'J', 'L2X', 'R', 'S', 'S1P', 'S1X']
- **URUM** day 344/2023: OK — systems present: ['C', 'D7I', 'E', 'G', 'I', 'J', 'L1W', 'L2P', 'L7X', 'R', 'S', 'S1X', 'S5X']
- **URUM** day 352/2023: OK — systems present: ['C', 'D7I', 'E', 'G', 'I', 'J', 'L1W', 'L2P', 'L7X', 'R', 'S', 'S1X', 'S5X']
- **HKWS** day 352/2023: OK — systems present: ['C', 'E', 'G', 'J', 'L5Q', 'L8Q', 'R']

Station truth-coordinate source found in data/external/: ['mgex_station_truth_coordinates.csv']

## UrbanNav kinematic sequences

### tunnel_1
- nav: ['BRDC00IGS_R_20211380000_01D_MN.rnx']
- ground truth: UrbanNav_tunnel_GT_raw.txt (401 data rows)
- receiver logs found (10):
  - `20210518.tunnel.cht.google.pixel4.obs` — systems ['E', 'G', 'J', 'R'] — **no BeiDou**
  - `20210518.tunnel.cht.huawei.p40pro.obs` — systems ['C', 'E', 'G', 'J', 'R'] — **has BeiDou (C)**
  - `20210518.tunnel.cht.novatel.flexpak6.obs` — systems ['C', 'G', 'R'] — **has BeiDou (C)**
  - `20210518.tunnel.cht.samsung.note8.obs` — systems ['C', 'G', 'R'] — **has BeiDou (C)**
  - `20210518.tunnel.cht.ublox.f9p.obs` — systems ['C', 'E', 'G', 'J', 'R', 'S'] — **has BeiDou (C)**
  - `20210518.tunnel.cht.ublox.f9p.splitter.obs` — systems ['C', 'E', 'G', 'J', 'R', 'S'] — **has BeiDou (C)**
  - `20210518.tunnel.cht.ublox.m8t.GC.obs` — systems ['C', 'G'] — **has BeiDou (C)**
  - `20210518.tunnel.cht.ublox.m8t.GEJ.obs` — systems ['E', 'G', 'J'] — **no BeiDou**
  - `20210518.tunnel.cht.ublox.m8t.GRJ.obs` — systems ['G', 'J', 'R'] — **no BeiDou**
  - `20210518.tunnel.cht.xiaomi.mi8.obs` — systems ['G', 'J', 'R'] — **no BeiDou**

### deep_urban_1
- nav: ['BRDC00IGS_R_20211410000_01D_MN.rnx']
- ground truth: UrbanNav_whampoa_raw.txt (1539 data rows)
- receiver logs found (10):
  - `UrbanNav-HK-Deep-Urban-1.google.pixel4.obs` — systems ['E', 'G', 'J', 'R'] — **no BeiDou**
  - `UrbanNav-HK-Deep-Urban-1.huawei.p40pro.obs` — systems ['C', 'E', 'G', 'J', 'R'] — **has BeiDou (C)**
  - `UrbanNav-HK-Deep-Urban-1.novatel.flexpak6.obs` — systems ['C', 'G', 'R'] — **has BeiDou (C)**
  - `UrbanNav-HK-Deep-Urban-1.samsung.note8.obs` — systems ['C', 'G', 'R'] — **has BeiDou (C)**
  - `UrbanNav-HK-Deep-Urban-1.ublox.f9p.obs` — systems ['C', 'E', 'G', 'J', 'R', 'S'] — **has BeiDou (C)**
  - `UrbanNav-HK-Deep-Urban-1.ublox.f9p.splitter.obs` — systems ['C', 'E', 'G', 'J', 'R', 'S'] — **has BeiDou (C)**
  - `UrbanNav-HK-Deep-Urban-1.ublox.m8t.GC.obs` — systems ['C', 'G'] — **has BeiDou (C)**
  - `UrbanNav-HK-Deep-Urban-1.ublox.m8t.GEJ.obs` — systems ['E', 'G', 'J'] — **no BeiDou**
  - `UrbanNav-HK-Deep-Urban-1.ublox.m8t.GRJ.obs` — systems ['G', 'J', 'R'] — **no BeiDou**
  - `UrbanNav-HK-Deep-Urban-1.xiaomi.mi8.obs` — systems ['G', 'J', 'R'] — **no BeiDou**

**OPEN DECISION — not resolvable by inspection alone:** several receiver logs exist per sequence, and more than one contains BeiDou observations (see flags above). This project needs exactly one designated as "the robot's receiver" for BDS-only SPP processing — which one is a project decision, not a data fact.