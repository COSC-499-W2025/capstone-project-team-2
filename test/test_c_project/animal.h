#ifndef ANIMAL_H
#define ANIMAL_H

/* Base "class" - Animal with vtable pattern */
typedef struct Animal Animal;

typedef struct AnimalVtable {
    void (*speak)(Animal* self);
    void (*move)(Animal* self);
    void (*destroy)(Animal* self);
} AnimalVtable;

struct Animal {
    const AnimalVtable* vtable;
    char* name;
    int age;
};

/* Constructor/destructor */
Animal* animal_create(const char* name, int age);
void animal_destroy(Animal* self);

/* Methods */
void animal_speak(Animal* self);
void animal_move(Animal* self);

#endif
