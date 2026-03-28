#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "animal.h"

static void default_speak(Animal* self) {
    printf("%s makes a sound\n", self->name);
}

static void default_move(Animal* self) {
    printf("%s moves around\n", self->name);
}

static const AnimalVtable animal_vtable = {
    .speak = default_speak,
    .move = default_move,
    .destroy = animal_destroy
};

Animal* animal_create(const char* name, int age) {
    Animal* a = malloc(sizeof(Animal));
    if (!a) return NULL;

    a->vtable = &animal_vtable;
    a->name = strdup(name);
    a->age = age;
    return a;
}

void animal_destroy(Animal* self) {
    if (self) {
        free(self->name);
        free(self);
    }
}

void animal_speak(Animal* self) {
    self->vtable->speak(self);
}

void animal_move(Animal* self) {
    self->vtable->move(self);
}
