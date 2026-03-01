#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "dog.h"

/* Override Animal methods for Dog */
static void dog_speak(Animal* self) {
    Dog* dog = (Dog*)self;
    printf("%s barks: Woof! (breed: %s)\n", self->name, dog->breed);
}

static void dog_move(Animal* self) {
    printf("%s runs on four legs\n", self->name);
}

static void dog_destroy_impl(Animal* self) {
    Dog* dog = (Dog*)self;
    free(dog->breed);
    free(self->name);
    free(dog);
}

/* Dog's vtable - polymorphism */
static const AnimalVtable dog_vtable = {
    .speak = dog_speak,
    .move = dog_move,
    .destroy = dog_destroy_impl
};

Dog* dog_new(const char* name, int age, const char* breed) {
    Dog* d = malloc(sizeof(Dog));
    if (!d) return NULL;

    d->base.vtable = &dog_vtable;
    d->base.name = strdup(name);
    d->base.age = age;
    d->breed = strdup(breed);
    d->is_trained = 0;
    return d;
}

void dog_free(Dog* self) {
    if (self) {
        self->base.vtable->destroy((Animal*)self);
    }
}

void dog_bark(Dog* self) {
    for (int i = 0; i < 3; i++) {
        printf("Woof! ");
    }
    printf("\n");
}

void dog_fetch(Dog* self) {
    printf("%s fetches the ball!\n", self->base.name);
    self->is_trained = 1;
}
