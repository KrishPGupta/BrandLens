"""Fine-tune DistilBERT. Meant for a Colab GPU:
   python src/sentiment/distilbert_finetune.py --data data/processed --out distilbert"""
import argparse
import json
import os
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

LABELS = ["negative", "neutral", "positive"]
L2I = {l: i for i, l in enumerate(LABELS)}
NAME = "distilbert-base-uncased"


def _device():
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def _tensors(df, tok, max_len=64):
    enc = tok(df["text_clean"].fillna("").tolist(), truncation=True, max_length=max_len,
              padding="max_length", return_tensors="pt")
    y = torch.tensor(df["label"].map(L2I).values)
    return TensorDataset(enc["input_ids"], enc["attention_mask"], y)


@torch.no_grad()
def _evaluate(model, loader, dev):
    model.eval()
    preds, ys = [], []
    for ids, mask, y in loader:
        logits = model(input_ids=ids.to(dev), attention_mask=mask.to(dev)).logits
        preds += logits.argmax(-1).cpu().tolist()
        ys += y.tolist()
    return np.array(ys), np.array(preds)


def fine_tune(data_dir, out_dir, epochs=2, bs=32, lr=3e-5, seed=42):
    torch.manual_seed(seed)
    dev = _device()
    print("device:", dev)
    tok = AutoTokenizer.from_pretrained(NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        NAME, num_labels=3, id2label=dict(enumerate(LABELS)), label2id=L2I).to(dev)

    tr, va, te = (pd.read_csv(os.path.join(data_dir, f"{n}.csv")) for n in ["train", "val", "test"])
    dl_tr = DataLoader(_tensors(tr, tok), batch_size=bs, shuffle=True)
    dl_va = DataLoader(_tensors(va, tok), batch_size=128)
    dl_te = DataLoader(_tensors(te, tok), batch_size=128)

    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total = epochs * len(dl_tr)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * total), total)

    for ep in range(epochs):
        model.train()
        for step, (ids, mask, y) in enumerate(dl_tr):
            loss = model(input_ids=ids.to(dev), attention_mask=mask.to(dev), labels=y.to(dev)).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
            if step % 100 == 0:
                print(f"epoch {ep + 1} step {step}/{len(dl_tr)} loss {loss.item():.4f}")
        yv, pv = _evaluate(model, dl_va, dev)
        print(f"epoch {ep + 1}: val acc={accuracy_score(yv, pv):.4f} macro-F1={f1_score(yv, pv, average='macro'):.4f}")

    yt, pt = _evaluate(model, dl_te, dev)
    print("\nTEST\n", classification_report(yt, pt, target_names=LABELS))
    save(model, tok, out_dir, {"test_accuracy": float(accuracy_score(yt, pt)),
                               "test_macro_f1": float(f1_score(yt, pt, average="macro"))})


def save(model, tok, out_dir, metrics):
    os.makedirs(out_dir, exist_ok=True)
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed")
    ap.add_argument("--out", default="models/distilbert")
    ap.add_argument("--epochs", type=int, default=2)
    a = ap.parse_args()
    fine_tune(a.data, a.out, epochs=a.epochs)
