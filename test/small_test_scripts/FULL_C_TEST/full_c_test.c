/*
 * Comprehensive C test file for static analysis
 * Tests: structs, vtables, constructors/destructors, complexity, data structures
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hashmap.h"
#include "queue.h"
#include "set.h"

// =============================================================================
// TEST: Basic struct with function pointers (potential vtable)
// =============================================================================

typedef struct Shape {
    double x, y;
    void (*draw)(struct Shape* self);
    double (*area)(struct Shape* self);
    void (*destroy)(struct Shape* self);
} Shape;

// =============================================================================
// TEST: Inheritance pattern (base struct as first member)
// =============================================================================

typedef struct Circle {
    Shape base;  // Inheritance via composition
    double radius;
    int color;
} Circle;

typedef struct Rectangle {
    Shape base;  // Inheritance via composition
    double width;
    double height;
} Rectangle;

// =============================================================================
// TEST: Vtable struct with multiple function pointers
// =============================================================================

typedef struct FileOperations {
    int (*open)(const char* path);
    int (*read)(void* buf, size_t size);
    int (*write)(const void* buf, size_t size);
    void (*close)(void);
    int (*seek)(long offset);
} FileOperations;

typedef struct NetworkOps {
    int (*connect)(const char* host);
    int (*send)(const void* data, size_t len);
    int (*recv)(void* buf, size_t len);
    void (*disconnect)(void);
} NetworkOps;

// =============================================================================
// TEST: Nested structs
// =============================================================================

typedef struct Node {
    int data;
    struct Node* next;
    struct Node* prev;
} Node;

typedef struct LinkedList {
    Node* head;
    Node* tail;
    size_t size;
} LinkedList;

// =============================================================================
// TEST: Opaque pointer pattern (forward declaration)
// =============================================================================

typedef struct Database Database;  // Opaque pointer
typedef struct Connection Connection;  // Opaque pointer

// =============================================================================
// TEST: Constructor functions
// =============================================================================

Circle* circle_create(double x, double y, double radius) {
    Circle* c = (Circle*)malloc(sizeof(Circle));
    if (!c) return NULL;
    c->base.x = x;
    c->base.y = y;
    c->radius = radius;
    return c;
}

Rectangle* rectangle_new(double x, double y, double w, double h) {
    Rectangle* r = (Rectangle*)malloc(sizeof(Rectangle));
    if (!r) return NULL;
    r->base.x = x;
    r->base.y = y;
    r->width = w;
    r->height = h;
    return r;
}

Node* node_init(int data) {
    Node* n = (Node*)calloc(1, sizeof(Node));
    if (n) n->data = data;
    return n;
}

LinkedList* alloc_list(void) {
    return (LinkedList*)calloc(1, sizeof(LinkedList));
}

// =============================================================================
// TEST: Destructor functions
// =============================================================================

void circle_destroy(Circle* c) {
    if (c) free(c);
}

void rectangle_free(Rectangle* r) {
    if (r) free(r);
}

void node_delete(Node* n) {
    if (n) free(n);
}

void list_cleanup(LinkedList* list) {
    Node* current = list->head;
    while (current) {
        Node* next = current->next;
        free(current);
        current = next;
    }
    free(list);
}

// =============================================================================
// TEST: Arrays (static and dynamic)
// =============================================================================

int global_array[100];
static int static_array[50];

void array_test(void) {
    int local_array[20];
    int matrix[10][10];
    char buffer[256];
    double* dynamic_array = (double*)malloc(100 * sizeof(double));
    
    int** ptr_array = (int**)malloc(10 * sizeof(int*));
    for (int i = 0; i < 10; i++) {
        ptr_array[i] = (int*)malloc(20 * sizeof(int));
    }
    
    // Cleanup
    for (int i = 0; i < 10; i++) {
        free(ptr_array[i]);
    }
    free(ptr_array);
    free(dynamic_array);
}

// =============================================================================
// TEST: Complexity - nested loops (depth 2)
// =============================================================================

void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

// =============================================================================
// TEST: Complexity - nested loops (depth 3)
// =============================================================================

void matrix_multiply(int a[][10], int b[][10], int c[][10], int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            c[i][j] = 0;
            for (int k = 0; k < n; k++) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}

// =============================================================================
// TEST: Complexity - nested loops (depth 4)
// =============================================================================

void four_nested_loops(int n) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = 0; k < n; k++) {
                for (int m = 0; m < n; m++) {
                    count++;
                }
            }
        }
    }
}

// =============================================================================
// TEST: qsort usage
// =============================================================================

int compare_ints(const void* a, const void* b) {
    return (*(int*)a - *(int*)b);
}

void sort_test(void) {
    int arr[100];
    qsort(arr, 100, sizeof(int), compare_ints);
}

// =============================================================================
// TEST: bsearch usage
// =============================================================================

void search_test(void) {
    int sorted_arr[100];
    int key = 42;
    int* result = (int*)bsearch(&key, sorted_arr, 100, sizeof(int), compare_ints);
}

// =============================================================================
// TEST: Multiple memory allocations
// =============================================================================

void memory_test(void) {
    void* p1 = malloc(100);
    void* p2 = calloc(50, sizeof(int));
    void* p3 = realloc(p1, 200);
    
    char* str = (char*)malloc(256);
    int* nums = (int*)calloc(1000, sizeof(int));
    
    free(p2);
    free(p3);
    free(str);
    free(nums);
}

// =============================================================================
// TEST: Simple functions (no nested loops)
// =============================================================================

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

void print_array(int arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int linear_search(int arr[], int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}

// =============================================================================
// TEST: Static functions
// =============================================================================

static void helper_function(void) {
    printf("Helper\n");
}

static int internal_compute(int x, int y) {
    return x * y + x - y;
}

// =============================================================================
// Main function
// =============================================================================

int main(void) {
    Circle* c = circle_create(0, 0, 5.0);
    Rectangle* r = rectangle_new(0, 0, 10.0, 20.0);
    
    LinkedList* list = alloc_list();
    
    int arr[10] = {5, 2, 8, 1, 9, 3, 7, 4, 6, 0};
    bubble_sort(arr, 10);
    qsort(arr, 10, sizeof(int), compare_ints);
    
    circle_destroy(c);
    rectangle_free(r);
    list_cleanup(list);
    
    return 0;
}