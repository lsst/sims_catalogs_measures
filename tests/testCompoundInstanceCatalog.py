from __future__ import with_statement
import os
import numpy
import unittest
import lsst.utils.tests as utilsTests
from lsst.utils import getPackageDir
from lsst.sims.utils import ObservationMetaData
from lsst.sims.catalogs.generation.db import fileDBObject, CatalogDBObject
from lsst.sims.catalogs.measures.instance import InstanceCatalog, \
                                                 CompoundInstanceCatalog

class table1DB1(CatalogDBObject):
    tableid = 'table1'
    objid = 'table1DB1'
    idColKey = 'id'
    raColName = 'ra'
    decColName = 'dec'

    columns = [('raJ2000','ra'),
               ('decJ2000','dec'),
               ('mag', None, numpy.float),
               ('dmag', None, numpy.float),
               ('dra', None, numpy.float),
               ('ddec', None, numpy.float)]


class table1DB2(CatalogDBObject):
    tableid = 'table1'
    objid = 'table1DB2'
    idColKey = 'id'
    raColName = 'ra'
    decColName = 'dec'

    columns = [('raJ2000', '2.0*ra'),
               ('decJ2000', '2.0*dec'),
               ('mag', None, numpy.float),
               ('dmag', None, numpy.float),
               ('dra', None, numpy.float),
               ('ddec', None, numpy.float)]


class table2DB(CatalogDBObject):
    tableid = 'table2'
    objid = 'table2DB'
    idColKey = 'id'
    raColName = 'ra'
    decColName = 'dec'

    columns = [('raJ2000', 'ra'),
               ('decJ2000', 'dec'),
               ('mag', None, numpy.float)]


class Cat1(InstanceCatalog):
    delimiter = ' '
    default_formats = {'f':'%.12f'}
    column_outputs = ['testId', 'raObs', 'decObs', 'final_mag']

    def get_testId(self):
        return self.column_by_name('id')+1000

    def get_raObs(self):
        return self.column_by_name('raJ2000')

    def get_decObs(self):
        return self.column_by_name('decJ2000')

    def get_final_mag(self):
        return self.column_by_name('mag') + self.column_by_name('dmag')


class Cat2(Cat1):

    def get_testId(self):
        return self.column_by_name('id')+2000

    def get_raObs(self):
        return self.column_by_name('raJ2000') + self.column_by_name('dra')

    def get_decObs(self):
        return self.column_by_name('decJ2000') + self.column_by_name('ddec')


class Cat3(Cat1):

    def get_testId(self):
        return self.column_by_name('id')+3000

    def get_final_mag(self):
        return self.column_by_name('mag')


class CompoundCatalogTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baseDir = os.path.join(getPackageDir('sims_catalogs_measures'),
                               'tests', 'scratchSpace')

        cls.table1FileName = os.path.join(cls.baseDir, 'compound_table1.txt')
        cls.table2FileName = os.path.join(cls.baseDir, 'compound_table2.txt')

        if os.path.exists(cls.table1FileName):
            os.unlink(cls.table1FileName)
        if os.path.exists(cls.table2FileName):
            os.unlink(cls.table2FileName)

        dtype1 = numpy.dtype([
                           ('ra', numpy.float),
                           ('dec', numpy.float),
                           ('mag', numpy.float),
                           ('dmag', numpy.float),
                           ('dra', numpy.float),
                           ('ddec', numpy.float)
                           ])

        dbDtype1 = numpy.dtype([
                           ('id', numpy.int),
                           ('ra', numpy.float),
                           ('dec', numpy.float),
                           ('mag', numpy.float),
                           ('dmag', numpy.float),
                           ('dra', numpy.float),
                           ('ddec', numpy.float)
                           ])

        nPts = 100
        numpy.random.seed(42)
        raList = numpy.random.random_sample(nPts)*360.0
        decList = numpy.random.random_sample(nPts)*180.0-90.0
        magList = numpy.random.random_sample(nPts)*10.0+15.0
        dmagList = numpy.random.random_sample(nPts)*10.0 - 5.0
        draList = numpy.random.random_sample(nPts)*5.0 - 2.5
        ddecList = numpy.random.random_sample(nPts)*(-2.0) - 4.0

        cls.table1Control = numpy.rec.fromrecords([
                                                  (r, d, mm, dm, dr, dd) \
                                                  for r, d, mm, dm, dr, dd \
                                                  in zip(raList, decList,
                                                         magList, dmagList,
                                                         draList, ddecList)],
                                                  dtype=dtype1
                                                  )

        with open(cls.table1FileName, 'w') as output:
            output.write("# id ra dec mag dmag dra ddec\n")
            for ix, (r, d, mm, dm, dr, dd) in \
            enumerate(zip(raList, decList, magList, dmagList, draList, ddecList)):

                output.write('%d %.12f %.12f %.12f %.12f %.12f %.12f\n' \
                             % (ix, r, d, mm, dm, dr, dd))


        dtype2 = numpy.dtype([
                            ('ra', numpy.float),
                            ('dec', numpy.float),
                            ('mag', numpy.float)
                            ])

        dbDtype2 = numpy.dtype([
                            ('id', numpy.int),
                            ('ra', numpy.float),
                            ('dec', numpy.float),
                            ('mag', numpy.float)
                            ])

        ra2List = numpy.random.random_sample(nPts)*360.0
        dec2List = numpy.random.random_sample(nPts)*180.0-90.0
        mag2List = numpy.random.random_sample(nPts)*(-3.0)-7.0

        cls.table2Control = numpy.rec.fromrecords([
                                                  (r, d, m) \
                                                  for r, d, m in \
                                                  zip(ra2List, dec2List, mag2List)
                                                  ], dtype=dtype2)

        with open(cls.table2FileName, 'w') as output:
            output.write('# id ra dec mag\n')
            for ix, (r, d, m) in enumerate(zip(ra2List, dec2List, mag2List)):
                output.write('%d %.12f %.12f %.12f\n' % (ix, r, d, m))

        cls.dbName = os.path.join(cls.baseDir, 'compound_db.db')
        if os.path.exists(cls.dbName):
            os.unlink(cls.dbName)

        fdbo = fileDBObject(cls.table1FileName, runtable='table1',
                            database=cls.dbName, dtype=dbDtype1,
                            idColKey='id')

        fdbo = fileDBObject(cls.table2FileName, runtable='table2',
                            database=cls.dbName, dtype=dbDtype2,
                            idColKey='id')


    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.table1FileName):
            os.unlink(cls.table1FileName)
        if os.path.exists(cls.table2FileName):
            os.unlink(cls.table2FileName)
        if os.path.exists(cls.dbName):
            os.unlink(cls.dbName)


    def testCompoundCatalog(self):
        fileName = os.path.join(self.baseDir, 'simplest_compound_catalog.txt')
        db1 = table1DB1(database=self.dbName, driver='sqlite')
        db2 = table1DB2(database=self.dbName, driver='sqlite')
        db3 = table2DB(database=self.dbName, driver='sqlite')

        cat1 = Cat1(db1)
        cat2 = Cat2(db2)
        cat3 = Cat3(db3)

        compoundCat = CompoundInstanceCatalog([cat1, cat2, cat3])

        compoundCat.write_catalog(fileName)

        self.assertTrue(len(compoundCat._dbObjectGroupList)==2)
        self.assertTrue(len(compoundCat._dbObjectGroupList[0])==2)
        self.assertTrue(len(compoundCat._dbObjectGroupList[1])==1)
        self.assertTrue(0 in compoundCat._dbObjectGroupList[0])
        self.assertTrue(1 in compoundCat._dbObjectGroupList[0])
        self.assertTrue(2 in compoundCat._dbObjectGroupList[1])

        dtype=numpy.dtype([
                          ('id', numpy.int),
                          ('raObs', numpy.float),
                          ('decObs', numpy.float),
                          ('final_mag', numpy.float)
                          ])

        testData = numpy.genfromtxt(fileName, dtype=dtype)

        for line in testData:
            if line[0]<2000:
                ix = line[0]-1000
                self.assertAlmostEqual(line[1], self.table1Control['ra'][ix], 6)
                self.assertAlmostEqual(line[2], self.table1Control['dec'][ix], 6)
                self.assertAlmostEqual(line[3], self.table1Control['mag'][ix]+self.table1Control['dmag'][ix], 6)
            elif line[0]<3000:
                ix = line[0]-2000
                self.assertAlmostEqual(line[1], 2.0*self.table1Control['ra'][ix]+self.table1Control['dra'][ix], 6)
                self.assertAlmostEqual(line[2], 2.0*self.table1Control['dec'][ix]+self.table1Control['ddec'][ix], 6)
                self.assertAlmostEqual(line[3], self.table1Control['mag'][ix]+self.table1Control['dmag'][ix], 6)
            else:
                ix = line[0]-3000
                self.assertAlmostEqual(line[1], self.table2Control['ra'][ix], 6)
                self.assertAlmostEqual(line[2], self.table2Control['dec'][ix], 6)
                self.assertAlmostEqual(line[3], self.table2Control['mag'][ix], 6)

        if os.path.exists(fileName):
            os.unlink(fileName)



    def testObservationMetaData(self):
        """
        Test that CompoundInstanceCatalog handles ObservationMetaData
        properly
        """
        fileName = os.path.join(self.baseDir, 'compound_obs_metadata_test_cat.txt')
        obs = ObservationMetaData(unrefractedRA = 180.0,
                                  unrefractedDec = 0.0,
                                  boundType = 'box',
                                  boundLength = (80.0, 25.0))

        db1 = table1DB1(database=self.dbName, driver='sqlite')
        db2 = table1DB2(database=self.dbName, driver='sqlite')
        db3 = table2DB(database=self.dbName, driver='sqlite')
        cat1 = Cat1(db1)
        cat2 = Cat2(db2)
        cat3 = Cat3(db3)

        compoundCat = CompoundInstanceCatalog([cat1, cat2, cat3],
                                              obs_metadata=obs)

        compoundCat.write_catalog(fileName)
        dtype=numpy.dtype([
                          ('id', numpy.int),
                          ('raObs', numpy.float),
                          ('decObs', numpy.float),
                          ('final_mag', numpy.float)
                          ])

        testData = numpy.genfromtxt(fileName, dtype=dtype)

        table1_good_rows = []
        table2_good_rows = []
        for line in testData:
            if line[0]<2000:
                ix = line[0]-1000
                if ix not in table1_good_rows:
                    table1_good_rows.append(ix)
                self.assertAlmostEqual(line[1], self.table1Control['ra'][ix], 6)
                self.assertAlmostEqual(line[2], self.table1Control['dec'][ix], 6)
                self.assertAlmostEqual(line[3], self.table1Control['mag'][ix]+self.table1Control['dmag'][ix], 6)
                self.assertTrue(self.table1Control['ra'][ix]>100.0 and self.table1Control['ra'][ix]<260.0)
                self.assertTrue(self.table1Control['dec'][ix]>-25.0 and self.table1Control['dec'][ix]<25.0)
            elif line[0]<3000:
                ix = line[0]-2000
                if ix not in table1_good_rows:
                    table1_good_rows.append(ix)
                self.assertAlmostEqual(line[1], 2.0*self.table1Control['ra'][ix]+self.table1Control['dra'][ix], 6)
                self.assertAlmostEqual(line[2], 2.0*self.table1Control['dec'][ix]+self.table1Control['ddec'][ix], 6)
                self.assertAlmostEqual(line[3], self.table1Control['mag'][ix]+self.table1Control['dmag'][ix], 6)
                self.assertTrue(self.table1Control['ra'][ix]>100.0 and self.table1Control['ra'][ix]<260.0)
                self.assertTrue(self.table1Control['dec'][ix]>-25.0 and self.table1Control['dec'][ix]<25.0)
            else:
                ix = line[0]-3000
                if ix not in table2_good_rows:
                    table2_good_rows.append(ix)
                self.assertAlmostEqual(line[1], self.table2Control['ra'][ix], 6)
                self.assertAlmostEqual(line[2], self.table2Control['dec'][ix], 6)
                self.assertAlmostEqual(line[3], self.table2Control['mag'][ix], 6)
                self.assertTrue(self.table2Control['ra'][ix]>100.0 and self.table2Control['ra'][ix]<260.0)
                self.assertTrue(self.table2Control['dec'][ix]>-25.0 and self.table2Control['dec'][ix]<25.0)


        table1_bad_rows = [ix for ix in range(self.table1Control.shape[0]) if ix not in table1_good_rows]
        table2_bad_rows = [ix for ix in range(self.table2Control.shape[0]) if ix not in table2_good_rows]


        in_bounds = [rr>100.0 and rr<260.0 and dd>-25.0 and dd<25.0 \
                     for rr, dd in zip(self.table1Control['ra'][table1_bad_rows],
                                       self.table1Control['dec'][table1_bad_rows])]

        for ix, switch in zip(table1_bad_rows, in_bounds):
            if switch:
                print self.table1Control['ra'][ix], self.table1Control['dec'][ix],ix,ix in table1_good_rows

        self.assertFalse(True in in_bounds)

        in_bounds = [rr>100.0 and rr<260.0 and dd>-25.0 and dd<25.0 \
                     for rr, dd in zip(self.table2Control['ra'][table2_bad_rows],
                                           self.table2Control['dec'][table2_bad_rows])]


        self.assertFalse(True in in_bounds)

        self.assertTrue(len(table1_good_rows)>0)
        self.assertTrue(len(table2_good_rows)>0)
        self.assertTrue(len(table1_bad_rows)>0)
        self.assertTrue(len(table2_bad_rows)>0)
        self.assertEqual(len(table1_good_rows)+len(table1_bad_rows), self.table1Control.shape[0])
        self.assertEqual(len(table2_good_rows)+len(table2_bad_rows), self.table2Control.shape[0])


def suite():
    """Returns a suite containing all the test cases in this module."""
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(CompoundCatalogTest)

    return unittest.TestSuite(suites)

def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
