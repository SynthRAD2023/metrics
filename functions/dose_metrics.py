#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from typing import Optional

def mae_dose(d_ct: np.ndarray, d_sct: np.ndarray, d_prescribed: float, threshold: Optional[float] = 1) -> float:
    """
    Compute Mean Absolute Error (MAE) for the dose distributions given a certain
    threshold [0,1] relative to the prescribed dose.

    Parameters
    ----------
    d_ct : np.ndarray
        Dose distribution of real CT.
    d_sct : np.ndarray
        Dose distribution of synthetic CT.
    d_prescribed : float
        Value of the prescribed dose.
    threshold : float, optional
        Theshold for determining the included voxels relative to the prescribed
        dose. It can be a value beteen 0 and 1. The default is 1.

    Returns
    -------
    mae_dose_value : float
        Mean absolute dose difference relative to the prescribed dose.

    """
    # Threshold dose distributions
    abs_th = threshold * d_prescribed
    d_ct = d_ct[d_ct >= abs_th]
    d_sct = d_sct[d_ct >= abs_th]
    n = len(d_ct)
    
    # Calculate MAE        
    mae_dose_value = np.sum(np.abs(d_ct - d_sct)/d_prescribed)/n
    return float(mae_dose_value)


# def dvh_metric():
#     # To implement
    
# def gamma_index():
#     # To implement
    