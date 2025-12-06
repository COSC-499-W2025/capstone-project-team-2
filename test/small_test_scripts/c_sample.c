#include <stdio.h>
#include "myheader.h"

// Opaque pointer typedef
typedef struct Hidden *Hidden_t;

// Base struct
struct Base {
    int x;
};

// Derived struct (inheritance by first member)
struct Derived {
    struct Base base;
    int y;
};

// Vtable struct
struct Foo_vtable {
    void (*start)(void*);
    void (*stop)(void*);
};

// Struct with method (function pointer)
struct Foo {
    int a;
    void (*bar)(int);
};

// Constructor / Destructor
Foo* foo_create() { return 0; }
void foo_destroy(Foo* f) { }

// Static function
static int helper() { return 1; }

// Function with nested loops
int test_loops() {
    for (int i = 0; i < 10; i++) {
        while (i < 5) {
            do {
            } while (i < 2);
        }
    }
    return 0;
}
