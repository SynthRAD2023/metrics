#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import warnings
import numpy as np
from typing import Optional
import json
import os
import subprocess
import h5py
import math

    
class DoseMetrics():       
    def __init__(self, dose_path, prescribed_doses = {'B': 2.0, 'P': 3.0}):
        self.prescribed_dose = prescribed_doses
        self.dose_path = dose_path
    
    def score_patient(self, patient_id, pred_path):
        region = patient_id[1]
        
        metrics = {}
        # Calculate dosimetric evaluation metrics
        for rad_type in ['photon', 'proton']:
            if os.path.isfile(self.dose_path / patient_id / f"{patient_id}_RTplan_{rad_type}s.mat"):
                # run the matRad script to recalculate dose on the prediction
                print(f'Calling matRad subproces for {patient_id} {rad_type}...')
                subprocess.call(["/matrad/compute_metrics", self.dose_path, patient_id, rad_type, pred_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print('Subprocess finished.')
                
                # Calculate MAE dose metric
                gt_mat_file = os.path.join(self.dose_path, patient_id, f'gtdose_{rad_type}.mat')
                pred_mat_file = os.path.join(self.dose_path, patient_id, f'preddose_{rad_type}.mat')
                if os.path.isfile(gt_mat_file) and os.path.isfile(pred_mat_file):
                    with h5py.File(gt_mat_file, 'r') as fh:
                        gt_dose = fh['doseCube'][()].T
                    with h5py.File(pred_mat_file, 'r') as fh:
                        pred_dose = fh['sctdoseCube'][()].T    
                    metrics[f'mae_target_{rad_type}'] = self.mae_dose(gt_dose,
                                                                      pred_dose,
                                                                      region,
                                                                      threshold=0.9)
                    # cleanup
                    os.remove(gt_mat_file)
                    os.remove(pred_mat_file)
                else:
                    warnings.warn(f"{patient_id}: gtdose_{rad_type}.mat and/or preddose_{rad_type}.mat not present")
                    metrics[f'mae_target_{rad_type}'] = float('nan')

                # Calculate DVH metric
                ct_dvh_file = os.path.join(self.dose_path, patient_id, f'ct_{rad_type}.json')
                pred_dvh_file = os.path.join(self.dose_path, patient_id, f'sct_{rad_type}.json')
                if os.path.isfile(ct_dvh_file) and os.path.isfile(pred_dvh_file):
                    with open(ct_dvh_file, 'r') as inf:
                        gt_dvh = json.load(inf)
                    with open(pred_dvh_file, 'r') as inf:
                        pred_dvh = json.load(inf)
                    metrics[f'dvh_{rad_type}'] = self.dvh_metric(gt_dvh,
                                                                 pred_dvh,
                                                                 region)
                    # cleanup
                    os.remove(ct_dvh_file)
                    os.remove(pred_dvh_file)
                else:
                    warnings.warn(f"{patient_id}: ct_{rad_type}.json and/or sct_{rad_type}.json not present")
                    metrics[f'dvh_{rad_type}'] = float('nan')

                # Calculate Gamma index
                gamma_file = os.path.join(self.dose_path, patient_id, f'gamma_{rad_type}.json')   
                if os.path.isfile(gamma_file):
                    with open(gamma_file, 'r') as inf:
                        gamma_pass = json.load(inf)
                    metrics[f'gamma_{rad_type}'] = [x for x in gamma_pass if 'ROI' in x['gammaPassRateCell1']][0]['gammaPassRateCell2']
                    # cleanup
                    os.remove(gamma_file)
                else:
                    warnings.warn(f"{patient_id}: gamma_{rad_type}.json not present")
                    metrics[f'dvh_{rad_type}'] = float('nan')

            else:
                warnings.warn(f"No {rad_type} treatment plan found for patient {patient_id}")
        return metrics
           
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
        
        # Find D98
        if ptv_gt['D_98'] is None or math.isnan(ptv_gt['D_98']):
            warnings.warn('None or NaN value in ground truth PTV D98')
            return float('nan')
        elif ptv_pred['D_98'] is None or math.isnan(ptv_pred['D_98']):
            warnings.warn('None or NaN value in sCT PTV D98')
            return float('nan')
        else:
            D98_target = ( np.abs(ptv_gt['D_98'] - ptv_pred['D_98'] + eps ) /
                          (ptv_gt['D_98'] + eps ) )
        
        # Find CI
        pd = self.prescribed_dose[region]
        if pd%1==0:
            pd_str=int(pd)
        else:
            pd_str=f"{pd}".replace('.','_')
        if ptv_gt[f'CI_{pd_str}Gy'] is None or math.isnan(ptv_gt[f'CI_{pd_str}Gy']):
            warnings.warn('None or NaN value in ground truth PTV CI')
            return float('nan')
        elif ptv_pred[f'CI_{pd_str}Gy'] is None or math.isnan(ptv_pred[f'CI_{pd_str}Gy']):
            warnings.warn('None or NaN value in sCT PTV CI')
            return float('nan')
        else:
            V95_target = ( np.abs(ptv_gt[f'CI_{pd_str}Gy'] - ptv_pred[f'CI_{pd_str}Gy'] + eps ) /
                          ( ptv_gt[f'CI_{pd_str}Gy'] + eps ) )            
        target_term = D98_target + V95_target

        # Define which 3 organs at risk are used for the evaluation
        mean_D5_Dmean_per_OAR = {}
        for organ, organ_ind in gt_organ_ind.items():
            if organ not in ['PTV', 'GTV', 'CTV']:
                oar_gt = gt_dvh[organ_ind]
                mean_D5_Dmean_per_OAR[organ] = (oar_gt['D_5'] + oar_gt['mean']) / 2
        OAR_used = sorted(mean_D5_Dmean_per_OAR, key=mean_D5_Dmean_per_OAR.get, reverse =True)
        OAR_used = OAR_used[ : min([3, len(OAR_used)])]
        
        
        # Define OAR DVH term
        D2_OAR, Dmean_OAR = [], []
        for organ in OAR_used:
            oar_gt = gt_dvh[gt_organ_ind[organ]]
            oar_pred = pred_dvh[pred_organ_ind[organ]]
               
            # Determine D2 for selected organ at risk
            if oar_gt['D_2']  is None or math.isnan(oar_gt['D_2']):
                warnings.warn(f'None or NaN value in ground truth {organ} D2')
                return float('nan')
            elif oar_pred['D_2'] is None or math.isnan(oar_pred['D_2']):
                warnings.warn(f'None or NaN value in sCT {organ} D2')
                return float('nan')
            else:
                D2_OAR.append( ( np.abs(oar_gt['D_2'] - oar_pred['D_2'] + eps ) /
                                 ( oar_gt['D_2'] + eps) ) )
             
            # Determine Dmean for selected organ at risk
            if oar_gt['mean']  is None or math.isnan(oar_gt['mean']):
                warnings.warn(f'None or NaN value in ground truth {organ} Dmean')
                return float('nan')
            elif oar_pred['mean'] is None or math.isnan(oar_pred['mean']):
                warnings.warn(f'None or NaN value in sCT {organ} Dmean')
                return float('nan')
            else:            
                Dmean_OAR.append( ( np.abs(oar_gt['mean'] - oar_pred['mean'] + eps ) /
                                    ( oar_gt['mean'] + eps) ) )
            

        # Calcuate the OAR term and print a warning when less than 3 are used.
        if len(D2_OAR)>0:
            OAR_term = 1/(len(D2_OAR)) * np.sum(D2_OAR) + 1/(len(Dmean_OAR)) * np.sum(Dmean_OAR)
        else:
            OAR_term = 0
        
        if len(D2_OAR)<3:
            warnings.warn('Less than 3 OARs used.')
        print(f'Used OARs: {OAR_used}')
    
        # Calculate sum
        return float(target_term + OAR_term)


if __name__=='__main__':
    dose_path = 'path/to/treatment_plans'
    predicted_path = "path/to/prediction.mha"
    patient_id="1BA000"
    
    metrics = DoseMetrics(dose_path)
    print(metrics.score_patient(patient_id, predicted_path))

    
    