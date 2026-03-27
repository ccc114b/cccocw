#include <stdio.h>

int fold_constants() {
    int a = 5 * 24;
    int b = 100 - 50;
    int c = 10 / 2;
    int d = 15 + 25;
    return a + b + c + d;
}

int main() {
    int result = fold_constants();
    printf("fold_constants() = %d\n", result);
    return 0;
}