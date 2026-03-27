#include <stdio.h>

int common_subexpression(int a, int b, int c) {
    int x = (a + b) * c;
    int y = (a + b) + c;
    return x + y;
}

int main() {
    int result = common_subexpression(1, 2, 3);
    printf("common_subexpression(1,2,3) = %d\n", result);
    return 0;
}