#ifndef DOG_H
#define DOG_H

#include "animal.h"

/* Dog "inherits" from Animal via composition */
typedef struct Dog {
    Animal base;      /* Inheritance: first member is base class */
    char* breed;
    int is_trained;
} Dog;

/* Constructor/destructor */
Dog* dog_new(const char* name, int age, const char* breed);
void dog_free(Dog* self);

/* Dog-specific methods */
void dog_bark(Dog* self);
void dog_fetch(Dog* self);

#endif
