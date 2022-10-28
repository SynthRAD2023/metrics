#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpuy as np
from typing import Optional
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def mae(ct: np.ndarray, sct: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
    """
    Compute Mean Absolute Error (MAE)

    Parameters
    ----------
    ct : np.ndarray
        Ground truth (real CT).
    sct : np.ndarray
        Prediction (synthetic CT).
    mask : np.ndarray, optional
        Mask for voxels to include. The default is None (including all voxels).

    Returns
    -------
    mae : float
        mean absolute error.

    """
    if mask == None:
        mask = np.ones(ct.shape)
    else:
        #binarize mask
        mask = np.where(mask>0, 1., 0.)
        
    mae_value = np.sum(np.abs(ct*mask - sct*mask))/mask.sum() 
    return float(mae_value)



def psnr(ct: np.ndarray, sct: np.ndarray, mask: Optional[np.ndarray] = None) -> float:
    """
    Compute Peak Signal to Noise Ratio metric (PSNR)

    Parameters
    ----------
    ct : np.ndarray
        Ground truth (real CT).
    sct : np.ndarray
        Prediction (synthetic CT).
    mask : np.ndarray, optional
        Mask for voxels to include. The default is None (including all voxels).

    Returns
    -------
    psnr : float
        Peak signal to noise ratio..

    """
    if mask == None:
        mask = np.ones(ct.shape)
    else:
        #binarize mask
        mask = np.where(mask>0, 1., 0.)
        
    # apply mask
    ct = ct[mask==1]
    sct = sct[mask==1]
    psnr_value = peak_signal_noise_ratio(ct, sct, data_range=ct.max()-ct.min())
    return float(psnr_value)



def ssim(ct: np.ndarray, sct: np.ndarray) -> float:
    """
    Compute Structural Similarity Index Metric (SSIM)

    Parameters
    ----------
    ct : np.ndarray
        Ground truth (real CT).
    sct : np.ndarray
        Prediction (synthetic CT).

    Returns
    -------
    ssim : float
        structural similarity index metric.

    """
    maxval = ct.max()-ct.min()
    ssim_value = structural_similarity(ct, sct, data_range=maxval)
    return float(ssim_value)

