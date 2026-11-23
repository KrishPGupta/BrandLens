import { useBrand } from "../../context/BrandContext";
import { API_URL } from "../../config/site";
import { useFetch } from "../../lib/api";
import AiSummary from "../../components/dashboard/AiSummary";
import Panel from "../../components/dashboard/Panel";
import { ErrorNote, Loading, PageHeader } from "../../components/dashboard/States";

const NAMES = { tfidf_lr: "TF-IDF + Logistic Regression (baseline)", distilbert: "DistilBERT (fine-tuned)" };
const METRICS = [
  ["accuracy", "Accuracy"],
  ["precision_macro", "Precision"],
  ["recall_macro", "Recall"],
  ["f1_macro", "F1 score"],
];

export default function ModelsPage() {
  const { brand } = useBrand();
  const { data, error, loading } = useFetch("/api/models/metrics");
  const models = (data?.models ?? []).filter((m) => !m.model.endsWith("_val"));

  return (
    <>
      <PageHeader
        eyebrow="Models"
        title="How reliable are the sentiment models?"
        description="Two models label every post. These scores come from posts the models never saw during training."
      />

      {brand && <AiSummary brand={brand} focus="models" />}

      {error && <ErrorNote message={error} />}
      {loading && <Loading>Loading model scores…</Loading>}

      {models.length > 0 && (
        <div className="space-y-6">
          <div className="grid gap-5 lg:grid-cols-2">
            {models.map((m) => (
              <Panel key={m.model} label={NAMES[m.model] ?? m.model}>
                <ul className="space-y-3">
                  {METRICS.map(([key, label]) => (
                    <li key={key}>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate">{label}</span>
                        <span className="text-ink-950">{(m[key] * 100).toFixed(1)}%</span>
                      </div>
                      <div className="mt-1 h-2 rounded-full bg-paper-line/60">
                        <div className="h-2 rounded-full bg-ink-900" style={{ width: `${m[key] * 100}%` }} />
                      </div>
                    </li>
                  ))}
                </ul>
                {m.confusion_matrix_url && (
                  <figure className="mt-5">
                    <img src={`${API_URL}${m.confusion_matrix_url}`} alt={`Confusion matrix for ${NAMES[m.model] ?? m.model}`} className="mx-auto w-full max-w-xs rounded bg-white" />
                    <figcaption className="mt-2 text-center text-xs text-slate">Rows are the true label, columns what the model predicted.</figcaption>
                  </figure>
                )}
              </Panel>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
