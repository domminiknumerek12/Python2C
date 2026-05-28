#include <stdio.h>
#include <string.h>

int add2(int a, int b, int c);
int add3(int a, int b);

int add2(int a, int b, int c) {
    return ((a + b) + c);
}

int add3(int a, int b) {
    return (a + b);
}

int main(void) {
    printf("%s\n", "Hello, World!");
    double x = 10;
    double y = 20;
    double z = 30;
    printf("%d\n", add2(x, y, z));
    x = 5;
    y = 10;
    z = (x + y);
    printf("%.6g\n", z);
    int result = add3(3, 4);
    printf("%d\n", result);
    for (int i = 0; i < 5; i++) {
        printf("%d\n", i);
    }
    x = 5;
    if ((x > 0)) {
        printf("%s\n", "positive");
    } else {
        printf("%s\n", "negative");
    }
    x = 3.14;
    y = 2.71;
    z = (x + y);
    printf("%.6g\n", z);
    int a = 5;
    int b = (+a);
    int c = (-a);
    printf("%d %d\n", b, c);
    return 0;
}