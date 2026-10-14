"""SHAP explainability for churn model."""

from churn_intel.explain.local import explain_customer_record
from churn_intel.explain.global_explain import run_global_shap_analysis

__all__ = ["explain_customer_record", "run_global_shap_analysis"]
