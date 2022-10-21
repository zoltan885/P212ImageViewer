# P212ImageViewer
image viewer for beamline P21.2 at PETRA

## important
TODO dark subtraction

TODO mask image

TODO 1d plot of roi values over the image range

TODO unify load function

## nice to have
FEATURE multi detector view (name the detectors?, so that one can pick later which one to calibrate)

FEATURE 
- scaling to physical coordinates (and back to pixels)
- calibration (either from pyFAI poni files or by filling out the values by hand)
- this should be globally applicable; how to do this for multi-detector view?

FEATURE uniform colorscale among several images

FEATURE detachable tabs (yeah, this is the wrong branch, but I messed it up, will correct it later)

FEATURE range scaling (e.g. rotation angle)

FEATURE read FIO file

FEATURE open copy of data (for alternative view, e.g. different range, without having to copy the data into memory again)

FEATURE interfaces
- General (XRD - with calibration)
- Tomo (corrections, access to tomopy and some quick reconstruction, locally???)
- Surface (CTR visualization, implement coordinate transformations from Gary's software)
- 3DXRD ???
- HRSSM

FEATURE arbitrary image filters (e.g. blur, 'like those from ImageJ')



