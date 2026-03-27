#include <stdio.h>

int dead_code_elimination(int x) {
    if (0) {
        return x + 1;
    }
    return x * 2;
}

int main() {
    int result = dead_code_elimination(10);
    printf("dead_code_elimination(10) = %d\n", result);
    return 0;
}