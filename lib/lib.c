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
    scanf("%a", &n);
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
        scanf("%a", &a[i]);
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
    char buff[32];
    int len = snprintf(buff, 32, "%a", a);
    char* exp = buff + len;
    if (!('0' <= buff[len - 1] && buff[len - 1] <= '9')) {
        printf("%s", buff);
        return;
    }
    while (*exp != 'p') exp--;
    char* z = exp - 1;
    while (*(z - 1) == '0') z--;
    if (*(z - 1) == '.') z--;
    *z = '\0';
    printf("%s%s", buff, exp);
}

void putfarray(int n, float a[]) {
    printf("%d:", n);
    for (int i = 0; i < n; i++) {
        putch(' ');
        putfloat(a[i]);
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
