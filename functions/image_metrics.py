#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import SimpleITK
from evalutils.io import SimpleITKLoader
import numpy as np
from typing import Optional
from skimage.metrics import peak_signal_noise_ratio, structural_similarity



class ImageMetrics():
    def __init__(self):
        # TODO
        # Use population wide dynamic range
        self.dynamic_range = 3071 - -1024
    
    def score_patient(self, ground_truth_path, predicted_path):
        loader = SimpleITKLoader()
        gt = loader.load_image(ground_truth_path)
        pred = loader.load_image(predicted_path)
        
        caster = SimpleITK.CastImageFilter()
        caster.SetOutputPixelType(SimpleITK.sitkFloat32)
        caster.SetNumberOfThreads(1)

        gt = caster.Execute(gt)
        pred = caster.Execute(pred)
        
        # Get numpy array from SITK Image
        gt_array = SimpleITK.GetArrayFromImage(gt)
        pred_array = SimpleITK.GetArrayFromImage(pred)
        
        mask_array = np.ones(gt_array.shape, dtype=gt_array.dtype)

        # Calculate image metrics
        mae_value = self.mae(gt_array, 
                                        pred_array,
                                        mask_array)
        
        psnr_value = self.psnr(gt_array, 
                                          pred_array,
                                          mask_array,
                                          use_population_range=True)
        
        ssim_value = self.ssim(gt_array, 
                                          pred_array, 
                                          use_population_range=True)
        return {
            'mae': mae_value,
            'ssim': ssim_value,
            'psnr': psnr_value
        }
    
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

if __name__=='__main__':
    metrics = ImageMetrics()
    ground_truth_path = "path/to/ground_truth.mha"
    predicted_path = "path/to/prediction.mha"
    print(metrics.score_patient(ground_truth_path, predicted_path))
