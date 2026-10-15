# Architecture

Planned data flow: manually supplied CIC-IDS2017 CSV files are inspected, validated, cleaned, and split by contiguous source-file blocks. Training-only preprocessing feeds model training. Validation data selects the model and operating threshold. After the selected model is frozen, the test set is used for final reporting. A shared serialized preprocessing/model bundle serves the FastAPI API and the Streamlit dashboard. Uploaded analyses and replay runs are stored locally under `data/runs/`.

Implementation and the Mermaid architecture diagram will be added as the corresponding roadmap phases are completed.
