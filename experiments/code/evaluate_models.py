import argparse
import csv
import json
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import pm4py
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from app.services.trace_builder import build_traces_from_pm4py_log
from app.services.trace_context_inferer import TraceContextInferer
from app.services.activity_classifier import ActivityClassifier
from app.services.ai.roberta_trace_context_inferer import RobertaTraceContextInferer
from app.services.ai.roberta_activity_classifier import RobertaActivityClassifier
from app.specifications.activity_types import ActivityType
from app.specifications.data_categories import DataCategory
from generate_pdf_report import generate_pdf_report


DATASETS = {
    "sepsis": {
        "path_candidates": [
            "Sepsis Cases - Event Log.xes.gz",
            "Sepsis Cases - Event Log.xes/Sepsis Cases - Event Log.xes",
        ],
        "context_truth": {
            "purpose": "medical treatment",
            "legal_basis": "legal_obligation",
            "data_category": "health",
            "data_subject_type": "patient",
            "processing_operation": "medical treatment",
            "retention_period": "legal_requirement",
            "processing_domain": "healthcare",
            "has_third_party_recipients": "false",
            "international_transfer": "none",
            "transfer_safeguard": "none",
            "consent_status": "not_needed",
        },
        "activity_truth": {
            "ER Registration": "DATA_COLLECTION",
            "ER Triage": "DATA_PROCESSING",
            "ER Sepsis Triage": "DATA_PROCESSING",
            "CRP": "DATA_PROCESSING",
            "Leucocytes": "DATA_PROCESSING",
            "LacticAcid": "DATA_PROCESSING",
            "IV Antibiotics": "DATA_PROCESSING",
            "IV Liquid": "DATA_PROCESSING",
            "Admission IC": "DATA_PROCESSING",
            "Admission NC": "DATA_PROCESSING",
            "Return ER": "DATA_PROCESSING",
            "Release A": "STORAGE_MANAGEMENT",
            "Release B": "STORAGE_MANAGEMENT",
            "Release C": "STORAGE_MANAGEMENT",
            "Release D": "STORAGE_MANAGEMENT",
            "Release E": "STORAGE_MANAGEMENT",
        },
    },
    "bpi2017": {
        "path_candidates": [
            "BPI Challenge 2017.xes.gz",
        ],
        "context_truth": {
            "purpose": "contract execution",
            "legal_basis": "contract",
            "data_category": "standard",
            "data_subject_type": "customer",
            "processing_operation": "contract execution",
            "retention_period": "indefinite",
            "processing_domain": "banking",
            "has_third_party_recipients": "false",
            "international_transfer": "none",
            "transfer_safeguard": "none",
            "consent_status": "not_needed",
        },
        "activity_truth": {
            "A_Create Application": "DATA_COLLECTION",
            "A_Submitted": "DATA_COLLECTION",
            "W_Handle leads": "DATA_PROCESSING",
            "W_Complete application": "DATA_PROCESSING",
            "A_Concept": "AUTOMATED_DECISION",
            "A_Accepted": "AUTOMATED_DECISION",
            "O_Create Offer": "AUTOMATED_DECISION",
            "O_Created": "AUTOMATED_DECISION",
            "O_Sent (mail and online)": "DATA_TRANSFER",
            "O_Sent (online only)": "DATA_TRANSFER",
            "W_Call after offers": "DATA_PROCESSING",
            "A_Complete": "STORAGE_MANAGEMENT",
            "W_Validate application": "DATA_PROCESSING",
            "A_Validating": "DATA_PROCESSING",
            "O_Returned": "DATA_PROCESSING",
            "W_Call incomplete files": "DATA_PROCESSING",
            "A_Incomplete": "DATA_PROCESSING",
            "O_Accepted": "AUTOMATED_DECISION",
            "A_Pending": "STORAGE_MANAGEMENT",
            "A_Denied": "AUTOMATED_DECISION",
            "A_Cancelled": "STORAGE_MANAGEMENT",
        },
    },
}

CONTEXT_FIELDS = [
    "purpose",
    "legal_basis",
    "data_category",
    "data_subject_type",
    "processing_operation",
    "retention_period",
    "processing_domain",
    "has_third_party_recipients",
    "international_transfer",
    "transfer_safeguard",
    "consent_status",
]

