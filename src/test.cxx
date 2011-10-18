#include "histogram.hxx"

using namespace vigra;







void test1()
{
	double rawfeatures [] =
	{
		0.5,  0.3, 0.4, 0.6, 1,
		0.33, 0.2, 0.6, 0.9, 0,

		0.5,  0.7, 0.6, 0.4, 0,
		0.77, 0.8, 0.4, 0.1, 1

	};


	double rawdesired [] =
	{
		0,  1,  1,  0, 0,
		1,  1,  0,  0, 1,

		1,  0,	0,  1, 1,
		0,  0,  1,  1, 0,

		0,  0,  0,  1, 1,
		0,  0,  1,  1, 0,

		1,  1,  1,  0, 0,
		1,  1,  0,  0, 1,


	};


	typedef MultiArrayShape<3>::type Shp;
	MultiArrayView<3, double> features(Shp(5, 2,2), rawfeatures);

	MultiArrayView<3, double> desired(Shp(5, 2,2), rawdesired);



	int nbin=2;

	MultiArray<3, double> res(Shp(5,2,4));

	histogram2D(features,nbin,res);


	for(int k=0;k<4;k++)
		{
		for(int j=0;j<2;j++)

			{
			for(int i=0;i<5;i++)
				std::cerr << res(i,j,k) << " , " ;
			std::cerr<< std::endl;
			}
		std::cerr<< std::endl;
		}


	for(int k=0;k<4;k++)
			for(int j=0;j<2;j++)
				for(int i=0;i<5;i++)
					if(res(i,j,k)!=desired(i,j,k))
						{
						std::cerr << "res " << res(i,j,k) << " des " << desired(i,j,k)
								<< " i " << i << " j " << j << " k " << k << std::endl;
						throw std::runtime_error("");

						}


}

