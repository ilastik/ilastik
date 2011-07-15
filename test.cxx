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




int main()
{
	test1();


	return 0;
}
