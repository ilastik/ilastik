#include <ilcplex/cpxconst.h>

int concatenate(int x, int y) {
  int power = 10;
  if (y == 0) return x;
  while(y >= power)
    power *= 10;
  return x * power + y;        
}
int main() {
  int vers = concatenate(CPX_VERSION_VERSION, CPX_VERSION_RELEASE);
  vers = concatenate(vers, CPX_VERSION_MODIFICATION);
  printf("%d", vers);



}
