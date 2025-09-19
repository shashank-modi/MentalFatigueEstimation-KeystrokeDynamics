# Mental Fatigue Estimation

A **content-safe monitoring system** that estimates mental fatigue using keyboard and mouse interaction patterns.  
This project captures raw interaction data, computes behavioral features, collects self-reported fatigue labels, and trains machine learning models to estimate fatigue levels.

---

##  Features
- **Event Logger**: Captures keystrokes & mouse events (contentless, privacy-preserving).  
- **Windowing**: Slices events into fixed 1-minute windows.  
- **Feature Engineering**: Extracts typing dynamics (IKI, backspace rate), mouse dynamics (speed, jerk), idle ratios, and time-of-day.  
- **Label Collection**: Tkinter popup prompts user fatigue score (1–5) at fixed intervals.  
- **Dataset Builder**: Combines features & labels into supervised datasets.  
- **Model Training**: Trains a Random Forest baseline (supports LightGBM/other ML models).  
- **Prediction**: Loads latest model and predicts fatigue score for new data.  

---

##  Project Structure
```
MentalFatigueEstimation/
├── src/
│   ├── collector/       # event capture
│   ├── features/        # windowing, feature computation, postprocess
│   ├── labeling/        # fatigue label scheduler
│   ├── model/           # train + predict scripts
│   ├── utils/           # helpers (time, io, config)
│   └── app.py           # combined runner
├── config/              # yaml configs
├── data/                # (ignored in git) raw events, labels, features, datasets
├── models/              # (ignored in git) saved ML models
├── requirements.txt     # dependencies
└── README.md            # project docs
```
---

##  Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/MentalFatigueEstimation.git
cd MentalFatigueEstimation

2. Setup environment

python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

pip install -r requirements.txt

3. Run event logger

python -m src.collector.eventcapture

(macOS users: grant Accessibility permissions for keyboard/mouse capture.)

4. Start fatigue labeling popup

python -m src.labeling.gui_scheduler

5. Compute features & dataset

python -m src.features.make_features
python -m src.features.dataset_builder

6. Train model

python -m src.model.train

7. Predict on latest data

python -m src.model.predict
```

⸻

 Example Output

[train] Saved model to models/2025-09-15T12-45-32_rf
[train] Test MAE: 0.36
[train] Features used (15): ['keys_total','backspace','avg_iki',...]


⸻

� Privacy
	•	No actual keystrokes or text are stored.
	•	Only timing and dynamics (IKI, corrections, idle time, mouse movement) are logged.

⸻

�️ Tech Stack
	•	Python (pandas, numpy, scikit-learn, LightGBM)
	•	pynput (event capture)
	•	Tkinter (label collection GUI)
	•	Joblib (model persistence)

⸻

 Future Work
	•	Support real-time fatigue prediction.
	•	Explore deep learning models (LSTMs, Transformers).
	•	Add visual dashboards for monitoring.
	•	Collect larger datasets for validation.