CONTEXT_IMPACT_LABELS = [
    "0_COMPLIANT",
    "1_VIOLATION",
    "2_WARNING",
]

CRITICAL_CONTEXT_FIELDS = {
    "legal_basis",
    "data_category",
    "data_subject_type",
    "processing_domain",
    "has_third_party_recipients",
    "international_transfer",
}

CONTEXT_ACCEPTABLE_KEYWORDS = {
    "medical_treatment": [
        "medical",
        "health",
        "healthcare",
        "hospital",
        "clinical",
        "patient",
        "treatment",
        "sepsis",
    ],
    "contract_execution": [
        "contract",
        "loan",
        "credit",
        "application",
        "offer",
        "banking",
        "financial",
        "service_delivery",
    ],
    "legal_obligation": [
        "legal_obligation",
        "legal",
        "obligation",
        "compliance",
        "required_by_law",
        "regulation",
    ],
    "contract": [
        "contract",
        "loan",
        "credit",
        "application",
        "customer",
        "banking",
    ],
    "health": [
        "health",
        "medical",
        "clinical",
        "hospital",
        "patient",
        "special_categories",
        "special_category",
        "sepsis",
    ],
    "standard": [
        "standard",
        "personal",
        "customer",
        "applicant",
        "financial",
        "banking",
    ],
    "patient": [
        "patient",
        "data_subject",
        "individual",
        "person",
    ],
    "customer": [
        "customer",
        "client",
        "applicant",
        "borrower",
        "data_subject",
    ],
    "legal_requirement": [
        "legal_requirement",
        "required_by_law",
        "regulation",
        "compliance",
        "healthcare",
        "medical",
    ],
    "indefinite": [
        "indefinite",
        "necessary",
        "as_long_as_necessary",
        "retained",
        "business_need",
    ],
    "healthcare": [
        "healthcare",
        "health",
        "medical",
        "hospital",
        "clinical",
        "patient",
        "sepsis",
    ],
    "banking": [
        "banking",
        "bank",
        "financial",
        "finance",
        "loan",
        "credit",
        "lending",
    ],
    "false": [
        "false",
        "no",
        "none",
        "not_applicable",
        "not_needed",
    ],
    "none": [
        "none",
        "no",
        "not_applicable",
        "not_needed",
        "no_transfer",
        "no_safeguard",
    ],
    "not_needed": [
        "not_needed",
        "not_required",
        "none",
        "no",
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate Phi-3 vs RoBERTa for GDPR context inference and ActivityType classification."
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help=(
            "Directory containing the real XES datasets. "
            "If omitted, the script tries app/data/input and then data/input."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "experiments" / "results"),
        help="Directory where metrics, reports and figures will be written.",
    )
    parser.add_argument(
        "--max-traces",
        type=int,
        default=250,
        help="Maximum traces per dataset. Use 0 to process the complete logs.",
    )
    parser.add_argument(
        "--skip-phi3",
        action="store_true",
        help="Skip Phi-3/Ollama execution and evaluate only RoBERTa.",
    )
    return parser.parse_args()


def resolve_dataset_path(input_dir, dataset_config):
    input_dir = Path(input_dir)

    for candidate in dataset_config["path_candidates"]:
        path = input_dir / candidate
        if path.exists():
            return path

    tried = [str(input_dir / candidate) for candidate in dataset_config["path_candidates"]]
    raise FileNotFoundError("Dataset not found. Tried: " + "; ".join(tried))


def resolve_input_dir(input_dir):
    if input_dir:
        return Path(input_dir)

    candidates = [
        ROOT / "app" / "data" / "input",
        ROOT / "data" / "input",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    tried = "; ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"No input data directory found. Tried: {tried}")


def load_traces(path, max_traces):
    log = pm4py.read_xes(str(path))

    if hasattr(log, "columns"):
        log = pm4py.convert_to_event_log(log)

    if max_traces and max_traces > 0:
        log = log[:max_traces]

    return build_traces_from_pm4py_log(log)


def build_activity_profiles(traces):
    activity_attrs = defaultdict(Counter)
    activity_counter = Counter()

    for trace in traces:
        for event in trace.events:
            activity_counter[event.name] += 1

            for key in getattr(event, "attributes", {}) or {}:
                activity_attrs[event.name][key] += 1

    profiles = []

    for activity_name, total in activity_counter.items():
        attrs = activity_attrs.get(activity_name, Counter())
        filtered = {
            attr: count
            for attr, count in attrs.items()
            if total and (count / total) >= 0.5
        }

        if not filtered:
            filtered = dict(attrs.most_common(5))

        profiles.append({
            "name": activity_name,
            "example_attributes": filtered,
        })

    return profiles


def normalize_value(value):
    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, DataCategory):
        return value.value

    if isinstance(value, ActivityType):
        return value.name

    if hasattr(value, "value") and not isinstance(value, str):
        return str(value.value).lower()

    if value is None:
        return "none"

    text = str(value).strip().lower()
    text = text.replace("datacategory.", "")
    text = text.replace(" ", "_")

    aliases = {
        "legal_obligation": "legal_obligation",
        "legal obligation": "legal_obligation",
        "health_data": "health",
        "standard_personal_data": "standard",
        "healthcare": "healthcare",
        "medical_treatment": "medical_treatment",
        "contract_execution": "contract_execution",
    }

    return aliases.get(text, text)


def text_contains_keyword(text, keywords):
    comparable = f" {text.replace('_', ' ')} {text} "

    for keyword in keywords:
        normalized_keyword = normalize_value(keyword)
        expanded_keyword = normalized_keyword.replace("_", " ")

        if normalized_keyword in text or expanded_keyword in comparable:
            return True

    return False


def context_prediction_matches(expected, predicted):
    expected_norm = normalize_value(expected)
    predicted_norm = normalize_value(predicted)

    if expected_norm == predicted_norm:
        return True

    keywords = CONTEXT_ACCEPTABLE_KEYWORDS.get(expected_norm, [])
    return text_contains_keyword(predicted_norm, keywords)


def context_impact_label(field, expected, predicted):
    predicted_norm = normalize_value(predicted)

    if context_prediction_matches(expected, predicted):
        return "0_COMPLIANT"

    if predicted_norm in {"__error__", "__ERROR__", "", "unknown"}:
        return "1_VIOLATION"

    if field in CRITICAL_CONTEXT_FIELDS:
        return "1_VIOLATION"

    return "2_WARNING"


def acceptable_context_values(expected):
    expected_norm = normalize_value(expected)
    keywords = CONTEXT_ACCEPTABLE_KEYWORDS.get(expected_norm, [])
    values = [expected_norm] + [
        keyword
        for keyword in keywords
        if keyword != expected_norm
    ]

    return " | ".join(values)


def normalize_activity_prediction(info):
    if isinstance(info, dict):
        value = info.get("activity_type")
    else:
        value = info

    if isinstance(value, ActivityType):
        return value.name

    if isinstance(value, str):
        value = value.strip()
        if value in ActivityType.__members__:
            return value
        upper = value.upper()
        if upper in ActivityType.__members__:
            return upper

    return "OTHER"


def context_to_dict(context):
    return {
        field: normalize_value(getattr(context, field, None))
        for field in CONTEXT_FIELDS
    }


def run_context_model(model_name, traces):
    if model_name == "roberta":
        return RobertaTraceContextInferer.infer_dataset_context(traces)

    if model_name == "phi3":
        return TraceContextInferer.infer_dataset_context_with_phi3(traces)

    raise ValueError(f"Unknown context model: {model_name}")


def run_activity_model(model_name, activity_profiles, context_text):
    if model_name == "roberta":
        return RobertaActivityClassifier.classify(activity_profiles, context_text)

    if model_name == "phi3":
        return ActivityClassifier.classify_with_phi3(activity_profiles, context_text)

    raise ValueError(f"Unknown activity model: {model_name}")


def safe_run(callable_, error_label):
    try:
        return callable_(), None
    except Exception as exc:
        return None, {
            "label": error_label,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


def compute_metrics(y_true, y_pred, labels):
    accuracy = accuracy_score(y_true, y_pred)
    macro = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    weighted = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="weighted", zero_division=0
    )
    micro = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="micro", zero_division=0
    )

    return {
        "accuracy": accuracy,
        "precision_macro": macro[0],
        "recall_macro": macro[1],
        "f1_macro": macro[2],
        "precision_micro": micro[0],
        "recall_micro": micro[1],
        "f1_micro": micro[2],
        "precision_weighted": weighted[0],
        "recall_weighted": weighted[1],
        "f1_weighted": weighted[2],
    }


