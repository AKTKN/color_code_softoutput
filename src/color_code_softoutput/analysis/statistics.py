"""Central 99% binomial intervals and shot-level success-logit fits."""
import warnings
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.special import expit
import statsmodels.api as sm

CONFIDENCE_LEVEL = .99


def rounded_scores(scores, round_digits: int | None = None) -> np.ndarray:
    """Copy scores, optionally applying Python round to each actual score.

    Args:
        scores: Numeric confidence values; stored arrays are never modified.
        round_digits: Decimal places (including negative integers), or None.
    Returns: Float array with the same shape, rounded before grouping/thresholds.
    Raises: ValueError if round_digits is neither an integer nor None.
    """
    values = np.array(scores, dtype=float, copy=True)
    if round_digits is None:
        return values
    if isinstance(round_digits, (bool, np.bool_)) or not isinstance(round_digits, (int, np.integer)):
        raise ValueError("round_digits must be an integer or None")
    return np.array([round(float(x), int(round_digits)) for x in values.flat]).reshape(values.shape)


def wilson_interval(failures, shots, confidence_level: float = CONFIDENCE_LEVEL):
    """Return vectorized Wilson limits from valid nonempty binomial counts.

    Args:
        failures: Scalar or array of observed failures.
        shots: Positive scalar or aligned count array.
        confidence_level: Probability in (0,1), default .99.
    Returns:
        Lower and upper rate limits, with exact 0/1 endpoints at extreme counts.
    Raises:
        ValueError: Invalid counts or confidence level.
    """
    failures, shots = np.asarray(failures), np.asarray(shots)
    if not 0 < confidence_level < 1 or np.any(shots <= 0) or np.any(failures < 0) or np.any(failures > shots):
        raise ValueError("Invalid binomial counts or confidence level")
    z = norm.ppf((1+confidence_level)/2)
    rate = failures/shots
    center = (rate+z*z/(2*shots))/(1+z*z/shots)
    half = z*np.sqrt(rate*(1-rate)/shots+z*z/(4*shots*shots))/(1+z*z/shots)
    return np.where(failures == 0,0,np.maximum(0,center-half)), np.where(failures == shots,1,np.minimum(1,center+half))


def grouped_rates(scores, failures, *, bins="auto", confidence_level: float = CONFIDENCE_LEVEL,
                  round_digits: int | None = None) -> pd.DataFrame:
    """Group near-discrete scores or histogram continuous scores, excluding empty bins.

    Args:
        scores: Finite confidence values, shape (shots,).
        failures: Matching boolean failure labels.
        bins: 'auto' rounds to 10 decimals if <=64 distinct values; otherwise
            NumPy auto histogram bins. Integer/edges force histogram bins.
        confidence_level: Wilson coverage probability.
        round_digits: Round actual scores first. With auto bins, group each exact
            rounded value; explicit histogram bins still take precedence. None
            preserves the previous near-discrete/histogram behavior.
    Returns:
        Table with score, shots, failures, logical_error_rate, low and high.
    """
    scores, failures = np.asarray(scores,dtype=float), np.asarray(failures,dtype=bool)
    if scores.ndim != 1 or scores.shape != failures.shape or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("Need aligned nonempty finite score/failure arrays")
    scores = rounded_scores(scores, round_digits)
    rounded = np.round(scores,10) if round_digits is None else scores
    if isinstance(bins,str) and bins == "auto" and (round_digits is not None or len(np.unique(rounded)) <= 64):
        centers, assignment = np.unique(rounded, return_inverse=True)
    else:
        edges = np.histogram_bin_edges(scores, bins=bins)
        centers = (edges[:-1]+edges[1:])/2
        assignment = np.clip(np.searchsorted(edges,scores,side="right")-1,0,len(centers)-1)
    counts = np.bincount(assignment, minlength=len(centers))
    errors = np.bincount(assignment, weights=failures, minlength=len(centers)).astype(np.int64)
    keep = counts > 0
    table = pd.DataFrame(dict(score=centers[keep],shots=counts[keep],failures=errors[keep]))
    table["logical_error_rate"] = table.failures/table.shots
    table["low"], table["high"] = wilson_interval(table.failures,table.shots,confidence_level)
    return table


def logistic_fit(scores, failures, confidence_level: float = CONFIDENCE_LEVEL) -> dict:
    """Fit logit P(success|score)=k*score+l with explicit degeneracy statuses.

    Args:
        scores: Finite shot-level scores, shape (shots,).
        failures: Aligned boolean labels for that metric's decoder.
        confidence_level: Wald interval coverage for the binomial GLM.
    Returns:
        k/l estimates, SEs, intervals, counts and status. Degenerate fits have
        NaN coefficients, never invented finite values. This is an empirical fit.
    """
    scores, failures = np.asarray(scores,dtype=float), np.asarray(failures,dtype=bool)
    if scores.ndim != 1 or scores.shape != failures.shape or not np.isfinite(scores).all():
        raise ValueError("Aligned finite score and failure arrays required")
    result = dict(shots=len(scores), failures=int(failures.sum()), fit_status="ok")
    result.update({key:np.nan for key in ("k","l","k_se","l_se","k_low","k_high","l_low","l_high")})
    if not len(scores) or failures.all() or not failures.any():
        result["fit_status"] = "single_outcome"
        return result
    if np.ptp(scores) == 0:
        result["fit_status"] = "constant_score"
        return result
    success_scores, failure_scores = scores[~failures], scores[failures]
    if success_scores.min() >= failure_scores.max() or failure_scores.min() >= success_scores.max():
        result["fit_status"] = "perfect_or_quasi_separation"
        return result
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        try:
            fit = sm.GLM((~failures).astype(float), sm.add_constant(scores), family=sm.families.Binomial()).fit()
            if not fit.converged or any("separation" in str(w.message).lower() for w in captured):
                result["fit_status"] = "separation_or_nonconvergence"
                return result
            bounds = fit.conf_int(alpha=1-confidence_level)
            if not np.isfinite(np.r_[fit.params,fit.bse,bounds.ravel()]).all():
                result["fit_status"] = "nonfinite_fit"
                return result
            for i,key in enumerate(("l","k")):
                result.update({key:fit.params[i],f"{key}_se":fit.bse[i],
                               f"{key}_low":bounds[i,0],f"{key}_high":bounds[i,1]})
        except (ValueError, np.linalg.LinAlgError) as exception:
            result["fit_status"] = f"fit_failed:{type(exception).__name__}"
    return result
