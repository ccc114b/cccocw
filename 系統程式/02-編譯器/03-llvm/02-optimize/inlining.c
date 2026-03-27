#include <stdio.h>

inline int square(int x) {
    return x * x;
}

inline int cube(int x) {
    return x * x * x;
}

int compute(int a, int b) {
    int s = square(a);
    int c = cube(b);
    return s + c;
}

int main() {
    int result = compute(5, 3);
    printf("compute(5, 3) = %d\n", result);
    return 0;
}