<img src="https://github.com/mathrip/ClinMRI-QC/blob/47fa80018a7e84220d33bd578d3c3f3572d37193/docs/quickbrain_logo.png" alt="quickbrain logo" width="100" align="left"/> 


# QuiCk-Brain
A light python package for automated quality check of clinical MRI scans

Results of the KCL BMEIS Hackathon 2026

## Team Members
- Mathilde Ripart (mathilde.ripart@kcl.ac.uk)
- Heqing Rong (heqing.rong@kcl.ac.uk)
- Jieun Seo (jieun.seo@kcl.ac.uk)
- Milly Mak (milly.mak@kcl.ac.uk)
- Joshua Astley (joshua.astley@kcl.ac.uk)

## Overview

MRI scans collected in clinical practice often contain quality issues that can negatively impact downstream analysis, AI pipelines, and clinical research.
Manual quality control is time-consuming and subjective.

QuiCk-Brain automatically checks:
- **Imaging artefacts** — motion, noise, ghosting, bias field, Gibbs ringing, zipper/RF interference (ResNet50 regression model, scores 0–1)
- **T1 gadolinium contrast enhancement** — heuristic screen for post-contrast T1w scans
- **Field-of-view (FOV) cropping** — detects incomplete brain coverage in 3 progressive checks
- **Coregistration quality** — SSIM and NCC against a reference image (optional)
- **Metadata & image features** — voxel size, anisotropy, foreground fraction, intensity statistics, centroid offset

## Data

Any open-source MRI dataset that contains clinical multimodal scans (T1w, T2w, FLAIR, ...).

**E.g. [Multiple Sclerosis Lesion Data](https://github.com/muschellij2/open_ms_data)**

The dataset contains:
- 30 patients with MS
- cross-sectional and longitudinal scans
- modalities: T1w, FLAIR, T2w, T1w with contrast, lesion mask on FLAIR

To download (~7GB):
```bash
git clone https://github.com/muschellij2/open_ms_data.git
```

## Install the package

```bash
git clone https://github.com/mathilderipart/ClinMRI-QC.git
cd ClinMRI-QC
pip install -e .
```

---

## Usage

### Run the full QC pipeline

```bash
python master.py \
    --images_dir /path/to/niftis \
    --output_dir /path/to/output
```

### Example with coregistration check and overwrite

```bash
python master.py \
    --images_dir /path/to/niftis \
    --output_dir /path/to/output  \
    --overwrite \
    --ref /path/to/ref_image
```

The pipeline will skull-strip each scan, run all QC modules, append results to a CSV, and generate an HTML report when all scans are done.

### All options

| Argument | Description | Default |
|---|---|---|
| `--images_dir` | Directory containing `.nii` / `.nii.gz` T1w scans | **required** |
| `--output_dir` | Where to write `qc_results.csv` and `qc_report.html` | **required** |
| `--ref` | Reference image for coregistration QC (SSIM + NCC vs each scan) | disabled |
| `--overwrite` | Reprocess scans already present in the CSV | resume mode |
| `--limit N` | Process only the first N scans (quick test) | all scans |
| `--device` | `cpu` or `cuda` | auto-detect |
| `--exclude_prefix` | Skip files whose name starts with this string | `synthetic_` |
| `--config` | Path to a custom JSON config file | `config/default.json` |

---

## Output

Both files are written to `--output_dir`.

### `qc_results.csv`

One row per scan. Columns are grouped by module:

| Column group | Columns | Description |
|---|---|---|
| **Identity** | `timestamp`, `scan_path`, `patient_id` | When and what was processed |
| **Image info** | `img_dim_x/y/z`, `img_vox_x/y/z`, `img_orientation` | Dimensions, voxel size (mm), RAS orientation |
| **Artefact detection** | `artifacts_quality_passed`, `artifacts_detected` | Overall pass/fail and pipe-separated list of flagged classes |
| | `prob_motion`, `prob_noise`, `prob_ghosting`, `prob_bias_field`, `prob_gibbs`, `prob_zipper` | Scaled severity score [0–1] per artefact class |
| | `iqm_motion_blur_score`, `iqm_snr` | Image quality metrics: EFC (motion/blur) and SNR |
| **Contrast** | `contrast_enhanced`, `contrast_vessel_ratio`, `contrast_bright_voxel_fraction` | Gadolinium enhancement flag + supporting metrics |
| **Coregistration** | `coreg_flag`, `coreg_ssim`, `coreg_ncc`, `coreg_ssim_passed`, `coreg_ncc_passed` | GREEN / YELLOW / RED flag, SSIM and NCC values vs reference |
| **FOV** | `fov_overall`, `fov_check1`, `fov_check2`, `fov_check3` | Overall pass/fail + 3 progressive proximity checks |
| **Metadata QC** | `metaqc_status`, `metaqc_reasons`, `metaqc_foreground_fraction`, `metaqc_intensity_mean`, `metaqc_intensity_std`, `metaqc_centroid_offset_mm`, `metaqc_metadata_status` | Image feature checks (foreground fraction, centroid offset, header voxel size) |

Coregistration columns are empty when `--ref` is not provided.

### `qc_report.html`

A self-contained interactive HTML file (no external dependencies, opens in any browser).

**Single scan** — expanded full report with:
- Overall PASS / FAIL verdict
- Artefact severity bar chart (per-class scores with detection thresholds)
- Representative axial slice preview
- EFC and SNR gauges with normal-range bands
- Recommended corrective actions per detected artefact

**Batch (multiple scans)** — dashboard view with:
- Summary statistics (total, passed, failed, pass rate)
- Cohort-level artefact prevalence bar chart
- EFC vs SNR scatter plot coloured by pass/fail
- Sortable overview table linking to each scan
- Collapsible per-patient sections with the full single-scan report for each entry

---
