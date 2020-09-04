# Hackathon 2019 -  COIN over Nigeria


## About the notebook

The goal of this notebook is to:

- Discover and stage-in the COIN processing request generated results
- Plot a few layers 

**The Coherence and Intensity change** 

The coherence between an images pair can show if the images have strong similarities, represented in a scale from 0 to 1. Areas of high coherence will appear bright (values near 1). Areas with poor coherence will be dark (values near 0). For example, vegetation and water have poor coherence and buildings have very high coherence.

The intensity represents the strength of the radar response from the observed scene. Such intensity can vary dependent on changes occurred in time between the acquisitions and also on the scene physical characteristics.

To better detect the intensity change this service provides, in addition to the intensity in dB of the individual images, the dB average and dB difference of the image pair.

Also a couple of RGB composites are provided:

- An RGB image with:

 * Red -  Coherence
 * Green - Intensity average
 * Blue - Null 

Thanks to this representation is possible to show urban centres in yellow, which have high coherence and intensity. Green can represent vegetated fields and forests. The reds and oranges represent unchanging features such as bare soil or possibly rocks.

- An RGB image with:
 
 * Red - Slave Intensity
 * Green - Master Intensity
 * Blue - Master Intensity
 
Thanks to this representation is possible to clearly show inundated areas in cyan.

## Run the notebook on Binder

Click the badge below to run this notebook on Binder

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ec-better/hackathon-2019-COIN-Nigeria/master?urlpath=lab)
