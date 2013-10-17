#include <stdlib.h>
#include <math.h>

/* Bring in the declarations for the string functions */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/* Include declaration for function at end of program */
#include <gurobi_c.h>

#if (defined(WIN32) || defined(_WIN32))
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif
static void
free_and_null (char **ptr);



/* This simple routine frees up the pointer *ptr, and sets *ptr to NULL */

static void
free_and_null (char **ptr)
{
  if ( *ptr != NULL ) {
    free (*ptr);
    *ptr = NULL;
  }
} /* END free_and_null */


/* The problem we are optimizing will have 2 rows, 3 columns,
   6 nonzeros, and 7 nonzeros in the quadratic coefficient matrix. */

int printfarray(const double * array, int numrows, int numcols, char * name) {
  int i,j;
  printf("%s\n", name);
  for (i = 0; i < numrows; ++i) {
    for (j = 0; j < numcols; ++j) {
      printf("%f\t", array[i * numcols + j]);
    }
    printf("\n");
  }
  return 0;
}
int printiarray(const int * array, int numrows, int numcols, char * name) {
  int i,j;
  for (i = 0; i < numrows; ++i) {
    for (j = 0; j < numcols; ++j) {
      printf("%d\t", array[i * numcols + j]);
    }
    printf("\n");
  }

  return 0;
}

