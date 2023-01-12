#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from typing import Optional
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


class ImageMetrics():
    def __init__(self):
        # TODO
        # Use population wide dynamic range
        self.dynamic_range=2000 
    
    def mae(self,
            gt: np.ndarray, 
            pred: np.ndarray,
            mask: Optional[np.ndarray] = None) -> float:
        """
        Compute Mean Absolute Error (MAE)
    
        Parameters
        ----------
        gt : np.ndarray
            Ground truth
        pred : np.ndarray
            Prediction
        mask : np.ndarray, optional
            Mask for voxels to include. The default is None (including all voxels).
    
        Returns
        -------
        mae : float
            mean absolute error.
    
        """
        if mask is None:
            mask = np.ones(gt.shape)
        else:
            #binarize mask
            mask = np.where(mask>0, 1., 0.)
            
        mae_value = np.sum(np.abs(gt*mask - pred*mask))/mask.sum() 
        return float(mae_value)
    
    
    def psnr(self,
             gt: np.ndarray, 
             pred: np.ndarray,
             mask: Optional[np.ndarray] = None,
             use_population_range: Optional[bool] = False) -> float:
        """
        Compute Peak Signal to Noise Ratio metric (PSNR)
    
        Parameters
        ----------
        gt : np.ndarray
            Ground truth
        pred : np.ndarray
            Prediction
        mask : np.ndarray, optional
            Mask for voxels to include. The default is None (including all voxels).
        use_population_range : bool, optional
            When a predefined population wide dynamic range should be used.
    
        Returns
        -------
        psnr : float
            Peak signal to noise ratio..
    
        """
        if mask is None:
            mask = np.ones(gt.shape)
        else:
            #binarize mask
            mask = np.where(mask>0, 1., 0.)
            
        if use_population_range:
            dynamic_range = self.dynamic_range
        else:
            dynamic_range = gt.max()-gt.min()
            
        # apply mask
        gt = gt[mask==1]
        pred = pred[mask==1]
        psnr_value = peak_signal_noise_ratio(gt, pred, data_range=dynamic_range)
        return float(psnr_value)
    
    
    def ssim(self,
              gt: np.ndarray, 
              pred: np.ndarray,
              use_population_range: Optional[bool] = False) -> float:
        """
        Compute Structural Similarity Index Metric (SSIM)
    
        Parameters
        ----------
        gt : np.ndarray
            Ground truth
        pred : np.ndarray
            Prediction
        use_population_range : bool, optional
            When a predefined population wide dynamic range should be used.
    
        Returns
        -------
        ssim : float
            strugtural similarity index metric.
    
        """
        if use_population_range:
            dynamic_range = self.dynamic_range
        else:
            dynamic_range = gt.max()-gt.min()
            
        ssim_value = structural_similarity(gt, pred, data_range=dynamic_range)
        return float(ssim_value)
    