def save_confusion_matrix(y_true, y_pred, labels, title, output_path):
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    width = max(8, len(labels) * 0.8)
    height = max(6, len(labels) * 0.7)

    plt.figure(figsize=(width, height))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("Ground truth")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def save_metrics_barplot(metrics_rows, task, output_path):
    selected = [row for row in metrics_rows if row["task"] == task]
    metrics = ["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    metric_labels = ["Accuracy", "Precision\nmacro", "Recall\nmacro", "F1-score\nmacro"]
    x = list(range(len(metrics)))
    models = sorted({row["model"] for row in selected})
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    for index, model in enumerate(models):
        row = next(item for item in selected if item["model"] == model)
        offset = (index - (len(models) - 1) / 2) * width
        bars = ax.bar(
            [value + offset for value in x],
            [row[metric] for metric in metrics],
            width=width,
            label=model,
        )
        ax.bar_label(
            bars,
            labels=[f"{row[metric]:.2f}" for metric in metrics],
            padding=3,
            fontsize=11,
            fontweight="bold",
        )

    title = "ActivityType metrics comparison" if task == "activity_type" else "Context metrics comparison"
    ax.set_title(title, fontsize=18, fontweight="bold", pad=14)
    ax.set_xlabel("Metric", fontsize=15, fontweight="bold", labelpad=10)
    ax.set_ylabel("Score", fontsize=15, fontweight="bold", labelpad=8)
    ax.set_ylim(0, 1.12)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, rotation=15, ha="right", fontsize=13, fontweight="bold")
    ax.tick_params(axis="y", labelsize=13)
    for tick in ax.get_yticklabels():
        tick.set_fontweight("bold")
    ax.legend(
        fontsize=13,
        frameon=True,
        loc="lower right",
        borderaxespad=0.8,
    )
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.35)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evaluate(args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = resolve_input_dir(args.input_dir)

    models = ["roberta"] if args.skip_phi3 else ["phi3", "roberta"]
    dataset_records = {}
    errors = []

    context_rows = []
    activity_rows = []

    for dataset_name, dataset_config in DATASETS.items():
        dataset_path = resolve_dataset_path(input_dir, dataset_config)
        traces = load_traces(dataset_path, args.max_traces)
        profiles = build_activity_profiles(traces)
        profile_by_name = {profile["name"]: profile for profile in profiles}

        dataset_records[dataset_name] = {
            "path": str(dataset_path),
            "trace_count": len(traces),
            "activity_count": len(profiles),
        }

        context_truth = {
            field: normalize_value(value)
            for field, value in dataset_config["context_truth"].items()
        }

        context_text = (
            f"Domain: {context_truth['processing_domain']}. "
            f"Purpose: {context_truth['purpose']}. "
            f"Data category: {context_truth['data_category']}."
        )

        labeled_activity_names = [
            name
            for name in dataset_config["activity_truth"]
            if name in profile_by_name
        ]
        labeled_profiles = [profile_by_name[name] for name in labeled_activity_names]

        missing_labels = sorted(
            set(dataset_config["activity_truth"]) - set(labeled_activity_names)
        )
        dataset_records[dataset_name]["missing_labeled_activities"] = missing_labels

        for model_name in models:
            context, error = safe_run(
                lambda model_name=model_name: run_context_model(model_name, traces),
                f"{model_name}:{dataset_name}:context",
            )

            if error:
                errors.append(error)
                context_prediction = {field: "__ERROR__" for field in CONTEXT_FIELDS}
            else:
                context_prediction = context_to_dict(context)

            for field in CONTEXT_FIELDS:
                expected_value = context_truth[field]
                predicted_value = context_prediction.get(field, "none")
                impact_label = context_impact_label(
                    field,
                    expected_value,
                    predicted_value,
                )

                context_rows.append({
                    "dataset": dataset_name,
                    "model": model_name,
                    "field": field,
                    "y_true": "0_COMPLIANT",
                    "y_pred": impact_label,
                    "expected_value": expected_value,
                    "acceptable_values": acceptable_context_values(expected_value),
                    "predicted_value": predicted_value,
                })

            activity_map, error = safe_run(
                lambda model_name=model_name: run_activity_model(
                    model_name,
                    labeled_profiles,
                    context_text,
                ),
                f"{model_name}:{dataset_name}:activity",
            )

            if error:
                errors.append(error)
                activity_map = {}

            for activity_name in labeled_activity_names:
                truth = dataset_config["activity_truth"][activity_name]
                prediction = normalize_activity_prediction(
                    activity_map.get(activity_name, "OTHER")
                )

                activity_rows.append({
                    "dataset": dataset_name,
                    "model": model_name,
                    "activity": activity_name,
                    "y_true": truth,
                    "y_pred": prediction,
                })

    write_csv(
        output_dir / "context_predictions.csv",
        context_rows,
        [
            "dataset",
            "model",
            "field",
            "y_true",
            "y_pred",
            "expected_value",
            "acceptable_values",
            "predicted_value",
        ],
    )
    write_csv(
        output_dir / "activity_predictions.csv",
        activity_rows,
        ["dataset", "model", "activity", "y_true", "y_pred"],
    )

    metric_rows = []
    reports = {}

    for task, rows in [
        ("context", context_rows),
        ("activity_type", activity_rows),
    ]:
        if task == "context":
            confusion_labels = CONTEXT_IMPACT_LABELS
        else:
            confusion_labels = sorted({row["y_true"] for row in rows} | {row["y_pred"] for row in rows})

        for model_name in models:
            model_rows = [row for row in rows if row["model"] == model_name]
            y_true = [row["y_true"] for row in model_rows]
            y_pred = [row["y_pred"] for row in model_rows]
            metric_labels = sorted(set(y_true) | set(y_pred))

            metrics = compute_metrics(y_true, y_pred, metric_labels)
            metric_rows.append({
                "task": task,
                "model": model_name,
                **metrics,
            })

            reports[f"{task}_{model_name}"] = classification_report(
                y_true,
                y_pred,
                labels=metric_labels,
                zero_division=0,
                output_dict=True,
            )

            report_text = classification_report(
                y_true,
                y_pred,
                labels=metric_labels,
                zero_division=0,
            )
            (output_dir / f"{task}_{model_name}_classification_report.txt").write_text(
                report_text,
                encoding="utf-8",
            )

            save_confusion_matrix(
                y_true,
                y_pred,
                confusion_labels,
                f"{task} confusion matrix - {model_name}",
                output_dir / f"{task}_{model_name}_confusion_matrix.png",
            )

    write_csv(
        output_dir / "metrics_summary.csv",
        metric_rows,
        [
            "task",
            "model",
            "accuracy",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "precision_micro",
            "recall_micro",
            "f1_micro",
            "precision_weighted",
            "recall_weighted",
            "f1_weighted",
        ],
    )

    for task in ["context", "activity_type"]:
        save_metrics_barplot(
            metric_rows,
            task,
            output_dir / f"{task}_metrics_comparison.png",
        )

    payload = {
        "datasets": dataset_records,
        "input_dir": str(input_dir),
        "metrics": metric_rows,
        "classification_reports": reports,
        "errors": errors,
    }
    (output_dir / "evaluation_results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    pdf_path = generate_pdf_report(
        results_dir=output_dir,
        output_path=output_dir / "Executive_Experiment_Report.pdf",
    )

    print(f"Evaluation completed. Results written to: {output_dir}")
    print(f"Executive PDF report written to: {pdf_path}")
    if errors:
        print(f"Completed with {len(errors)} model execution error(s). See evaluation_results.json.")


if __name__ == "__main__":
    evaluate(parse_args())
