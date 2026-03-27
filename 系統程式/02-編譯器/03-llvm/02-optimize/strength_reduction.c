#include <stdio.h>

int strength_reduction(int n) {
    int result = 0;
    for (int i = 0; i < n; i++) {
        result = result + 16;
    }
    return result;
}

int main() {
    int result = strength_reduction(5);
    printf("strength_reduction(5) = %d\n", result);
    return 0;
}