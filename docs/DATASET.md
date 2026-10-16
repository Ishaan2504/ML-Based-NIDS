# CIC-IDS2017 Dataset Documentation

## Provenance & Attribution

- **Dataset**: Canadian Institute for Cybersecurity Intrusion Detection Dataset (CIC-IDS2017)
- **Institution**: University of New Brunswick (UNB), Canadian Institute for Cybersecurity (CIC)
- **Original Citation**:
  ```bibtex
  @inproceedings{sharafaldin2018toward,
    title={Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization},
    author={Sharafaldin, Iman and Lashkari, Arash Habibi and Ghorbani, Ali A.},
    booktitle={Proceedings of the 4th International Conference on Information Systems Security and Privacy (ICISSP)},
    pages={108--116},
    year={2018},
    organization={SCITEPRESS}
  }
  ```

## Capture Schedule & Traffic Breakdown

The CIC-IDS2017 dataset was captured over a 5-day period in July 2017 in an isolated emulation environment:

| Capture Day | File Name | Attack Classes Injected | Primary Threat Family |
|---|---|---|---|
| **Monday** | `Monday-WorkingHours.pcap_ISCX.csv` | Normal benign traffic only | BENIGN |
| **Tuesday** | `Tuesday-WorkingHours.pcap_ISCX.csv` | FTP-Patator, SSH-Patator | Brute Force |
| **Wednesday** | `Wednesday-workingHours.pcap_ISCX.csv` | DoS GoldenEye, DoS Slowloris, DoS Slowhttptest, DoS Hulk, Heartbleed | DoS / DDoS |
| **Thursday Morning** | `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv` | Web Attack – Brute Force, Web Attack – XSS, Web Attack – Sql Injection | Web Attacks |
| **Thursday Afternoon** | `Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv` | Infiltration (MetaSploit exploit, privilege escalation) | Infiltration |
| **Friday Morning** | `Friday-WorkingHours-Morning.pcap_ISCX.csv` | Botnet ARES | Botnet |
| **Friday Afternoon (1)** | `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv` | PortScan | PortScan / Recon |
| **Friday Afternoon (2)** | `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` | DDoS LOIT | DoS / DDoS |

## Statistical Flow Features (CICFlowMeter)

The network traffic is summarized into bidirectional network flow statistics (80+ columns) including:
- **Identification & Addressing**: Source IP, Destination IP, Source Port, Destination Port, Protocol, Timestamp
- **Flow Dynamics**: Flow Duration, Total Forward Packets, Total Backward Packets, Total Length of Fwd/Bwd Packets
- **Packet Length Distribution**: Mean, Standard Deviation, Max, Min of Forward and Backward Packet Lengths
- **Inter-Arrival Times (IAT)**: Flow IAT Mean, Flow IAT Std, Flow IAT Max, Fwd/Bwd IAT distributions
- **Protocol Flags**: FIN, SYN, RST, PSH, ACK, URG, CWE, ECE flag counts
- **Bandwidth & Rate**: Flow Bytes/s, Flow Packets/s

## Usage Terms & Privacy

- Dataset files are intended strictly for cybersecurity research and education.
- Raw CSV files are excluded from git version control via `.gitignore`.
- Analysts must download data directly from the official UNB portal and adhere to UNB CIC licensing terms.
