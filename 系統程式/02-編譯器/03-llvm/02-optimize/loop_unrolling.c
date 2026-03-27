#include <stdio.h>

int loop_unrolling(int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += i;
    }
    return sum;
}

int main() {
    int result = loop_unrolling(8);
    printf("loop_unrolling(8) = %d\n", result);
    return 0;
}