#! /usr/bin/env python

models = {}

def CasA (freq, year):
    """Return the flux of Cas A given a frequency and the year of
    observation. Based on the formula given in Baars et al., 1977.
    
    Parameters:

    freq - Observation frequency in GHz.
    year - Year of observation. May be floating-point.

    Returns: s, flux in Jy.
    """
    from math import log10
    
    snu = 10. ** (5.745 - 0.770 * log10 (freq * 1000.)) # Jy
    dnu = 0.01 * (0.97 - 0.30 * log10 (freq)) # percent per yr.
    loss = (1 - dnu) ** (year - 1980.)

    return snu * loss

def initCasA (year):
    """Insert an entry for Cas A into the table of models. Need to
    specify the year of the observations to account for the time
    variation of Cas A's emission."""

    year = float (year)
    models['CasA'] = lambda f: CasA (f, year)


# Other models from Baars et al. 1977

def _makeGenericBaars (a, b, c, fmin, fmax):
    from numpy import log10, any

    def f (freq):
        if any (freq < fmin) or any (freq > fmax):
            raise Exception ('Going beyond frequency limits of model!')
        
        lf = log10 (freq)
        return 10.**(a + b * lf + c * lf**2)

    return f

def _addGenericBaars (src, a, b, c, fmin, fmax):
    models[src] = _makeGenericBaars (a, b, c, fmin, fmax)

# Data from Baars et al. 1977 Table 5

_addGenericBaars ('3c48', 2.345, 0.071, -0.138, 405., 15000.)
_addGenericBaars ('3c123', 2.921, -0.002, -0.124, 405., 15000.)
_addGenericBaars ('3c147', 1.766, 0.447, -0.184, 405., 15000.)
_addGenericBaars ('3c161', 1.633, 0.498, -0.194, 405., 10700.)
_addGenericBaars ('3c218', 4.497, -0.910, 0.0, 405., 10700.)
_addGenericBaars ('3c227', 3.460, -0.827, 0.0, 405, 15000.)
_addGenericBaars ('3c249.1', 1.230, 0.288, -0.176, 405., 15000.)
_addGenericBaars ('3c286', 1.480, 0.292, -0.124, 405., 15000.)
_addGenericBaars ('3c295', 1.485, 0.759, -0.255, 405., 15000.)
_addGenericBaars ('3c348', 4.963, -1.052, 0., 405., 10700.)
_addGenericBaars ('3c353', 2.944, -0.034, -0.109, 405., 10700.)
_addGenericBaars ('DR21', 1.81, -0.122, 0., 7000., 31000.)
_addGenericBaars ('NGC7027', 1.32, -0.127, 0., 10000., 31000.)

# Custom models from VLA data

def modelFromVLA (Lband, Cband):
    """Generate spectral model parameters from VLA calibrator
    table data. Lband is the L-band (20 cm) flux in Jy, Cband
    is the C-band (6 cm) flux in Jy.

    Returns (A, B), where the spectral model is

       log10 (Flux in Jy) = A * log10 (Freq in MHz) + B
    """

    import cgs
    from math import log10
    
    fL = log10 (cgs.c / 20 / 1e6)
    fC = log10 (cgs.c / 6 / 1e6)

    lL = log10 (Lband)
    lC = log10 (Cband)

    m = (lL - lC) / (fL - fC)

    return m, lL - m * fL

def funcFromVLA (Lband, Cband):
    A, B = modelFromVLA (Lband, Cband)
    from numpy import log10
    
    def f (freq):
        return 10.**(A * log10 (freq) + B)

    return f

def addFromVLA (src, Lband, Cband):
    """Add an entry into the models table for a source based on the
    Lband and Cband entries from the VLA catalog."""

    if src in models: raise Exception ('Already have a model for ' + src)
    models[src] = funcFromVLA (Lband, Cband)

# If we're executed as a program, print out a flux given a source
# name

def _usage ():
    from sys import stderr, argv, exit
    
    print >>stderr, """Usage: %s <source> <freq> [year]

Where:
  <source> is the source name (e.g., 3c348)
  <freq> is the observing frequency in MHz (e.g., 1420)
  [year] is the decimal year of the observation (e.g., 2007.8).
     Only needed if <source> is CasA.

Prints the flux in Jy of the specified calibrator at the
specified frequency.""" % argv[0]
    exit (0)
    
def _interactive ():
    from sys import argv, exit, stderr

    if len (argv) < 2: _usage ()

    source = argv[1]

    if source == 'CasA':
        if len (argv) != 4: _usage ()

        try:
            year = float (argv[3])
            initCasA (year)
        except Exception, e:
            print >>stderr, 'Unable to parse year \"%s\":' % argv[3], e
            exit (1)
    elif len (argv) != 3: _usage ()

    try:
        freq = float (argv[2])
    except Exception, e:
        print >>stderr, 'Unable to parse frequency \"%s\":' % argv[2], e
        exit (1)
        
    if source not in models:
        print >>stderr, 'Unknown source \"%s\". Known sources are:' % source
        print >>stderr, '   ', ', '.join (sorted (models.keys ()))
        exit (1)

    try:
        flux = models[source](freq)
        print '%lg' % (flux, )
        exit (0)
    except Exception, e:
        # Catch, e.g, going beyond frequency limits.
        print >>stderr, 'Error finding flux of %s at %f MHz:' % (source, freq), e
        exit (1)

if __name__ == '__main__':
    _interactive ()
