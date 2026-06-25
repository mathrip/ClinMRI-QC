import argparse
import os
import sys
import numpy as np 
import nibabel
import tempfile

def load_nifti (path:str) -> np.ndarray: 
    img = nibabel.load(path)
    data = np.asanyarray(img.dataobj, dtype = np.float32)
    return data 


import nibabel as nib
from scipy.ndimage import zoom

def get_brain_mask(path: str, outfile=None) -> np.ndarray:
    import brainchop as bc
    from brainchop.cli import _save_inverse_conform

    vol = bc.load(path)
    brain_mask = bc.segment(vol, "mindgrab")
 
    if outfile is None:
        outfile = tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False)
    
    _save_inverse_conform(brain_mask, path, outfile.name)
    
    mask = load_nifti(outfile.name)

    return (mask>0).astype(bool)