void test2()
{
        double rawfeatures [] =
        {
                0.5,  0.33, 0.45, 0.6, 1,
                0.33, 0.2, 0.61, 0.9, 0,

                0.51,  0.7, 0.61, 0.44, 0.11,
                0.77, 0.8, 0.42, 0.12, 1

        };


        double rawdesiredOH [] =
        {
            0,  0,  0,  0, 0,
            0,  1,  0,  0, 1,

            0,  1,  1,  0, 0,
            1,  1,  0,  0, 0,

            1,  1,  1,  1, 0,
            1,  0,  1,  0, 0,

            0,  0,  0,  1, 0,
            0,  0,  1,  0, 0,

            0,  0,  0,  0, 1,
            0,  0,  0,  1, 0,

            0,  0,  0,  0, 1,
            0,  0,  0,  1, 0,

            0,  0,  0,  1, 1,
            0,  0,  1,  1, 0,

            1,  1,  1,  1, 0,
            0,  0,  1,  0, 0,

            1,  1,  1,  0, 0,
            1,  1,  0,  0, 0,

            0,  0,  0,  0, 0,
            1,  1,  0,  0, 1,

        };

        double rawdesiredIOH [] =
        {
            0,  0,  0,  0, 0,
            0,  1,  1,  1, 2,

            0,  1,  2,  2, 2,
            1,  3,  4,  4, 4,

            1,  2,  3,  4, 4,
            2,  3,  5,  6, 6,

            0,  0,  0,  1, 1,
            0,  0,  1,  2, 2,

            0,  0,  0,  0, 1,
            0,  0,  0,  1, 2,

            0,  0,  0,  0, 1,
            0,  0,  0,  1, 2,

            0,  0,  0,  1, 2,
            0,  0,  1,  3, 4,

            1,  2,  3,  4, 4,
            1,  2,  4,  5, 5,

            1,  2,  3,  3, 3,
            2,  4,  5,  5, 5,

            0,  0,  0,  0, 0,
            1,  2,  2,  2, 3,

        };

        //lower border doesn't count to bin, only upper border
        //should be the other way around
        double rawdesiredH [] =
        {
                0,  0,  0,  0, 0,
                0,  1,  0,  0, 1,

                0,  1,	0,  0, 0,
                1,  0,  0,  0, 0,

                1,  0,  1,  1, 0,
                0,  0,  0,  0, 0,

                0,  0,  0,  0, 0,
                0,  0,  1,  0, 0,

                0,  0,  0,  0, 1,
                0,  0,  0,  1, 0,

                0,  0,	0,  0, 1,
                0,  0,  0,  1, 0,

                0,  0,  0,  0, 0,
                0,  0,  0,  0, 0,

                1,  0,  0,  1, 0,
                0,  0,  1,  0, 0,

                0,  1,  1,  0, 0,
                1,  1,  0,  0, 0,

                0,  0,	0,  0, 0,
                0,  0,  0,  0, 1,

        };


        double rawdesiredIH [] =
        {
                0,  0,  0,  0, 0,
                0,  1,  1,  1, 2,

                0,  1,	1,  1, 1,
                1,  2,  2,  2, 2,

                1,  1,  2,  3, 3,
                1,  1,  2,  3, 3,

                0,  0,  0,  0, 0,
                0,  0,  1,  1, 1,

                0,  0,  0,  0, 1,
                0,  0,  0,  1, 2,

                0,  0,	0,  0, 1,
                0,  0,  0,  1, 2,

                0,  0,  0,  0, 0,
                0,  0,  0,  0, 0,

                1,  1,  1,  2, 2,
                1,  1,  2,  3, 3,

                0,  1,  2,  2, 2,
                1,  3,  4,  4, 4,

                0,  0,	0,  0, 0,
                0,  0,  0,  0, 1,

        };





        typedef MultiArrayShape<3>::type Shp;
        MultiArrayView<3, double> features(Shp(5, 2,2), rawfeatures);

        MultiArrayView<3, double> desiredH(Shp(5, 2,10), rawdesiredH);
        MultiArrayView<3, double> desiredOH(Shp(5, 2, 10), rawdesiredOH);
        MultiArrayView<3, double> desiredIH(Shp(5, 2,10), rawdesiredIH);
        MultiArrayView<3, double> desiredIOH(Shp(5, 2,10), rawdesiredIOH);



        int nbin=5;

        MultiArray<3, double> resIH(Shp(5,2,10));
        MultiArray<3, double> resH(Shp(5,2,10));
        MultiArray<3, double> resOH(Shp(5,2,10));
        MultiArray<3, double> resO2H(Shp(5,2,10));
        MultiArray<3, double> resIOH(Shp(5,2,10));

        integralHistogram2D(features,nbin,resIH);
        histogram2D(features,nbin,resH);
        float f = 0.5;
        overlappingHistogram2D(features,nbin,f,resOH);
        overlappingWeightLinHistogram2D(features,nbin,f,resO2H);
        integralOverlappingHistogram2D(features,nbin,f,resIOH);






//        for(int k=0;k<4;k++)
//        {
//                        for(int j=0;j<2;j++)
//                        {
//                                for(int i=0;i<5;i++)
//
//                                    {
//                                      std::cerr << "res " << res(i,j,k) << " des " << desired(i,j,k)
//                                                << " i " << i << " j " << j << " k " << k << std::endl;
//
//
//                                  }
//                          std::cerr << std::endl;
//                          }
//          std::cerr << std::endl;
//        }
//
//
//
//        std::cerr << "WWWWWWWWWWWWW" << std::endl;

        std::cerr << "Histogramm" << std::endl;
        for(int k=0;k<10;k++)
                {
                for(int j=0;j<2;j++)

                        {
                        for(int i=0;i<5;i++)
                                std::cerr << resH(i,j,k) << " , " ;
                        std::cerr<< std::endl;
                        }
                std::cerr<< std::endl;
                }

        for(int k=0;k<10;k++)
                        for(int j=0;j<2;j++)
                                for(int i=0;i<5;i++)
                                        if(resH(i,j,k)!=desiredH(i,j,k))
                                                {
                                                std::cerr << "res " << resH(i,j,k) << " des " << desiredH(i,j,k)
                                                                << " i " << i << " j " << j << " k " << k << std::endl;
                                                throw std::runtime_error("");

                                                }

        std::cerr << "######################" << std::endl;

        std::cerr << "integralHistogramm" << std::endl;
        for(int k=0;k<10;k++)
                {
                for(int j=0;j<2;j++)

                        {
                        for(int i=0;i<5;i++)
                                std::cerr << resIH(i,j,k) << " , " ;
                        std::cerr<< std::endl;
                        }
                std::cerr<< std::endl;
                }


        for(int k=0;k<10;k++)
                        for(int j=0;j<2;j++)
                                for(int i=0;i<5;i++)
                                        if(resIH(i,j,k)!=desiredIH(i,j,k))
                                                {
                                                std::cerr << "res " << resIH(i,j,k) << " des " << desiredIH(i,j,k)
                                                                << " i " << i << " j " << j << " k " << k << std::endl;
                                                throw std::runtime_error("");

                                                }

        std::cerr << "######################" << std::endl;

        std::cerr << "overlappingHistogram" << std::endl;
        for(int k=0;k<10;k++)
                {
                for(int j=0;j<2;j++)

                        {
                        for(int i=0;i<5;i++)
                                std::cerr << resOH(i,j,k) << " , " ;
                        std::cerr<< std::endl;
                        }
                std::cerr<< std::endl;
                }

        for(int k=0;k<10;k++)
                        for(int j=0;j<2;j++)
                                for(int i=0;i<5;i++)
                                        if(resOH(i,j,k)!=desiredOH(i,j,k))
                                                {
                                                std::cerr << "res " << resOH(i,j,k) << " des " << desiredOH(i,j,k)
                                                                << " i " << i << " j " << j << " k " << k << std::endl;
                                                throw std::runtime_error("");

                                                }

        std::cerr << "######################" << std::endl;


        std::cerr << "overlapping2Histogram" << std::endl;
        for(int k=0;k<10;k++)
                {
                for(int j=0;j<2;j++)

                        {
                        for(int i=0;i<5;i++)
                                std::cerr << resO2H(i,j,k) << " , " ;
                        std::cerr<< std::endl;
                        }
                std::cerr<< std::endl;
                }

        std::cerr << "######################" << std::endl;

        std::cerr << "integralOverlappingHistogram" << std::endl;
        for(int k=0;k<10;k++)
                {
                for(int j=0;j<2;j++)

                        {
                        for(int i=0;i<5;i++)
                                std::cerr << resIOH(i,j,k) << " , " ;
                        std::cerr<< std::endl;
                        }
                std::cerr<< std::endl;
                }

        for(int k=0;k<10;k++)
                        for(int j=0;j<2;j++)
                                for(int i=0;i<5;i++)
                                        if(resIOH(i,j,k)!=desiredIOH(i,j,k))
                                                {
                                                std::cerr << "res " << resIOH(i,j,k) << " des " << desiredIOH(i,j,k)
                                                                << " i " << i << " j " << j << " k " << k << std::endl;
                                                throw std::runtime_error("");

                                                }

        std::cerr << "######################" << std::endl;





}


int main()
{
        //test1();
        test2();

	return 0;
}
