#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import warnings
import numpy as np
from typing import Optional

class DoseMetrics():
    def __init__(self, matrad_path, dose_path, prescribed_doses):
        self.prescribed_dose = prescribed_doses
        self.matrad_path = matrad_path
        self.dose_path = dose_path
    
        
    def mae_dose(self,
                 d_gt : np.ndarray, 
                 d_pred : np.ndarray,
                 region : str,
                 threshold: Optional[float] = 1) -> float:
        """
        Compute Mean Absolute Error (MAE) for the dose distributions given a certain
        threshold [0,1] relative to the prescribed dose.
    
        Parameters
        ----------
        d_gt : np.ndarray
            Dose distribution of the ground truth CT
        d_pred : np.ndarray
            Dose distribution of the predicted synthetic CT.
        region : str
            Which region is analyzed, either 'B' (for brain) or 'P' (for pelvis).
        threshold : float, optional
            Theshold for determining the included voxels relative to the prescribed
            dose. It can be a value beteen 0 and 1. The default is 1.
    
        Returns
        -------
        mae_dose_value : float
            Mean absolute dose difference relative to the prescribed dose.
    
        """
        # Threshold dose distributions
        abs_th = threshold * self.prescribed_dose[region]
        d_pred = d_pred[d_gt >= abs_th]
        d_gt = d_gt[d_gt >= abs_th]
        n = len(d_gt)
        
        # Calculate MAE     
        mae_dose_value = np.sum(np.abs(d_gt - d_pred)/self.prescribed_dose[region])/n
        return float(mae_dose_value)
    
    
    def dvh_metric(self, 
                   gt_dvh : dict, 
                   pred_dvh : dict,
                   region : str,
                   eps : Optional[float] = 1e-12 ) -> float:
        """
        Calculate the dose volume histogram (DVH) metric from the given DVH
        parameters.

        Parameters
        ----------
        gt_dvh : dict
            DVH parameters for the dose calculation on ground truth CT.
        pred_dvh : dict
            DVH parameters for the dose calculation on predicted synthetic CT.
        region : str
            The region for this image. Either 'B' (for brain) or 'P' (for pelvis).
        eps : float, optional
            Small epsilon value to prevent division by zero
            
        Returns
        -------
        DVH_metric : float
            One combined metric based on several DVH parameters for the SynthRAD 
            challenge.

        """
        gt_organ_ind = {gt_dvh[i]['name']: i for i in range(len(gt_dvh))}
        pred_organ_ind = {pred_dvh[i]['name']: i for i in range(len(pred_dvh))}
        
        # target metrics
        ptv_gt = gt_dvh[gt_organ_ind['PTV']]
        ptv_pred = pred_dvh[pred_organ_ind['PTV']]
        
        D98_target = ( np.abs(ptv_gt['D_98'] - ptv_pred['D_98'] + eps ) /
                      (ptv_gt['D_98'] + eps ) )
        
        pd = self.prescribed_dose[region]
        if pd%1==0:
            pd_str=int(pd)
        else:
            pd_str=f"{pd}".replace('.','_')
        
        V95_target = ( np.abs(ptv_gt[f'CI_{pd_str}Gy'] - ptv_pred[f'CI_{pd_str}Gy'] + eps ) /
                        ( ptv_gt[f'CI_{pd_str}Gy'] + eps ) )
        target_term = D98_target + V95_target
        
        
        # Defining OAR priorities
        # TODO (for test phase): update priority list (for pelvis hardcode per patient)
        if region == 'B':
            priorities = ['Brain',
                          'Brainstem',
                          'OpticChiasm',
                          'OpticNerve_L',
                          'OpticNerve_R',
                          'Cochlea_L',
                          'Cochlea_R',
                          'Pituitary',
                          'Eye_L',
                          'Eye_R',
                          'Eye_Post_L',
                          'Eye_Post_R',
                          'Lens_L',
                          'Lens_R',
                          'Eye_Ant_L',
                          'Eye_Ant_R',
                          'Body']
        elif region == 'P':
            priorities = ['Bladder',
                          'Rectum',
                          'Bowel',
                          'Femur_L',
                          'Femur_R',
                          'Sigmoid',
                          'Uterus',
                          'Prostate',
                          'Vagina',
                          'Vulva',
                          'Body']
        
        # OAR metrics
        D2_OAR, Dmean_OAR, OAR_used = [], [], []
        pos = 0
        while len(OAR_used) < 3 and pos < len(priorities):
            organ = priorities[pos]
            if organ in gt_organ_ind.keys() and organ in pred_organ_ind.keys():
                oar_gt = gt_dvh[gt_organ_ind[organ]]
                oar_pred = pred_dvh[pred_organ_ind[organ]]
               
                # Determine D2 and D_mean for selected organ at risk
                D2_OAR.append( ( np.abs(oar_gt['D_2'] - oar_pred['D_2'] + eps ) /
                                 ( oar_gt['D_2'] + eps) ) )
                Dmean_OAR.append( ( np.abs(oar_gt['mean'] - oar_pred['mean'] + eps ) /
                                    ( oar_gt['mean'] + eps) ) )
                OAR_used.append(organ)
            pos += 1
            
        # Calcuate the OAR term and print a warning when less than 3 are used.
        if len(D2_OAR)>0:
            OAR_term = 1/(len(D2_OAR)) * np.sum(D2_OAR) + 1/(len(Dmean_OAR)) * np.sum(Dmean_OAR)
        else:
            OAR_term = 0
            
        if len(D2_OAR)<3:
            warnings.warn('Less than 3 OARs used.')
        print(f'Used OARs: {OAR_used}')
        
        # Calculate sum
        return float(target_term +  OAR_term)

    
    