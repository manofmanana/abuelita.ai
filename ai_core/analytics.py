"""Analytics helpers using pandas/matplotlib with a safe fallback."""
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import matplotlib.pyplot as plt
except Exception:
    pd = None
    plt = None


def summarize_progress(records):
    """Given a list of dicts with 'score' and 'completed', show a tiny summary.

    Returns a dict with summary stats so tests can assert on them.
    """
    if not records:
        return {"avg": 0.0, "completed_pct": 0.0}
    if pd is None:
        # Fallback: compute simple averages
        scores = [r.get("score", 0) for r in records]
        completed = [1 if r.get("completed") else 0 for r in records]
        avg = sum(scores) / len(scores)
        completed_pct = (sum(completed) / len(completed)) * 100
        return {"avg": round(avg, 2), "completed_pct": round(completed_pct, 2)}

    df = pd.DataFrame(records)
    avg = df["score"].mean()
    completed = df.get("completed", pd.Series([False] * len(df))).mean() * 100
    # Plot simple bar for local debugging
    try:
        fig, ax = plt.subplots()
        ax.bar(["Average Score", "Completion %"], [avg, completed])
        ax.set_title("Student Progress Overview")
        # Do not show in tests; leave the figure to be saved by callers if needed.
        plt.close(fig)
    except Exception:
        pass
    return {"avg": round(float(avg), 2), "completed_pct": round(float(completed), 2)}