EXPORT int fit(const double * X_p, const double * Yl_p, double* w, int postags, int numSamples, int numFeatures, double C, double epsilon,
        int numBoxConstraints, double * boxValues, const int64_t * boxIndices, const double * boxMatrix)
{
  int i,j,k;
  GRBenv *     env = NULL;
  GRBenv *    aenv = NULL;
  GRBmodel *   model = NULL;
  int status;
  char probname[] = "Testproblem";

  int numrows = postags + numSamples;
  int numcols = numFeatures + 1 + numrows;
  int nnzcol = numFeatures + 2;
  int numEntries = nnzcol * numrows;

  char *sense = (char*) malloc(numrows * sizeof(char));
  double *lb = (double*) malloc(numcols * sizeof(double));
  double *obj = (double*) malloc(numcols * sizeof(double));
  double *rhs = (double*) malloc(numrows * sizeof(double));
  double *tagarray = (double*) malloc(numrows * sizeof(double));

  int      *matbeg = (int*) malloc(numrows * sizeof(int));
  int      *matind = (int*) malloc(numEntries * sizeof(int));
  double   *matval = (double* ) malloc(numEntries * sizeof(double));
  int * qrow = (int*) malloc((numcols + 2 * numBoxConstraints) * sizeof(int));
  int * qcol = (int*) malloc((numcols + 2 * numBoxConstraints) * sizeof(int));
  double   *qsepvec = (double*) malloc((numcols + 2 * numBoxConstraints) * sizeof(double));

  int       numBoxSamples = 0;
  double   *dens = NULL;
  double   *boxConstraints = NULL;
  int      *boxrmatbeg = NULL;
  int      *boxrmatind = NULL;
  char     *boxSense = NULL;
  int      *hmatbeg = NULL;
  int      *hmatind = NULL;
  double   *hmatval = NULL;
  char     *hSense = NULL;
  status = GRBloadenv(&env, NULL);
  if ( status ) {
    fprintf (stderr,
             "Failure to create CPLEX environment, error %d.\n", status);
    goto QUIT;
  }

  if (sense == NULL || lb == NULL || obj == NULL 
      || rhs == NULL || tagarray == NULL || qsepvec == NULL) {
    status = 1;
    goto QUIT;
  }


  for (i = 0; i < postags; ++i) {
    tagarray[i] = 1;
    sense[i] = GRB_GREATER_EQUAL;
  }
  for (i = postags; i < numrows; ++i) {
    tagarray[i] = -1;
    sense[i] = GRB_LESS_EQUAL;
  }
  for (i = 0; i < postags; ++i) {
    rhs[i] = Yl_p[i] - tagarray[i] * epsilon ;
  }
  for (i = postags; i < numrows; ++i) {
    rhs[i] = Yl_p[i - postags] - tagarray[i] * epsilon ;
  }
  for (i = 0; i < numFeatures + 1; ++i) {
    lb[i] = -GRB_INFINITY;
  }

  for (i = 0; i < postags; ++i) {
    for (j = 0; j < numFeatures; ++j) {
      matind[i * nnzcol + j] = j;
      matval[i * nnzcol + j] = X_p[i * numFeatures + j];
    }
  }
  for (i = postags; i < numrows; ++i) {
    for (j = 0; j < numFeatures; ++j) {
      matind[i * nnzcol + j] = j;
      matval[i * nnzcol + j] = X_p[(i - postags) * numFeatures + j];
    }
  }

  for (i = 0; i < numrows; ++i) {
    matbeg[i] = i * nnzcol;
    matind[i * nnzcol + numFeatures] = numFeatures;
    matval[i * nnzcol + numFeatures] = 1;
    matind[i * nnzcol + numFeatures+1] = i + (numFeatures + 1);
    matval[i * nnzcol + numFeatures+1] = tagarray[i];
  }


  for (i = 0; i < numFeatures; ++i){
    qsepvec[i] = 1;
  }
  qsepvec[numFeatures] = 0;
  for (i = numFeatures + 1; i < numcols; ++i){
    qsepvec[i] = 2 * C;
  }
  for (i = 0; i < numcols + 2 * numBoxConstraints; ++i) {
    qrow[i] = i;
    qcol[i] = i;

  }

  status = GRBnewmodel(env, &model, "Counting", numcols + 2 * numBoxConstraints, NULL, NULL, NULL, NULL, NULL);
  if (status) goto QUIT;
  status = GRBaddconstrs (model, numrows, numEntries,
                          matbeg, matind, matval, sense, rhs, NULL);
  if (status) goto QUIT;
  status = GRBsetdblattrarray(model, "lb", 0, numFeatures+1, lb);
  if (status) goto QUIT;

  aenv = GRBgetenv(model);
  if (!aenv) goto QUIT;
  
  status = GRBsetintparam(aenv, "OutputFlag", 0);
  if (status) goto QUIT;
  status = GRBaddqpterms(model, numcols, qrow, qcol, qsepvec);
  if (status) goto QUIT;
  status = GRBupdatemodel(model);
  status = GRBoptimize(model);
  if (status) goto QUIT;
  /*status = GRBwrite(model, "qp.lp");*/
  status = GRBgetdblattrarray(model, GRB_DBL_ATTR_X, 0, numFeatures+1, w);
  if (status) goto QUIT;



  if (numBoxConstraints > 0) {
    numBoxSamples = (int) boxIndices[numBoxConstraints];

    dens = (double*) malloc(numBoxSamples * sizeof(double));
    boxConstraints = (double*) calloc(numBoxConstraints * (numFeatures + 2), sizeof(double));
    boxrmatbeg = (int*) malloc(numBoxConstraints * sizeof(int));
    boxrmatind = (int*) malloc(numBoxConstraints * (numFeatures + 2) * sizeof(int));
    boxSense = (char*) malloc(numBoxConstraints * sizeof(char));

    hmatbeg = (int*) malloc(numBoxSamples * sizeof(int));
    hmatind = (int*) malloc(numBoxSamples * (numFeatures + 1) * sizeof(int));
    hmatval = (double* ) malloc(numBoxSamples * (numFeatures + 1) * sizeof(double));
    hSense = (char* ) malloc(numBoxSamples * sizeof(char));

    if (dens == NULL || boxConstraints == NULL || boxrmatbeg == NULL || boxrmatind == NULL
        || boxSense == NULL) {
      status = 1;
      goto QUIT;
    }
    if (hmatbeg == NULL || hmatind == NULL || hmatval == NULL || hSense == NULL) {
      status = 1;
      goto QUIT;
    }




    for (i = 0; i < numBoxSamples; ++i) {
      dens[i] = w[numFeatures];
      for (j = 0; j < numFeatures; ++j) {
        dens[i] += boxMatrix[i * numFeatures + j] * w[j];
      }
    } 
    for (i = 0; i < numBoxSamples; ++i) {
      if (dens[i] > 0){
        dens[i] = 1;
      }
      else {
        dens[i] = 0;
      }
    }

    for (k = 0; k < numBoxConstraints; ++k) {
      boxrmatbeg[k] = k * (numFeatures + 2);
      for (i = (int) boxIndices[k]; i < boxIndices[k + 1]; ++i){
        for (j = 0; j < numFeatures; ++j){
          boxConstraints[k * (numFeatures + 2) + j]  += dens[i] * boxMatrix[i * numFeatures + j];
        }
        boxConstraints[k * (numFeatures + 2) + numFeatures] += dens[i];
      }
    }
    for (i = 0; i < numBoxConstraints; ++i) {
      for (j = 0; j < numFeatures + 1; ++j) {
        boxrmatind[i * (numFeatures + 2) + j] = j;
      } 
      boxrmatind[i * (numFeatures + 2) + numFeatures + 1] = numcols + i;
    }

    for (i = 0; i < numBoxConstraints; ++i) { 
      boxSense[i] = GRB_LESS_EQUAL;
    }
    for (i = 0; i < numBoxConstraints; ++i) {
      boxConstraints[i * (numFeatures + 2) + numFeatures+1] = - 1;
    }
    
    status = GRBaddconstrs (model, numBoxConstraints, numBoxConstraints * (numFeatures + 2),
                            boxrmatbeg, boxrmatind, boxConstraints, boxSense, boxValues, NULL);
    
    
    for (i = 0; i < numBoxConstraints; ++i) {
      boxrmatind[i * (numFeatures + 2) + numFeatures + 1] = numcols + numBoxConstraints + i;
    }

    for (i = 0; i < numBoxConstraints; ++i) { 
      boxSense[i] = GRB_GREATER_EQUAL;
    }
    for (i = 0; i < numBoxConstraints; ++i) {
      boxConstraints[i * (numFeatures + 2) + numFeatures+1] = + 1;
    }
    status = GRBaddconstrs (model, numBoxConstraints, numBoxConstraints * (numFeatures + 2),
                            boxrmatbeg, boxrmatind, boxConstraints, boxSense, boxValues, NULL);

    for (i = 0; i < numBoxConstraints; ++i) {
      qsepvec[numcols + i] = 2 * C / (boxIndices[i + 1] - boxIndices[i]);
      qsepvec[numcols + i + numBoxConstraints] = 2 * C / (boxIndices[i + 1] - boxIndices[i]);
    }


    for (i = 0; i < numBoxSamples; ++i) {
      hmatbeg[i] = i * (numFeatures + 1);
      for (j = 0; j < numFeatures; ++j) {
        hmatind[i * (numFeatures + 1) + j] = j;
        hmatval[i * (numFeatures + 1) + j] = boxMatrix[i * numFeatures + j];
      }
      hmatind[i * (numFeatures + 1) + numFeatures] = numFeatures;
      hmatval[i * (numFeatures + 1) + numFeatures] = 1;

      if (dens[i] == 0){
        hSense[i]  = GRB_LESS_EQUAL;
      }
      else {
        hSense[i] = GRB_GREATER_EQUAL;
      }
    }
    status = GRBaddconstrs(model, numBoxSamples, numBoxSamples * (numFeatures + 1),
                           hmatbeg, hmatind, hmatval, hSense, NULL, NULL);


    status = GRBaddqpterms(model, 2 * numBoxConstraints, qrow + numcols, qcol + numcols, qsepvec + numcols);
    if (status) goto QUIT;
    status = GRBupdatemodel(model);
    status = GRBoptimize(model);
    if (status) goto QUIT;
    status = GRBwrite(model, "qp.lp");
    status = GRBgetdblattrarray(model, GRB_DBL_ATTR_X, 0, numFeatures+1, w);
  if (status) goto QUIT;
  }

QUIT:

  free_and_null ((char **) &obj);
  free_and_null ((char **) &rhs);
  free_and_null ((char **) &sense);
  free_and_null ((char **) &tagarray);
  free_and_null ((char **) &lb);
  free_and_null ((char **) &matbeg);
  free_and_null ((char **) &matind);
  free_and_null ((char **) &matval);
  free_and_null ((char **) &qrow);
  free_and_null ((char **) &qcol);
  free_and_null ((char **) &qsepvec);

  free_and_null ((char **) &dens);
  free_and_null ((char **) &boxConstraints);
  free_and_null ((char **) &boxrmatbeg);
  free_and_null ((char **) &boxrmatind);

  free_and_null ((char **) &hmatbeg);
  free_and_null ((char **) &hmatind);
  free_and_null ((char **) &hmatval);
  free_and_null ((char **) &hSense);
  if (status) {
    printf("ERROR: %s\n", GRBgeterrormsg(env));
  }
  GRBfreemodel(model);
  GRBfreeenv(env);
  return (status);

}



/* This function fills in the data structures for the quadratic program:

   Maximize
obj: x1 + 2 x2 + 3 x3
- 0.5 ( 33x1*x1 + 22*x2*x2 + 11*x3*x3
-  12*x1*x2 - 23*x2*x3 )
Subject To
c1: - x1 + x2 + x3 <= 20
c2: x1 - 3 x2 + x3 <= 30
Bounds
0 <= x1 <= 40
End
*/

