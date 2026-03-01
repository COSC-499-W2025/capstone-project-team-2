#include <stdio.h>
#include "animal.h"
#include "dog.h"

int main(void) {
    /* Create base Animal */
    Animal* animal = animal_create("Generic Animal", 5);

    /* Create Dog (polymorphic) */
    Dog* dog = dog_new("Buddy", 3, "Golden Retriever");

    /* Demonstrate polymorphism - same interface, different behavior */
    printf("=== Animal ===\n");
    animal_speak(animal);
    animal_move(animal);

    printf("\n=== Dog (as Animal) ===\n");
    animal_speak((Animal*)dog);  /* Calls dog_speak via vtable */
    animal_move((Animal*)dog);   /* Calls dog_move via vtable */

    printf("\n=== Dog-specific ===\n");
    dog_bark(dog);
    dog_fetch(dog);

    /* Cleanup */
    animal_destroy(animal);
    dog_free(dog);

    return 0;
}
