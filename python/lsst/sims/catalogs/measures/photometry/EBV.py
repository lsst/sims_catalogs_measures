import pyfits
import math
import numpy

def interp1D(z1 , z2, offset):
    """ 1D interpolation on a grid"""

    zPrime = (z2-z1)*offset + z1

    return zPrime

def calculateEbv(gLon, gLat, northMap, southMap, interp=False):
    """ For an array of Gal long, lat calculate E(B-V)"""
    ebv = numpy.zeros(len(gLon))
                      
    for i,lon in enumerate(gLon):
        if (gLat[i] <= 0.):
            ebv[i] = southMap.generateEbv(gLon[i],gLat[i],interpolate=interp)
        else:
            ebv[i] = northMap.generateEbv(gLon[i],gLat[i], interpolate=interp)

    return ebv
            
class EbvMap():
    '''Class  for describing a map of EBV

    Images are read in from a fits file and assume a ZEA projection
    '''
    def __init__(self):
        data = None
        
    def readMapFits(self, fileName):
        """ read a fits file containing the ebv data"""
        hdulist = pyfits.open(fileName)
        self.header = hdulist[0].header
        self.data = hdulist[0].data
        self.nr = self.data.shape[0]
        self.nc = self.data.shape[1]

        #read WCS information
        self.cd11 = self.header['CD1_1']
        self.cd22 = self.header['CD2_2']
        self.cd12 = 0.
        self.cd21 = 0.

        self.crpix1 = self.header['CRPIX1']
        self.crval1 = self.header['CRVAL1']

        self.crpix2 = self.header['CRPIX2']
        self.crval2 = self.header['CRVAL2']

        # read projection information
        self.nsgp = self.header['LAM_NSGP']
        self.scale = self.header['LAM_SCAL']
        self.lonpole = self.header['LONPOLE']

    def skyToXY(self, gLon, gLat):
        """ convert long, lat angles to pixel x y

        input angles are in radians but the conversion assumes radians
        """

        rad2deg= 180./math.pi
        
        # use the SFD approach to define xy pixel positions
        # ROTATION - Equn (4) - degenerate case 
        if (self.crval2 > 89.9999):
            theta = gLat*rad2deg
            phi = gLon*rad2deg + 180.0 + self.lonpole - self.crval1
        elif (self.crval2 < -89.9999):
            theta = -gLat*rad2deg
            phi = self.lonpole + self.crval1 - gLon*rad2deg
        else:    
            # Assume it's an NGP projection ... 
            theta = gLat*rad2deg
            phi = gLon*rad2deg + 180.0 + self.lonpole - self.crval1

        # Put phi in the range [0,360) degrees 
        phi = phi - 360.0 * math.floor(phi/360.0);

        # FORWARD MAP PROJECTION - Equn (26) 
        Rtheta = 2.0 * rad2deg * math.sin((0.5 / rad2deg) * (90.0 - theta));

        # Equns (10), (11) 
        xr = Rtheta * math.sin(phi / rad2deg);
        yr = - Rtheta * math.cos(phi / rad2deg);
    
        # SCALE FROM PHYSICAL UNITS - Equn (3) after inverting the matrix 
        denom = self.cd11 * self.cd22 - self.cd12 * self.cd21;
        x = (self.cd22 * xr - self.cd12 * yr) / denom + (self.crpix1 - 1.0);
        y = (self.cd11 * yr - self.cd21 * xr) / denom + (self.crpix2 - 1.0);

        return x,y

    def generateEbv(self, glon, glat, interpolate = False):
        """ Calculate EBV with option for interpolation"""

        # calculate pixel values
        x,y = self.skyToXY(glon, glat)

        ix = int(x + 0.5)
        iy = int(y + 0.5)

        #TODO check bounds        
        
        if (interpolate):
            xLow = interp1D(self.data[iy][ix], self.data[iy][ix+1], x - ix)
#            print xLow, self.data[iy][ix], self.data[iy][ix+1]

            xHigh = interp1D(self.data[iy+1][ix], self.data[iy+1][ix+1], x - ix)
#            print xHigh, self.data[iy+1][ix], self.data[iy+1][ix+1]

            ebvVal = interp1D(xLow, xHigh, y - iy)
        else:
            ebvVal = self.data[iy][ix]

        return ebvVal    
                        
    def skyToXYInt(self, gLong, gLat):
        x,y = self.skyToXY(gLong, gLat)
        ix = int(x+0.5)
        iy = int(y+0.5)

        return ix,iy

def main():
    glon = float(sys.argv[1])
    glat = float(sys.argv[2])

    map = EbvMap()
    map.readMapFits('SFD_dust_4096_sgp.fits')

    x,y = map.skyToXY(glon, glat)

    ebv = map.generateEbv(glon, glat)

    print ebv

    ebv = map.generateEbv(glon, glat, interpolate=True)

    print ebv

if __name__ == '__main__':
    main()