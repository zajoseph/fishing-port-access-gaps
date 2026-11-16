"""Unit tests for the T4.1 event-study estimators (no data files needed)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from portgaps.eventstudy import methods as M  # noqa: E402


def test_sc_weights_recover_convex_combination():
    rng = np.random.default_rng(0)
    A = rng.random((60, 5))
    w_true = np.array([0.6, 0.0, 0.4, 0.0, 0.0])
    w = M.sc_weights(A, A @ w_true)
    assert np.allclose(w, w_true, atol=1e-4)
    assert abs(w.sum() - 1) < 1e-9 and (w >= 0).all()


def test_window_months_wraps_year():
    assert M.window_months(2024) == [202410, 202411, 202412] + [202500 + m for m in range(1, 9)]
    assert M.window_months(2024, 10, 2)[-1] == 202502


def test_window_did_zero_effect_when_ratio_constant():
    idx = [y * 100 + m for y in range(2016, 2026) for m in range(1, 13)]
    k = pd.Series(np.linspace(1, 2, len(idx)), index=idx)
    r = M.window_did(2 * k, k)
    assert abs(r["effect_pct"]) < 1e-12


def test_sc_fit_scaled_counterfactual_matches_donor_shape():
    idx = [y * 100 + m for y in range(2016, 2026) for m in range(1, 13)]
    base = pd.Series(1 + np.sin(np.arange(len(idx))) ** 2, index=idx)
    y1 = 10 * base
    Y0 = pd.DataFrame({"a": base, "b": pd.Series(np.cos(np.arange(len(idx))) ** 2 + 1, index=idx)})
    r = M.sc_fit(y1, Y0, pre_end=202409, windows={"during": (202410, 202508)})
    assert r["weights"]["a"] > 0.999
    assert abs(r["during_pct"]) < 1e-6


def test_placebo_in_time_sc_dec_sep_window_wraps_year():
    """T4.2 fake events run Dec -> Sep; the fit ends the month before."""
    idx = [y * 100 + m for y in range(2016, 2026) for m in range(1, 13)]
    base = pd.Series(1 + np.sin(np.arange(len(idx))) ** 2, index=idx)
    Y0 = pd.DataFrame({"a": base, "b": pd.Series(np.cos(np.arange(len(idx))) ** 2 + 1, index=idx)})
    tp = M.placebo_in_time_sc(3 * base, Y0, [2017, 2018], m_start=12, m_end=9)
    assert list(tp.fake_event) == ["2017-12", "2018-12"]
    assert (tp.during_pct.abs() < 1e-6).all()
    # default call keeps the T4.1 Oct -> Aug convention
    assert list(M.placebo_in_time_sc(3 * base, Y0, [2017]).fake_event) == ["2017-10"]


def test_charleston_config_windows():
    from portgaps.eventstudy import config_charleston as K
    assert K.PRE_END == 201911 and K.DURING == (201912, 202009) and K.AFTER == (202010, 202412)
    assert K.AFTER_Y1 == (202010, 202109) and K.AFTER_LATER == (202110, 202412)
    assert len(K.CLOSURE_MONTHS) == 10 and K.PANEL_END == 202412
    assert M.window_months(2019, 12, 9) == [201912] + [202000 + m for m in range(1, 10)]
