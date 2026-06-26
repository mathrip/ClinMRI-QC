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

## Configuration

All thresholds live in a single JSON file, `config/default.json`. The pipeline reads it automatically; pass `--config /path/to/your.json` to use a different one. Edit the numbers here rather than inside the code. Each QC module has its own section.

```json
{
  "check_metadata":              { ... },
  "check_artifacts":             { ... },
  "check_contrast_enhancement":  { ... },
  "check_registration":          { ... },
  "check_fov":                   { ... }
}
```

### `check_metadata`

Metadata and image-feature QC.

| Key | Meaning | Default |
|---|---|---|
| `min_voxel_size_mm` | Voxel spacing below this is implausible | `0.1` |
| `max_voxel_size_mm` | Voxel spacing above this is implausibly coarse | `6.0` |
| `max_anisotropy_ratio` | max/min spacing above this warns (very anisotropic) | `8.0` |
| `min_foreground_fraction` | Foreground below this fails (near-empty volume) | `0.05` |
| `warn_foreground_fraction` | Foreground below this warns | `0.10` |
| `min_intensity_std` | Intensity spread below this fails (constant image) | `1e-6` |
| `max_centroid_offset_mm` | Brain centre this far from the volume centre warns | `30.0` |
| `foreground_percentile` | Percentile used to estimate foreground when no mask is given | `10.0` |

### `check_artifacts`

ResNet50 regression artefact detector. `class_thresholds` are per-class cut-offs in the model's `[0, 1]` output space, above which a class is flagged. The defaults are calibrated at roughly the 99th percentile across 937 scans (`bias_field` lowered, as the model scores most brain MRI high on inhomogeneity), so changing them shifts the false-positive / false-negative balance.

| Key | Meaning | Default |
|---|---|---|
| `model_path` | Path to the trained checkpoint | `quickbrain/classifier/best_regression_model.pt` |
| `threshold` | Fallback cut-off if a class has no specific threshold | `0.5` |
| `class_thresholds.motion` | Flag cut-off for motion | `0.15` |
| `class_thresholds.noise` | Flag cut-off for noise | `0.38` |
| `class_thresholds.ghosting` | Flag cut-off for ghosting | `0.45` |
| `class_thresholds.bias_field` | Flag cut-off for bias field | `0.8818` |
| `class_thresholds.gibbs` | Flag cut-off for Gibbs ringing | `0.10` |
| `class_thresholds.zipper` | Flag cut-off for zipper / RF interference | `0.0305` |

### `check_contrast_enhancement`

Heuristic screen for post-contrast (gadolinium) T1w scans. A scan is flagged only when both markers exceed their thresholds.

| Key | Meaning | Default |
|---|---|---|
| `vessel_ratio_threshold` | Minimum 99th/50th-percentile intensity ratio (bright vessels) | `1.6` |
| `bright_fraction_threshold` | Minimum fraction of very-bright brain voxels | `0.002` |
| `sigma_factor` | Brightness cut-off as mean + this many standard deviations | `3.0` |

### `check_registration`

SSIM and NCC against a reference image (only runs when `--ref` is given). A scan is flagged if a metric falls below its threshold.

| Key | Meaning | Default |
|---|---|---|
| `ssim_threshold` | Minimum acceptable structural similarity | `0.70` |
| `ncc_threshold` | Minimum acceptable normalised cross-correlation | `0.80` |

### `check_fov`

Field-of-view cropping check.

| Key | Meaning | Default |
|---|---|---|
| `margin_threshold` | Minimum margin (mm) between the brain and the scan edge | `5` |

### Changing a threshold

Two ways:

1. Edit `config/default.json` and run the pipeline normally.
2. Copy it, edit your copy, and pass `--config my_config.json`.

When calling a module directly in Python, pass overrides as a dict (any subset; the rest fall back to defaults):

```python
metaqc.run_qc(
    "subject01/T1W.nii.gz",
    thresholds={"max_centroid_offset_mm": 45.0},
)
```

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
