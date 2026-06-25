import argparse
import os
import sys
import numpy as np 
import nibabel

def load_nifti (path:str) -> np.ndarray: 
    img = nibabel.load(path)
    data = np.asanyarray(img.dataobj, dtype = np.float32)
    return data 


def get_brain_mask(path:str, outfile=None) -> np.ndarray: 
    import brainchop as bc
    # Load, skull-strip, save
    vol = bc.load(path)
    brain_stripped = bc.segment(vol, "mindgrab")
    mask = (brain_stripped.data.numpy()>0).astype(bool)
    if not outfile is None:
        bc.save(mask, outfile)
        print(f'Saved brain mask in {outfile}')
    return mask


# %%
