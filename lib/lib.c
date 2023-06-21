#include <stdio.h>
#include <stdarg.h>

int getint() {
    int t;
    scanf("%d", &t);
    return t;
}

int getch() {
    char c;
    scanf("%c", &c);
    return (int)c;
}

float getfloat() {
    float n;
    scanf("%f", &n);
    return n;
}

int getarray(int a[]) {
    int n;
    scanf("%d", &n);
    for (int i = 0; i < n; i++) {
        scanf("%d", &a[i]);
    }
    return n;
}

int getfarray(float a[]) {
    int n;
    scanf("%d", &n);
    for (int i = 0; i < n; i++) {
        scanf("%f", &a[i]);
    }
    return n;
}

void putint(int a) {
    printf("%d", a);
}

void putch(int a) {
    printf("%c", a);
}

void putarray(int n, int a[]) {
    printf("%d:", n);
    for (int i = 0; i < n; i++) {
        printf(" %d", a[i]);
    }
    printf("\n");
}

void putfloat(float a) {
    printf("%f", a);
}

void putfarray(int n, float a[]) {
    printf("%d:", n);
    for (int i = 0; i < n; i++) {
        printf(" %f", a[i]);
    }
    printf("\n");
}

void putf(char a[], ...) {
    va_list args;
    va_start(args, a);
    vfprintf(stdout, a, args);
    va_end(args);
}

// Time info won't be output into *.out file, so unable time functions

void starttime() {}

void stoptime() {}
