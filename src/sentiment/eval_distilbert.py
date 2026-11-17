"""After copying the Colab model into models/distilbert, evaluate it on the same test split."""
import pandas as pd
from src.config import load_config, resolve
from src.sentiment.evaluate import report
from src.sentiment.predict import predict
from src.storage import db

cfg = load_config()
test = pd.read_csv(resolve(cfg, "processed") / "test.csv")
pred = predict(test["text"], "distilbert", cfg)
report(test["label"], pred["label"], "distilbert", cfg=cfg)
db.save_metrics(pd.read_csv(resolve(cfg, "reports") / "results.csv"), cfg)
print("saved to results.csv and SQLite")
